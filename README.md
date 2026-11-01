# Zoning Capacity Explorer

An open-source tool that shows what zoning legally allows on every parcel in a
city, and how much housing a proposed rule change would enable. Cities so far:
**Pasadena** (the pilot), **Glendale** and **Burbank**, California. Pick a city in
the site's header, or link to one with `?city=burbank`.

**Live site: <https://rbp142857.github.io/zoning-capacity-explorer/>**

New to the code? Start with the **[beginner's guide](docs/BEGINNER_GUIDE.md)**.

> **Disclaimer:** this is an estimate for research and advocacy, not legal or
> zoning advice. Always confirm with the city before relying on it.

## Status

| Milestone | State |
|---|---|
| 1. Pilot city research | ✅ Pasadena chosen |
| 2. Data pipeline + data quality report | ✅ built |
| 3. Rule files + capacity engine | ✅ 16 zones, state law (SB 9, ADU, AB 2097), 69 tests |
| 4. Static map | ✅ MapLibre + PMTiles, 3 views, legend, deploy workflow |
| 5. Scenario engine in the browser | ✅ 9 levers, shareable links, Python/TypeScript parity test |
| 6. Charts, lot details, address search, printable summary | ✅ |
| 7. Realistic redevelopment estimate | ✅ 5 screens, shown beside theoretical everywhere |
| 8. Validation, methodology, deploy | ✅ live on GitHub Pages |
| 9. Developer pro forma (optional) | planned |
| LA County expansion | ✅ multi-city pipeline and site; Glendale and Burbank added. Next: [wave plan](docs/WAVE_PLAN.md) |

Reports: [data quality](reports/pasadena/quality_report.md) ·
[capacity](reports/pasadena/capacity_report.md) ·
[validation](reports/pasadena/validation.md) ·
method: [METHODOLOGY.md](METHODOLOGY.md) ·
[hand-checked lots](docs/HAND_CHECKS.md) ·
new city: [ADDING_A_CITY.md](ADDING_A_CITY.md) ·
**[beginner's guide](docs/BEGINNER_GUIDE.md)**

## How it fits together

```
cities/pasadena/city.yaml        where the data comes from, which CRS to measure in
        │
        ▼  make download         ArcGIS layers + GTFS → data.nosync/raw/pasadena/
        ▼  make clean            adapters → spatial joins → flags
data.nosync/clean/pasadena/parcels.parquet   one row per lot, zoning attached
reports/pasadena/quality_report.md           counts of every flag (committed)
        │
cities/pasadena/rules/*.yaml     one file per zone, every value cited
cities/_california/state_overrides.yaml      SB 9, ADUs, AB 2097, ...
        ▼  make capacity         engine: min over constraints, then state law
data.nosync/out/pasadena/capacity.parquet    max units, binding constraint per lot
reports/pasadena/capacity_report.md          totals by zone, district, transit
        ▼  make export           tippecanoe + JSON
web/public/data/pasadena/parcels.pmtiles     lot shapes (committed, ~4 MB)
web/public/data/pasadena/parcels.json        numbers + engine inputs per lot (committed, ~1.6 MB, ~340 kB gzipped)
web/public/data/pasadena/rules.json          rule files + state law for the browser engine
web/public/data/pasadena/addresses.json      address search index (loaded on first search)
        ▼  make golden           Python answers for 415 lots x 9 scenarios
shared/fixtures/golden.json                  the browser engine must match these exactly
        ▼  web/ (Vite + TypeScript + MapLibre)  static site, no server
```

- `pipeline/src/zce/adapters/`: turn each publisher's format into our common
  columns. `la_assessor.py` is shared by every LA County city.
- `pipeline/src/zce/spatial.py`: parcel ↔ zone (largest overlap), parcel ↔
  council district and specific plan.
- `pipeline/src/zce/transit.py`: transit stops and distance from each lot to the nearest one.
- `pipeline/src/zce/clean.py`: runs it all and adds flags. Lots are flagged, never dropped.
- `pipeline/src/zce/rules/schema.py`: what a rule file may contain (Pydantic).
- `pipeline/src/zce/engine/`: the zoning math, with no GIS imports. `constraints.py`
  has one function per constraint; `capacity.py` combines them and applies state law.
- `pipeline/src/zce/capacity_step.py`: runs the engine over every lot.
- `pipeline/src/zce/export_web.py`: writes the website's tiles and data.
- `pipeline/src/zce/engine/scenario.py`: reform levers applied to copies of the rules.
- `web/src/engine/`: the same engine and scenario logic in TypeScript, so the
  browser recalculates every lot (~30 ms) when a lever changes.
  `parity.test.ts` checks it against `shared/fixtures/golden.json`.
- `web/src/`: the site. `map.ts` (layers and coloring), `colors.ts` (palettes and
  classes), `legend.ts`, `url.ts` (scenario ↔ shareable link), `charts.ts` and
  `summary.ts` (bar charts by district and transit distance), `details.ts` (lot
  panel with code citations), `search.ts` (address search), `print.ts`
  (one-page summary), `main.ts` (wires it together).

## Running it locally

You need [uv](https://docs.astral.sh/uv/) (`pip install uv`), `make`,
[tippecanoe](https://github.com/felt/tippecanoe) (`brew install tippecanoe`) for the
map tiles, and Node.js 16 or newer for the website.

```bash
make setup
```

```bash
make all CITY=pasadena
```

```bash
make test
```

To run the website locally (after `make all`, or using the committed data):

```bash
cd web && npm install && npm run dev
```

Then open the address Vite prints (http://127.0.0.1:5173 by default).

**Validation** (`make validate`) compares the results with official figures. Two of
its sources are on servers that refuse automated downloads; `make download`
prints their links and where to save them (open the link in a browser, save the
file there, run `make validate` again).

`make test` runs the Python tests and the web tests (including the parity
test). If you change the engine, a rule file or `zce/golden.py`, run
`make golden` and commit the new `shared/fixtures/golden.json`;
`test_golden.py` fails until you do.

**npm and iCloud:** `web/node_modules` is a link to `web/node_modules.nosync`
(so iCloud doesn't sync it). `npm install` can replace the link with a real
folder; if that happens, run
`cd web && rm -rf node_modules.nosync && mv node_modules node_modules.nosync && ln -s node_modules.nosync node_modules`.

The download is about 120 MB and takes a minute or two. Raw data is never
committed; `make download` fetches it again and records dates in
`data.nosync/raw/pasadena/_manifest.json`.

**Why `.nosync`?** This repo lives on an iCloud-synced Desktop. iCloud skips
folders ending in `.nosync`, which keeps 100+ MB of data out of iCloud, and
it avoids a real bug: iCloud marks files in synced `.venv` folders as hidden,
and Python ignores hidden `.pth` files, so `import zce` fails. The Makefile
points uv at `pipeline/.venv.nosync` for that reason.

## Deploying

The site is plain static files. `.github/workflows/deploy.yml` builds `web/`
and publishes it to GitHub Pages on every push to `main`. One-time setup in
the GitHub repo: **Settings → Pages → Source: GitHub Actions**. The map data
is committed, so CI never runs the Python pipeline; re-run `make all` locally
and commit when the data or rules change.

## Privacy

The tool is about rules and land, not about who owns a house. The LA County
Assessor layer we use contains no owner names (California law restricts
publishing them), and our adapter keeps only an explicit **whitelist** of
columns, so any personal field the county might add later is dropped
automatically. A test checks this. Property (situs) addresses are kept for
address search; owner mailing addresses are never used.

## Data sources

| Data | Publisher |
|---|---|
| Parcels, assessed values, buildings | Los Angeles County Office of the Assessor |
| Zoning, specific plans, council districts, city boundary | City of Pasadena |
| Major transit stops (PRC 21064.3 / AB 2553) | SCAG, Connect SoCal 2024 (base year 2022) |
| Rail stations (GTFS) | LA Metro |
| Basemap | © OpenStreetMap contributors, via OpenFreeMap |

Exact URLs and license notes are in [cities/pasadena/city.yaml](cities/pasadena/city.yaml).

## License

Code: [MIT](LICENSE). Rule files (`cities/**/rules/`) and documentation: CC BY 4.0.

MIT lets anyone reuse the code for anything, including commercial tools,
which maximizes adoption by other cities and advocates. The tradeoff is that
someone could build a closed product on it. AGPL would force anyone who hosts
a modified version to publish their changes, but it scares off many
government and nonprofit users. CC BY on the rule files and methodology asks
for attribution, which is what you want for numbers people cite.
