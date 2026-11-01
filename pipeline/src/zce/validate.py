"""Validation: compare our numbers with official figures.

    make validate   ->   reports/<city>/validation.md

Three checks, each skipped (with instructions) if its source file is missing:

1. Existing homes: the Assessor roll's unit count vs. the state Department
   of Finance (DOF) E-5 housing-unit estimates.
2. Housing Element sites: for every site in the city's 2021-2029 sites
   inventory, the city's capacity estimate vs. ours on the same parcel.
3. Actual production: homes permitted per year (HCD Annual Progress Reports,
   Table A2), by building type and by where they were built, vs. our
   "likely to redevelop" estimate.

These are comparisons, not pass/fail tests: the city, the state and this
tool count different things, so the report explains each difference.
"""

import json
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

from zce.config import DATA_DIR, REPO_ROOT, CityConfig
from zce.report import _table


def _fmt(n) -> str:
    return f"{int(round(n)):,}"


def _address_key(address) -> str | None:
    """'1878 E WALNUT ST CONDOMINIUM\nPASADENA...' -> '1878 E WALNUT ST' (number + 3 street words)."""
    first = str(address or "").upper().split("\n")[0]
    m = re.match(r"\s*(\d+)\s+(.*)", first)
    if not m:
        return None
    noise = {"CONDOMINIUM", "MIXED", "USE", "UNIT", "PASADENA", "CA", "APARTMENTS"}
    words = [w for w in re.sub(r"[^A-Z0-9 ]", " ", m.group(2)).split() if w not in noise]
    return f"{m.group(1)} {' '.join(words[:3])}" if words else None


def _digits(apn) -> str:
    return re.sub(r"\D", "", str(apn or ""))


# --- 1. DOF housing units -------------------------------------------------------


def dof_housing_units(xlsx: Path, city_name: str) -> pd.DataFrame:
    """Total and 5+ unit housing counts for one city, every year in the E-5 file."""
    xl = pd.ExcelFile(xlsx)
    rows = []
    for sheet in xl.sheet_names:
        m = re.match(r"E5CityCounty(\d{4})", sheet)
        if not m:
            continue
        df = pd.read_excel(xl, sheet, header=None)
        hit = df[df[0].astype(str).str.strip().str.lower() == city_name.lower()]
        if hit.empty:
            continue
        r = hit.iloc[0]
        # Columns: 4 = total units, 5 = single detached, 6 = single attached,
        # 7 = two to four, 8 = five plus (see the sheet's header rows).
        rows.append({"year": int(m.group(1)), "total": int(r[4]), "single_detached": int(r[5]),
                     "two_to_four": int(r[7]), "five_plus": int(r[8])})
    return pd.DataFrame(rows).sort_values("year")


# --- 2. Housing Element sites inventory ------------------------------------------

# One row of the HCD sites-inventory table as it comes out of the PDF:
#   <address> <zip> <APN> [<site letter>] <GP> <zone> <min du/ac> <max du/ac> <acres> ...
#   ...<"Used/Not Used in Prior Housing ..."> <low> <moderate> <above moderate> <total> ...
SITE_ROW = re.compile(
    r"(?P<apn>\d{10}) (?:(?P<site>[A-Z]{1,2}) )?(?P<gp>\S+) (?P<zone>\S+) "
    r"(?P<min_du_ac>[\d.]+) (?P<max_du_ac>[\d.]+) (?P<acres>[\d.]+) "
    r".*?(?:Hou|Housing|Consecu\w*)\s+(?P<low>\d+) (?P<moderate>\d+) (?P<above>\d+) (?P<total>\d+)"
)
SITE_LINE = re.compile(r" 9\d{4} \d{10} ")


