"""SCAG's official SB 79 stops, and which lots can use them.

SCAG publishes the map SB 79 requires, with each stop's tier. We keep one copy
for the county, since cities' lots can use stops across their borders.
"""

import json
import re
import urllib.parse
import urllib.request

import geopandas as gpd

from zce.config import DATA_DIR

URL = "https://maps.scag.ca.gov/scaggis/rest/services/SB79/SB79/MapServer/0/query"
# SB 79 covers sites zoned residential, mixed or commercial (§65912.157(a)).
_ELIGIBLE = re.compile(r"residential|commercial|suburban", re.I)
_NOT_ELIGIBLE = re.compile(r"industr", re.I)


def zone_eligible(category) -> bool:
    return isinstance(category, str) and bool(_ELIGIBLE.search(category)) and not _NOT_ELIGIBLE.search(category)


def _stops_path():
    path = DATA_DIR / "raw" / "_sb79" / "stops.geojson"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        query = urllib.parse.urlencode({"where": "1=1", "outFields": "STOP_NAME,SB79_TIER,TRN_MODE", "outSR": 4326, "f": "geojson"})
        with urllib.request.urlopen(f"{URL}?{query}", timeout=60) as r:
            data = json.load(r)
        if not data.get("features") or data.get("exceededTransferLimit"):
            raise RuntimeError("SCAG's SB 79 stops came back empty or cut off")
        path.write_text(json.dumps(data))
    return path


def half_mile_lots(parcels: gpd.GeoDataFrame):
    """Which lots touch SCAG's half-mile zones.

    SB 79's quarter-to-half-mile band covers only cities of 35,000 or more
    (§65912.157(a)), and SCAG's zones already leave smaller cities out.
    """
    path = DATA_DIR / "raw" / "_sb79" / "zones.geojson"
    if not path.exists():
        query = urllib.parse.urlencode({"where": "BUFFER='0.5 Miles'", "outFields": "NAME", "outSR": 4326, "f": "geojson"})
        with urllib.request.urlopen(f"{URL.replace('/0/query', '/1/query')}?{query}", timeout=120) as r:
            data = json.load(r)
        if not data.get("features") or data.get("exceededTransferLimit"):
            raise RuntimeError("SCAG's SB 79 zones came back empty or cut off")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    zones = gpd.read_file(path).to_crs(parcels.crs).geometry.union_all()
    return parcels.geometry.intersects(zones)


def load_stops(tier: str, crs) -> gpd.GeoDataFrame:
    """Stops of one tier ("T1" or "T2") in the given CRS."""
    stops = gpd.read_file(_stops_path())
    return stops[stops["SB79_TIER"] == tier].to_crs(crs)[["STOP_NAME", "geometry"]]
