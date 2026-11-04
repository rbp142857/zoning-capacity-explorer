"""Public release: nothing private goes out, and the trust levels mean what the docs say."""

import json

import pytest

from zce import release as R


def test_no_private_columns_in_lot_files():
    assert not [c for c in R.LOT_COLUMNS if R.FORBIDDEN.search(c)]


@pytest.mark.parametrize("modeled, approval, year, want", [
    (0.97, 0.9, 2024, "Fuller"), (0.97, 0.9, None, "Fuller"), (0.97, 0.9, 2016, "Usable"),
    (0.97, 0.5, 2024, "Usable"), (0.90, 0.9, 2024, "Usable"), (0.80, 1.0, 2024, "Partial"),
])
def test_coverage_level(modeled, approval, year, want):
    assert R.coverage_level(modeled, approval, year) == want


@pytest.mark.parametrize("value, year", [(1468972800000, 2016), (1111708800000, 2005), (2021, 2021), ("2018", 2018), (None, None), ("n/a", None)])
def test_map_year_reads_scag_dates_and_plain_years(value, year):
    assert R.map_year(value) == year


def test_hand_check_counts():
    text = "# Hand-checked parcels\n### 1. A\n### 2. B\n# Glendale (5 lots)\n### G-1\n## Los Angeles (single-family zones)\n### L-1\n## Los Angeles (Chapter 1A)\n### L-2\n"
    assert R.hand_check_counts(text) == {"pasadena": 2, "glendale": 1, "los angeles": 2}


def test_partial_cities_stay_off_the_map(tmp_path, monkeypatch):
    from zce import export_web

    data_root = tmp_path / "web" / "public" / "data"
    # azusa is rated Partial in this table; avalon is held off whatever its level.
    for city in ["burbank", "azusa", "avalon"]:
        (data_root / city).mkdir(parents=True)
        (data_root / city / "parcels.json").write_text("{}")
    table = tmp_path / "reports" / "la_county" / "coverage.csv"
    table.parent.mkdir(parents=True)
    table.write_text("city_id,coverage_level\nburbank,Fuller\nazusa,Partial\navalon,Usable\n")
    monkeypatch.setattr(export_web, "REPO_ROOT", tmp_path)

    export_web.write_city_index()

    listed = json.loads((data_root / "cities.json").read_text())
    assert [(c["id"], c["level"]) for c in listed] == [("burbank", "Fuller")]
