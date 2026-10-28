"""Clean step: raw downloads -> one GeoParquet of parcels with zoning attached.

Output: data.nosync/clean/<city>/parcels.parquet
Report: reports/<city>/quality_report.md  (committed, so changes are visible in git)

Golden rule of this step: parcels are FLAGGED, never silently dropped. Every
row that comes in goes out, and the report counts each flag.
"""

import json

import geopandas as gpd
import pandas as pd

from zce.adapters import la_assessor, pasadena_zoning
from zce.config import REPO_ROOT, CityConfig
from zce.report import write_quality_report
from zce import spatial, transit

# Lots smaller than this (sq ft) are almost always slivers, strips or mapping
# artifacts rather than buildable lots. 500 sq ft is smaller than any
# residential minimum lot size in Pasadena.
SLIVER_SQFT = 500


def _add_flag(flags: pd.Series, condition: pd.Series, name: str) -> pd.Series:
    """Append `name` to the flag list of every row where condition is True."""
    condition = condition.fillna(False).astype(bool)
    return flags.where(~condition, flags.map(lambda f: f + [name]))


def _distance_or_nan(parcels, stops, label):
    """Run the transit exercise function, or leave NaN until it's written."""
    try:
        return transit.distance_to_nearest_ft(parcels, stops), True
    except NotImplementedError:
        print(f"  ! {label}: distance_to_nearest_ft() is not written yet (exercise); leaving NaN")
        return pd.Series(float("nan"), index=parcels.index), False


def clean_city(city: CityConfig) -> gpd.GeoDataFrame:
    raw, crs = city.raw_dir, city.analysis_crs
    manifest = json.loads((raw / "_manifest.json").read_text())

    print("Loading parcels")
    parcels, stats = la_assessor.load_parcels(raw / "parcels.geojson", crs)
    n_in = len(parcels)

    print("Loading zoning")
    zones = pasadena_zoning.load_zoning(raw / "zoning.geojson", crs, city.specific_plan_prefixes)

    print("Joining parcels to zones (largest overlap)")
    parcels = parcels.join(spatial.assign_zone(parcels, zones))

    print("Joining parcels to council districts")
    districts = gpd.read_file(raw / "districts.geojson").to_crs(crs)
    parcels["district"] = spatial.assign_district(parcels, districts, "DISTRICT_NAME")

    # The zone-code prefix only gave us a guess; the plan boundary layer is
    # authoritative for "is this lot inside a specific plan, and which one".
    plans = gpd.read_file(raw / "specific_plans.geojson").to_crs(crs)
    parcels["specific_plan"] = spatial.assign_district(parcels, plans, "NAME")

    boundary = gpd.read_file(raw / "city_boundary.geojson").to_crs(crs)
    parcels["in_city_limits"] = spatial.inside_boundary(parcels, boundary)

    print("Measuring distance to transit")
    major = transit.load_major_transit_stops(raw / "major_transit_stops.geojson", crs)
    rail = transit.load_rail_stations(raw / manifest["metro_rail_gtfs"]["file"], crs)
    parcels["dist_major_transit_ft"], transit_done = _distance_or_nan(parcels, major, "major transit stops")
    parcels["dist_rail_station_ft"], _ = _distance_or_nan(parcels, rail, "rail stations")

    # ---- Flags -------------------------------------------------------------
    flags = pd.Series([[] for _ in range(len(parcels))], index=parcels.index)
    flags = _add_flag(flags, ~parcels["in_city_limits"], "outside_city_limits")
    flags = _add_flag(flags, parcels["zone_code"].isna(), "no_zone")
    flags = _add_flag(flags, parcels["zone_share"] < spatial.SPLIT_ZONE_THRESHOLD, "split_zoned")
    flags = _add_flag(flags, parcels["specific_plan"].notna(), "specific_plan_simplified")
    flags = _add_flag(flags, parcels["base_zone"].str.startswith("PD", na=False), "planned_development")
    flags = _add_flag(flags, parcels["overlay_unparsed"].fillna("") != "", "overlay_unparsed")
    flags = _add_flag(flags, parcels["existing_units"].isna(), "missing_building_data")
    flags = _add_flag(flags, parcels["land_value"].isna(), "missing_assessed_value")
    flags = _add_flag(flags, parcels["lot_area_sqft"] < SLIVER_SQFT, "sliver_lot")
    if not transit_done:
        flags = _add_flag(flags, pd.Series(True, index=parcels.index), "transit_distance_missing")
    parcels["flags"] = flags

    # Sanity checks that should never fail. If one does, stop: something
    # upstream is broken and every later number would be wrong.
    assert len(parcels) == n_in, "rows were lost during the joins"
    assert parcels["parcel_id"].is_unique, "duplicate parcel IDs after condo merge"
    assert (parcels["lot_area_sqft"] > 0).all(), "a lot has zero or negative area"
    assert not (parcels["existing_units"] < 0).any(), "negative existing units"

    city.clean_dir.mkdir(parents=True, exist_ok=True)
    out = city.clean_dir / "parcels.parquet"
    parcels.to_parquet(out)  # GeoParquet: Parquet + geometry + CRS metadata
    print(f"Wrote {len(parcels):,} lots to {out}")

    report_path = REPO_ROOT / "reports" / city.id / "quality_report.md"
    write_quality_report(parcels, zones, stats, manifest, city, report_path)
    print(f"Wrote {report_path}")
    return parcels