def parse_sites(text: str) -> tuple[pd.DataFrame, list[str]]:
    """Parse sites-inventory rows from the Housing Element's extracted text."""
    rows, unparsed = [], []
    for line in text.split("\n"):
        if not SITE_LINE.search(line):
            continue
        m = SITE_ROW.search(line)
        if m:
            rows.append(m.groupdict())
        else:
            unparsed.append(line)
    df = pd.DataFrame(rows)
    for c in ["low", "moderate", "above", "total"]:
        df[c] = df[c].astype(int)
    for c in ["min_du_ac", "max_du_ac", "acres"]:
        df[c] = df[c].astype(float)
    return df, unparsed


def housing_element_text(pdf: Path) -> str:
    from pypdf import PdfReader  # imported here: slow, and only this step needs it

    return "\n".join(page.extract_text() or "" for page in PdfReader(pdf).pages)


# --- 3. Annual Progress Report production ------------------------------------------


def load_apr(path: Path) -> pd.DataFrame:
    apr = pd.DataFrame(json.loads(path.read_text()))
    bp = [c for c in apr.columns if c.startswith("BP_") and c.endswith(("_DR", "_NDR", "_INCOME"))]
    co = [c for c in apr.columns if c.startswith("CO_") and c.endswith(("_DR", "_NDR", "_INCOME"))]
    for c in bp + co:
        apr[c] = pd.to_numeric(apr[c], errors="coerce").fillna(0)
    apr["permitted"] = apr[bp].sum(axis=1)
    apr["completed"] = apr[co].sum(axis=1)
    apr["apn"] = apr["APN"].map(_digits)
    apr["YEAR"] = apr["YEAR"].astype(int)
    return apr


# --- Report ----------------------------------------------------------------------------


