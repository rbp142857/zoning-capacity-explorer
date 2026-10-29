# Adding a city

The pipeline is built so a new city mostly means **new rule files and a small
zoning adapter**. This guide walks through it, using a second Los Angeles
County city as the example (the parcel adapter and California state law are
already done). Budget most of your time for step 4: reading the zoning code.

## 0. Check the data exists (an afternoon)

You need, at minimum:

- **Parcels** with lot shapes and, ideally, existing units, building year and
  assessed values. In LA County the Assessor layer covers every city.
- **A zoning map** as GIS data (polygons with a zone code per area).
- **The zoning code text**, online (Municode, eCode360, the city's site).
- **Transit stops.** In Southern California, SCAG's major-transit-stops layer;
  elsewhere, compute from the agency's GTFS feed.
- **Licenses** that let you republish derived data. Write down what you find.

## 1. Create the city folder

```bash
mkdir -p cities/<city-id>/rules
```

Copy `cities/pasadena/city.yaml` to `cities/<city-id>/city.yaml` and edit it:

- `id`, `name`, `state`.
- `analysis_crs`: a projected coordinate system in feet or meters for the
  area (California: the State Plane zone, e.g. EPSG:2229 for LA County).
- `sources`: URLs for parcels, zoning, boundary, districts (whatever the city
  uses for neighborhoods or council districts), transit, plus validation
  sources (Housing Element, permits). For LA County parcels keep
  `adapter: la_assessor` and change the `where` filter to the city's
  `TaxRateCity` (the legal city, not the mailing city).
- `specific_plan_prefixes`, if the city's zone codes have them.
- `assumptions` and `redevelopment` thresholds: start with Pasadena's and
  revisit them for local conditions; explain any change in a comment.

Run `make download CITY=<city-id>` and check `data.nosync/raw/<city-id>/`.

## 2. Write the zoning adapter

Every city's zoning layer names its fields differently. Copy
`pipeline/src/zce/adapters/pasadena_zoning.py` to `<city>_zoning.py` and change
`load_zoning()` so it returns the same columns: `zone_code`, `zone_category`,
`specific_plan`, `base_zone`, `overlays` (a list), `overlay_unparsed`,
`zone_ordinance`. Rewrite `OVERLAY_PATTERN` for the city's overlay codes, and
add tests like `tests/test_pasadena_zoning.py`.

Then point `clean.py` at the new adapter. (Today it calls the Pasadena adapter
directly; the second city is the moment to pick the adapter from
`city.yaml`'s `adapter:` field instead. That's a small refactor worth doing
then, not before.)

Outside LA County you also need a **parcel adapter**: copy
`adapters/la_assessor.py`, keep its column **whitelist** idea (never a
blacklist, for privacy), and produce the same output columns.

## 3. Clean and read the quality report

```bash
make clean CITY=<city-id>
```

Open `reports/<city-id>/quality_report.md`. Before writing any rules, look at:

- **Lots by zone code:** this tells you which rule files matter most. Write
  rules for the zones covering most residential land first.
- **Unparsed overlays and category mismatches:** fix the adapter or note them.
- **Flags:** a large share of `no_zone` or `outside_city_limits` usually means
  a filter or coordinate-system mistake.

## 4. Write the rule files (most of the work)

One YAML file per zone in `cities/<city-id>/rules/`, following
`pipeline/src/zce/rules/schema.py`. Start from the Pasadena file most similar
in kind (single-family, multifamily, commercial).

For each zone, from the development-standards tables:

- Allowed housing types, and whether housing is allowed at all.
- Density: units per lot, units per acre, or lot area per unit, plus the
  code's rounding rule.
- Minimum lot size and width (for new lots).
- Setbacks, height and stories, lot coverage, floor-area ratio or floor-area
  formulas, required open space.
- Parking per unit, and guest parking.

Rules for writing them:

- **Cite every number** (`source:` key → `sources:` entry with section and URL).
- **Write down every judgment call** in `assumption:` next to the value:
  merged table cells, "see section X" cross-references, ranges you collapsed
  to one number, average stories for split height limits.
- **List what you left out** under `simplifications:`.
- Unsure whether a zone allows housing? Say so in the assumption, rather than
  guessing silently.

The schema rejects typos and unknown citation keys, so loading the rules is
itself a check:

```bash
cd pipeline && uv run python -c "from pathlib import Path; from zce.rules.schema import load_zone_rules; print(sorted(load_zone_rules(Path('../cities/<city-id>/rules'))))"
```

## 5. State law

California cities reuse `cities/_california/state_overrides.yaml`. For
another state, create `cities/_<state>/state_overrides.yaml` with that state's
preemption laws (each `modeled` or `not_modeled`, with citations), and add
engine support for any law that works differently from the existing ones.

## 6. Run capacity and check it by hand

```bash
make capacity export golden validate CITY=<city-id>
```

- Read `reports/<city-id>/capacity_report.md`. Do the binding constraints make
  sense for each zone? Any zone with 0 capacity you didn't expect?
- **Hand-check at least 10 real lots**, one or two per common zone, against
  the code text, as in `docs/HAND_CHECKS.md`, and add them to a test like
  `tests/test_real_parcels.py`.
- Read `reports/<city-id>/validation.md`: existing homes vs. official counts,
  the Housing Element sites, and recent permits.

## 7. Website and docs

- The site currently loads one city (`CITY` in `web/src/main.ts`, and the map
  center in `web/src/map.ts`). For a second city, make both come from a small
  per-city config, and add a city picker.
- Add a city section to METHODOLOGY.md: data sources with dates and licenses,
  every simplification, and the validation results.
- `make test` must pass, including the golden parity test.
