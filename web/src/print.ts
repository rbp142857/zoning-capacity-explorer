// One-page printable summary.
//
// When the user prints (button or Ctrl/Cmd+P), we fill a hidden section with
// a plain summary: the scenario in words, citywide totals, the two
// breakdowns as tables, a snapshot of the map, the link back, and the
// disclaimer. Print CSS (style.css) hides the interactive page and shows it.

import type { ChartRow } from "./charts";

const fmt = new Intl.NumberFormat("en-US");

function esc(s: string): string {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c] as string);
}

/** Each changed lever as "Label: chosen option", read from the form itself. */
export function describeScenario(form: HTMLFormElement): string[] {
  const out: string[] = [];
  form.querySelectorAll<HTMLSelectElement | HTMLInputElement>(".changed").forEach((el) => {
    const labelEl = el.closest("label");
    // A select's label text comes before the select; a checkbox's after it.
    const label = (
      el instanceof HTMLInputElement ? labelEl?.textContent : labelEl?.childNodes[0]?.textContent
    )?.trim() ?? el.name;
    const value = el instanceof HTMLSelectElement ? el.selectedOptions[0]?.textContent ?? el.value : "Yes";
    const group = el.closest("fieldset")?.querySelector("legend")?.textContent;
    out.push(`${group ? `${group}: ` : ""}${label} ${el instanceof HTMLSelectElement ? `→ ${value}` : ""}`.trim());
  });
  return out;
}

function table(title: string, rows: ChartRow[], reform: boolean): string {
  const body = rows
    .map(
      (r) =>
        `<tr><th scope="row">${esc(r.label)}</th><td>${fmt.format(r.today)}</td>${
          reform ? `<td>${fmt.format(r.scenario)}</td><td>${r.scenario - r.today >= 0 ? "+" : "−"}${fmt.format(Math.abs(r.scenario - r.today))}</td>` : ""
        }</tr>`,
    )
    .join("");
  return `<h3>${esc(title)}</h3><table><thead><tr><th></th><th>Today's rules</th>${
    reform ? "<th>This scenario</th><th>Change</th>" : ""
  }</tr></thead><tbody>${body}</tbody></table>`;
}

export interface PrintData {
  city: string;
  reform: boolean;
  levers: string[];
  existing: number;
  todayMax: number;
  scenarioMax: number;
  todayNet: number;
  scenarioNet: number;
  byDistrict: ChartRow[];
  byTransit: ChartRow[];
  mapImage: string | null;
  url: string;
  generatedAt: string;
}

export function renderPrintSummary(el: HTMLElement, d: PrintData) {
  const scenarioText = d.reform
    ? `<p><strong>Reform scenario:</strong></p><ul>${d.levers.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>`
    : "<p>Today's rules (no reform scenario applied).</p>";
  const totals = d.reform
    ? `<tr><th>Legal maximum (homes)</th><td>${fmt.format(d.todayMax)}</td><td>${fmt.format(d.scenarioMax)}</td></tr>
       <tr><th>New homes possible</th><td>${fmt.format(d.todayNet)}</td><td>${fmt.format(d.scenarioNet)}</td></tr>`
    : `<tr><th>Legal maximum (homes)</th><td>${fmt.format(d.todayMax)}</td></tr>
       <tr><th>New homes possible</th><td>${fmt.format(d.todayNet)}</td></tr>`;
  el.innerHTML = `
    <h1>${esc(d.city)}: zoning capacity summary</h1>
    <p class="print-disclaimer"><strong>Estimate for research and advocacy, not legal or zoning advice.</strong>
      Always confirm with the City of Pasadena. Numbers are theoretical maximums if lots were rebuilt, not predictions.</p>
    ${scenarioText}
    <table class="print-totals"><thead><tr><th></th><th>Today's rules</th>${d.reform ? "<th>This scenario</th>" : ""}</tr></thead>
      <tbody><tr><th>Homes on modeled lots today</th><td>${fmt.format(d.existing)}</td>${d.reform ? `<td>${fmt.format(d.existing)}</td>` : ""}</tr>${totals}</tbody></table>
    ${d.mapImage ? `<img class="print-map" src="${d.mapImage}" alt="Map of the current view">` : ""}
    <div class="print-tables">
      ${table("New homes possible by council district", d.byDistrict, d.reform)}
      ${table("New homes possible by distance to a major transit stop", d.byTransit, d.reform)}
    </div>
    <p class="print-foot">Interactive version and method: ${esc(d.url)}<br>
      Data: LA County Assessor parcels, City of Pasadena zoning (Municode, Sep 2, 2026), SCAG major transit stops.
      Specific-plan and planned-development lots are not modeled yet. Generated ${esc(d.generatedAt)}.</p>`;
}
