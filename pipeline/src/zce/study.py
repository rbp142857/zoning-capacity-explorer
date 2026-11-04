"""Reform study: what would a rule change allow, city by city, with its limits written out?

    python -m zce study studies/transit_upzone.yaml

The YAML file gives a title, the cities, and the lever values (see engine/scenario.py).
Writes reports/studies/<file name>.md and .csv. Uses the same engine as the site, so a
reader can reproduce the numbers with the scenario's lever settings.
"""

import subprocess
from dataclasses import fields
from pathlib import Path

import pandas as pd
import yaml

from zce.config import DATA_DIR, REPO_ROOT, load_city
from zce.engine import EngineAssumptions, Lot
from zce.engine.redevelop import is_special_land, redevelopment, screens_from_config
from zce.engine.scenario import Scenario, apply_scenario, capacity_under_scenario
from zce.report import _table
from zce.rules.schema import load_state_overrides, load_zone_rules

BANDS = [(1320, "Under ¼ mile"), (2640, "¼ to ½ mile"), (5280, "½ to 1 mile"), (float("inf"), "Over 1 mile or unknown")]
COLUMNS = ["rules_zone", "model_status", "lot_area_sqft", "lot_width_ft", "lot_depth_ft", "overlays", "dist_major_transit_ft",
           "existing_units", "dist_single_family_ft", "redev_mask", "use_description", "capacity_flags", "net_new_units", "realistic_new_units"]


def _num(v):
    return None if pd.isna(v) else float(v)


def _whole(v) -> int:
    return 0 if pd.isna(v) else int(v)


def _band(distance) -> str:
    d = float("inf") if pd.isna(distance) else distance
    return next((label for limit, label in BANDS if d < limit), BANDS[-1][1])


def scenario_from_dict(levers: dict) -> Scenario:
    known = {f.name for f in fields(Scenario)}
    unknown = set(levers) - known
    if unknown:
        raise ValueError(f"Unknown levers: {sorted(unknown)}. Known: {sorted(known)}")
    return Scenario(**levers)


def run_city(city_id: str, scenario: Scenario) -> tuple[dict, dict]:
    city = load_city(city_id)
    rules = load_zone_rules(city.rules_dir)
    state = load_state_overrides(city.state_law_file)
    a = EngineAssumptions(city.assumptions.gross_sqft_per_unit, city.assumptions.parking_stall_sqft, city.assumptions.min_home_sqft)
    screens = screens_from_config(city.redevelopment)
    new_rules, new_state = apply_scenario(rules, state, scenario)
    lots = pd.read_parquet(DATA_DIR / "out" / city_id / "capacity.parquet", columns=COLUMNS)
    t = {"city": city.name.split(",")[0], "lots": len(lots), "modeled": 0, "conditions": 0, "today_net": 0, "scenario_net": 0, "today_likely": 0,
         "scenario_likely": 0, "scenario_net_special": 0}
    bands = {label: {"today_net": 0, "scenario_net": 0, "today_likely": 0, "scenario_likely": 0} for _, label in BANDS}
    for row in lots.itertuples(index=False):
        if row.model_status != "ok":
            continue
        lot = Lot(row.lot_area_sqft, row.lot_width_ft, row.lot_depth_ft, tuple(row.overlays) if row.overlays is not None else (),
                  _num(row.dist_major_transit_ft), _num(row.existing_units), _num(row.dist_single_family_ft))
        r = capacity_under_scenario(row.rules_zone, lot, a, new_rules, new_state, scenario)
        redev = redevelopment(screens, int(row.redev_mask), r.local_units, lot.existing_units)
        net = r.net_new_units or 0
        t["modeled"] += 1
        today_net, today_likely = _whole(row.net_new_units), _whole(row.realistic_new_units)
        t["today_net"] += today_net
        t["scenario_net"] += net
        t["today_likely"] += today_likely
        t["scenario_likely"] += redev.realistic_new_units
        if is_special_land(row.use_description):
            t["scenario_net_special"] += net
        if row.capacity_flags is not None and "zoning_conditions_not_modeled" in list(row.capacity_flags):
            t["conditions"] += 1
        b = bands[_band(row.dist_major_transit_ft)]
        b["today_net"] += today_net
        b["scenario_net"] += net
        b["today_likely"] += today_likely
        b["scenario_likely"] += redev.realistic_new_units
    return t, bands


