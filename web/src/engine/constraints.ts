// The zoning math, ported line by line from pipeline/src/zce/engine/constraints.py.
// Keep the two files in step: shared/fixtures/golden.json checks they agree.
// Comments explaining the rules live in the Python file.

import { type Band, type Banded, type SideSetback, type ZoneRules, isBanded, isSideSetback, pick } from "./types";

export const SQFT_PER_ACRE = 43_560;
const EPS = 1e-9;

export interface Lot {
  area_sqft: number;
  width_ft: number;
  depth_ft: number;
  overlays: string[];
  dist_major_transit_ft: number | null;
  existing_units: number | null;
  dist_single_family_ft: number | null;
}

export interface EngineAssumptions {
  gross_sqft_per_unit: number;
  parking_stall_sqft: number;
  min_home_sqft?: number;
}

export function shapeFactor(lot: Lot): number {
  const rect = lot.width_ft * lot.depth_ft;
  return rect > 0 ? Math.min(1, lot.area_sqft / rect) : 0;
}

export function roundUnits(x: number, mode: string): number {
  const whole = Math.floor(x + EPS);
  const fraction = x - whole;
  if (mode === "floor") return whole;
  if (mode === "up_above_0_75") return fraction > 0.75 + EPS ? whole + 1 : whole;
  if (mode === "nearest_half_up") return fraction >= 0.5 - EPS ? whole + 1 : whole;
  if (mode === "up") return fraction > EPS ? whole + 1 : whole;
  throw new Error(`unknown rounding mode ${mode}`);
}

function pickValue(v: number | Banded, lot: Lot): Band | number {
  return isBanded(v) ? pick(v, lot.area_sqft, lot.width_ft, lot.dist_single_family_ft) : v;
}

function bandArea(band: Band, lot: Lot, units = 0): number | null {
  if (band.share === null) return band.value;
  const area = band.share * lot.area_sqft + band.plus_sqft + band.plus_sqft_per_unit * units;
  return Math.max(area, band.at_least_sqft);
}

function asNumber(v: number | Banded, lot: Lot): number | null {
  const p = pickValue(v, lot);
  if (typeof p === "number") return p;
  return p.share === null ? p.value : p.share;
}

export function sideSetbackFt(v: number | SideSetback, lot: Lot): number {
  if (isSideSetback(v)) return Math.min(Math.max(v.pct_of_width * lot.width_ft, v.min_ft), v.max_ft);
  return v;
}

function rounding(r: ZoneRules): string {
  return r.density_rounding ? r.density_rounding.value : "floor";
}

export function densityLimit(r: ZoneRules, lot: Lot): number | null {
  const limits: number[] = [];
  if (r.max_units_per_lot) limits.push(r.max_units_per_lot.value);
  if (r.units_per_acre) limits.push(roundUnits((lot.area_sqft / SQFT_PER_ACRE) * r.units_per_acre.value, rounding(r)));
  return limits.length ? Math.min(...limits) : null;
}

export function lotAreaPerUnitLimit(r: ZoneRules, lot: Lot): number | null {
  if (r.small_lot_units && r.small_lot_units_below_sqft !== null && lot.area_sqft < r.small_lot_units_below_sqft) {
    return Math.trunc(pick(r.small_lot_units.value, lot.area_sqft, lot.width_ft, lot.dist_single_family_ft).value as number);
  }
  if (!r.lot_area_per_unit_sqft) return null;
  return roundUnits(lot.area_sqft / (asNumber(r.lot_area_per_unit_sqft.value, lot) as number), rounding(r));
}

export function setbackAreaSqft(r: ZoneRules, lot: Lot): number {
  const s = r.setbacks;
  const usableWidth = lot.width_ft - 2 * sideSetbackFt(s.side_ft.value, lot);
  const usableDepth = lot.depth_ft - s.front_ft.value - s.rear_ft.value;
  return Math.max(0, usableWidth) * Math.max(0, usableDepth) * shapeFactor(lot);
}

export function maxFootprintSqft(r: ZoneRules, lot: Lot): number {
  const caps = [setbackAreaSqft(r, lot)];
  if (r.lot_coverage) {
    const p = pickValue(r.lot_coverage.value, lot);
    const cap = typeof p === "number" ? p * lot.area_sqft : bandArea(p, lot);
    if (cap !== null) caps.push(cap);
  }
  if (r.min_open_space_share) caps.push(lot.area_sqft * (1 - (asNumber(r.min_open_space_share.value, lot) as number)));
  return Math.min(...caps);
}

export function envelopeLimit(r: ZoneRules, lot: Lot, a: EngineAssumptions): number {
  const stories = asNumber(r.max_stories.value, lot) || 0;
  let floorArea = maxFootprintSqft(r, lot) * stories;
  if (r.max_far) floorArea = Math.min(floorArea, r.max_far.value * lot.area_sqft);

  let units = Math.floor(floorArea / a.gross_sqft_per_unit + EPS);

  if (r.max_floor_area) {
    const band = pick(r.max_floor_area.value, lot.area_sqft, lot.width_ft, lot.dist_single_family_ft);
    let byFormula: number;
    if (band.plus_sqft_per_unit) {
      const fixed = (band.share as number) * lot.area_sqft + band.plus_sqft;
      const perUnitNet = a.gross_sqft_per_unit - band.plus_sqft_per_unit;
      byFormula = perUnitNet > 0 ? Math.floor(fixed / perUnitNet + EPS) : units;
    } else {
      byFormula = Math.floor((bandArea(band, lot) as number) / a.gross_sqft_per_unit + EPS);
    }
    units = Math.min(units, byFormula);
    floorArea = Math.min(
      floorArea,
      band.plus_sqft_per_unit
        ? (band.share as number) * lot.area_sqft + band.plus_sqft + band.plus_sqft_per_unit
        : (bandArea(band, lot) as number),
    );
  }
  if (units < 1 && a.min_home_sqft && floorArea >= a.min_home_sqft) units = 1;
  return Math.max(0, units);
}

export function requiredStalls(r: ZoneRules, units: number): number {
  if (!r.parking_per_unit) return 0;
  let stalls = units * r.parking_per_unit.value;
  if (r.guest_parking_per_unit && units >= (r.guest_parking_min_units || 0)) {
    stalls += units * r.guest_parking_per_unit.value;
  }
  return roundUnits(stalls, "nearest_half_up");
}

export function parkingLimit(r: ZoneRules, lot: Lot, a: EngineAssumptions, exempt = false): number | null {
  if (exempt || !r.parking_per_unit || r.parking_per_unit.value === 0) return null;
  const stories = asNumber(r.max_stories.value, lot) || 0;
  if (stories <= 0) return 0;

  const frontStrip = r.setbacks.front_ft.value * lot.width_ft * shapeFactor(lot);
  let ground = lot.area_sqft - frontStrip;
  if (r.min_open_space_share) {
    ground = Math.min(ground, lot.area_sqft * (1 - (asNumber(r.min_open_space_share.value, lot) as number)));
  }
  const footprintPerUnit = a.gross_sqft_per_unit / stories;
  const fits = (n: number) => n * footprintPerUnit + requiredStalls(r, n) * a.parking_stall_sqft <= ground + 1e-6;

  let n = Math.max(0, Math.ceil(ground / footprintPerUnit));
  while (n > 0 && !fits(n)) n--;
  return n;
}
