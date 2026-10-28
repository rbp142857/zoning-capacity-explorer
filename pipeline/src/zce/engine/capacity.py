"""Combine the constraints into one answer per lot, then apply state law.

    local capacity = min(density, lot area per unit, envelope, parking)
    max legal units = the best of: local capacity, the ADU path, the SB 9 path

and we record WHICH rule set the number (the binding constraint), because
that's what tells a user what would have to change to allow more homes.
"""

from dataclasses import dataclass, field

from zce.engine.constraints import (
    EngineAssumptions,
    Lot,
    density_limit,
    envelope_limit,
    lot_area_per_unit_limit,
    parking_limit,
)
from zce.rules.schema import StateOverrides, ZoneRules

# When two constraints give the same number, report the first one in this
# list. Legal limits come before physical ones because a legal limit is the
# rule a reform would need to change.
TIE_ORDER = ["use_not_permitted", "density", "lot_area_per_unit", "envelope", "parking"]


@dataclass
class CapacityResult:
    status: str  # "ok", or "not_modeled" when there's no rule file for the zone
    max_units: int | None = None
    local_units: int | None = None
    binding_constraint: str | None = None  # e.g. "parking", or "state_law:sb9"
    local_binding_constraint: str | None = None
    limits: dict[str, int | None] = field(default_factory=dict)  # every constraint's answer
    state_laws_applied: list[str] = field(default_factory=list)
    net_new_units: int | None = None
    flags: list[str] = field(default_factory=list)


def local_capacity(
    rules: ZoneRules, lot: Lot, a: EngineAssumptions, parking_exempt: bool = False
) -> tuple[int, str, dict[str, int | None]]:
    """(units, binding constraint, all limits) under local zoning only."""
    if not rules.residential_allowed.value:
        return 0, "use_not_permitted", {"use_not_permitted": 0}

    limits = {
        "density": density_limit(rules, lot),
        "lot_area_per_unit": lot_area_per_unit_limit(rules, lot),
        "envelope": envelope_limit(rules, lot, a),
        "parking": parking_limit(rules, lot, a, exempt=parking_exempt),
    }
    applicable = {k: v for k, v in limits.items() if v is not None}
    units = min(applicable.values())
    binding = next(k for k in TIE_ORDER if applicable.get(k) == units)
    return units, binding, limits


def _has_excluded_overlay(lot: Lot, prefixes) -> bool:
    return any(o.startswith(p) for o in lot.overlays for p in prefixes)


def compute_capacity(
    rules: ZoneRules | None,
    lot: Lot,
    a: EngineAssumptions,
    state: StateOverrides | None = None,
) -> CapacityResult:
    if rules is None:
        return CapacityResult(status="not_modeled", flags=["zone_not_modeled"])

    result = CapacityResult(status="ok")

    # Lot-size minimums apply to creating new lots. An existing smaller lot
    # can still be built on, so we flag it instead of zeroing its capacity.
    if rules.min_lot_area_sqft and lot.area_sqft < rules.min_lot_area_sqft.value:
        result.flags.append("substandard_lot_area")
    if rules.min_lot_width_ft and lot.width_ft < rules.min_lot_width_ft.value:
        result.flags.append("substandard_lot_width")

    # AB 2097: no parking minimums within 1/2 mile of a major transit stop.
    ab2097 = state.get("ab2097") if state else None
    parking_exempt = bool(
        ab2097
        and lot.dist_major_transit_ft is not None
        and lot.dist_major_transit_ft <= ab2097.params["radius_ft"]
    )
    units, binding, limits = local_capacity(rules, lot, a, parking_exempt)
    if parking_exempt and rules.residential_allowed.value:
        result.state_laws_applied.append("ab2097")
    result.local_units, result.local_binding_constraint, result.limits = units, binding, limits

    best_units, best_binding = units, binding

    # ADU path: a single-family home can add one ADU and one junior ADU.
    adu = state.get("adu") if state else None
    if adu and rules.residential_allowed.value and rules.family in adu.params["applies_to_families"] and units == 1:
        adu_units = 1 + int(adu.params["units_added_to_single_family"])
        limits["state_adu"] = adu_units
        if adu_units > best_units:
            best_units, best_binding = adu_units, "state_law:adu"

    # SB 9 path: two units, or four with an urban lot split, in single-family zones.
    sb9 = state.get("sb9") if state else None
    if sb9 and rules.family in sb9.params["applies_to_families"]:
        if _has_excluded_overlay(lot, sb9.params["excluded_overlay_prefixes"]):
            result.flags.append("sb9_excluded_historic_district")
        elif lot.area_sqft < sb9.params["min_lot_sqft_for_two_units"]:
            result.flags.append("sb9_lot_too_small")
        else:
            split_ok = lot.area_sqft >= sb9.params["min_lot_sqft_for_split"]
            sb9_units = int(sb9.params["units_with_split" if split_ok else "units_without_split"])
            limits["state_sb9"] = sb9_units
            if sb9_units > best_units:
                best_units, best_binding = sb9_units, "state_law:sb9"

    if best_binding.startswith("state_law:"):
        result.state_laws_applied.append(best_binding.split(":")[1])

    result.max_units = best_units
    result.binding_constraint = best_binding
    if lot.existing_units is not None and lot.existing_units == lot.existing_units:  # not NaN
        result.net_new_units = max(0, best_units - int(lot.existing_units))
    return result
