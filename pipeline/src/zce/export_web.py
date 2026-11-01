"""Export step: capacity results -> files the static website loads.

Two files, kept apart on purpose (see docs/PLAN.md, "Geometry and attributes
are kept apart"):

  web/public/data/<city>/parcels.pmtiles   lot shapes only, each with a numeric `pid`
  web/public/data/<city>/parcels.json      every number the map shows, as columns
                                           indexed by the same `pid`

The map draws shapes from the tiles and colors them from the JSON, so a
scenario change in milestone 5 just recomputes numbers in the browser; the
tiles never change.

These files are generated, small (a few MB), and committed, so the site can be
deployed as plain static files without running the pipeline in CI.
"""

import json
import shutil
import subprocess
from datetime import datetime, timezone

import geopandas as gpd
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

# Tile zoom range. Parcels are too small to see at z8, but the colors still
# show where capacity is across cities. 8 is low enough to see all of LA County at once; keep in step with minZoom in web/src/map.ts.
MIN_ZOOM, MAX_ZOOM = 8, 16


def _int_column(series: pd.Series) -> list:
    """Nullable integers -> JSON list with null for unknown."""
    return [None if pd.isna(v) else int(v) for v in series]


def write_tiles(lots: gpd.GeoDataFrame, out_path, work_dir) -> None:
    """Write lot shapes (with only `pid`) to PMTiles using tippecanoe."""
    if shutil.which("tippecanoe") is None:
        raise RuntimeError("tippecanoe is not installed: brew install tippecanoe")
    # Web maps use longitude/latitude (EPSG:4326) input.
    shapes = lots[["pid", "geometry"]].to_crs("EPSG:4326")
    geojson = work_dir / "parcels_for_tiles.geojson"
    shapes.to_file(geojson, driver="GeoJSON")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "tippecanoe",
            "--force",
            f"--output={out_path}",
            "--layer=parcels",
            f"--minimum-zoom={MIN_ZOOM}",
            f"--maximum-zoom={MAX_ZOOM}",
            # Each shape keeps its `pid` as a property; the browser promotes
            # it to the feature id (MapLibre `promoteId`). We don't use
            # tippecanoe's id option because vector tiles reserve id 0.
            # Never drop or merge lots: a missing lot would look like a lot
            # with no capacity. Simplify shapes instead to keep tiles small.
            "--no-feature-limit",
            "--no-tile-size-limit",
            "--simplification=4",
            "--no-tiny-polygon-reduction",
            "--detect-shared-borders",
            "--quiet",
            str(geojson),
        ],
        check=True,
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


def write_addresses(lots: gpd.GeoDataFrame, path) -> None:
    """Address search index, loaded by the browser only when someone searches.

    Situs (property) addresses only; owner mailing addresses are never in
    our data. Each entry has the lot's pid and a point inside the lot to fly
    the map to. Sorted by address so the list reads naturally.
    """
    has_address = lots["address"].fillna("").str.strip() != ""
    sub = lots[has_address]
    points = sub.geometry.representative_point().to_crs("EPSG:4326")
    # "960 SAN PASQUAL ST PASADENA CA 91106" -> "960 SAN PASQUAL ST, 91106":
    # every address here is in Pasadena, so the city name is noise.
    clean = (
        sub["address"].str.strip().str.replace(r"\s+PASADENA\s+CA\s+", ", ", regex=True).str.replace(r"\s+", " ", regex=True)
    )
    order = clean.argsort(kind="stable")
    payload = {
        "address": clean.iloc[order].tolist(),
        "pid": sub["pid"].iloc[order].astype(int).tolist(),
        "lng": [round(p.x, 6) for p in points.iloc[order]],
        "lat": [round(p.y, 6) for p in points.iloc[order]],
    }
    path.write_text(json.dumps(payload, separators=(",", ":")))


def write_city_index() -> None:
    """web/public/data/cities.json: every city with exported data, for the city picker."""
    from zce.config import CITIES_DIR, load_city

    data_root = REPO_ROOT / "web" / "public" / "data"
    cities = []
    for folder in sorted(p for p in CITIES_DIR.iterdir() if (p / "city.yaml").exists()):
        if (data_root / folder.name / "parcels.json").exists():
            c = load_city(folder.name)
            cities.append({"id": c.id, "name": c.name, "center": list(c.map.center), "zoom": c.map.zoom})
    (data_root / "cities.json").write_text(json.dumps(cities, indent=1))


def export_city(city: CityConfig) -> None:
    lots = gpd.read_parquet(DATA_DIR / "out" / city.id / "capacity.parquet")
    # Stable ids: sort by parcel id so the same lot keeps its pid between runs.
    lots = lots.sort_values("parcel_id").reset_index(drop=True)
    lots["pid"] = lots.index.astype(int)

    web_dir = REPO_ROOT / "web" / "public" / "data" / city.id
    work_dir = DATA_DIR / "out" / city.id
    write_tiles(lots, web_dir / "parcels.pmtiles", work_dir)

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
    single_home_share = lots.loc[one_home, "lot_area_sqft"].sum() / lots.loc[residential, "lot_area_sqft"].sum()
    payload = {
        "city": city.name,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
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
            "residential_land_sqft": int(lots.loc[residential, "lot_area_sqft"].sum()),
        },
        # Columns: element i belongs to the lot with pid i.
        "columns": {
            "parcel_id": lots["parcel_id"].tolist(),
            "zone": [zone_index.get(z, -1) if isinstance(z, str) else -1 for z in lots["zone_code"]],
            "existing_units": _int_column(lots["existing_units"]),
            "local_units": _int_column(lots["local_units"]),
            "max_units": _int_column(lots["max_units"]),
            "net_new_units": _int_column(lots["net_new_units"]),
            "binding": binding.astype(int).tolist(),
            # Engine inputs, already rounded in the capacity step, so the
            # browser recomputes from exactly what Python used.
            "lot_area_sqft": [int(v) for v in lots["lot_area_sqft"]],
            "lot_width_ft": [float(v) for v in lots["lot_width_ft"]],
            "lot_depth_ft": [float(v) for v in lots["lot_depth_ft"]],
            "dist_major_transit_ft": _int_column(lots["dist_major_transit_ft"]),
            "dist_single_family_ft": _int_column(lots["dist_single_family_ft"]),
            "rules_zone": [rule_index.get(z, -1) if isinstance(z, str) else -1 for z in lots["rules_zone"]],
            "overlay_set": [overlay_index[tuple(o) if o is not None else ()] for o in lots["overlays"]],
            "district": [district_index.get(d, -1) if isinstance(d, str) else -1 for d in lots["district"]],
            "redev_mask": [int(m) for m in lots["redev_mask"]],
        },
    }
    # separators=(",", ":") drops spaces: about 20% smaller.
    (web_dir / "parcels.json").write_text(json.dumps(payload, separators=(",", ":")))
    write_addresses(lots, web_dir / "addresses.json")

    write_city_index()

    sizes = {p.name: p.stat().st_size for p in web_dir.iterdir()}
    for name, size in sizes.items():
        print(f"  {name}: {size / 1e6:.1f} MB")
