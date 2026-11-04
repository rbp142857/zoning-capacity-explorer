import { describe, expect, it } from "vitest";
import { lotsCsv } from "./csv";
import type { ParcelData } from "./data";
import type { Results } from "./engine/run";

const data = {
  count: 2,
  codes: { zone: ["R3", 'A,"B"'] },
  columns: {
    parcel_id: ["111", "222"], zone: [0, 1], lot_area_sqft: [5000, 9000], existing_units: [1, null],
    redev_mask: [63, 31], dist_major_transit_ft: [2640, null],
  },
} as unknown as ParcelData;

const results = (over: Partial<Results> = {}): Results =>
  ({ max: [4, null], net: [3, null], realistic: [3, 0], binding: [2, -1], ...over }) as unknown as Results;

describe("lotsCsv", () => {
  const lines = lotsCsv(data, results(), results({ max: [8, null], net: [7, null], realistic: [7, 0] }), "https://x/?a=1", true).trim().split("\n");

  it("starts with the source and disclaimer, then a header", () => {
    expect(lines[0]).toContain("not legal or zoning advice");
    expect(lines[1].startsWith("parcel_id,zone,")).toBe(true);
  });

  it("writes a modeled lot, with today and the scenario", () => {
    expect(lines[2]).toBe("111,R3,5000,1,1,4,3,3,0,0.5,8,7,7");
  });

  it("leaves unknown values blank, flags special land and quotes awkward zones", () => {
    expect(lines[3]).toBe('222,"A,""B""",9000,,0,,,,1,,,,');
  });

  it("leaves out scenario columns when there's no reform", () => {
    expect(lotsCsv(data, results(), results(), "u", false).split("\n")[1]).not.toContain("scenario");
  });

  it("has no owner or mailing fields", () => {
    expect(lines[1]).not.toMatch(/owner|mail|name/i);
  });
});
