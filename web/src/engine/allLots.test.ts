// Every lot in every city: the browser engine's answer under today's rules
// must equal the pipeline's (parcels.json). The golden test checks samples
// under many scenarios; this one checks all ~65,000 lots under one.

import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import type { ParcelData } from "../data";
import { buildLotInputs, runScenario } from "./run";
import { BASELINE } from "./scenario";
import type { RulesFile } from "./types";

const dataRoot = fileURLToPath(new URL("../../public/data/", import.meta.url));
const cities = readdirSync(dataRoot).filter((d) => existsSync(`${dataRoot}${d}/parcels.json`));

describe("browser engine matches the pipeline on every lot", () => {
  for (const city of cities) {
    it(city, () => {
      const data: ParcelData = JSON.parse(readFileSync(`${dataRoot}${city}/parcels.json`, "utf8"));
      const rules: RulesFile = JSON.parse(readFileSync(`${dataRoot}${city}/rules.json`, "utf8"));
      const results = runScenario(data, buildLotInputs(data), rules, BASELINE);
      const wrong = data.columns.max_units
        .map((want, pid) => (want === results.max[pid] ? null : `pid ${pid}: pipeline ${want}, browser ${results.max[pid]}`))
        .filter((x) => x !== null);
      expect(wrong.slice(0, 5)).toEqual([]);
      expect(results.totals.max).toBe(data.headline.max_units);
    });
  }
});
