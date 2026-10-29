"""Golden file: Python's answers that the browser engine must reproduce.

shared/fixtures/golden.json holds
  - lots: their engine inputs (a sample of real Pasadena lots plus hand-made
    edge cases), and
  - for each scenario, Python's result for every lot.

web/src/engine/parity.test.ts runs the TypeScript engine on the same inputs
and fails if any number differs. pipeline/tests/test_golden.py fails if the
file is out of date with the Python engine, so you're reminded to run
`make golden` after changing the engine, the rules, or the scenarios here.
"""

import json
import random
from dataclasses import asdict

import pandas as pd

from zce.config import DATA_DIR, REPO_ROOT, CityConfig, load_city
from zce.engine import EngineAssumptions, Lot
from zce.engine.scenario import Scenario, apply_scenario, capacity_under_scenario
from zce.rules.schema import load_state_overrides, load_zone_rules

GOLDEN_PATH = REPO_ROOT / "shared" / "fixtures" / "golden.json"
SAMPLE_SIZE = 400
SEED = 42

# One scenario per lever, plus a combined "everything" case.
SCENARIOS: dict[str, Scenario] = {
    "baseline": Scenario(),
    "fourplex": Scenario(sf_units_per_lot=4),
    "small_lots": Scenario(sf_min_lot_sqft=3_000),
    "no_parking": Scenario(parking_per_unit=0),
    "parking_1_mile": Scenario(parking_exempt_radius_ft=5_280, parking_per_unit=1),
    "transit_upzone": Scenario(transit_radius_ft=2_640, transit_extra_stories=2, transit_density_multiplier=2),
    "housing_in_cg": Scenario(housing_in_cg=True),
    "more_adus": Scenario(adu_units_added=3),
    "everything": Scenario(
        sf_units_per_lot=4, sf_min_lot_sqft=2_500, parking_per_unit=0, parking_exempt_radius_ft=5_280,
        transit_radius_ft=5_280, transit_extra_stories=1, transit_density_multiplier=1.5,
        housing_in_cg=True, adu_units_added=3,
    ),
}

# Hand-made lots that hit edge cases (rounding boundaries, slivers, ties...).
EDGE_LOTS = [
    {"zone": "RS-6", "area_sqft": 7200, "width_ft": 60, "depth_ft": 120, "overlays": [], "dist_major_transit_ft": 9000, "existing_units": 1},
    {"zone": "RS-6", "area_sqft": 7200, "width_ft": 60, "depth_ft": 120, "overlays": ["LD-1"], "dist_major_transit_ft": 9000, "existing_units": 1},
    {"zone": "RS-6", "area_sqft": 400, "width_ft": 10, "depth_ft": 40, "overlays": [], "dist_major_transit_ft": None, "existing_units": None},
    {"zone": "RS-6", "area_sqft": 2399, "width_ft": 30, "depth_ft": 80, "overlays": [], "dist_major_transit_ft": 100, "existing_units": 0},
    {"zone": "RM-16", "area_sqft": 10450, "width_ft": 70, "depth_ft": 150, "overlays": [], "dist_major_transit_ft": 4000, "existing_units": 2},
    {"zone": "RM-16", "area_sqft": 10312, "width_ft": 70, "depth_ft": 150, "overlays": [], "dist_major_transit_ft": 4000, "existing_units": 2},
    {"zone": "RM-32", "area_sqft": 15000, "width_ft": 100, "depth_ft": 150, "overlays": [], "dist_major_transit_ft": 5000, "existing_units": 4},
    {"zone": "RM-32", "area_sqft": 9999, "width_ft": 59.9, "depth_ft": 170, "overlays": [], "dist_major_transit_ft": 2640, "existing_units": 3},
    {"zone": "RM-48", "area_sqft": 6800, "width_ft": 50, "depth_ft": 136, "overlays": ["HD"], "dist_major_transit_ft": 2641, "existing_units": None},
    {"zone": "RM-12", "area_sqft": 8000, "width_ft": 80, "depth_ft": 100, "overlays": [], "dist_major_transit_ft": 3000, "existing_units": 1},
    {"zone": "CO", "area_sqft": 20000, "width_ft": 100, "depth_ft": 200, "overlays": [], "dist_major_transit_ft": 1000, "existing_units": 0},
    {"zone": "CL-2", "area_sqft": 30000, "width_ft": 150, "depth_ft": 200, "overlays": [], "dist_major_transit_ft": 8000, "existing_units": 0},
    {"zone": "CG", "area_sqft": 13600, "width_ft": 80, "depth_ft": 170, "overlays": [], "dist_major_transit_ft": 1000, "existing_units": 0},
    {"zone": "OS", "area_sqft": 50000, "width_ft": 200, "depth_ft": 250, "overlays": [], "dist_major_transit_ft": 1000, "existing_units": 0},
    {"zone": None, "area_sqft": 10000, "width_ft": 100, "depth_ft": 100, "overlays": [], "dist_major_transit_ft": 1000, "existing_units": 5},
]


def _sample_real_lots(city: CityConfig) -> list[dict]:
    df = pd.read_parquet(DATA_DIR / "out" / city.id / "capacity.parquet")
    rows = list(df.itertuples(index=False))
    random.Random(SEED).shuffle(rows)
    lots = []
    for row in rows[:SAMPLE_SIZE]:
        lots.append({
            "zone": row.rules_zone if isinstance(row.rules_zone, str) else None,
            "area_sqft": float(row.lot_area_sqft),
            "width_ft": float(row.lot_width_ft),
            "depth_ft": float(row.lot_depth_ft),
            "overlays": list(row.overlays) if row.overlays is not None else [],
            "dist_major_transit_ft": None if pd.isna(row.dist_major_transit_ft) else float(row.dist_major_transit_ft),
            "existing_units": None if pd.isna(row.existing_units) else float(row.existing_units),
        })
    return lots


def compute_expected(city: CityConfig, lots: list[dict]) -> dict:
    rules = load_zone_rules(city.rules_dir)
    state = load_state_overrides(city.state_law_file)
    a = EngineAssumptions(city.assumptions.gross_sqft_per_unit, city.assumptions.parking_stall_sqft)
    results = {}
    for name, s in SCENARIOS.items():
        r2, st2 = apply_scenario(rules, state, s)
        out = []
        for d in lots:
            lot = Lot(d["area_sqft"], d["width_ft"], d["depth_ft"], tuple(d["overlays"]),
                      d["dist_major_transit_ft"], d["existing_units"])
            res = capacity_under_scenario(d["zone"], lot, a, r2, st2, s)
            out.append({
                "max_units": res.max_units,
                "local_units": res.local_units,
                "binding_constraint": res.binding_constraint,
                "net_new_units": res.net_new_units,
                "limits": res.limits,
            })
        results[name] = out
    return results


def build_golden(city: CityConfig) -> dict:
    lots = EDGE_LOTS + _sample_real_lots(city)
    return {
        "city": city.id,
        "note": "Generated by `make golden`. Do not edit by hand.",
        "scenarios": {k: asdict(v) for k, v in SCENARIOS.items()},
        "lots": lots,
        "expected": compute_expected(city, lots),
    }


def write_golden(city_id: str = "pasadena") -> None:
    city = load_city(city_id)
    golden = build_golden(city)
    GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN_PATH.write_text(json.dumps(golden, indent=1))
    n = len(golden["lots"]) * len(golden["scenarios"])
    print(f"Wrote {GOLDEN_PATH} ({len(golden['lots'])} lots x {len(golden['scenarios'])} scenarios = {n} results)")
