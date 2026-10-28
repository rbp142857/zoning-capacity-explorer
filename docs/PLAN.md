# Zoning Capacity Explorer — Plan

## Context

Zoning rules sit in legal PDFs, so almost nobody can answer "what can be built on this lot?" or "how much housing would a fourplex reform enable?". This project turns one city's zoning into validated, cited rule files, runs a per-parcel capacity engine in Python, and ships a static map site that recalculates reform scenarios in the browser. Audiences: residents and activists, planning staff, and small builders. The owner is learning Python, so the code stays readable, decisions get explained, and some core functions are set aside for them to write first.

The working folder is currently empty (a temporary folder the app made). **Step 0:** move the session to a real project folder and `git init` before any code is written.

---

## Milestone 1: Pilot city (decided: one mid-size city in LA County)

Decisions so far: LA County, one mid-size city first. Vite + plain TS + MapLibre on GitHub Pages. MIT for code, CC BY 4.0 for docs and rule files. Project folder: `~/Desktop/zoning-capacity-explorer`.

**Why one city and not the whole county:** LA County has 88 city codes plus Title 22, across about 2.4M parcels. One city keeps the payload small enough for phones and the rule files manageable. The design keeps the parts shared across LA County separate, so each further city mostly means new rule files and a zoning adapter.

**Shared county layer (written once, reused for every LA County city):**
- **LA County Assessor parcel roll:** land and improvement values, year built, units, building sq ft, use code. It's about 2.4M records, filtered to the city boundary. State law already withholds owner names. We still whitelist columns.
- **LA Metro GTFS** (open), plus city transit (Pasadena Transit or Big Blue Bus).
- **California state overrides** in `cities/_california/state_overrides.yaml`: SB 9 (two units plus a lot split in single-family zones), state ADU/JADU law, AB 2097 (no parking minimums within ½ mile of a "major transit stop", PRC 21064.3), and SB 79 (2025 transit-oriented upzoning; effective date and details to verify). State density bonus law is noted but left out of the MVP (flagged).
- **Validation:** the state HCD Housing Element site inventory data plus the city's own Housing Element appendix.

**Important California caveat for M7:** under Prop 13, assessed values reflect the purchase year, not market value. A long-held house shows a tiny land value, so improvement-to-land ratios are skewed. The realistic estimate will lean on building age and the share of capacity already used, and METHODOLOGY will explain why.

**Final city check (the first task after approval; then I stop for your pick).** About 30 minutes of read-only checks on two candidates:

| | **Pasadena** | **Santa Monica** |
|---|---|---|
| Size | ~140k people, larger | ~90k people, smaller payload |
| Zoning GIS | City ArcGIS "Zoning" FeatureServer (base, overlay, and 7 specific plans) | data.santamonica.gov (zoning layer still to confirm) |
| Transit | Metro A Line (several stations) | Metro E Line (3 stations) plus Big Blue Bus |
| Preemption story | Fought SB 9 in historic districts; strong state-vs-city angle | Ongoing Housing Element / "builder's remedy" history |
| Risk | Specific plans cover most corridors, so more rule files | Specific plans (Downtown, Bergamot) too |

What I'll check for each: the zoning layer's date and fields, whether the code is readable online, whether a Housing Element site inventory exists, and how well assessor parcels join to zoning. Then I'll send you a recommendation and wait for your decision.

---

## Architecture (with pushback)

```
zoning-capacity-explorer/
  pipeline/                  # Python package (managed with uv)
    zce/engine/              # pure functions, no GIS imports: constraints.py, scenario.py, redevelop.py
    zce/rules/schema.py      # Pydantic models for rule files
    zce/adapters/la_assessor.py  # shared LA County parcel roll → common schema
    zce/adapters/<city>.py       # city zoning layer → zone codes
    zce/spatial.py           # GeoPandas joins: parcel↔zone, parcel↔transit distance, neighborhood
    zce/report.py            # data-quality report (flagged parcels, counts)
    tests/                   # pytest; hand-calculated parcels
  cities/_california/state_overrides.yaml
  cities/<city>/
    rules/*.yaml             # one file per zone; every value has a `source`
    # (state overrides live in _california, applied after local rules)
    city.yaml                # data URLs, CRS, assumed unit size, etc.
  shared/fixtures/golden.json# sample parcels + scenarios + expected results (used by BOTH Python and JS tests)
  web/                       # Vite + plain TypeScript, MapLibre GL JS, PMTiles
  Makefile                   # make download / clean / capacity / tiles / site
  docs: README, METHODOLOGY, ADDING_A_CITY, LEARNING, LICENSE
```

