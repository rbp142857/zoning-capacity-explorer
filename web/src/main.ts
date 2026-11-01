// Entry point: load the data, draw the map, wire up the controls.
//
// Flow: the URL hash -> a Scenario -> run the engine on every lot ->
// headline numbers, legend and map colors. Changing a lever updates the
// hash, so the address bar always holds a shareable link to what you see.

import maplibregl from "maplibre-gl";

import "./style.css";
import { renderBarChart } from "./charts";
import {
  COMBINED, type CityInfo, mergeParcelData, mergeResults, selectionFromSearch, selectionToSearch, shortName,
} from "./cities";
import { BINDING_LABELS } from "./colors";
import { type ParcelData, loadJson } from "./data";
import { type LotInputs, type Results, buildLotInputs, runScenario } from "./engine/run";
import { BASELINE, type Scenario, isBaseline } from "./engine/scenario";
import type { RulesFile } from "./engine/types";
import { renderLotDetails } from "./details";
import { renderLegend } from "./legend";
import { createMap, currentTheme, type MapCity, type View } from "./map";
import { describeScenario, renderPrintSummary } from "./print";
import { type AddressIndex, setupSearch } from "./search";
import { byDistrict, byTransitDistance, netNew, realisticNew } from "./summary";
import { LEVERS, scenarioFromHash, scenarioToHash } from "./url";

// import.meta.env.BASE_URL is "./" (see vite.config.ts), so these work
// whether the site is served at / or at /<repo-name>/ on GitHub Pages.
const DATA_ROOT = `${import.meta.env.BASE_URL}data`;

/** What one selected city needs: its own rules, and its answers under today's rules. */
interface CityBundle {
  info: CityInfo;
  data: ParcelData;
  rules: RulesFile;
  inputs: LotInputs;
  today: Results;
  offset: number; // where its lots start in the combined list
}

const cityDir = (id: string) => `${DATA_ROOT}/${id}`;

/** Build the dropdown of checkboxes; onChange gets the ids that are now ticked. */
function setupCityPicker(cities: CityInfo[], selected: string[], onChange: (ids: string[]) => void) {
  const picker = $<HTMLDetailsElement>("city-picker");
  const box = $("city-options");
  const makeRow = (text: string, value: string) => {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = value;
    label.append(input, text);
    box.append(label);
    return input;
  };
  const all = makeRow("Select all", "");
  all.parentElement?.classList.add("select-all");
  const rows = cities.map((c) => makeRow(shortName(c), c.id));
  const ticked = () => rows.filter((r) => r.checked).map((r) => r.value);
  const showState = () => {
    const ids = ticked();
    all.checked = ids.length === rows.length;
    all.indeterminate = ids.length > 0 && ids.length < rows.length;
    const one = cities.find((c) => c.id === ids[0]);
    $("city-summary").textContent =
      ids.length === 0 ? "No cities" : ids.length === 1 && one ? shortName(one) : ids.length === rows.length ? "All cities" : `${ids.length} cities`;
  };
  rows.forEach((r) => (r.checked = selected.includes(r.value)));
  showState();
  all.addEventListener("change", () => rows.forEach((r) => (r.checked = all.checked)));
  box.addEventListener("change", () => {
    showState();
    onChange(ticked());
  });
  // Close like a menu: click elsewhere, or press Escape.
  document.addEventListener("click", (e) => {
    if (picker.open && !picker.contains(e.target as Node)) picker.open = false;
  });
  picker.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && picker.open) {
      picker.open = false;
      picker.querySelector("summary")?.focus();
    }
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

/** What a city's chart groups are: several cities show one bar per city. */
function districtTitle(data: ParcelData): string {
  if (data.city === COMBINED) return "city";
  return data.codes.district.some((d) => d.startsWith("ZIP")) ? "ZIP code" : "council district";
}

