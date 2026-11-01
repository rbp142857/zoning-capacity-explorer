// The lot details panel: what can be built on one lot, which rule limits it,
// and the code sections behind each number (for builders and planners).

import { BINDING_LABELS } from "./colors";
import type { ParcelData } from "./data";
import type { CapacityResult } from "./engine/capacity";
import { redevelopment } from "./engine/redevelop";
import type { LotInputs } from "./engine/run";
import { type Scenario, applyScenario, adjustForLot, capacityUnderScenario } from "./engine/scenario";
import type { RulesFile, Sourced, ZoneRules } from "./engine/types";
import { isBanded, isSideSetback, pick } from "./engine/types";

const fmt = new Intl.NumberFormat("en-US");

function esc(s: string): string {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c] as string);
}

const LIMIT_ROWS: [string, string][] = [
  ["density", "Homes per lot / per acre cap"],
  ["lot_area_per_unit", "Minimum land per home"],
  ["envelope", "Building size (setbacks, height, coverage, gardens, floor area)"],
  ["parking", "Room left after required parking"],
  ["state_adu", "State ADU law (house + ADU + junior ADU)"],
  ["state_sb9", "State law SB 9"],
];

/** A citation as a link, using the rule file's sources table. */
function cite(r: ZoneRules, v: Sourced<unknown> | null): string {
  if (!v) return "";
  const src = r.sources[v.source];
  if (!src) return "";
  const label = esc(src.section);
  const link = src.url ? `<a href="${esc(src.url)}" target="_blank" rel="noopener">${label}</a>` : label;
  const note = v.assumption ? `<span class="assumption">Our reading: ${esc(v.assumption)}</span>` : "";
  return `<span class="cite">${link}</span>${note}`;
}

function describeValue(v: unknown, area: number, width: number, distSf: number | null): string {
  if (isBanded(v)) {
    const b = pick(v, area, width, distSf);
    if (b.share !== null) {
      const parts = [`${Math.round(b.share * 100)}% of the lot`];
      if (b.plus_sqft) parts.push(`+ ${fmt.format(b.plus_sqft)} sq ft`);
      if (b.plus_sqft_per_unit) parts.push(`+ ${fmt.format(b.plus_sqft_per_unit)} sq ft per home`);
      if (b.at_least_sqft) parts.push(`(at least ${fmt.format(b.at_least_sqft)} sq ft)`);
      return parts.join(" ");
    }
    return b.value === null ? "no limit for this lot" : String(b.value);
  }
  if (isSideSetback(v)) return `${Math.round(v.pct_of_width * 100)}% of lot width (${v.min_ft}–${v.max_ft} ft)`;
  return String(v);
}

function rulesTable(r: ZoneRules, area: number, width: number, distSf: number | null): string {
  const rows: [string, Sourced<unknown> | null, string?][] = [
    ["Housing allowed", r.residential_allowed, r.residential_allowed.value ? "Yes" : "No"],
    ["Homes per lot", r.max_units_per_lot],
    ["Homes per acre", r.units_per_acre],
    ["Land per home (sq ft)", r.lot_area_per_unit_sqft],
    ["Front setback (ft)", r.setbacks.front_ft],
    ["Side setbacks (ft)", r.setbacks.side_ft],
    ["Rear setback (ft)", r.setbacks.rear_ft],
    ["Height (ft)", r.max_height_ft],
    ["Stories", r.max_stories],
    ["Lot coverage", r.lot_coverage],
    ["Floor area", r.max_floor_area],
    ["Floor area ratio", r.max_far],
    ["Garden / open space", r.min_open_space_share],
    ["Parking per home", r.parking_per_unit],
  ];
  // Where housing isn't allowed, the other standards don't matter here.
  const shown = r.residential_allowed.value ? rows : rows.slice(0, 1);
  return shown
    .filter(([, v]) => v !== null && v !== undefined)
    .map(([label, v, text]) => {
      const s = v as Sourced<unknown>;
      let shown = text ?? describeValue(s.value, area, width, distSf);
      if (label === "Lot coverage" || label === "Garden / open space") {
        if (typeof s.value === "number") shown = `${Math.round(s.value * 100)}% of the lot`;
      }
      const isScenario = s.source === "scenario";
      return `<tr${isScenario ? ' class="scenario-col"' : ""}><th scope="row">${label}</th><td>${esc(shown)}${
        isScenario ? " <em>(scenario)</em>" : ""
      }<br>${isScenario ? "" : cite(r, s)}</td></tr>`;
    })
    .join("");
}

function limitsTable(today: CapacityResult, now: CapacityResult, reform: boolean): string {
  const n = (v: number | null | undefined) => (v === null || v === undefined ? "–" : fmt.format(v));
  const mark = (r: CapacityResult, key: string) =>
    r.binding_constraint === key || r.binding_constraint === `state_law:${key.replace("state_", "")}` ? " binding" : "";
  return LIMIT_ROWS.filter(([k]) => k in today.limits || k in now.limits)
    .map(
      ([k, label]) =>
        `<tr><th scope="row">${label}</th><td class="${mark(today, k)}">${n(today.limits[k])}</td>${
          reform ? `<td class="scenario-col${mark(now, k)}">${n(now.limits[k])}</td>` : ""
        }</tr>`,
    )
    .join("");
}

