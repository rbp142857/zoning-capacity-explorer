// The map: basemap, lot shapes from PMTiles, and colors.
//
// Today's color for every lot is stored in the tiles, so the map draws with no
// lot data at all and needs no per-lot work in the browser. A reform scenario only
// overrides the lots it changes, using MapLibre's "feature state": each paint rule
// reads the state if a lot has one, and the tile's number if not.
//
// All cities share a few tiles files. A lot's number in its file is its city's
// `start` + its `pid`. The rest of the site numbers lots across the selected
// cities, so a lot's number there is its city's `offset` + its `pid`.

import maplibregl, { type ExpressionSpecification, type Map as MlMap } from "maplibre-gl";
import { Protocol } from "pmtiles";
import "maplibre-gl/dist/maplibre-gl.css";

import {
  ADDED_CLASSES,
  BINDING_GROUPS,
  CATEGORICAL,
  MAX_UNITS_CLASSES,
  NET_NEW_CLASSES,
  NEUTRAL,
  rampFor,
  type Theme,
  type ValueClass,
} from "./colors";
import { NA } from "./data";
import type { Results } from "./engine/run";

export type View = "max" | "net" | "added" | "likely" | "binding";

// Below this zoom the tiles leave out the smallest lots, so a click zooms in.
// Keep in step with DETAIL_ZOOM in export_web.py.
const DETAIL_ZOOM = 12;

const SOURCE_LAYER = "parcels"; // the layer name we gave tippecanoe
const sourceId = (group: string) => `lots-${group}`;
const fillId = (group: string) => `lots-fill-${group}`;
const lineId = (group: string) => `lots-line-${group}`;
const selectedId = (group: string) => `lots-selected-${group}`;

/** One selected city: where its lots are in the tiles and in the combined numbering. */
export interface MapCity {
  id: string;
  index: number; // its place in cities.json, stored in the tiles as `c`
  tiles: string;
  start: number;
  offset: number;
  count: number;
}

// Free basemaps from OpenFreeMap (OpenStreetMap data, no API key).
const BASEMAPS: Record<Theme, string> = {
  light: "https://tiles.openfreemap.org/styles/positron",
  dark: "https://tiles.openfreemap.org/styles/dark",
};

const DATA_ATTRIBUTION =
  "Parcels: LA County Assessor · Zoning: city zoning maps and SCAG · Transit stops: SCAG · Analysis: Zoning Capacity Explorer";

// The pmtiles:// protocol lets MapLibre read individual tiles out of one
// .pmtiles file using HTTP range requests, so no tile server is needed.
maplibregl.addProtocol("pmtiles", new Protocol().tile);

