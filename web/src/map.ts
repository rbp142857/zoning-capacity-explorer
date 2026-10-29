// The map: basemap, lot shapes from PMTiles, and colors from engine results.
//
// How coloring works: every lot shape in the tiles has a `pid`. We tell
// MapLibre to use it as the feature id (`promoteId`), then attach numbers to
// each id with `setFeatureState`. The paint rules read those numbers with
// ["feature-state", ...]. A new scenario only calls setResults(): the tiles
// are never re-downloaded.

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
import type { ParcelData } from "./data";
import type { Results } from "./engine/run";

export type View = "max" | "net" | "added" | "binding";

const SOURCE = "lots";
const SOURCE_LAYER = "parcels"; // the layer name we gave tippecanoe
const FILL = "lots-fill";
const LINE = "lots-line";

// Free basemaps from OpenFreeMap (OpenStreetMap data, no API key).
const BASEMAPS: Record<Theme, string> = {
  light: "https://tiles.openfreemap.org/styles/positron",
  dark: "https://tiles.openfreemap.org/styles/dark",
};

const DATA_ATTRIBUTION =
  "Parcels: LA County Assessor · Zoning: City of Pasadena · Transit stops: SCAG · Analysis: Zoning Capacity Explorer";

// The pmtiles:// protocol lets MapLibre read individual tiles out of one
// .pmtiles file using HTTP range requests, so no tile server is needed.
maplibregl.addProtocol("pmtiles", new Protocol().tile);

