// Run the engine over every lot for one scenario.

import { NA, type ParcelData, lotAt, zoneAt } from "../data";
import type { EngineAssumptions } from "./constraints";
import { LAND, likelyNewUnits } from "./redevelop";
import { type Scenario, applyScenario, capacityUnderScenario } from "./scenario";
import type { RulesFile } from "./types";

/** Results for every lot, as columns indexed by pid. NA means unknown (see data.ts). */
export interface Results {
  max: Int32Array;
  local: Int32Array;
  net: Int32Array;
  binding: Int8Array; // index into data.codes.binding, -1 = not modeled
  realistic: Int32Array; // net new homes counted in the realistic estimate (0 if not likely)
  // specialLandNet: the part of `net` on public or special land (see engine/redevelop.ts).
  totals: { max: number; local: number; net: number; existing: number; realistic: number; likelyLots: number; specialLandNet: number };
}

export function emptyResults(count: number): Results {
  return {
    max: new Int32Array(count), local: new Int32Array(count), net: new Int32Array(count),
    binding: new Int8Array(count), realistic: new Int32Array(count),
    totals: { max: 0, local: 0, net: 0, existing: 0, realistic: 0, likelyLots: 0, specialLandNet: 0 },
  };
}

const asColumn = (v: number | null) => (v === null ? NA : v);

/**
 * Today's results, from the numbers the pipeline already worked out. This is far
 * faster than running the engine on every lot, and allLots.test.ts checks that
 * the two agree on every lot in every city.
 */
export function resultsFromColumns(data: ParcelData, rules: RulesFile): Results {
  const c = data.columns;
  const out = emptyResults(data.count);
  out.max.set(c.max_units);
  out.local.set(c.local_units);
  out.net.set(c.net_new_units);
  out.binding.set(c.binding);
  const t = out.totals;
  for (let pid = 0; pid < data.count; pid++) {
    const local = c.local_units[pid];
    const existing = c.existing_units[pid];
    const mask = c.redev_mask[pid];
    const likely = likelyNewUnits(rules.redevelopment, mask, local === NA ? null : local, existing === NA ? null : existing);
    if (likely > 0) out.realistic[pid] = likely;
    if (c.binding[pid] < 0) continue;
    const net = c.net_new_units[pid] === NA ? 0 : c.net_new_units[pid];
    t.max += c.max_units[pid] === NA ? 0 : c.max_units[pid];
    t.local += local === NA ? 0 : local;
    t.net += net;
    if (!(mask & LAND)) t.specialLandNet += net;
    t.existing += existing === NA ? 0 : existing;
    if (likely >= 0) {
      t.realistic += likely;
      t.likelyLots++;
    }
  }
  return out;
}

/** The engine over every lot, pausing at each yield so a page can stay responsive. */
function* scenarioSteps(data: ParcelData, rules: RulesFile, scenario: Scenario, out: Results): Generator<void> {
  const [zoneRules, state] = applyScenario(rules.zones, rules.state, scenario);
  const a: EngineAssumptions = rules.assumptions;
  const codeOf = new Map(data.codes.binding.map((name, i) => [name, i]));
  const mask = data.columns.redev_mask;
  const t = out.totals;
  for (let pid = 0; pid < data.count; pid++) {
    if (pid % 2000 === 0) yield;
    const lot = lotAt(data, pid);
    const r = capacityUnderScenario(zoneAt(data, pid), lot, a, zoneRules, state, scenario);
    out.max[pid] = asColumn(r.max_units);
    out.local[pid] = asColumn(r.local_units);
    out.net[pid] = asColumn(r.net_new_units);
    out.binding[pid] = r.binding_constraint === null ? -1 : codeOf.get(r.binding_constraint) ?? -1;
    const likely = likelyNewUnits(rules.redevelopment, mask[pid], r.local_units, lot.existing_units);
    if (likely > 0) out.realistic[pid] = likely;
    if (r.status === "ok") {
      t.max += r.max_units ?? 0;
      t.local += r.local_units ?? 0;
      t.net += r.net_new_units ?? 0;
      if (!(mask[pid] & LAND)) t.specialLandNet += r.net_new_units ?? 0;
      t.existing += lot.existing_units ?? 0;
      if (likely >= 0) {
        t.realistic += likely;
        t.likelyLots++;
      }
    }
  }
}

export function runScenario(data: ParcelData, rules: RulesFile, scenario: Scenario): Results {
  const out = emptyResults(data.count);
  for (const _ of scenarioSteps(data, rules, scenario, out)) void _;
  return out;
}

/** runScenario in short bursts, so the page never freezes. Null if `stillWanted` turned false. */
export async function runScenarioInSteps(
  data: ParcelData, rules: RulesFile, scenario: Scenario, stillWanted: () => boolean,
): Promise<Results | null> {
  const out = emptyResults(data.count);
  let burstStart = performance.now();
  for (const _ of scenarioSteps(data, rules, scenario, out)) {
    void _;
    if (performance.now() - burstStart > 12) {
      await new Promise((resolve) => setTimeout(resolve));
      if (!stillWanted()) return null;
      burstStart = performance.now();
    }
  }
  return out;
}
