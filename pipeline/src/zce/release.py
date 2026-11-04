"""Public data release: citable tables for researchers, journalists and planners.

    python -m zce release

Writes, to reports/la_county/ (small, committed):
  coverage.md / coverage.csv   each city's totals and how far to trust them
  rules.csv                    every rule value with its citation and written assumption

And, to data.nosync/out/release/ (one per city, not committed; publish them separately):
  <city>_lots.csv.gz           lot-level results

Lot files hold parcel number, zone and capacity only: no owner, mailing address or sale data.
"""

import json
import re
from pathlib import Path

import pandas as pd
import yaml

from zce.config import CITIES_DIR, DATA_DIR, REPO_ROOT, load_city
from zce.engine.redevelop import is_special_land
from zce.report import _table

LOT_COLUMNS = ["parcel_id", "zone_code", "rules_zone", "model_status", "lot_area_sqft", "existing_units", "year_built",
               "dist_major_transit_ft", "local_units", "max_units", "net_new_units", "binding_constraint", "approval",
               "likely_redevelop", "realistic_new_units"]
# A safety check: these must never reach a published file.
FORBIDDEN = re.compile(r"owner|mail|taxpayer|buyer|seller|sale|name", re.I)
SETBACKS = ("front_ft", "side_ft", "rear_ft")


def coverage_level(modeled_share: float, approval_share: float, data_year: int | None) -> str:
    """How far to trust a city's numbers. Plain thresholds, written down in METHODOLOGY.md."""
    if modeled_share < 0.85:
        return "Partial"
    if modeled_share >= 0.95 and approval_share >= 0.8 and (data_year is None or data_year >= 2021):
        return "Fuller"
    return "Usable"


def map_year(value) -> int | None:
    """SCAG's YEAR_ZN is a date in milliseconds since 1970, or sometimes a plain year."""
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return None
    return int(number) if number < 3000 else pd.to_datetime(int(number), unit="ms").year


def zoning_year(city) -> int | None:
    """Year of a city's SCAG zoning map, most common across its lots. None if it uses its own current map."""
    if city.sources["zoning"].adapter != "scag_zoning":
        return None
    try:
        records = json.loads((city.raw_dir / "zoning.json").read_text())
    except (OSError, ValueError):
        return None
    years = pd.Series([map_year(r.get("YEAR_ZN")) for r in records]).dropna()
    return int(years.mode().iloc[0]) if len(years) else None


