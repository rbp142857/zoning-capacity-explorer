"""Real lots checked by hand against each city's zoning code text
(ten in Pasadena, five in Glendale).

The arithmetic for each is written out in docs/HAND_CHECKS.md. Inputs are the
pipeline's values for these lots (area, width, depth, overlays, distance to
transit, existing homes), copied here so the test doesn't need the data
download. If a change to the engine or rule files alters any of these
answers, this test fails: check the new answer against the code text and
update HAND_CHECKS.md if the change is right.
"""

from pathlib import Path

import pytest

from zce.engine import EngineAssumptions, Lot, compute_capacity
from zce.rules.schema import load_state_overrides, load_zone_rules

REPO = Path(__file__).resolve().parents[2]

# (address, zone, Lot(area, width, depth, overlays, dist_transit, existing),
#  expected max homes, binding constraint, {limit: value})
CASES = [
    ("2314 E Mountain St", "RS-6", Lot(7252, 50.0, 145.1, (), 4643, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "parking": 5, "state_adu": 3, "state_sb9": 4}),
    ("1776 Orangewood St", "RS-6", Lot(6196, 49.5, 125.6, ("LD-25",), 3471, 1),
     3, "state_law:adu", {"density": 1, "envelope": 2, "parking": 4, "state_adu": 3}),
    ("1510 Sierra Madre Villa Ave", "RS-2", Lot(21474, 110.2, 195.1, (), 7831, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 5, "parking": 16, "state_sb9": 4}),
    ("667 N Oakland Ave", "RM-12", Lot(8417, 60.1, 140.3, (), 3326, 1),
     3, "state_law:adu", {"density": 2, "envelope": 5, "parking": 6, "state_adu": 3}),
    ("1060 E Orange Grove Blvd", "RM-16", Lot(11676, 103.2, 114.0, (), 2186, 4),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 14, "parking": None}),
    ("534 N Los Robles Ave", "RM-32", Lot(12192, 62.0, 196.9, (), 3056, 10),
     7, "parking", {"lot_area_per_unit": 9, "envelope": 18, "parking": 7}),
    ("233 N Wilson Ave", "RM-32", Lot(6476, 52.0, 125.0, ("PK",), 1040, 1),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 8, "parking": None}),
    ("180 S Catalina Ave", "RM-48", Lot(10445, 60.1, 174.1, (), 2511, 10),
     11, "lot_area_per_unit", {"lot_area_per_unit": 11, "envelope": 20, "parking": None}),
    ("1864 E Washington Blvd", "CL", Lot(10003, 100.0, 100.6, (), 5983, 0),
     6, "envelope", {"lot_area_per_unit": 7, "envelope": 6, "parking": 7}),
    ("960 N Lake Ave", "CO", Lot(9242, 50.0, 185.0, ("SP-1a",), 3841, 0),
     6, "envelope", {"lot_area_per_unit": 10, "envelope": 6, "parking": 7}),
]


@pytest.fixture(scope="module")
def pasadena():
    rules = load_zone_rules(REPO / "cities" / "pasadena" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", CASES, ids=[c[0] for c in CASES])
def test_hand_checked_parcel(pasadena, address, zone, lot, max_units, binding, limits):
    rules, state, a = pasadena
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


# Glendale: (address, zone, Lot, expected max, binding, limits). See HAND_CHECKS.md.
GLENDALE = [
    ("1248 Thompson Ave", "R1", Lot(6837, 42.7, 161.5, (), 6865, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 1, "parking": 3, "state_adu": 3, "state_sb9": 4}),
    ("1056 Kildonan Dr", "R1R", Lot(10560, 92.5, 115.3, (), 10456, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "parking": 5, "state_sb9": 4}),
    ("651 Salem St", "R-2250", Lot(7056, 50.9, 139.3, (), 3372, 1),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3, "envelope": 5, "parking": 5}),
    ("325 N Howard St", "R-1250", Lot(14999, 99.6, 151.4, (), 1674, 18),
     14, "lot_area_per_unit", {"lot_area_per_unit": 14, "envelope": 16, "parking": None}),
    ("1109 N Brand Blvd", "C3", Lot(8709, 40.0, 218.4, (), 5478, 0),
     6, "lot_area_per_unit", {"lot_area_per_unit": 6, "envelope": 18, "parking": 8}),
]


@pytest.fixture(scope="module")
def glendale():
    rules = load_zone_rules(REPO / "cities" / "glendale" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", GLENDALE, ids=[c[0] for c in GLENDALE])
def test_hand_checked_glendale_parcel(glendale, address, zone, lot, max_units, binding, limits):
    rules, state, a = glendale
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"
