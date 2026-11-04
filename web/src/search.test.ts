import { describe, expect, it } from "vitest";

import { makeAddressIndex, searchAddresses } from "./search";

const make = (lines: string[], offset = 5) => {
  const lng = new Float32Array(lines.map((_, i) => i + 1));
  return makeAddressIndex(lines.join("\n"), lng, lng.map((v) => v * 2), offset);
};
const index = [make(["10 E COLORADO BLVD, 91105", "100 N LAKE AVE, 91101", "1000 E COLORADO BLVD, 91106", "22 LAKE ST, 91103"])];
const ids: Record<string, number> = { "5713000006": 5, "5713000001": 0 };
const find = (digits: string) => ids[digits] ?? -1;

describe("address search", () => {
  it("needs at least 3 characters", () => {
    expect(searchAddresses(index, "10", find)).toEqual([]);
  });

  it("matches every word, case-insensitive, prefix matches first", () => {
    expect(searchAddresses(index, "colorado 10", find).map((h) => h.pid)).toEqual([5, 7]);
    expect(searchAddresses(index, "lake", find).map((h) => h.pid)).toEqual([6, 8]);
  });

  it("returns the lot's point", () => {
    expect(searchAddresses(index, "22 lake", find)[0]).toMatchObject({ pid: 8, lng: 4, lat: 8, address: "22 LAKE ST, 91103" });
  });

  it("finds a lot by assessor parcel number, with or without dashes", () => {
    const hits = searchAddresses(index, "5713-000-006", find);
    expect(hits[0].pid).toBe(5);
    expect(hits[0].address).toContain("5713000006");
  });

  it("finds a lot with no address by its parcel number, and not by words", () => {
    const withBlank = [make(["", "100 N LAKE AVE, 91101", "22 LAKE ST, 91103"], 0)];
    const hits = searchAddresses(withBlank, "5713000001", find);
    expect(hits).toHaveLength(1);
    expect(hits[0]).toMatchObject({ pid: 0, lng: 1, lat: 2, address: "Lot 5713000001 (no address on record)" });
    expect(searchAddresses(withBlank, "lake", find).map((h) => h.pid)).toEqual([1, 2]);
  });

  it("finds an exact address after thousands of lines that share its city name", () => {
    const lines = Array.from({ length: 5000 }, (_, i) => `${i + 1} ELM ST ALHAMBRA CA 91801`);
    const big = [make(["9 ROSE AVE ARCADIA CA 91007", ...lines, "2909 W MAIN ST ALHAMBRA CA 91801"], 0)];
    expect(searchAddresses(big, "2909 W MAIN ST ALHAMBRA CA 91801", find)[0]?.pid).toBe(5001);
  });

  it("searches every selected city, each with its own numbering", () => {
    const two = [make(["1 MAIN ST"], 0), make(["2 MAIN ST"], 100)];
    expect(searchAddresses(two, "main", find).map((h) => h.pid)).toEqual([0, 100]);
  });
});
