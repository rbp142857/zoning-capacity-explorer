"""Spatial joins: attach zoning and council district to each parcel.

After this step every parcel carries plain columns (zone, district, ...) and
the capacity engine never needs to touch geometry again.
"""

import geopandas as gpd
import pandas as pd

# If the largest zone covers less than this share of a parcel, the parcel is
# "split-zoned" and gets a flag. 0.9 leaves room for small mapping
# misalignments between the city's zoning lines and the county's parcel lines.
SPLIT_ZONE_THRESHOLD = 0.9


def assign_zone(parcels: gpd.GeoDataFrame, zones: gpd.GeoDataFrame) -> pd.DataFrame:
    """For each parcel, pick the zone that covers the largest part of it.

    Why largest overlap instead of "which zone contains the parcel's center"?
    Zoning lines and parcel lines come from different agencies and are often
    a few feet apart, and a few parcels really are split between two zones.
    Largest overlap handles both, and the share tells us how clean the match was.
    """
    zone_cols = ["zone_code", "zone_category", "specific_plan", "base_zone",
                 "overlays", "overlay_unparsed", "zone_ordinance"]
    left = parcels[["geometry"]].reset_index(names="_pid")
    right = zones[zone_cols + ["geometry"]].reset_index(names="_zid")

    # overlay(how="intersection") returns one piece per (parcel, zone) pair
    # that overlaps, with both sides' columns.
    pieces = gpd.overlay(left, right, how="intersection", keep_geom_type=True)
    pieces["piece_area"] = pieces.geometry.area

    # Total zoned area per parcel, and the largest piece per parcel.
    zoned_area = pieces.groupby("_pid")["piece_area"].sum()
    best = pieces.sort_values("piece_area", ascending=False).drop_duplicates("_pid")
    best = best.set_index("_pid")

    result = best[zone_cols].copy()
    parcel_area = parcels.geometry.area
    result["zone_share"] = best["piece_area"] / parcel_area.reindex(best.index)
    result["zoned_share"] = zoned_area / parcel_area.reindex(zoned_area.index)
    # Parcels with no overlap at all get NaN zone columns and are flagged later.
    return result.reindex(parcels.index)


def assign_district(parcels: gpd.GeoDataFrame, districts: gpd.GeoDataFrame, name_col: str) -> pd.Series:
    """Which area (council district, specific plan, ...) each parcel falls in.

    Uses a point guaranteed to be inside each parcel.

    representative_point() is like a centroid, but always falls inside the
    polygon (a centroid of an L-shaped or curved lot can land outside it).
    """
    points = gpd.GeoDataFrame(geometry=parcels.geometry.representative_point(), crs=parcels.crs)
    joined = gpd.sjoin(points, districts[[name_col, "geometry"]], how="left", predicate="within")
    # A point exactly on a shared border can match two districts; keep the first.
    joined = joined[~joined.index.duplicated(keep="first")]
    return joined[name_col].reindex(parcels.index)


def inside_boundary(parcels: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame) -> pd.Series:
    """True where the parcel's representative point is inside the city limits."""
    city = boundary.geometry.union_all()
    return parcels.geometry.representative_point().within(city)


def lot_dimensions(parcels: gpd.GeoDataFrame) -> pd.DataFrame:
    """Width and depth of each lot, from its minimum rotated rectangle.

    The minimum rotated rectangle is the smallest box (at any angle) that
    contains the lot. For the typical long, narrow city lot its short side is
    the street frontage (width) and its long side is the depth. This is an
    assumption: corner lots and odd shapes can face the "wrong" way. The
    engine also gets a shape factor (lot area / box area) so irregular lots
    don't get credit for area they don't have.
    """
    rects = parcels.geometry.minimum_rotated_rectangle()
    widths, depths = [], []
    for rect in rects:
        if rect.geom_type != "Polygon":  # degenerate slivers collapse to a line
            widths.append(0.0)
            depths.append(0.0)
            continue
        xs, ys = rect.exterior.coords.xy
        # Lengths of two adjacent sides of the rectangle.
        a = ((xs[1] - xs[0]) ** 2 + (ys[1] - ys[0]) ** 2) ** 0.5
        b = ((xs[2] - xs[1]) ** 2 + (ys[2] - ys[1]) ** 2) ** 0.5
        widths.append(min(a, b))
        depths.append(max(a, b))
    return pd.DataFrame({"lot_width_ft": widths, "lot_depth_ft": depths}, index=parcels.index)
