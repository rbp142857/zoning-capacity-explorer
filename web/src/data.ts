// Reading the compact lot files (written by `python -m zce export`).
//
// A lot is only a few numbers, so each file holds one typed column per field,
// and element i of every column belongs to the lot with pid i. That takes about a
// tenth of the memory of ordinary objects and needs no parsing.
//
// File layout, after gzip: 4-byte header length, JSON header, then the columns,
// each on an 8-byte boundary so it can be read in place.

import type { Lot } from "./engine/constraints";

/** "Unknown" in whole-number columns. Keep in step with NA in export_web.py. */
export const NA = -2147483648;

/** A column value, or null if it's unknown. */
export const na = (v: number): number | null => (v === NA ? null : v);

// Binding limits, in the order the files number them. Keep in step with BINDING_CODES in export_web.py.
export const BINDING_CODES = [
  "state_law:sb9", "state_law:adu", "density", "lot_area_per_unit", "envelope", "parking", "use_not_permitted",
];

export type IndexColumn = Int8Array | Uint8Array | Int16Array | Int32Array;

export interface ParcelData {
  city: string;
  count: number;
  bounds: [number, number, number, number]; // west, south, east, north
  codes: { binding: string[]; zone: string[]; rules_zone: string[]; overlay_sets: string[][]; district: string[] };
  headline: {
    existing_units: number;
    local_units: number;
    max_units: number;
    net_new_units: number;
    lots_modeled: number;
    lots_not_modeled: number;
    single_home_land_share: number;
    residential_land_sqft: number;
  };
  /** Parcel numbers that aren't plain digits, by pid. Their parcel_id value is NaN. */
  parcel_id_exceptions: Record<string, string>;
  columns: {
    parcel_id: Float64Array;
    zone: IndexColumn; // index into codes.zone, -1 = none
    existing_units: Int32Array;
    building_sqft: Int32Array;
    local_units: Int32Array;
    max_units: Int32Array;
    net_new_units: Int32Array;
    binding: IndexColumn; // index into codes.binding, -1 = not modeled
    lot_area_sqft: Int32Array;
    lot_width_tenths: Int32Array;
    lot_depth_tenths: Int32Array;
    dist_major_transit_ft: Int32Array;
    dist_single_family_ft: Int32Array;
    dist_sb79_t1_ft: Int32Array;
    dist_sb79_t2_ft: Int32Array;
    sb79_zone_ok: IndexColumn;
    sb79_half_mile: IndexColumn;
    rules_zone: IndexColumn; // index into codes.rules_zone, -1 = not modeled
    overlay_set: IndexColumn; // index into codes.overlay_sets
    district: IndexColumn; // index into codes.district, -1 = none
    redev_mask: IndexColumn; // static redevelopment screens passed (bit mask, see engine/redevelop.ts)
  };
}

const TYPES = {
  float64: Float64Array, float32: Float32Array, int32: Int32Array, int16: Int16Array, int8: Int8Array, uint8: Uint8Array,
} as const;

export interface BinaryFile {
  header: Record<string, unknown>;
  columns: Record<string, Float64Array | Float32Array | Int32Array | Int16Array | Int8Array | Uint8Array>;
}

/** Split an uncompressed file into its header and columns, without copying them. */
export function parseBinary(buffer: ArrayBuffer): BinaryFile {
  const size = new DataView(buffer).getUint32(0, true);
  const header = JSON.parse(new TextDecoder().decode(new Uint8Array(buffer, 4, size)));
  const start = 4 + size;
  const columns: BinaryFile["columns"] = {};
  for (const c of header.columns as { name: string; type: keyof typeof TYPES; offset: number; length: number }[]) {
    columns[c.name] = new TYPES[c.type](buffer, start + c.offset, c.length);
  }
  return { header, columns };
}

/** Download a binary file. Files are gzipped by us, because GitHub Pages wouldn't compress them. */
export async function fetchBinary(url: string): Promise<BinaryFile> {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Could not load ${url}: HTTP ${resp.status}`);
  const raw = await resp.arrayBuffer();
  const magic = new Uint8Array(raw, 0, 2);
  if (magic[0] !== 0x1f || magic[1] !== 0x8b) return parseBinary(raw); // a server already unzipped it
  const stream = new Blob([raw]).stream().pipeThrough(new DecompressionStream("gzip"));
  return parseBinary(await new Response(stream).arrayBuffer());
}

/** A lots file as lot data. */
export function parcelDataFrom(file: BinaryFile): ParcelData {
  const h = file.header as unknown as Omit<ParcelData, "columns">;
  return { ...h, parcel_id_exceptions: h.parcel_id_exceptions ?? {}, columns: file.columns as unknown as ParcelData["columns"] };
}

export async function loadLots(url: string): Promise<ParcelData> {
  return parcelDataFrom(await fetchBinary(url));
}

export async function loadJson<T>(url: string): Promise<T> {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Could not load ${url}: HTTP ${resp.status}`);
  return (await resp.json()) as T;
}

export function parcelId(data: ParcelData, pid: number): string {
  const id = data.columns.parcel_id[pid];
  return Number.isNaN(id) ? data.parcel_id_exceptions[pid] ?? "unnumbered" : String(id);
}

/** Engine inputs for one lot. Built when needed: holding 1.3 million of these takes gigabytes. */
export function lotAt(data: ParcelData, pid: number): Lot {
  const c = data.columns;
  return {
    area_sqft: c.lot_area_sqft[pid],
    width_ft: c.lot_width_tenths[pid] / 10,
    depth_ft: c.lot_depth_tenths[pid] / 10,
    overlays: data.codes.overlay_sets[c.overlay_set[pid]],
    dist_major_transit_ft: na(c.dist_major_transit_ft[pid]),
    existing_units: na(c.existing_units[pid]),
    dist_single_family_ft: na(c.dist_single_family_ft[pid]),
  };
}

/** The rule file a lot uses, or null if its zone isn't modeled. */
export function zoneAt(data: ParcelData, pid: number): string | null {
  const z = data.columns.rules_zone[pid];
  return z >= 0 ? data.codes.rules_zone[z] : null;
}
