// The map: basemap, lot shapes from PMTiles, and colors from parcels.json.
//
// How coloring works: every lot shape in the tiles has a `pid`. We tell
// MapLibre to use it as the feature id (`promoteId`), then attach numbers to
// each id with `setFeatureState`. The paint rules read those numbers with
// ["feature-state", ...]. Changing views or (in milestone 5) scenarios only
// changes feature state or paint rules; the tiles are never re-downloaded.

import maplibregl, { type ExpressionSpecification, type Map as MlMap } from "maplibre-gl";
import { Protocol } from "pmtiles";
import "maplibre-gl/dist/maplibre-gl.css";

import {
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

export type View = "max" | "net" | "binding";

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
  onLotClick(handler: (pid: number, lngLat: maplibregl.LngLat) => void): void;
}

export function createMap(container: string, data: ParcelData, tilesUrl: string): Promise<MapController> {
  let theme = currentTheme();
  let view: View = "max";
  let highlight: number | null = null;
  const clickHandlers: ((pid: number, lngLat: maplibregl.LngLat) => void)[] = [];

  const map = new maplibregl.Map({
    container,
    style: BASEMAPS[theme],
    center: [-118.135, 34.16], // Pasadena city hall, roughly
    zoom: 12.3,
    minZoom: 11,
    maxZoom: 18,
    attributionControl: { customAttribution: DATA_ATTRIBUTION, compact: true },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "imperial" }), "bottom-left");

  // Group index per binding-constraint code, so feature state can hold a small number.
  const groupOfCode = data.codes.binding.map((name) =>
    BINDING_GROUPS.findIndex((g) => g.members.includes(name)),
  );

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
    applyFeatureState();
  }

  function applyFeatureState() {
    const c = data.columns;
    for (let pid = 0; pid < data.count; pid++) {
      const code = c.binding[pid];
      map.setFeatureState(
        { source: SOURCE, sourceLayer: SOURCE_LAYER, id: pid },
        {
          max: code < 0 ? -1 : c.max_units[pid] ?? -1,
          net: code < 0 ? -1 : c.net_new_units[pid] ?? -1,
          bind: code < 0 ? -1 : groupOfCode[code],
          braw: code,
        },
      );
    }
  }

  function paintFor(): ExpressionSpecification {
    if (view === "max") return classExpression("max", MAX_UNITS_CLASSES, theme);
    if (view === "net") return classExpression("net", NET_NEW_CLASSES, theme);
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
    onLotClick(handler) {
      clickHandlers.push(handler);
    },
  };

  return new Promise((resolve) => {
    map.once("load", () => {
      addLotLayers();
      resolve(controller);
    });
  });
}