const SCREEN_TEXT: Record<string, [string, string]> = {
  zoning_allows_too_little_more: ["Zoning allows at least twice the homes already there", "Zoning allows less than twice the homes already there"],
  building_too_new: ["Building is 50+ years old (or lot is vacant)", "Building is less than 50 years old"],
  building_worth_more_than_land: ["Building assessed at less than the land", "Building assessed at more than the land (or value unknown)"],
  condo_many_owners: ["Not a condo", "Condo (many owners)"],
  historic_district: ["Not in a landmark district", "In a landmark (historic) district"],
  single_family_zone: ["Not in a single-family zone", "In a single-family zone (small-scale infill is counted separately)"],
};

function redevSection(rules: RulesFile, mask: number, r: CapacityResult, existing: number | null, reform: boolean): string {
  const redev = redevelopment(rules.redevelopment, mask, r.local_units, existing);
  const items = Object.entries(SCREEN_TEXT)
    .map(([code, [pass, fail]]) => {
      const failed = redev.failed.includes(code);
      return `<li class="${failed ? "fail" : "pass"}"><span aria-hidden="true">${failed ? "✗" : "✓"}</span>
        <span class="visually-hidden">${failed ? "Fails" : "Passes"}: </span>${failed ? fail : pass}</li>`;
    })
    .join("");
  const verdict = redev.likely
    ? `Likely to redevelop${reform ? " under this scenario" : ""}: counts ${fmt.format(redev.realistic_new_units)} new homes in the realistic estimate.`
    : `Not likely to redevelop${reform ? " under this scenario" : ""}.`;
  return `<h3>Likely to redevelop?</h3><p>${verdict}</p><ul class="screens">${items}</ul>`;
}

export function renderLotDetails(
  el: HTMLElement,
  pid: number,
  data: ParcelData,
  inputs: LotInputs,
  rules: RulesFile,
  scenario: Scenario,
  reform: boolean,
  todayScenario: Scenario,
) {
  const c = data.columns;
  const lot = inputs.lots[pid];
  const zone = inputs.zones[pid];
  const zoneCode = c.zone[pid] >= 0 ? data.codes.zone[c.zone[pid]] : "unknown";
  const head = `<h2 id="details-title">Lot ${esc(c.parcel_id[pid])}</h2>
    <p class="details-meta">Zone <strong>${esc(zoneCode)}</strong> · ${fmt.format(lot.area_sqft)} sq ft
    (about ${Math.round(lot.width_ft)} × ${Math.round(lot.depth_ft)} ft) ·
    ${lot.dist_major_transit_ft === null ? "transit distance unknown" : `${fmt.format(lot.dist_major_transit_ft)} ft from a major transit stop`}</p>`;

  if (zone === null) {
    el.innerHTML = `${head}<p>This zone isn't modeled yet. It's in a specific plan or planned development with its own rules; see METHODOLOGY.md.</p>`;
    return;
  }

  const run = (s: Scenario) => {
    const [zr, st] = applyScenario(rules.zones, rules.state, s);
    return { result: capacityUnderScenario(zone, lot, rules.assumptions, zr, st, s), rules: adjustForLot(zr[zone], lot, s) };
  };
  const today = run(todayScenario);
  const now = reform ? run(scenario) : today;
  const label = (r: CapacityResult) => BINDING_LABELS[r.binding_constraint ?? ""] ?? "–";
  const n = (v: number | null) => (v === null ? "unknown" : fmt.format(v));

  const flags = [...new Set([...today.result.flags, ...now.result.flags])];
  const flagText: Record<string, string> = {
    substandard_lot_area: "Smaller than today's minimum for new lots (an existing lot can still be built on).",
    substandard_lot_width: "Narrower than today's minimum for new lots.",
    sb9_excluded_historic_district: "In a landmark (historic) district, where SB 9 doesn't apply.",
    sb9_lot_too_small: "Too small for SB 9's two homes.",
    sb9_excluded_by_city: "The city's code bars SB 9 homes in this zone (we follow the city; see the rule file).",
  };

  el.innerHTML = `${head}
    <dl class="details-summary">
      <div><dt>Homes today</dt><dd>${n(lot.existing_units)}</dd></div>
      <div><dt>Allowed, today's rules</dt><dd>${n(today.result.max_units)}</dd></div>
      ${reform ? `<div class="scenario-col"><dt>Allowed, this scenario</dt><dd>${n(now.result.max_units)}</dd></div>` : ""}
    </dl>
    <p><strong>What limits it${reform ? " today" : ""}:</strong> ${label(today.result)}</p>
    ${reform ? `<p class="scenario-col"><strong>Under this scenario:</strong> ${label(now.result)}</p>` : ""}
    ${
      limitsTable(today.result, now.result, reform)
        ? `<h3>Each limit, in homes</h3>
    <table class="details-table">
      <thead><tr><th scope="col">Limit</th><th scope="col">Today</th>${reform ? '<th scope="col">Scenario</th>' : ""}</tr></thead>
      <tbody>${limitsTable(today.result, now.result, reform)}</tbody>
    </table>
    <p class="fineprint">The lowest local limit is the city's answer; state law can then allow more. The binding limit is in bold.
    ${today.result.state_laws_applied.includes("ab2097") ? "No parking minimum here (within ½ mile of a major transit stop, AB 2097)." : ""}</p>`
        : ""
    }
    ${flags.length ? `<ul class="details-flags">${flags.map((f) => `<li>${esc(flagText[f] ?? f)}</li>`).join("")}</ul>` : ""}
    ${redevSection(rules, data.columns.redev_mask[pid], reform ? now.result : today.result, lot.existing_units, reform)}
    <h3>Rules that apply (${esc(now.rules.name)})</h3>
    <table class="details-table rules">${rulesTable(now.rules, lot.area_sqft, lot.width_ft, lot.dist_single_family_ft)}</table>`;
}
