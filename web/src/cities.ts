// Showing several cities at once.
//
// Each city keeps its own rule files, because "R1" means something different
// in every city, so the engine runs city by city. Everything that only reads
// the answers (headline, legend, charts, map colors) sees one combined list
// of lots, in which a city's lots start at its `offset`.

import type { ParcelData } from "./data";
import type { Results } from "./engine/run";

export interface CityInfo {
  id: string;
  name: string;
  center: [number, number];
  zoom: number;
}

/** `city` of combined data, whose district codes are city names. */
export const COMBINED = "(several cities)";

export const shortName = (c: { name: string }) => c.name.split(",")[0];

// Links shared before more cities were added have no city in them, and were
// made for Pasadena, so it stays the default.
const DEFAULT_CITY = "pasadena";

/** Which cities the address asks for: ?cities=a,b or ?cities=all (or the older ?city=a). */
export function selectionFromSearch(search: string, allIds: string[]): string[] {
  const params = new URLSearchParams(search);
  const many = params.get("cities");
  if (many === "all") return allIds;
  // A real param, even an empty one, wins: "?cities=" is "no cities selected".
  const wanted = many !== null ? many.split(",") : [params.get("city") ?? DEFAULT_CITY];
  const known = allIds.filter((id) => wanted.includes(id));
  if (known.length || many === "") return known;
  return allIds.slice(0, 1); // a link to a city that doesn't exist
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

/** Combine cities' parcel data; each city's codes are renumbered into shared lists. */
export function mergeParcelData(cities: ParcelData[], names: string[]): ParcelData {
  if (cities.length === 1) return cities[0];
  const out: ParcelData = {
    city: COMBINED,
    generated_at: cities[0]?.generated_at ?? "",
    count: 0,
    bounds: unionBounds(cities.map((c) => c.bounds)),
    // Every city's export uses the same list of limits (BINDING_CODES).
    codes: { binding: cities[0]?.codes.binding ?? [], zone: [], rules_zone: [], overlay_sets: [], district: names },
    headline: {
      existing_units: 0, local_units: 0, max_units: 0, net_new_units: 0, lots_modeled: 0, lots_not_modeled: 0,
      single_home_land_share: 0, residential_land_sqft: 0,
    },
    columns: {
      parcel_id: [], zone: [], existing_units: [], local_units: [], max_units: [], net_new_units: [], binding: [],
      lot_area_sqft: [], lot_width_ft: [], lot_depth_ft: [], dist_major_transit_ft: [], dist_single_family_ft: [],
      rules_zone: [], overlay_set: [], district: [], redev_mask: [],
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
  cities.forEach((d, cityIndex) => {
    const c = d.columns;
    const o = out.columns;
    const zones = d.codes.zone.map(zoneCode);
    const ruleBase = out.codes.rules_zone.length;
    const overlayBase = out.codes.overlay_sets.length;
    out.codes.rules_zone.push(...d.codes.rules_zone);
    out.codes.overlay_sets.push(...d.codes.overlay_sets);
    for (let pid = 0; pid < d.count; pid++) {
      o.parcel_id.push(c.parcel_id[pid]);
      o.zone.push(c.zone[pid] >= 0 ? zones[c.zone[pid]] : -1);
      o.existing_units.push(c.existing_units[pid]);
      o.local_units.push(c.local_units[pid]);
      o.max_units.push(c.max_units[pid]);
      o.net_new_units.push(c.net_new_units[pid]);
      o.binding.push(c.binding[pid]);
      o.lot_area_sqft.push(c.lot_area_sqft[pid]);
      o.lot_width_ft.push(c.lot_width_ft[pid]);
      o.lot_depth_ft.push(c.lot_depth_ft[pid]);
      o.dist_major_transit_ft.push(c.dist_major_transit_ft[pid]);
      o.dist_single_family_ft.push(c.dist_single_family_ft[pid]);
      o.rules_zone.push(c.rules_zone[pid] >= 0 ? ruleBase + c.rules_zone[pid] : -1);
      o.overlay_set.push(overlayBase + c.overlay_set[pid]);
      o.district.push(cityIndex); // charts show one bar per city
      o.redev_mask.push(c.redev_mask[pid]);
    }
    out.count += d.count;
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
  const out: Results = {
    max: [], local: [], net: [], binding: [], likely: [], realistic: [],
    totals: { max: 0, local: 0, net: 0, existing: 0, realistic: 0, likelyLots: 0 },
  };
  for (const r of results) {
    for (let i = 0; i < r.max.length; i++) {
      out.max.push(r.max[i]);
      out.local.push(r.local[i]);
      out.net.push(r.net[i]);
      out.binding.push(r.binding[i]);
      out.likely.push(r.likely[i]);
      out.realistic.push(r.realistic[i]);
    }
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
