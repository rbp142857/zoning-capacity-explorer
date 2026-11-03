"""Real lots checked by hand against each city's zoning code text
(ten in Pasadena, five in Glendale, six in Burbank, seven in Santa Monica, 29 in Los Angeles, nine in El Monte, nine in Inglewood, nine in West Hollywood, nine in Monrovia, nine in Santa Clarita, seven in Duarte, seven in Long Beach, five in Lancaster, seven in Gardena, five in Norwalk, three in Santa Fe Springs, six in Whittier, five in Arcadia, three in South Gate, five in Culver City, five in Montebello, three in Rolling Hills Estates, six in West Covina, six in Westlake Village, six in Alhambra, eight in Palmdale, seven in Carson, six in Azusa, five in Lomita, seven in Hawthorne, seven in San Gabriel, six in Monterey Park, ten in Agoura Hills, 14 in Torrance, ten in Artesia, nine in Avalon, ten in Baldwin Park, eight in Bell, nine in Bell Gardens, nine in Bellflower, seven in Beverly Hills, six in Bradbury, ten in Calabasas, seven in Cerritos, eight in Commerce, nine in Compton, ten in Claremont, ten in Covina, eight in Cudahy, nine in Diamond Bar).

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


DUARTE = [
    ("1835 Bradbury Ave", "R1", Lot(6415, 59.7, 108.5, (), 4554, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("2621 Starcrest Dr", "R1A", Lot(8774, 64.0, 161.4, (), 9165, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("2228 High Mesa Dr", "R1D", Lot(19505, 140.0, 170.2, (), 8670, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("1709 3rd St", "R2", Lot(7412, 59.3, 125.7, (), 3081, 1),
     3, "state_law:adu", {"density": 2, "state_adu": 3}),
    ("1392 3rd St", "R3", Lot(6424, 60.5, 106.7, (), 3699, 4),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3, "envelope": 8}),
    ("1709 Huntington Dr", "R4", Lot(28287, 106.2, 267.7, (), 2658, 0),
     18, "lot_area_per_unit", {"lot_area_per_unit": 18}),
    ("1475 Huntington Dr", "CG", Lot(16967, 119.8, 148.8, (), 3198, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def duarte():
    rules = load_zone_rules(REPO / "cities" / "duarte" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", DUARTE, ids=[c[0] for c in DUARTE])
def test_hand_checked_duarte_parcel(duarte, address, zone, lot, max_units, binding, limits):
    rules, state, a = duarte
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


LONG_BEACH = [
    ("5507 E Pageantry St", "R-1-N", Lot(5214, 52.8, 99.6, (), 11094, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "state_sb9": 4}),
    ("5521 E Sorrento Dr", "R-1-S", Lot(3287, 40.1, 82.4, (), 5899, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 3, "state_sb9": 4}),
    ("771 Freeman Ave", "R-2-N", Lot(6754, 50.0, 135.1, (), 3509, 4),
     3, "state_law:adu", {"density": 2, "lot_area_per_unit": 2, "envelope": 3, "state_adu": 3}),
    ("3901 E 4th St", "R-3-T", Lot(38283, 128.0, 300.0, (), 5686, 1),
     15, "lot_area_per_unit", {"lot_area_per_unit": 15}),
    ("3637 E Ocean Blvd", "R-4-R", Lot(11217, 55.1, 217.7, (), 7411, 8),
     7, "lot_area_per_unit", {"lot_area_per_unit": 7}),
    ("2907 Claremore Ln", "R-4-R", Lot(25626, 155.6, 285.2, (), 17496, 8),
     17, "lot_area_per_unit", {"lot_area_per_unit": 17}),
    ("3737 Atlantic Ave", "R-4-N", Lot(58572, 211.0, 278.5, (), 3652, 169),
     60, "lot_area_per_unit", {"lot_area_per_unit": 60}),
]


@pytest.fixture(scope="module")
def long_beach():
    rules = load_zone_rules(REPO / "cities" / "long_beach" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", LONG_BEACH, ids=[c[0] for c in LONG_BEACH])
def test_hand_checked_long_beach_parcel(long_beach, address, zone, lot, max_units, binding, limits):
    rules, state, a = long_beach
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


LANCASTER = [
    ("1132 Langhorn St", "R-7000", Lot(6307, 60.0, 105.5, (), 8015, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("1723 Granville Way", "R-10,000", Lot(10975, 91.4, 128.2, (), 14329, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("43710 Ryckebosch Ln", "RR-1", Lot(40232, 237.0, 239.6, (), 22355, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("45537 Corkwood Ave", "MDR", Lot(6000, 60.0, 101.6, (), 5315, 2),
     3, "state_law:adu", {"lot_area_per_unit": 2, "state_adu": 3}),
    ("902 W Newgrove St", "HDR", Lot(8232, 54.9, 150.5, (), 3336, 1),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5}),
]


@pytest.fixture(scope="module")
def lancaster():
    rules = load_zone_rules(REPO / "cities" / "lancaster" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", LANCASTER, ids=[c[0] for c in LANCASTER])
def test_hand_checked_lancaster_parcel(lancaster, address, zone, lot, max_units, binding, limits):
    rules, state, a = lancaster
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


GARDENA = [
    ("1911 W 160th St", "R1", Lot(5006, 50.0, 100.2, (), 12911, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("1658 W 166th St", "R3", Lot(7500, 50.0, 150.1, (), 13935, 4),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3}),
    ("14807 S Normandie Ave", "R4", Lot(18438, 132.0, 140.7, (), 11723, 19),
     11, "lot_area_per_unit", {"lot_area_per_unit": 11}),
    ("15210 S Ave A", "R4", Lot(30894, 106.0, 291.5, (), 12928, 18),
     21, "lot_area_per_unit", {"lot_area_per_unit": 21}),
    ("16321 S Western Ave", "C3-HO-5", Lot(12904, 100.0, 129.6, (), 13228, 0),
     14, "lot_area_per_unit", {"lot_area_per_unit": 14}),
    ("1957 W 144th St", "C3-HO-6", Lot(9774, 70.0, 140.0, (), 9019, 0),
     14, "parking", {"lot_area_per_unit": 15, "parking": 14}),
    ("1440 W 178th St", "M1-HO-4", Lot(17182, 96.5, 183.0, (), 15910, 0),
     11, "lot_area_per_unit", {"lot_area_per_unit": 11}),
]


@pytest.fixture(scope="module")
def gardena():
    rules = load_zone_rules(REPO / "cities" / "gardena" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", GARDENA, ids=[c[0] for c in GARDENA])
def test_hand_checked_gardena_parcel(gardena, address, zone, lot, max_units, binding, limits):
    rules, state, a = gardena
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


NORWALK = [
    ("13508 Leibacher Ave", "R-1", Lot(5196, 51.9, 100.6, (), 1793, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 1, "parking": None, "state_sb9": 4}),
    ("11037 Barnwall St", "R-2", Lot(15059, 100.0, 150.7, (), 8020, 10),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 6}),
    ("12165 Pine St", "R-3", Lot(6791, 48.9, 140.9, (), 5838, 4),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3, "envelope": 3}),
    ("12226 Sproul St", "R-3", Lot(11157, 74.5, 150.1, (), 4522, 6),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 5}),
    ("11433 Excelsior Dr", "R-2", Lot(43864, 110.0, 399.0, (), 7502, 16),
     16, "lot_area_per_unit", {"lot_area_per_unit": 16}),
]


@pytest.fixture(scope="module")
def norwalk():
    rules = load_zone_rules(REPO / "cities" / "norwalk" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", NORWALK, ids=[c[0] for c in NORWALK])
def test_hand_checked_norwalk_parcel(norwalk, address, zone, lot, max_units, binding, limits):
    rules, state, a = norwalk
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


SANTA_FE_SPRINGS = [
    ("11030 Davenrich St", "R-1", Lot(7471, 69.8, 134.4, (), 6442, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 5, "state_sb9": 4}),
    ("10800 Pioneer Blvd", "R-3", Lot(193333, 390.1, 623.6, (), 8177, 107),
     110, "lot_area_per_unit", {"lot_area_per_unit": 110}),
    ("12341 Heritage Springs Dr", "R-3", Lot(59585, 254.7, 628.7, (), 9298, 15),
     34, "lot_area_per_unit", {"lot_area_per_unit": 34}),
]


@pytest.fixture(scope="module")
def santa_fe_springs():
    rules = load_zone_rules(REPO / "cities" / "santa_fe_springs" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", SANTA_FE_SPRINGS, ids=[c[0] for c in SANTA_FE_SPRINGS])
def test_hand_checked_santa_fe_springs_parcel(santa_fe_springs, address, zone, lot, max_units, binding, limits):
    rules, state, a = santa_fe_springs
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


WHITTIER = [
    ("14854 Carnell St", "R-1", Lot(15981, 50.0, 325.0, (), 17437, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("13719 Mar Vista St", "R-2", Lot(15104, 83.0, 184.2, (), 19395, 9),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5}),
    ("7703 Comstock Ave", "R-3", Lot(7035, 50.5, 140.4, (), 17326, 8),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4}),
    ("7727 Newlin Ave", "R-4", Lot(5965, 48.8, 122.8, (), 16960, 3),
     3, "state_law:adu", {"lot_area_per_unit": 2, "state_adu": 3}),
    ("7723 Milton Ave", "R-4", Lot(7196, 51.5, 140.2, (), 17180, 8),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5}),
    ("8930 Painter Ave", "R-4", Lot(119792, 285.1, 421.6, (), 15554, 92),
     95, "lot_area_per_unit", {"lot_area_per_unit": 95}),
]


@pytest.fixture(scope="module")
def whittier():
    rules = load_zone_rules(REPO / "cities" / "whittier" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", WHITTIER, ids=[c[0] for c in WHITTIER])
def test_hand_checked_whittier_parcel(whittier, address, zone, lot, max_units, binding, limits):
    rules, state, a = whittier
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


ARCADIA = [
    ("45 W Magna Vista Ave", "R-1", Lot(11655, 61.0, 192.3, (), 5538, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 4, "state_sb9": 4}),
    ("462 Arbolada Dr", "R", Lot(20494, 176.3, 176.8, (), 6340, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 7, "state_sb9": 4}),
    ("307 Genoa St", "R-2", Lot(10144, 68.0, 149.5, (), 4046, 2),
     3, "state_law:adu", {"lot_area_per_unit": 2, "state_adu": 3}),
    ("135 Diamond St", "R-3", Lot(7966, 49.5, 161.1, (), 2514, 4),
     7, "lot_area_per_unit", {"lot_area_per_unit": 7, "envelope": 10}),
    ("437 S Baldwin Ave", "R-3-R", Lot(11000, 50.1, 219.9, (), 5681, 5),
     5, "envelope", {"lot_area_per_unit": 7, "envelope": 5}),
]


@pytest.fixture(scope="module")
def arcadia():
    rules = load_zone_rules(REPO / "cities" / "arcadia" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", ARCADIA, ids=[c[0] for c in ARCADIA])
def test_hand_checked_arcadia_parcel(arcadia, address, zone, lot, max_units, binding, limits):
    rules, state, a = arcadia
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


SOUTH_GATE = [
    ("8976 Annetta Ave", "NL", Lot(5108, 40.1, 128.2, (), 1557, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("9739 Elizabeth Ave", "NM", Lot(4177, 30.0, 139.6, (), 864, 2),
     3, "state_law:adu", {"lot_area_per_unit": 1, "state_adu": 3}),
    ("4100 Firestone Blvd", "NM", Lot(18030, 120.2, 150.8, (), 228, None),
     8, "lot_area_per_unit", {"lot_area_per_unit": 8}),
]


@pytest.fixture(scope="module")
def south_gate():
    rules = load_zone_rules(REPO / "cities" / "south_gate" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", SOUTH_GATE, ids=[c[0] for c in SOUTH_GATE])
def test_hand_checked_south_gate_parcel(south_gate, address, zone, lot, max_units, binding, limits):
    rules, state, a = south_gate
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


CULVER_CITY = [
    ("10826 Franklin Ave", "R1", Lot(4987, 47.5, 105.1, (), 3482, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "parking": None, "state_sb9": 4}),
    ("4174 Baldwin Ave", "R2", Lot(6755, 50.0, 135.0, (), 3395, 2),
     3, "state_law:adu", {"density": 2, "envelope": 3, "state_adu": 3}),
    ("3845 Sawtelle Blvd", "RLD", Lot(6299, 50.1, 125.9, (), 1103, 2),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5, "parking": None}),
    ("4450 Overland Ave", "RMD", Lot(9504, 70.0, 166.7, (), 3337, 8),
     10, "lot_area_per_unit", {"lot_area_per_unit": 10, "parking": None}),
    ("6060 Buckingham Pkwy", "RHD", Lot(35407, 157.2, 244.7, (), 2168, 50),
     56, "lot_area_per_unit", {"lot_area_per_unit": 56}),
]


@pytest.fixture(scope="module")
def culver_city():
    rules = load_zone_rules(REPO / "cities" / "culver_city" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", CULVER_CITY, ids=[c[0] for c in CULVER_CITY])
def test_hand_checked_culver_city_parcel(culver_city, address, zone, lot, max_units, binding, limits):
    rules, state, a = culver_city
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


MONTEBELLO = [
    ("1319 Via Camille", "R-1", Lot(8689, 65.6, 167.9, (), 5953, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("641 N Maple Ave", "R-A", Lot(6137, 70.1, 90.3, (), 5603, 1),
     4, "state_law:sb9", {"density": 1, "state_sb9": 4}),
    ("817 Palm Pl", "R-2", Lot(4982, 44.9, 115.0, (), 5563, 1),
     3, "state_law:adu", {"lot_area_per_unit": 1, "state_adu": 3}),
    ("216 N 4th St", "R-3", Lot(6753, 50.0, 135.2, (), 6606, 4),
     3, "state_law:adu", {"lot_area_per_unit": 2, "state_adu": 3}),
    ("633 N Taylor Ave", "R-4", Lot(48727, 203.5, 239.7, (), 6059, 41),
     24, "lot_area_per_unit", {"lot_area_per_unit": 24}),
]


@pytest.fixture(scope="module")
def montebello():
    rules = load_zone_rules(REPO / "cities" / "montebello" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", MONTEBELLO, ids=[c[0] for c in MONTEBELLO])
def test_hand_checked_montebello_parcel(montebello, address, zone, lot, max_units, binding, limits):
    rules, state, a = montebello
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


ROLLING_HILLS_ESTATES = [
    ("78 Dapplegray Ln", "RA-20,000", Lot(19571, 110.7, 251.9, (), 16140, 1),
     4, "state_law:sb9", {"density": 1, "state_adu": 3, "state_sb9": 4}),
    ("5228 Bluemound Rd", "RA-10,000", Lot(7262, 66.1, 110.1, (), 28781, 1),
     4, "state_law:sb9", {"density": 1, "state_adu": 3, "state_sb9": 4}),
    ("2 Strawberry Ln", "RAE", Lot(49621, 185.0, 348.7, (), 18183, 1),
     4, "state_law:sb9", {"density": 1, "state_adu": 3, "state_sb9": 4}),
]


@pytest.fixture(scope="module")
def rolling_hills_estates():
    rules = load_zone_rules(REPO / "cities" / "rolling_hills_estates" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", ROLLING_HILLS_ESTATES, ids=[c[0] for c in ROLLING_HILLS_ESTATES])
def test_hand_checked_rolling_hills_estates_parcel(rolling_hills_estates, address, zone, lot, max_units, binding, limits):
    rules, state, a = rolling_hills_estates
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


WEST_COVINA = [
    ("521 S Astell Ave", "R-1", Lot(9408, 60.4, 157.2, (), 8448, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 3, "state_sb9": 4}),
    ("3330 E Holt Ave", "R-A", Lot(15109, 133.0, 160.7, (), 9633, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 4, "state_sb9": 4}),
    ("1912 Tanglewood Dr", "MF-8", Lot(5724, 76.4, 83.1, (), 5748, 2),
     3, "state_law:adu", {"lot_area_per_unit": 1, "state_adu": 3}),
    ("1799 Aspen Village Way", "MF-15", Lot(28350, 156.3, 222.2, (), 9249, 7),
     9, "lot_area_per_unit", {"lot_area_per_unit": 9}),
    ("223 S Bandy Ave", "MF-20", Lot(6759, 62.9, 107.8, (), 7520, 3),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3}),
    ("2117 E Garvey Ave N", "MF-45", Lot(6200, 66.3, 94.7, (), 5423, 1),
     6, "lot_area_per_unit", {"lot_area_per_unit": 6}),
]


@pytest.fixture(scope="module")
def west_covina():
    rules = load_zone_rules(REPO / "cities" / "west_covina" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", WEST_COVINA, ids=[c[0] for c in WEST_COVINA])
def test_hand_checked_west_covina_parcel(west_covina, address, zone, lot, max_units, binding, limits):
    rules, state, a = west_covina
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


WESTLAKE_VILLAGE = [
    ("6156 Hedgewall Dr", "R-1", Lot(8256, 75.1, 110.5, (), 48513, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 7, "state_sb9": 4}),
    ("6148 Hedgewall Dr", "R-1", Lot(7803, 71.0, 110.5, (), 48556, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 6, "state_sb9": 4}),
    ("3956 Freshwind Cir", "RPD", Lot(10390, 112.0, 137.4, (), 54399, 1),
     3, "state_law:adu", {"density": 1, "envelope": 10, "state_adu": 3}),
    ("1 Sherwood Dr", "MHP", Lot(5595, 75.5, 94.6, (), 58285, 1),
     3, "state_law:adu", {"density": 1, "envelope": 3, "state_adu": 3}),
    ("5711 Corsa Ave", "SP No. 2-Mixed-Use Corsa", Lot(56092, 254.7, 413.8, (), 52113, 0),
     25, "lot_area_per_unit", {"lot_area_per_unit": 25, "envelope": 63}),
    ("5701 Lindero Canyon Rd", "SP No. 2-Mixed-Use Lindero", Lot(330577, 612.1, 619.7, (), 52028, 0),
     242, "lot_area_per_unit", {"lot_area_per_unit": 242, "envelope": 373}),
]


@pytest.fixture(scope="module")
def westlake_village():
    rules = load_zone_rules(REPO / "cities" / "westlake_village" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", WESTLAKE_VILLAGE, ids=[c[0] for c in WESTLAKE_VILLAGE])
def test_hand_checked_westlake_village_parcel(westlake_village, address, zone, lot, max_units, binding, limits):
    rules, state, a = westlake_village
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


ALHAMBRA = [
    ("2600 Orange Grove Ave", "R-1", Lot(6137, 70.6, 115.5, (), 3841, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "state_sb9": 4}),
    ("2040 S 3rd St", "R-2", Lot(7015, 47.6, 150.7, (), 3035, 2),
     3, "state_law:adu", {"lot_area_per_unit": 2, "envelope": 8, "state_adu": 3}),
    ("1850 Garvey Ave", "R-3", Lot(7925, 63.1, 136.7, (), 3988, 3),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4}),
    ("2916 W Ramona Rd", "R-3", Lot(12451, 103.2, 122.1, (), 3579, 12),
     11, "parking", {"lot_area_per_unit": 12, "parking": 11}),
    ("150 N Garfield Ave", "CBD", Lot(11332, 66.9, 170.7, (), 2768, 0),
     15, "parking", {"lot_area_per_unit": 16, "parking": 15}),
    ("1129 E Main St", "EMC", Lot(7410, 49.5, 150.4, (), 6769, 0),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5}),
]


@pytest.fixture(scope="module")
def alhambra():
    rules = load_zone_rules(REPO / "cities" / "alhambra" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", ALHAMBRA, ids=[c[0] for c in ALHAMBRA])
def test_hand_checked_alhambra_parcel(alhambra, address, zone, lot, max_units, binding, limits):
    rules, state, a = alhambra
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


PALMDALE = [
    ("4648 Paseo Hermoso", "SFR3", Lot(7755, 64.8, 119.9, (), 30569, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 7, "state_sb9": 4}),
    ("40332 Tesoro Ln", "SFR1", Lot(24183, 143.1, 170.2, (), 21380, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 13, "state_sb9": 4}),
    ("2637 E Avenue Q4", "RN1", Lot(11402, 75.0, 152.3, (), 11498, 1),
     3, "state_law:adu", {"lot_area_per_unit": 2, "state_adu": 3}),
    ("39039 Yucca Tree St", "RN2", Lot(11204, 75.2, 150.5, (), 8739, 1),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5}),
    ("1623 Watling Dr", "RN3", Lot(19348, 125.0, 158.7, (), 13146, 1),
     13, "lot_area_per_unit", {"lot_area_per_unit": 13}),
    ("38533 11th St E", "RN4", Lot(22134, 74.5, 297.1, (), 3898, 1),
     25, "lot_area_per_unit", {"lot_area_per_unit": 25}),
    ("1358 E Palmdale Blvd", "MU1", Lot(17794, 130.0, 139.0, (), 6247, 0),
     8, "lot_area_per_unit", {"lot_area_per_unit": 8}),
    ("803 W Palmdale Blvd", "MEDFX", Lot(21802, 140.3, 168.4, (), 8400, 0),
     15, "lot_area_per_unit", {"lot_area_per_unit": 15}),
]


@pytest.fixture(scope="module")
def palmdale():
    rules = load_zone_rules(REPO / "cities" / "palmdale" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", PALMDALE, ids=[c[0] for c in PALMDALE])
def test_hand_checked_palmdale_parcel(palmdale, address, zone, lot, max_units, binding, limits):
    rules, state, a = palmdale
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


CARSON = [
    ("559 E 169th St", "RS", Lot(5530, 54.9, 100.7, (), 13034, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 5, "state_sb9": 4}),
    ("118 W 234th St", "RM (8)", Lot(6424, 50.8, 131.8, (), 8190, 1),
     3, "state_law:adu", {"lot_area_per_unit": 1, "state_adu": 3}),
    ("750 Alondra Blvd", "RM (12)", Lot(12158, 94.2, 143.9, (), 12016, 0),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3}),
    ("21105 S Santa Fe Ave", "RM (25)", Lot(8772, 76.7, 138.7, (), 3744, 1),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5}),
    ("2543 E Carson St", "RM (25)", Lot(39819, 107.6, 500.4, (), 6885, 12),
     23, "lot_area_per_unit", {"lot_area_per_unit": 23}),
    ("714 E Carson St", "MU-CS", Lot(51680, 194.0, 270.3, (), 14530, 86),
     42, "lot_area_per_unit", {"lot_area_per_unit": 42}),
    ("440 E Sepulveda Blvd", "MU-SB", Lot(18595, 94.0, 200.0, (), 6178, 11),
     11, "lot_area_per_unit", {"lot_area_per_unit": 11}),
]


@pytest.fixture(scope="module")
def carson():
    rules = load_zone_rules(REPO / "cities" / "carson" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", CARSON, ids=[c[0] for c in CARSON])
def test_hand_checked_carson_parcel(carson, address, zone, lot, max_units, binding, limits):
    rules, state, a = carson
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


AZUSA = [
    ("1350 N Alameda Ave", "NG3-Low", Lot(8518, 71.9, 122.0, (), 3491, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 10, "state_sb9": 4}),
    ("556 W 11th St", "NG1-Low", Lot(7374, 53.0, 139.3, (), 2656, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 10, "state_sb9": 4}),
    ("309 N Soldano Ave", "NG2-Med", Lot(7569, 50.3, 151.2, (), 2641, 2),
     3, "state_law:adu", {"lot_area_per_unit": 2, "state_adu": 3}),
    ("1325 N Azusa Ave", "NG3-Mod", Lot(20271, 72.6, 290.9, (), 3421, 6),
     12, "lot_area_per_unit", {"lot_area_per_unit": 12}),
    ("246 N Azusa Ave", "CAZ", Lot(13830, 100.5, 138.5, (), 2669, 0),
     8, "lot_area_per_unit", {"lot_area_per_unit": 8}),
    ("843 W Arrow Hwy", "CAH", Lot(32862, 166.5, 235.6, (), 7197, 1),
     20, "lot_area_per_unit", {"lot_area_per_unit": 20}),
]


@pytest.fixture(scope="module")
def azusa():
    rules = load_zone_rules(REPO / "cities" / "azusa" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", AZUSA, ids=[c[0] for c in AZUSA])
def test_hand_checked_azusa_parcel(azusa, address, zone, lot, max_units, binding, limits):
    rules, state, a = azusa
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


LOMITA = [
    ("23826 Eshelman Ave", "R1", Lot(7014, 56.3, 125.3, (), 13349, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 3, "state_sb9": 4}),
    ("25542 Pennsylvania Ave", "A1", Lot(8647, 62.3, 140.6, (), 15136, 2),
     4, "state_law:sb9", {"density": 1, "envelope": 4, "state_sb9": 4}),
    ("2269 243rd St", "RVD2500", Lot(7072, 48.0, 147.3, (), 15326, 2),
     3, "state_law:adu", {"lot_area_per_unit": 2, "state_adu": 3}),
    ("2309 241st St", "RVD1500", Lot(11827, 55.0, 215.0, (), 15620, 4),
     7, "lot_area_per_unit", {"lot_area_per_unit": 7}),
    ("25620 Oak St", "RVD5000", Lot(9077, 59.8, 152.3, (), 12649, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 5, "state_sb9": 4}),
]


@pytest.fixture(scope="module")
def lomita():
    rules = load_zone_rules(REPO / "cities" / "lomita" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", LOMITA, ids=[c[0] for c in LOMITA])
def test_hand_checked_lomita_parcel(lomita, address, zone, lot, max_units, binding, limits):
    rules, state, a = lomita
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


HAWTHORNE = [
    ("12236 Ramona Ave", "R-1", Lot(5970, 43.0, 138.7, (), 4640, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 5, "state_sb9": 4}),
    ("3737 W 119th St", "R-2", Lot(7832, 52.5, 168.1, (), 3637, 1),
     3, "state_law:adu", {"lot_area_per_unit": 2, "state_adu": 3}),
    ("3747 W 119th St", "R-2", Lot(5566, 50.6, 110.1, (), 3740, 1),
     3, "state_law:adu", {"lot_area_per_unit": 1, "state_adu": 3}),
    ("12220 Grevillea Ave", "R-3", Lot(7876, 52.5, 150.0, (), 4381, 9),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5}),
    ("4510 W 120th St", "R-3", Lot(4682, 40.0, 117.0, (), 3725, 1),
     3, "state_law:adu", {"lot_area_per_unit": 1, "state_adu": 3}),
    ("3833 W 139th St", "R-4", Lot(8322, 65.0, 128.1, (), 7754, 1),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5}),
    ("3831 W Rosecrans Ave", "C-3 (MU)", Lot(15141, 101.8, 149.0, (), 8871, 0),
     10, "lot_area_per_unit", {"lot_area_per_unit": 10}),
]


@pytest.fixture(scope="module")
def hawthorne():
    rules = load_zone_rules(REPO / "cities" / "hawthorne" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", HAWTHORNE, ids=[c[0] for c in HAWTHORNE])
def test_hand_checked_hawthorne_parcel(hawthorne, address, zone, lot, max_units, binding, limits):
    rules, state, a = hawthorne
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


SAN_GABRIEL = [
    ("711 Los Olivos Dr", "R-1", Lot(8842, 51.0, 173.8, (), 7867, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "state_sb9": 4}),
    ("305 N San Marino Ave", "R-1A", Lot(11505, 100.0, 116.1, (), 10577, 0),
     3, "state_law:adu", {"lot_area_per_unit": 2, "envelope": 3, "state_adu": 3}),
    ("1708 Jackson Ave", "R-2", Lot(8693, 59.2, 149.3, (), 10203, 2),
     3, "state_law:adu", {"lot_area_per_unit": 2, "state_adu": 3}),
    ("266 W Bencamp St", "R-2", Lot(6518, 58.8, 113.2, (), 10327, 1),
     3, "state_law:adu", {"lot_area_per_unit": 1, "state_adu": 3}),
    ("1244 S Ramona St", "R-3", Lot(6920, 104.3, 113.2, (), 8481, 1),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3}),
    ("1240 S Ramona St", "R-3", Lot(22916, 152.5, 328.1, (), 8500, 1),
     13, "lot_area_per_unit", {"lot_area_per_unit": 13}),
    ("235 S Arroyo Dr", "R-3 A", Lot(10482, 77.6, 326.1, (), 7107, 1),
     6, "lot_area_per_unit", {"lot_area_per_unit": 6}),
]


@pytest.fixture(scope="module")
def san_gabriel():
    rules = load_zone_rules(REPO / "cities" / "san_gabriel" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", SAN_GABRIEL, ids=[c[0] for c in SAN_GABRIEL])
def test_hand_checked_san_gabriel_parcel(san_gabriel, address, zone, lot, max_units, binding, limits):
    rules, state, a = san_gabriel
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


MONTEREY_PARK = [
    ("1890 Verde Vista Dr", "R-1", Lot(5550, 55.5, 100.0, (), 3992, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 2, "state_sb9": 4}),
    ("546 Casuda Canyon Dr", "R-1", Lot(8029, 67.0, 120.0, (), 3465, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 3, "state_sb9": 4}),
    ("577 Casuda Canyon Dr", "R-1", Lot(14036, 143.1, 169.7, (), 2755, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 4, "state_sb9": 4}),
    ("101 Campanita Ct", "R-2", Lot(7201, 80.4, 110.1, (), 4959, 1),
     3, "state_law:adu", {"lot_area_per_unit": 2, "state_adu": 3}),
    ("1581 College View Dr", "R-3", Lot(8238, 60.3, 136.9, (), 2864, 5),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4}),
    ("1501 S Atlantic Blvd", "R-3", Lot(22604, 150.1, 151.2, (), 2987, 0),
     12, "lot_area_per_unit", {"lot_area_per_unit": 12}),
]


@pytest.fixture(scope="module")
def monterey_park():
    rules = load_zone_rules(REPO / "cities" / "monterey_park" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", MONTEREY_PARK, ids=[c[0] for c in MONTEREY_PARK])
def test_hand_checked_monterey_park_parcel(monterey_park, address, zone, lot, max_units, binding, limits):
    rules, state, a = monterey_park
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


AGOURA_HILLS = [
    ("6309 Aquarius Ave", "RS", Lot(6671, 61.2, 113.3, (), 41916, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 5, "state_adu": 3, "state_sb9": 4}),
    ("4014 Patrick Henry Pl", "RS", Lot(12760, 74.8, 187.3, (), 38783, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 8, "state_adu": 3, "state_sb9": 4}),
    ("4965 Kingsgate Court", "RM", Lot(6204, 76.1, 81.7, (), 40022, 1),
     3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 6, "parking": 3, "state_adu": 3}),
    ("5322 Colodny Dr", "RH", Lot(27939, 124.3, 235.6, (), 40797, 18),
     11, "lot_area_per_unit", {"lot_area_per_unit": 11, "envelope": 26, "parking": 20}),
    ("5321 Colodny Dr", "RH", Lot(22123, 61.3, 362.9, (), 40903, 14),
     9, "lot_area_per_unit", {"lot_area_per_unit": 9, "envelope": 20, "parking": 16}),
    ("5515 Foothill Dr", "RL", Lot(20101, 88.2, 228.0, (), 41606, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 13, "state_sb9": 4}),
    ("5909 1/2 Chesebro Rd", "RV", Lot(49685, 145.3, 375.0, (), 37223, 0),
     4, "state_law:sb9", {"density": 1, "envelope": 23, "state_sb9": 4}),
    ("5601 Kanan Rd", "CS-MU", Lot(35246, 160.0, 229.0, (), 44405, 0),
     12, "lot_area_per_unit", {"lot_area_per_unit": 12, "envelope": 33, "parking": 24}),
    ("28700 Thousand Oaks Blvd", "OS-R", Lot(91984, 239.9, 387.0, (), 41960, None),
     3, "state_law:adu", {"density": 1, "envelope": 17, "state_adu": 3}),
    ("28230 Dorothy Dr", "CRS", Lot(21836, 66.6, 340.1, (), 41525, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def agoura_hills():
    rules = load_zone_rules(REPO / "cities" / "agoura_hills" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", AGOURA_HILLS, ids=[c[0] for c in AGOURA_HILLS])
def test_hand_checked_agoura_hills_parcel(agoura_hills, address, zone, lot, max_units, binding, limits):
    rules, state, a = agoura_hills
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


def test_coverage_band_with_a_share_as_value_is_rejected(agoura_hills):
    rules, _, _ = agoura_hills
    data = rules["RS"].model_dump(exclude_none=True)
    data["lot_coverage"]["value"]["bands"][0] = {"below": 10000, "value": 0.5}
    with pytest.raises(ValueError, match="lot_coverage bands"):
        type(rules["RS"]).model_validate(data)


TORRANCE = [
    ("3313 W 166th St", "R1", Lot(5350, 53.5, 100.0, (), 6724, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 3, "state_adu": 3, "state_sb9": 4}),
    ("4566 Mindora Dr", "R1", Lot(9000, 60.0, 150.1, (), 19127, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 5, "state_sb9": 4}),
    ("2116 Santa Cruz Ct", "R2", Lot(6406, 61.0, 105.0, (), 17792, 2),
     3, "state_law:adu", {"density": 2, "envelope": 3, "parking": 3, "state_adu": 3}),
    ("3564 Del Amo Blvd", "R3", Lot(6000, 50.0, 120.0, (), 9444, 4),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3, "envelope": 5, "parking": 4}),
    ("16817 Yukon Ave", "R3", Lot(10001, 50.0, 200.0, (), 5114, 9),
     6, "lot_area_per_unit", {"lot_area_per_unit": 6, "envelope": 9, "parking": 7}),
    ("21010 Anza Ave", "R3", Lot(35755, 132.0, 272.0, (), 12928, 34),
     20, "envelope", {"lot_area_per_unit": 22, "envelope": 20, "parking": 29}),
    ("2407 Gramercy Ave", "R33", Lot(6209, 50.0, 124.2, (), 17678, 3),
     3, "density", {"density": 3, "lot_area_per_unit": 3, "envelope": 5}),
    ("4033 W 182nd St", "RR3", Lot(9555, 51.1, 186.8, (), 3719, 5),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 12, "parking": 7}),
    ("16700 Yukon Ave", "R4", Lot(58769, 235.1, 250.0, (), 5481, 50),
     58, "lot_area_per_unit", {"lot_area_per_unit": 58, "envelope": 186, "parking": 62}),
    ("2202 W 230th St", "RP", Lot(7571, 65.0, 118.7, (), 16673, 1),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 9, "parking": 5}),
    ("17305 Crenshaw Blvd", "C2", Lot(27114, 123.0, 220.5, (), 7684, 1),
     16, "lot_area_per_unit", {"lot_area_per_unit": 16, "envelope": 81, "parking": 28}),
    ("4565 Sharynne Ln", "A1", Lot(72755, 167.9, 434.7, (), 19338, 3),
     3, "state_law:adu", {"density": 1, "state_adu": 3}),
    ("3811 Jason Cir", "RTH", Lot(6444, 55.2, 120.0, (), 19603, 1),
     3, "state_law:adu", {"lot_area_per_unit": 1, "parking": 4, "state_adu": 3}),
    ("1855 Del Amo Blvd", "M2", Lot(20428, 102.7, 212.7, (), 15829, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def torrance():
    rules = load_zone_rules(REPO / "cities" / "torrance" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", TORRANCE, ids=[c[0] for c in TORRANCE])
def test_hand_checked_torrance_parcel(torrance, address, zone, lot, max_units, binding, limits):
    rules, state, a = torrance
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


ARTESIA = [
    ("11674 168th St", "R-1", Lot(5680, 56.2, 108.5, (), 14160, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 5, "state_adu": 3, "state_sb9": 4}),
    ("17602 Summer Ave", "R-1", Lot(6167, 60.0, 105.7, (), 15961, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 5, "state_sb9": 4}),
    ("18004 Roseton Ave", "M-R", Lot(7053, 51.6, 136.9, (), 17500, 1),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 6, "parking": 5}),
    ("18601 Arline Ave", "M-R", Lot(21719, 149.5, 157.0, (), 19622, 12),
     12, "lot_area_per_unit", {"lot_area_per_unit": 12, "envelope": 20, "parking": 16}),
    ("11512 186th St", "M-R", Lot(22195, 94.1, 236.1, (), 19003, 1),
     12, "lot_area_per_unit", {"lot_area_per_unit": 12, "envelope": 20, "parking": 16}),
    ("18863 Clarkdale Ave", "M-D-R", Lot(4494, 46.0, 103.6, (), 21052, 1),
     3, "state_law:adu", {"density": 2, "envelope": 4, "parking": 3, "state_adu": 3}),
    ("19212 Norwalk Blvd", "M-C-R", Lot(7318, 77.6, 94.9, (), 22199, 1),
     3, "state_law:adu", {"density": 1, "envelope": 8, "state_adu": 3}),
    ("11555 187th St", "A-1", Lot(10574, 45.3, 233.8, (), 19338, 2),
     3, "state_law:adu", {"density": 1, "envelope": 9, "state_adu": 3}),
    ("11424 186th St", "C-O", Lot(50247, 165.6, 338.7, (), 18801, 15),
     17, "lot_area_per_unit", {"lot_area_per_unit": 17, "envelope": 80, "parking": 42}),
    ("18642 Pioneer Blvd", "C-G", Lot(7446, 52.2, 143.3, (), 19879, 1),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def artesia():
    rules = load_zone_rules(REPO / "cities" / "artesia" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", ARTESIA, ids=[c[0] for c in ARTESIA])
def test_hand_checked_artesia_parcel(artesia, address, zone, lot, max_units, binding, limits):
    rules, state, a = artesia
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


AVALON = [
    ("358 Claressa Ave", "HD-R", Lot(2366, 48.8, 50.0, (), 159301, 2),
     3, "state_law:adu", {"lot_area_per_unit": 2, "envelope": 2, "parking": 2, "state_adu": 3}),
    ("341 Clemente Ave", "HD-R", Lot(1951, 39.1, 50.0, (), 159235, 3),
     3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 2, "parking": 2, "state_adu": 3}),
    ("323 Metropole Ave", "HD-R", Lot(6326, 39.9, 159.8, (), 158505, 4),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 7, "parking": 7}),
    ("233 W Whittley Ave", "HD-R", Lot(6918, 54.8, 129.8, (), 157876, 17),
     6, "lot_area_per_unit", {"lot_area_per_unit": 6, "envelope": 8, "parking": 8}),
    ("191 Lower Terrace", "MD-R", Lot(2640, 53.8, 54.5, (), 158439, 2),
     3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 1, "parking": 2, "state_adu": 3}),
    ("127 Vieudelou Ave", "MD-R", Lot(6926, 57.8, 120.1, (), 157566, 5),
     3, "lot_area_per_unit", {"lot_area_per_unit": 3, "envelope": 6, "parking": 7}),
    ("103 Vieudelou Ave", "LD-R", Lot(4706, 39.2, 120.0, (), 157370, 1),
     4, "state_law:sb9", {"lot_area_per_unit": 1, "envelope": 3, "parking": 5, "state_sb9": 4}),
    ("313 Beacon St", "SC", Lot(2314, 18.5, 125.0, (), 158439, 1),
     3, "state_law:adu", {"lot_area_per_unit": 2, "envelope": 2, "parking": 2, "state_adu": 3}),
    ("122 Sumner Ave", "C", Lot(4802, 40.2, 120.2, (), 158056, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def avalon():
    rules = load_zone_rules(REPO / "cities" / "avalon" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", AVALON, ids=[c[0] for c in AVALON])
def test_hand_checked_avalon_parcel(avalon, address, zone, lot, max_units, binding, limits):
    rules, state, a = avalon
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


BALDWIN_PARK = [
    ("13308 Demblon St", "R1", Lot(5873, 54.3, 109.2, (), 7559, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 4, "state_adu": 3, "state_sb9": 4}),
    ("14432 Olive St", "R1", Lot(15707, 55.1, 285.6, (), 4480, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 13, "state_sb9": 4}),
    ("14567 Pacific Ave", "RG", Lot(5689, 50.1, 114.0, (), 1116, 3),
     3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 5, "state_adu": 3}),
    ("3833 Bresee Ave", "RG", Lot(19014, 63.1, 302.5, (), 4103, 9),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 17, "parking": 14}),
    ("13727 Los Angeles St", "R3", Lot(8993, 61.2, 148.1, (), 5601, 3),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 9, "parking": 6}),
    ("4135 La Rica Ave", "R3", Lot(29471, 143.0, 208.7, (), 2922, 13),
     13, "lot_area_per_unit", {"lot_area_per_unit": 13, "envelope": 33, "parking": 22}),
    ("14514 Central Ave", "MU-1", Lot(31030, 128.0, 243.7, (), 261, None),
     21, "lot_area_per_unit", {"lot_area_per_unit": 21, "envelope": 58}),
    ("14914 Pacific Ave", "MU-2", Lot(16110, 81.1, 199.1, (), 3192, 0),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 18, "parking": 13}),
    ("14864 Pacific Ave", "MU-2", Lot(24653, 100.0, 246.9, (), 2729, 13),
     16, "lot_area_per_unit", {"lot_area_per_unit": 16, "envelope": 27, "parking": 19}),
    ("14064 Francisquito Ave", "C2", Lot(8870, 72.0, 123.5, (), 8621, None),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def baldwin_park():
    rules = load_zone_rules(REPO / "cities" / "baldwin_park" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", BALDWIN_PARK, ids=[c[0] for c in BALDWIN_PARK])
def test_hand_checked_baldwin_park_parcel(baldwin_park, address, zone, lot, max_units, binding, limits):
    rules, state, a = baldwin_park
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


BELL = [
    ("6936 Prospect Ave", "R1", Lot(5315, 49.4, 108.3, (), 1333, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 5, "state_adu": 3, "state_sb9": 4}),
    ("3629 Anita Dr", "R2", Lot(5127, 52.2, 100.1, (), 2497, 1),
     3, "state_law:adu", {"density": 2, "envelope": 5, "state_adu": 3}),
    ("6322 Flora Ave", "R3", Lot(5956, 39.9, 150.1, (), 3081, 1),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 8, "parking": 4}),
    ("7032 Bear Ave", "R3", Lot(5925, 43.0, 137.9, (), 3181, 1),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 8, "parking": 4}),
    ("6815 California Ave", "R3", Lot(18768, 64.6, 300.1, (), 2050, 12),
     12, "lot_area_per_unit", {"lot_area_per_unit": 12, "envelope": 26}),
    ("4345 Florence Ave", "C3R", Lot(5973, 50.1, 119.3, (), 562, 2),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 8}),
    ("4828 Florence Ave", "C3R", Lot(19197, 52.7, 365.1, (), 2127, 12),
     13, "lot_area_per_unit", {"lot_area_per_unit": 13, "envelope": 27}),
    ("4511 Gage Ave", "C3", Lot(6219, 53.7, 117.2, (), 2877, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def bell():
    rules = load_zone_rules(REPO / "cities" / "bell" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", BELL, ids=[c[0] for c in BELL])
def test_hand_checked_bell_parcel(bell, address, zone, lot, max_units, binding, limits):
    rules, state, a = bell
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


BELL_GARDENS = [
    ("5554 Agra St", "R-1", Lot(6387, 49.4, 130.7, (), 5801, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 5, "state_adu": 3, "state_sb9": 4}),
    ("5900 Agra St", "R-2", Lot(6751, 49.9, 137.7, (), 4389, 2),
     3, "state_law:adu", {"density": 3, "lot_area_per_unit": 2, "envelope": 5, "parking": 5, "state_adu": 3}),
    ("5951 Watcher St", "R-2", Lot(10002, 64.0, 156.6, (), 4844, 1),
     3, "density", {"density": 3, "lot_area_per_unit": 4, "envelope": 8, "parking": 7}),
    ("6632 Specht Ave", "R-3", Lot(6888, 41.0, 169.3, (), 4716, 3),
     3, "state_law:adu", {"lot_area_per_unit": 2, "envelope": 5, "parking": 4, "state_adu": 3}),
    ("5826 Live Oak St", "R-3", Lot(23346, 89.9, 261.1, (), 3328, 8),
     11, "lot_area_per_unit", {"lot_area_per_unit": 11, "envelope": 19, "parking": 17}),
    ("5720 Clara St", "R-3", Lot(74849, 211.2, 357.0, (), 3907, 65),
     42, "lot_area_per_unit", {"lot_area_per_unit": 42, "envelope": 63, "parking": 55}),
    ("5526 Clara St", "R-4", Lot(11900, 39.7, 301.0, (), 5167, 4),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 10, "parking": 8}),
    ("6357 Eastern Ave", "M-U", Lot(18763, 137.0, 138.8, (), 5282, 0),
     12, "lot_area_per_unit", {"lot_area_per_unit": 12, "envelope": 53, "parking": 16}),
    ("6320 Florence Ave", "C-4", Lot(31641, 140.7, 238.0, (), 206, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def bell_gardens():
    rules = load_zone_rules(REPO / "cities" / "bell_gardens" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", BELL_GARDENS, ids=[c[0] for c in BELL_GARDENS])
def test_hand_checked_bell_gardens_parcel(bell_gardens, address, zone, lot, max_units, binding, limits):
    rules, state, a = bell_gardens
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


BELLFLOWER = [
    ("14002 Dunrobin Ave", "S-F", Lot(5419, 54.8, 99.0, (), 5832, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 4, "state_adu": 3, "state_sb9": 4}),
    ("9448 Rose St", "R-1", Lot(5266, 69.1, 76.3, (), 15219, 1),
     4, "state_law:sb9", {"lot_area_per_unit": 1, "envelope": 4, "parking": 3, "state_sb9": 4}),
    ("14544 Bellflower Blvd", "R-1", Lot(17056, 66.0, 258.6, (), 6665, 1),
     4, "state_law:sb9", {"lot_area_per_unit": 3, "envelope": 14, "parking": 13, "state_sb9": 4}),
    ("16261 California Ave", "A-E", Lot(11343, 82.0, 138.5, (), 10613, 1),
     3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 4, "parking": 6, "state_adu": 3}),
    ("9438 Mayne St", "R-2", Lot(7844, 60.0, 130.7, (), 9613, 5),
     3, "state_law:adu", {"lot_area_per_unit": 2, "envelope": 8, "parking": 4, "state_adu": 3}),
    ("8539 Rose St", "R-2", Lot(18293, 70.5, 260.9, (), 14785, 7),
     5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 23, "parking": 11}),
    ("10136 Maple St", "R-3", Lot(8911, 66.0, 135.0, (), 12475, 3),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 15, "parking": 5}),
    ("16336 Cornuta Ave", "R-3", Lot(40045, 115.2, 348.6, (), 11157, 15),
     20, "lot_area_per_unit", {"lot_area_per_unit": 20, "envelope": 84, "parking": 23}),
    ("9824 Maple St", "T-C", Lot(7879, 63.1, 125.3, (), 12044, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def bellflower():
    rules = load_zone_rules(REPO / "cities" / "bellflower" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", BELLFLOWER, ids=[c[0] for c in BELLFLOWER])
def test_hand_checked_bellflower_parcel(bellflower, address, zone, lot, max_units, binding, limits):
    rules, state, a = bellflower
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


BEVERLY_HILLS = [
    ("126 N Palm Dr", "R-1", Lot(7500, 50.0, 150.0, (), 4837, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 4, "state_adu": 3, "state_sb9": 4}),
    ("912 N Roxbury Dr", "R-1", Lot(24596, 114.9, 231.3, (), 5255, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 10, "state_sb9": 4}),
    ("174 N Almont Dr", "R-4", Lot(6762, 59.0, 115.4, (), 3599, 13),
     4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 10, "parking": 4}),
    ("434 S Canon Dr", "R-4", Lot(12124, 100.0, 121.3, (), 5144, 29),
     8, "lot_area_per_unit", {"lot_area_per_unit": 8, "envelope": 21, "parking": 8}),
    ("441 N Oakhurst Dr", "R-4", Lot(22503, 150.1, 150.1, (), 3107, 36),
     17, "parking", {"lot_area_per_unit": 19, "envelope": 45, "parking": 17}),
    ("9901 Durant Dr", "R-4", Lot(11005, 100.1, 110.0, (), 752, 8),
     7, "lot_area_per_unit", {"lot_area_per_unit": 7, "envelope": 18}),
    ("140 N Robertson Blvd", "C-3", Lot(6713, 50.0, 134.5, (), 2808, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def beverly_hills():
    rules = load_zone_rules(REPO / "cities" / "beverly_hills" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", BEVERLY_HILLS, ids=[c[0] for c in BEVERLY_HILLS])
def test_hand_checked_beverly_hills_parcel(beverly_hills, address, zone, lot, max_units, binding, limits):
    rules, state, a = beverly_hills
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


BRADBURY = [
    ("2332 Gardi St", "R-7,500", Lot(6854, 72.2, 95.5, (), 5687, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 3, "state_adu": 3, "state_sb9": 4}),
    ("2341 Freeborn St", "R-7,500", Lot(8834, 83.5, 126.5, (), 6074, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 4, "state_sb9": 4}),
    ("2205 Gardi St", "R-20,000", Lot(20296, 110.5, 185.1, (), 5235, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 20, "state_sb9": 4}),
    ("1395 Lemon Ave", "A-1", Lot(45243, 146.0, 312.0, (), 5744, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 42, "state_sb9": 4}),
    ("4 Bradbury Hills Rd", "A-2", Lot(82650, 218.7, 410.6, (), 4872, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 98, "state_sb9": 4}),
    ("368 Old Ranch Rd", "A-5", Lot(188692, 326.3, 615.1, (), 6639, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 264, "state_sb9": 4}),
]


@pytest.fixture(scope="module")
def bradbury():
    rules = load_zone_rules(REPO / "cities" / "bradbury" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", BRADBURY, ids=[c[0] for c in BRADBURY])
def test_hand_checked_bradbury_parcel(bradbury, address, zone, lot, max_units, binding, limits):
    rules, state, a = bradbury
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


CALABASAS = [
    ("23015 Wrencrest Dr", "RS", Lot(9029, 80.8, 121.5, (), 17794, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 8, "state_adu": 3, "state_sb9": 4}),
    ("3940 Prado De Verde", "RS", Lot(15172, 122.4, 135.1, (), 28654, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 13, "state_sb9": 4}),
    ("4559 Cielo Cir", "RM", Lot(12100, 115.6, 131.4, (), 31616, 2),
     6, "lot_area_per_unit", {"lot_area_per_unit": 6, "envelope": 12, "parking": 8}),
    ("4654 Cielo Cir", "RM", Lot(54378, 260.8, 308.6, (), 31151, 1),
     29, "lot_area_per_unit", {"lot_area_per_unit": 29, "envelope": 56, "parking": 41}),
    ("3889 Old Topanga Road", "RR", Lot(43822, 169.8, 297.5, (), 20114, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 24, "state_sb9": 4}),
    ("3485 Old Topanga Canyon Rd", "RC", Lot(16563, 51.0, 330.5, (), 23281, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 10, "state_sb9": 4}),
    ("24325 Mulholland Hwy", "HM", Lot(48190, 229.9, 238.7, (), 28405, 1),
     3, "state_law:adu", {"density": 1, "envelope": 41, "state_adu": 3}),
    ("26050 Mureau Rd", "CMU", Lot(69222, 205.5, 362.2, (), 27951, 0),
     38, "lot_area_per_unit", {"lot_area_per_unit": 38, "envelope": 65, "parking": 56}),
    ("23556 Calabasas Rd", "CT", Lot(14398, 93.0, 157.3, (), 16148, 0),
     6, "lot_area_per_unit", {"lot_area_per_unit": 6, "envelope": 13, "parking": 11}),
    ("4830 Las Virgenes Rd", "CR", Lot(31647, 152.0, 220.9, (), 30136, 1),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def calabasas():
    rules = load_zone_rules(REPO / "cities" / "calabasas" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", CALABASAS, ids=[c[0] for c in CALABASAS])
def test_hand_checked_calabasas_parcel(calabasas, address, zone, lot, max_units, binding, limits):
    rules, state, a = calabasas
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


CERRITOS = [
    ("16628 Greenbrook Cir", "RS-5000", Lot(5724, 60.0, 96.7, (), 13319, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 3, "state_adu": 3, "state_sb9": 4}),
    ("12510 Yosemite St", "RS-6500", Lot(6519, 60.4, 109.0, (), 16317, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 4, "state_sb9": 4}),
    ("12659 Liddington St", "RS-6500", Lot(8833, 70.6, 146.6, (), 22451, 1),
     4, "state_law:sb9", {"density": 1, "envelope": 5, "state_sb9": 4}),
    ("12458 Dawn Ln", "RM", Lot(6679, 76.5, 88.7, (), 13406, 4),
     3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 2, "parking": 4, "state_adu": 3}),
    ("18944 Vickie Ave", "RM", Lot(280589, 491.3, 642.7, (), 19700, 203),
     128, "lot_area_per_unit", {"lot_area_per_unit": 128, "envelope": 211, "parking": 238}),
    ("16230 Drycreek Ln", "ADP-3", Lot(5125, 50.5, 102.5, (), 12098, 1),
     3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 3, "parking": 3, "state_adu": 3}),
    ("13363 Artesia Blvd", "CN", Lot(25000, 158.7, 159.1, (), 15939, 0),
     0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def cerritos():
    rules = load_zone_rules(REPO / "cities" / "cerritos" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", CERRITOS, ids=[c[0] for c in CERRITOS])
def test_hand_checked_cerritos_parcel(cerritos, address, zone, lot, max_units, binding, limits):
    rules, state, a = cerritos
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


COMMERCE = [
    ("2116 Fitzgerald Ave", "R-1", Lot(4984, 40.3, 124.2, (), 3250, 1), 4, "state_law:sb9", {"density": 1, "envelope": 1, "parking": 3}),
    ("5217 Harbor St", "R-1", Lot(2134, 24.8, 94.5, (), 4100, 1), 3, "state_law:adu", {"envelope": 1, "parking": 1}),
    ("4483 Lovett St", "R-2", Lot(6668, 50.5, 132.0, (), 4944, 2), 3, "state_law:adu", {"lot_area_per_unit": 2, "density": 2, "envelope": 7, "parking": 5}),
    ("1444 S McDonnell Ave", "R-2", Lot(5691, 64.2, 177.3, (), 3467, 0), 3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 7, "parking": 4}),
    ("6734 Agra St", "R-3", Lot(6763, 76.0, 160.7, (), 4650, 1), 3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 13, "parking": 5}),
    ("6742 Lanto St", "R-3", Lot(7670, 66.5, 141.2, (), 5081, 3), 3, "lot_area_per_unit", {"lot_area_per_unit": 3, "envelope": 14, "parking": 6}),
    ("5440 Telegraph Rd", "C-2", Lot(21279, 117.8, 265.0, (), 2802, 0), 10, "envelope", {"envelope": 10, "parking": 16}),
    ("6048 Triangle Dr", "M-2", Lot(32453, 140.0, 231.8, (), 5131, 1), 0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def commerce():
    rules = load_zone_rules(REPO / "cities" / "commerce" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", COMMERCE, ids=[c[0] for c in COMMERCE])
def test_hand_checked_commerce_parcel(commerce, address, zone, lot, max_units, binding, limits):
    rules, state, a = commerce
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


COMPTON = [
    ("1214 W 130th St", "R-L", Lot(9457, 50.1, 189.1, (), 3606, 1), 4, "state_law:sb9", {"lot_area_per_unit": 1, "envelope": 11, "parking": 7}),
    ("2313 E Killen Ct", "R-L", Lot(15864, 134.8, 153.4, (), 4706, 1), 4, "state_law:sb9", {"lot_area_per_unit": 3, "envelope": 20, "parking": 12}),
    ("805 E Clemmer Dr", "R-A", Lot(22251, 130.1, 175.3, (), 1855, 1), 4, "state_law:sb9", {"lot_area_per_unit": 2, "envelope": 29}),
    ("612 S Harris Ave", "R-M", Lot(11268, 80.3, 145.0, (), 6246, 3), 4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 20, "parking": 11}),
    ("812 W Arbutus St", "R-M", Lot(4995, 49.9, 102.6, (), 4312, 1), 3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 6, "parking": 4}),
    ("1004 N Sloan Ave", "R-H", Lot(7069, 49.9, 144.3, (), 4527, 5), 4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 13, "parking": 7}),
    ("209 S Willow Ave", "R-H", Lot(6758, 45.0, 152.7, (), 2140, 6), 4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 12}),
    ("408 N Bowen Ave", "C-L", Lot(19855, 97.1, 209.7, (), 5102, 0), 13, "lot_area_per_unit", {"lot_area_per_unit": 13, "envelope": 52, "parking": 27}),
    ("500 E Pine St", "M-H", Lot(43673, 145.3, 300.7, (), 4848, 1), 0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def compton():
    rules = load_zone_rules(REPO / "cities" / "compton" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", COMPTON, ids=[c[0] for c in COMPTON])
def test_hand_checked_compton_parcel(compton, address, zone, lot, max_units, binding, limits):
    rules, state, a = compton
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


CLAREMONT = [
    ("1490 Towne Ave", "RS-10000", Lot(10021, 78.8, 130.9, (), 3778, 1), 4, "state_law:sb9", {"density": 1, "envelope": 3, "parking": 7}),
    ("1046 Moab Dr", "RR-35000", Lot(27510, 174.2, 184.6, (), 11591, 1), 4, "state_law:sb9", {"envelope": 5, "parking": 16}),
    ("254 W 11th St", "HC", Lot(7500, 50.0, 150.2, (), 3654, 2), 4, "state_law:sb9", {"envelope": 2, "parking": 5}),
    ("237 Spring St", "RM-4000", Lot(8321, 48.8, 172.1, (), 884, 2), 3, "state_law:adu", {"lot_area_per_unit": 2, "envelope": 8}),
    ("450 Champlain Dr", "RM-3000", Lot(8898, 105.3, 116.1, (), 8742, 1), 3, "state_law:adu", {"lot_area_per_unit": 2, "envelope": 10, "parking": 5}),
    ("928 Heritage Ct", "RM-3000", Lot(14781, 79.9, 241.9, (), 9473, 3), 4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 19, "parking": 9}),
    ("645 Colby Cir", "RM-2000", Lot(16821, 118.5, 178.2, (), 5965, 8), 8, "lot_area_per_unit", {"lot_area_per_unit": 8, "envelope": 37, "parking": 12}),
    ("150 Olive St", "MU2", Lot(25810, 151.3, 171.1, (), 359, 0), 13, "lot_area_per_unit", {"lot_area_per_unit": 13, "envelope": 68}),
    ("735 S Mills Ave", "CP", Lot(81512, 196.8, 456.8, (), 4360, 0), 27, "lot_area_per_unit", {"lot_area_per_unit": 27, "envelope": 130, "parking": 56}),
    ("655 E Foothill Blvd", "CH", Lot(25815, 159.0, 164.5, (), 5352, 0), 0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def claremont():
    rules = load_zone_rules(REPO / "cities" / "claremont" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", CLAREMONT, ids=[c[0] for c in CLAREMONT])
def test_hand_checked_claremont_parcel(claremont, address, zone, lot, max_units, binding, limits):
    rules, state, a = claremont
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


COVINA = [
    ("568 W Alcross St", "R-1-7500", Lot(6756, 73.5, 101.4, (), 6026, 1), 4, "state_law:sb9", {"density": 1, "envelope": 4, "parking": 4}),
    ("413 S Farber Ave", "R-1-10,000", Lot(10042, 72.8, 138.5, (), 7101, 1), 4, "state_law:sb9", {"envelope": 8, "parking": 7}),
    ("1438 E Holt Ave", "E-1", Lot(141069, 299.2, 700.9, (), 11401, 1), 4, "state_law:sb9", {"envelope": 92, "parking": 114}),
    ("671 S Calvados Ave", "RD-4000", Lot(106394, 319.8, 336.2, (), 5199, 24), 26, "lot_area_per_unit", {"lot_area_per_unit": 26, "envelope": 162, "parking": 83}),
    ("258 W Hampton Ct", "RD-3000", Lot(5653, 38.4, 148.6, (), 1612, 1), 3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 5}),
    ("351 E College St", "RD-3000", Lot(10280, 53.5, 192.7, (), 1972, 2), 3, "lot_area_per_unit", {"lot_area_per_unit": 3, "envelope": 10}),
    ("1375 N Sunflower Ave", "RD-3000", Lot(17059, 79.1, 216.7, (), 13364, 2), 5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 16, "parking": 15}),
    ("341 E School St", "RD-1500", Lot(30641, 151.0, 203.6, (), 1470, 24), 15, "lot_area_per_unit", {"lot_area_per_unit": 15, "envelope": 30}),
    ("248 E Dexter St", "RD-1250", Lot(9247, 50.0, 185.4, (), 3101, 1), 3, "state_law:adu", {"lot_area_per_unit": 2, "envelope": 9, "parking": 8}),
    ("900 N Citrus Ave", "C-2", Lot(18702, 125.5, 150.4, (), 1384, 0), 0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def covina():
    rules = load_zone_rules(REPO / "cities" / "covina" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", COVINA, ids=[c[0] for c in COVINA])
def test_hand_checked_covina_parcel(covina, address, zone, lot, max_units, binding, limits):
    rules, state, a = covina
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


CUDAHY = [
    ("5108 Cecilia St", "LDR", Lot(5464, 39.9, 137.3, (), 2898, 1), 3, "state_law:adu", {"lot_area_per_unit": 1, "envelope": 5, "parking": 3}),
    ("5009 Elizabeth St", "MDR", Lot(25965, 99.3, 262.4, (), 3910, 8), 14, "lot_area_per_unit", {"lot_area_per_unit": 14, "envelope": 54, "parking": 27}),
    ("5155 Clara St", "MDR", Lot(10412, 54.9, 190.0, (), 4408, 2), 5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 17, "parking": 10}),
    ("4926 Live Oak St", "HDR", Lot(40453, 105.3, 385.5, (), 2830, 12), 37, "lot_area_per_unit", {"lot_area_per_unit": 37, "envelope": 112, "parking": 49}),
    ("4534 Live Oak St", "CMU", Lot(8480, 51.3, 168.3, (), 1044, 1), 5, "lot_area_per_unit", {"lot_area_per_unit": 5, "envelope": 12}),
    ("4528 Elizabeth St", "CivicMU", Lot(10123, 53.4, 192.6, (), 2530, 3), 6, "lot_area_per_unit", {"lot_area_per_unit": 6, "envelope": 21}),
    ("4505 Santa Ana St", "I-Ind", Lot(39888, 107.9, 375.2, (), 2902, 12), 27, "lot_area_per_unit", {"lot_area_per_unit": 27, "envelope": 46, "parking": 44}),
    ("8420 S Atlantic Ave", "Ent", Lot(24742, 150.9, 196.3, (), 1495, 0), 0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def cudahy():
    rules = load_zone_rules(REPO / "cities" / "cudahy" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", CUDAHY, ids=[c[0] for c in CUDAHY])
def test_hand_checked_cudahy_parcel(cudahy, address, zone, lot, max_units, binding, limits):
    rules, state, a = cudahy
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


DIAMOND_BAR = [
    ("22442 Mountain Laurel Way", "RL", Lot(7011, 63.7, 112.8, (), 8566, 1), 4, "state_law:sb9", {"density": 1, "envelope": 5, "parking": 5}),
    ("867 Golden Prados Dr", "RLM", Lot(8161, 59.1, 139.1, (), 10288, 1), 4, "state_law:sb9", {"envelope": 6, "parking": 6}),
    ("2601 Wagon Train Ln", "RR", Lot(38229, 203.5, 327.1, (), 12658, 1), 4, "state_law:sb9", {"envelope": 21, "parking": 30}),
    ("805 Windwood Dr", "RM", Lot(16032, 118.8, 135.5, (), 1013, 8), 4, "lot_area_per_unit", {"lot_area_per_unit": 4, "envelope": 13}),
    ("20767 E Crest Ln", "RM", Lot(133244, 443.4, 443.6, (), 10415, 28), 36, "lot_area_per_unit", {"lot_area_per_unit": 36, "envelope": 112, "parking": 115}),
    ("22886 Hilton Head Dr", "RMH", Lot(112234, 324.4, 535.8, (), 8807, 1), 41, "lot_area_per_unit", {"lot_area_per_unit": 41, "envelope": 95, "parking": 97}),
    ("338 Torito Ln", "RH", Lot(8136, 54.6, 149.2, (), 12345, 7), 3, "lot_area_per_unit", {"lot_area_per_unit": 3, "envelope": 6, "parking": 6}),
    ("876 Sunset Place", "OS", Lot(37926, 186.0, 315.7, (), 7922, 3), 3, "state_law:adu", {"envelope": 71, "parking": 33}),
    ("2751 S Diamond Bar Blvd", "C-2", Lot(108837, 370.9, 443.3, (), 11593, 0), 0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def diamond_bar():
    rules = load_zone_rules(REPO / "cities" / "diamond_bar" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", DIAMOND_BAR, ids=[c[0] for c in DIAMOND_BAR])
def test_hand_checked_diamond_bar_parcel(diamond_bar, address, zone, lot, max_units, binding, limits):
    rules, state, a = diamond_bar
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


DOWNEY = [
    ("8506 Puritan St Downey Ca 90242", "R-1 5,000", Lot(6090, 50.2, 122.0, (), 1937, 1, 0), 4, "state_law:sb9", {'density': 1, 'envelope': 2, 'state_adu': 3, 'state_sb9': 4}),
    ("7539 Buell St Downey Ca 90241", "R-1 7,500", Lot(7798, 65.1, 123.1, (), 5539, 1, 0), 4, "state_law:sb9", {'density': 1, 'envelope': 3, 'parking': 5, 'state_adu': 3, 'state_sb9': 4}),
    ("10702 Lesterford Ave Downey Ca 90241", "R-1 6,000", Lot(6106, 54.0, 113.3, (), 4978, 1, 0), 4, "state_law:sb9", {'density': 1, 'envelope': 2, 'parking': 4, 'state_adu': 3, 'state_sb9': 4}),
    ("7524 Stewart And Gray Rd Downey Ca 90241", "R-3", Lot(8779, 51.8, 171.9, (), 8522, 5, 0), 4, "lot_area_per_unit", {'lot_area_per_unit': 4, 'envelope': 12, 'parking': 7, 'state_adu': 3}),
    ("8144 Comolette St Downey Ca 90242", "R-2", Lot(5781, 55.3, 105.9, (), 3781, 2, 185), 3, "state_law:adu", {'lot_area_per_unit': 2, 'envelope': 5, 'parking': 3, 'state_adu': 3}),
    ("9129 Lubec St Downey Ca 90240", "R-1 10,000", Lot(10373, 78.0, 133.0, (), 1600, 1, 0), 4, "state_law:sb9", {'density': 1, 'envelope': 4, 'state_adu': 3, 'state_sb9': 4}),
    ("7501 Firestone Blvd Downey Ca 90241", "C-2", Lot(15360, 106.5, 153.2, (), 6355, 0, 20), 0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def downey():
    rules = load_zone_rules(REPO / "cities" / "downey" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", DOWNEY, ids=[c[0] for c in DOWNEY])
def test_hand_checked_downey_parcel(downey, address, zone, lot, max_units, binding, limits):
    rules, state, a = downey
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"


EL_SEGUNDO = [
    ("619 Maryland St El Segundo Ca 90245", "R-1", Lot(6424, 53.5, 120.1, (), 5870, 1, 0), 4, "state_law:sb9", {'density': 1, 'envelope': 3, 'state_adu': 3, 'state_sb9': 4}),
    ("135 W Palm Ave El Segundo Ca 90245", "R-3", Lot(6718, 44.7, 150.1, (), 8992, 4, 0), 4, "density", {'density': 4, 'envelope': 6, 'state_adu': 3}),
    ("514 Sheldon St El Segundo Ca 90245", "R-2", Lot(6000, 40.0, 150.0, (), 7001, 1, 210), 3, "state_law:adu", {'density': 2, 'lot_area_per_unit': 3, 'envelope': 5, 'state_adu': 3}),
    ("215 S Douglas St El Segundo Ca 90245", "M-1", Lot(69679, 215.0, 325.0, (), 1050, 0, 5147), 0, "use_not_permitted", {}),
]


@pytest.fixture(scope="module")
def el_segundo():
    rules = load_zone_rules(REPO / "cities" / "el_segundo" / "rules")
    state = load_state_overrides(REPO / "cities" / "_california" / "state_overrides.yaml")
    return rules, state, EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300, min_home_sqft=500)


@pytest.mark.parametrize("address, zone, lot, max_units, binding, limits", EL_SEGUNDO, ids=[c[0] for c in EL_SEGUNDO])
def test_hand_checked_el_segundo_parcel(el_segundo, address, zone, lot, max_units, binding, limits):
    rules, state, a = el_segundo
    r = compute_capacity(rules[zone], lot, a, state)
    assert r.max_units == max_units
    assert r.binding_constraint == binding
    for name, value in limits.items():
        assert r.limits.get(name) == value, f"{address}: {name}"
