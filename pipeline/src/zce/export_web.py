"""Export step: capacity results -> files the static website loads.

Every lot is only a few numbers, so they travel as compact binary columns:

  web/public/data/<city>/lots.bin.gz     every number the site needs, as columns
  web/public/data/<city>/search.bin.gz   addresses and map points, loaded on the first search
  web/public/data/<city>/rules.json      the rule files, for reform scenarios
  web/public/data/tiles/<group>.pmtiles  lot shapes for many cities, in one file

A lot's color under today's rules is stored in the tiles, so the map draws at
once with no lot data at all. A reform only overrides the lots it changes.

Cities are exported one at a time. `python -m zce tiles` then rebuilds the shared
tiles. Run it after any export, because a lot's number in the tiles depends on
every city before it. The tiles are about 100 MB, so a rebuild adds that much to
the repository's history; do it when publishing, not on every experiment.

These files are generated and committed, so the site can be deployed as plain
static files without running the pipeline in CI.
"""

import gzip
import json
import shutil
import struct
import subprocess

import geopandas as gpd
import numpy as np
import pandas as pd

from zce.config import DATA_DIR, REPO_ROOT, CityConfig
from zce.rules.schema import load_state_overrides, load_zone_rules

# Binding constraints as small integers to keep the JSON compact.
# -1 means "not modeled". The order here is the order the website lists them.
BINDING_CODES = [
    "state_law:sb9",
    "state_law:adu",
    "density",
    "lot_area_per_unit",
    "envelope",
    "parking",
    "use_not_permitted",
]

# Below this zoom, lots are close to a pixel or smaller, so each tile keeps its largest
# lots up to a size limit. Clicking there zooms in instead of opening a lot; keep in
# step with DETAIL_ZOOM in web/src/map.ts. Don't lower --low-detail below 11 to save
# space: small lots snap to a coarse grid and turn into jagged triangles.
DETAIL_ZOOM = 12
OVERVIEW_TILE_BYTES = 500_000

# Tile zoom range. Parcels are too small to see at z8, but the colors still
# show where capacity is across cities. 8 is low enough to see all of LA County at once; keep in step with minZoom in web/src/map.ts.
MIN_ZOOM, MAX_ZOOM = 8, 15


# Stands for "unknown" in integer columns. Keep in step with NA in web/src/data.ts.
NA = -2_147_483_648

# Colors stop changing at 50 homes, so tiles cap their numbers there. Fewer distinct
# values make the tiles smaller. Keep in step with the top classes in web/src/colors.ts.
TILE_CAP = 50

# City of LA gets its own tiles file, because together they'd pass GitHub's 100 MB limit.
OWN_TILES = {"los_angeles": "la"}
SHARED_TILES = "rest"


def _int_column(series: pd.Series) -> np.ndarray:
    """Whole numbers as int32, with NA for unknown."""
    values = pd.to_numeric(series).to_numpy(dtype="float64", na_value=np.nan)
    known = ~np.isnan(values)
    assert (values[known] == np.round(values[known])).all(), "a whole-number column has a fraction"
    return np.where(known, values, NA).astype("int32")


def _tenths_column(series: pd.Series) -> np.ndarray:
    """Lengths stored in tenths of a foot; the browser divides by 10 to get the same number back."""
    values = series.to_numpy(dtype="float64")
    tenths = np.round(values * 10)
    assert (tenths / 10 == values).all(), "a length has more than one decimal"
    return tenths.astype("int32")


def write_lots(path, header: dict, columns: dict[str, np.ndarray]) -> None:
    """One gzip file: header length, JSON header, then each column on an 8-byte boundary."""
    blocks, table, offset = [], [], 0
    for name, array in columns.items():
        raw = array.astype(array.dtype.newbyteorder("<")).tobytes()
        table.append({"name": name, "type": array.dtype.name, "offset": offset, "length": len(array)})
        pad = -len(raw) % 8
        blocks += [raw, b"\0" * pad]
        offset += len(raw) + pad
    head = json.dumps({**header, "columns": table}, separators=(",", ":")).encode()
    head += b" " * (-(4 + len(head)) % 8)
    # mtime=0: the same data always gives the same file, so git stores no new copy.
    path.write_bytes(gzip.compress(struct.pack("<I", len(head)) + head + b"".join(blocks), 9, mtime=0))


def read_lots_header(path) -> dict:
    """The JSON header of a lots file, without reading its columns."""
    with gzip.open(path, "rb") as f:
        size = struct.unpack("<I", f.read(4))[0]
        return json.loads(f.read(size))


