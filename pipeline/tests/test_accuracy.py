"""The accuracy test's matching and sorting. It runs on real permits, so its logic has to be right."""

import numpy as np
import pandas as pd
import pytest

from zce import accuracy as A


@pytest.mark.parametrize("raw, want", [("5525004023", "5525004023"), ("5525-004-023", "5525004023"), ("2226029***", None), ("2701BRKDWN", None), (None, None)])
def test_apn_digits(raw, want):
    assert A.apn_digits(raw) == want


@pytest.mark.parametrize("permitted, local, maximum, bonus_max, reported, simplified, want", [
    (10, 10, 12, A.np.nan, False, False, A.FITS_LOCAL),
    (11, 10, 12, 18, False, False, A.FITS_STATE),
    (20, 10, 12, 30, True, False, A.BONUS_REPORTED),
    (15, 10, 12, 18, False, True, A.FITS_BONUS),
    (40, 10, 12, 18, False, True, A.FLAGGED),
    (40, 10, 12, 18, False, False, A.UNEXPLAINED),
    (40, 10, 12, pd.NA, False, False, A.UNEXPLAINED),
])
def test_classify(permitted, local, maximum, bonus_max, reported, simplified, want):
    assert A.classify(permitted, local, maximum, bonus_max, reported, simplified) == want


def test_small_buildings_just_over_our_number_may_be_multifamily_adus():
    assert A.classify(4, 2, 3, pd.NA, False, False, "2 to 4") == A.MULTIFAMILY_ADU
    assert A.classify(4, 1, 1, pd.NA, False, False, "2 to 4") == A.UNEXPLAINED
    assert A.classify(5, 2, 3, pd.NA, False, False, "5+") == A.UNEXPLAINED


def _apr(**kw):
    base = dict(UNIT_CAT="5+", permitted=10.0, APN="1111111111", DENSITY_BONUS_TOTAL=0, APPROVE_SB35="N", STREET_ADDRESS="1 A ST", YEAR=2020)
    return {**base, **kw}


def test_permits_add_up_across_years_and_skip_adus_and_masked_parcels():
    apr = pd.DataFrame([_apr(YEAR=2019), _apr(YEAR=2021, permitted=5.0), _apr(UNIT_CAT="ADU"), _apr(APN="2226029***"), _apr(permitted=0.0, APN="3333333333")])
    p = A.projects_from_apr(apr)
    assert len(p) == 1 and p.loc[0, "permitted"] == 15 and p.loc[0, "first_year"] == 2019
    assert p.attrs["masked_apn_rows"] == 1


@pytest.mark.parametrize("bonus, sb35, want", [(0, "N", False), (0.35, "N", True), (35, "NONE", True), ("0", "SB 9 (2021) - Duplex in SF Zone", True), (None, None, False)])
def test_reported_bonus(bonus, sb35, want):
    assert A._reported_bonus({"DENSITY_BONUS_TOTAL": bonus, "APPROVE_SB35": sb35}) is want


def _lots():
    return pd.DataFrame({
        "parcel_id": ["1111111111", "2222222222", "4444444444"], "ains": [np.array(["1111111111", "1111111112"]), None, None],
        "model_status": ["ok", "not_modeled", "ok"], "rules_zone": ["R3", None, "R4"], "local_units": pd.array([20, pd.NA, 5], dtype="Int64"),
        "max_units": pd.array([20, pd.NA, 5], dtype="Int64"), "density_bonus_80_units": pd.array([36, pd.NA, 9], dtype="Int64"),
        "capacity_flags": [[], [], ["zoning_conditions_not_modeled"]],
    })


def test_check_city_matches_condo_parcels_and_reports_untestable_projects():
    apr = pd.DataFrame([_apr(APN="1111111112"), _apr(APN="2222222222"), _apr(APN="9999999999"), _apr(APN="4444444444", permitted=50.0)])
    out = A.check_city("x", apr, _lots()).set_index("apn")["result"]
    assert out["1111111112"] == A.FITS_LOCAL
    assert out["2222222222"] == "lot_not_modeled"
    assert out["9999999999"] == "lot_not_found"
    assert out["4444444444"] == A.FLAGGED


def test_a_repeated_permit_is_not_counted_twice(tmp_path):
    import json
    from zce.validate import load_apr

    row = {"BP_ABOVE_MOD_INCOME": 4, "CO_ABOVE_MOD_INCOME": 0, "UNIT_CAT": "2 to 4", "APN": "1111111111", "JURS_TRACKING_ID": "21010-30000-05877",
           "BP_ISSUE_DT1": "2022-03-01", "DENSITY_BONUS_TOTAL": 0, "APPROVE_SB35": "N", "STREET_ADDRESS": "1 A ST"}
    path = tmp_path / "apr.json"
    path.write_text(json.dumps([{**row, "YEAR": 2022}, {**row, "YEAR": 2024}]))
    assert A.projects_from_apr(load_apr(path)).loc[0, "permitted"] == 4
