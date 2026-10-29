// Totals by council district and by distance to transit, for the charts and
// the printable summary. Only modeled lots count (like the headline).

import type { ChartRow } from "./charts";
import type { ParcelData } from "./data";
import type { Results } from "./engine/run";

export const TRANSIT_BANDS = [
  { label: "< ¼ mile", maxFt: 1320 },
  { label: "¼–½ mile", maxFt: 2640 },
  { label: "½–1 mile", maxFt: 5280 },
  { label: "> 1 mile", maxFt: Infinity },
];

type Pick = (r: Results, pid: number) => number;

/** Sum a per-lot value into groups (group index per lot, -1 = skip). */
function groupSums(data: ParcelData, groupOf: (pid: number) => number, labels: string[], today: Results, now: Results, value: Pick): ChartRow[] {
  const rows = labels.map((label) => ({ label, today: 0, scenario: 0 }));
  for (let pid = 0; pid < data.count; pid++) {
    if (today.binding[pid] < 0) continue; // not modeled
    const g = groupOf(pid);
    if (g < 0) continue;
    rows[g].today += value(today, pid);
    rows[g].scenario += value(now, pid);
  }
  return rows;
}

export const netNew: Pick = (r, pid) => r.net[pid] ?? 0;

export function byDistrict(data: ParcelData, today: Results, now: Results, value: Pick = netNew): ChartRow[] {
  return groupSums(data, (pid) => data.columns.district[pid], data.codes.district, today, now, value);
}

export function byTransitDistance(data: ParcelData, today: Results, now: Results, value: Pick = netNew): ChartRow[] {
  const groupOf = (pid: number) => {
    const d = data.columns.dist_major_transit_ft[pid];
    return d === null ? -1 : TRANSIT_BANDS.findIndex((b) => d < b.maxFt);
  };
  return groupSums(data, groupOf, TRANSIT_BANDS.map((b) => b.label), today, now, value);
}
