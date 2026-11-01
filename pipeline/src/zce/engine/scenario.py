"""Reform scenarios: "what if the rules changed like this?"

A scenario is a small set of lever values. Applying one never edits the rule
files; it makes modified COPIES of the rules, in two steps:

1. apply_scenario(): changes that are the same for every lot in a zone
   (e.g. "allow 4 homes per lot in single-family zones", "no parking minimums").
2. adjust_for_lot(): changes that depend on the lot itself
   (e.g. "within 1/2 mile of transit, add 2 stories", or how many smaller
   lots a big lot could be split into).

Then the normal engine (compute_capacity) runs on the modified rules.

The SAME logic exists in TypeScript (web/src/engine/scenario.ts) so the
browser can recompute instantly. shared/fixtures/golden.json holds answers
computed here; a browser-side test checks the TypeScript gives identical
results. If you change anything in this file, change scenario.ts to match
and regenerate the golden file (`make golden`).
"""

import math
from dataclasses import asdict, dataclass

from zce.engine.capacity import CapacityResult, compute_capacity
from zce.engine.constraints import EngineAssumptions, Lot
from zce.rules.schema import Band, Banded, Citation, Sourced, StateOverrides, ZoneRules

SCENARIO_SOURCE = "scenario"
SCENARIO_CITATION = Citation(section="Reform scenario (hypothetical, not current law)", url="")

AB2097_RADIUS_FT = 2640  # state law floor: a scenario can widen it, never shrink it


@dataclass(frozen=True)
class Scenario:
    """Lever values. None / defaults mean "keep today's rules"."""

    # Single-family zones: homes allowed per lot (2 = duplex, 4 = fourplex).
    sf_units_per_lot: int | None = None
    # Single-family zones: new minimum lot size. A lot can be split into
    # floor(area / this) lots, each allowed sf_units_per_lot (or 1) homes.
    sf_min_lot_sqft: float | None = None
    # Parking spaces required per home in every zone (0 = no minimums).
    parking_per_unit: float | None = None
    # No parking minimums within this distance of a major transit stop.
    # State law (AB 2097) already sets 2,640 ft; smaller values are ignored.
    parking_exempt_radius_ft: float = AB2097_RADIUS_FT
    # Upzoning near transit, for multifamily and commercial zones.
    transit_radius_ft: float = AB2097_RADIUS_FT
    transit_extra_stories: int = 0
    transit_density_multiplier: float = 1.0
    # Allow housing in General Commercial (CG), using CL's housing standards.
    housing_in_cg: bool = False
    # Homes an ADU path adds to a single-family lot (state law today: 2 = ADU + JADU).
    adu_units_added: int | None = None

    def is_baseline(self) -> bool:
        return self == Scenario()

    def to_dict(self) -> dict:
        return asdict(self)


def _cite(value) -> Sourced:
    return Sourced(value=value, source=SCENARIO_SOURCE)


def _with_scenario_source(rules: ZoneRules, **updates) -> ZoneRules:
    sources = {**rules.sources, SCENARIO_SOURCE: SCENARIO_CITATION}
    return rules.model_copy(update={"sources": sources, **updates})


def _cg_from_cl(cl: ZoneRules, cg: ZoneRules) -> ZoneRules:
    """Housing standards for CG under the "housing in CG" lever.

    Assumption: CG would use CL's residential standards (RM-32 density and
    gardens), but keep CG's own height (45 ft, so 4 stories) and FAR 0.80
    from Table 2-6.
    """
    return _with_scenario_source(
        cl,
        zone=cg.zone,
        name=f"{cg.name}, housing allowed by scenario",
        max_stories=_cite(4),
        max_far=_cite(0.80),
        max_height_ft=_cite(45),
    )