function renderCharts(data: ParcelData, now: Results, today: Results, reform: boolean) {
  const realistic = document.querySelector<HTMLInputElement>('input[name="chart-mode"]:checked')?.value === "realistic";
  const pickValue = realistic ? realisticNew : netNew;
  const what = realistic ? "New homes on lots likely to redevelop" : "New homes possible";
  for (const [id, title, rows] of [
    ["chart-district", `${what}, by ${districtTitle(data)}`, byDistrict(data, today, now, pickValue)],
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
    const allIds = cities.map((c) => c.id);

    // Each city is downloaded once, however many times it's ticked and unticked.
    const loaded = new Map<string, Promise<Omit<CityBundle, "offset">>>();
    const loadCity = (info: CityInfo) => {
      let city = loaded.get(info.id);
      if (!city) {
        city = (async () => {
          const [data, rules] = await Promise.all([
            loadJson<ParcelData>(`${cityDir(info.id)}/parcels.json`),
            loadJson<RulesFile>(`${cityDir(info.id)}/rules.json`),
          ]);
          const inputs = buildLotInputs(data);
          return { info, data, rules, inputs, today: runScenario(data, inputs, rules, BASELINE) };
        })();
        city.catch(() => loaded.delete(info.id)); // allow a retry
        loaded.set(info.id, city);
      }
      return city;
    };

    // The selection and everything computed from it. Listeners below read
    // these when they run, so changing the selection needs no re-wiring.
    let bundles: CityBundle[] = [];
    let data = mergeParcelData([], []);
    let today = mergeResults([]);
    let scenario = scenarioFromHash(window.location.hash);
    let now = today;

    const computeNow = () =>
      isBaseline(scenario)
        ? today
        : mergeResults(bundles.map((b) => runScenario(b.data, b.inputs, b.rules, scenario)));

    /** Load `ids` and make them the current selection. False if a newer selection replaced it. */
    let selectionToken = 0;
    const setSelection = async (ids: string[]) => {
      const token = ++selectionToken;
      const chosen = cities.filter((c) => ids.includes(c.id));
      const parts = await Promise.all(chosen.map(loadCity));
      if (token !== selectionToken) return false;
      let offset = 0;
      bundles = parts.map((p) => {
        const b = { ...p, offset };
        offset += p.data.count;
        return b;
      });
      data = mergeParcelData(parts.map((p) => p.data), chosen.map(shortName));
      today = mergeResults(parts.map((p) => p.today));
      now = computeNow();
      const place = bundles.length === 1 ? shortName(bundles[0].info) : bundles.length ? `${bundles.length} Cities` : "LA County";
      $("city-name").textContent = place;
      document.title = `${place} Zoning Capacity`;
      return true;
    };

    const selected = selectionFromSearch(window.location.search, allIds);
    await setSelection(selected);
    writeForm(scenario);
    showHeadline(data, scenario, now, today);

    const mapCities = (): MapCity[] =>
      bundles.map((b) => ({
        id: b.info.id,
        tilesUrl: new URL(`${cityDir(b.info.id)}/parcels.pmtiles`, window.location.href).href,
        offset: b.offset,
        count: b.data.count,
      }));

    // One city opens at its usual view; several are framed to fit.
    const start = bundles.length === 1 ? bundles[0].info : cities[0];
    const bindingCodes = bundles[0]?.data.codes.binding ?? (await loadCity(cities[0])).data.codes.binding;
    const controller = await createMap("map", bindingCodes, { center: start.center, zoom: start.zoom });
    const frameCities = (animate: boolean) => {
      if (bundles.length === 1) {
        const { center, zoom } = bundles[0].info;
        controller.map.easeTo({ center, zoom, duration: animate ? 600 : 0 });
      } else if (bundles.length > 1) {
        const [w, s, e, n] = data.bounds;
        controller.map.fitBounds([[w, s], [e, n]], { padding: 40, animate });
      }
    };
    frameCities(false);
    status.textContent = "";
    controller.setCities(mapCities());
    controller.setResults(now, today);

    // Highlight menu: one option per binding constraint.
    const select = $<HTMLSelectElement>("highlight");
    bindingCodes.forEach((name, code) => {
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
      renderLegend(legend, data, view, now, today, currentTheme(), code === null ? null : bindingCodes[code]);
    };

    // --- Lot details panel ---
    let selectedPid: number | null = null;
    const details = $("details");
    const closeDetails = () => {
      details.hidden = true;
      selectedPid = null;
      controller.select(null);
    };
    const showDetails = (pid: number, focus = false) => {
      selectedPid = pid;
      controller.select(pid);
      // The engine's details need the lot's own city: its rules, its numbering.
      const b = bundles.find((c) => pid >= c.offset && pid < c.offset + c.data.count) as CityBundle;
      renderLotDetails($("details-body"), pid - b.offset, b.data, b.inputs, b.rules, scenario, !isBaseline(scenario), BASELINE);
      details.hidden = false;
      if (focus) {
        details.focus();
        details.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }
    };
    $("details-close").addEventListener("click", () => {
      closeDetails();
      $("search-input").focus();
    });

    const applyScenario = (next: Scenario, updateUrl = true) => {
      scenario = next;
      const t0 = performance.now();
      now = computeNow();
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
    const loadAddresses = async (): Promise<AddressIndex> => {
      const lists = await Promise.all(
        bundles.map(async (b) => ({ b, list: await loadJson<AddressIndex>(`${cityDir(b.info.id)}/addresses.json`) })),
      );
      return {
        address: lists.flatMap(({ list }) => list.address),
        pid: lists.flatMap(({ b, list }) => list.pid.map((p) => p + b.offset)),
        lng: lists.flatMap(({ list }) => list.lng),
        lat: lists.flatMap(({ list }) => list.lat),
      };
    };
    const search = setupSearch(
      $<HTMLInputElement>("search-input"),
      $<HTMLUListElement>("search-list"),
      $("search-status"),
      loadAddresses,
      () => data.columns.parcel_id,
      (hit) => {
        controller.map.flyTo({ center: [hit.lng, hit.lat], zoom: 17, duration: 800 });
        controller.map.once("moveend", () => openLot(hit.pid, [hit.lng, hit.lat]));
        showDetails(hit.pid);
      },
    );

    // --- Choosing cities ---
    setupCityPicker(cities, selected, async (ids) => {
      status.textContent = "Loading…";
      try {
        if (!(await setSelection(ids))) return; // a newer choice took over
        status.textContent = ids.length ? "" : "Select a city to see its lots.";
        popup.remove();
        closeDetails();
        search.reset();
        controller.setCities(mapCities());
        controller.setResults(now, today);
        showHeadline(data, scenario, now, today);
        redraw();
        renderCharts(data, now, today, !isBaseline(scenario));
        frameCities(true);
        history.replaceState(
          null, "",
          window.location.pathname + selectionToSearch(window.location.search, ids, allIds) + window.location.hash,
        );
      } catch (err) {
        status.textContent = `Couldn't load that city. ${(err as Error).message}`;
        console.error(err);
      }
    });

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
        cities: bundles.map((b) => shortName(b.info)),
        districtTitle: districtTitle(data),
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
