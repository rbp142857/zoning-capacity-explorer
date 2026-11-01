import { describe, expect, it } from "vitest";

import { mergeParcelData, mergeResults, selectionFromSearch, selectionToSearch } from "./cities";
import type { ParcelData } from "./data";
import type { Results } from "./engine/run";

const ALL = ["burbank", "glendale", "pasadena"];

describe("city selection in the address", () => {
  it("keeps old links working", () => {
    expect(selectionFromSearch("", ALL)).toEqual(["pasadena"]);
    expect(selectionFromSearch("?city=burbank", ALL)).toEqual(["burbank"]);
    expect(selectionFromSearch("?city=nowhere", ALL)).toEqual(["burbank"]);
  });
  it("reads several cities, all cities, or none", () => {
    expect(selectionFromSearch("?cities=glendale,burbank", ALL)).toEqual(["burbank", "glendale"]);
    expect(selectionFromSearch("?cities=all", ALL)).toEqual(ALL);
    expect(selectionFromSearch("?cities=", ALL)).toEqual([]);
  });
  it("round-trips through the address", () => {
    for (const selected of [["glendale"], ["burbank", "pasadena"], ALL, []]) {
      expect(selectionFromSearch(selectionToSearch("?x=1", selected, ALL), ALL)).toEqual(selected);
    }
    expect(selectionToSearch("?city=burbank", ALL, ALL)).toBe("?cities=all");
  });
});

function city(zones: string[], lots: number, land: number, share: number, bounds: ParcelData["bounds"]): ParcelData {
  const none = () => Array(lots).fill(0);
  return {
    city: "x", generated_at: "", count: lots, bounds,
    codes: { binding: ["density"], zone: zones, rules_zone: zones, overlay_sets: [[]], district: ["D"] },
    headline: {
      existing_units: lots, local_units: lots, max_units: lots, net_new_units: 0, lots_modeled: lots, lots_not_modeled: 0,
      single_home_land_share: share, residential_land_sqft: land,
    },
    columns: {
      parcel_id: none().map((_, i) => `p${i}`), zone: none(), existing_units: none(), local_units: none(), max_units: none(),
      net_new_units: none(), binding: none(), lot_area_sqft: none(), lot_width_ft: none(), lot_depth_ft: none(),
      dist_major_transit_ft: none(), dist_single_family_ft: none(), rules_zone: none(), overlay_set: none(),
      district: none(), redev_mask: none(),
    },
  };
}

describe("combining cities", () => {
  const a = city(["R1"], 2, 100, 0.5, [-118, 34, -117.9, 34.1]);
  const b = city(["R1", "C2"], 1, 300, 0.9, [-118.5, 33.9, -118.4, 34]);
  b.columns.zone[0] = 1;

  it("leaves a single city untouched", () => {
    expect(mergeParcelData([a], ["A"])).toBe(a);
  });
  it("renumbers codes, adds totals and weights the land share", () => {
    const m = mergeParcelData([a, b], ["A", "B"]);
    expect(m.count).toBe(3);
    expect(m.codes.zone).toEqual(["R1", "C2"]);
    expect(m.columns.zone).toEqual([0, 0, 1]);
    expect(m.codes.district).toEqual(["A", "B"]);
    expect(m.columns.district).toEqual([0, 0, 1]);
    expect(m.headline.existing_units).toBe(3);
    expect(m.headline.single_home_land_share).toBeCloseTo(0.8); // (0.5 x 100 + 0.9 x 300) / 400
    expect(m.bounds).toEqual([-118.5, 33.9, -117.9, 34.1]);
  });
  it("handles no cities", () => {
    const m = mergeParcelData([], []);
    expect(m.count).toBe(0);
    expect(m.headline.single_home_land_share).toBe(0);
  });
  it("adds results in order", () => {
    const r = (v: number): Results => ({
      max: [v], local: [v], net: [v], binding: [0], likely: [false], realistic: [0],
      totals: { max: v, local: v, net: v, existing: v, realistic: 0, likelyLots: 0 },
    });
    const m = mergeResults([r(2), r(5)]);
    expect(m.max).toEqual([2, 5]);
    expect(m.totals.max).toBe(7);
  });
});
