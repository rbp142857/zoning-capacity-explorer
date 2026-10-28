"""Capacity engine tests with hand-calculated example lots.

Each test shows its arithmetic in comments so you can check it with a
calculator. Most tests use small made-up rule objects (built by `zone()`) so
one constraint can be tested at a time; the last section uses Pasadena's real
rule files.

Shared assumptions for the made-up tests:
  gross floor area per unit = 1,000 sf, parking stall = 300 sf
"""

from pathlib import Path

import pytest

from zce.engine import EngineAssumptions, Lot, compute_capacity
from zce.engine.constraints import (
    density_limit,
    envelope_limit,
    lot_area_per_unit_limit,
    max_footprint_sqft,
    parking_limit,
    required_stalls,
    round_units,
    setback_area_sqft,
)
from zce.rules.schema import ZoneRules, load_state_overrides, load_zone_rules

REPO = Path(__file__).resolve().parents[2]
A = EngineAssumptions(gross_sqft_per_unit=1000, parking_stall_sqft=300)


def s(value):
    """Wrap a value as a cited rule value (tests cite a dummy source)."""
    return {"value": value, "source": "test"}


def zone(**overrides) -> ZoneRules:
    """A minimal multifamily zone; override any field per test."""
    data = {
        "zone": "TEST",
        "name": "Test zone",
        "family": "multifamily",
        "sources": {"test": {"section": "test", "url": "https://example.com"}},
        "residential_allowed": s(True),
        "housing_types": s(["multifamily"]),
        "setbacks": {"front_ft": s(0), "side_ft": s(0), "rear_ft": s(0)},
        "max_stories": s(3),
    }
    data.update(overrides)
    return ZoneRules.model_validate(data)


# --- Rounding -------------------------------------------------------------------


@pytest.mark.parametrize(
    "x, mode, expected",
    [
        (2.99, "floor", 2),
        (3.0, "floor", 3),
        (2.9999999999, "floor", 3),  # floating-point noise is treated as 3
        (2.75, "up_above_0_75", 2),  # exactly .75 does NOT round up
        (2.76, "up_above_0_75", 3),
        (2.49, "nearest_half_up", 2),
        (2.50, "nearest_half_up", 3),
    ],
)
def test_round_units(x, mode, expected):
    assert round_units(x, mode) == expected


# --- Constraint 1 and 2: density -------------------------------------------------


def test_units_per_lot_cap():
    assert density_limit(zone(max_units_per_lot=s(2)), Lot(10_000, 50, 200)) == 2


def test_units_per_acre():
    # 16 units/acre on 20,000 sf: 20,000 / 43,560 x 16 = 7.35 -> 7
    assert density_limit(zone(units_per_acre=s(16)), Lot(20_000, 100, 200)) == 7


def test_no_density_rule_means_not_applicable():
    assert density_limit(zone(), Lot(10_000, 50, 200)) is None


def test_lot_area_per_unit():
    # 13,600 / 1,360 = 10.0 -> 10
    assert lot_area_per_unit_limit(zone(lot_area_per_unit_sqft=s(1360)), Lot(13_600, 80, 170)) == 10


def test_lot_area_per_unit_uses_zone_rounding():
    # RM-16 style: 10,450 / 2,750 = 3.8 -> fraction over .75 -> 4
    z = zone(lot_area_per_unit_sqft=s(2750), density_rounding=s("up_above_0_75"))
    assert lot_area_per_unit_limit(z, Lot(10_450, 70, 150)) == 4
    # 10,300 / 2,750 = 3.745 -> fraction under .75 -> 3
    assert lot_area_per_unit_limit(z, Lot(10_300, 70, 150)) == 3


