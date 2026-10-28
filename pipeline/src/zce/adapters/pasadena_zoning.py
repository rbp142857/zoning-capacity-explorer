"""Adapter: City of Pasadena zoning layer -> clean zoning polygons.

Each output polygon has:
  zone_code       the full code as published, e.g. "CD-MU-C"
  specific_plan   the specific plan it belongs to, or None
  base_zone       the district without the plan prefix, e.g. "MU-C"
  overlays        a list of recognized overlay codes, e.g. ["HD", "LD-12"]
  overlay_unparsed whatever text in the overlay field we could not recognize

Pasadena's overlay field is hand-typed and inconsistent ("HD LD-12",
"OC-HL-1", "SP-1a LD-4", descriptions with stray line breaks). Instead of
guessing, we pull out the overlay codes we recognize and report the rest in
the data-quality report so a human can look at it.
"""

import re

import geopandas as gpd

# Overlay families from Pasadena Zoning Code Article 3 (overlay districts).
# Order matters: longer, more specific patterns must come before shorter ones
# (e.g. "HD-SR" before "HD"), because the regex tries alternatives left to right.
OVERLAY_PATTERN = re.compile(
    r"""
    HD-SR | HD-\d+ | HD        # hillside development (HD-1 is used for a height limit)
    | LD-\d+                   # landmark district (historic)
    | HL-\d+                   # height limit
    | SP-1[a-e]                # North Lake specific plan overlay subareas
    | SFO-[A-Z]+(?:-[A-Z]+)?   # South Fair Oaks specific plan overlay
    | AD-\d                    # alcohol sales overlay (no effect on housing)
    | PK                       # parking overlay
    | OC                       # office conversion
    | SS | ND | HH            # other single-letter-pair overlays (see report)
    """,
    re.VERBOSE,
)


def parse_zone_code(zone_code: str, plan_prefixes: dict[str, str]) -> tuple[str | None, str]:
    """Split "CD-MU-C" into ("Central District Specific Plan", "MU-C").

    Codes without a known prefix (e.g. "RS-6") return (None, "RS-6").
    Some East Pasadena codes use a lowercase subdistrict ("EPSP-d2-CG-B"); we
    keep the subdistrict in base_zone because its rules differ.
    """
    code = zone_code.strip()
    prefix, _, rest = code.partition("-")
    if prefix.upper() in plan_prefixes and rest:
        return plan_prefixes[prefix.upper()], rest
    return None, code


def parse_overlays(overlay_code: str | None) -> tuple[list[str], str]:
    """Return (recognized overlay codes, leftover text we did not recognize)."""
    # Missing values arrive from pandas as NaN (a float), not None.
    if not isinstance(overlay_code, str) or not overlay_code.strip():
        return [], ""
    text = overlay_code.strip()
    found = OVERLAY_PATTERN.findall(text)
    leftover = OVERLAY_PATTERN.sub("", text).replace("-", " ").strip()
    return found, leftover


def load_zoning(raw_path, analysis_crs: str, plan_prefixes: dict[str, str]) -> gpd.GeoDataFrame:
    raw = gpd.read_file(raw_path).to_crs(analysis_crs)

    zones = gpd.GeoDataFrame(
        {
            "zone_code": raw["ZONE_CODE"].fillna("").str.strip(),
            "zone_category": raw["GEN_CODE"],
            "zone_ordinance": raw["ORDINANCE"],
        },
        geometry=raw.geometry,
        crs=raw.crs,
    )
    parsed = zones["zone_code"].map(lambda c: parse_zone_code(c, plan_prefixes))
    zones["specific_plan"] = parsed.str[0]
    zones["base_zone"] = parsed.str[1]

    overlays = raw["OVERLAY_CODE"].map(parse_overlays)
    zones["overlays"] = overlays.str[0]
    zones["overlay_unparsed"] = overlays.str[1]

    # A few published polygons are slightly self-intersecting. make_valid fixes
    # them so area calculations in the spatial join are correct.
    zones["geometry"] = zones.geometry.make_valid()
    return zones
