// Entry point: load the data, draw the map, wire up the controls.
//
// Flow: the URL hash -> a Scenario -> run the engine on every lot ->
// headline numbers, legend and map colors. Changing a lever updates the
// hash, so the address bar always holds a shareable link to what you see.

import maplibregl from "maplibre-gl";

import "./style.css";
import { BINDING_LABELS } from "./colors";
import { type ParcelData, loadJson } from "./data";
import { type Results, buildLotInputs, runScenario } from "./engine/run";
import { BASELINE, type Scenario, isBaseline } from "./engine/scenario";
import type { RulesFile } from "./engine/types";
import { renderLegend } from "./legend";
import { createMap, currentTheme, type View } from "./map";
import { LEVERS, scenarioFromHash, scenarioToHash } from "./url";

const CITY = "pasadena";
// import.meta.env.BASE_URL is "./" (see vite.config.ts), so these work
// whether the site is served at / or at /<repo-name>/ on GitHub Pages.
const DATA_DIR = `${import.meta.env.BASE_URL}data/${CITY}`;
const TILES_URL = new URL(`${DATA_DIR}/parcels.pmtiles`, window.location.href).href;

const PRESETS: Record<string, Partial<Scenario>> = {
  fourplex: { sf_units_per_lot: 4 },
  parking: { parking_per_unit: 0, parking_exempt_radius_ft: 5280 },
  transit: { transit_radius_ft: 2640, transit_extra_stories: 2, transit_density_multiplier: 2 },
  reset: {},
};

const fmt = new Intl.NumberFormat("en-US");
const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;

// --- Levers form <-> Scenario --------------------------------------------------

const form = () => $<HTMLFormElement>("levers");

function readForm(): Scenario {
  const s: Scenario = { ...BASELINE };
  for (const lever of Object.keys(LEVERS) as (keyof Scenario)[]) {
    const el = form().elements.namedItem(lever) as HTMLInputElement | HTMLSelectElement;
    const value =
      el instanceof HTMLInputElement && el.type === "checkbox" ? el.checked : el.value === "" ? null : Number(el.value);
    (s as unknown as Record<string, unknown>)[lever] = value;
  }
  return s;
}

function writeForm(s: Scenario) {
  for (const lever of Object.keys(LEVERS) as (keyof Scenario)[]) {
    const el = form().elements.namedItem(lever) as HTMLInputElement | HTMLSelectElement;
    const v = s[lever];
    if (el instanceof HTMLInputElement && el.type === "checkbox") el.checked = Boolean(v);
    else el.value = v === null ? "" : String(v);
    // Mark levers that differ from today's rules, so changes are easy to spot.
    el.classList.toggle("changed", v !== BASELINE[lever]);
  }
}

// --- Headline and popup ------------------------------------------------------------

function showHeadline(data: ParcelData, scenario: Scenario, now: Results, today: Results) {
  $("stat-existing").textContent = fmt.format(today.totals.existing);
  $("stat-single").textContent = `${Math.round(data.headline.single_home_land_share * 100)}%`;
  const reform = !isBaseline(scenario);
  $("stat-max-label").textContent = reform ? "Legal maximum under this scenario" : "Legal maximum under today's rules";
  $("stat-max").textContent = fmt.format(now.totals.max);
  const note = $("stat-max-note");
  if (reform) {
    const diff = now.totals.max - today.totals.max;
    note.innerHTML = `<span class="up">${diff >= 0 ? "+" : "−"}${fmt.format(Math.abs(diff))}</span> vs. ${fmt.format(today.totals.max)} under today's rules`;
  } else {
    note.textContent = `${fmt.format(today.totals.local)} under city zoning alone, the rest from state law`;
  }
  const state = $("scenario-state");
  state.textContent = reform ? "Scenario active" : "Today's rules";
  state.classList.toggle("active", reform);
  $("not-modeled-note").textContent =
    `${fmt.format(data.headline.lots_not_modeled)} lots in specific plans and planned developments are not modeled yet (shown in light gray).`;
}

function popupHtml(data: ParcelData, pid: number, now: Results, today: Results, reform: boolean): string {
  const c = data.columns;
  const zone = c.zone[pid] >= 0 ? data.codes.zone[c.zone[pid]] : "unknown";
  const n = (v: number | null) => (v === null ? "unknown" : fmt.format(v));
  const header = `<h3>Lot ${c.parcel_id[pid]}</h3><div>Zone <strong>${zone}</strong> · ${fmt.format(c.lot_area_sqft[pid])} sq ft</div>`;
  if (now.binding[pid] < 0) {
    return `<div class="popup">${header}<p class="limit">This zone isn't modeled yet (specific plan or planned development).</p></div>`;
  }
  const limit = (r: Results) => BINDING_LABELS[data.codes.binding[r.binding[pid]]] ?? "";
  const rows = [
    `<dt>Homes today</dt><dd>${n(c.existing_units[pid])}</dd>`,
    `<dt>Allowed, today's rules</dt><dd><strong>${n(today.max[pid])}</strong></dd>`,
  ];
  if (reform) rows.push(`<dt class="scenario-col">Allowed, this scenario</dt><dd class="scenario-col"><strong>${n(now.max[pid])}</strong></dd>`);
  rows.push(`<dt>New homes possible${reform ? " (scenario)" : ""}</dt><dd>${n(now.net[pid])}</dd>`);
  const limits = reform
    ? `<div class="limit">Limit today: ${limit(today)}</div><div class="limit scenario-col">Limit under scenario: ${limit(now)}</div>`
    : `<div class="limit">Limit: ${limit(today)}</div>`;
  return `<div class="popup">${header}<dl>${rows.join("")}</dl>${limits}</div>`;
}

