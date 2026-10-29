// The legend: every color with a text label and how many lots have it, so
// color is never the only way to read the map.

import {
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
import { bindingOf, type ParcelData } from "./data";
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
  data: ParcelData,
  classes: ValueClass[],
  theme: Theme,
  zeroLabel: string,
): Row[] {
  const ramp = rampFor(theme);
  const counts = new Array(classes.length).fill(0);
  let zero = 0;
  let notModeled = 0;
  for (let pid = 0; pid < data.count; pid++) {
    const v = values[pid];
    if (data.columns.binding[pid] < 0 || v === null) notModeled++;
    else if (v === 0) zero++;
    else counts[classes.findIndex((c) => v >= c.min && (c.max === null || v <= c.max))]++;
  }
  return [
    ...classes.map((c, i) => ({ color: ramp[i], label: c.label, count: counts[i] })).reverse(),
    { color: NEUTRAL[theme].zero, label: zeroLabel, count: zero },
    { color: NEUTRAL[theme].notModeled, label: "Not modeled yet (specific plans, planned developments)", count: notModeled },
  ];
}

function bindingRows(data: ParcelData, theme: Theme, highlight: string | null): Row[] {
  const tally: Record<string, number> = {};
  let notModeled = 0;
  for (let pid = 0; pid < data.count; pid++) {
    const b = bindingOf(data, pid);
    if (b === null) notModeled++;
    else tally[b] = (tally[b] ?? 0) + 1;
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

export function renderLegend(el: HTMLElement, data: ParcelData, view: View, theme: Theme, highlight: string | null) {
  const c = data.columns;
  const rows =
    view === "max"
      ? classRows(c.max_units, data, MAX_UNITS_CLASSES, theme, "0: housing not allowed or doesn't fit")
      : view === "net"
        ? classRows(c.net_new_units, data, NET_NEW_CLASSES, theme, "0: no room for more homes")
        : bindingRows(data, theme, highlight);

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
