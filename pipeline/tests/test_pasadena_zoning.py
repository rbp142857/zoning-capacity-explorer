import pytest

from zce.adapters.pasadena_zoning import parse_overlays, parse_zone_code

PREFIXES = {"CD": "Central District Specific Plan", "EPSP": "East Pasadena Specific Plan"}


@pytest.mark.parametrize(
    "code, expected",
    [
        ("RS-6", (None, "RS-6")),
        ("RM-16-1", (None, "RM-16-1")),
        ("CD-MU-C", ("Central District Specific Plan", "MU-C")),
        ("EPSP-d2-CG-B", ("East Pasadena Specific Plan", "d2-CG-B")),
        ("  RS-4 ", (None, "RS-4")),
    ],
)
def test_parse_zone_code(code, expected):
    assert parse_zone_code(code, PREFIXES) == expected


@pytest.mark.parametrize(
    "raw, overlays, leftover",
    [
        (None, [], ""),
        (float("nan"), [], ""),
        ("   ", [], ""),
        ("HD", ["HD"], ""),
        ("HD LD-12", ["HD", "LD-12"], ""),
        ("HD-SR", ["HD-SR"], ""),  # must not be read as "HD" plus junk
        ("OC-HL-1", ["OC", "HL-1"], ""),
        ("SP-1a LD-4", ["SP-1a", "LD-4"], ""),
        ("XYZ", [], "XYZ"),  # unknown text is reported, not silently dropped
    ],
)
def test_parse_overlays(raw, overlays, leftover):
    assert parse_overlays(raw) == (overlays, leftover)
