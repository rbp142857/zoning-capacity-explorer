"""Shared test helpers: tiny hand-made parcels so every expected number can be
checked with a calculator.

All test geometry is in EPSG:2229 (feet), so a 50 x 100 box is 5,000 sq ft.
"""

import geopandas as gpd
import pytest
from shapely.geometry import box

CRS = "EPSG:2229"


def raw_assessor_row(ain, geom, units1=1, year1=1950, sqft1=1500, parcel_type=0, **extra):
    """One fake Assessor record with the columns the adapter reads."""
    row = {
        "AIN": ain, "SitusFullAddress": f"{ain} TEST ST PASADENA CA 91101", "UseCode": "0100",
        "UseType": "Residential", "UseDescription": "Single", "ParcelTypeCode": parcel_type,
        "Roll_Year": "2026", "Roll_LandValue": 400_000, "Roll_ImpValue": 200_000, "Roll_LandBaseYear": 1990,
        "Units1": units1, "YearBuilt1": year1, "SQFTmain1": sqft1, "geometry": geom,
    }
    for i in range(2, 6):
        row.update({f"Units{i}": None, f"YearBuilt{i}": None, f"SQFTmain{i}": None})
    row.update(extra)
    return row


@pytest.fixture
def write_raw_parcels(tmp_path):
    """Write fake Assessor rows to a GeoJSON file, like the real download."""
    def _write(rows):
        gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs=CRS).to_crs("EPSG:4326")
        path = tmp_path / "parcels.geojson"
        gdf.to_file(path, driver="GeoJSON")
        return path
    return _write


@pytest.fixture
def lot():
    """A 50 ft x 100 ft lot (5,000 sq ft) at the origin."""
    return box(0, 0, 50, 100)
