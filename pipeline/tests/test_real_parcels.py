"""Real lots checked by hand against each city's zoning code text
(ten in Pasadena, five in Glendale, six in Burbank, seven in Santa Monica, 29 in Los Angeles, nine in El Monte, nine in Inglewood, nine in West Hollywood, nine in Monrovia, nine in Santa Clarita).

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


# Burbank: Lot(..., dist_single_family_ft) as the last value: Burbank's height
# and coverage limits depend on distance to single-family zoning. See HAND_CHECKS.md.
BURBANK = [
    ("1065 E Grinnell Dr", "R-1", Lot(7850, 50.0, 157.3, (), 6062, 1, 0),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "parking": 6, "state_adu": 3, "state_sb9": 4}),
    ("438 S Lamer St", "R-1-H", Lot(10125, 75.0, 135.1, (), 7807, 1, 0),
     3, "state_law:adu", {"density": 1, "envelope": 3, "parking": 7, "state_adu": 3, "state_sb9": None}),
    ("1919 W Alameda Ave", "R-4", Lot(10583, 97.9, 109.0, (), 7380, 0, 21),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 11, "parking": 7}),
    ("520 E Orange Grove Ave", "R-4", Lot(12303, 101.7, 121.6, (), 2439, 0, 1428),
     8, "lot_area_per_unit", {"lot_area_per_unit": 8, "envelope": 24, "parking": None}),
    ("2907 W Burbank Blvd", "C-3", Lot(7861, 75.0, 105.5, (), 6227, 0, 20),
     5, "density", {"density": 5, "envelope": 19, "parking": 9}),
    ("300 E Olive Ave", "BCC-2", Lot(31000, 155.0, 200.1, (), 1175, None, 2517),
     62, "density", {"density": 62, "envelope": 134, "parking": None}),
]


@pytest.fixture(scope="module")
def burbank():
    rules = load_zone_rules(REPO / "cities" / "burbank" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", BURBANK, ids=[c[0] for c in BURBANK])
def test_hand_checked_burbank_parcel(burbank, address, zone, lot, max_units, binding, limits):
    rules, state, a = burbank
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


SANTA_MONICA = [
    ("1723 Robson Ave", "R1", Lot(5106, 50.0, 102.1, (), 5719, 1, 0),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "parking": 3, "state_adu": 3, "state_sb9": 4}),
    ("2013 18th St", "R2", Lot(7991, 50.0, 160.0, (), 2978, 3, 884),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 7, "parking": None}),
    ("2428 Beverley Ave", "OP2", Lot(7124, 50.1, 142.6, (), 1908, 4, 1449),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 6, "parking": None}),
    ("1438 15th St", "R3", Lot(7491, 50.0, 150.0, (), 1084, 7, 3596),
     6, "lot_area_per_unit", {"lot_area_per_unit": 6, "envelope": 10, "parking": None}),
    ("1501 17th St", "MUBL", Lot(7500, 50.0, 150.0, (), 677, 5, 3177),
     22, "envelope", {"envelope": 22, "parking": None}),
    ("728 Montana Ave", "NC-MOM", Lot(6006, 60.1, 100.1, (), 3475, 6, 255),
     14, "envelope", {"envelope": 14, "parking": None}),
    ("2452 Lincoln Blvd", "GC-LINCOLN", Lot(7518, 78.2, 110.1, (), 2054, 16, 524),
     17, "envelope", {"envelope": 17, "parking": None}),
]


@pytest.fixture(scope="module")
def santa_monica():
    rules = load_zone_rules(REPO / "cities" / "santa_monica" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", SANTA_MONICA, ids=[c[0] for c in SANTA_MONICA])
def test_hand_checked_santa_monica_parcel(santa_monica, address, zone, lot, max_units, binding, limits):
    rules, state, a = santa_monica
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


LOS_ANGELES = [
    ("10548 McClemont Ave", "R1", Lot(5088, 50.0, 101.9, ("RFA",), 25858, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "state_adu": 3, "state_sb9": 4}),
    ("16428 Gunther St", "RS", Lot(11183, 124.2, 201.0, (), 12509, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 4, "state_adu": 3, "state_sb9": 4}),
    ("9447 Haines Canyon Ave", "RE11", Lot(11183, 76.2, 158.1, (), 23562, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 4, "state_adu": 3, "state_sb9": 4}),
    ("14937 Bledsoe St", "RA", Lot(84415, 346.4, 423.7, ("K",), 7389, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 15, "state_adu": 3, "state_sb9": 4}),
    ("3400 Corinth Ave", "R1V2", Lot(6126, 60.0, 102.9, (), 1549, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 3, "parking": None, "state_adu": 3, "state_sb9": 4}),
    ("1224 Hauser Blvd", "R1R3", Lot(6076, 60.0, 101.4, ("RG", "O"), 3190, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "state_adu": 3, "state_sb9": 4}),
    ("10466 Glory Ave", "RE40", Lot(54198, 148.2, 366.9, ("K",), 28431, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 17, "state_adu": 3, "state_sb9": 4}),
    ("931 S Cochran Ave", "R1", Lot(7949, 57.3, 138.7, ("O", "HPOZ"), 957, 1),
     3, "state_law:adu", {"density": 1, "envelope": 3, "state_adu": 3, "state_sb9": None}),
    ("9300 Reverie Rd", "A1", Lot(296744, 617.6, 680.0, (), 19615, 1),
     3, "state_law:adu", {"density": 2, "lot_area_per_unit": 2, "envelope": 713, "state_adu": 3, "state_sb9": None}),
    ("8800 Wentworth St", "A2", Lot(70395, 225.6, 454.9, (), 21751, 1),
     3, "state_law:adu", {"density": 2, "lot_area_per_unit": 1, "envelope": 141, "state_adu": 3, "state_sb9": None}),
    ("2276 Ewing St", "R2", Lot(7502, 50.0, 150.6, (), 4923, 3),
     3, "state_law:adu", {"density": 2, "lot_area_per_unit": 3, "envelope": 13, "state_adu": 3}),
    ("1925 W 35th St", "RD1.5", Lot(6907, 50.0, 138.3, ("O",), 2884, 4),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 12, "parking": 7}),
    ("1501 S Dunsmuir Ave", "RD2", Lot(6100, 50.0, 122.1, ("O",), 2814, 3),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3, "envelope": 10}),
    ("7124 Flight Ave", "R3", Lot(7201, 60.0, 120.0, (), 4322, 6),
     7, "parking", {"lot_area_per_unit": 9, "envelope": 12, "parking": 7}),
    ("1069 S Cloverdale Ave", "R3", Lot(6905, 50.0, 138.1, ("O", "HPOZ"), 1107, 2),
     8, "lot_area_per_unit", {"lot_area_per_unit": 8, "envelope": 12, "parking": None}),
    ("2100 N Cahuenga Blvd", "R3-1XL", Lot(6638, 50.0, 132.9, (), 2867, 2),
     6, "parking", {"lot_area_per_unit": 8, "envelope": 7, "parking": 6}),
    ("11124 La Maida St", "R4-2", Lot(7749, 50.0, 155.1, (), 3463, 3),
     10, "parking", {"lot_area_per_unit": 19, "envelope": 27, "parking": 10}),
    ("7802 Foothill Blvd", "C2", Lot(10466, 79.4, 172.1, (), 23752, 0),
     11, "envelope", {"lot_area_per_unit": 26, "envelope": 11, "parking": 12}),
    ("4801 S Broadway", "C2", Lot(6740, 67.4, 100.1, ("CPIO",), 1699, None),
     6, "envelope", {"lot_area_per_unit": 16, "envelope": 6, "parking": None}),
    ("4615 Lankershim Blvd", "C2-2", Lot(6340, 50.0, 139.9, (), 4996, 1),
     10, "parking", {"lot_area_per_unit": 15, "envelope": 24, "parking": 10}),
    ("17827 Chatsworth St", "C1-1XL", Lot(6847, 50.0, 137.0, (), 11488, 1),
     6, "envelope", {"lot_area_per_unit": 8, "envelope": 6, "parking": 6}),
    ("3731 S Grand Ave", "CM", Lot(6907, 48.3, 143.2, ("CPIO",), 1700, None),
     6, "envelope", {"lot_area_per_unit": 8, "envelope": 6, "parking": None}),
    ("18428 Gault St", "M1", Lot(14995, 100.0, 150.0, (), 810, 0),
     0, "use_not_permitted", {}),
    ("960 N Broadway", "[DM5-SH2-5][CX1-FA]", Lot(8598, 65.0, 133.1, ("CPIO",), 429, 1),
     48, "envelope", {"envelope": 48, "parking": None}),
    ("770 S Grand Avenue", "[HB5-G1-5][CX3-FA]", Lot(129533, 314.5, 445.9, ("CPIO",), 61, 700),
     1097, "envelope", {"envelope": 1097}),
    ("3216 Eagle St", "[H3-MU3-3][RX2-2L]", Lot(5112, 41.0, 124.8, ("CPIO",), 2282, 1),
     3, "state_law:adu", {"density": 2, "envelope": 2, "state_adu": 3}),
    ("647 Camulos St", "[VN1-MU3-3][RX2-15]", Lot(5600, 40.0, 140.3, ("CPIO",), 1885, 2),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3, "envelope": 5}),
    ("2624 E Cesar E Chavez Ave", "[LM3-CC1-4][CX5-8]", Lot(4000, 40.0, 100.2, ("CPIO",), 1112, 1),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 5}),
    ("525 E 6th St", "[MB2-G1-5][IX1-FA]", Lot(6019, 60.1, 100.2, ("CPIO",), 813, 0),
     16, "envelope", {"envelope": 16}),
]


@pytest.fixture(scope="module")
def los_angeles():
    rules = load_zone_rules(REPO / "cities" / "los_angeles" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", LOS_ANGELES, ids=[c[0] for c in LOS_ANGELES])
def test_hand_checked_los_angeles_parcel(los_angeles, address, zone, lot, max_units, binding, limits):
    rules, state, a = los_angeles
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


EL_MONTE = [
    ("11421 Elmcrest St", "R-1A", Lot(9546, 60.0, 160.0, (), 6323, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "state_adu": 3, "state_sb9": 4}),
    ("4726 Maxson Rd", "R-1B", Lot(13472, 73.0, 201.8, (), 9796, 2),
     4, "state_law:sb9", {"lot_area_per_unit": 1, "envelope": 3, "state_sb9": 4}),
    ("12043 Cherrylee Dr", "R-1C", Lot(33763, 133.4, 254.9, (), 11308, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 6, "state_sb9": 4}),
    ("11066 McGirk Ave", "R-2", Lot(6010, 60.0, 102.4, (), 3919, 1),
     3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 2, "state_adu": 3}),
    ("3641 Durfee Ave", "R-3", Lot(22937, 81.4, 283.0, (), 3609, 13),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 10}),
    ("9743 Valley Blvd", "R-4", Lot(42178, 100.1, 634.9, (), 4312, None),
     23, "envelope", {"lot_area_per_unit": 24, "envelope": 23}),
    ("3141 Peck Rd", "C-3", Lot(52139, 195.5, 367.3, (), 2176, 0),
     29, "envelope", {"lot_area_per_unit": 35, "envelope": 29, "parking": None}),
    ("2822 Durfee Ave", "MMU", Lot(34445, 140.0, 248.9, (), 2476, 0),
     24, "lot_area_per_unit", {"lot_area_per_unit": 24, "parking": None}),
    ("12315 Dahlia Ave", "M-1", Lot(11605, 80.2, 148.0, (), 2353, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def el_monte():
    rules = load_zone_rules(REPO / "cities" / "el_monte" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", EL_MONTE, ids=[c[0] for c in EL_MONTE])
def test_hand_checked_el_monte_parcel(el_monte, address, zone, lot, max_units, binding, limits):
    rules, state, a = el_monte
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


INGLEWOOD = [
    ("9120 S 8th Ave", "R-1", Lot(8505, 63.0, 135.2, (), 2015, 1),
     4, "state_law:sb9", {"density": 1, "parking": None, "state_adu": 3, "state_sb9": 4}),
    ("3249 W 108th St", "R-2", Lot(6066, 40.0, 151.7, (), 2712, 1),
     3, "state_law:adu", {"lot_area_per_unit": 2, "state_adu": 3}),
    ("3714 W 105th St", "R-2", Lot(14588, 91.0, 160.3, (), 3927, 2),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5}),
    ("500 E Fairview Blvd", "R-2A", Lot(12771, 80.6, 175.4, (), 2034, 4),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3}),
    ("134 E Spruce Ave", "R-3", Lot(9625, 50.0, 192.5, (), 930, 9),
     6, "lot_area_per_unit", {"lot_area_per_unit": 6, "parking": None}),
    ("709 Venice Way", "R-3", Lot(18503, 80.0, 234.5, (), 3405, 5),
     16, "lot_area_per_unit", {"lot_area_per_unit": 16}),
    ("816 N Market St", "R-4", Lot(12476, 50.0, 250.2, (), 902, 6),
     9, "lot_area_per_unit", {"lot_area_per_unit": 9, "parking": None}),
    ("910 Myrtle Ave", "R-M", Lot(12260, 52.5, 234.1, (), 1110, 14),
     8, "lot_area_per_unit", {"lot_area_per_unit": 8, "parking": None}),
    ("400 E Kelso St", "C-2", Lot(31107, 163.7, 190.1, (), 947, 1),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def inglewood():
    rules = load_zone_rules(REPO / "cities" / "inglewood" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", INGLEWOOD, ids=[c[0] for c in INGLEWOOD])
def test_hand_checked_inglewood_parcel(inglewood, address, zone, lot, max_units, binding, limits):
    rules, state, a = inglewood
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


WEST_HOLLYWOOD = [
    ("419 Huntley Dr", "R1B", Lot(6004, 49.9, 121.8, (), 1687, 2),
     4, "state_law:sb9", {"lot_area_per_unit": 2, "envelope": 2, "state_sb9": 4}),
    ("1249 N Ogden Dr", "R2", Lot(7484, 51.4, 148.5, (), 1295, 10),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3, "parking": None}),
    ("1015 N Stanley Ave", "R3B", Lot(6495, 50.7, 129.1, (), 1485, 9),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5}),
    ("1217 Havenhurst Dr", "R4A", Lot(15240, 80.6, 190.2, (), 1908, 19),
     17, "lot_area_per_unit", {"lot_area_per_unit": 17}),
    ("1342 N Crescent Heights Blvd", "R4B", Lot(14983, 79.5, 189.5, (), 1373, 12),
     17, "lot_area_per_unit", {"lot_area_per_unit": 17}),
    ("1019 N Fairfax Ave", "CC1", Lot(6672, 47.0, 143.2, (), 541, 0),
     9, "envelope", {"envelope": 9, "parking": None}),
    ("7906 Santa Monica Blvd", "CC2", Lot(9375, 75.0, 125.5, (), 120, 0),
     17, "envelope", {"envelope": 17}),
    ("369 N Robertson Blvd", "CN1", Lot(13343, 105.0, 195.2, (), 2304, 0),
     12, "envelope", {"envelope": 12}),
    ("500 N Doheny Dr", "CN2", Lot(5174, 53.8, 96.9, (), 2325, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def west_hollywood():
    rules = load_zone_rules(REPO / "cities" / "west_hollywood" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", WEST_HOLLYWOOD, ids=[c[0] for c in WEST_HOLLYWOOD])
def test_hand_checked_west_hollywood_parcel(west_hollywood, address, zone, lot, max_units, binding, limits):
    rules, state, a = west_hollywood
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


MONROVIA = [
    ("438 Kirkwood Ln", "RL", Lot(7093, 84.3, 118.7, (), 9387, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "parking": 4, "state_sb9": 4}),
    ("523 W Hillcrest Blvd", "RE", Lot(19141, 70.2, 289.5, (), 7295, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 4, "state_sb9": 4}),
    ("Unaddressed RF lot", "RF", Lot(55280, 263.7, 444.3, (), 10363, None),
     4, "state_law:sb9", {"density": 1, "envelope": 9, "state_sb9": 4}),
    ("816 Bonita St", "RM3500", Lot(8252, 50.0, 165.1, (), 4200, 2),
     3, "state_law:adu", {"lot_area_per_unit": 2, "envelope": 3, "state_adu": 3}),
    ("1703 Alamitas Ave", "RM4000", Lot(16421, 77.4, 232.8, (), 2767, 1),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 6}),
    ("856 W Olive Ave", "RM/RH", Lot(17297, 142.6, 179.4, (), 3443, 8),
     11, "parking", {"lot_area_per_unit": None, "envelope": 12, "parking": 11}),
    ("526 Fano St D", "RM/RH", Lot(2753, 55.0, 56.7, (), 2120, 1),
     3, "state_law:adu", {"lot_area_per_unit": 1, "state_adu": 3}),
    ("543 W Duarte Rd", "RH", Lot(23281, 100.5, 251.3, (), 2352, 10),
     16, "envelope", {"lot_area_per_unit": None, "envelope": 16, "parking": None}),
    ("950 W Foothill Blvd", "NC", Lot(19596, 101.7, 193.0, (), 3800, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def monrovia():
    rules = load_zone_rules(REPO / "cities" / "monrovia" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", MONROVIA, ids=[c[0] for c in MONROVIA])
def test_hand_checked_monrovia_parcel(monrovia, address, zone, lot, max_units, binding, limits):
    rules, state, a = monrovia
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


SANTA_CLARITA = [
    ("19771 Terri Dr", "UR2", Lot(22211, 154.3, 158.0, (), 3937, None),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("23453 Darcy Ln", "UR1", Lot(9287, 153.6, 191.0, (), 8183, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("15906 Pashley St", "NU5", Lot(109170, 330.1, 332.5, (), 16929, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("26476 Township St", "UR3", Lot(7736, 69.0, 116.5, (), 3615, 1),
     3, "state_law:adu", {"lot_area_per_unit": 1, "state_adu": 3}),
    ("28494 N Herrera Street", "UR4", Lot(31130, 188.9, 193.7, (), 19518, 14),
     12, "lot_area_per_unit", {"lot_area_per_unit": 12}),
    ("27905 Tyler Ln", "UR5", Lot(61197, 171.1, 403.5, (), 6956, 52),
     42, "lot_area_per_unit", {"lot_area_per_unit": 42}),
    ("23310 Cinema Dr", "MX-C", Lot(40532, 171.9, 283.5, (), 6061, 1),
     27, "lot_area_per_unit", {"lot_area_per_unit": 27}),
    ("22432 12th St", "MX-N", Lot(4869, 49.5, 100.0, (), 1454, 0),
     3, "state_law:adu", {"lot_area_per_unit": 2, "parking": None, "state_adu": 3}),
    ("17737 Sierra Hwy", "CC", Lot(14644, 119.3, 123.5, (), 10003, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def santa_clarita():
    rules = load_zone_rules(REPO / "cities" / "santa_clarita" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", SANTA_CLARITA, ids=[c[0] for c in SANTA_CLARITA])
def test_hand_checked_santa_clarita_parcel(santa_clarita, address, zone, lot, max_units, binding, limits):
    rules, state, a = santa_clarita
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"
