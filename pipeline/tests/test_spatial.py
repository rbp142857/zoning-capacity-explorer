import math

import geopandas as gpd
from shapely.geometry import box

from conftest import CRS
from zce.spatial import assign_district, assign_zone, inside_boundary


def _zones(*items):
    """items: (zone_code, geometry) pairs -> a zoning GeoDataFrame."""
    return gpd.GeoDataFrame(
        {
            "zone_code": [c for c, _ in items],
            "zone_category": "test",
            "specific_plan": None,
            "base_zone": [c for c, _ in items],
            "overlays": [[] for _ in items],
            "overlay_unparsed": "",
            "zone_ordinance": None,
        },
        geometry=[g for _, g in items],
        crs=CRS,
    )


def test_parcel_takes_zone_with_largest_overlap():
    # A 100 ft wide lot: 70 ft is in RS-6, 30 ft is in RM-16.
    parcels = gpd.GeoDataFrame(geometry=[box(0, 0, 100, 100)], crs=CRS)
    zones = _zones(("RS-6", box(-500, -500, 70, 500)), ("RM-16", box(70, -500, 500, 500)))
    result = assign_zone(parcels, zones)
    assert result.loc[0, "zone_code"] == "RS-6"
    assert math.isclose(result.loc[0, "zone_share"], 0.70)
    assert math.isclose(result.loc[0, "zoned_share"], 1.0)


def test_parcel_outside_all_zones_is_kept_with_no_zone():
    parcels = gpd.GeoDataFrame(geometry=[box(0, 0, 10, 10), box(1000, 1000, 1010, 1010)], crs=CRS)
    zones = _zones(("RS-6", box(-50, -50, 50, 50)))
    result = assign_zone(parcels, zones)
    assert len(result) == 2  # nothing dropped
    assert result.loc[0, "zone_code"] == "RS-6"
    assert result.loc[1, "zone_code"] != result.loc[1, "zone_code"]  # NaN


def test_district_uses_a_point_inside_an_l_shaped_lot():
    # The centroid of this L-shaped lot falls in district B's square, but most
    # of the lot (and its representative point) is in district A.
    l_shape = box(0, 0, 100, 10).union(box(0, 0, 10, 100))
    parcels = gpd.GeoDataFrame(geometry=[l_shape], crs=CRS)
    districts = gpd.GeoDataFrame(
        {"name": ["A", "B"]},
        geometry=[box(-1, -1, 101, 101).difference(box(15, 15, 40, 40)), box(15, 15, 40, 40)],
        crs=CRS,
    )
    assert assign_district(parcels, districts, "name").iloc[0] == "A"


def test_inside_boundary():
    parcels = gpd.GeoDataFrame(geometry=[box(0, 0, 10, 10), box(500, 500, 510, 510)], crs=CRS)
    boundary = gpd.GeoDataFrame(geometry=[box(-100, -100, 100, 100)], crs=CRS)
    assert inside_boundary(parcels, boundary).tolist() == [True, False]