def apply_scenario(
    rules: dict[str, ZoneRules], state: StateOverrides, s: Scenario
) -> tuple[dict[str, ZoneRules], StateOverrides]:
    """Zone-wide changes: returns modified copies of the rules and state law."""
    out: dict[str, ZoneRules] = {}
    for zone, r in rules.items():
        updates = {}
        if r.family == "single_family" and r.residential_allowed.value and s.sf_units_per_lot is not None:
            updates["max_units_per_lot"] = _cite(s.sf_units_per_lot)
        if s.parking_per_unit is not None and r.parking_per_unit is not None:
            updates["parking_per_unit"] = _cite(s.parking_per_unit)
            if s.parking_per_unit == 0:
                updates["guest_parking_per_unit"] = None
        out[zone] = _with_scenario_source(r, **updates) if updates else r

    if s.housing_in_cg and "CG" in out and "CL" in out:
        out["CG"] = _cg_from_cl(out["CL"], out["CG"])

    laws = []
    for law in state.laws:
        params = dict(law.params)
        if law.id == "ab2097":
            params["radius_ft"] = max(AB2097_RADIUS_FT, s.parking_exempt_radius_ft)
        if law.id == "adu" and s.adu_units_added is not None:
            params["units_added_to_single_family"] = s.adu_units_added
        laws.append(law.model_copy(update={"params": params}) if params != law.params else law)
    return out, state.model_copy(update={"laws": laws})


def _scale_banded_values(banded: Banded, factor: float) -> Banded:
    bands = [b.model_copy(update={"value": math.floor(b.value * factor + 1e-9)}) if b.value is not None else b
             for b in banded.bands]
    return banded.model_copy(update={"bands": bands})


def _add_stories(stories: float | Banded, extra: int) -> float | Banded:
    if isinstance(stories, Banded):
        bands = [Band(**{**b.model_dump(), "value": (b.value or 0) + extra}) for b in stories.bands]
        return stories.model_copy(update={"bands": bands})
    return stories + extra


def adjust_for_lot(r: ZoneRules, lot: Lot, s: Scenario) -> ZoneRules:
    """Lot-dependent changes (lot splits, upzoning near transit)."""
    updates = {}

    # Smaller minimum lot size in single-family zones -> the lot could be
    # split, multiplying the per-lot cap. Assumption: every split lot is
    # buildable (no check of street frontage or access).
    if r.family == "single_family" and r.residential_allowed.value and s.sf_min_lot_sqft:
        per_lot = r.max_units_per_lot.value if r.max_units_per_lot else 1
        lots = max(1, math.floor(lot.area_sqft / s.sf_min_lot_sqft + 1e-9))
        updates["max_units_per_lot"] = _cite(per_lot * lots)

    near_transit = lot.dist_major_transit_ft is not None and lot.dist_major_transit_ft <= s.transit_radius_ft
    if (
        near_transit
        and r.family in ("multifamily", "commercial")
        and r.residential_allowed.value
        and (s.transit_extra_stories > 0 or s.transit_density_multiplier != 1.0)
    ):
        m, extra = s.transit_density_multiplier, s.transit_extra_stories
        if extra:
            updates["max_stories"] = _cite(_add_stories(r.max_stories.value, extra))
            if r.max_far is not None:
                # Keep FAR in proportion to the added stories, or the extra
                # height could never be used (assumption).
                base = r.max_stories.value
                base_stories = base if not isinstance(base, Banded) else base.pick(lot.area_sqft, lot.width_ft, lot.dist_single_family_ft).value
                if base_stories:
                    updates["max_far"] = _cite(r.max_far.value * (base_stories + extra) / base_stories)
        if m != 1.0:
            if r.lot_area_per_unit_sqft is not None:
                v = r.lot_area_per_unit_sqft.value
                if isinstance(v, Banded):
                    v = v.model_copy(update={"bands": [b.model_copy(update={"value": b.value / m}) for b in v.bands]})
                else:
                    v = v / m
                updates["lot_area_per_unit_sqft"] = _cite(v)
            if r.units_per_acre is not None:
                updates["units_per_acre"] = _cite(r.units_per_acre.value * m)
            if r.max_units_per_lot is not None:
                updates["max_units_per_lot"] = _cite(math.floor(r.max_units_per_lot.value * m + 1e-9))
            if r.small_lot_units is not None:
                updates["small_lot_units"] = _cite(_scale_banded_values(r.small_lot_units.value, m))

    return _with_scenario_source(r, **updates) if updates else r


def capacity_under_scenario(
    zone: str | None,
    lot: Lot,
    a: EngineAssumptions,
    scenario_rules: dict[str, ZoneRules],
    scenario_state: StateOverrides,
    s: Scenario,
) -> CapacityResult:
    """Capacity of one lot under a scenario (rules already passed through apply_scenario)."""
    r = scenario_rules.get(zone) if zone else None
    if r is not None:
        r = adjust_for_lot(r, lot, s)
    return compute_capacity(r, lot, a, scenario_state)

