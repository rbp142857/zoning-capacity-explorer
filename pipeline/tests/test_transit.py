"""Tests for distance_to_nearest_ft().

Every expected value can be checked by hand (geometry is in feet).
"""

import math

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, box

from conftest import CRS
from zce.transit import distance_to_nearest_ft


@pytest.fixture
def parcels():
    return gpd.GeoDataFrame(
        geometry=[
            box(0, 0, 100, 100),      # lot A
            box(1000, 0, 1100, 100),  # lot B
        ],
        index=[10, 20],  # deliberately not 0, 1: your index must match
        crs=CRS,
    )


def test_distance_is_measured_from_the_lot_edge(parcels):
    # A stop 50 ft to the right of lot A's right edge (x=100).
    stops = gpd.GeoDataFrame(geometry=[Point(150, 50)], crs=CRS)
    d = distance_to_nearest_ft(parcels, stops)
    assert math.isclose(d.loc[10], 50)    # edge to point, not center (which would be 100)
    assert math.isclose(d.loc[20], 850)   # 1000 - 150


def test_picks_the_nearest_of_several_stops(parcels):
    stops = gpd.GeoDataFrame(geometry=[Point(150, 50), Point(1050, 400)], crs=CRS)
    d = distance_to_nearest_ft(parcels, stops)
    assert math.isclose(d.loc[10], 50)
    assert math.isclose(d.loc[20], 300)   # 400 - 100 (top edge of lot B)


def test_equally_near_stops_give_one_value_per_lot(parcels):
    # Two stops exactly 50 ft from lot A (left and right). sjoin_nearest
    # returns both; the function must still return one row per lot.
    stops = gpd.GeoDataFrame(geometry=[Point(-50, 50), Point(150, 50)], crs=CRS)
    d = distance_to_nearest_ft(parcels, stops)
    assert len(d) == 2 and math.isclose(d.loc[10], 50)


def test_stop_inside_or_touching_a_lot_is_zero(parcels):
    stops = gpd.GeoDataFrame(geometry=[Point(50, 50), Point(1100, 50)], crs=CRS)
    d = distance_to_nearest_ft(parcels, stops)
    assert d.loc[10] == 0 and d.loc[20] == 0


def test_index_and_length_match_parcels(parcels):
    stops = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs=CRS)
    d = distance_to_nearest_ft(parcels, stops)
    assert isinstance(d, pd.Series)
    assert list(d.index) == [10, 20]


def test_no_stops_gives_unknown_not_zero(parcels):
    stops = gpd.GeoDataFrame(geometry=[], crs=CRS)
    d = distance_to_nearest_ft(parcels, stops)
    assert d.isna().all() and len(d) == 2


def test_rejects_degrees(parcels):
    stops = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs=CRS)
    with pytest.raises(ValueError):
        distance_to_nearest_ft(parcels.to_crs("EPSG:4326"), stops.to_crs("EPSG:4326"))


def test_rejects_mismatched_crs(parcels):
    stops = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs=CRS).to_crs("EPSG:3857")
    with pytest.raises(ValueError):
        distance_to_nearest_ft(parcels, stops)
