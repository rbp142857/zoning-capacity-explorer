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


def distance_to_nearest_ft(parcels: gpd.GeoDataFrame, stops: gpd.GeoDataFrame) -> pd.Series:
    """Straight-line distance in feet from each parcel to its nearest stop.

    Distance is measured from the parcel's EDGE: a lot that touches a stop is
    0 ft away. That matches how "within 1/2 mile" is commonly read for AB 2097
    (any part of the lot within the radius); the alternative reading (from the
    lot's center) is recorded as an assumption in METHODOLOGY.md.

    Returns a Series with the same index as `parcels`, so the caller can write
    `parcels["dist_ft"] = distance_to_nearest_ft(parcels, stops)`.
    """
    # Guard 1: both layers must use the same CRS, or we'd be comparing feet
    # in one coordinate system with numbers from another.
    if parcels.crs != stops.crs:
        raise ValueError(f"CRS mismatch: parcels are {parcels.crs}, stops are {stops.crs}")
    # Guard 2: in a geographic CRS (lon/lat) the "distance" would be in
    # degrees, which is not a fixed length. Fail loudly instead of returning
    # numbers that look plausible but are wrong.
    if parcels.crs is None or parcels.crs.is_geographic:
        raise ValueError("Use a projected CRS measured in feet (e.g. EPSG:2229), not lon/lat degrees")

    # No stops at all means "unknown", not "0 ft away".
    if stops.empty:
        return pd.Series(float("nan"), index=parcels.index, name="distance_ft")

    # sjoin_nearest uses a spatial index (an R-tree) to find each parcel's
    # closest stop without measuring against every stop, and distance_col
    # asks it to also return that distance. Polygon-to-point distance in
    # Shapely is already edge-to-point (and 0 if the point is inside).
    nearest = gpd.sjoin_nearest(
        parcels[["geometry"]],
        stops[["geometry"]],
        how="left",
        distance_col="distance_ft",
    )

    # If two stops are exactly equally close, sjoin_nearest returns one row
    # for each, so the same parcel appears twice. Keep one value per parcel
    # (the distance is identical either way), then put rows back in the
    # parcels' original order.
    distance = nearest["distance_ft"].groupby(level=0).min()
    return distance.reindex(parcels.index)
