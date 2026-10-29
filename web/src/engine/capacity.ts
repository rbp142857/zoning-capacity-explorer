// Ported from pipeline/src/zce/engine/capacity.py. Keep in step (golden test).

import {
  type EngineAssumptions,
  type Lot,
  densityLimit,
  envelopeLimit,
  lotAreaPerUnitLimit,
  parkingLimit,
} from "./constraints";
import { type StateOverrides, type ZoneRules, getLaw } from "./types";

export const TIE_ORDER = ["use_not_permitted", "density", "lot_area_per_unit", "envelope", "parking"];

export interface CapacityResult {
  status: "ok" | "not_modeled";
  max_units: number | null;
  local_units: number | null;
  binding_constraint: string | null;
  local_binding_constraint: string | null;
  limits: Record<string, number | null>;
  state_laws_applied: string[];
  net_new_units: number | null;
  flags: string[];
}

export function localCapacity(
  r: ZoneRules,
  lot: Lot,
  a: EngineAssumptions,
  parkingExempt = false,
): [number, string, Record<string, number | null>] {
  if (!r.residential_allowed.value) return [0, "use_not_permitted", { use_not_permitted: 0 }];
  const limits: Record<string, number | null> = {
    density: densityLimit(r, lot),
    lot_area_per_unit: lotAreaPerUnitLimit(r, lot),
    envelope: envelopeLimit(r, lot, a),
    parking: parkingLimit(r, lot, a, parkingExempt),
  };
  const applicable = Object.entries(limits).filter(([, v]) => v !== null) as [string, number][];
  const units = Math.min(...applicable.map(([, v]) => v));
  const binding = TIE_ORDER.find((k) => limits[k] === units) as string;
  return [units, binding, limits];
}

function hasExcludedOverlay(lot: Lot, prefixes: string[]): boolean {
  return lot.overlays.some((o) => prefixes.some((p) => o.startsWith(p)));
}

export function computeCapacity(
  r: ZoneRules | null,
  lot: Lot,
  a: EngineAssumptions,
  state: StateOverrides | null = null,
): CapacityResult {
  if (r === null) {
    return {
      status: "not_modeled", max_units: null, local_units: null, binding_constraint: null,
      local_binding_constraint: null, limits: {}, state_laws_applied: [], net_new_units: null,
      flags: ["zone_not_modeled"],
    };
  }
  const flags: string[] = [];
  const applied: string[] = [];
  if (r.min_lot_area_sqft && lot.area_sqft < r.min_lot_area_sqft.value) flags.push("substandard_lot_area");
  if (r.min_lot_width_ft && lot.width_ft < r.min_lot_width_ft.value) flags.push("substandard_lot_width");

  const ab2097 = getLaw(state, "ab2097");
  const parkingExempt = Boolean(
    ab2097 && lot.dist_major_transit_ft !== null && lot.dist_major_transit_ft <= (ab2097.params.radius_ft as number),
  );
  const [units, binding, limits] = localCapacity(r, lot, a, parkingExempt);
  if (parkingExempt && r.residential_allowed.value) applied.push("ab2097");

  let bestUnits = units;
  let bestBinding = binding;

  const adu = getLaw(state, "adu");
  if (adu && r.residential_allowed.value && (adu.params.applies_to_families as string[]).includes(r.family) && units === 1) {
    const aduUnits = 1 + Math.trunc(adu.params.units_added_to_single_family as number);
    limits.state_adu = aduUnits;
    if (aduUnits > bestUnits) [bestUnits, bestBinding] = [aduUnits, "state_law:adu"];
  }

  const sb9 = getLaw(state, "sb9");
  if (sb9 && (sb9.params.applies_to_families as string[]).includes(r.family)) {
    if (hasExcludedOverlay(lot, sb9.params.excluded_overlay_prefixes as string[])) {
      flags.push("sb9_excluded_historic_district");
    } else if (lot.area_sqft < (sb9.params.min_lot_sqft_for_two_units as number)) {
      flags.push("sb9_lot_too_small");
    } else {
      const splitOk = lot.area_sqft >= (sb9.params.min_lot_sqft_for_split as number);
      const sb9Units = Math.trunc(sb9.params[splitOk ? "units_with_split" : "units_without_split"] as number);
      limits.state_sb9 = sb9Units;
      if (sb9Units > bestUnits) [bestUnits, bestBinding] = [sb9Units, "state_law:sb9"];
    }
  }
  if (bestBinding.startsWith("state_law:")) applied.push(bestBinding.split(":")[1]);

  const netNew = lot.existing_units === null ? null : Math.max(0, bestUnits - Math.trunc(lot.existing_units));
  return {
    status: "ok",
    max_units: bestUnits,
    local_units: units,
    binding_constraint: bestBinding,
    local_binding_constraint: binding,
    limits,
    state_laws_applied: applied,
    net_new_units: netNew,
    flags,
  };
}
