"""Scenario tests on Pasadena's real rules, with hand-calculated expectations.

Shared assumptions (Pasadena): 1,062.5 sf of building per home, 300 sf per stall.
"""

from pathlib import Path

import pytest

from zce.engine import EngineAssumptions, Lot
from zce.engine.scenario import Scenario, apply_scenario, capacity_under_scenario
from zce.rules.schema import load_state_overrides, load_zone_rules

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def base():
    rules = load_zone_rules(REPO / "cities" / "pasadena" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300)


def run(base, zone, lot, **levers):
    rules, state, a = base
    s = Scenario(**levers)
    r2, st2 = apply_scenario(rules, state, s)
    return capacity_under_scenario(zone, lot, a, r2, st2, s)


def test_baseline_scenario_changes_nothing(base):
    rules, state, a = base
    r2, st2 = apply_scenario(rules, state, Scenario())
    assert r2 == rules and st2 == state


def test_fourplex_in_rs6_is_capped_by_floor_area(base):
    # 7,200 sf RS-6 lot. Fourplex lever raises the per-lot cap to 4, but the
    # floor-area formula (30% x 7,200 + 500 = 2,660 sf) fits only
    # 2,660 / 1,062.5 = 2.5 -> 2 homes locally. SB 9 (4 with a split) still wins.
    r = run(base, "RS-6", Lot(7_200, 60, 120, dist_major_transit_ft=9_000), sf_units_per_lot=4)
    assert r.local_units == 2 and r.local_binding_constraint == "envelope"
    assert r.max_units == 4 and r.binding_constraint == "state_law:sb9"


def test_fourplex_on_big_rs2_lot(base):
    # 20,000 sf RS-2 lot (100 x 200). Floor area band 12k-24k: 20% x 20,000 + 1,700
    # = 5,700 sf -> 5.36 -> 5 homes, so the fourplex cap (4) binds.
    # Parking: 4 homes x 2 stalls is far from binding on 20,000 sf.
    r = run(base, "RS-2", Lot(20_000, 100, 200, dist_major_transit_ft=9_000), sf_units_per_lot=4)
    assert r.local_units == 4 and r.local_binding_constraint == "density"


def test_smaller_minimum_lot_allows_splits(base):
    # 20,000 sf RS-2 lot, minimum lot 5,000 sf -> 4 lots x 1 home = density cap 4.
    # The envelope (5 homes, see above) doesn't bind, so local = 4.
    r = run(base, "RS-2", Lot(20_000, 100, 200, dist_major_transit_ft=9_000), sf_min_lot_sqft=5_000)
    assert r.limits["density"] == 4 and r.local_units == 4


def test_no_parking_minimums_removes_parking_constraint(base):
    # Same RM-32 lot as the engine tests: parking binds at 9 today; with no
    # parking minimums, lot area per unit (11) binds.
    lot = Lot(15_000, 100, 150, dist_major_transit_ft=5_000)
    assert run(base, "RM-32", lot).max_units == 9
    r = run(base, "RM-32", lot, parking_per_unit=0)
    assert r.max_units == 11 and r.limits["parking"] is None


def test_wider_parking_exemption_radius(base):
    # 5,000 ft from transit: outside AB 2097's 2,640 ft, inside a 1-mile (5,280 ft) exemption.
    lot = Lot(15_000, 100, 150, dist_major_transit_ft=5_000)
    r = run(base, "RM-32", lot, parking_exempt_radius_ft=5_280)
    assert r.max_units == 11 and "ab2097" in r.state_laws_applied


def test_parking_radius_cannot_shrink_state_law(base):
    # A scenario radius below 2,640 ft is ignored: state law still applies at 1,000 ft.
    lot = Lot(15_000, 100, 150, dist_major_transit_ft=1_000)
    r = run(base, "RM-32", lot, parking_exempt_radius_ft=500)
    assert r.max_units == 11


def test_transit_upzoning_doubles_density_near_transit_only(base):
    # RM-32, 15,000 sf, within 1/2 mile (parking exempt by AB 2097).
    # Density x2: 1,360 / 2 = 680 sf per home -> 15,000 / 680 = 22.06 -> 22.
    # Envelope: 10,650 sf footprint x (2.4 + 1) stories = 36,210 / 1,062.5 = 34.08 -> 34.
    near = Lot(15_000, 100, 150, dist_major_transit_ft=1_000)
    r = run(base, "RM-32", near, transit_density_multiplier=2, transit_extra_stories=1)
    assert r.limits["lot_area_per_unit"] == 22 and r.limits["envelope"] == 34
    assert r.max_units == 22
    # The same lot 1 mile away is unchanged (parking binds at 9).
    far = Lot(15_000, 100, 150, dist_major_transit_ft=5_280)
    assert run(base, "RM-32", far, transit_density_multiplier=2, transit_extra_stories=1).max_units == 9


def test_transit_upzoning_scales_far_with_stories(base):
    # CO, 20,000 sf (100 x 200), near transit, +1 story: 4 -> 5 stories,
    # FAR 0.80 -> 0.80 x 5/4 = 1.0 -> 20,000 sf of floor area -> 18.8 -> 18 homes.
    r = run(base, "CO", Lot(20_000, 100, 200, dist_major_transit_ft=1_000), transit_extra_stories=1)
    assert r.limits["envelope"] == 18


def test_housing_in_cg(base):
    # CG doesn't allow housing today; with the lever it uses CL's standards,
    # 4 stories and FAR 0.80. 13,600 sf lot: 13,600 / 1,360 = 10 homes by density.
    lot = Lot(13_600, 80, 170, dist_major_transit_ft=1_000)
    assert run(base, "CG", lot).max_units == 0
    r = run(base, "CG", lot, housing_in_cg=True)
    assert r.max_units == 10 and r.binding_constraint == "lot_area_per_unit"


def test_more_adus(base):
    # RS-6 lot in a landmark district (no SB 9): ADU path 1 + 2 = 3 today; with
    # 3 ADU units allowed, 1 + 3 = 4.
    lot = Lot(7_200, 60, 120, overlays=("LD-1",), dist_major_transit_ft=9_000)
    assert run(base, "RS-6", lot).max_units == 3
    assert run(base, "RS-6", lot, adu_units_added=3).max_units == 4
