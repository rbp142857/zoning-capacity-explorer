"""Transit stops, and distance from each parcel to the nearest one.

Distance to transit matters twice in this project:
- California AB 2097 removes parking minimums within 1/2 mile (2,640 ft) of a
  "major transit stop", so it changes the parking constraint.
- Several reform levers ("raise heights near transit") and the
  "capacity by distance to transit" chart need it.
"""

import zipfile

import geopandas as gpd
import pandas as pd


def load_major_transit_stops(raw_path, analysis_crs: str) -> gpd.GeoDataFrame:
    """SCAG's official major transit stops (PRC 21064.3, as amended by AB 2553)."""
    stops = gpd.read_file(raw_path).to_crs(analysis_crs)
    return stops[["STATIONNAM", "geometry"]].rename(columns={"STATIONNAM": "stop_name"})


def load_rail_stations(gtfs_zip_path, analysis_crs: str) -> gpd.GeoDataFrame:
    """Metro rail stations from a GTFS feed.

    In GTFS, stops.txt lists every boarding point. location_type 1 means a
    "station" (a parent that groups platforms), which is what we want: one
    point per station rather than one per platform.
    """
    with zipfile.ZipFile(gtfs_zip_path) as z, z.open("stops.txt") as f:
        stops = pd.read_csv(f, dtype={"location_type": "Int64"})
    stations = stops[stops["location_type"] == 1]
    if stations.empty:  # some feeds have no parent stations; fall back to all stops
        stations = stops
    return gpd.GeoDataFrame(
        {"stop_name": stations["stop_name"].values},
        geometry=gpd.points_from_xy(stations["stop_lon"], stations["stop_lat"]),
        crs="EPSG:4326",  # GTFS coordinates are always WGS84 lon/lat
    ).to_crs(analysis_crs)


# ---------------------------------------------------------------------------
# 🧑‍🎓 EXERCISE (milestone 2): write this function.
#
# Read LEARNING.md -> "Coordinate systems" and "Spatial joins" first.
#
# What it should do:
#   Given parcels (polygons) and stops (points), both already in the SAME
#   projected CRS measured in feet (EPSG:2229), return a pandas Series with one
#   number per parcel: the straight-line distance in feet from the parcel to
#   the nearest stop.
#
# Rules:
#   - The result's index must match `parcels.index` exactly (same order, same
#     labels), so the pipeline can do `parcels["dist_ft"] = your_result`.
#   - Measure from the parcel's EDGE, not its center: a parcel that touches a
#     stop is distance 0. (Hint: Shapely/GeoPandas distance between a polygon
#     and a point is already edge-to-point.)
#   - If `stops` is empty, return all NaN (unknown), not 0 or infinity.
#   - Raise a ValueError if the two inputs have different CRSs, or if the CRS
#     is geographic (degrees), because distances in degrees are meaningless.
#     (Hint: `gdf.crs.is_geographic`.)
#   - It must be fast enough for ~30,000 parcels x ~1,000 stops. A double
#     Python for-loop will be very slow; look at `geopandas.sjoin_nearest`,
#     which uses a spatial index.
#
# Tests that check your version: pipeline/tests/test_transit_exercise.py
# Run them with:   make exercise
# ---------------------------------------------------------------------------
def distance_to_nearest_ft(parcels: gpd.GeoDataFrame, stops: gpd.GeoDataFrame) -> pd.Series:
    raise NotImplementedError("Exercise: see the comment above this function")