def _commit() -> str:
    done = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True)
    return done.stdout.strip() or "unknown"


def write_study(path: str) -> Path:
    spec = yaml.safe_load(Path(path).read_text())
    scenario = scenario_from_dict(spec.get("levers", {}))
    if scenario.is_baseline():
        raise ValueError("This scenario changes nothing, so there's nothing to study.")
    totals, bands = [], {label: {"today_net": 0, "scenario_net": 0, "today_likely": 0, "scenario_likely": 0} for _, label in BANDS}
    for city_id in spec["cities"]:
        t, b = run_city(city_id, scenario)
        totals.append(t)
        for label, values in b.items():
            for k, v in values.items():
                bands[label][k] += v
    df = pd.DataFrame(totals)
    out_dir = REPO_ROOT / "reports" / "studies"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(path).stem
    df.to_csv(out_dir / f"{stem}.csv", index=False)

    def n(v) -> str:
        return f"{int(v):,}"

    def change(a, b) -> str:
        return f"{'+' if b >= a else '−'}{abs(int(b - a)):,}"

    view = pd.DataFrame({
        "City": df["city"], "Lots modeled": [f"{m / l:.0%}" for m, l in zip(df["modeled"], df["lots"])],
        "Theoretical, today": df["today_net"].map(n), "Theoretical, reform": df["scenario_net"].map(n),
        "Change": [change(a, b) for a, b in zip(df["today_net"], df["scenario_net"])],
        "Likely lots, today": df["today_likely"].map(n), "Likely lots, reform": df["scenario_likely"].map(n),
        "Change ": [change(a, b) for a, b in zip(df["today_likely"], df["scenario_likely"])],
    })
    band_view = pd.DataFrame([{"Distance to major transit": label, "Theoretical, today": n(v["today_net"]), "Theoretical, reform": n(v["scenario_net"]),
                               "Likely lots, today": n(v["today_likely"]), "Likely lots, reform": n(v["scenario_likely"])} for label, v in bands.items()])
    levers = "\n".join(f"- `{k}`: {v}" for k, v in spec["levers"].items())
    notes = []
    if scenario.housing_in_cg:
        notes.append("- The `housing_in_cg` lever only acts where a city has zones named CG and CL, so it may do nothing in some cities.")
    if scenario.sf_units_per_lot or scenario.sf_min_lot_sqft or scenario.adu_units_added:
        notes.append("- Single-family lots are left out of the likely estimate on purpose, so these reforms show up mainly in the theoretical numbers.")
    text = [
        f"# {spec['title']}", "",
        f"{spec.get('summary', '').strip()}", "",
        "**This is an estimate of what rules would allow, not a forecast of what would be built.** Generated by "
        f"`python -m zce study` at commit `{_commit()}`. Not legal or zoning advice.", "",
        "## The reform modeled", "", levers, "",
        "## Results", "", "New homes, net of homes already there:", "", _table(view), "",
        f"Together: **{n(df['scenario_net'].sum() - df['today_net'].sum())}** more homes in theory and "
        f"**{n(df['scenario_likely'].sum() - df['today_likely'].sum())}** more on lots passing the redevelopment screens.", "",
        "## By distance to major transit", "", _table(band_view), "",
        "## How to read these numbers", "",
        "- **Theoretical** assumes every lot is rebuilt to the maximum, which won't happen. "
        f"It includes **{n(df['scenario_net_special'].sum())}** homes on government, utility, quarry, cemetery, golf and private school land.",
        "- **Likely lots** counts only lots passing all redevelopment screens (METHODOLOGY.md section 6). It's a screen, not a prediction of timing or amount.",
        "- **Totals run low where plans are missing:** lots not modeled count as nothing. "
        f"Here that is {n(df['lots'].sum() - df['modeled'].sum())} of {n(df['lots'].sum())} lots, often in the places a city builds most.",
        f"- **{n(df['conditions'].sum())} lots** carry site-specific conditions (such as LA's Q and T) that aren't modeled.",
        "- **Not modeled:** market demand, construction cost, financing, design review, CEQA, and bonus programs such as LA's TOC.",
        "- See [coverage.md](../la_county/coverage.md) and [accuracy.md](../la_county/accuracy.md) for how far to trust each city.",
        *notes, "",
    ]
    out = out_dir / f"{stem}.md"
    out.write_text("\n".join(text))
    print(f"Wrote {out}")
    return out
