// Entry point: load the data, draw the map, wire up the controls.
//
// Flow: the URL hash -> a Scenario -> run the engine on every lot ->
// headline numbers, legend and map colors. Changing a lever updates the
// hash, so the address bar always holds a shareable link to what you see.

import maplibregl from "maplibre-gl";

import "./style.css";
import { renderBarChart } from "./charts";
import { BINDING_LABELS } from "./colors";
import { type ParcelData, loadJson } from "./data";
import { type Results, buildLotInputs, runScenario } from "./engine/run";
import { BASELINE, type Scenario, isBaseline } from "./engine/scenario";
import type { RulesFile } from "./engine/types";
import { renderLotDetails } from "./details";
import { renderLegend } from "./legend";
import { createMap, currentTheme, type View } from "./map";
import { describeScenario, renderPrintSummary } from "./print";
import { type AddressIndex, setupSearch } from "./search";
import { byDistrict, byTransitDistance, netNew, realisticNew } from "./summary";
import { LEVERS, scenarioFromHash, scenarioToHash } from "./url";

// import.meta.env.BASE_URL is "./" (see vite.config.ts), so these work
// whether the site is served at / or at /<repo-name>/ on GitHub Pages.
const DATA_ROOT = `${import.meta.env.BASE_URL}data`;

interface CityInfo {
  id: string;
  name: string;
  center: [number, number];
  zoom: number;
}

// Links shared before more cities were added have no ?city=, and were made
// for Pasadena, so it stays the default.
const DEFAULT_CITY = "pasadena";

/** The city comes from ?city=... in the address. */
function pickCity(cities: CityInfo[]): CityInfo {
  const wanted = new URLSearchParams(window.location.search).get("city") ?? DEFAULT_CITY;
  return cities.find((c) => c.id === wanted) ?? cities[0];
}

function setupCityPicker(cities: CityInfo[], current: CityInfo) {
  const select = $<HTMLSelectElement>("city");
  for (const c of cities) {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.name.split(",")[0];
    select.append(opt);
  }
  select.value = current.id;
  // Switching city reloads the page with ?city=..., keeping the scenario
  // (the #hash), since the reform levers apply to every city.
  select.addEventListener("change", () => {
    const url = new URL(window.location.href);
    url.searchParams.set("city", select.value);
    window.location.href = url.toString();
  });
}

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
  $("stat-realistic").textContent = fmt.format(now.totals.realistic);
  const rNote = $("stat-realistic-note");
  if (reform) {
    const d = now.totals.realistic - today.totals.realistic;
    rNote.innerHTML = `<span class="up">${d >= 0 ? "+" : "−"}${fmt.format(Math.abs(d))}</span> vs. ${fmt.format(today.totals.realistic)} today · ${fmt.format(now.totals.likelyLots)} lots · a screen, not a forecast`;
  } else {
    rNote.textContent = `on ${fmt.format(now.totals.likelyLots)} lots, vs. ${fmt.format(now.totals.net)} new homes in theory · a screen, not a forecast`;
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
  return `<div class="popup">${header}<dl>${rows.join("")}</dl>${limits}
    <button type="button" class="popup-details">All limits and code sections</button></div>`;
}

function renderCharts(data: ParcelData, now: Results, today: Results, reform: boolean) {
  const realistic = document.querySelector<HTMLInputElement>('input[name="chart-mode"]:checked')?.value === "realistic";
  const pickValue = realistic ? realisticNew : netNew;
  const what = realistic ? "New homes on lots likely to redevelop" : "New homes possible";
  for (const [id, title, rows] of [
    ["chart-district", `${what}, by council district`, byDistrict(data, today, now, pickValue)],
    ["chart-transit", `${what}, by distance to a major transit stop`, byTransitDistance(data, today, now, pickValue)],
  ] as const) {
    const el = $(id);
    renderBarChart(el, { title, valueLabel: what.toLowerCase(), rows: [...rows], showScenario: reform }, currentTheme(), el.clientWidth || 300);
  }
}

// --- Main ----------------------------------------------------------------------------

