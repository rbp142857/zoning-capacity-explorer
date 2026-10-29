// Types for rules.json, mirroring pipeline/src/zce/rules/schema.py.
// (The Python side validates the files; the browser trusts them.)

export interface Sourced<T> {
  value: T;
  source: string;
  assumption?: string | null;
}

export interface Band {
  below: number | null;
  value: number | null;
  share: number | null;
  plus_sqft: number;
  plus_sqft_per_unit: number;
  at_least_sqft: number;
}

export interface Banded {
  by: "lot_area_sqft" | "lot_width_ft";
  bands: Band[];
}

export interface SideSetback {
  pct_of_width: number;
  min_ft: number;
  max_ft: number;
}

export type Family = "single_family" | "multifamily" | "commercial" | "nonresidential";
export type Rounding = "floor" | "up_above_0_75" | "nearest_half_up";

export interface ZoneRules {
  zone: string;
  name: string;
  family: Family;
  sources: Record<string, { section: string; url: string }>;
  residential_allowed: Sourced<boolean>;
  housing_types: Sourced<string[]>;
  min_lot_area_sqft: Sourced<number> | null;
  min_lot_width_ft: Sourced<number> | null;
  max_units_per_lot: Sourced<number> | null;
  lot_area_per_unit_sqft: Sourced<number> | null;
  units_per_acre: Sourced<number> | null;
  small_lot_units: Sourced<Banded> | null;
  small_lot_units_below_sqft: number | null;
  density_rounding: Sourced<Rounding> | null;
  setbacks: {
    front_ft: Sourced<number>;
    side_ft: Sourced<number | SideSetback>;
    rear_ft: Sourced<number>;
  };
  max_height_ft: Sourced<number | Banded> | null;
  max_stories: Sourced<number | Banded>;
  lot_coverage: Sourced<number | Banded> | null;
  max_floor_area: Sourced<Banded> | null;
  max_far: Sourced<number> | null;
  min_open_space_share: Sourced<number | Banded> | null;
  parking_per_unit: Sourced<number> | null;
  guest_parking_per_unit: Sourced<number> | null;
  guest_parking_min_units: number | null;
  simplifications: string[];
}

export interface StateLaw {
  id: string;
  name: string;
  status: "modeled" | "not_modeled";
  summary: string;
  citation: { section: string; url: string };
  assumptions: string[];
  params: Record<string, number | string | string[]>;
}

export interface StateOverrides {
  state: string;
  as_of: string;
  laws: StateLaw[];
}

export interface RulesFile {
  zones: Record<string, ZoneRules>;
  state: StateOverrides;
  assumptions: { gross_sqft_per_unit: number; parking_stall_sqft: number };
  redevelopment: {
    as_of_year: number;
    min_capacity_multiple: number;
    min_net_new_units: number;
    min_building_age_years: number;
    max_improvement_to_land_ratio: number;
    exclude_condos: boolean;
    exclude_overlay_prefixes: string[];
    exclude_single_family_zones: boolean;
  };
}

export function isBanded(v: unknown): v is Banded {
  return typeof v === "object" && v !== null && "bands" in v;
}

export function isSideSetback(v: unknown): v is SideSetback {
  return typeof v === "object" && v !== null && "pct_of_width" in v;
}

/** Same as Banded.pick() in schema.py. */
export function pick(b: Banded, lotAreaSqft: number, lotWidthFt: number): Band {
  const key = b.by === "lot_area_sqft" ? lotAreaSqft : lotWidthFt;
  for (const band of b.bands) {
    if (band.below === null || key < band.below) return band;
  }
  throw new Error("unreachable: last band has no upper bound");
}

/** StateOverrides.get() in schema.py: a modeled law by id, or null. */
export function getLaw(state: StateOverrides | null, id: string): StateLaw | null {
  return state?.laws.find((l) => l.id === id && l.status === "modeled") ?? null;
}
