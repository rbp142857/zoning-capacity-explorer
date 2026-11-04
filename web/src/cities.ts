// Showing several cities at once.
//
// Each city keeps its own rule files, because "R1" means something different
// in every city, so the engine runs city by city. Everything that only reads
// the answers (headline, legend, charts, map colors) sees one combined list
// of lots, in which a city's lots start at its `offset`.

import type { ParcelData } from "./data";
import { type Results, emptyResults } from "./engine/run";

export interface CityInfo {
  id: string;
  name: string;
  center: [number, number];
  zoom: number;
  bounds: [number, number, number, number];
  count: number;
  tiles: string; // which shared tiles file holds its lots
  start: number; // its lot with pid i is lot start + i in that file
  level?: string; // "Fuller" or "Usable", from reports/la_county/coverage.md
}

/** Where the map opens with no city selected. */
export const COUNTY_VIEW: { center: [number, number]; zoom: number } = { center: [-118.25, 34.1], zoom: 9 };

/** `city` of combined data, whose district codes are city names. */
export const COMBINED = "(several cities)";

export const shortName = (c: { name: string }) => c.name.split(",")[0];

// One city, for phones and for links to a city that doesn't exist.
const LIGHT_CITY = "pasadena";

/**
 * Which cities the address asks for: ?cities=a,b or ?cities=all (or the older ?city=a).
 * With neither, a computer opens on every city and a phone on one, since a phone
 * has the least memory and the smallest screen.
 */
export function selectionFromSearch(search: string, allIds: string[], smallScreen = false): string[] {
  const params = new URLSearchParams(search);
  const many = params.get("cities");
  const one = params.get("city");
  if (many === "all") return allIds;
  if (many === null && one === null) {
    if (!smallScreen) return allIds;
    return allIds.includes(LIGHT_CITY) ? [LIGHT_CITY] : allIds.slice(0, 1);
  }
  // A real param, even an empty one, wins: "?cities=" is "no cities selected".
  const wanted = many !== null ? many.split(",") : [one as string];
  const known = allIds.filter((id) => wanted.includes(id));
  if (known.length || many === "") return known;
  // A link to a city that doesn't exist.
  return allIds.includes(LIGHT_CITY) ? [LIGHT_CITY] : allIds.slice(0, 1);
}

/** The address's search part for a selection, leaving other params alone. */
export function selectionToSearch(search: string, selected: string[], allIds: string[]): string {
  const params = new URLSearchParams(search);
  params.delete("city");
  params.delete("cities");
  if (selected.length === 1) params.set("city", selected[0]);
  else params.set("cities", selected.length === allIds.length ? "all" : selected.join(","));
  return `?${params.toString().replace(/%2C/g, ",")}`;
}

type IntColumn = Int8Array | Uint8Array | Int16Array | Int32Array | Float64Array;

/** Join columns end to end. */
function join<T extends IntColumn>(Type: new (n: number) => T, parts: IntColumn[], total: number): T {
  const out = new Type(total);
  let at = 0;
  for (const part of parts) {
    out.set(part as unknown as ArrayLike<number> & Int32Array & Float64Array, at);
    at += part.length;
  }
  return out;
}

