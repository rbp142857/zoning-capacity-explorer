"""Tests for the validation helpers: parsing Housing Element site rows and
matching addresses. Sample lines are in the format the HCD sites-inventory
table takes after PDF text extraction."""

from zce.validate import _address_key, parse_sites

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
