// Parity test: the TypeScript engine must give exactly the same answers as
// the Python engine for every lot and scenario in shared/fixtures/golden.json.
// Regenerate the golden file with `make golden` after changing the Python side.

import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { redevelopment } from "./redevelop";
import { type Scenario, applyScenario, capacityUnderScenario } from "./scenario";
import type { RulesFile } from "./types";

const root = fileURLToPath(new URL("../../../", import.meta.url));
const goldenFiles = readdirSync(`${root}shared/fixtures`).filter((f) => /^golden_.+\.json$/.test(f));

interface GoldenLot {
  zone: string | null;
  area_sqft: number;
  width_ft: number;
  depth_ft: number;
  overlays: string[];
  dist_major_transit_ft: number | null;
  existing_units: number | null;
  redev_mask: number;
}

for (const file of goldenFiles) {
const golden = JSON.parse(readFileSync(`${root}shared/fixtures/${file}`, "utf8"));
const rules: RulesFile = JSON.parse(readFileSync(`${root}web/public/data/${golden.city}/rules.json`, "utf8"));

describe(`TypeScript engine matches Python (${file})`, () => {
  for (const [name, scenario] of Object.entries(golden.scenarios as Record<string, Scenario>)) {
    it(`scenario: ${name}`, () => {
      const [r2, st2] = applyScenario(rules.zones, rules.state, scenario);
      const mismatches: string[] = [];
      (golden.lots as GoldenLot[]).forEach((d, i) => {
        const lot = {
          area_sqft: d.area_sqft,
          width_ft: d.width_ft,
          depth_ft: d.depth_ft,
          overlays: d.overlays,
          dist_major_transit_ft: d.dist_major_transit_ft,
          existing_units: d.existing_units,
        };
        const got = capacityUnderScenario(d.zone, lot, rules.assumptions, r2, st2, scenario);
        const want = golden.expected[name][i];
        const redev = redevelopment(rules.redevelopment, d.redev_mask, got.local_units, d.existing_units);
        const actual = {
          likely_redevelop: redev.likely,
          realistic_new_units: redev.realistic_new_units,
          max_units: got.max_units,
          local_units: got.local_units,
          binding_constraint: got.binding_constraint,
          net_new_units: got.net_new_units,
          limits: got.limits,
        };
        if (JSON.stringify(sortKeys(actual)) !== JSON.stringify(sortKeys(want))) {
          mismatches.push(`lot ${i} (${d.zone}, ${d.area_sqft} sf): got ${JSON.stringify(actual)} want ${JSON.stringify(want)}`);
        }
      });
      expect(mismatches.slice(0, 5)).toEqual([]);
    });
  }
});
}

function sortKeys(o: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const k of Object.keys(o).sort()) {
    const v = o[k];
    out[k] = v && typeof v === "object" && !Array.isArray(v) ? sortKeys(v as Record<string, unknown>) : v;
  }
  return out;
}
