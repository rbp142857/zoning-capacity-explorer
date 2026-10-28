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


def download_arcgis_layer(source: Source, out_path: Path) -> int:
    """Download every feature of an ArcGIS layer to a GeoJSON file.

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
                "f": "geojson",
            },
        )
        batch = page.get("features", [])
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
    out_path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    return len(features)


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
        print(f"Downloading {name} from {source.url}")
        if source.kind == "arcgis":
            out = city.raw_dir / f"{name}.geojson"
            size = download_arcgis_layer(source, out)
            unit = "features"
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
