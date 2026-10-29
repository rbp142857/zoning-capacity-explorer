# Learning notes

Concepts used in this project, in roughly the order you meet them. Each has a
short explanation and a link to good documentation. This file grows with each
milestone.

---

## Milestone 2: data pipeline

### Python environments and uv
A *virtual environment* is a private folder of Python packages for one project,
so this project's GeoPandas version can't clash with another project's. `uv` is
a fast tool that creates the environment, installs packages listed in
`pyproject.toml`, and pins exact versions in `uv.lock`, so anyone who clones the
repo gets the same versions. `uv run <command>` runs a command inside the
environment without you having to "activate" it.
Docs: <https://docs.astral.sh/uv/guides/projects/>

### Parcels, the assessor roll, and APN/AIN
A *parcel* is a legally defined piece of land with its own tax ID. In LA County
the ID is the AIN (Assessor's Identification Number; the APN is the same number
with dashes). The *assessor roll* is the county's list of every parcel's taxable
value and building facts. We use it for lot shape, existing units, building
age, and land vs. improvement value.
Docs: <https://portal.assessor.lacounty.gov/>

### Condo "stacks"
The Assessor gives each condo *unit* its own AIN, and all units in a building
share one copy of the same polygon. Zoning applies to the land, not to units, so
we merge each stack into one lot by grouping on the polygon's exact shape. We
call `geometry.normalize()` first so two copies of the same shape drawn starting
at different corners still compare as equal, then compare their WKB (a compact
binary encoding of the geometry).
Docs: <https://shapely.readthedocs.io/en/stable/reference/shapely.normalize.html>

### Coordinate reference systems (CRS)
A CRS says what the numbers in a geometry mean. **EPSG:4326** is longitude and
latitude in *degrees*. It's the default for GeoJSON and GPS, but a degree isn't
a fixed length (one degree of longitude shrinks toward the poles), so you can't
measure area or distance in it. A *projected* CRS flattens part of the Earth
onto a grid measured in real units. We use **EPSG:2229** (California State
Plane Zone 5, US feet), designed for this part of Southern California, so
`geometry.area` is square feet and `distance` is feet. Rule of thumb: store
and exchange data in 4326, but `to_crs()` into a local projected CRS before
measuring anything. Measuring in the wrong CRS doesn't raise an error; it just
gives silently wrong numbers, which is why `distance_to_nearest_ft()` refuses
geographic CRSs.
Docs: <https://geopandas.org/en/stable/docs/user_guide/projections.html> ·
<https://epsg.io/2229>

### GeoPandas and GeoDataFrames
GeoPandas extends pandas: a `GeoDataFrame` is a DataFrame with a special
`geometry` column of Shapely shapes, plus a CRS. You get spatial methods
(`.area`, `.to_crs()`, `.representative_point()`) and spatial joins on top of
everything pandas can do.
Docs: <https://geopandas.org/en/stable/getting_started/introduction.html>

### Spatial joins
A normal join matches rows by equal keys. A *spatial join* matches rows by how
their shapes relate. We use three kinds:
- `gpd.sjoin(points, districts, predicate="within")`: which district each
  point is inside. We join a *representative point* rather than the whole lot,
  because a point is inside exactly one district. Unlike a centroid, a
  representative point is guaranteed to be inside the polygon (the centroid of
  an L-shaped lot can fall outside it).
- `gpd.overlay(parcels, zones, how="intersection")`: cuts every lot into
  pieces by zone, so we can measure which zone covers the *most* of each lot.
  This is more robust than a point test when city zoning lines and county
  parcel lines are a few feet apart.
- `gpd.sjoin_nearest(...)`: for each row, find the nearest feature on the
  other side, optionally returning the distance. `transit.distance_to_nearest_ft()`
  uses it to measure each lot's distance to transit.
Docs: <https://geopandas.org/en/stable/docs/user_guide/mergingdata.html> ·
<https://geopandas.org/en/stable/docs/reference/api/geopandas.sjoin_nearest.html>

### Spatial indexes
Comparing 30,000 lots against 1,000 stops naively is 30 million distance
calculations. A *spatial index* (an R-tree) groups shapes into nested boxes so
the computer can skip everything far away and only measure nearby candidates.
GeoPandas builds one automatically (`gdf.sindex`) and `sjoin`/`sjoin_nearest`
use it, which is why they're fast and a double for-loop isn't.
Docs: <https://geopandas.org/en/stable/docs/reference/sindex.html>

