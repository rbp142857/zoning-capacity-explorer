// Scenarios <-> URL, so a scenario can be shared as a link.
//
// Only levers that differ from today's rules are written, with short keys:
//   #v=1&sf=4&pk=0&pr=5280
// Unknown keys are ignored and bad values fall back to today's rules, so an
// old or hand-edited link never breaks the page. `v` is the format version:
// if the lever set ever changes incompatibly, bump it and translate old links.

import { BASELINE, type Scenario } from "./engine/scenario";

const VERSION = "1";

// Short URL key for each lever, and the values the UI offers. Only these
// values are accepted from a URL (anything else is treated as "today").
type Spec = { key: string; allowed: (number | boolean | null)[] };
export const LEVERS: Record<keyof Scenario, Spec> = {
  sf_units_per_lot: { key: "sf", allowed: [null, 2, 3, 4, 6] },
  sf_min_lot_sqft: { key: "ml", allowed: [null, 5000, 3000, 2500, 1500] },
  parking_per_unit: { key: "pk", allowed: [null, 1, 0.5, 0] },
  parking_exempt_radius_ft: { key: "pr", allowed: [2640, 3960, 5280] },
  transit_radius_ft: { key: "tr", allowed: [1320, 2640, 5280] },
  transit_extra_stories: { key: "ts", allowed: [0, 1, 2, 3, 4] },
  transit_density_multiplier: { key: "td", allowed: [1, 1.5, 2, 3] },
  housing_in_cg: { key: "cg", allowed: [false, true] },
  adu_units_added: { key: "adu", allowed: [null, 3, 4] },
};

function encodeValue(v: number | boolean | null): string {
  return typeof v === "boolean" ? (v ? "1" : "0") : String(v);
}

export function scenarioToHash(s: Scenario): string {
  const parts = [`v=${VERSION}`];
  for (const [lever, spec] of Object.entries(LEVERS) as [keyof Scenario, Spec][]) {
    if (s[lever] !== BASELINE[lever]) parts.push(`${spec.key}=${encodeValue(s[lever])}`);
  }
  return parts.length > 1 ? `#${parts.join("&")}` : "";
}

export function scenarioFromHash(hash: string): Scenario {
  const params = new URLSearchParams(hash.replace(/^#/, ""));
  const s: Scenario = { ...BASELINE };
  if (params.get("v") !== VERSION) return s;
  for (const [lever, spec] of Object.entries(LEVERS) as [keyof Scenario, Spec][]) {
    const raw = params.get(spec.key);
    if (raw === null) continue;
    const match = spec.allowed.find((v) => encodeValue(v) === raw);
    if (match !== undefined) (s as unknown as Record<string, unknown>)[lever] = match;
  }
  return s;
}