export function currentTheme(): Theme {
  const forced = document.documentElement.dataset.theme;
  if (forced === "light" || forced === "dark") return forced;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/** Color by value classes: grays for "not modeled" (-1) and 0, then the ramp. */
function classExpression(key: string, classes: ValueClass[], theme: Theme): ExpressionSpecification {
  const ramp = rampFor(theme);
  const n = NEUTRAL[theme];
  const value: ExpressionSpecification = ["coalesce", ["feature-state", key], -1];
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

function bindingExpression(theme: Theme, highlightCode: number | null): ExpressionSpecification {
  const n = NEUTRAL[theme];
  const cat = CATEGORICAL[theme];
  if (highlightCode !== null) {
    // One limit in the first categorical color, every other lot muted.
    const raw: ExpressionSpecification = ["coalesce", ["feature-state", "braw"], -1];
    return ["case", ["==", raw, highlightCode], cat[0], ["<", raw, 0], n.notModeled, n.zero];
  }
  const group: ExpressionSpecification = ["coalesce", ["feature-state", "bind"], -1];
  const pairs: (number | string)[] = [];
  BINDING_GROUPS.forEach((g, i) => pairs.push(i, g.slot === "zero" ? n.zero : cat[g.slot]));
  return ["match", group, ...pairs, n.notModeled] as unknown as ExpressionSpecification;
}

export interface MapController {
  map: MlMap;
  setView(view: View, highlightCode?: number | null): void;
  setResults(scenario: Results, today: Results): void;
  onLotClick(handler: (pid: number, lngLat: maplibregl.LngLat) => void): void;
  /** Outline one lot (the one shown in the details panel), or none. */
  select(pid: number | null): void;
}

export function createMap(container: string, data: ParcelData, tilesUrl: string): Promise<MapController> {
  let theme = currentTheme();
  let view: View = "max";
  let highlight: number | null = null;
  let latest: { scenario: Results; today: Results } | null = null;
  let selected: number | null = null;
  const clickHandlers: ((pid: number, lngLat: maplibregl.LngLat) => void)[] = [];

  const map = new maplibregl.Map({
    container,
    style: BASEMAPS[theme],
    center: [-118.135, 34.16], // Pasadena city hall, roughly
    zoom: 12.3,
    minZoom: 11,
    maxZoom: 18,
    attributionControl: { customAttribution: DATA_ATTRIBUTION, compact: true },
    // Keep the last frame readable so the print summary can include a
    // snapshot of the map (canvas.toDataURL()).
    preserveDrawingBuffer: true,
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "imperial" }), "bottom-left");

  // Group index per binding-constraint code, so feature state can hold a small number.
  const groupOfCode = data.codes.binding.map((name) => BINDING_GROUPS.findIndex((g) => g.members.includes(name)));

  function addLotLayers() {
    map.addSource(SOURCE, {
      type: "vector",
      url: `pmtiles://${tilesUrl}`,
      promoteId: { [SOURCE_LAYER]: "pid" },
    });
    map.addLayer({
      id: FILL,
      type: "fill",
      source: SOURCE,
      "source-layer": SOURCE_LAYER,
      paint: { "fill-color": paintFor(), "fill-opacity": 0.88 },
    });
    // A thin line in the background color separates neighboring lots.
    map.addLayer({
      id: LINE,
      type: "line",
      source: SOURCE,
      "source-layer": SOURCE_LAYER,
      minzoom: 14,
      paint: {
        "line-color": NEUTRAL[theme].outline,
        "line-width": ["interpolate", ["linear"], ["zoom"], 14, 0.3, 17, 1.2],
      },
    });
    // Thick outline around the selected lot, in the ink color so it reads
    // on every fill color.
    map.addLayer({
      id: "lots-selected",
      type: "line",
      source: SOURCE,
      "source-layer": SOURCE_LAYER,
      filter: ["==", ["get", "pid"], selected ?? -1],
      paint: { "line-color": theme === "dark" ? "#f0efec" : "#0b0b0b", "line-width": 3 },
    });
    applyFeatureState();
  }

  function applyFeatureState() {
    if (!latest || !map.getSource(SOURCE)) return;
    const { scenario, today } = latest;
    for (let pid = 0; pid < data.count; pid++) {
      const code = scenario.binding[pid];
      const modeled = code >= 0;
      map.setFeatureState(
        { source: SOURCE, sourceLayer: SOURCE_LAYER, id: pid },
        {
          max: modeled ? scenario.max[pid] ?? -1 : -1,
          net: modeled ? scenario.net[pid] ?? -1 : -1,
          added: modeled ? Math.max(0, (scenario.max[pid] ?? 0) - (today.max[pid] ?? 0)) : -1,
          bind: modeled ? groupOfCode[code] : -1,
          braw: code,
        },
      );
    }
  }

  function paintFor(): ExpressionSpecification {
    if (view === "max") return classExpression("max", MAX_UNITS_CLASSES, theme);
    if (view === "net") return classExpression("net", NET_NEW_CLASSES, theme);
    if (view === "added") return classExpression("added", ADDED_CLASSES, theme);
    return bindingExpression(theme, highlight);
  }

  map.on("click", FILL, (e) => {
    // The id can arrive as a number or a numeric string depending on how
    // the tile encoded `pid`, so convert explicitly.
    const pid = Number(e.features?.[0]?.id);
    if (Number.isInteger(pid)) clickHandlers.forEach((h) => h(pid, e.lngLat));
  });
  map.on("mouseenter", FILL, () => (map.getCanvas().style.cursor = "pointer"));
  map.on("mouseleave", FILL, () => (map.getCanvas().style.cursor = ""));

  // Follow the OS light/dark setting. Switching basemaps replaces the whole
  // style, so our layers and feature state are added again afterwards.
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    const next = currentTheme();
    if (next === theme) return;
    theme = next;
    map.once("style.load", addLotLayers);
    map.setStyle(BASEMAPS[theme]);
  });

  const controller: MapController = {
    map,
    setView(next, highlightCode = null) {
      view = next;
      highlight = highlightCode;
      if (map.getLayer(FILL)) map.setPaintProperty(FILL, "fill-color", paintFor());
    },
    setResults(scenario, today) {
      latest = { scenario, today };
      applyFeatureState();
    },
    onLotClick(handler) {
      clickHandlers.push(handler);
    },
    select(pid) {
      selected = pid;
      if (map.getLayer("lots-selected")) map.setFilter("lots-selected", ["==", ["get", "pid"], pid ?? -1]);
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
      addLotLayers();
      resolve(controller);
    });
  });
}
