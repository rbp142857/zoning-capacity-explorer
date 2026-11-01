"""Clean step: raw downloads -> one GeoParquet of parcels with zoning attached.

Output: data.nosync/clean/<city>/parcels.parquet
Report: reports/<city>/quality_report.md  (committed, so changes are visible in git)

Golden rule of this step: parcels are FLAGGED, never silently dropped. Every
row that comes in goes out, and the report counts each flag.
"""

import json

import geopandas as gpd
import pandas as pd

from zce.adapters import ZONING_ADAPTERS, la_assessor
from zce.config import REPO_ROOT, CityConfig
from zce.report import write_quality_report
from zce import spatial, transit

# Lots smaller than this (sq ft) are almost always slivers, strips or mapping
# artifacts rather than buildable lots. 500 sq ft is smaller than any
# residential minimum lot size in the cities modeled so far.
SLIVER_SQFT = 500


def _add_flag(flags: pd.Series, condition: pd.Series, name: str) -> pd.Series:
    """Append `name` to the flag list of every row where condition is True."""
    condition = condition.fillna(False).astype(bool)
    return flags.where(~condition, flags.map(lambda f: f + [name]))


def apply_zone_splits(base_zone: pd.Series, address: pd.Series, splits) -> pd.Series:
    """Re-label lots whose zone's standards depend on the street (city.yaml `zone_splits`)."""
    out = base_zone.copy()
    done = pd.Series(False, index=base_zone.index)
    addr = address.fillna("")
    for split in splits:
        hit = ~done & (base_zone == split.zone) & addr.str.contains(split.address_pattern, case=False, regex=True)
        out[hit] = split.to
        done |= hit
    return out


def clean_city(city: CityConfig) -> gpd.GeoDataFrame:
    raw, crs = city.raw_dir, city.analysis_crs
    manifest = json.loads((raw / "_manifest.json").read_text())

    print("Loading parcels")
    parcels, stats = la_assessor.load_parcels(raw / "parcels.geojson", crs)
    n_in = len(parcels)

    print("Attaching zoning")
    adapter = ZONING_ADAPTERS[city.sources["zoning"].adapter]
    zone_cols, zones, zoning_notes = adapter(parcels, raw, city)
    parcels = parcels.join(zone_cols)
    parcels["base_zone"] = apply_zone_splits(parcels["base_zone"], parcels["address"], city.zone_splits)

    # Neighborhood grouping for charts: council districts where the city has
    # them, otherwise ZIP code (some cities, like Glendale, elect at large).
    if "districts" in city.sources:
        print("Joining parcels to council districts")
        districts = gpd.read_file(raw / "districts.geojson").to_crs(crs)
        parcels["district"] = spatial.assign_district(parcels, districts, city.sources["districts"].name_field)
    else:
        zips = "ZIP " + parcels["address"].str.extract(r"(9\d{4})\s*$", expand=False)
        # Lots with no address (mostly vacant or public land), and the few
        # addresses with a typo or a neighboring city's ZIP, go into one group
        # so the charts stay readable.
        counts = zips.value_counts()
        parcels["district"] = zips.where(zips.map(counts) >= 50, "Other or no ZIP")

    # Where the city publishes specific-plan boundaries, they're authoritative
    # for "is this lot inside a specific plan" (some plan areas use plain zone
    # codes); otherwise the adapter's reading of the zone code stands.
    if "specific_plans" in city.sources:
        plans = gpd.read_file(raw / "specific_plans.geojson").to_crs(crs)
        parcels["specific_plan"] = spatial.assign_district(parcels, plans, city.sources["specific_plans"].name_field)

    if "city_boundary" in city.sources:
        boundary = gpd.read_file(raw / "city_boundary.geojson").to_crs(crs)
        parcels["in_city_limits"] = spatial.inside_boundary(parcels, boundary)
    else:
        parcels["in_city_limits"] = True  # parcels were already filtered by tax-rate city

    print("Measuring distance to transit")
    major = transit.load_major_transit_stops(raw / "major_transit_stops.geojson", crs)
    rail = transit.load_rail_stations(raw / manifest["metro_rail_gtfs"]["file"], crs)
    parcels["dist_major_transit_ft"] = transit.distance_to_nearest_ft(parcels, major)
    parcels["dist_rail_station_ft"] = transit.distance_to_nearest_ft(parcels, rail)

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
    write_quality_report(parcels, zones, stats, manifest, city, report_path, zoning_notes)
    print(f"Wrote {report_path}")
    return parcels
