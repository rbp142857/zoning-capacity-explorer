// Entry point: load the data, draw the map, wire up the controls.

import maplibregl from "maplibre-gl";

import "./style.css";
import { BINDING_LABELS } from "./colors";
import { bindingOf, loadParcels, type ParcelData } from "./data";
import { renderLegend } from "./legend";
import { createMap, currentTheme, type View } from "./map";

const CITY = "pasadena";
// import.meta.env.BASE_URL is "./" (see vite.config.ts), so these work
// whether the site is served at / or at /<repo-name>/ on GitHub Pages.
const DATA_URL = `${import.meta.env.BASE_URL}data/${CITY}/parcels.json`;
const TILES_URL = new URL(`${import.meta.env.BASE_URL}data/${CITY}/parcels.pmtiles`, window.location.href).href;

const fmt = new Intl.NumberFormat("en-US");
const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;

function showHeadline(data: ParcelData) {
  const h = data.headline;
  $("stat-existing").textContent = fmt.format(h.existing_units);
  $("stat-max").textContent = fmt.format(h.max_units);
  $("stat-local").textContent = `${fmt.format(h.local_units)} under city zoning alone`;
  $("stat-single").textContent = `${Math.round(h.single_home_land_share * 100)}%`;
  $("not-modeled-note").textContent =
    `${fmt.format(h.lots_not_modeled)} lots in specific plans and planned developments are not modeled yet (shown in light gray).`;
}

function popupHtml(data: ParcelData, pid: number): string {
  const c = data.columns;
  const zone = c.zone[pid] >= 0 ? data.codes.zone[c.zone[pid]] : "unknown";
  const binding = bindingOf(data, pid);
  const n = (v: number | null) => (v === null ? "unknown" : fmt.format(v));
  const header = `<h3>Lot ${c.parcel_id[pid]}</h3><div>Zone <strong>${zone}</strong> · ${fmt.format(c.lot_area_sqft[pid])} sq ft</div>`;
  if (binding === null) {
    return `<div class="popup">${header}<p class="limit">This zone isn't modeled yet (specific plan or planned development).</p></div>`;
  }
  return `<div class="popup">${header}
    <dl>
      <dt>Homes today</dt><dd>${n(c.existing_units[pid])}</dd>
      <dt>Allowed by city zoning</dt><dd>${n(c.local_units[pid])}</dd>
      <dt>Allowed with state law</dt><dd><strong>${n(c.max_units[pid])}</strong></dd>
      <dt>New homes possible</dt><dd>${n(c.net_new_units[pid])}</dd>
    </dl>
    <div class="limit"><span class="visually-hidden">Limited by: </span>Limit: ${BINDING_LABELS[binding] ?? binding}</div>
  </div>`;
}

async function main() {
  const status = $("status");
  try {
    const data = await loadParcels(DATA_URL);
    showHeadline(data);

    const controller = await createMap("map", data, TILES_URL);
    status.textContent = "";

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
      renderLegend(legend, data, view, currentTheme(), code === null ? null : data.codes.binding[code]);
    };
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
    controller.onLotClick((pid, lngLat) => popup.setLngLat(lngLat).setHTML(popupHtml(data, pid)).addTo(controller.map));
  } catch (err) {
    status.textContent = `Couldn't load the map data. ${(err as Error).message}`;
    console.error(err);
  }
}

main();