export function currentTheme(): Theme {
  const forced = document.documentElement.dataset.theme;
  if (forced === "light" || forced === "dark") return forced;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/** A number the state overrides, or the one in the tile (see tile_properties in export_web.py). */
const stateOrTile = (key: string, prop: string): ExpressionSpecification => ["coalesce", ["feature-state", key], ["get", prop]];

/** Homes added by a reform: only in the state. Without one, it's 0 on modeled lots. */
const addedValue: ExpressionSpecification = ["coalesce", ["feature-state", "added"], ["case", ["<", ["get", "m"], 0], -1, 0]];

/** Color by value classes: grays for "not modeled" (-1) and 0, then the ramp. */
function classExpression(value: ExpressionSpecification, classes: ValueClass[], theme: Theme): ExpressionSpecification {
  const ramp = rampFor(theme);
  const n = NEUTRAL[theme];
  // ["step", input, color0, stop1, color1, ...]: color_i applies from stop_i up.
  const steps: (string | number)[] = [ramp[0]];
  classes.slice(1).forEach((c, i) => steps.push(c.min, ramp[i + 1]));
  return [
    "case",
    ["<", value, 0], n.notModeled,
    ["==", value, 0], n.zero,
    ["step", value, ...steps] as unknown as ExpressionSpecification,
  ];
}

function bindingExpression(bindingCodes: string[], theme: Theme, highlightCode: number | null): ExpressionSpecification {
  const n = NEUTRAL[theme];
  const cat = CATEGORICAL[theme];
  const raw = stateOrTile("binding", "b");
  if (highlightCode !== null) {
    // One limit in the first categorical color, every other lot muted.
    return ["case", ["==", raw, highlightCode], cat[0], ["<", raw, 0], n.notModeled, n.zero];
  }
  const pairs: (number | string)[] = [];
  bindingCodes.forEach((name, code) => {
    const g = BINDING_GROUPS.find((group) => group.members.includes(name));
    if (g) pairs.push(code, g.slot === "zero" ? n.zero : cat[g.slot]);
  });
  return ["match", raw, ...pairs, n.notModeled] as unknown as ExpressionSpecification;
}

export interface MapController {
  map: MlMap;
  setView(view: View, highlightCode?: number | null): void;
  /** Show these cities' lots, in today's colors until the next setResults call. */
  setCities(cities: MapCity[]): void;
  setResults(scenario: Results, today: Results): void;
  /** `pids` is every lot under the click: the county's parcels sometimes overlap. */
  onLotClick(handler: (pids: number[], lngLat: maplibregl.LngLat) => void): void;
  /** Outline one lot (the one shown in the details panel), or none. */
  select(pid: number | null): void;
}

/**
 * @param citiesInGroup how many cities each tiles file holds, to spot "all of them"
 */
export function createMap(
  container: string,
  citiesInGroup: Record<string, number>,
  tilesUrl: (group: string) => string,
  bindingCodes: string[],
  view0: { center: [number, number]; zoom: number },
): Promise<MapController> {
  const groups = Object.keys(citiesInGroup);
  let theme = currentTheme();
  let view: View = "max";
  let highlight: number | null = null;
  let latest: { scenario: Results; today: Results } | null = null;
  // What the map's lots show, or null if unknown or still being painted.
  let applied: { scenario: Results; today: Results } | null = null;
  let paintJob = 0;
  let selected: number | null = null;
  let cities: MapCity[] = [];
  const clickHandlers: ((pids: number[], lngLat: maplibregl.LngLat) => void)[] = [];

  const map = new maplibregl.Map({
    container,
    style: BASEMAPS[theme],
    center: view0.center,
    zoom: view0.zoom,
    minZoom: 8,
    maxZoom: 18,
    attributionControl: { customAttribution: DATA_ATTRIBUTION, compact: true },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "imperial" }), "bottom-left");

  function paintFor(): ExpressionSpecification {
    if (view === "max") return classExpression(stateOrTile("max", "m"), MAX_UNITS_CLASSES, theme);
    if (view === "net") return classExpression(stateOrTile("net", "n"), NET_NEW_CLASSES, theme);
    if (view === "added") return classExpression(addedValue, ADDED_CLASSES, theme);
    if (view === "likely") return classExpression(stateOrTile("likely", "l"), ADDED_CLASSES, theme);
    return bindingExpression(bindingCodes, theme, highlight);
  }

  /** Where a lot in the combined numbering is in the tiles. */
  function target(pid: number) {
    const city = cities.find((c) => pid >= c.offset && pid < c.offset + c.count);
    return city ? { source: sourceId(city.tiles), sourceLayer: SOURCE_LAYER, id: city.start + pid - city.offset } : null;
  }

  function addLotLayers(group: string) {
    const SOURCE = sourceId(group);
    map.addSource(SOURCE, {
      type: "vector",
      url: `pmtiles://${tilesUrl(group)}`,
      promoteId: { [SOURCE_LAYER]: "pid" },
    });
    map.addLayer({
      id: fillId(group),
      type: "fill",
      source: SOURCE,
      "source-layer": SOURCE_LAYER,
      paint: { "fill-color": paintFor(), "fill-opacity": 0.88 },
    });
    // A thin line in the background color separates neighboring lots.
    map.addLayer({
      id: lineId(group),
      type: "line",
      source: SOURCE,
      "source-layer": SOURCE_LAYER,
      minzoom: 14,
      paint: {
        "line-color": NEUTRAL[theme].outline,
        "line-width": ["interpolate", ["linear"], ["zoom"], 14, 0.3, 17, 1.2],
      },
    });
    // Thick outline around the selected lot, in the ink color so it reads on every
    // fill color. It changes with feature state: changing a layer's filter instead
    // would rebuild every tile on screen, which took seconds with many cities.
    map.addLayer({
      id: selectedId(group),
      type: "line",
      source: SOURCE,
      "source-layer": SOURCE_LAYER,
      minzoom: 12,
      paint: {
        "line-color": theme === "dark" ? "#f0efec" : "#0b0b0b",
        "line-width": 3,
        "line-opacity": ["case", ["boolean", ["feature-state", "selected"], false], 1, 0],
      },
    });
  }

  /** Show only the selected cities. A file with none is hidden, so its tiles aren't fetched. */
  function applyCityFilter() {
    for (const group of groups) {
      if (!map.getLayer(fillId(group))) continue;
      const mine = cities.filter((c) => c.tiles === group).map((c) => c.index);
      // Every city in the file selected means no filter, which is cheapest to draw.
      const filter = mine.length === citiesInGroup[group] || !mine.length ? null : (["in", ["get", "c"], ["literal", mine]] as ExpressionSpecification);
      for (const layer of [fillId(group), lineId(group), selectedId(group)]) {
        map.setLayoutProperty(layer, "visibility", mine.length ? "visible" : "none");
        map.setFilter(layer, filter);
      }
    }
  }

  function outlineSelected() {
    const t = selected === null ? null : target(selected);
    if (t && map.getSource(t.source)) map.setFeatureState(t, { selected: true });
  }

  function clearStates() {
    for (const group of groups) {
      if (map.getSource(sourceId(group))) map.removeFeatureState({ source: sourceId(group), sourceLayer: SOURCE_LAYER });
    }
    outlineSelected();
  }

  const sameAnswer = (a: Results, b: Results, i: number) =>
    a.binding[i] === b.binding[i] && a.max[i] === b.max[i] && a.net[i] === b.net[i] && a.realistic[i] === b.realistic[i];

  /**
   * Bring the map up to date with `latest`: only lots whose answer changed, in
   * short bursts, so the map keeps moving while a large reform draws.
   */
  function paintResults() {
    const job = ++paintJob;
    if (!latest) return;
    const current = latest;
    const { scenario, today } = current;
    // Lots hold state only while a finished paint says what it was.
    const known = applied !== null && applied.today === today;
    const before = known && applied ? applied.scenario : today;
    applied = null;
    if (!known || scenario === today) clearStates();
    if (scenario === today) {
      applied = current;
      return;
    }
    const start = !known || scenario === today ? today : before;
    const todo = cities.slice();
    let cityAt = 0;
    let at = 0;
    const step = () => {
      if (job !== paintJob) {
        return; // a newer scenario took over; it starts clean because `applied` is null
      }
      const stopAt = performance.now() + 8;
      for (; cityAt < todo.length; cityAt++, at = 0) {
        const city = todo[cityAt];
        const source = sourceId(city.tiles);
        if (!map.getSource(source)) continue;
        for (; at < city.count; at++) {
          if (at % 256 === 0 && performance.now() > stopAt) {
            requestAnimationFrame(step);
            return;
          }
          const i = city.offset + at;
          if (sameAnswer(start, scenario, i)) continue;
          const feature = { source, sourceLayer: SOURCE_LAYER, id: city.start + at };
          if (sameAnswer(today, scenario, i)) {
            map.removeFeatureState(feature); // back to the tile's color
            if (selected === i) outlineSelected();
            continue;
          }
          const code = scenario.binding[i];
          const modeled = code >= 0;
          const orNone = (v: number) => (modeled && v !== NA ? v : -1);
          map.setFeatureState(feature, {
            max: orNone(scenario.max[i]),
            net: orNone(scenario.net[i]),
            added: modeled ? Math.max(0, (scenario.max[i] === NA ? 0 : scenario.max[i]) - (today.max[i] === NA ? 0 : today.max[i])) : -1,
            likely: modeled ? scenario.realistic[i] : -1,
            binding: code,
          });
        }
      }
      applied = current;
    };
    step();
  }

  const lotsAt = (point: maplibregl.Point) => {
    const layers = groups.map(fillId).filter((id) => map.getLayer(id) && map.getLayoutProperty(id, "visibility") !== "none");
    return layers.length ? map.queryRenderedFeatures(point, { layers }) : [];
  };
  map.on("click", (e) => {
    if (map.getZoom() < DETAIL_ZOOM) {
      if (lotsAt(e.point).length) map.easeTo({ center: e.lngLat, zoom: DETAIL_ZOOM + 2, duration: 500 });
      return;
    }
    const pids = lotsAt(e.point).flatMap((feature) => {
      // The id can arrive as a number or a numeric string depending on how
      // the tile encoded `pid`, so convert explicitly.
      const id = Number(feature.id);
      const city = cities.find((c) => sourceId(c.tiles) === feature.source && id >= c.start && id < c.start + c.count);
      return city ? [city.offset + id - city.start] : [];
    });
    if (pids.length) clickHandlers.forEach((h) => h(pids, e.lngLat));
  });
  // Pointer cursor over lots, checked at most about ten times a second.
  let lastHover = 0;
  map.on("mousemove", (e) => {
    if (e.originalEvent.timeStamp - lastHover < 100) return;
    lastHover = e.originalEvent.timeStamp;
    map.getCanvas().style.cursor = lotsAt(e.point).length ? "pointer" : "";
  });

  // Follow the OS light/dark setting. Switching basemaps replaces the whole
  // style, so our layers and feature state are added again afterwards.
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    const next = currentTheme();
    if (next === theme) return;
    theme = next;
    map.once("style.load", () => {
      applied = null; // a new style starts with no scenario colors
      groups.forEach(addLotLayers);
      applyCityFilter();
      paintResults();
      outlineSelected();
    });
    map.setStyle(BASEMAPS[theme]);
  });

  const controller: MapController = {
    map,
    setView(next, highlightCode = null) {
      view = next;
      highlight = highlightCode;
      for (const group of groups) {
        if (map.getLayer(fillId(group))) map.setPaintProperty(fillId(group), "fill-color", paintFor());
      }
    },
    setCities(next) {
      // Results from the old selection use the old numbering.
      paintJob++;
      latest = null;
      applied = null;
      selected = null;
      clearStates();
      cities = next;
      applyCityFilter();
    },
    setResults(scenario, today) {
      latest = { scenario, today };
      paintResults();
    },
    onLotClick(handler) {
      clickHandlers.push(handler);
    },
    select(pid) {
      const old = selected === null ? null : target(selected);
      if (old && map.getSource(old.source)) map.removeFeatureState(old, "selected");
      selected = pid;
      outlineSelected();
    },
  };

  // The compact credits box starts expanded and covers much of a phone
  // screen. Collapse it to its (i) button once the map is drawn; it still
  // opens on click. (Removing this class is how MapLibre itself collapses it.)
  map.once("idle", () =>
    map.getContainer().querySelector(".maplibregl-ctrl-attrib")?.classList.remove("maplibregl-compact-show"),
  );
  // Add our layers as soon as the basemap's style is parsed ("style.load"),
  // not on "load", which also waits for every basemap tile, font and icon.
  // If the free basemap is slow or down, the lots still appear.
  map.on("error", (e) => console.warn("Map error:", e.error?.message ?? e));
  return new Promise((resolve) => {
    map.once("style.load", () => {
      groups.forEach(addLotLayers);
      resolve(controller);
    });
  });
}
