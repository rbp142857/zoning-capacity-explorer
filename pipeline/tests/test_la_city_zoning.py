import geopandas as gpd
import pytest
from shapely.geometry import box

from zce.adapters.la_city_zoning import NEW_CODE, attach_zoning, parse_zone_string
from zce.capacity_step import rules_for_lot


# Every string below is a real one from LA City Planning's layer (or built from
# real parts); the layer has 2,154 distinct strings.
@pytest.mark.parametrize(
    "text, base, zone_class, height, conditions, overlays",
    [
        ("R1-1", "R1-1", "R1", "1", [], []),
        ("R1-1-HCR", "R1-1", "R1", "1", [], ["HCR"]),
        ("[Q]R1-1D-HCR", "R1-1", "R1", "1", ["Q", "D"], ["HCR"]),
        ("(T)(Q)C2-1VL-CPIO", "C2-1VL", "C2", "1VL", ["T", "Q"], ["CPIO"]),
        ("(F)CM-1-CUGU", "CM-1", "CM", "1", ["F"], ["CUGU"]),
        ("C2-2D-CPIO", "C2-2", "C2", "2", ["D"], ["CPIO"]),
        ("RE15-1-H-HCR", "RE15-1", "RE15", "1", [], ["H", "HCR"]),
        ("R1-1XL-O#-CUGU", "R1-1XL", "R1", "1XL", [], ["O", "CUGU"]),  # # is a map footnote mark
        ("C2-1VL-CPIO ", "C2-1VL", "C2", "1VL", [], ["CPIO"]),  # stray space
        ("R1V2-O", "R1V2", "R1V2", None, [], ["O"]),  # no height district
        ("QC2-1", "C2-1", "C2", "1", ["Q"], []),  # condition glued to the zone
        ("RD1.5-1XL", "RD1.5-1XL", "RD1.5", "1XL", [], []),  # a dot in the zone isn't a separator
        ("QRD1.5-1", "RD1.5-1", "RD1.5", "1", ["Q"], []),
    ],
)
def test_parse_regular_strings(text, base, zone_class, height, conditions, overlays):
    p = parse_zone_string(text)
    assert (p.base_zone, p.zone_class, p.height_district) == (base, zone_class, height)
    assert p.conditions == conditions
    assert p.overlays == overlays
    assert p.specific_plan is None
    assert p.overlay_unparsed == ""


@pytest.mark.parametrize(
    "text, base, plan",
    [
        ("MU(EC)-O", "MU(EC)", "Specific plan (EC)"),
        ("R3(PV)-1L", "R3(PV)-1L", "Specific plan (PV)"),
        ("(WC)COLLEGE-SN-RIO", "COLLEGE", "Specific plan (WC)"),
    ],
)
def test_specific_plan_zones_keep_their_own_code(text, base, plan):
    p = parse_zone_string(text)
    assert (p.base_zone, p.specific_plan) == (base, plan)


def test_new_zoning_code():
    p = parse_zone_string("[LM2-MU1-5][CX2-FA][CPIO-O]")
    assert p.base_zone == p.zone_class == "[LM2-MU1-5][CX2-FA]"
    assert p.overlays == ["CPIO", "O"]
    assert p.specific_plan == NEW_CODE
    # No third group: no overlays, and nothing to report.
    p = parse_zone_string("[VF1-G1-5][OS1-N]")
    assert (p.overlays, p.overlay_unparsed) == ([], "")


def test_unknown_text_is_reported_not_dropped():
    assert parse_zone_string("RE15-1-RPD-2.9-H").overlay_unparsed == "2.9"
    assert parse_zone_string("USC-1B").overlay_unparsed == "1B"


def _rule_names(*names):
    return {n: type("Rules", (), {"zone": n})() for n in names}


def _row(base, zone_class=None, overlays=()):
    return {"base_zone": base, "zone_class": zone_class, "specific_plan": None, "overlays": list(overlays)}


def test_rule_lookup_prefers_the_height_district_then_the_zone():
    rules = _rule_names("C2", "C2-1VL")
    assert rules_for_lot(_row("C2-1VL", "C2"), rules)[0].zone == "C2-1VL"
    assert rules_for_lot(_row("C2-1", "C2"), rules)[0].zone == "C2"
    assert rules_for_lot(_row("R3-1", "R3"), rules)[0] is None  # not modeled yet


def test_other_cities_have_no_zone_class():
    row = {"base_zone": "R1", "specific_plan": None, "overlays": []}
    assert rules_for_lot(row, _rule_names("R1"))[0].zone == "R1"


def test_conditions_and_hillside_are_flagged():
    _, flags = rules_for_lot(_row("R3-1", "R3", ["cond:Q", "H"]), _rule_names("R3"))
    assert flags == ["hillside_overlay_not_modeled", "zoning_conditions_not_modeled"]


def test_attach_zoning_gives_every_lot_the_standard_columns(tmp_path):
    crs = "EPSG:2229"
    gpd.GeoDataFrame(
        {"Zoning": ["[Q]R3-1D-O", "Multiple"], "CATEGORY": ["Multiple Family Residential", "Commercial"]},
        geometry=[box(0, 0, 100, 100), box(100, 0, 200, 100)],
        crs=crs,
    ).to_crs(4326).to_file(tmp_path / "zoning.geojson", driver="GeoJSON")
    lots = gpd.GeoDataFrame(
        {"parcel_id": ["a", "b"]},
        geometry=[box(10, 10, 90, 90), box(500, 500, 600, 600)],  # the second is outside every zone
        crs=crs,
    )
    city = type("City", (), {"analysis_crs": crs})()
    cols, _, _ = attach_zoning(lots, tmp_path, city)
    a, b = cols.iloc[0], cols.iloc[1]
    assert (a.zone_code, a.base_zone, a.zone_class) == ("[Q]R3-1D-O", "R3-1", "R3")
    assert a.zone_category == "Multi-Family Residential"
    assert sorted(a.overlays) == ["O", "cond:D", "cond:Q"]
    assert a.zone_share == pytest.approx(1.0, abs=0.01)
    # A lot in no zone keeps its row, with an empty overlay list for later steps.
    assert b.overlays == [] and not isinstance(b.zone_code, str)