def validate_city(city: CityConfig) -> Path:
    raw = city.raw_dir
    lots = gpd.read_parquet(DATA_DIR / "out" / city.id / "capacity.parquet")
    ok = lots["model_status"] == "ok"
    by_ain = lots.set_index("parcel_id")
    out = [f"# Validation report: {city.name}", "", "Generated by `make validate`. Do not edit by hand.", "",
           "Each section compares this tool with an official source. They count different things, so the point is "
           "to understand the differences, not to match exactly.", ""]

    def missing(name: str) -> None:
        src = city.sources[name]
        out.append(f"_Skipped: download {src.url} in a browser and save it as "
                   f"`data.nosync/raw/{city.id}/{src.filename}`, then run `make validate` again._\n")

    # 1. Existing homes ------------------------------------------------------------
    out.append("## 1. Existing homes: Assessor roll vs. Department of Finance\n")
    roll_total = lots["existing_units"].sum()
    dof_src = city.sources.get("dof_e5")
    xlsx = raw / (dof_src.filename or "") if dof_src else None
    if xlsx and xlsx.exists():
        dof = dof_housing_units(xlsx, city.official_name)
        latest = dof.iloc[-1]
        diff = roll_total / latest["total"] - 1
        out.append(_table(dof.rename(columns={"year": "DOF year (Jan 1; 2020 = Census)"})))
        out.append(f"\n- Homes on the Assessor roll (all lots, incl. not-modeled ones): **{_fmt(roll_total)}**")
        out.append(f"- DOF estimate for {int(latest['year'])}: **{_fmt(latest['total'])}** "
                   f"(difference **{diff:+.1%}**)")
        out.append("- Expected differences: the roll counts units the Assessor taxes (ADUs are sometimes "
                   "folded into the main building, sometimes not); DOF starts from the 2020 Census and adds "
                   "permits. A gap of a few percent is normal; a large gap would point to a data problem.\n")
    elif dof_src:
        missing("dof_e5")
    else:
        out.append("_Not configured for this city (add `dof_e5` to city.yaml)._\n")

    # 2. Housing Element sites -----------------------------------------------------
    out.append("## 2. Housing Element sites inventory vs. this tool\n")
    he_src = city.sources.get("housing_element")
    pdf = raw / (he_src.filename or "") if he_src else None
    if pdf and pdf.exists():
        sites, unparsed = parse_sites(housing_element_text(pdf))
        out.append(f"Parsed **{len(sites):,}** site rows from Appendix C (unparsed lines: {len(unparsed)}), "
                   f"total capacity **{_fmt(sites['total'].sum())}** homes. The document states 10,261 for "
                   "the sites table; a match confirms the parse.\n")
        sites["matched"] = sites["apn"].isin(by_ain.index)
        m = sites[sites["matched"]].join(by_ain, on="apn", rsuffix="_ours")
        m["our_local_new"] = (m["local_units"].astype("Float64") - m["existing_units"].fillna(0)).clip(lower=0)
        m["group"] = m["model_status"].map({"ok": "Modeled zones"}).fillna("Not modeled (specific plans, PDs)")
        g = m.groupby("group").agg(
            sites=("apn", "size"), city_capacity=("total", "sum"),
            our_local_new=("our_local_new", "sum"), our_realistic=("realistic_new_units", "sum"),
            our_likely_sites=("likely_redevelop", "sum"),
        ).reset_index()
        for c in ["city_capacity", "our_local_new", "our_realistic"]:
            g[c] = g[c].map(_fmt)
        out.append(_table(g))
        out.append(f"\nSite parcels not found among our lots: {int((~sites['matched']).sum())} "
                   "(usually condo or newly subdivided parcels whose numbers changed after 2022).\n")
        modeled = m[m["model_status"] == "ok"]
        if len(modeled):
            ratio = modeled["total"].sum() / max(1, modeled["our_local_new"].sum())
            out.append(f"- On sites in zones we model, the city's capacity is **{ratio:.0%}** of our maximum. "
                       "Housing Elements must use *realistic* capacity (state law asks cities to discount for "
                       "what actually gets built), so it should be lower than our theoretical maximum.")
            out.append(f"- Our screens mark **{int(modeled['likely_redevelop'].sum())} of {len(modeled)}** of those "
                       "site parcels as likely to redevelop. The city also includes sites with active applications, "
                       "which our screens can't see.")
        out.append(f"- **{int((m['model_status'] != 'ok').sum())} site parcels** with "
                   f"{_fmt(m.loc[m['model_status'] != 'ok', 'total'].sum())} homes are in specific plans or PDs "
                   "that this tool doesn't model yet: most of the city's planned capacity is there.\n")
    elif he_src:
        missing("housing_element")
    else:
        out.append("_Not configured for this city yet: its sites inventory table needs its own parser._\n")

    # 3. Production ----------------------------------------------------------------
    out.append("## 3. What actually gets built (HCD Annual Progress Reports)\n")
    apr_path = raw / "apr_table_a2.json"
    if apr_path.exists():
        apr = load_apr(apr_path)
        permits = apr.pivot_table(index="YEAR", columns="UNIT_CAT", values="permitted", aggfunc="sum", fill_value=0)
        permits["Total"] = permits.sum(axis=1)
        out.append("Homes **permitted** per year, by building type (ADU = accessory dwelling unit, SFD/SFA = "
                   "single-family detached/attached, MH = mobile home):\n")
        out.append(_table(permits.astype(int).reset_index()))
        years = permits.index.max() - permits.index.min() + 1
        per_year = permits.sum() / years
        out.append(f"\nAverage per year, {permits.index.min()}–{permits.index.max()}: "
                   f"**{_fmt(per_year['Total'])} homes**, of which {_fmt(per_year.get('5+', 0))} in buildings of 5+ "
                   f"homes, {_fmt(per_year.get('ADU', 0))} ADUs, and {_fmt(per_year.get('2 to 4', 0))} in 2–4 unit "
                   "buildings.\n")

        # Where were 5+ unit buildings permitted? Parcel numbers often no
        # longer exist (lots merged or turned into condos after the project),
        # so match in three steps: parcel number, then street address, then
        # the nearest lot to the record's map point (geocoded points tend to
        # sit in the street, so "nearest within 150 ft" rather than "inside").
        big = apr[(apr["UNIT_CAT"] == "5+") & (apr["permitted"] > 0)].copy()
        big["lot_id"] = big["apn"].where(big["apn"].isin(by_ain.index))
        big["match"] = big["lot_id"].notna().map({True: "parcel number", False: None})
        addr_to_lot = (
            lots.assign(k=lots["address"].map(_address_key)).dropna(subset=["k"]).drop_duplicates("k").set_index("k")["parcel_id"]
        )
        by_addr = big["STREET_ADDRESS"].map(_address_key).map(addr_to_lot)
        fill = big["lot_id"].isna() & by_addr.notna()
        big.loc[fill, "lot_id"], big.loc[fill, "match"] = by_addr[fill], "address"
        need = big["lot_id"].isna() & pd.to_numeric(big.get("LATITUDE"), errors="coerce").notna()
        if need.any():
            pts = gpd.GeoDataFrame(
                index=big.index[need],
                geometry=gpd.points_from_xy(pd.to_numeric(big.loc[need, "LONGITUDE"]), pd.to_numeric(big.loc[need, "LATITUDE"])),
                crs="EPSG:4326",
            ).to_crs(lots.crs)
            hit = gpd.sjoin_nearest(pts, lots[["parcel_id", "geometry"]], how="left", max_distance=150)
            hit = hit[~hit.index.duplicated()].dropna(subset=["parcel_id"])
            big.loc[hit.index, "lot_id"], big.loc[hit.index, "match"] = hit["parcel_id"], "nearest lot"
        how = big.groupby(big["match"].fillna("not matched"))["permitted"].sum()
        matched_share = big.loc[big["lot_id"].notna(), "permitted"].sum() / big["permitted"].sum()
        big = big.join(by_ain[["model_status", "zone_code", "specific_plan"]], on="lot_id")
        big["where"] = big["specific_plan"].fillna(
            big["model_status"].map({"ok": "Modeled base zones", "not_modeled": "Other zones not modeled (PDs, no zone found, ...)"}))
        big["where"] = big["where"].fillna("Parcel not matched")
        w = big.groupby("where")["permitted"].sum().sort_values(ascending=False)
        out.append(f"Where homes in **5+ unit buildings** were permitted ({matched_share:.0%} of them matched to a lot: "
                   + ", ".join(f"{_fmt(v)} by {k}" for k, v in how.items()) + "):\n")
        out.append(_table(pd.DataFrame({"area": w.index, "homes permitted": [_fmt(v) for v in w.values],
                                        "share": [f"{v / w.sum():.0%}" for v in w.values]})))
        modeled_rate = w.get("Modeled base zones", 0) / years
        realistic = lots.loc[ok, "realistic_new_units"].sum()
        out.append(f"\n- In the zones this tool models, 5+ unit buildings added about **{_fmt(modeled_rate)} homes "
                   f"a year**. Our likely-to-redevelop estimate for those zones is **{_fmt(realistic)} homes**, "
                   f"roughly **{realistic / max(modeled_rate, 1):.0f} years** of building at that pace. That's a "
                   "sanity check on scale, not a forecast: the pace depends on the market, not only on zoning.")
        out.append(f"- 2–4 unit buildings (the \"missing middle\" that SB 9 and fourplex reforms target) added about "
                   f"{_fmt(per_year.get('2 to 4', 0))} homes a year citywide. That's why the realistic estimate "
                   "doesn't count small-scale infill in single-family zones.")
        modeled_share = w.get("Modeled base zones", 0) / w.sum()
        coverage = ("Most new apartment buildings are in areas this tool doesn't model yet, so its totals miss "
                    "where the city builds most." if modeled_share < 0.5 else
                    f"{modeled_share:.0%} of new apartment homes are in zones this tool models.")
        out.append("- Nearest-lot matches can land on a neighbor across the street, so treat the shares as "
                   f"approximate. {coverage}\n")
    else:
        out.append("_Skipped: run `make download` to fetch the Annual Progress Report data._\n")

    path = REPO_ROOT / "reports" / city.id / "validation.md"
    path.write_text("\n".join(out) + "\n")
    print(f"Wrote {path}")
    return path
