"""Capacity step: cleaned parcels + rule files -> capacity per lot.

Input:  data.nosync/clean/<city>/parcels.parquet  (from `make clean`)
Output: data.nosync/out/<city>/capacity.parquet
Report: reports/<city>/capacity_report.md

This is the only place that connects the GIS world (GeoDataFrames) to the
engine (plain numbers): it turns each row into an engine `Lot`, picks the
zone's rules, and stores the engine's answer back as columns.
"""

import geopandas as gpd
import pandas as pd

from zce import spatial
from zce.capacity_report import write_capacity_report
from zce.config import DATA_DIR, REPO_ROOT, CityConfig
from zce.engine import EngineAssumptions, Lot, compute_capacity
from zce.engine.redevelop import redevelopment, screens_from_config, static_mask
from zce.rules.schema import load_state_overrides, load_zone_rules

LIMIT_NAMES = ["density", "lot_area_per_unit", "envelope", "parking", "state_adu", "state_sb9"]


def round_engine_inputs(parcels: pd.DataFrame) -> pd.DataFrame:
    """Round the numbers the engine reads, once, here.

    The browser receives these values rounded (to keep the download small)
    and recomputes capacity from them. Rounding them here too means Python
    and the browser compute from identical inputs, so their answers match
    exactly. The precision (1 sq ft, 0.1 ft, 1 ft) is far finer than the
    accuracy of the parcel data.
    """
    out = parcels.copy()
    out["lot_area_sqft"] = out["lot_area_sqft"].round(0)
    out["lot_width_ft"] = out["lot_width_ft"].round(1)
    out["lot_depth_ft"] = out["lot_depth_ft"].round(1)
    out["dist_major_transit_ft"] = out["dist_major_transit_ft"].round(0)
    return out


def _number_or_none(x):
    return None if pd.isna(x) else float(x)


def rules_for_lot(row, rules: dict):
    """Which rule file applies to a lot, and any simplification flags.

    Inside a specific plan, Pasadena's base-district standards apply unless
    the plan supersedes them (§17.22.060). In the MVP we apply the base
    district's rules when one exists (e.g. "CD-RM-32" -> RM-32) and flag the
    lot; plan-only districts such as MU-C are "not modeled" until their own
    rule files are written.
    """
    flags = []
    base = row["base_zone"]
    if isinstance(base, str) and base.startswith("PD"):
        return None, ["planned_development_not_modeled"]
    zone_rules = rules.get(base) if isinstance(base, str) else None
    if zone_rules is not None and isinstance(row["specific_plan"], str):
        flags.append("specific_plan_base_rules_used")
    if any(o.startswith("HD") for o in (row["overlays"] if row["overlays"] is not None else [])):
        flags.append("hillside_overlay_not_modeled")
    return zone_rules, flags


def run_capacity(city: CityConfig) -> gpd.GeoDataFrame:
    parcels = gpd.read_parquet(city.clean_dir / "parcels.parquet")
    rules = load_zone_rules(city.rules_dir)
    state = load_state_overrides(city.state_law_file)
    a = EngineAssumptions(
        gross_sqft_per_unit=city.assumptions.gross_sqft_per_unit,
        parking_stall_sqft=city.assumptions.parking_stall_sqft,
    )
    screens = screens_from_config(city.redevelopment)
    print(f"Loaded {len(rules)} zone rule files and {len(state.laws)} state laws")

    parcels = parcels.join(spatial.lot_dimensions(parcels))
    parcels = round_engine_inputs(parcels)

    records = []
    for row in parcels.itertuples(index=False):
        row = row._asdict()
        zone_rules, flags = rules_for_lot(row, rules)
        lot = Lot(
            area_sqft=row["lot_area_sqft"],
            width_ft=row["lot_width_ft"],
            depth_ft=row["lot_depth_ft"],
            overlays=tuple(row["overlays"]) if row["overlays"] is not None else (),
            dist_major_transit_ft=_number_or_none(row["dist_major_transit_ft"]),
            existing_units=_number_or_none(row["existing_units"]),
        )
        result = compute_capacity(zone_rules, lot, a, state)
        mask = static_mask(
            screens,
            year_built=_number_or_none(row["year_built"]),
            land_value=_number_or_none(row["land_value"]),
            improvement_value=_number_or_none(row["improvement_value"]),
            existing_units=lot.existing_units,
            is_condo=bool(row["is_condo"]),
            overlays=lot.overlays,
            single_family_zone=zone_rules is not None and zone_rules.family == "single_family",
        )
        redev = redevelopment(screens, mask, result.local_units, lot.existing_units)
        if result.status == "not_modeled" and "planned_development_not_modeled" in flags:
            result.flags = []  # the PD flag already says why
        records.append(
            {
                "model_status": result.status,
                "rules_zone": zone_rules.zone if zone_rules else None,
                "max_units": result.max_units,
                "local_units": result.local_units,
                "net_new_units": result.net_new_units,
                "binding_constraint": result.binding_constraint,
                "local_binding_constraint": result.local_binding_constraint,
                "state_laws_applied": result.state_laws_applied,
                **{f"limit_{k}": result.limits.get(k) for k in LIMIT_NAMES},
                "capacity_flags": flags + result.flags,
                "redev_mask": mask,
                "likely_redevelop": redev.likely,
                "realistic_new_units": redev.realistic_new_units,
                "redev_failed": list(redev.failed),
            }
        )
    out = parcels.join(pd.DataFrame(records, index=parcels.index))
    # Integer columns that may hold "unknown" use pandas' nullable Int64.
    for col in ["max_units", "local_units", "net_new_units"] + [f"limit_{k}" for k in LIMIT_NAMES]:
        out[col] = out[col].astype("Int64")

    # Sanity checks (see the brief): nothing negative, nothing dropped.
    assert len(out) == len(parcels)
    assert not (out["max_units"] < 0).any(), "negative capacity"
    assert not (out["net_new_units"] < 0).any(), "negative net new units"
    assert out["model_status"].notna().all()

    out_dir = DATA_DIR / "out" / city.id
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_parquet(out_dir / "capacity.parquet")
    print(f"Wrote {out_dir / 'capacity.parquet'}")

    report = REPO_ROOT / "reports" / city.id / "capacity_report.md"
    write_capacity_report(out, rules, state, city, report)
    print(f"Wrote {report}")
    return out