### ArcGIS REST services and pagination
Most US city and county GIS data is published through Esri ArcGIS servers. Each
layer has a URL, and appending `/query?where=...&f=geojson` returns features.
Servers cap each response (often at 1,000 features), so `download.py` *pages*
through results with `resultOffset`, sorted by the layer's ID field so pages
never overlap. It also checks the final count against `returnCountOnly`, so a
silently truncated download fails loudly.
Docs: <https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/>

### GeoJSON vs. GeoParquet
GeoJSON is human-readable text, which is great for exchange but large and slow
(our raw parcels are 117 MB). GeoParquet is the Parquet columnar format plus
geometry and CRS metadata. It's binary, compressed, keeps column types (an
integer stays an integer), and loads in a fraction of the time. Raw downloads
stay GeoJSON; everything we produce is GeoParquet.
Docs: <https://geoparquet.org/>

### GTFS
The General Transit Feed Specification is the standard format transit agencies
use to publish schedules: a zip of CSV files (`stops.txt`, `routes.txt`,
`stop_times.txt`, ...). We read only `stops.txt`. Rows with `location_type = 1`
are *stations* (parents that group platforms), so we get one point per Metro
station.
Docs: <https://gtfs.org/documentation/schedule/reference/#stopstxt>

### "Major transit stop" (California law)
California defines a major transit stop in Public Resources Code §21064.3: a
rail or BRT station, a ferry terminal, or the intersection of two bus routes
with frequent peak service (AB 2553 relaxed "frequent" from every 15 minutes to
every 20). State laws such as AB 2097 (no parking minimums within ½ mile of
one) use this definition, so we use SCAG's official inventory instead of
computing our own from GTFS.
Docs: <https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=PRC&sectionNum=21064.3> ·
<https://scag.ca.gov/high-quality-transit-areas>

### Whitelists vs. blacklists (privacy by design)
A blacklist says "drop these columns"; a whitelist says "keep *only* these."
With a blacklist, a new `OWNER_NAME` column added by the publisher next year
would leak into the published data. With a whitelist it can't. The test
`test_personal_columns_are_dropped` locks this behaviour in.

### Data validation with Pydantic
Pydantic turns a plain dict (here, parsed YAML) into a typed Python object and
raises a clear error if a field is missing, misspelled, or the wrong type.
`extra="forbid"` makes unknown keys an error, so a typo like `ulr:` in
`city.yaml` fails immediately. Milestone 3 uses Pydantic much more heavily for
the zoning rule files.
Docs: <https://docs.pydantic.dev/latest/concepts/models/>

### Flag, don't drop
When a record is incomplete (no zone, no building data), the tempting fix is
`dropna()`. That silently shrinks the city and biases every total. Instead,
each lot gets a list of flags, and the quality report counts them. Totals stay
honest, and users can see exactly what's uncertain.

### Testing with pytest
Test files are `tests/test_*.py`; any function named `test_*` is a test, and a
plain `assert` is the check. *Fixtures* (in `conftest.py`) build reusable
inputs; `@pytest.mark.parametrize` runs one test over many input/expected
pairs. Our tests use tiny hand-drawn boxes in feet so every expected number
can be checked on paper. *Markers* (`@pytest.mark.exercise`) let us skip
tests for an unfinished learning exercise by default.
Docs: <https://docs.pytest.org/en/stable/getting-started.html>

### Prop 13 and assessed values (a warning for milestone 7)
Under California's Proposition 13, a property's assessed value is reset to
market value only when it's sold, then can rise at most 2% a year. A house
bought in 1978 can show a land value far below market, so "improvement-to-land
value ratio", a common redevelopment heuristic elsewhere, is distorted here.
The roll's `land_base_year` column (kept in our data) tells us how stale each
value is.
Docs: <https://www.boe.ca.gov/proptaxes/prop13.htm>

---

## Milestone 3: rule files and the capacity engine

### Rules as data, not code
Each zone's rules live in a YAML file (`cities/pasadena/rules/RS-6.yaml`)
instead of `if zone == "RS-6":` branches in Python. Data can be read by people
who don't code, diffed in git when the city amends its code, validated
automatically, and loaded by the browser later. The engine stays generic: it
knows what a "lot-area-per-unit rule" is, not what RS-6 is.
Docs (YAML basics): <https://learnxinyminutes.com/docs/yaml/>

