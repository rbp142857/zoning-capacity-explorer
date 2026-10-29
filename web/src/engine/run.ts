// Run the engine over every lot for one scenario.

import type { ParcelData } from "../data";
import type { EngineAssumptions, Lot } from "./constraints";
import { type Scenario, applyScenario, capacityUnderScenario } from "./scenario";
import type { RulesFile } from "./types";

/** Results for every lot, as columns indexed by pid (like parcels.json). */
export interface Results {
  max: (number | null)[];
  local: (number | null)[];
  net: (number | null)[];
  binding: number[]; // index into data.codes.binding, -1 = not modeled
  totals: { max: number; local: number; net: number; existing: number };
}

/** Engine inputs for each lot, built once from parcels.json. */
export interface LotInputs {
  lots: Lot[];
  zones: (string | null)[];
}

export function buildLotInputs(data: ParcelData): LotInputs {
  const c = data.columns;
  const lots: Lot[] = [];
  const zones: (string | null)[] = [];
  for (let pid = 0; pid < data.count; pid++) {
    lots.push({
      area_sqft: c.lot_area_sqft[pid],
      width_ft: c.lot_width_ft[pid],
      depth_ft: c.lot_depth_ft[pid],
      overlays: data.codes.overlay_sets[c.overlay_set[pid]],
      dist_major_transit_ft: c.dist_major_transit_ft[pid],
      existing_units: c.existing_units[pid],
    });
    zones.push(c.rules_zone[pid] >= 0 ? data.codes.rules_zone[c.rules_zone[pid]] : null);
  }
  return { lots, zones };
}

export function runScenario(data: ParcelData, inputs: LotInputs, rules: RulesFile, scenario: Scenario): Results {
  const [zoneRules, state] = applyScenario(rules.zones, rules.state, scenario);
  const a: EngineAssumptions = rules.assumptions;
  const codeOf = new Map(data.codes.binding.map((name, i) => [name, i]));
  const out: Results = {
    max: [], local: [], net: [], binding: [],
    totals: { max: 0, local: 0, net: 0, existing: 0 },
  };
  for (let pid = 0; pid < data.count; pid++) {
    const r = capacityUnderScenario(inputs.zones[pid], inputs.lots[pid], a, zoneRules, state, scenario);
    out.max.push(r.max_units);
    out.local.push(r.local_units);
    out.net.push(r.net_new_units);
    out.binding.push(r.binding_constraint === null ? -1 : codeOf.get(r.binding_constraint) ?? -1);
    if (r.status === "ok") {
      out.totals.max += r.max_units ?? 0;
      out.totals.local += r.local_units ?? 0;
      out.totals.net += r.net_new_units ?? 0;
      out.totals.existing += inputs.lots[pid].existing_units ?? 0;
    }
  }
  return out;
}