/** Combine cities' parcel data; each city's codes are renumbered into shared lists. */
export function mergeParcelData(cities: ParcelData[], names: string[]): ParcelData {
  if (cities.length === 1) return cities[0];
  const total = cities.reduce((n, d) => n + d.count, 0);
  const col = <K extends keyof ParcelData["columns"]>(key: K) => cities.map((d) => d.columns[key] as unknown as IntColumn);
  const ints = (key: keyof ParcelData["columns"]) => join(Int32Array, col(key), total);
  const small = (key: keyof ParcelData["columns"]) => join(Int8Array, col(key), total);
  const out: ParcelData = {
    city: COMBINED,
    count: total,
    bounds: unionBounds(cities.map((c) => c.bounds)),
    // Every city's export uses the same list of limits (BINDING_CODES).
    codes: { binding: cities[0]?.codes.binding ?? [], zone: [], rules_zone: [], overlay_sets: [], district: names },
    headline: {
      existing_units: 0, local_units: 0, max_units: 0, net_new_units: 0, lots_modeled: 0, lots_not_modeled: 0,
      single_home_land_share: 0, residential_land_sqft: 0,
    },
    parcel_id_exceptions: {},
    columns: {
      parcel_id: join(Float64Array, col("parcel_id"), total),
      zone: new Int32Array(total),
      existing_units: ints("existing_units"),
      building_sqft: ints("building_sqft"),
      local_units: ints("local_units"),
      max_units: ints("max_units"),
      net_new_units: ints("net_new_units"),
      binding: small("binding"),
      lot_area_sqft: ints("lot_area_sqft"),
      lot_width_tenths: ints("lot_width_tenths"),
      lot_depth_tenths: ints("lot_depth_tenths"),
      dist_major_transit_ft: ints("dist_major_transit_ft"),
      dist_single_family_ft: ints("dist_single_family_ft"),
      dist_sb79_t1_ft: ints("dist_sb79_t1_ft"),
      dist_sb79_t2_ft: ints("dist_sb79_t2_ft"),
      sb79_zone_ok: small("sb79_zone_ok"),
      sb79_half_mile: small("sb79_half_mile"),
      rules_zone: new Int32Array(total),
      overlay_set: new Int32Array(total),
      district: new Int16Array(total),
      redev_mask: join(Uint8Array, col("redev_mask"), total),
    },
  };
  const zoneIndex = new Map<string, number>();
  const zoneCode = (zone: string) => {
    if (!zoneIndex.has(zone)) {
      zoneIndex.set(zone, out.codes.zone.length);
      out.codes.zone.push(zone);
    }
    return zoneIndex.get(zone) as number;
  };
  const h = out.headline;
  let oneHomeLand = 0;
  let at = 0;
  cities.forEach((d, cityIndex) => {
    const c = d.columns;
    const o = out.columns;
    const zones = d.codes.zone.map(zoneCode);
    const ruleBase = out.codes.rules_zone.length;
    const overlayBase = out.codes.overlay_sets.length;
    out.codes.rules_zone.push(...d.codes.rules_zone);
    out.codes.overlay_sets.push(...d.codes.overlay_sets);
    for (let pid = 0; pid < d.count; pid++, at++) {
      o.zone[at] = c.zone[pid] >= 0 ? zones[c.zone[pid]] : -1;
      o.rules_zone[at] = c.rules_zone[pid] >= 0 ? ruleBase + c.rules_zone[pid] : -1;
      o.overlay_set[at] = overlayBase + c.overlay_set[pid];
      o.district[at] = cityIndex; // charts show one bar per city
    }
    for (const [pid, id] of Object.entries(d.parcel_id_exceptions)) out.parcel_id_exceptions[at - d.count + Number(pid)] = id;
    h.existing_units += d.headline.existing_units;
    h.local_units += d.headline.local_units;
    h.max_units += d.headline.max_units;
    h.net_new_units += d.headline.net_new_units;
    h.lots_modeled += d.headline.lots_modeled;
    h.lots_not_modeled += d.headline.lots_not_modeled;
    h.residential_land_sqft += d.headline.residential_land_sqft;
    oneHomeLand += d.headline.single_home_land_share * d.headline.residential_land_sqft;
  });
  h.single_home_land_share = h.residential_land_sqft ? oneHomeLand / h.residential_land_sqft : 0;
  return out;
}

/** Combine cities' results, in the same order as mergeParcelData. */
export function mergeResults(results: Results[]): Results {
  if (results.length === 1) return results[0];
  const total = results.reduce((n, r) => n + r.max.length, 0);
  const out = emptyResults(total);
  let at = 0;
  for (const r of results) {
    out.max.set(r.max, at);
    out.local.set(r.local, at);
    out.net.set(r.net, at);
    out.binding.set(r.binding, at);
    out.realistic.set(r.realistic, at);
    at += r.max.length;
    for (const key of Object.keys(out.totals) as (keyof Results["totals"])[]) out.totals[key] += r.totals[key];
  }
  return out;
}

export function unionBounds(all: ParcelData["bounds"][]): ParcelData["bounds"] {
  if (!all.length) return [0, 0, 0, 0];
  return [
    Math.min(...all.map((b) => b[0])),
    Math.min(...all.map((b) => b[1])),
    Math.max(...all.map((b) => b[2])),
    Math.max(...all.map((b) => b[3])),
  ];
}
