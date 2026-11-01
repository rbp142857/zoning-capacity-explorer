"""Rank every LA County jurisdiction to plan which cities to add next.

    make waves   ->   reports/la_county/city_ranking.md (+ .csv)

For each of the 89 jurisdictions (88 cities + unincorporated county):
- parcels: how much of the county it covers (SCAG's parcel-level table)
- zone codes, and how many codes cover 90% of its parcels: roughly how many
  rule files it needs (the main cost of adding a city)
- homes permitted per year, 2018-2025, by building type (HCD Annual Progress
  Reports): where housing actually gets built, i.e. where the tool matters

Value per effort = homes permitted per year in buildings of 2+ homes (the
building types local zoning controls; ADUs follow state law everywhere) /
zone codes for 90% of parcels.
These are planning signals, not a verdict: docs/WAVE_PLAN.md explains the
waves drawn from them.
"""

import json
from pathlib import Path

import pandas as pd
import requests

from zce.config import REPO_ROOT
from zce.report import _table

SCAG = "https://maps.scag.ca.gov/scaggis/rest/services/LDX/Zoning_poly_LA/MapServer/0/query"
CKAN_SQL = "https://data.ca.gov/api/3/action/datastore_search_sql"
APR_A2 = "fe505d9b-8c36-42ba-ba30-08bc4f34e022"
HEADERS = {"User-Agent": "zoning-capacity-explorer (open-source research tool)"}
YEARS = (2018, 2025)
DONE = {"Pasadena", "Glendale", "Burbank", "Santa Monica"}
OUT_DIR = REPO_ROOT / "reports" / "la_county"


def _scag_stats(where: str, group_by: str) -> list[dict]:
    params = {
        "where": where,
        "groupByFieldsForStatistics": group_by,
        "outStatistics": json.dumps([{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}]),
        "f": "json",
    }
    data = requests.get(SCAG, params=params, headers=HEADERS, timeout=300).json()
    if data.get("exceededTransferLimit"):
        raise RuntimeError(f"SCAG statistics truncated for {where}")
    return [f["attributes"] for f in data["features"]]


def zone_stats() -> pd.DataFrame:
    """Parcels, zone codes, and codes covering 90% of parcels, per jurisdiction."""
    cities = [r["CITY"] for r in _scag_stats("COUNTY='Los Angeles'", "CITY") if r["CITY"]]
    rows = []
    for city in sorted(cities):
        counts = sorted((r["n"] for r in _scag_stats(f"CITY='{city.replace(chr(39), chr(39) * 2)}'", "ZN24_CITY")), reverse=True)
        total, running, codes90 = sum(counts), 0, 0
        for n in counts:
            running += n
            codes90 += 1
            if running >= 0.9 * total:
                break
        rows.append({"jurisdiction": city, "parcels": total, "zone_codes": len(counts), "codes_for_90pct": codes90})
        print(f"  {city}: {total:,} parcels, {len(counts)} codes")
    return pd.DataFrame(rows)


def permit_stats() -> pd.DataFrame:
    """Homes permitted per year by building type, per LA County jurisdiction."""
    bp = [f"BP_{lvl}_{kind}" for lvl in ("ACUTELY_LOW_INCOME", "EXTREMELY_LOW_INCOME", "VLOW_INCOME", "LOW_INCOME", "MOD_INCOME")
          for kind in ("DR", "NDR")] + ["BP_ABOVE_MOD_INCOME"]
    total = " + ".join(f'COALESCE("{c}", 0)' for c in bp)  # numeric columns; NULL = none
    sql = (f'SELECT "JURIS_NAME", "UNIT_CAT", SUM({total}) AS permits FROM "{APR_A2}" '
           f"WHERE \"CNTY_NAME\" = 'Los Angeles' AND \"YEAR\" BETWEEN {YEARS[0]} AND {YEARS[1]} "
           'GROUP BY "JURIS_NAME", "UNIT_CAT"')
    data = requests.get(CKAN_SQL, params={"sql": sql}, headers=HEADERS, timeout=300).json()
    if not data.get("success") or not data["result"]["records"]:
        raise RuntimeError(f"HCD permit query failed or returned nothing: {str(data)[:300]}")
    df = pd.DataFrame(data["result"]["records"])
    df["permits"] = pd.to_numeric(df["permits"]) / (YEARS[1] - YEARS[0] + 1)
    wide = df.pivot_table(index="JURIS_NAME", columns="UNIT_CAT", values="permits", aggfunc="sum", fill_value=0)
    out = pd.DataFrame({
        "permits_per_year": wide.sum(axis=1),
        "apartments_5plus_per_year": wide.get("5+", 0),
        "adus_per_year": wide.get("ADU", 0),
        "two_to_four_per_year": wide.get("2 to 4", 0),
    })
    return out.rename_axis("hcd_name").reset_index()


