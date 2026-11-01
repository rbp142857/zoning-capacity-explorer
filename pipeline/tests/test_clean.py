"""Clean-step helpers that don't need the data download."""

import pandas as pd

from zce.clean import apply_zone_splits
from zce.config import ZoneSplit


def split(zone, pattern, to):
    return ZoneSplit(zone=zone, address_pattern=pattern, to=to, reason="test")


def test_zone_splits_first_match_wins_and_others_are_kept():
    splits = [
        split("GC", "PICO BLVD", "GC-PICO"),
        split("GC", "LINCOLN BLVD|90405", "GC-LINCOLN"),
        split("GC", "", "GC-SMB"),  # empty pattern: every remaining GC lot
    ]
    zones = pd.Series(["GC", "GC", "GC", "GC", "R2", None])
    addresses = pd.Series([
        "2000 PICO BLVD SANTA MONICA CA 90405",  # matches Pico first, though also 90405
        "1500 lincoln blvd santa monica ca 90401",  # case doesn't matter
        "700 HILL ST SANTA MONICA CA 90405",
        None,  # no address: only the catch-all matches
        "1000 PICO BLVD SANTA MONICA CA 90405",  # not GC, unchanged
        "1 MAIN ST",
    ])
    out = apply_zone_splits(zones, addresses, splits)
    assert out.tolist()[:5] == ["GC-PICO", "GC-LINCOLN", "GC-LINCOLN", "GC-SMB", "R2"]
    assert pd.isna(out.iloc[5])  # no zone stays missing
