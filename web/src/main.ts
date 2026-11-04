// Entry point: load the data, draw the map, wire up the controls.
//
// Flow: the URL hash -> a Scenario -> run the engine on every lot ->
// headline numbers, legend and map colors. Changing a lever updates the
// hash, so the address bar always holds a shareable link to what you see.

import maplibregl from "maplibre-gl";

import "./style.css";
import { renderBarChart } from "./charts";
import {
  COMBINED, COUNTY_VIEW, type CityInfo, mergeParcelData, mergeResults, selectionFromSearch, selectionToSearch, shortName, unionBounds,
} from "./cities";
import { BINDING_LABELS } from "./colors";
import { BINDING_CODES, type ParcelData, fetchBinary, loadJson, loadLots, na, parcelId } from "./data";
import { type Results, resultsFromColumns, runScenarioInSteps } from "./engine/run";
import { BASELINE, type Scenario, isBaseline } from "./engine/scenario";
import type { RulesFile } from "./engine/types";
import { renderLotDetails } from "./details";
import { renderLegend } from "./legend";
import { createMap, currentTheme, type MapCity, type View } from "./map";
import { downloadText, lotsCsvParts } from "./csv";
import { describeScenario, renderPrintSummary } from "./print";
import { type AddressIndex, makeAddressIndex, setupSearch } from "./search";
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
  today: Results;
  offset: number; // where its lots start in the combined list
}

const cityDir = (id: string) => `${DATA_ROOT}/${id}`;