def tile_properties(lots: pd.DataFrame) -> pd.DataFrame:
    """What a lot's shape carries: its color under today's rules in every map view.

    m, n and l are homes allowed, new homes and likely new homes, capped at TILE_CAP,
    with -1 for no answer. b is the binding limit (an index into BINDING_CODES).
    """
    modeled = (lots["model_status"] == "ok").to_numpy()

    def capped(series: pd.Series) -> np.ndarray:
        values = pd.to_numeric(series).to_numpy(dtype="float64", na_value=np.nan)
        return np.where(modeled & ~np.isnan(values), np.minimum(np.nan_to_num(values), TILE_CAP), -1).astype("int32")

    binding = lots["binding_constraint"].map(lambda b: BINDING_CODES.index(b) if isinstance(b, str) else -1)
    return pd.DataFrame(
        {
            "m": capped(lots["max_units"]),
            "n": capped(lots["net_new_units"]),
            "l": capped(lots["realistic_new_units"]),
            "b": np.where(modeled, binding.to_numpy(), -1).astype("int32"),
        },
        index=lots.index,
    )


def build_tiles() -> None:
    """Rebuild the shared tiles from every city on the map (`python -m zce tiles`)."""
    if shutil.which("tippecanoe") is None:
        raise RuntimeError("tippecanoe is not installed: brew install tippecanoe")
    data_root = REPO_ROOT / "web" / "public" / "data"
    cities = json.loads((data_root / "cities.json").read_text())
    work_dir = DATA_DIR / "out" / "tiles"
    work_dir.mkdir(parents=True, exist_ok=True)
    tiles_dir = data_root / "tiles"
    tiles_dir.mkdir(exist_ok=True)
    # If tippecanoe gives up it can end this whole process with no error, so remove
    # the old record first: test_tiles_match_the_city_index then fails instead of
    # old tiles passing as new.
    (tiles_dir / "built_for.json").unlink(missing_ok=True)

    streams = {}
    for index, c in enumerate(cities):
        lots = gpd.read_parquet(
            DATA_DIR / "out" / c["id"] / "capacity.parquet",
            columns=["parcel_id", "geometry", "model_status", "max_units", "net_new_units", "realistic_new_units", "binding_constraint"],
        )
        lots = lots.sort_values("parcel_id").reset_index(drop=True)
        assert len(lots) == c["count"], f"{c['id']} changed since its export; export it again"
        shapes = gpd.GeoDataFrame(
            tile_properties(lots).assign(pid=lots.index.astype(int) + c["start"], c=index),
            geometry=lots.geometry.to_crs("EPSG:4326"),
        )
        group = c["tiles"]
        if group not in streams:
            streams[group] = (work_dir / f"{group}.geojsonl").open("w")
        # One feature per line: tippecanoe reads this without holding it all in memory.
        for feature in shapes.iterfeatures(drop_id=True):
            streams[group].write(json.dumps(feature, separators=(",", ":")) + "\n")
        print(f"  {c['id']}: {len(lots):,} lots")
    for stream in streams.values():
        stream.close()

    for group in streams:
        out = tiles_dir / f"{group}.pmtiles"
        source = work_dir / f"{group}.geojsonl"
        common = ["tippecanoe", "--force", "--layer=parcels", "--detect-shared-borders", "--read-parallel", "--quiet"]
        overview, detail = work_dir / f"{group}_overview.mbtiles", work_dir / f"{group}_detail.mbtiles"
        subprocess.run(
            [
                *common,
                f"--output={overview}",
                f"--minimum-zoom={MIN_ZOOM}",
                f"--maximum-zoom={DETAIL_ZOOM - 1}",
                "--simplification=4",
                "--low-detail=11",
                "--no-feature-limit",
                f"--maximum-tile-bytes={OVERVIEW_TILE_BYTES}",
                "--drop-smallest-as-needed",
                str(source),
            ],
            check=True,
        )
        subprocess.run(
            [
                *common,
                f"--output={detail}",
                f"--minimum-zoom={DETAIL_ZOOM}",
                f"--maximum-zoom={MAX_ZOOM}",
                # Keep every lot once they can be told apart: a missing lot would look
                # like a lot with no capacity. Coarser shapes below the top zoom keep
                # tiles small; only slivers are lost at the top zoom.
                "--simplification=4",
                "--low-detail=10",
                "--no-feature-limit",
                "--no-tile-size-limit",
                str(source),
            ],
            check=True,
        )
        subprocess.run(["tile-join", "--force", "--quiet", "--no-tile-size-limit", f"--output={out}", str(overview), str(detail)], check=True)
        source.unlink()
        overview.unlink()
        detail.unlink()
        print(f"  {out.name}: {out.stat().st_size / 1e6:.1f} MB")
    # What these tiles were built for. A test compares it with cities.json.
    (tiles_dir / "built_for.json").write_text(
        json.dumps([[c["id"], c["tiles"], c["start"], c["count"]] for c in cities], indent=0)
    )


