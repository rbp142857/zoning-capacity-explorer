"""Reform studies must refuse a scenario file with a misspelled lever, rather than quietly ignore it."""

import pytest

import pandas as pd

from zce.study import _band, _whole, scenario_from_dict


def test_unknown_lever_is_an_error():
    with pytest.raises(ValueError, match="Unknown levers"):
        scenario_from_dict({"parking_per_units": 0})


def test_known_levers_build_a_scenario():
    assert scenario_from_dict({"parking_per_unit": 0}).parking_per_unit == 0


@pytest.mark.parametrize("distance, label", [(100, "Under ¼ mile"), (1320, "¼ to ½ mile"), (5280, "Over 1 mile or unknown"), (float("nan"), "Over 1 mile or unknown")])
def test_band(distance, label):
    assert _band(distance) == label


def test_unknown_counts_add_as_zero():
    assert _whole(pd.NA) == 0 and _whole(7) == 7
