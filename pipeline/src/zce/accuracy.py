"""Accuracy test: what cities actually permitted vs. what this tool says each lot allows.

    python -m zce accuracy   ->   reports/la_county/accuracy.md, accuracy_by_city.csv, accuracy_cases.csv

Source: HCD Annual Progress Reports (Table A2), which list permitted projects by parcel.
If a real building has more homes than our number, we may have the rule wrong, or the
project may have used something we don't model. So this test can only catch numbers that
are too LOW. It can't show a number is too high, because most buildings don't use all the
capacity they're allowed. See METHODOLOGY.md, "Accuracy test".
"""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from zce.config import CITIES_DIR, DATA_DIR, REPO_ROOT
from zce.report import _table
from zce.validate import load_apr

CATEGORIES = ("5+", "2 to 4")
# Most-to-least supportive of our number. Each project gets the first that applies.
FITS_LOCAL = "fits_local_rules"
FITS_STATE = "fits_with_state_law"
MULTIFAMILY_ADU = "over_by_two_or_fewer_small_buildings"
BONUS_REPORTED = "over_but_bonus_reported"
FITS_BONUS = "over_but_fits_a_density_bonus"
FLAGGED = "over_on_a_lot_flagged_as_simplified"
UNEXPLAINED = "over_and_unexplained"
LABELS = {
    FITS_LOCAL: "Fits our number under city rules",
    FITS_STATE: "Fits our number with state law (ADU, SB 9)",
    MULTIFAMILY_ADU: "Over our number by 1 or 2, in a 2 to 4 home building. ADUs on multifamily lots could explain it (not modeled)",
    BONUS_REPORTED: "Over our number, but the city reported a density bonus or streamlining",
    FITS_BONUS: "Over our number, but would fit an 80% density bonus (none reported)",
    FLAGGED: "Over our number, on a lot we flag as having conditions or plan rules we don't model",
    UNEXPLAINED: "Over our number with no explanation found",
}
SIMPLIFIED_FLAGS = {"zoning_conditions_not_modeled", "specific_plan_base_rules_used", "hillside_overlay_not_modeled"}
COLUMNS = ["parcel_id", "ains", "model_status", "rules_zone", "local_units", "max_units", "density_bonus_80_units", "capacity_flags"]


def apn_digits(apn) -> str | None:
    """A usable 10-digit parcel number, or None. HCD masks some with asterisks."""
    digits = re.sub(r"[-\s]", "", str(apn or ""))
    return digits if re.fullmatch(r"\d{10}", digits) else None


def _reported_bonus(row) -> bool:
    bonus = pd.to_numeric(row["DENSITY_BONUS_TOTAL"], errors="coerce")
    streamlined = str(row["APPROVE_SB35"] or "").strip().upper() not in ("", "N", "NONE", "NONE.")
    return (pd.notna(bonus) and bonus > 0) or streamlined


def projects_from_apr(apr: pd.DataFrame) -> pd.DataFrame:
    """One row per parcel and building type, with homes permitted across all years."""
    df = apr[apr["UNIT_CAT"].isin(CATEGORIES) & (apr["permitted"] > 0)].copy()
    df["apn"] = df["APN"].map(apn_digits)
    masked = int(df["apn"].isna().sum())
    df = df[df["apn"].notna()]
    df["bonus"] = df.apply(_reported_bonus, axis=1) if len(df) else False
    out = df.groupby(["apn", "UNIT_CAT"], as_index=False).agg(
        permitted=("permitted", "sum"), bonus=("bonus", "max"),
        address=("STREET_ADDRESS", "first"), first_year=("YEAR", "min"),
    )
    out.attrs["masked_apn_rows"] = masked
    return out


def lot_lookup(lots: pd.DataFrame) -> dict[str, int]:
    """Parcel number -> row position. Condo lots merge many parcel numbers into one lot."""
    index: dict[str, int] = {}
    for i, (pid, ains) in enumerate(zip(lots["parcel_id"], lots["ains"])):
        index[str(pid)] = i
        if isinstance(ains, (list, tuple, np.ndarray)):
            for a in ains:
                index[str(a)] = i
    return index


def classify(permitted: float, local: int, maximum: int, bonus_max, reported: bool, simplified: bool, category: str = "5+") -> str:
    if permitted <= local:
        return FITS_LOCAL
    if permitted <= maximum:
        return FITS_STATE
    if category == "2 to 4" and permitted <= maximum + 2:
        return MULTIFAMILY_ADU
    if reported:
        return BONUS_REPORTED
    if not pd.isna(bonus_max) and permitted <= bonus_max:
        return FITS_BONUS
    return FLAGGED if simplified else UNEXPLAINED


def check_city(city_id: str, apr: pd.DataFrame, lots: pd.DataFrame) -> pd.DataFrame:
    """Every permitted project in one city, matched to our lot and classified."""
    projects = projects_from_apr(apr)
    index = lot_lookup(lots)
    rows = []
    for p in projects.itertuples(index=False):
        i = index.get(p.apn)
        base = {"city": city_id, "apn": p.apn, "category": p.UNIT_CAT, "permitted": int(p.permitted),
                "first_year": int(p.first_year), "address": p.address}
        if i is None:
            rows.append({**base, "result": "lot_not_found"})
            continue
        lot = lots.iloc[i]
        if lot["model_status"] != "ok":
            rows.append({**base, "result": "lot_not_modeled"})
            continue
        flags = lot["capacity_flags"]
        simplified = flags is not None and bool(SIMPLIFIED_FLAGS & set(flags))
        rows.append({**base, "zone": lot["rules_zone"], "local_units": int(lot["local_units"]), "max_units": int(lot["max_units"]),
                     "result": classify(p.permitted, int(lot["local_units"]), int(lot["max_units"]), lot["density_bonus_80_units"], bool(p.bonus), simplified, p.UNIT_CAT)})
    return pd.DataFrame(rows)


