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
        export_web.write_lots(data_root / city / "lots.bin.gz", {"count": 2, "bounds": [0, 0, 1, 1]}, {})
    table = tmp_path / "reports" / "la_county" / "coverage.csv"
    table.parent.mkdir(parents=True)
    table.write_text("city_id,coverage_level\nburbank,Fuller\nazusa,Partial\navalon,Usable\n")
    monkeypatch.setattr(export_web, "REPO_ROOT", tmp_path)

    export_web.write_city_index()

    listed = json.loads((data_root / "cities.json").read_text())
    assert [(c["id"], c["level"]) for c in listed] == [("burbank", "Fuller")]


def test_lots_file_round_trip(tmp_path):
    import gzip
    import struct

    import numpy as np

    from zce import export_web

    path = tmp_path / "lots.bin.gz"
    export_web.write_lots(path, {"count": 3}, {"a": np.array([1, export_web.NA, 3], dtype="int32"), "b": np.array([7, 8, 9], dtype="uint8")})
    assert export_web.read_lots_header(path)["count"] == 3
    raw = gzip.decompress(path.read_bytes())
    size = struct.unpack("<I", raw[:4])[0]
    assert (4 + size) % 8 == 0  # columns start on an 8-byte boundary
    header = json.loads(raw[4 : 4 + size])
    b = next(c for c in header["columns"] if c["name"] == "b")
    assert b["offset"] % 8 == 0
    assert list(raw[4 + size + b["offset"] :][:3]) == [7, 8, 9]


def test_tiles_match_the_city_index():
    # A lot's number in the tiles depends on every city before it. If this fails,
    # run `python -m zce tiles`, or the map would color the wrong lots.
    root = R.REPO_ROOT / "web" / "public" / "data"
    cities = json.loads((root / "cities.json").read_text())
    built = json.loads((root / "tiles" / "built_for.json").read_text())
    for group in {c["tiles"] for c in cities}:
        assert (root / "tiles" / f"{group}.pmtiles").stat().st_size < 100_000_000  # GitHub's limit per file
    assert [[c["id"], c["tiles"], c["start"], c["count"]] for c in cities] == built


def test_tile_colors_cap_at_the_top_class():
    import pandas as pd

    from zce import export_web

    lots = pd.DataFrame({
        "model_status": ["ok", "ok", "not_modeled"],
        "max_units": [120, 3, None], "net_new_units": [None, 2, None], "realistic_new_units": [60, 0, 0],
        "binding_constraint": ["density", "state_law:adu", None],
    })
    p = export_web.tile_properties(lots)
    assert p["m"].tolist() == [50, 3, -1]
    assert p["n"].tolist() == [-1, 2, -1]  # unknown existing homes: no answer
    assert p["l"].tolist() == [50, 0, -1]
    assert p["b"].tolist() == [export_web.BINDING_CODES.index("density"), export_web.BINDING_CODES.index("state_law:adu"), -1]
