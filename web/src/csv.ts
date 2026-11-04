// Lot-level results as a CSV file, for researchers and reporters.
//
// Parcel number, zone and capacity only. The site holds no owner names or mailing
// addresses, and this file adds nothing beyond what the map already shows.

import { type ParcelData, na, parcelId } from "./data";
import type { Results } from "./engine/run";
import { LAND } from "./engine/redevelop";

/** Quote a value if a comma, quote or line break would otherwise break the row. */
function cell(v: string | number | null): string {
  if (v === null) return "";
  const s = String(v);
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

/** The file as pieces, so the whole text never has to fit in one string. */
export function lotsCsvParts(data: ParcelData, today: Results, now: Results, url: string, reform: boolean): string[] {
  const c = data.columns;
  const head = ["parcel_id", "zone", "lot_area_sqft", "existing_homes", "modeled", "max_homes_today", "new_homes_today", "likely_new_homes_today", "special_land", "miles_to_major_transit"];
  if (reform) head.push("max_homes_scenario", "new_homes_scenario", "likely_new_homes_scenario");
  const parts: string[] = [];
  let rows = [
    `# Zoning Capacity Explorer. An estimate for research, not legal or zoning advice. Scenario: ${url.replace(/[\r\n]/g, "")}`,
    head.join(","),
  ];
  for (let pid = 0; pid < data.count; pid++) {
    const modeled = today.binding[pid] >= 0;
    const transit = na(c.dist_major_transit_ft[pid]);
    const row: (string | number | null)[] = [
      parcelId(data, pid),
      c.zone[pid] >= 0 ? data.codes.zone[c.zone[pid]] : null,
      c.lot_area_sqft[pid],
      na(c.existing_units[pid]),
      modeled ? 1 : 0,
      na(today.max[pid]),
      na(today.net[pid]),
      modeled ? today.realistic[pid] : null,
      c.redev_mask[pid] & LAND ? 0 : 1,
      transit === null ? null : Math.round((transit / 5280) * 100) / 100,
    ];
    if (reform) row.push(na(now.max[pid]), na(now.net[pid]), modeled ? now.realistic[pid] : null);
    rows.push(row.map(cell).join(","));
    if (rows.length >= 50000) {
      parts.push(`${rows.join("\n")}\n`);
      rows = [];
    }
  }
  if (rows.length) parts.push(`${rows.join("\n")}\n`);
  return parts;
}

export const lotsCsv = (data: ParcelData, today: Results, now: Results, url: string, reform: boolean) =>
  lotsCsvParts(data, today, now, url, reform).join("");

export function downloadText(filename: string, parts: string[]) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob(parts, { type: "text/csv" }));
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}
