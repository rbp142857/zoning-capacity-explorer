import { describe, expect, it } from "vitest";

import { BASELINE } from "./engine/scenario";
import { scenarioFromHash, scenarioToHash } from "./url";

describe("scenario URL", () => {
  it("today's rules give an empty hash", () => {
    expect(scenarioToHash(BASELINE)).toBe("");
  });

  it("round-trips every lever", () => {
    const s = {
      ...BASELINE,
      sf_units_per_lot: 4,
      sf_min_lot_sqft: 2500,
      parking_per_unit: 0,
      parking_exempt_radius_ft: 5280,
      transit_radius_ft: 1320,
      transit_extra_stories: 2,
      transit_density_multiplier: 1.5,
      housing_in_cg: true,
      adu_units_added: 3,
    };
    const hash = scenarioToHash(s);
    expect(hash).toBe("#v=1&sf=4&ml=2500&pk=0&pr=5280&tr=1320&ts=2&td=1.5&cg=1&adu=3");
    expect(scenarioFromHash(hash)).toEqual(s);
  });

  it("only writes levers that changed", () => {
    expect(scenarioToHash({ ...BASELINE, sf_units_per_lot: 4 })).toBe("#v=1&sf=4");
  });

  it("ignores bad values, unknown keys and other versions", () => {
    expect(scenarioFromHash("#v=1&sf=99&zz=1&pk=abc")).toEqual(BASELINE);
    expect(scenarioFromHash("#v=2&sf=4")).toEqual(BASELINE);
    expect(scenarioFromHash("")).toEqual(BASELINE);
  });
});