def test_small_lot_table_replaces_per_unit_rule():
    # Pasadena RM-32/RM-48: lots under 10,000 sf use a table, e.g. 6,000 sf -> 4 units
    z = zone(
        lot_area_per_unit_sqft=s(910),
        small_lot_units=s({"by": "lot_area_sqft", "bands": [
            {"below": 4000, "value": 2}, {"below": 5500, "value": 3},
            {"below": 7000, "value": 4}, {"below": 8500, "value": 5}, {"value": 6}]}),
        small_lot_units_below_sqft=10_000,
    )
    assert lot_area_per_unit_limit(z, Lot(6_000, 50, 120)) == 4
    # 12,000 sf is not a small lot: 12,000 / 910 = 13.2 -> 13
    assert lot_area_per_unit_limit(z, Lot(12_000, 80, 150)) == 13


# --- Constraint 3: envelope ---------------------------------------------------------


def test_setback_area_rectangle():
    # 50 x 100 lot, 20 ft front, 5 ft sides, 10 ft rear:
    # (50 - 2x5) x (100 - 20 - 10) = 40 x 70 = 2,800 sf
    z = zone(setbacks={"front_ft": s(20), "side_ft": s(5), "rear_ft": s(10)})
    assert setback_area_sqft(z, Lot(5_000, 50, 100)) == 2_800


def test_side_setback_as_share_of_width_is_clamped():
    # 10% of width, min 5, max 10. A 60 ft lot -> 6 ft sides; a 150 ft lot -> capped at 10.
    side = {"pct_of_width": 0.10, "min_ft": 5, "max_ft": 10}
    z = zone(setbacks={"front_ft": s(0), "side_ft": s(side), "rear_ft": s(0)})
    assert setback_area_sqft(z, Lot(6_000, 60, 100)) == (60 - 12) * 100
    assert setback_area_sqft(z, Lot(15_000, 150, 100)) == (150 - 20) * 100


def test_irregular_lot_scales_setback_area():
    # Bounding rectangle 50 x 100 = 5,000 sf, but the lot is only 4,000 sf
    # (shape factor 0.8). No setbacks: usable = 5,000 x 0.8 = 4,000 sf.
    assert setback_area_sqft(zone(), Lot(4_000, 50, 100)) == pytest.approx(4_000)


def test_setbacks_larger_than_lot_give_zero_not_negative():
    z = zone(setbacks={"front_ft": s(60), "side_ft": s(5), "rear_ft": s(60)})
    assert setback_area_sqft(z, Lot(5_000, 50, 100)) == 0


def test_footprint_is_tightest_of_setbacks_coverage_open_space():
    # 10,000 sf lot (100 x 100), no setbacks -> 10,000; coverage 40% -> 4,000;
    # open space 50% -> 5,000. Tightest = 4,000.
    z = zone(lot_coverage=s(0.40), min_open_space_share=s(0.50))
    assert max_footprint_sqft(z, Lot(10_000, 100, 100)) == 4_000


def test_envelope_stories_and_far():
    # 10,000 sf lot, footprint 4,000 (40% coverage) x 3 stories = 12,000 sf,
    # but FAR 1.0 caps it at 10,000 sf -> 10,000 / 1,000 per unit = 10 units.
    z = zone(lot_coverage=s(0.40), max_far=s(1.0))
    assert envelope_limit(z, Lot(10_000, 100, 100), A) == 10
    # Without the FAR cap: 12,000 / 1,000 = 12 units.
    assert envelope_limit(zone(lot_coverage=s(0.40)), Lot(10_000, 100, 100), A) == 12


def test_envelope_floor_area_formula_with_per_unit_allowance():
    # RM-12 style: max floor area = 35% of lot + 500 sf per unit.
    # 8,000 sf lot: n x 1,000 <= 2,800 + 500n  ->  500n <= 2,800  ->  n = 5
    z = zone(max_floor_area=s({"by": "lot_area_sqft",
                               "bands": [{"share": 0.35, "plus_sqft_per_unit": 500}]}))
    assert envelope_limit(z, Lot(8_000, 80, 100), A) == 5


