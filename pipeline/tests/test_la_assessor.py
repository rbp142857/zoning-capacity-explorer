import math

import pandas as pd

from shapely.geometry import box

from conftest import CRS, raw_assessor_row
from zce.adapters.la_assessor import WHITELIST, load_parcels, unique_parcel_ids


def test_lot_area_is_computed_in_square_feet(write_raw_parcels, lot):
    lots, _ = load_parcels(write_raw_parcels([raw_assessor_row("1", lot)]), CRS)
    # 50 ft x 100 ft. Allow a tiny error from the round trip through lon/lat.
    assert math.isclose(lots.loc[0, "lot_area_sqft"], 5_000, rel_tol=1e-4)


def test_personal_columns_are_dropped(write_raw_parcels, lot):
    # Even if the county added owner columns, the whitelist must drop them.
    row = raw_assessor_row("1", lot, OwnerName="JANE DOE", MailAddress="1 PRIVATE LN")
    lots, _ = load_parcels(write_raw_parcels([row]), CRS)
    published = set(lots.columns)
    assert "OwnerName" not in published and "MailAddress" not in published
    assert not any("owner" in c.lower() or "mail" in c.lower() for c in published)
    assert set(WHITELIST.values()) <= published


def test_buildings_are_summed_and_oldest_year_kept(write_raw_parcels, lot):
    # A house (1 unit, 1925) plus a back unit (1 unit, 1990) on the same lot.
    row = raw_assessor_row("1", lot, units1=1, year1=1925, sqft1=1200, Units2=1, YearBuilt2=1990, SQFTmain2=500)
    lots, _ = load_parcels(write_raw_parcels([row]), CRS)
    assert lots.loc[0, "existing_units"] == 2
    assert lots.loc[0, "building_sqft"] == 1700
    assert lots.loc[0, "year_built"] == 1925


def test_missing_building_data_stays_unknown_not_zero(write_raw_parcels, lot):
    row = raw_assessor_row("1", lot, units1=None, year1=None, sqft1=None)
    lots, _ = load_parcels(write_raw_parcels([row]), CRS)
    assert math.isnan(lots.loc[0, "existing_units"])


def test_year_zero_means_unknown(write_raw_parcels, lot):
    lots, _ = load_parcels(write_raw_parcels([raw_assessor_row("1", lot, year1=0)]), CRS)
    assert math.isnan(lots.loc[0, "year_built"])


def test_condo_stack_becomes_one_lot(write_raw_parcels, lot):
    # Three condo units drawn on the same polygon, plus one ordinary house next door.
    rows = [raw_assessor_row(str(i), lot, parcel_type=1,
                             SitusFullAddress=f"10 MAIN ST NO {i} PASADENA CA 91101") for i in (3, 1, 2)]
    rows.append(raw_assessor_row("9", box(100, 0, 150, 100)))
    lots, stats = load_parcels(write_raw_parcels(rows), CRS)

    assert len(lots) == 2
    assert stats["condo_records_merged"] == 2
    condo = lots[lots["is_condo"]].iloc[0]
    assert condo["ain_count"] == 3
    assert condo["existing_units"] == 3
    assert condo["parcel_id"] == "1"  # the lowest AIN represents the lot
    assert condo["land_value"] == 3 * 400_000
    assert condo["address"] == "10 MAIN ST PASADENA CA 91101"  # unit number removed


def test_unique_parcel_ids_keeps_every_lot():
    ids = pd.Series(["111", "222", "111", " ", None])
    assert unique_parcel_ids(ids).tolist() == ["111", "222", "111-2", "unnumbered", "unnumbered-2"]
