"""SCAG's zoning table: a city name that matches nothing should fail clearly."""
import pytest

from zce.adapters.scag_zoning import load_zone_table


def test_empty_download_names_the_likely_cause(tmp_path):
    raw = tmp_path / "zoning.json"
    raw.write_text("[]")
    with pytest.raises(ValueError, match="SCAG's spelling"):
        load_zone_table(raw, {})
