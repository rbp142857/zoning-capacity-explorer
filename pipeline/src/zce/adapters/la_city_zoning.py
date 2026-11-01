"""Adapter: City of Los Angeles zoning layer -> zone columns for each lot.

LA writes everything about a lot's zoning into one string. For example
"[Q]R3-1D-O-HPOZ" means:

  [Q]    a condition set in a separate ordinance ("qualified"; also (T), (F))
  R3     the zone class
  1      the height district, which sets height and floor-area limits
  D      a development limitation, also in a separate ordinance
  O, ... supplemental districts (overlays)

Conditions and D limits differ lot by lot and live in ordinances we don't
read, so those lots are flagged as simplified, not guessed at.

Two other families are recognized and left for their own rule files:
- LA's new zoning code (LAMC Chapter 1A), written as bracket groups:
  "[LM2-MU2-5][RX1-FA][CPIO-O]" = form and frontage, use and density, overlays.
- Specific-plan zones, marked with a code in parentheses: "MU(EC)", "R3(PV)",
  "(WC)COLLEGE-SN". Those plans set their own standards.
"""

import re
from dataclasses import dataclass, field

import geopandas as gpd
import pandas as pd

# The layer's labels -> the labels the quality report uses for every city.
CATEGORIES = {"Single Family Residential": "Single-Family Residential", "Multiple Family Residential": "Multi-Family Residential"}

NEW_CODE = "Chapter 1A (new zoning code)"
CONDITION_MARK = "cond:"  # conditions stored in the overlays list, e.g. "cond:Q"
CONDITION = re.compile(r"^(\[[A-Z]\]|\([A-Z]\))")
PLAN_PREFIX = re.compile(r"^\(([A-Z]+)\)(.+)$")  # "(WC)COLLEGE-SN"
PLAN_SUFFIX = re.compile(r"^(.+)\(([A-Z]+)\)$")  # "MU(EC)"
GLUED_Q = re.compile(r"^Q[A-Z]")  # no LA zone class starts with Q
HEIGHT_DISTRICT = re.compile(r"^(1XL|1VL|1SS|1L|1A|2L|\d+(?:\.\d+)?)(D?)$")

# Supplemental districts seen in the layer. Anything else goes to
# overlay_unparsed, which the quality report lists for a person to review.
KNOWN_OVERLAYS = {
    "CA", "CDO", "CPIO", "CSA1", "CUGU", "G", "H", "HCR", "HPOZ", "K", "MPR", "NSO", "O", "POD", "RFA", "RG", "RIO",
    "RPD", "SN", "SP", "TCN",
}


@dataclass
class ParsedZone:
    zone_class: str | None = None  # "R3"
    height_district: str | None = None  # "1", without any D
    base_zone: str | None = None  # "R3-1": what rule files are looked up by first
    conditions: list[str] = field(default_factory=list)  # ["Q", "D"]
    overlays: list[str] = field(default_factory=list)
    specific_plan: str | None = None
    overlay_unparsed: str = ""


def _overlays(parts: list[str]) -> tuple[list[str], str]:
    """Sort overlay codes into known and unknown. A trailing # is a map footnote mark."""
    cleaned = [p.rstrip("#") for p in parts if p.rstrip("#")]
    known = [p for p in cleaned if p in KNOWN_OVERLAYS]
    return known, " ".join(p for p in cleaned if p not in KNOWN_OVERLAYS)


def parse_zone_string(text: str) -> ParsedZone:
    s = text.strip()

    # New zoning code: two or more bracket groups, the first with hyphens.
    groups = re.findall(r"\[([^\]]*)\]", s)
    if len(groups) >= 2 and "-" in groups[0]:
        base = "".join(f"[{g}]" for g in groups[:2])
        known, leftover = _overlays("-".join(groups[2:]).split("-"))
        return ParsedZone(zone_class=base, base_zone=base, overlays=known, specific_plan=NEW_CODE, overlay_unparsed=leftover)

    conditions = []
    while m := CONDITION.match(s):
        conditions.append(m.group(1)[1:-1])
        s = s[m.end():]

    specific_plan = None
    if m := PLAN_PREFIX.match(s):
        specific_plan, s = m.group(1), m.group(2)

    zone_class, *rest = s.split("-")
    # Older strings glue the condition to the zone: "QC2" is "[Q]C2".
    if GLUED_Q.match(zone_class):
        conditions.append("Q")
        zone_class = zone_class[1:]
    if m := PLAN_SUFFIX.match(zone_class):
        specific_plan = m.group(2)
    if specific_plan and not specific_plan.startswith("Specific"):
        specific_plan = f"Specific plan ({specific_plan})"

    height = None
    if rest and (m := HEIGHT_DISTRICT.match(rest[0])):
        height = m.group(1)
        if m.group(2):
            conditions.append("D")
        rest = rest[1:]

    known, leftover = _overlays(rest)
    return ParsedZone(
        zone_class=zone_class,
        height_district=height,
        base_zone=f"{zone_class}-{height}" if height else zone_class,
        conditions=conditions,
        overlays=known,
        specific_plan=specific_plan,
        overlay_unparsed=leftover,
    )


def load_zoning(raw_path, analysis_crs: str) -> gpd.GeoDataFrame:
    raw = gpd.read_file(raw_path).to_crs(analysis_crs)
    parsed = {text: parse_zone_string(text) for text in raw["Zoning"].dropna().unique()}
    zones = gpd.GeoDataFrame(
        {
            "zone_code": raw["Zoning"].str.strip(),
            "zone_category": raw["CATEGORY"].map(lambda c: CATEGORIES.get(c, c)),
            "zone_ordinance": None,  # the layer doesn't name ordinances
        },
        geometry=raw.geometry.make_valid(),
        crs=raw.crs,
    )
    get = lambda field: [getattr(parsed[t], field) if isinstance(t, str) else None for t in raw["Zoning"]]
    zones["zone_class"] = get("zone_class")
    zones["base_zone"] = get("base_zone")
    zones["specific_plan"] = get("specific_plan")
    zones["overlay_unparsed"] = [u or "" for u in get("overlay_unparsed")]
    # Conditions travel with the overlays, marked so nothing mistakes them for
    # a district: the capacity step flags these lots as simplified.
    zones["overlays"] = [
        (p.overlays + [f"{CONDITION_MARK}{c}" for c in p.conditions]) if isinstance(t, str) and (p := parsed[t]) else []
        for t in raw["Zoning"]
    ]
    return zones


def attach_zoning(parcels: gpd.GeoDataFrame, raw_dir, city) -> tuple[pd.DataFrame, gpd.GeoDataFrame, list[str]]:
    """Zone columns for every lot, the zoning table, and data-quality notes.

    Each lot takes the zone covering most of it (see spatial.assign_zone).
    Rule lookups try base_zone ("C2-1VL") first, then zone_class ("C2"), so a
    single rule file can cover a zone unless its height district matters.
    """
    from zce import spatial  # local import: spatial imports pandas/geopandas heavily

    zones = load_zoning(raw_dir / "zoning.geojson", city.analysis_crs)
    zone_cols = spatial.assign_zone(parcels, zones)
    zone_cols["zone_class"] = zone_cols["zone_code"].map(zones.drop_duplicates("zone_code").set_index("zone_code")["zone_class"])
    # A missing zone comes back as NaN from the join, but every other step expects a list.
    zone_cols["overlays"] = zone_cols["overlays"].map(lambda o: o if isinstance(o, list) else [])
    return zone_cols, zones, []
