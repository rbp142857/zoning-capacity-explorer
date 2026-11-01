"""Download raw data listed in a city's city.yaml.

Raw data is never committed to git. Instead, this module re-downloads it and
writes a small `_manifest.json` recording when each file was fetched, from
where, and how many features it had, so results can always be traced back to
a dated source (METHODOLOGY.md cites these dates).
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from zce.config import CityConfig, Source

# Be polite to public servers: identify ourselves and do not hammer them.
HEADERS = {"User-Agent": "zoning-capacity-explorer (open-source research tool)"}
PAUSE_SECONDS = 0.2


def _get_json(url: str, params: dict) -> dict:
    """GET a URL and return JSON, retrying a few times on network hiccups."""
    for attempt in range(4):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            # ArcGIS reports errors inside a 200 response, so check for that too.
            if "error" in data:
                raise RuntimeError(f"ArcGIS error from {url}: {data['error']}")
            return data
        except (requests.RequestException, ValueError) as exc:
            if attempt == 3:
                raise
            wait = 2**attempt
            print(f"  retrying in {wait}s after: {exc}")
            time.sleep(wait)
    raise AssertionError("unreachable")


def download_arcgis_layer(source: Source, out_path: Path, geometry: bool = True) -> int:
    """Download every feature of an ArcGIS layer to a GeoJSON file
    (or, with geometry=False, a JSON list of attribute records).

    ArcGIS servers return at most `maxRecordCount` features per request (often
    1,000), so we page through results with `resultOffset`, ordered by
    the layer's ID field so pages never overlap or skip features.
    """
    layer_info = _get_json(source.url, {"f": "json"})
    page_size = layer_info.get("maxRecordCount", 1000)
    # The ID field is usually OBJECTID but not always (e.g. "FID"), so ask.
    id_field = layer_info.get("objectIdField") or next(
        f["name"] for f in layer_info["fields"] if f["type"] == "esriFieldTypeOID"
    )
    expected = _get_json(
        f"{source.url}/query",
        {"where": source.where, "returnCountOnly": "true", "f": "json"},
    )["count"]

    features: list[dict] = []
    while len(features) < expected:
        page = _get_json(
            f"{source.url}/query",
            {
                "where": source.where,
                "outFields": "*",
                "outSR": 4326,  # GeoJSON is always lon/lat (EPSG:4326)
                "orderByFields": id_field,
                "resultOffset": len(features),
                "resultRecordCount": page_size,
                "returnGeometry": "true" if geometry else "false",
                "f": "geojson" if geometry else "json",
            },
        )
        batch = page.get("features", [])
        if not geometry:
            batch = [f["attributes"] for f in batch]
        if not batch:
            break
        features.extend(batch)
        print(f"  {len(features):,} / {expected:,}", end="\r")
        time.sleep(PAUSE_SECONDS)
    print()

    if len(features) != expected:
        raise RuntimeError(
            f"Expected {expected} features from {source.url} but got {len(features)}"
        )
    payload = {"type": "FeatureCollection", "features": features} if geometry else features
    out_path.write_text(json.dumps(payload))
    return len(features)


def download_ckan(source: Source, out_path: Path) -> int:
    """All matching rows of a CKAN datastore table (data.ca.gov), paged."""
    records: list[dict] = []
    while True:
        page = _get_json(
            f"{source.url}/api/3/action/datastore_search",
            {"resource_id": source.resource_id, "filters": json.dumps(source.filters),
             "limit": 1000, "offset": len(records)},
        )["result"]
        records.extend(page["records"])
        if len(records) >= page["total"] or not page["records"]:
            break
        time.sleep(PAUSE_SECONDS)
    out_path.write_text(json.dumps(records))
    return len(records)


def download_file(source: Source, out_path: Path) -> int:
    resp = requests.get(source.url, headers=HEADERS, timeout=300)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    return len(resp.content)


def download_city(city: CityConfig, only: list[str] | None = None) -> None:
    city.raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = city.raw_dir / "_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    for name, source in city.sources.items():
        if only and name not in only:
            continue
        if source.kind == "manual":
            out = city.raw_dir / (source.filename or Path(source.url).name)
            if not out.exists():
                print(f"MANUAL DOWNLOAD NEEDED for '{name}': this server doesn't allow automated downloads.\n"
                      f"  1. Open {source.url} in your browser\n  2. Save the file as {out}")
                continue
            print(f"Found manually downloaded {name}: {out.name}")
            size, unit = out.stat().st_size, "bytes"
            manifest[name] = {"url": source.url, "where": "", "file": out.name, unit: size,
                              "downloaded_at": datetime.fromtimestamp(out.stat().st_mtime, timezone.utc).isoformat(timespec="seconds"),
                              "publisher": source.publisher, "license": source.license}
            manifest_path.write_text(json.dumps(manifest, indent=2))
            continue
        print(f"Downloading {name} from {source.url}")
        if source.kind == "arcgis" and not source.geometry:
            out = city.raw_dir / f"{name}.json"
            size = download_arcgis_layer(source, out, geometry=False)
            unit = "records"
        elif source.kind == "arcgis":
            out = city.raw_dir / f"{name}.geojson"
            size = download_arcgis_layer(source, out)
            unit = "features"
        elif source.kind == "ckan":
            out = city.raw_dir / f"{name}.json"
            size = download_ckan(source, out)
            unit = "records"
        else:
            out = city.raw_dir / Path(source.url).name
            size = download_file(source, out)
            unit = "bytes"
        manifest[name] = {
            "url": source.url,
            "where": source.where,
            "file": out.name,
            unit: size,
            "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "publisher": source.publisher,
            "license": source.license,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2))