def _city_ids() -> list[str]:
    out = []
    for folder in sorted(CITIES_DIR.iterdir()):
        ok = (DATA_DIR / "out" / folder.name / "capacity.parquet").exists() and (DATA_DIR / "raw" / folder.name / "apr_table_a2.json").exists()
        if ok and any((folder / "rules").glob("*.yaml")):
            out.append(folder.name)
    return out


def _share(n: int, d: int) -> str:
    return f"{n / d:.0%}" if d else "n/a"


def summarize(all_rows: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for city, g in all_rows.groupby("city"):
        tested = g[~g["result"].isin(["lot_not_found", "lot_not_modeled"])]
        five = tested[tested["category"] == "5+"]
        rows.append({
            "city": city, "projects": len(g), "tested": len(tested), "tested_5plus": len(five),
            "not_modeled": int((g["result"] == "lot_not_modeled").sum()), "not_found": int((g["result"] == "lot_not_found").sum()),
            "fits": int(tested["result"].isin([FITS_LOCAL, FITS_STATE]).sum()),
            "unexplained": int((tested["result"] == UNEXPLAINED).sum()),
            "fits_5plus": int(five["result"].isin([FITS_LOCAL, FITS_STATE]).sum()),
            "unexplained_5plus": int((five["result"] == UNEXPLAINED).sum()),
        })
    return pd.DataFrame(rows)


def write_accuracy() -> Path:
    frames = []
    for city in _city_ids():
        apr = load_apr(DATA_DIR / "raw" / city / "apr_table_a2.json")
        lots = pd.read_parquet(DATA_DIR / "out" / city / "capacity.parquet", columns=COLUMNS)
        frames.append(check_city(city, apr, lots))
    rows = pd.concat(frames, ignore_index=True)
    out_dir = REPO_ROOT / "reports" / "la_county"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(rows)
    summary.to_csv(out_dir / "accuracy_by_city.csv", index=False)
    over = rows[rows["result"].isin([MULTIFAMILY_ADU, FLAGGED, UNEXPLAINED, FITS_BONUS])].sort_values(["result", "permitted"], ascending=[True, False])
    over[["city", "apn", "address", "category", "permitted", "first_year", "zone", "local_units", "max_units", "result"]].to_csv(out_dir / "accuracy_cases.csv", index=False)

    tested = rows[~rows["result"].isin(["lot_not_found", "lot_not_modeled"])]
    table = []
    for cat in CATEGORIES:
        g = tested[tested["category"] == cat]
        for key, label in LABELS.items():
            n = int((g["result"] == key).sum())
            table.append({"building type": f"{cat} homes", "result": label, "projects": f"{n:,}", "share": _share(n, len(g))})
    untested = rows[rows["result"].isin(["lot_not_found", "lot_not_modeled"])]
    by_city = summary.sort_values("tested", ascending=False)
    by_city_out = pd.DataFrame({
        "city": by_city["city"], "tested": by_city["tested"].map("{:,}".format),
        "fits": [_share(a, b) for a, b in zip(by_city["fits"], by_city["tested"])],
        "unexplained": [_share(a, b) for a, b in zip(by_city["unexplained"], by_city["tested"])],
        "5+ tested": by_city["tested_5plus"].map("{:,}".format),
        "5+ fits": [_share(a, b) for a, b in zip(by_city["fits_5plus"], by_city["tested_5plus"])],
        "5+ unexplained": [_share(a, b) for a, b in zip(by_city["unexplained_5plus"], by_city["tested_5plus"])],
        "not modeled": by_city["not_modeled"].map("{:,}".format),
    })
    years = f"{int(rows['first_year'].min())}-{int(rows['first_year'].max())}"
    text = [
        "# Accuracy test: permitted buildings vs. this tool", "",
        "Generated by `python -m zce accuracy`. Do not edit by hand.", "",
        f"For {len(summary)} cities, every building of 2+ homes in the state's Annual Progress Reports (first permitted {years}) is matched "
        "to its lot and compared with this tool's number for that lot.", "",
        "**How to read this.** A building larger than our number means we may have the rule wrong, or the project may have used something we "
        "don't model, such as a bonus program, a variance, an older rule or a rezoning. This test can only catch numbers that are too low. "
        "It **can't show a number is too high**, because most buildings don't use all their allowed capacity. Passing doesn't prove a rule is right.", "",
        "Other limits: rules and zoning are today's, while permits date back to 2018. A lot may have been merged or split since, and a townhome project can show as "
        "one home on each tiny lot. The multifamily ADU row is a likely explanation, not a confirmed one. "
        "Homes on one parcel are added across years, and homes kept on the lot aren't counted.", "",
        "## Results", "", _table(pd.DataFrame(table)), "",
        f"Not tested: {int((untested['result'] == 'lot_not_modeled').sum()):,} projects on lots we don't model and "
        f"{int((untested['result'] == 'lot_not_found').sum()):,} whose parcel number we couldn't find. "
        "Masked parcel numbers are left out before matching.", "",
        "## By city", "", _table(by_city_out), "",
        "Every project over our number is listed in [accuracy_cases.csv](accuracy_cases.csv), so rules can be checked against the code.", "",
    ]
    path = out_dir / "accuracy.md"
    path.write_text("\n".join(text))
    print(f"Wrote {path}: {len(tested):,} projects tested")
    return path
