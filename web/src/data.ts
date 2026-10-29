// Loading and reading parcels.json (written by `make export`).
//
// The file is "columnar": instead of 30,000 objects, it holds one array per
// field, and element i of every array belongs to the lot with pid i. That's
// smaller to download and fast to scan.

export interface ParcelData {
  city: string;
  generated_at: string;
  count: number;
  codes: { binding: string[]; zone: string[]; rules_zone: string[]; overlay_sets: string[][]; district: string[] };
  headline: {
    existing_units: number;
    local_units: number;
    max_units: number;
    net_new_units: number;
    lots_modeled: number;
    lots_not_modeled: number;
    single_home_land_share: number;
  };
  columns: {
    parcel_id: string[];
    zone: number[];
    existing_units: (number | null)[];
    local_units: (number | null)[];
    max_units: (number | null)[];
    net_new_units: (number | null)[];
    binding: number[]; // index into codes.binding, or -1 = not modeled
    lot_area_sqft: number[];
    lot_width_ft: number[];
    lot_depth_ft: number[];
    dist_major_transit_ft: (number | null)[];
    rules_zone: number[]; // index into codes.rules_zone, -1 = not modeled
    overlay_set: number[]; // index into codes.overlay_sets
    district: number[]; // index into codes.district, -1 = none
  };
}

export async function loadJson<T>(url: string): Promise<T> {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Could not load ${url}: HTTP ${resp.status}`);
  return (await resp.json()) as T;
}
