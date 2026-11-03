import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { densityBonusUnits, sb79Units } from "./statePaths";

const data = JSON.parse(readFileSync(new URL("../../../shared/fixtures/state_paths.json", import.meta.url), "utf8"));

describe("state paths match Python", () => {
  it("SB 79", () => {
    for (const c of data.sb79) expect(sb79Units(...(c.args as Parameters<typeof sb79Units>))).toBe(c.want);
  });
  it("density bonus", () => {
    for (const c of data.bonus) expect(densityBonusUnits(c.limits, c.share)).toBe(c.want);
  });
});
