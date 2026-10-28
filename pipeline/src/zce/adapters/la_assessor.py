"""Adapter: LA County Assessor parcels -> the project's common parcel schema.

This adapter is shared by every city in LA County. A city in another county
would get its own adapter that produces the same columns (see
ADDING_A_CITY.md).

Two things happen here:
1. PRIVACY: we keep only an explicit whitelist of columns. A whitelist (not a
   blacklist) means that if the county ever adds an owner-name or mailing
   address column, it is dropped automatically instead of leaking.
2. CONDOS: the Assessor gives every condo unit its own record, and all units in
   a building share one identical polygon (one complex here has 134 stacked
   copies). Zoning applies to the land, so we merge each stack into one lot.
"""

import geopandas as gpd
import pandas as pd

# Source column -> our column. Anything not listed here is discarded.
# Situs ("site") address is the property's street address, not the owner's
# mailing address; we keep it for address search.
WHITELIST = {
    "AIN": "parcel_id",
    "SitusFullAddress": "address",
    "UseCode": "use_code",
    "UseType": "use_type",
    "UseDescription": "use_description",
    "ParcelTypeCode": "parcel_type_code",
    "Roll_Year": "roll_year",
    "Roll_LandValue": "land_value",
    "Roll_ImpValue": "improvement_value",
    "Roll_LandBaseYear": "land_base_year",
}
# The Assessor stores up to five buildings per parcel in numbered columns.
BUILDING_SLOTS = range(1, 6)
CONDO_PARCEL_TYPE = 1  # ParcelTypeCode: 0 = regular, 1 = condo unit, 2 = other


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _summarize_buildings(raw: pd.DataFrame) -> pd.DataFrame:
    """Collapse the five numbered building columns into per-parcel totals."""
    units = pd.concat([_to_number(raw[f"Units{i}"]) for i in BUILDING_SLOTS], axis=1)
    sqft = pd.concat([_to_number(raw[f"SQFTmain{i}"]) for i in BUILDING_SLOTS], axis=1)
    years = pd.concat([_to_number(raw[f"YearBuilt{i}"]) for i in BUILDING_SLOTS], axis=1)
    # A year of 0 means "unknown" in this dataset, not the year 0.
    years = years.where(years > 0)

    return pd.DataFrame(
        {
            # min_count=1 keeps the result NaN (unknown) when every slot is
            # empty, instead of pretending the parcel has 0 units.
            "existing_units": units.sum(axis=1, min_count=1),
            "building_sqft": sqft.sum(axis=1, min_count=1),
            # The oldest building is the best single proxy for "building age".
            "year_built": years.min(axis=1),
        },
        index=raw.index,
    )


def _merge_condo_stacks(parcels: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Merge records that share an identical polygon into one lot."""
    # normalize() puts each polygon's vertices in a canonical order, so two
    # copies of the same shape compare equal even if drawn differently.
    shape_key = parcels.geometry.normalize().to_wkb()
    parcels = parcels.assign(_shape=shape_key)

    grouped = parcels.groupby("_shape", sort=False)
    lots = grouped.agg(
        parcel_id=("parcel_id", "min"),  # a stable representative ID
        ain_count=("parcel_id", "size"),
        address=("address", "first"),
        use_code=("use_code", "first"),
        use_type=("use_type", "first"),
        use_description=("use_description", "first"),
        parcel_type_code=("parcel_type_code", "first"),
        roll_year=("roll_year", "first"),
        land_value=("land_value", lambda s: s.sum(min_count=1)),
        improvement_value=("improvement_value", lambda s: s.sum(min_count=1)),
        land_base_year=("land_base_year", "min"),
        existing_units=("existing_units", lambda s: s.sum(min_count=1)),
        building_sqft=("building_sqft", lambda s: s.sum(min_count=1)),
        year_built=("year_built", "min"),
        geometry=("geometry", "first"),
    )
    lots["is_condo"] = grouped["parcel_type_code"].apply(
        lambda s: (s == CONDO_PARCEL_TYPE).any()
    )
    # For a condo stack, use the building's address without the unit number,
    # e.g. "960 SAN PASQUAL ST NO 101 ..." -> "960 SAN PASQUAL ST ...".
    stacked = lots["ain_count"] > 1
    lots.loc[stacked, "address"] = lots.loc[stacked, "address"].str.replace(
        r"\s+(NO|UNIT|APT|#)\s*\S+", "", regex=True
    )
    return gpd.GeoDataFrame(lots.reset_index(drop=True), geometry="geometry", crs=parcels.crs)


def load_parcels(raw_path, analysis_crs: str) -> tuple[gpd.GeoDataFrame, dict]:
    """Read raw Assessor GeoJSON and return (lots, stats for the quality report)."""
    raw = gpd.read_file(raw_path)

    parcels = raw[list(WHITELIST)].rename(columns=WHITELIST)
    for col in ("land_value", "improvement_value", "land_base_year"):
        parcels[col] = _to_number(parcels[col])
    parcels = parcels.join(_summarize_buildings(raw))
    parcels = gpd.GeoDataFrame(parcels, geometry=raw.geometry, crs=raw.crs).to_crs(analysis_crs)

    lots = _merge_condo_stacks(parcels)

    # Lot area comes from the polygon, in square feet because EPSG:2229 is in
    # feet. The Assessor's own lot-size field is often missing, so geometry is
    # the more complete source (see METHODOLOGY.md).
    lots["lot_area_sqft"] = lots.geometry.area

    stats = {
        "assessor_records": len(raw),
        "lots_after_condo_merge": len(lots),
        "condo_records_merged": int(len(raw) - len(lots)),
        "condo_lots": int(lots["is_condo"].sum()),
    }
    return lots, stats
