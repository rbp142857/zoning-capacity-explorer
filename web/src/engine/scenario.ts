// Reform scenarios, ported from pipeline/src/zce/engine/scenario.py.
// Keep in step (golden test). Explanations of each lever live in the Python file.

import { type CapacityResult, computeCapacity } from "./capacity";
import type { EngineAssumptions, Lot } from "./constraints";
import type { Banded, Sourced, StateOverrides, ZoneRules } from "./types";
import { pick } from "./types";

export const AB2097_RADIUS_FT = 2640;

export interface Scenario {
  sf_units_per_lot: number | null;
  sf_min_lot_sqft: number | null;
  parking_per_unit: number | null;
  parking_exempt_radius_ft: number;
  transit_radius_ft: number;
  transit_extra_stories: number;
  transit_density_multiplier: number;
  housing_in_cg: boolean;
  adu_units_added: number | null;
}

export const BASELINE: Scenario = {
  sf_units_per_lot: null,
  sf_min_lot_sqft: null,
  parking_per_unit: null,
  parking_exempt_radius_ft: AB2097_RADIUS_FT,
  transit_radius_ft: AB2097_RADIUS_FT,
  transit_extra_stories: 0,
  transit_density_multiplier: 1,
  housing_in_cg: false,
  adu_units_added: null,
};

export function isBaseline(s: Scenario): boolean {
  return (Object.keys(BASELINE) as (keyof Scenario)[]).every((k) => s[k] === BASELINE[k]);
}

const cite = <T>(value: T): Sourced<T> => ({ value, source: "scenario" });

export function applyScenario(
  rules: Record<string, ZoneRules>,
  state: StateOverrides,
  s: Scenario,
): [Record<string, ZoneRules>, StateOverrides] {
  const out: Record<string, ZoneRules> = {};
  for (const [zone, r] of Object.entries(rules)) {
    const u: Partial<ZoneRules> = {};
    if (r.family === "single_family" && r.residential_allowed.value && s.sf_units_per_lot !== null) {
      u.max_units_per_lot = cite(s.sf_units_per_lot);
    }
    if (s.parking_per_unit !== null && r.parking_per_unit) {
      u.parking_per_unit = cite(s.parking_per_unit);
      if (s.parking_per_unit === 0) u.guest_parking_per_unit = null;
    }
    out[zone] = Object.keys(u).length ? { ...r, ...u } : r;
  }
  if (s.housing_in_cg && out.CG && out.CL) {
    out.CG = {
      ...out.CL,
      zone: out.CG.zone,
      name: `${out.CG.name}, housing allowed by scenario`,
      max_stories: cite(4),
      max_far: cite(0.8),
      max_height_ft: cite(45),
    };
  }
  const laws = state.laws.map((law) => {
    const params = { ...law.params };
    if (law.id === "ab2097") params.radius_ft = Math.max(AB2097_RADIUS_FT, s.parking_exempt_radius_ft);
    if (law.id === "adu" && s.adu_units_added !== null) params.units_added_to_single_family = s.adu_units_added;
    return { ...law, params };
  });
  return [out, { ...state, laws }];
}

function scaleBandedValues(b: Banded, factor: number): Banded {
  return { ...b, bands: b.bands.map((band) => (band.value === null ? band : { ...band, value: Math.floor(band.value * factor + 1e-9) })) };
}

function addStories(stories: number | Banded, extra: number): number | Banded {
  if (typeof stories === "number") return stories + extra;
  return { ...stories, bands: stories.bands.map((b) => ({ ...b, value: (b.value || 0) + extra })) };
}

export function adjustForLot(r: ZoneRules, lot: Lot, s: Scenario): ZoneRules {
  const u: Partial<ZoneRules> = {};

  if (r.family === "single_family" && r.residential_allowed.value && s.sf_min_lot_sqft) {
    const perLot = r.max_units_per_lot ? r.max_units_per_lot.value : 1;
    const lots = Math.max(1, Math.floor(lot.area_sqft / s.sf_min_lot_sqft + 1e-9));
    u.max_units_per_lot = cite(perLot * lots);
  }

  const nearTransit = lot.dist_major_transit_ft !== null && lot.dist_major_transit_ft <= s.transit_radius_ft;
  if (
    nearTransit &&
    (r.family === "multifamily" || r.family === "commercial") &&
    r.residential_allowed.value &&
    (s.transit_extra_stories > 0 || s.transit_density_multiplier !== 1)
  ) {
    const m = s.transit_density_multiplier;
    const extra = s.transit_extra_stories;
    if (extra) {
      u.max_stories = cite(addStories(r.max_stories.value, extra));
      if (r.max_far) {
        const base = r.max_stories.value;
        const baseStories = typeof base === "number" ? base : pick(base, lot.area_sqft, lot.width_ft).value;
        if (baseStories) u.max_far = cite((r.max_far.value * (baseStories + extra)) / baseStories);
      }
    }
    if (m !== 1) {
      if (r.lot_area_per_unit_sqft) u.lot_area_per_unit_sqft = cite(r.lot_area_per_unit_sqft.value / m);
      if (r.units_per_acre) u.units_per_acre = cite(r.units_per_acre.value * m);
      if (r.max_units_per_lot) u.max_units_per_lot = cite(Math.floor(r.max_units_per_lot.value * m + 1e-9));
      if (r.small_lot_units) u.small_lot_units = cite(scaleBandedValues(r.small_lot_units.value, m));
    }
  }
  return Object.keys(u).length ? { ...r, ...u } : r;
}

export function capacityUnderScenario(
  zone: string | null,
  lot: Lot,
  a: EngineAssumptions,
  scenarioRules: Record<string, ZoneRules>,
  scenarioState: StateOverrides,
  s: Scenario,
): CapacityResult {
  let r = zone ? scenarioRules[zone] ?? null : null;
  if (r) r = adjustForLot(r, lot, s);
  return computeCapacity(r, lot, a, scenarioState);
}
