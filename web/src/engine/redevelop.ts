// Redevelopment screens, ported from pipeline/src/zce/engine/redevelop.py
// (the dynamic part only: static screens arrive precomputed as a bit mask).
// Keep in step with the Python file; the golden test checks they agree.

export const AGE = 1;
export const VALUE = 2;
export const OWNERSHIP = 4;
export const HISTORIC = 8;
export const ZONE = 16;
export const LAND = 32;
export const SCREEN_NAMES: [number, string][] = [
  [AGE, "building_too_new"],
  [VALUE, "building_worth_more_than_land"],
  [OWNERSHIP, "condo_many_owners"],
  [HISTORIC, "historic_district"],
  [ZONE, "single_family_zone"],
  [LAND, "public_or_special_land"],
];

export interface Redevelopment {
  likely: boolean;
  realistic_new_units: number;
  failed: string[];
}

export interface Thresholds {
  min_capacity_multiple: number;
  min_net_new_units: number;
}

const ALL_SCREENS = SCREEN_NAMES.reduce((all, [bit]) => all | bit, 0);

/**
 * New homes if the lot is likely to redevelop, or -1 if not. Same answer as
 * redevelopment() below, without building a list of reasons for each of 1.3 million lots.
 */
export function likelyNewUnits(t: Thresholds, mask: number, localUnits: number | null, existingUnits: number | null): number {
  if (localUnits === null || (mask & ALL_SCREENS) !== ALL_SCREENS) return -1;
  const existing = existingUnits === null ? 0 : Math.trunc(existingUnits);
  if (localUnits < t.min_capacity_multiple * Math.max(existing, 1) || localUnits - existing < t.min_net_new_units) return -1;
  return Math.max(0, localUnits - existing);
}

export function redevelopment(
  t: Thresholds,
  mask: number,
  localUnits: number | null,
  existingUnits: number | null,
): Redevelopment {
  if (localUnits === null) return { likely: false, realistic_new_units: 0, failed: ["not_modeled"] };
  const existing = existingUnits === null ? 0 : Math.trunc(existingUnits);
  const failed = SCREEN_NAMES.filter(([bit]) => !(mask & bit)).map(([, name]) => name);
  if (localUnits < t.min_capacity_multiple * Math.max(existing, 1) || localUnits - existing < t.min_net_new_units) {
    failed.unshift("zoning_allows_too_little_more");
  }
  if (failed.length) return { likely: false, realistic_new_units: 0, failed };
  return { likely: true, realistic_new_units: Math.max(0, localUnits - existing), failed: [] };
}
