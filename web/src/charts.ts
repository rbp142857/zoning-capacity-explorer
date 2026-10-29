// Small horizontal bar charts, drawn as plain SVG (no chart library).
//
// Design rules (see LEARNING.md -> "Accessible charts"):
// - One axis, bars start at zero, thin bars with a small gap between them.
// - "Today" and "this scenario" are two series: blue and orange, the first
//   two slots of the validated palette. With no scenario, only "today".
// - A legend whenever there are two series, plus a value label at each bar's end.
// - Every bar group can be hovered or focused with the keyboard to show a
//   tooltip, and each chart has a "Show as table" view.

import { CATEGORICAL, type Theme } from "./colors";

export interface ChartRow {
  label: string;
  today: number;
  scenario: number;
}

export interface ChartSpec {
  title: string;
  valueLabel: string; // e.g. "new homes possible"
  rows: ChartRow[];
  showScenario: boolean;
}

const fmt = new Intl.NumberFormat("en-US");
const BAR_H = 12;
const BAR_GAP = 2; // surface gap between the two bars of a group
const GROUP_GAP = 12;
const LABEL_W = 92; // space for category labels on the left
const VALUE_W = 58; // space for value labels on the right

function esc(s: string): string {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c] as string);
}

/** A bar with 4px rounded corners on its data end only (the right side). */
function barPath(x: number, y: number, w: number, h: number): string {
  if (w <= 0) return "";
  const r = Math.min(4, w, h / 2);
  return `M${x},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h - r}Q${x + w},${y + h} ${x + w - r},${y + h}H${x}Z`;
}

function describe(row: ChartRow, spec: ChartSpec): string {
  if (!spec.showScenario) return `${row.label}: ${fmt.format(row.today)} ${spec.valueLabel}`;
  const diff = row.scenario - row.today;
  const sign = diff >= 0 ? "+" : "−";
  return `${row.label}: ${fmt.format(row.today)} today, ${fmt.format(row.scenario)} under this scenario (${sign}${fmt.format(Math.abs(diff))})`;
}

export function renderBarChart(el: HTMLElement, spec: ChartSpec, theme: Theme, width: number) {
  const [cToday, cScenario] = CATEGORICAL[theme];
  const series = spec.showScenario ? 2 : 1;
  const groupH = series * BAR_H + (series - 1) * BAR_GAP;
  const height = spec.rows.length * (groupH + GROUP_GAP);
  const plotW = Math.max(60, width - LABEL_W - VALUE_W);
  const maxValue = Math.max(1, ...spec.rows.flatMap((r) => (spec.showScenario ? [r.today, r.scenario] : [r.today])));
  const scale = (v: number) => (v / maxValue) * plotW;

  const groups = spec.rows
    .map((row, i) => {
      const y0 = i * (groupH + GROUP_GAP);
      const bars: string[] = [];
      const values = spec.showScenario ? [row.today, row.scenario] : [row.today];
      values.forEach((v, j) => {
        const y = y0 + j * (BAR_H + BAR_GAP);
        bars.push(`<path d="${barPath(LABEL_W, y, scale(v), BAR_H)}" fill="${j === 0 ? cToday : cScenario}"/>`);
        bars.push(
          `<text class="chart-value" x="${LABEL_W + scale(v) + 4}" y="${y + BAR_H - 2}">${fmt.format(v)}</text>`,
        );
      });
      const text = describe(row, spec);
      return `<g class="chart-group" tabindex="0" role="listitem" aria-label="${esc(text)}" data-tip="${esc(text)}">
        <rect class="chart-hit" x="0" y="${y0 - GROUP_GAP / 2}" width="${width}" height="${groupH + GROUP_GAP}"/>
        <text class="chart-label" x="${LABEL_W - 6}" y="${y0 + groupH / 2 + 4}" text-anchor="end">${esc(row.label)}</text>
        ${bars.join("")}
      </g>`;
    })
    .join("");

  const legend = spec.showScenario
    ? `<div class="chart-legend" aria-hidden="true">
        <span><i style="background:${cToday}"></i>Today's rules</span>
        <span><i style="background:${cScenario}"></i>This scenario</span>
      </div>`
    : "";

  const tableRows = spec.rows
    .map(
      (r) =>
        `<tr><th scope="row">${esc(r.label)}</th><td>${fmt.format(r.today)}</td>${
          spec.showScenario ? `<td>${fmt.format(r.scenario)}</td><td>${r.scenario - r.today >= 0 ? "+" : "−"}${fmt.format(Math.abs(r.scenario - r.today))}</td>` : ""
        }</tr>`,
    )
    .join("");

  el.innerHTML = `
    <h3 class="chart-title">${esc(spec.title)}</h3>
    ${legend}
    <div class="chart-body">
      <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="list" aria-label="${esc(spec.title)}">${groups}</svg>
      <div class="chart-tip" role="tooltip" hidden></div>
    </div>
    <details class="chart-table">
      <summary>Show as table</summary>
      <table>
        <thead><tr><th scope="col"></th><th scope="col">Today's rules</th>${
          spec.showScenario ? '<th scope="col">This scenario</th><th scope="col">Change</th>' : ""
        }</tr></thead>
        <tbody>${tableRows}</tbody>
      </table>
    </details>`;

  // Tooltip on hover and keyboard focus.
  const tip = el.querySelector<HTMLDivElement>(".chart-tip") as HTMLDivElement;
  const body = el.querySelector<HTMLDivElement>(".chart-body") as HTMLDivElement;
  el.querySelectorAll<SVGGElement>(".chart-group").forEach((g) => {
    const show = () => {
      tip.textContent = g.dataset.tip ?? "";
      tip.hidden = false;
      const gBox = g.getBoundingClientRect();
      const bBox = body.getBoundingClientRect();
      tip.style.top = `${gBox.bottom - bBox.top + 2}px`;
    };
    const hide = () => (tip.hidden = true);
    g.addEventListener("mouseenter", show);
    g.addEventListener("focus", show);
    g.addEventListener("mouseleave", hide);
    g.addEventListener("blur", hide);
  });
}