### Pydantic generics and validators
`Sourced[float]` is a *generic* model: one class definition, `Sourced[T]`,
that holds a value of any type `T` plus a citation. `model_validator` runs a
check over the whole object after parsing; ours walks the rule file and fails
if any `source:` key is missing from `sources:`. `extra="forbid"` means a
misspelled field is an error instead of being silently ignored.
Docs: <https://docs.pydantic.dev/latest/concepts/models/#generic-models> ·
<https://docs.pydantic.dev/latest/concepts/validators/#model-validators>

### Lookup tables as "bands"
Zoning is full of tables keyed on lot size or width ("lots under 12,000 sf:
30% of the lot plus 500 sf"). `Banded` stores such a table as a list of
bands, each applying below an upper bound, and `.pick()` finds the band for a
lot. One small structure covers coverage, floor area, height, stories,
garden space and Pasadena's small-lot density table.

### Binding constraint (the min over constraints)
Each rule gives its own maximum number of units; the legal maximum is the
*smallest* of them, and the rule that produced it is the **binding
constraint**. It's the most useful output for users: if parking binds,
upzoning density adds nothing until parking rules change. When two rules
tie, we report legal limits (density) before physical ones (envelope),
because a legal limit is what a reform would change.

### Rounding rules matter
Codes say how to round fractional units, and they differ: Pasadena rounds
RM-16 up only above .75, and RM-32/RM-48 to the nearest unit. `round_units()`
implements each mode, with a tiny tolerance because floating-point math can
turn 3.0 into 2.9999999.
Docs (why 0.1 + 0.2 != 0.3): <https://docs.python.org/3/tutorial/floatingpoint.html>

### Minimum rotated rectangle (lot width and depth)
Setbacks need a lot's width and depth, but the data only has polygons. The
*minimum rotated rectangle* is the smallest box, at any angle, that contains
the polygon. Its short side approximates frontage (width) and its long side
depth. For irregular lots we multiply by a shape factor (lot area / box area)
so the lot isn't credited with land it doesn't have.
Docs: <https://shapely.readthedocs.io/en/stable/reference/shapely.oriented_envelope.html>

### State preemption
California's legislature can override city zoning for housing. SB 9 lets
owners build two homes on most single-family lots and split the lot once;
ADU law adds a backyard unit and a junior unit; AB 2097 bans parking minimums
near major transit. The engine computes the local answer first, then each
state "path", and keeps both, so users can see how much capacity comes from
Sacramento rather than City Hall.
Docs: <https://www.hcd.ca.gov/planning-and-community-development/accessory-dwelling-units> ·
<https://www.hcd.ca.gov/policy-and-research/sb9>

### Theoretical vs. realistic capacity
The numbers in `capacity_report.md` are **theoretical**: what the rules allow
if every lot were rebuilt to the maximum. Almost none will be. Milestone 7
adds a separate "likely to redevelop" estimate. Reading theoretical capacity
as a forecast is the most common mistake made with tools like this.

### Dataclasses
`Lot` and `EngineAssumptions` are `@dataclass(frozen=True)` classes: Python
writes the `__init__` for you, and `frozen=True` makes them read-only, so a
constraint function can't accidentally change the lot another function sees.
Docs: <https://docs.python.org/3/library/dataclasses.html>

---

## Milestone 4: the map

### Vector tiles and PMTiles
A web map can't download 30,000 lot shapes at once on a phone. *Vector tiles*
cut the data into square tiles per zoom level, so the browser loads only the
tiles on screen, simplified for that zoom. **PMTiles** packs all the tiles
into one file. The browser asks for just the bytes of the tiles it needs
using HTTP *range requests* (`Range: bytes=1000-2000`), so any static host
works and no tile server is needed. `tippecanoe` builds the file from GeoJSON.
Docs: <https://docs.protomaps.com/pmtiles/> · <https://github.com/felt/tippecanoe>

### Geometry and numbers kept apart
The tiles hold only each lot's shape and its `pid`. Everything the map shows
lives in `parcels.json`, one array per field, where element *i* belongs to
lot *i*. In milestone 5 the browser will recompute those numbers for a reform
scenario without touching the tiles.

### MapLibre GL JS, expressions and feature state
MapLibre draws vector tiles with WebGL. Layer colors are *expressions*, small
JSON programs like `["step", value, color0, 2, color1, 3, color2]` that
MapLibre runs for every feature on the GPU-friendly side. `promoteId` tells
MapLibre to use the `pid` property as each feature's id; `setFeatureState(id,
{max: 4})` attaches a number to it; `["feature-state", "max"]` reads it in an
expression. Changing a view only swaps the expression.
Docs: <https://maplibre.org/maplibre-style-spec/expressions/> ·
<https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#setfeaturestate>

### Color-blind-safe map colors
- **Amounts** (homes allowed) use one hue, light to dark, split into a few
  classes. A rainbow would suggest categories that aren't there.
- **Categories** (what limits a lot) use distinct hues, but on a map every
  color can touch every other, so only a few hues stay distinguishable for
  people with color-vision deficiency. We checked ours with a validator that
  simulates color blindness (it computes color differences, rather than
  trusting our eyes), and cap the map at three hues plus grays. Finer detail
  comes from "Highlight one limit".
- Color is never the only channel: every legend row has a label and a count,
  and clicking a lot gives the numbers in words.
Docs: <https://jfly.uni-koeln.de/color/> (Okabe & Ito, "Color Universal Design")

### Light and dark mode
CSS custom properties (`--surface`, `--ink`) hold the colors; a
`prefers-color-scheme: dark` media query swaps them, and the map switches to
a dark basemap. Dark mode reverses the blue ramp, so small values sit close
to the dark background and large values stand out.
Docs: <https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme>

### Vite and TypeScript
TypeScript is JavaScript with type annotations. `tsc --noEmit` checks them
without producing files, catching mistakes like passing a string where a
number is expected. Vite serves the site during development (reloading on
save) and bundles it into `web/dist` for deployment. `base: "./"` makes asset
paths relative, so the site works under GitHub Pages' `/<repo-name>/` path.
Docs: <https://vitejs.dev/guide/> · <https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html>

### Static hosting and GitHub Actions
GitHub Pages serves plain files for free. A GitHub Actions *workflow*
(`.github/workflows/deploy.yml`) runs on GitHub's servers on every push:
install, build, upload `web/dist`, publish. A second workflow runs the tests.
Docs: <https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages>

---

## Milestone 5: scenarios in the browser

### Same logic, two languages, one test
The engine exists in Python (the pipeline, the source of truth) and in
TypeScript (so the browser can recompute instantly without a server). Two
copies of the same logic will drift apart unless something checks them. A
**golden test** does: Python computes answers for a fixed set of inputs and
saves them (`shared/fixtures/golden.json`); the TypeScript test runs the same
inputs and fails on any difference. A second Python test fails if the golden
file is stale, so a change on the Python side forces you to regenerate it.
Docs: <https://en.wikipedia.org/wiki/Characterization_test>

### Testing the test (mutation testing, by hand)
A test that can't fail is worthless. We deliberately broke the TypeScript
rounding rule (0.75 -> 0.70) and confirmed the parity test went red, then
put it back. Tools like Stryker automate this idea.
Docs: <https://stryker-mutator.io/docs/>

### Floating-point and rounding at boundaries
Python and JavaScript both use IEEE-754 doubles, so the same operations in
the same order give the same bits. Where we round (lot dimensions to 0.1 ft
before export), we round *once in the pipeline* and have both engines use
the rounded values; rounding in only one place changed 10 lots' answers.

### Never mutate the rules
A scenario makes modified **copies** of the rules (`model_copy(update=...)`
in Python, `{...rules, ...changes}` in TypeScript) instead of editing them.
The "today" results and every scenario start from the same untouched rules,
so switching scenarios back and forth can't leave stale changes behind.
Docs: <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Spread_syntax>

### State in the URL
The scenario lives in the URL's `#hash` (`#v=1&sf=4&pk=0`), so sharing the
address shares the scenario, and the back button and bookmarks work. Only
changed levers are written; unknown or invalid values fall back to today's
rules, so a mistyped or old link never breaks the page. `v=1` is a version
number for when the lever set changes. `history.replaceState` updates the
address without adding a history entry on every click.
Docs: <https://developer.mozilla.org/en-US/docs/Web/API/History/replaceState> ·
<https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams>

### Vitest
Vitest is a test runner for TypeScript that understands Vite projects.
`describe`/`it`/`expect` play the role of pytest's test functions and
`assert`.
Docs: <https://vitest.dev/guide/>
