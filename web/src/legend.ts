// The legend: every color with a text label and how many lots have it, so
// color is never the only way to read the map.

import {
  ADDED_CLASSES,
  BINDING_GROUPS,
  BINDING_LABELS,
  CATEGORICAL,
  MAX_UNITS_CLASSES,
  NET_NEW_CLASSES,
  NEUTRAL,
  rampFor,
  type Theme,
  type ValueClass,
} from "./colors";
import type { ParcelData } from "./data";
import type { Results } from "./engine/run";
import type { View } from "./map";

interface Row {
  color: string;
  label: string;
  count: number;
  sub?: string;
}

const fmt = new Intl.NumberFormat("en-US");

function classRows(
  values: (number | null)[],
  modeled: (pid: number) => boolean,
  count: number,
  classes: ValueClass[],
  theme: Theme,
  zeroLabel: string,
): Row[] {
  const ramp = rampFor(theme);
  const counts = new Array(classes.length).fill(0);
  let zero = 0;
  let notModeled = 0;
  for (let pid = 0; pid < count; pid++) {
    const v = values[pid];
    if (!modeled(pid) || v === null) notModeled++;
    else if (v === 0) zero++;
    else counts[classes.findIndex((c) => v >= c.min && (c.max === null || v <= c.max))]++;
  }
  return [
    ...classes.map((c, i) => ({ color: ramp[i], label: c.label, count: counts[i] })).reverse(),
    { color: NEUTRAL[theme].zero, label: zeroLabel, count: zero },
    { color: NEUTRAL[theme].notModeled, label: "Not modeled yet (specific plans, planned developments)", count: notModeled },
  ];
}

function bindingRows(data: ParcelData, results: Results, theme: Theme, highlight: string | null): Row[] {
  const tally: Record<string, number> = {};
  let notModeled = 0;
  for (let pid = 0; pid < data.count; pid++) {
    const code = results.binding[pid];
    if (code < 0) notModeled++;
    else tally[data.codes.binding[code]] = (tally[data.codes.binding[code]] ?? 0) + 1;
  }
  const nm = { color: NEUTRAL[theme].notModeled, label: "Not modeled yet", count: notModeled };
  if (highlight) {
    const others = Object.entries(tally).reduce((s, [k, v]) => (k === highlight ? s : s + v), 0);
    return [
      { color: CATEGORICAL[theme][0], label: BINDING_LABELS[highlight], count: tally[highlight] ?? 0 },
      { color: NEUTRAL[theme].zero, label: "Any other limit", count: others },
      nm,
    ];
  }
  return [
    ...BINDING_GROUPS.map((g) => ({
      color: g.slot === "zero" ? NEUTRAL[theme].zero : CATEGORICAL[theme][g.slot],
      label: g.label,
      count: g.members.reduce((s, m) => s + (tally[m] ?? 0), 0),
      sub:
        g.members.length > 1
          ? g.members.map((m) => `${BINDING_LABELS[m]}: ${fmt.format(tally[m] ?? 0)}`).join(" · ")
          : undefined,
    })),
    nm,
  ];
}

export function renderLegend(
  el: HTMLElement,
  data: ParcelData,
  view: View,
  scenario: Results,
  today: Results,
  theme: Theme,
  highlight: string | null,
) {
  const modeled = (pid: number) => scenario.binding[pid] >= 0;
  let rows: Row[];
  if (view === "max") {
    rows = classRows(scenario.max, modeled, data.count, MAX_UNITS_CLASSES, theme, "0: housing not allowed or doesn't fit");
  } else if (view === "net") {
    rows = classRows(scenario.net, modeled, data.count, NET_NEW_CLASSES, theme, "0: no room for more homes");
  } else if (view === "added") {
    const added = scenario.max.map((v, pid) => (v === null ? null : Math.max(0, v - (today.max[pid] ?? 0))));
    rows = classRows(added, modeled, data.count, ADDED_CLASSES, theme, "No change from today's rules");
  } else {
    rows = bindingRows(data, scenario, theme, highlight);
  }

  el.replaceChildren(
    ...rows.map((r) => {
      const li = document.createElement("li");
      const sw = document.createElement("span");
      sw.className = "swatch";
      sw.style.background = r.color;
      sw.setAttribute("aria-hidden", "true");
      const label = document.createElement("span");
      label.textContent = r.label;
      const count = document.createElement("span");
      count.className = "count";
      count.textContent = `${fmt.format(r.count)} lots`;
      li.append(sw, label, count);
      if (r.sub) {
        const sub = document.createElement("span");
        sub.className = "sub";
        sub.textContent = r.sub;
        li.append(sub);
      }
      return li;
    }),
  );
}