async function main() {
  const status = $("status");
  try {
    const cities = await loadJson<CityInfo[]>(`${DATA_ROOT}/cities.json`);
    const city = pickCity(cities);
    setupCityPicker(cities, city);
    const cityName = city.name.split(",")[0];
    $("city-name").textContent = cityName;
    document.title = `${cityName} Zoning Capacity`;
    const DATA_DIR = `${DATA_ROOT}/${city.id}`;
    const TILES_URL = new URL(`${DATA_DIR}/parcels.pmtiles`, window.location.href).href;
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

    const controller = await createMap("map", data, TILES_URL, { center: city.center, zoom: city.zoom });
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

    // --- Lot details panel ---
    let selectedPid: number | null = null;
    const details = $("details");
    const showDetails = (pid: number, focus = false) => {
      selectedPid = pid;
      controller.select(pid);
      renderLotDetails($("details-body"), pid, data, inputs, rules, scenario, !isBaseline(scenario), BASELINE);
      details.hidden = false;
      if (focus) {
        details.focus();
        details.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }
    };
    $("details-close").addEventListener("click", () => {
      details.hidden = true;
      selectedPid = null;
      controller.select(null);
      $("search-input").focus();
    });

    const applyScenario = (next: Scenario, updateUrl = true) => {
      scenario = next;
      const t0 = performance.now();
      now = isBaseline(scenario) ? today : runScenario(data, inputs, rules, scenario);
      writeForm(scenario);
      showHeadline(data, scenario, now, today);
      controller.setResults(now, today);
      redraw();
      renderCharts(data, now, today, !isBaseline(scenario));
      if (selectedPid !== null) showDetails(selectedPid);
      popup.remove();
      // Keep ?city=... (the search part); only the #scenario changes.
      if (updateUrl) history.replaceState(null, "", window.location.pathname + window.location.search + scenarioToHash(scenario));
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

    renderCharts(data, now, today, !isBaseline(scenario));
    document.querySelectorAll<HTMLInputElement>('input[name="chart-mode"]').forEach((input) =>
      input.addEventListener("change", () => renderCharts(data, now, today, !isBaseline(scenario))),
    );
    let chartWidth = $("chart-district").clientWidth;
    window.addEventListener("resize", () => {
      if ($("chart-district").clientWidth !== chartWidth) {
        chartWidth = $("chart-district").clientWidth;
        renderCharts(data, now, today, !isBaseline(scenario));
      }
    });

    const popup = new maplibregl.Popup({ maxWidth: "300px", focusAfterOpen: true });
    const openLot = (pid: number, lngLat: maplibregl.LngLatLike) => {
      popup.setLngLat(lngLat).setHTML(popupHtml(data, pid, now, today, !isBaseline(scenario))).addTo(controller.map);
      popup.getElement()?.querySelector(".popup-details")?.addEventListener("click", () => showDetails(pid, true));
      showDetails(pid);
    };
    controller.onLotClick((pid, lngLat) => {
      openLot(pid, lngLat);
      // On phones the map is short, so move the clicked lot near the top to
      // leave room for the popup below it.
      if (window.matchMedia("(max-width: 760px)").matches) {
        const height = controller.map.getContainer().clientHeight;
        controller.map.easeTo({ center: lngLat, offset: [0, -(height / 2 - 40)], duration: 300 });
      }
    });

    // --- Address search ---
    setupSearch(
      $<HTMLInputElement>("search-input"),
      $<HTMLUListElement>("search-list"),
      $("search-status"),
      () => loadJson<AddressIndex>(`${DATA_DIR}/addresses.json`),
      data.columns.parcel_id,
      (hit) => {
        controller.map.flyTo({ center: [hit.lng, hit.lat], zoom: 17, duration: 800 });
        controller.map.once("moveend", () => openLot(hit.pid, [hit.lng, hit.lat]));
        showDetails(hit.pid);
      },
    );

    // --- Printable summary ---
    const fillPrint = () => {
      const reform = !isBaseline(scenario);
      let mapImage: string | null = null;
      try {
        mapImage = controller.map.getCanvas().toDataURL("image/png");
      } catch {
        mapImage = null; // a blank or tainted canvas: print without the map
      }
      renderPrintSummary($("print-summary"), {
        city: cityName,
        reform,
        levers: describeScenario(form()),
        existing: today.totals.existing,
        todayMax: today.totals.max,
        scenarioMax: now.totals.max,
        todayNet: today.totals.net,
        scenarioNet: now.totals.net,
        todayRealistic: today.totals.realistic,
        scenarioRealistic: now.totals.realistic,
        byDistrict: byDistrict(data, today, now),
        byTransit: byTransitDistance(data, today, now),
        mapImage,
        url: window.location.href,
        generatedAt: new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }),
      });
    };
    window.addEventListener("beforeprint", fillPrint);
    $("print").addEventListener("click", () => {
      fillPrint();
      window.print();
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