def test_banded_coverage_with_at_least_and_no_limit_band():
    # Pasadena RS: no max up to 7,200 sf; 35% up to 12,000; then max(35%, 4,800 sf).
    cov = {"by": "lot_area_sqft", "bands": [
        {"below": 7200.01, "value": None}, {"below": 12000, "share": 0.35},
        {"share": 0.35, "at_least_sqft": 4800}]}
    z = zone(lot_coverage=s(cov))
    assert max_footprint_sqft(z, Lot(7_000, 70, 100)) == 7_000  # no coverage limit
    assert max_footprint_sqft(z, Lot(10_000, 100, 100)) == 3_500  # 35%
    assert max_footprint_sqft(z, Lot(12_000, 100, 120)) == 4_800  # 35% = 4,200 < 4,800


# --- Constraint 4: parking ------------------------------------------------------------


def test_required_stalls_with_guest_threshold():
    z = zone(parking_per_unit=s(2), guest_parking_per_unit=s(0.1), guest_parking_min_units=10)
    assert required_stalls(z, 9) == 18  # under 10 units: no guest spaces
    assert required_stalls(z, 10) == 21  # 20 + 1 guest
    assert required_stalls(z, 15) == 32  # 30 + 1.5 guest -> 31.5 -> rounds up to 32


def test_parking_limit_hand_calculated():
    # 10,000 sf lot (100 x 100), no setbacks, 2 stories, 2 stalls x 300 sf per unit.
    # Each unit: footprint 1,000 / 2 = 500 sf + parking 600 sf = 1,100 sf.
    # 10,000 / 1,100 = 9.09 -> 9 units (9 x 1,100 = 9,900 <= 10,000).
    z = zone(max_stories=s(2), parking_per_unit=s(2))
    assert parking_limit(z, Lot(10_000, 100, 100), A) == 9


def test_parking_guest_spaces_can_reduce_the_count():
    # 11,500 sf, same zone plus 0.1 guest/unit at 10+ units.
    # 10 units: 10 x 500 + 21 x 300 = 11,300 <= 11,500 fits.
    # 11 units: 11 x 500 + round(22 + 1.1 = 23.1) = 23 x 300 -> 5,500 + 6,900 = 12,400 too big.
    z = zone(max_stories=s(2), parking_per_unit=s(2), guest_parking_per_unit=s(0.1),
             guest_parking_min_units=10)
    assert parking_limit(z, Lot(11_500, 100, 115), A) == 10


def test_parking_exempt_lot_has_no_parking_limit():
    z = zone(parking_per_unit=s(2))
    assert parking_limit(z, Lot(10_000, 100, 100), A, exempt=True) is None


# --- Combining constraints --------------------------------------------------------------


def test_binding_constraint_is_the_minimum():
    # 13,600 sf: lot-area-per-unit -> 10, envelope -> 13,600 x 3 / 1,000 = 40,
    # parking (3 stories): unit = 333 + 600 = 933 sf -> 13,600 / 933 = 14.
    z = zone(lot_area_per_unit_sqft=s(1360), parking_per_unit=s(2))
    r = compute_capacity(z, Lot(13_600, 80, 170, existing_units=2), A)
    assert r.max_units == 10
    assert r.binding_constraint == "lot_area_per_unit"
    assert r.net_new_units == 8


def test_ties_report_legal_limit_before_physical():
    # density cap 2 and an envelope that also fits exactly 2 -> "density".
    z = zone(max_units_per_lot=s(2), max_stories=s(1))
    r = compute_capacity(z, Lot(2_000, 20, 100), A)
    assert r.max_units == 2 and r.binding_constraint == "density"


def test_no_negative_capacity_and_net_new_floor_at_zero():
    # A lot with more existing units than allowed: net new is 0, not negative.
    z = zone(max_units_per_lot=s(1))
    r = compute_capacity(z, Lot(5_000, 50, 100, existing_units=4), A)
    assert r.max_units == 1 and r.net_new_units == 0


def test_residential_not_allowed():
    r = compute_capacity(zone(residential_allowed=s(False)), Lot(10_000, 100, 100), A)
    assert r.max_units == 0 and r.binding_constraint == "use_not_permitted"


def test_zone_without_rules_is_not_modeled_not_zero():
    r = compute_capacity(None, Lot(10_000, 100, 100), A)
    assert r.status == "not_modeled" and r.max_units is None


