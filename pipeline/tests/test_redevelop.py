"""Redevelopment screen tests. Thresholds as in Pasadena's city.yaml:
2x capacity, 50-year-old buildings (as of 2026), building worth < land,
no condos, no landmark (LD-) districts."""

import math

import pytest

from zce.engine.redevelop import AGE, ALL_STATIC, HISTORIC, LAND, OWNERSHIP, VALUE, ZONE, Screens, is_special_land, redevelopment, static_mask

S = Screens(
    as_of_year=2026, min_capacity_multiple=2.0, min_net_new_units=3, min_building_age_years=50,
    max_improvement_to_land_ratio=1.0, exclude_condos=True, exclude_overlay_prefixes=("LD-",),
)


def mask(**kw):
    base = dict(year_built=1950, land_value=800_000, improvement_value=200_000,
                existing_units=1, is_condo=False, overlays=())
    base.update(kw)
    return static_mask(S, **base)


@pytest.mark.parametrize("label, special", [
    ("Government Parcel", True), ("Mineral Processing", True), ("Golf Courses", True),
    ("Utility Commercial & Mutual: Pumping Plants State Assessed Pr", True), ("Schools (Private)", True),
    ("Cemeteries, Mausoleums, Mortuaries", True), ("Single", False), ("Parking Lots (Commercial Use Properties)", False),
    (None, False), (float("nan"), False),
])
def test_special_land_labels(label, special):
    assert is_special_land(label) is special


def test_government_land_is_not_likely_to_redevelop():
    m = mask(land_value=500_000, improvement_value=0, year_built=None, existing_units=None, special_land=True)
    assert not m & LAND
    r = redevelopment(S, m, local_units=100, existing_units=None)
    assert not r.likely and r.failed == ("public_or_special_land",)


def test_lot_off_the_tax_roll_is_not_vacant():
    # Lomita's Harbor Hills public housing lot has blanks for everything but its use.
    m = mask(land_value=None, improvement_value=None, year_built=None, existing_units=None)
    assert not m & AGE and not m & VALUE
    assert not redevelopment(S, m, local_units=374, existing_units=None).likely


@pytest.mark.parametrize("land, vacant", [(9, False), (1_000, False), (1_001, True)])
def test_placeholder_land_value_is_not_vacant(land, vacant):
    m = mask(land_value=land, improvement_value=0, year_built=None, existing_units=None)
    assert bool(m & AGE) is vacant and bool(m & VALUE) is vacant


def test_old_cheap_building_passes_every_static_screen():
    assert mask() == ALL_STATIC


@pytest.mark.parametrize("year, passes", [(1976, True), (1977, False), (2015, False)])
def test_age_screen_boundary(year, passes):
    # 2026 - 1976 = 50 years: passes; 1977 is 49 years: fails.
    assert bool(mask(year_built=year) & AGE) is passes


def test_value_screen():
    assert mask(improvement_value=720_000) & VALUE  # 0.9 x land: passes
    assert not mask(improvement_value=800_000) & VALUE  # equal to land: fails
    assert not mask(land_value=None) & VALUE  # unknown value fails
    assert not mask(land_value=math.nan) & VALUE  # NaN from pandas is "unknown" too


def test_vacant_lot_passes_age_and_value():
    m = mask(year_built=None, improvement_value=0, existing_units=0)
    assert m & AGE and m & VALUE


def test_condo_and_landmark_district_fail():
    assert not mask(is_condo=True) & OWNERSHIP
    assert not mask(overlays=("HD", "LD-4")) & HISTORIC
    assert mask(overlays=("HD",)) & HISTORIC  # hillside overlay isn't historic


def test_single_family_zone_lots_are_never_likely():
    # Small-scale infill in single-family zones is reported separately,
    # whether SB 9 or a city fourplex rule allows it.
    m = mask(single_family_zone=True)
    assert not m & ZONE
    r = redevelopment(S, m, local_units=4, existing_units=1)
    assert not r.likely and r.failed == ("single_family_zone",)


def test_likely_when_zoning_allows_double():
    # RM-32 lot with 4 homes; rules allow 11 (>= 2 x 4): likely, adds 11 - 4 = 7.
    r = redevelopment(S, ALL_STATIC, local_units=11, existing_units=4)
    assert r.likely and r.realistic_new_units == 7 and r.failed == ()


def test_not_likely_when_gain_is_small():
    # 8 allowed, 5 there: 8 < 2 x 5, so rebuilding isn't worth it.
    r = redevelopment(S, ALL_STATIC, local_units=8, existing_units=5)
    assert not r.likely and r.realistic_new_units == 0
    assert r.failed == ("zoning_allows_too_little_more",)


def test_vacant_lot_needs_at_least_three_homes():
    # The 3-home minimum gain applies to vacant lots too.
    assert redevelopment(S, ALL_STATIC, local_units=3, existing_units=0).realistic_new_units == 3
    assert not redevelopment(S, ALL_STATIC, local_units=2, existing_units=None).likely


def test_house_to_duplex_is_not_counted():
    # 2 allowed, 1 there: double, but only +1 home, which rarely pays for a teardown.
    r = redevelopment(S, ALL_STATIC, local_units=2, existing_units=1)
    assert not r.likely and r.failed == ("zoning_allows_too_little_more",)
    # A fourplex on the same lot (+3) counts.
    assert redevelopment(S, ALL_STATIC, local_units=4, existing_units=1).realistic_new_units == 3


def test_every_failed_screen_is_reported():
    r = redevelopment(S, ALL_STATIC & ~AGE & ~HISTORIC, local_units=1, existing_units=1)
    assert r.failed == ("zoning_allows_too_little_more", "building_too_new", "historic_district")


def test_not_modeled():
    assert redevelopment(S, ALL_STATIC, local_units=None, existing_units=3).failed == ("not_modeled",)