def write_rules(city: CityConfig, path) -> None:
    """Rule files, state law and assumptions as one JSON file for the browser engine."""
    rules = load_zone_rules(city.rules_dir)
    state = load_state_overrides(city.state_law_file)
    payload = {
        "zones": {z: r.model_dump(mode="json") for z, r in rules.items()},
        "state": state.model_dump(mode="json"),
        "assumptions": {
            "gross_sqft_per_unit": city.assumptions.gross_sqft_per_unit,
            "parking_stall_sqft": city.assumptions.parking_stall_sqft,
            "min_home_sqft": city.assumptions.min_home_sqft,
        },
        "redevelopment": city.redevelopment.model_dump(),
    }
    path.write_text(json.dumps(payload, separators=(",", ":")))


def write_search(lots: gpd.GeoDataFrame, path) -> None:
    """Search file, loaded by the browser only when someone searches.

    Situs (property) addresses only; owner mailing addresses are never in our
    data. Line i of the text is the lot with pid i, blank if it has no address, so
    its parcel number can still be searched. The points, inside each lot, are where
    the map flies to.
    """
    points = lots.geometry.representative_point().to_crs("EPSG:4326")
    # "960 SAN PASQUAL ST PASADENA CA 91106" -> "960 SAN PASQUAL ST, 91106":
    # every address here is in Pasadena, so the city name is noise.
    clean = (
        lots["address"].fillna("").str.strip().str.replace(r"\s+PASADENA\s+CA\s+", ", ", regex=True).str.replace(r"\s+", " ", regex=True)
    )
    text = "\n".join(clean).encode()
    write_lots(
        path,
        {"text_length": len(text)},
        {
            "lng": points.x.to_numpy().astype("float32"),
            "lat": points.y.to_numpy().astype("float32"),
            "text": np.frombuffer(text, dtype="uint8"),
        },
    )


# Cities the owner has kept off the map whatever their level, and why.
HELD_OFF_MAP = {
    "avalon": "on Catalina Island, where wildlife restrictions limit development and the rule files don't model them",
}


def coverage_levels(path=None) -> dict[str, str]:
    """Each city's level from the coverage table `python -m zce release` writes."""
    path = path or REPO_ROOT / "reports" / "la_county" / "coverage.csv"
    if not path.exists():
        return {}
    return dict(pd.read_csv(path, usecols=["city_id", "coverage_level"]).values)


def write_city_index() -> None:
    """web/public/data/cities.json: exported cities for the city picker and the map.

    Partial cities stay off the map even if their files exist: their totals run
    low because the plans where they build most are missing. A city not yet in
    the coverage table is listed without a level.

    `tiles` and `start` say where a city's lots are in the shared tiles: its lot
    with pid i is lot start + i there.
    """
    from zce.config import CITIES_DIR, load_city

    data_root = REPO_ROOT / "web" / "public" / "data"
    levels = coverage_levels()
    cities = []
    starts: dict[str, int] = {}
    for folder in sorted(p for p in CITIES_DIR.iterdir() if (p / "city.yaml").exists()):
        lots_file = data_root / folder.name / "lots.bin.gz"
        if lots_file.exists():
            level = levels.get(folder.name)
            if folder.name in HELD_OFF_MAP:
                print(f"  {folder.name} is held off the map: {HELD_OFF_MAP[folder.name]}")
                continue
            if level == "Partial":
                print(f"  {folder.name} is rated Partial, so it stays off the map")
                continue
            c = load_city(folder.name)
            header = read_lots_header(lots_file)
            group = OWN_TILES.get(folder.name, SHARED_TILES)
            entry = {
                "id": c.id, "name": c.name, "center": list(c.map.center), "zoom": c.map.zoom,
                "bounds": header["bounds"], "count": header["count"], "tiles": group, "start": starts.get(group, 0),
            }
            starts[group] = entry["start"] + entry["count"]
            if level:
                entry["level"] = level
            cities.append(entry)
    (data_root / "cities.json").write_text(json.dumps(cities, indent=1))