def test_substandard_lot_is_flagged_not_zeroed():
    z = zone(min_lot_area_sqft=s(7200), max_units_per_lot=s(1))
    r = compute_capacity(z, Lot(5_000, 50, 100), A)
    assert r.max_units == 1 and "substandard_lot_area" in r.flags
    assert "substandard_lot_width" not in r.flags  # 50 ft wide, no width minimum in this zone


# --- Pasadena's real rules + California state law -----------------------------------------


@pytest.fixture(scope="module")
def pasadena():
    rules = load_zone_rules(REPO / "cities" / "pasadena" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    # Pasadena's real assumptions: 850 net / 0.80 = 1,062.5 sf gross per unit.
    a = EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300)
    return rules, state, a


def test_every_rule_file_cites_known_sources(pasadena):
    rules, _, _ = pasadena
    assert {"RS-1", "RS-2", "RS-4", "RS-6", "RM-12", "RM-16", "RM-16-1", "RM-32", "RM-48"} <= set(rules)


def test_rs6_typical_lot_sb9_wins(pasadena):
    # 7,200 sf RS-6 lot (60 x 120). Local zoning: 1 unit (density).
    # ADU path: 1 + ADU + JADU = 3. SB 9 with a lot split (>= 2,400 sf): 4. Max = 4.
    rules, state, a = pasadena
    r = compute_capacity(rules["RS-6"], Lot(7_200, 60, 120, existing_units=1), a, state)
    assert r.local_units == 1 and r.local_binding_constraint == "density"
    assert r.limits["state_adu"] == 3 and r.limits["state_sb9"] == 4
    assert r.max_units == 4 and r.binding_constraint == "state_law:sb9"
    assert r.net_new_units == 3


def test_rs6_in_landmark_district_gets_adus_but_not_sb9(pasadena):
    rules, state, a = pasadena
    r = compute_capacity(rules["RS-6"], Lot(7_200, 60, 120, overlays=("LD-1",)), a, state)
    assert r.max_units == 3 and r.binding_constraint == "state_law:adu"
    assert "sb9_excluded_historic_district" in r.flags


def test_rm32_parking_binds_unless_near_transit(pasadena):
    # 15,000 sf RM-32 lot, 100 x 150. Lot area per unit: 15,000 / 1,360 = 11.03 -> 11.
    # Gardens (80-160 ft wide): 29% -> ground for building + parking = 10,650 sf.
    # Stories 2.4 -> footprint per unit 1,062.5 / 2.4 = 442.7 sf.
    # 9 units: 9 x 442.7 + 18 stalls x 300 = 3,984 + 5,400 = 9,384 fits;
    # 10 units: 4,427 + 21 x 300 = 10,727 > 10,650 doesn't. Parking -> 9.
    rules, state, a = pasadena
    far = compute_capacity(rules["RM-32"], Lot(15_000, 100, 150, dist_major_transit_ft=5_000), a, state)
    assert far.max_units == 9 and far.binding_constraint == "parking"
    # Within 1/2 mile of a major transit stop, AB 2097 removes the parking
    # minimum, and lot area per unit (11) binds instead.
    near = compute_capacity(rules["RM-32"], Lot(15_000, 100, 150, dist_major_transit_ft=1_000), a, state)
    assert near.max_units == 11 and near.binding_constraint == "lot_area_per_unit"
    assert "ab2097" in near.state_laws_applied


def test_sliver_lot_gets_no_sb9_units(pasadena):
    # A 400 sf strip zoned RS-6: nothing fits locally, and it's too small for
    # SB 9's two 800 sf homes (our 1,200 sf threshold), so capacity stays 0.
    rules, state, a = pasadena
    r = compute_capacity(rules["RS-6"], Lot(400, 10, 40), a, state)
    assert r.max_units == 0 and "sb9_lot_too_small" in r.flags


def test_cg_allows_no_housing(pasadena):
    rules, state, a = pasadena
    r = compute_capacity(rules["CG"], Lot(10_000, 100, 100), a, state)
    assert r.max_units == 0 and r.binding_constraint == "use_not_permitted"