Key decisions:
- **Engine with no GIS imports.** Spatial work (joins, distances) happens once in the pipeline and gives each parcel plain numbers such as `lot_area_sqft`, `dist_to_frequent_transit_m`, `zone`. The engine only does arithmetic, so it's easy to read and test.
- **Plain TypeScript in the browser, not DuckDB-WASM.** Recomputing ~30–60k parcels with typed arrays takes well under 50 ms. DuckDB-WASM adds a multi-MB download for no gain at this size. If a 500k-parcel city comes later, we look at this again.
- **Geometry and attributes are kept apart.** PMTiles carries only the parcel polygons and their IDs. A separate small columnar file (`parcels.bin` or JSON) carries the numbers the scenario math needs. The map colors parcels through MapLibre `feature-state`, so a scenario change never rebuilds tiles.
- **One spec, two implementations, one shared test.** The scenario math exists in Python and in TS. `golden.json` is generated by Python, and a vitest test asserts the TS output matches it on a sample of a few hundred parcels plus the hand-made edge cases. CI fails if they drift.
- **No frontend framework (React and similar).** Vite + plain TS keeps the learning surface small. The UI is a map, a panel, a few controls, and charts (Observable Plot, small and accessible).
- **Hosting: GitHub Pages.** It's free, deploys from the repo with Actions, and supports HTTP range requests (which PMTiles needs). Target: initial payload under 3 MB.
- **Privacy:** the adapter whitelists columns (it never drops a blacklist), so owner and mailing fields cannot leak even if the source adds new ones. A test asserts that no published column matches a PII pattern.
- **License suggestion:** MIT for code (simplest, maximum reuse). CC BY 4.0 for rule files and docs (asks for citation, which fits a methodology people cite). Alternative: AGPL if you want forks of the site to stay open. I'll explain the tradeoffs in the README.

### Capacity math (engine core)
For each parcel, `max_units = min(...)` over:
1. **Density:** units per lot, or `floor(acres × units_per_acre)`
2. **Lot area per unit:** `floor(lot_area / min_lot_area_per_unit)`. If the lot is below the minimum lot size, the result is 0 or "nonconforming" (flagged)
3. **Envelope:** `footprint = min((lot_w − side setbacks)×(lot_d − front − rear), lot_area × coverage)`; `floor_area = min(footprint × stories, lot_area × FAR)`; `units = floor(floor_area × efficiency / avg_unit_size)`. When lot dimensions are missing, approximate with a square or rectangle of the same area (assumption recorded)
4. **Parking:** `units` such that `footprint_used + units × parking_ratio × stall_area ≤ lot_area` (surface parking assumption, stated)
5. **Use permitted:** 0 if residential isn't allowed

The result records `binding_constraint` (the argmin, with a tie order documented) plus `existing_units`, `net_new = max(0, max_units − existing)`, and `flags[]`. State overrides (for example ADUs) apply after local rules and are labeled as such.

**Realistic estimate (M7):** a transparent score using improvement-to-land ratio, building age, and the share of allowed capacity already used. It's shown as "parcels most likely to redevelop" and never framed as a forecast. The thresholds are in `city.yaml`.

**Scenarios:** a small JSON object (lever values) encoded in the URL hash, versioned (`v=1`).

---

## Milestones

1. **City research.** Above; your decision.
2. **Pipeline.** Download → clean → whitelist columns → spatial joins (zone, neighborhood, transit distance) → GeoParquet, plus `quality_report.md` (missing data, unmatched zones, flagged counts). 🧑‍🎓 *You write:* the function that computes distance to the nearest frequent-transit stop (after I explain CRS and projection).
3. **Rule files + engine.** Pydantic schema; YAML for the single-family, multifamily and main commercial/mixed-use zones covering most residential land; constraint functions with pytest. 🧑‍🎓 *You write:* `lot_area_per_unit_limit()` and `envelope_limit()` from my spec and hand-calculated test cases. I review.
4. **Static map.** PMTiles + MapLibre, colored by current capacity or binding constraint, color-blind-safe palettes, disclaimer banner, deployed to Pages.
5. **Scenario engine in TS + levers + URL sharing + golden test.** 🧑‍🎓 *You write:* the URL encode/decode functions.
6. **UI:** charts by neighborhood and transit distance, parcel panel with citations, address search (local index of addresses, no geocoding API), printable summary (print CSS), keyboard and accessibility pass. 🧑‍🎓 *You write:* one chart.
7. **Realistic redevelopment estimate.**
8. **METHODOLOGY / ADDING_A_CITY**, validation against the official figures, 10 hand-checked real parcels, final deploy.
9. *(Optional)* **Pro forma.**

Each milestone ends with: a summary, "what to understand", exercises, open questions, and a commit. `LEARNING.md` grows each milestone.

## Verification
- `make test`: pytest (every constraint, with hand-calculated parcels; sanity checks: no negative capacity, flagged parcels counted and never dropped) plus vitest (golden parity Python↔TS).
- `make all` reproduces the outputs from a clean clone (raw data is downloaded, never committed).
- Manual: 10 real parcels checked against the municipal code; totals compared with the Housing Element site inventory in METHODOLOGY.
- Browser: Lighthouse mobile performance and accessibility checks; keyboard-only walkthrough.