// --- Main ----------------------------------------------------------------------------

async function main() {
  const status = $("status");
  try {
    const [data, rules] = await Promise.all([
      loadJson<ParcelData>(`${DATA_DIR}/parcels.json`),
      loadJson<RulesFile>(`${DATA_DIR}/rules.json`),
    ]);
    const inputs = buildLotInputs(data);
    const today = runScenario(data, inputs, rules, BASELINE);
    let scenario = scenarioFromHash(window.location.hash);
    let now = isBaseline(scenario) ? today : runScenario(data, inputs, rules, scenario);

    writeForm(scenario);
    showHeadline(data, scenario, now, today);

    const controller = await createMap("map", data, TILES_URL);
    status.textContent = "";
    controller.setResults(now, today);

    // Highlight menu: one option per binding constraint.
    const select = $<HTMLSelectElement>("highlight");
    data.codes.binding.forEach((name, code) => {
      const opt = document.createElement("option");
      opt.value = String(code);
      opt.textContent = BINDING_LABELS[name] ?? name;
      select.append(opt);
    });

    const legend = $("legend");
    // Start from whichever option is checked: browsers restore form state
    // on reload, so it isn't always the default.
    let view: View =
      (document.querySelector<HTMLInputElement>('input[name="view"]:checked')?.value as View) ?? "max";
    const redraw = () => {
      const code = view === "binding" && select.value !== "" ? Number(select.value) : null;
      controller.setView(view, code);
      $("highlight-wrap").hidden = view !== "binding";
      renderLegend(legend, data, view, now, today, currentTheme(), code === null ? null : data.codes.binding[code]);
    };

    const applyScenario = (next: Scenario, updateUrl = true) => {
      scenario = next;
      const t0 = performance.now();
      now = isBaseline(scenario) ? today : runScenario(data, inputs, rules, scenario);
      writeForm(scenario);
      showHeadline(data, scenario, now, today);
      controller.setResults(now, today);
      redraw();
      popup.remove();
      if (updateUrl) history.replaceState(null, "", scenarioToHash(scenario) || window.location.pathname);
      console.debug(`Scenario recomputed in ${Math.round(performance.now() - t0)} ms`);
    };

    form().addEventListener("change", () => applyScenario(readForm()));
    document.querySelectorAll<HTMLButtonElement>("[data-preset]").forEach((btn) =>
      btn.addEventListener("click", () => applyScenario({ ...BASELINE, ...PRESETS[btn.dataset.preset as string] })),
    );
    // Someone pasting a different scenario link into the same tab.
    window.addEventListener("hashchange", () => applyScenario(scenarioFromHash(window.location.hash), false));

    $("share").addEventListener("click", async () => {
      const shareStatus = $("share-status");
      try {
        await navigator.clipboard.writeText(window.location.href);
        shareStatus.textContent = "Link copied.";
      } catch {
        shareStatus.textContent = "Copy the address from your browser's address bar.";
      }
    });

    document.querySelectorAll<HTMLInputElement>('input[name="view"]').forEach((input) =>
      input.addEventListener("change", () => {
        view = input.value as View;
        redraw();
      }),
    );
    select.addEventListener("change", redraw);
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", redraw);
    redraw();

    const popup = new maplibregl.Popup({ maxWidth: "300px", focusAfterOpen: true });
    controller.onLotClick((pid, lngLat) => {
      popup.setLngLat(lngLat).setHTML(popupHtml(data, pid, now, today, !isBaseline(scenario))).addTo(controller.map);
      // On phones the map is short, so move the clicked lot near the top to
      // leave room for the popup below it.
      if (window.matchMedia("(max-width: 760px)").matches) {
        const height = controller.map.getContainer().clientHeight;
        controller.map.easeTo({ center: lngLat, offset: [0, -(height / 2 - 40)], duration: 300 });
      }
    });

    // Sanity check in development: the browser's "today" must equal the
    // pipeline's numbers in parcels.json (the golden test checks a sample;
    // this checks every lot).
    if (import.meta.env.DEV) {
      const bad = data.columns.max_units.findIndex((v, pid) => v !== today.max[pid]);
      if (bad >= 0) console.error(`Browser engine disagrees with pipeline on lot ${bad}`);
      else console.debug("Browser engine matches pipeline on all lots");
    }
  } catch (err) {
    status.textContent = `Couldn't load the map data. ${(err as Error).message}`;
    console.error(err);
  }
}

main();
