// Every lot in every city: the browser engine's answer under today's rules
// must equal the pipeline's (lots.bin.gz), and the quick results the site opens
// with must equal both. The golden test checks samples under many scenarios.

import { gunzipSync } from "node:zlib";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { BINDING_CODES, parcelDataFrom, parseBinary } from "../data";
import { resultsFromColumns, runScenario } from "./run";
import { BASELINE } from "./scenario";
import type { RulesFile } from "./types";

const dataRoot = fileURLToPath(new URL("../../public/data/", import.meta.url));
const cities = readdirSync(dataRoot).filter((d) => existsSync(`${dataRoot}${d}/lots.bin.gz`));

function firstDifference(a: ArrayLike<number>, b: ArrayLike<number>): number {
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return i;
  return -1;
}

describe("browser engine matches the pipeline on every lot", () => {
  it("found the cities", () => {
    expect(cities.length).toBeGreaterThan(0);
  });
  for (const city of cities) {
    it(city, () => {
      const raw = gunzipSync(readFileSync(`${dataRoot}${city}/lots.bin.gz`));
      const data = parcelDataFrom(parseBinary(raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength) as ArrayBuffer));
      const rules: RulesFile = JSON.parse(readFileSync(`${dataRoot}${city}/rules.json`, "utf8"));
      expect(data.codes.binding).toEqual(BINDING_CODES);

      const engine = runScenario(data, rules, BASELINE);
      expect(firstDifference(engine.max, data.columns.max_units)).toBe(-1);
      expect(engine.totals.max).toBe(data.headline.max_units);

      // What the site opens with, without running the engine.
      const quick = resultsFromColumns(data, rules);
      expect(firstDifference(quick.max, engine.max)).toBe(-1);
      expect(firstDifference(quick.local, engine.local)).toBe(-1);
      expect(firstDifference(quick.net, engine.net)).toBe(-1);
      expect(firstDifference(quick.binding, engine.binding)).toBe(-1);
      expect(firstDifference(quick.realistic, engine.realistic)).toBe(-1);
      expect(quick.totals).toEqual(engine.totals);
    });
  }
});
