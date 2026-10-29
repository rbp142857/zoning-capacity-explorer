import { describe, expect, it } from "vitest";

import { searchAddresses } from "./search";

const index = {
  address: ["10 E COLORADO BLVD, 91105", "100 N LAKE AVE, 91101", "1000 E COLORADO BLVD, 91106", "22 LAKE ST, 91103"],
  pid: [5, 6, 7, 8],
  lng: [0, 0, 0, 0],
  lat: [0, 0, 0, 0],
};
const ids = ["5713000001", "5713000002", "5713000003", "5713000004", "5713000005", "5713000006", "5713000007", "5713000008", "5713000009"];

describe("address search", () => {
  it("needs at least 3 characters", () => {
    expect(searchAddresses(index, "10", ids)).toEqual([]);
  });

  it("matches every word, case-insensitive, prefix matches first", () => {
    const hits = searchAddresses(index, "colorado 10", ids).map((h) => h.pid);
    expect(hits).toEqual([5, 7]);
    expect(searchAddresses(index, "lake", ids).map((h) => h.pid)).toEqual([6, 8]);
  });

  it("finds a lot by assessor parcel number, with or without dashes", () => {
    const hits = searchAddresses(index, "5713-000-006", ids);
    expect(hits[0].pid).toBe(5);
    expect(hits[0].address).toContain("5713000006");
  });
});
