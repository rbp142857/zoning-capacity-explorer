"""Adapter: SCAG's regional zoning table -> zone columns for each lot.

SCAG (the Southern California Association of Governments) compiles every
city's zoning into one parcel-level dataset for its whole region. Each record
has the parcel number (APN24), the city's own zone code (ZN24_CITY) and a
standardized regional category (ZN24_SCAG). That lets one adapter serve every
city in LA County: we join zones to the county's parcels by parcel number, no
map overlay needed.

Limits of this source, compared with a city's own zoning map:
- No overlay districts (historic, hillside, height limits), so overlay rules
  and the SB 9 historic-district exclusion can't be applied. Lots are not
  flagged for this individually; METHODOLOGY.md says so per city.
- Its zone codes reflect SCAG's 2024 compilation; a city may have rezoned
  since. The download date is in the manifest.
"""

import json
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

# SCAG's standardized zoning categories (first digits of ZN24_SCAG). Used only
# for reports and the "share of land in single-family zones" headline; the
# capacity math always uses the city's own rule files.
SCAG_CATEGORY = [
    ("111", "Single-Family Residential"),
    ("112", "Multi-Family Residential"),
    ("11", "Residential"),
    ("12", "Commercial"),
    ("13", "Industry"),
    ("14", "Transportation and Utilities"),
    ("15", "Mixed Commercial and Industrial"),
    ("16", "Mixed Residential and Commercial"),
    ("18", "Open Space"),
]


def scag_category(code) -> str | None:
    code = str(code or "")
    return next((name for prefix, name in SCAG_CATEGORY if code.startswith(prefix)), None)


def split_zone(zone_code: str, plan_prefixes: dict[str, str]) -> tuple[str | None, str]:
    """"DSP/EB" -> ("Downtown Specific Plan", "EB"); "R1" -> (None, "R1")."""
    prefix, sep, rest = zone_code.partition("/")
    if sep and prefix.upper() in plan_prefixes:
        return plan_prefixes[prefix.upper()], rest
    return None, zone_code


def load_zone_table(raw_path: Path, plan_prefixes: dict[str, str], aliases: dict[str, str] | None = None) -> pd.DataFrame:
    """One row per parcel number with its zone, from SCAG's attribute records."""
    records = json.loads(Path(raw_path).read_text())
    df = pd.DataFrame(records)[["APN24", "ZN24_CITY", "ZN24_SCAG"]]
    df["apn"] = df["APN24"].map(lambda v: re.sub(r"\D", "", str(v or "")))
    df["zone_code"] = df["ZN24_CITY"].fillna("").astype(str).str.strip()
    df.loc[df["zone_code"].isin(["", "None"]), "zone_code"] = None
    # Missing codes are NaN (a float) in pandas, so test for a real string.
    parsed = df["zone_code"].map(lambda c: split_zone(c, plan_prefixes) if isinstance(c, str) else (None, None))
    df["specific_plan"] = parsed.str[0]
    # Translate SCAG's spelling to the code's (city.yaml `zone_aliases`).
    df["base_zone"] = parsed.str[1].map(lambda z: (aliases or {}).get(z, z) if isinstance(z, str) else z)
    df["zone_category"] = df["ZN24_SCAG"].map(scag_category)
    return df.drop_duplicates("apn").set_index("apn")


def attach_zoning(parcels: gpd.GeoDataFrame, raw_dir, city) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Zone columns for every lot, the zoning table, and data-quality notes."""
    table = load_zone_table(Path(raw_dir) / "zoning.json", city.specific_plan_prefixes, city.zone_aliases)

    def first_zoned(ains) -> str | None:
        # A condo lot has many parcel numbers; use the first one SCAG knows.
        return next((a for a in ains if a in table.index and isinstance(table.at[a, "zone_code"], str)), None)

    hit = parcels["ains"].map(first_zoned)
    cols = ["zone_code", "zone_category", "specific_plan", "base_zone"]
    out = table.reindex(hit.values)[cols].set_axis(parcels.index)
    out["overlays"] = [[] for _ in range(len(out))]  # SCAG has no overlays
    out["overlay_unparsed"] = ""
    out["zone_ordinance"] = None
    # A parcel-number join either matches the whole lot or not at all.
    out["zone_share"] = hit.notna().astype(float).where(hit.notna())
    out["zoned_share"] = out["zone_share"]

    zones = table.reset_index()[["zone_code", "zone_category", "base_zone"]].assign(overlay_unparsed="")
    notes = [f"{(~hit.notna()).sum():,} lots had no matching parcel number in SCAG's table."]
    return out, zones, notes