def rule_rows(city_id: str) -> list[dict]:
    """One row per rule value: the value, its citation and any written assumption."""
    rows = []
    for path in sorted((CITIES_DIR / city_id / "rules").glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        sources = data.get("sources", {})

        def add(field, item):
            if isinstance(item, dict) and "value" in item and "source" in item:
                src = sources.get(item["source"], {})
                value = item["value"]
                rows.append({"city": city_id, "zone": data["zone"], "zone_name": data.get("name"), "family": data.get("family"), "field": field,
                             "value": value if isinstance(value, (int, float, str, bool)) else json.dumps(value, ensure_ascii=False),
                             "code_section": src.get("section"), "url": src.get("url"), "assumption": item.get("assumption")})

        for key, item in data.items():
            if key == "setbacks":
                for s in SETBACKS:
                    add(s, item.get(s))
            else:
                add(key, item)
    return rows


def hand_check_counts(text: str) -> dict[str, int]:
    """Lots per city in HAND_CHECKS.md. "Los Angeles (single-family zones)" counts toward Los Angeles.

    The file opens with Pasadena under its title, and "By-right homes" isn't a city.
    """
    counts: dict[str, int] = {}
    city = None
    for line in text.splitlines():
        heading = re.match(r"#{1,2} (.+)", line)
        if heading:
            title = re.sub(r"\s*\(.*\)$", "", heading.group(1)).strip().lower()
            city = "pasadena" if title == "hand-checked parcels" else title
        elif line.startswith("### ") and city:
            counts[city] = counts.get(city, 0) + 1
    return counts


def _published() -> set[str]:
    path = REPO_ROOT / "web" / "public" / "data" / "cities.json"
    return {c["id"] for c in json.loads(path.read_text())} if path.exists() else set()


def write_release() -> Path:
    out_dir = REPO_ROOT / "reports" / "la_county"
    out_dir.mkdir(parents=True, exist_ok=True)
    lot_dir = DATA_DIR / "out" / "release"
    lot_dir.mkdir(parents=True, exist_ok=True)
    bad = [c for c in LOT_COLUMNS if FORBIDDEN.search(c)]
    assert not bad, f"Private columns in the release: {bad}"

    accuracy_path = out_dir / "accuracy_by_city.csv"
    accuracy = pd.read_csv(accuracy_path).set_index("city") if accuracy_path.exists() else pd.DataFrame()
    checks = hand_check_counts((REPO_ROOT / "docs" / "HAND_CHECKS.md").read_text())
    published = _published()
    rows, rules = [], []
    for folder in sorted(CITIES_DIR.iterdir()):
        city_id = folder.name
        parquet = DATA_DIR / "out" / city_id / "capacity.parquet"
        if not parquet.exists() or not any((folder / "rules").glob("*.yaml")):
            continue
        city = load_city(city_id)
        name = city.name.split(",")[0]
        lots = pd.read_parquet(parquet, columns=LOT_COLUMNS + ["use_description", "capacity_flags"])
        ok = lots[lots["model_status"] == "ok"]
        special = ok["use_description"].map(is_special_land)
        conditions = ok["capacity_flags"].map(lambda f: f is not None and "zoning_conditions_not_modeled" in list(f))
        approval = ok["approval"].notna().mean() if len(ok) else 0.0
        modeled = len(ok) / len(lots) if len(lots) else 0.0
        year = zoning_year(city)
        fits = accuracy.loc[city_id] if city_id in accuracy.index else None
        rows.append({
            "city_id": city_id, "city": name, "on_site": city_id in published,
            "coverage_level": coverage_level(modeled, approval, year),
            "lots": len(lots), "modeled_share": round(modeled, 3), "lots_not_modeled": len(lots) - len(ok),
            "approval_confirmed_share": round(float(approval), 3), "zoning_map_year": year if year else "city's current map",
            "rule_files": len(list((folder / "rules").glob("*.yaml"))), "lots_reviewed": checks.get(name.lower(), 0),
            "existing_homes": int(ok["existing_units"].sum()), "local_capacity": int(ok["local_units"].sum()),
            "max_with_state_law": int(ok["max_units"].sum()), "net_new_theoretical": int(ok["net_new_units"].sum()),
            "net_new_on_special_land": int(ok.loc[special, "net_new_units"].sum()),
            "likely_new_homes": int(ok["realistic_new_units"].sum()), "likely_lots": int(ok["likely_redevelop"].sum()),
            "lots_with_unmodeled_conditions": int(conditions.sum()),
            "permits_tested": int(fits["tested"]) if fits is not None else 0,
            "permits_unexplained": int(fits["unexplained"]) if fits is not None else 0,
        })
        rules.extend(rule_rows(city_id))
        lots[LOT_COLUMNS].to_csv(lot_dir / f"{city_id}_lots.csv.gz", index=False)

    table = pd.DataFrame(rows)
    table.to_csv(out_dir / "coverage.csv", index=False)
    pd.DataFrame(rules).to_csv(out_dir / "rules.csv", index=False)
    view = pd.DataFrame({
        "City": table["city"], "Level": table["coverage_level"], "On site": table["on_site"].map({True: "yes", False: ""}),
        "Lots modeled": (table["modeled_share"] * 100).round().astype(int).astype(str) + "%",
        "Approval confirmed": (table["approval_confirmed_share"] * 100).round().astype(int).astype(str) + "%",
        "Zoning map": table["zoning_map_year"], "Lots reviewed": table["lots_reviewed"],
        "Lots with unmodeled conditions": table["lots_with_unmodeled_conditions"].map("{:,}".format),
        "Likely new homes": table["likely_new_homes"].map("{:,}".format),
        "Theoretical new homes": table["net_new_theoretical"].map("{:,}".format),
        "...on special land": table["net_new_on_special_land"].map("{:,}".format),
    })
    counts = table["coverage_level"].value_counts()
    text = [
        "# Coverage: which cities are modeled, and how far to trust them", "",
        "Generated by `python -m zce release`. Do not edit by hand. The same data is in [coverage.csv](coverage.csv).", "",
        "**Levels** are simple thresholds, not a measure of accuracy. **Fuller:** 95%+ of lots modeled, 80%+ with approval type confirmed, zoning map from 2021 or newer "
        "(or the city's own). **Usable:** 85%+ of lots modeled. **Partial:** under 85%, usually because the plans where a city builds most are missing, so totals run low. "
        "No level accounts for bonus programs such as LA's TOC, which aren't modeled anywhere.", "",
        f"Today: {int(counts.get('Fuller', 0))} Fuller, {int(counts.get('Usable', 0))} Usable, {int(counts.get('Partial', 0))} Partial, of {len(table)} cities with rule files (88 in the county).", "",
        "**Lots reviewed** counts lots in `docs/HAND_CHECKS.md`. In recent cities these review engine results rather than redo the arithmetic independently. "
        "**Special land** is government, utility, quarry, cemetery, golf and private school land, which counts in theoretical totals but not in likely new homes.", "",
        _table(view), "",
    ]
    path = out_dir / "coverage.md"
    path.write_text("\n".join(text))
    print(f"Wrote {path}, rules.csv ({len(rules):,} values) and {len(rows)} lot files in {lot_dir}")
    return path