def export_city(city: CityConfig) -> None:
    lots = gpd.read_parquet(DATA_DIR / "out" / city.id / "capacity.parquet")
    # Stable ids: sort by parcel id so the same lot keeps its pid between runs.
    lots = lots.sort_values("parcel_id").reset_index(drop=True)
    lots["pid"] = lots.index.astype(int)

    web_dir = REPO_ROOT / "web" / "public" / "data" / city.id
    web_dir.mkdir(parents=True, exist_ok=True)

    write_rules(city, web_dir / "rules.json")

    zones = sorted(z for z in lots["zone_code"].dropna().unique())
    zone_index = {z: i for i, z in enumerate(zones)}
    districts = sorted(d for d in lots["district"].dropna().unique())
    district_index = {d: i for i, d in enumerate(districts)}
    rule_zones = sorted(z for z in lots["rules_zone"].dropna().unique())
    rule_index = {z: i for i, z in enumerate(rule_zones)}
    # Overlays only matter to the engine as a set per lot; store each
    # distinct set once and give lots an index into that list.
    overlay_sets = sorted({tuple(o) if o is not None else () for o in lots["overlays"]})
    overlay_index = {o: i for i, o in enumerate(overlay_sets)}

    binding = lots["binding_constraint"].map(lambda b: BINDING_CODES.index(b) if isinstance(b, str) else -1)

    ok = lots["model_status"] == "ok"
    # Share of residential land where local zoning allows only one home
    # (same definition as capacity_report.md).
    residential = ok & (lots["binding_constraint"] != "use_not_permitted")
    one_home = residential & (lots["local_units"] <= 1)
    residential_land = lots.loc[residential, "lot_area_sqft"].sum()
    # A city with no rule files yet has no residential land (and JSON has no NaN).
    single_home_share = lots.loc[one_home, "lot_area_sqft"].sum() / residential_land if residential_land else 0
    # Parcel numbers are stored as numbers. The few that aren't plain digits
    # (blank or repeated numbers) are listed by pid instead.
    ids = lots["parcel_id"].astype(str)
    plain = ids.str.fullmatch(r"[1-9]\d{9}")
    header = {
        "city": city.name,
        "count": len(lots),
        # [west, south, east, north], so the map can frame several cities at once.
        "bounds": [round(float(v), 5) for v in lots.to_crs("EPSG:4326").total_bounds],
        "codes": {
            "binding": BINDING_CODES,
            "zone": zones,
            "rules_zone": rule_zones,
            "district": districts,
            "overlay_sets": [list(o) for o in overlay_sets],
        },
        "headline": {
            "existing_units": int(lots.loc[ok, "existing_units"].sum()),
            "local_units": int(lots.loc[ok, "local_units"].sum()),
            "max_units": int(lots.loc[ok, "max_units"].sum()),
            "net_new_units": int(lots.loc[ok, "net_new_units"].sum()),
            "lots_modeled": int(ok.sum()),
            "lots_not_modeled": int((~ok).sum()),
            "single_home_land_share": round(float(single_home_share), 3),
            # Lets the site combine this share across cities, weighted by land.
            "residential_land_sqft": int(residential_land),
        },
        "parcel_id_exceptions": {str(i): ids.iloc[i] for i in np.flatnonzero(~plain.to_numpy())},
    }
    # Element i of every column belongs to the lot with pid i. Lengths are in tenths
    # of a foot. Engine inputs were already rounded in the capacity step, so the
    # browser recomputes from exactly what Python used.
    columns = {
        "parcel_id": pd.to_numeric(ids.where(plain)).to_numpy(dtype="float64"),
        "zone": np.array([zone_index.get(z, -1) if isinstance(z, str) else -1 for z in lots["zone_code"]], dtype="int16"),
        "existing_units": _int_column(lots["existing_units"]),
        "building_sqft": _int_column(lots["building_sqft"]),
        "local_units": _int_column(lots["local_units"]),
        "max_units": _int_column(lots["max_units"]),
        "net_new_units": _int_column(lots["net_new_units"]),
        "binding": binding.to_numpy().astype("int8"),
        "lot_area_sqft": _int_column(lots["lot_area_sqft"]),
        "lot_width_tenths": _tenths_column(lots["lot_width_ft"]),
        "lot_depth_tenths": _tenths_column(lots["lot_depth_ft"]),
        "dist_major_transit_ft": _int_column(lots["dist_major_transit_ft"]),
        "dist_single_family_ft": _int_column(lots["dist_single_family_ft"]),
        "dist_sb79_t1_ft": _int_column(lots["dist_sb79_t1_ft"]),
        "dist_sb79_t2_ft": _int_column(lots["dist_sb79_t2_ft"]),
        "sb79_zone_ok": lots["sb79_zone_ok"].astype(int).to_numpy().astype("int8"),
        "sb79_half_mile": lots["sb79_half_mile"].astype(int).to_numpy().astype("int8"),
        "rules_zone": np.array([rule_index.get(z, -1) if isinstance(z, str) else -1 for z in lots["rules_zone"]], dtype="int16"),
        "overlay_set": np.array([overlay_index[tuple(o) if o is not None else ()] for o in lots["overlays"]], dtype="int32"),
        "district": np.array([district_index.get(d, -1) if isinstance(d, str) else -1 for d in lots["district"]], dtype="int16"),
        "redev_mask": lots["redev_mask"].astype(int).to_numpy().astype("uint8"),
    }
    write_lots(web_dir / "lots.bin.gz", header, columns)
    write_search(lots, web_dir / "search.bin.gz")

    write_city_index()

    sizes = {p.name: p.stat().st_size for p in web_dir.iterdir()}
    for name, size in sizes.items():
        print(f"  {name}: {size / 1e6:.1f} MB")