/** Build the dropdown of checkboxes; onChange gets the ids that are now ticked. */
function setupCityPicker(cities: CityInfo[], selected: string[], onChange: (ids: string[]) => void) {
  const picker = $<HTMLDetailsElement>("city-picker");
  const box = $("city-options");
  const makeRow = (text: string, value: string, level?: string) => {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = value;
    label.append(input, text);
    if (level) {
      const tag = document.createElement("span");
      tag.className = "city-level";
      tag.textContent = level;
      label.append(tag);
    }
    box.append(label);
    return input;
  };
  const all = makeRow("Select all", "");
  all.parentElement?.classList.add("select-all");
  const rows = cities.map((c) => makeRow(shortName(c), c.id, c.level));
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
  const special = now.totals.specialLandNet;
  if (special > 0) {
    note.append(` · ${fmt.format(special)} of the new homes are on government, utility, quarry, cemetery, golf or private school land`);
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
  const n = (v: number) => (na(v) === null ? "unknown" : fmt.format(v));
  const header = `<h3>Lot ${parcelId(data, pid)}</h3><div>Zone <strong>${zone}</strong> · ${fmt.format(c.lot_area_sqft[pid])} sq ft</div>`;
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
    const citiesInGroup: Record<string, number> = {};
    for (const c of cities) citiesInGroup[c.tiles] = (citiesInGroup[c.tiles] ?? 0) + 1;

    // Each city is downloaded once, however many times it's ticked and unticked.
    const loaded = new Map<string, Promise<Omit<CityBundle, "offset">>>();
    const loadCity = (info: CityInfo) => {
      let city = loaded.get(info.id);
      if (!city) {
        city = (async () => {
          const [data, rules] = await Promise.all([
            loadLots(`${cityDir(info.id)}/lots.bin.gz`),
            loadJson<RulesFile>(`${cityDir(info.id)}/rules.json`),
          ]);
          return { info, data, rules, today: resultsFromColumns(data, rules) };
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
    let lotsReady = false; // false while a selection's numbers are still loading

    /** Today's results if nothing changed. Null if a newer scenario took over while this ran. */
    let computeToken = 0;
    const computeNow = async (): Promise<Results | null> => {
      const token = ++computeToken;
      if (isBaseline(scenario)) return today;
      const parts: Results[] = [];
      for (const b of bundles) {
        const r = await runScenarioInSteps(b.data, b.rules, scenario, () => token === computeToken);
        if (!r) return null;
        parts.push(r);
      }
      return token === computeToken ? mergeResults(parts) : null;
    };

    /** Where the chosen cities' lots are, known before any lot data arrives. */
    const mapCitiesFor = (ids: string[]): MapCity[] => {
      let offset = 0;
      const out: MapCity[] = [];
      cities.forEach((c, index) => {
        if (!ids.includes(c.id)) return;
        out.push({ id: c.id, index, tiles: c.tiles, start: c.start, offset, count: c.count });
        offset += c.count;
      });
      return out;
    };

    /** Load `ids` and make them the current selection. False if a newer selection replaced it. */
    let selectionToken = 0;
    const setSelection = async (ids: string[]) => {
      const token = ++selectionToken;
      lotsReady = false;
      const chosen = cities.filter((c) => ids.includes(c.id));
      let done = 0;
      const progress = () => {
        if (token === selectionToken && chosen.length > 1) status.textContent = `Loading lot numbers: ${done} of ${chosen.length} cities…`;
      };
      progress();
      const parts = await Promise.all(chosen.map((c) => loadCity(c).then((p) => { done++; progress(); return p; })));
      if (token !== selectionToken) return false;
      let offset = 0;
      bundles = parts.map((p) => {
        const b = { ...p, offset };
        offset += p.data.count;
        return b;
      });
      data = mergeParcelData(parts.map((p) => p.data), chosen.map(shortName));
      today = mergeResults(parts.map((p) => p.today));
      now = (await computeNow()) ?? today;
      if (token !== selectionToken) return false;
      lotsReady = true;
      return true;
    };

    const showPlace = (ids: string[]) => {
      const chosen = cities.filter((c) => ids.includes(c.id));
      const place = chosen.length === 1 ? shortName(chosen[0]) : chosen.length ? `${chosen.length} Cities` : "LA County";
      $("city-name").textContent = place;
      document.title = `${place} Zoning Capacity`;
    };

    const selected = selectionFromSearch(window.location.search, allIds, window.matchMedia("(max-width: 760px)").matches);
    // Put the choice in the address, so a copied link shows the same cities on any screen.
    history.replaceState(null, "", window.location.pathname + selectionToSearch(window.location.search, selected, allIds) + window.location.hash);
    showPlace(selected);
    writeForm(scenario);

    // Start the numbers downloading, and draw the map without waiting for them:
    // its colors for today's rules come with the tiles.
    let selectedIds = selected;
    const firstLoad = setSelection(selected);

    // One city opens at its usual view; several are framed to fit; none shows the county.
    const firstCity = cities.find((c) => c.id === selected[0]);
    const start = selected.length === 1 && firstCity ? firstCity : COUNTY_VIEW;
    const bindingCodes = BINDING_CODES;
    const controller = await createMap(
      "map", citiesInGroup, (group: string) => new URL(`${DATA_ROOT}/tiles/${group}.pmtiles`, window.location.href).href, bindingCodes,
      { center: start.center, zoom: start.zoom },
    );
    const frameCities = (ids: string[], animate: boolean) => {
      const chosen = cities.filter((c) => ids.includes(c.id));
      if (chosen.length === 1) {
        const { center, zoom } = chosen[0];
        controller.map.easeTo({ center, zoom, duration: animate ? 600 : 0 });
      } else if (chosen.length > 1) {
        const [w, s, e, n] = unionBounds(chosen.map((c) => c.bounds));
        controller.map.fitBounds([[w, s], [e, n]], { padding: 40, animate });
      }
    };
    frameCities(selected, false);
    controller.setCities(mapCitiesFor(selected));

    // Choices made while the first load runs are picked up when it's done.
    let onCitiesChosen: ((ids: string[]) => void) | null = null;
    setupCityPicker(cities, selected, (ids) => {
      selectedIds = ids;
      showPlace(ids);
      frameCities(ids, true);
      controller.setCities(mapCitiesFor(ids));
      onCitiesChosen?.(ids);
    });

    await firstLoad;
    if (lotsReady) status.textContent = "";
    showHeadline(data, scenario, now, today);
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
      renderLotDetails($("details-body"), pid - b.offset, b.data, b.rules, scenario, !isBaseline(scenario), BASELINE);
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

    const applyScenario = async (next: Scenario, updateUrl = true) => {
      scenario = next;
      writeForm(scenario);
      // Keep ?city=... (the search part); only the #scenario changes.
      if (updateUrl) history.replaceState(null, "", window.location.pathname + window.location.search + scenarioToHash(scenario));
      if (!lotsReady) return; // the selection's load will use this scenario when it finishes
      const t0 = performance.now();
      if (!isBaseline(scenario)) status.textContent = "Calculating…";
      const result = await computeNow();
      if (!result) return; // a newer scenario took over
      now = result;
      status.textContent = "";
      showHeadline(data, scenario, now, today);
      controller.setResults(now, today);
      redraw();
      renderCharts(data, now, today, !isBaseline(scenario));
      if (selectedPid !== null) showDetails(selectedPid);
      popup.remove();
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
      if (!lotsReady) {
        status.textContent = "Still loading this lot's numbers. Try again in a moment.";
        return;
      }
      popup.setLngLat(lngLat).setHTML(popupHtml(data, pid, now, today, !isBaseline(scenario))).addTo(controller.map);
      popup.getElement()?.querySelector(".popup-details")?.addEventListener("click", () => showDetails(pid, true));
      showDetails(pid);
    };
    controller.onLotClick((pids, lngLat) => {
      // Where a big parcel covers smaller ones, the smallest is the one you can see to aim at.
      openLot(pids.reduce((a, b) => (data.columns.lot_area_sqft[b] < data.columns.lot_area_sqft[a] ? b : a)), lngLat);
      // On phones the map is short, so move the clicked lot near the top to
      // leave room for the popup below it.
      if (window.matchMedia("(max-width: 760px)").matches) {
        const height = controller.map.getContainer().clientHeight;
        controller.map.easeTo({ center: lngLat, offset: [0, -(height / 2 - 40)], duration: 300 });
      }
    });

    // --- Address search ---
    const loadAddresses = async (): Promise<AddressIndex[]> =>
      Promise.all(
        bundles.map(async (b) => {
          const file = await fetchBinary(`${cityDir(b.info.id)}/search.bin.gz`);
          const c = file.columns;
          return makeAddressIndex(new TextDecoder().decode(c.text as Uint8Array), c.lng as Float32Array, c.lat as Float32Array, b.offset);
        }),
      );
    const search = setupSearch(
      $<HTMLInputElement>("search-input"),
      $<HTMLUListElement>("search-list"),
      $("search-status"),
      loadAddresses,
      (digits) => data.columns.parcel_id.indexOf(Number(digits)),
      (hit) => {
        controller.map.flyTo({ center: [hit.lng, hit.lat], zoom: 17, duration: 800 });
        controller.map.once("moveend", () => openLot(hit.pid, [hit.lng, hit.lat]));
        showDetails(hit.pid);
      },
    );

    // --- Choosing cities ---
    onCitiesChosen = async (ids) => {
      popup.remove();
      closeDetails();
      search.reset();
      try {
        if (!(await setSelection(ids))) return; // a newer choice took over
        status.textContent = ids.length ? "" : "Select a city to see its lots.";
        controller.setResults(now, today);
        showHeadline(data, scenario, now, today);
        redraw();
        renderCharts(data, now, today, !isBaseline(scenario));
        history.replaceState(
          null, "",
          window.location.pathname + selectionToSearch(window.location.search, ids, allIds) + window.location.hash,
        );
      } catch (err) {
        status.textContent = `Couldn't load that city. ${(err as Error).message}`;
        console.error(err);
      }
    };
    // Cities changed while the first load ran.
    if (selectedIds !== selected) onCitiesChosen(selectedIds);

    // --- Printable summary ---
    const fillPrint = () => {
      const reform = !isBaseline(scenario);
      let mapImage: string | null = null;
      try {
        // The canvas only holds a picture right after drawing, so draw first.
        controller.map.redraw();
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
    $("cite-date").textContent = new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
    $("download-csv").addEventListener("click", () => {
      const reform = !isBaseline(scenario);
      downloadText("zoning-capacity-lots.csv", lotsCsvParts(data, today, now, window.location.href, reform));
    });
    $("print").addEventListener("click", () => {
      fillPrint();
      window.print();
    });

  } catch (err) {
    status.textContent = `Couldn't load the map data. ${(err as Error).message}`;
    console.error(err);
  }
}

main();
