"""By-right homes: how a zone's approval path turns into a number."""

from pathlib import Path

import pytest

from zce.engine.capacity import by_right_units
from zce.rules.schema import ZoneRules, load_zone_rules

REPO = Path(__file__).resolve().parents[2]


def _approval_rules(**extra):
    base = {
        "zone": "T", "name": "Test", "family": "multifamily",
        "sources": {"Z": {"section": "§1", "url": "https://example.com"}},
        "residential_allowed": {"value": True, "source": "Z"},
        "housing_types": {"value": ["multifamily"], "source": "Z"},
        "setbacks": {k: {"value": 0, "source": "Z"} for k in ("front_ft", "side_ft", "rear_ft")},
        "max_stories": {"value": 3, "source": "Z"},
    }
    return ZoneRules(**{**base, **extra})


def test_by_right_follows_the_zones_approval():
    approval = lambda v: {"approval": {"value": v, "source": "Z"}}
    assert by_right_units(_approval_rules(**approval("by_right")), 10, None) == 10
    assert by_right_units(_approval_rules(**approval("conditional")), 10, None) == 0
    assert by_right_units(_approval_rules(**approval("mixed")), 10, None) is None
    assert by_right_units(_approval_rules(), 10, None) is None


def test_by_right_cap_and_sb9_floor():
    capped = _approval_rules(approval={"value": "by_right", "source": "Z"}, by_right_max_units={"value": 4, "source": "Z"})
    assert by_right_units(capped, 10, None) == 4
    assert by_right_units(capped, 3, None) == 3
    assert by_right_units(_approval_rules(), 4, 4) == 4
    assert by_right_units(_approval_rules(approval={"value": "conditional", "source": "Z"}), 4, 4) == 4


def test_approval_must_fit_the_use():
    with pytest.raises(ValueError):
        _approval_rules(residential_allowed={"value": False, "source": "Z"}, approval={"value": "by_right", "source": "Z"})
    with pytest.raises(ValueError):
        _approval_rules(approval={"value": "not_allowed", "source": "Z"})
    with pytest.raises(ValueError):
        _approval_rules(by_right_max_units={"value": 4, "source": "Z"})


# Real lots from docs/HAND_CHECKS.md, section BR: (city, zone, max homes, SB 9 homes, by-right homes).
HAND_CHECKED = [
    ("los_angeles", "R3", 5690, None, 49),
    ("los_angeles", "R1", 4, 4, 4),
    ("los_angeles", "M1", 0, None, 0),
    ("pasadena", "RS-6", 4, 4, 4),
    ("pasadena", "CO", 6, None, 6),
    ("compton", "R-H", 4, None, 4),
    ("torrance", "C2", 8, None, 0),
    ("torrance", "R1", 4, 4, 4),
]


@pytest.mark.parametrize("city, zone, max_units, sb9, expected", HAND_CHECKED)
def test_hand_checked_by_right_lot(city, zone, max_units, sb9, expected):
    rules = load_zone_rules(REPO / "cities" / city / "rules")
    assert by_right_units(rules[zone], max_units, sb9) == expected