def _hcd_name(scag_name: str) -> str:
    # HCD reports the unincorporated county as "LOS ANGELES COUNTY".
    return "LOS ANGELES COUNTY" if scag_name == "Unincorporated" else scag_name.upper()


def rank() -> pd.DataFrame:
    print("SCAG zoning statistics (one request per jurisdiction)...")
    zones = zone_stats()
    print("HCD permit statistics...")
    permits = permit_stats()
    df = zones.assign(hcd_name=zones["jurisdiction"].map(_hcd_name)).merge(permits, on="hcd_name", how="left")
    df[["permits_per_year", "apartments_5plus_per_year", "adus_per_year", "two_to_four_per_year"]] = df[
        ["permits_per_year", "apartments_5plus_per_year", "adus_per_year", "two_to_four_per_year"]].fillna(0)
    # Apartments and 2-4 unit buildings depend on local zoning; ADUs follow
    # state law everywhere, so they don't measure the value of a city's rules.
    df["multifamily_per_year"] = df["apartments_5plus_per_year"] + df["two_to_four_per_year"]
    df["value_per_rule_file"] = df["multifamily_per_year"] / df["codes_for_90pct"].clip(lower=1)
    df["status"] = df["jurisdiction"].map(lambda c: "done" if c in DONE else "")
    return df.sort_values("value_per_rule_file", ascending=False).reset_index(drop=True)


def write_ranking() -> Path:
    df = rank()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "city_ranking.csv", index=False)
    shown = df[["jurisdiction", "status", "parcels", "zone_codes", "codes_for_90pct", "permits_per_year",
                "apartments_5plus_per_year", "adus_per_year", "value_per_rule_file"]].copy()
    for c in ["parcels", "permits_per_year", "apartments_5plus_per_year", "adus_per_year"]:
        shown[c] = shown[c].round().astype(int).map("{:,}".format)
    shown["value_per_rule_file"] = shown["value_per_rule_file"].round(1)
    lines = [
        "# LA County jurisdictions, ranked for planning", "",
        "Generated by `make waves`. Do not edit by hand. The waves themselves are in "
        "[docs/WAVE_PLAN.md](../../docs/WAVE_PLAN.md).", "",
        f"- **zone codes / codes for 90%**: from SCAG's parcel-level zoning table; the second is roughly how many "
        "rule files cover 90% of the city's parcels (the main cost of adding a city).",
        f"- **permits per year**: average homes permitted per year, {YEARS[0]}-{YEARS[1]}, HCD Annual Progress "
        "Reports (Table A2), all building types; 5+ = apartments in buildings of 5 or more homes.",
        "- **value per rule file**: homes per year in buildings of 2+ homes (what local zoning controls; ADUs "
        "follow state law everywhere) / codes for 90%: where a rule file goes furthest.", "",
        f"{len(df)} jurisdictions, {df['parcels'].sum():,} parcels, "
        f"{df['permits_per_year'].sum():,.0f} homes permitted per year.", "",
        _table(shown),
    ]
    path = OUT_DIR / "city_ranking.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"Wrote {path}")
    return path
