"""Tests for the validation helpers: parsing Housing Element site rows and
matching addresses. Sample lines are in the format the HCD sites-inventory
table takes after PDF text extraction."""

import pandas as pd

from zce.validate import _address_key, drop_repeat_permits, parse_sites

SAMPLE = "\n".join([
    # With a consolidated-site letter ("A") and capacity on this parcel.
    "540 S LAKE AVE 91101 5327002001 A MMU CD5 48 87 0.167431898 Commercial YES - Current "
    "NO - Privately-OwnedAvailable Not Used in Prior Hou  7 55 0 62 Office 6, 7 Common ownership",
    # Without a site letter; a two-letter GP code that could look like one.
    "446 N CRAIG AVE 91107 5744022009 LC CL 0 16 0.178550733 Residential YES - Current "
    "NO - Privately-OwnedAvailable Not Used in Prior Hou  0 5 0 5 Bt  Main Street Commercial Low 6, 8, 9",
    # "Used in Two Consecutive" cycles instead of "...Prior Housing".
    "100 E GREEN ST 91105 5722011017 HMU CD1 48 87 0.683772914 Commercial YES - Current "
    "NO - Privately-OwnedAvailable Used in Two Consecu      0 100 123 223 Other 1",
    "Not a site row 12345",
])


def test_parse_sites():
    df, unparsed = parse_sites(SAMPLE)
    assert unparsed == []
    assert df["apn"].tolist() == ["5327002001", "5744022009", "5722011017"]
    assert df.loc[0, "site"] == "A" and df["site"].iloc[1:].isna().all()  # no site letter -> missing
    assert df["zone"].tolist() == ["CD5", "CL", "CD1"]
    assert df["total"].tolist() == [62, 5, 223]
    assert df.loc[0, ["low", "moderate", "above"]].tolist() == [7, 55, 0]


def test_address_key_ignores_suffixes_and_case():
    assert _address_key("1878 E WALNUT ST CONDOMINIUM") == "1878 E WALNUT ST"
    assert _address_key("127 N MADISON AVE MIXED USE\nPASADENA, CA 91101") == "127 N MADISON AVE"
    assert _address_key("735 N Orange Grove Blvd") == "735 N ORANGE GROVE"
    assert _address_key("1878 E WALNUT ST PASADENA CA 91106") == "1878 E WALNUT ST"
    assert _address_key("no number here") is None


def _permits(*rows):
    return pd.DataFrame(rows, columns=["JURS_TRACKING_ID", "BP_ISSUE_DT1", "UNIT_CAT", "YEAR", "permitted"])


def test_a_repeated_permit_counts_once_in_its_earliest_year():
    # The real pair: the same permit, reported again in 2024 when it was finished.
    apr = _permits(("21010-30000-05877", "2022-03-01", "2 to 4", 2024, 4), ("21010-30000-05877", "2022-03-01", "2 to 4", 2022, 4))
    assert drop_repeat_permits(apr)["permitted"].tolist() == [0, 4]


def test_differently_written_tracking_numbers_are_the_same_permit():
    apr = _permits(("18010-30000-00079", "2018-05-05", "2 to 4", 2018, 2), ("180103000000079", "2018-05-05", "2 to 4", 2021, 2))
    assert drop_repeat_permits(apr)["permitted"].sum() == 2


def test_different_permits_on_one_project_both_count():
    apr = _permits(("21010-30000-05877", "2022-03-01", "5+", 2022, 10), ("21010-30000-05877", "2023-06-01", "5+", 2023, 10))
    assert drop_repeat_permits(apr)["permitted"].sum() == 20


def test_several_permits_listed_in_one_row_match_their_separate_rows():
    # A real pattern: 2 + 2 reported separately later, 4 reported together first, order swapped.
    apr = _permits(("22010-30000-02185", "2022-10-27", "2 to 4", 2025, 2), ("22010-30000-02186", "2022-10-27", "2 to 4", 2025, 2),
                   ("22010-30000-02186 22010-30000-02185", "2022-10-27", "2 to 4", 2022, 4))
    assert drop_repeat_permits(apr)["permitted"].sum() == 4
    swapped = _permits(("20010-1; 20010-2", "2021-07-12", "2 to 4", 2021, 4), ("20010-2 20010-1", "2021-07-12", "2 to 4", 2023, 4))
    assert drop_repeat_permits(swapped)["permitted"].sum() == 4


def test_parts_reported_first_add_up_when_no_row_has_the_total():
    apr = _permits(("20010-1", "2021-07-12", "5+", 2021, 6), ("20010-2", "2021-07-12", "5+", 2021, 6), ("20010-1 20010-2", "2021-07-12", "5+", 2023, 8))
    assert drop_repeat_permits(apr)["permitted"].sum() == 12


def test_rows_without_a_usable_id_or_date_are_kept():
    apr = _permits(("N/A", "2022-03-01", "5+", 2022, 10), ("N/A", "2022-03-01", "5+", 2023, 10), ("21010-1", None, "5+", 2022, 3), ("21010-1", None, "5+", 2023, 3))
    assert drop_repeat_permits(apr)["permitted"].sum() == 26
