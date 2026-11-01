# Beginner's guide to the Zoning Capacity Explorer

Written for someone working through **CS50P** who wants to understand this
project from the ground up: what it does, how to use it, how every piece of
code works, and how a project like this gets built. You don't need to read it
all at once. Each part stands on its own.

**Contents**

1. [Use the tool](#1-use-the-tool) (no code)
2. [The big idea in one picture](#2-the-big-idea-in-one-picture)
3. [Set up your computer to explore the code](#3-set-up-your-computer)
4. [A tour of the folders](#4-a-tour-of-the-folders)
5. [Follow one lot through the whole system](#5-follow-one-lot-through-the-whole-system)
6. [The code, matched to CS50P weeks](#6-the-code-matched-to-cs50p-weeks)
7. [Hands-on experiments](#7-hands-on-experiments), from easy to hard
8. [Things CS50P doesn't cover (yet)](#8-things-cs50p-doesnt-cover-yet)
9. [How this was built: the process](#9-how-this-was-built-the-process)
10. [Glossary](#10-glossary)

---

## 1. Use the tool

Open **<https://rbp142857.github.io/zoning-capacity-explorer/>**. Pick a city
(Pasadena or Glendale) in the header. Try these in order; each one shows a
different feature.

1. **Read the headline numbers** at the top of the left panel: homes today,
   the legal maximum, and the share of land where the city allows only one home.
2. **Switch the map colors** with "Color lots by":
   - *Homes allowed*: how many homes each lot could have.
   - *What limits it*: the rule that sets each lot's limit. Blue = state law,
     orange = city density rules, green = building size or parking. Try
     "Highlight one limit" → "Required parking takes the room".
3. **Search your favorite address** (or "100 N Garfield", City Hall) and press
   Enter. The map flies there and the **lot details panel** shows every limit,
   with links to the exact section of the zoning code.
4. **Try a reform.** Open "Reform scenario", click **Upzone near transit**.
   The totals change instantly, and the address bar changes too: copy it and
   open it in another tab, and you get the same scenario back. That's a
   shareable link.
5. **Compare theoretical vs. realistic.** Read "What's this?" next to
   *New homes on lots likely to redevelop*, then switch the charts to "Only on
   lots likely to redevelop". Notice that the fourplex reform barely moves the
   realistic number: the guide's section 9 explains why that's honest.
6. **Print** a one-page summary with the button near the bottom.

Questions to answer for yourself while exploring (good practice for thinking
like an analyst):

- Which council district has the most new-home capacity? Does that change
  under the transit scenario?
- Find a lot where parking is the limit. What happens to it when you set
  "Parking spaces required per home" to None?
- Why are some lots light gray? (Hint: specific plans.)

---

## 2. The big idea in one picture

Zoning rules are written as legal text. Parcels (lots) are GIS data. The tool
connects the two:

```
 ┌──────────────┐   ┌─────────────────┐   ┌───────────────────┐   ┌─────────────┐
 │ 1. DOWNLOAD  │ → │ 2. CLEAN + JOIN │ → │ 3. CAPACITY       │ → │ 4. WEBSITE  │
 │ public data  │   │ one row per lot │   │ rules + math      │   │ map, levers │
 │ (county,     │   │ with its zone,  │   │ = max homes and   │   │ recomputes  │
 │  city, state)│   │ district, etc.  │   │ what limits it    │   │ in browser  │
 └──────────────┘   └─────────────────┘   └───────────────────┘   └─────────────┘
   download.py        clean.py              engine/*.py              web/src/*.ts
                      spatial.py            rules/*.yaml
```

Each box is a separate step you can run on its own (`make download`,
`make clean`, `make capacity`, `make export`), and each step reads the files
the previous step wrote. That's called a **pipeline**. It means you can
change one step and re-run just that part, and every result can be traced
back to dated source files.

Two ideas make it trustworthy:

- **Rules are data, not code.** Each zone's numbers live in a YAML file with a
  citation for every value (`cities/pasadena/rules/RS-6.yaml`). The Python code
  doesn't know what "RS-6" is; it only knows how to apply *any* rule file.
- **The math is pure functions.** The engine (`pipeline/src/zce/engine/`)
  takes plain numbers in and gives numbers out. No maps, no files, no
  internet. That's why it's easy to test with a calculator.

---

## 3. Set up your computer

You'll use the **Terminal** (a text window where you type commands). Each
command below is one line you paste in and press Enter.

**Step 1. Make `uv` available everywhere.** `uv` is the tool that manages
this project's Python and its libraries. It's installed but not on your
"PATH" (the list of folders your terminal searches for programs). Your
terminal uses `bash`, so add one line to `~/.bash_profile`:

```bash
echo 'export PATH="$HOME/Library/Python/3.15/bin:$PATH"' >> ~/.bash_profile
```

Then close and reopen the terminal. Check it worked:

```bash
uv --version
```

**Step 2. Go to the project folder.**

```bash
cd ~/Desktop/zoning-capacity-explorer
```

**Step 3. Run the tests.** This proves everything works on your machine
(about 170 checks, a few seconds):

```bash
make test
```

**Step 4. Run the website on your own computer.**

```bash
make site
```

Open the address it prints (http://127.0.0.1:5173). Edit a file in
`web/src/` and the page reloads by itself. Press Ctrl-C in the terminal to stop it.

**Step 5. Open the code in an editor.** [VS Code](https://code.visualstudio.com/)
is free and what CS50 uses. Open the folder with File → Open Folder. Install
its Python extension; then you can hover over any function to see what it is,
and Cmd-click to jump to where it's defined. That's the fastest way to
explore a codebase.

**Step 6. Ask Python questions directly.** This opens a Python prompt where all
the project's code can be imported:

```bash
make repl
```

Paste this in, line by line. It computes one real lot (2314 E Mountain St):

```python
from zce.config import load_city
from zce.rules.schema import load_zone_rules, load_state_overrides
from zce.engine import Lot, EngineAssumptions, compute_capacity

city = load_city("pasadena")
rules = load_zone_rules(city.rules_dir)
state = load_state_overrides(city.state_law_file)
a = EngineAssumptions(gross_sqft_per_unit=1062.5, parking_stall_sqft=300)

lot = Lot(area_sqft=7252, width_ft=50, depth_ft=145.1, dist_major_transit_ft=4643, existing_units=1)
r = compute_capacity(rules["RS-6"], lot, a, state)
print(r.max_units, r.binding_constraint)
print(r.limits)
```

You should see `4 state_law:sb9` and each limit. Now change `area_sqft` to
`2000` and run the last three lines again. What changed, and why? (Type
`exit()` to leave.)

Explore the real results table the same way (this needs the data, which is
on your computer already):

```python
import geopandas as gpd
lots = gpd.read_parquet("../data.nosync/out/pasadena/capacity.parquet")
len(lots)                                    # how many lots
lots.columns.tolist()                        # every column name
lots[["address", "rules_zone", "max_units", "binding_constraint"]].head()
lots.groupby("rules_zone")["max_units"].sum().sort_values(ascending=False)
lots[lots["address"].str.contains("MOUNTAIN ST", na=False)]
```

---

## 4. A tour of the folders

```
zoning-capacity-explorer/
├── README.md               what it is, how to run it
├── METHODOLOGY.md          every calculation in plain language (read this early)
├── LEARNING.md             one paragraph per concept, with links (your study notes)
├── ADDING_A_CITY.md        how to do this for another city
├── Makefile                shortcuts: make test, make all, make site, make repl
├── cities/
│   ├── pasadena/
│   │   ├── city.yaml       where the data comes from + assumptions
│   │   └── rules/*.yaml    one file per zone, every number cited
│   └── _california/
│       └── state_overrides.yaml   SB 9, ADUs, AB 2097, ...
├── pipeline/               the Python side
│   ├── pyproject.toml      which libraries the project uses
│   ├── src/zce/            the code ("zce" = Zoning Capacity Explorer)
│   │   ├── __main__.py     the command line: python -m zce clean pasadena
│   │   ├── config.py       reads city.yaml
│   │   ├── download.py     step 1
│   │   ├── adapters/       turn each publisher's data into our format
│   │   ├── spatial.py      map math: which zone is each lot in?
│   │   ├── transit.py      distance to transit
│   │   ├── clean.py        step 2 (+ report.py writes the quality report)
│   │   ├── rules/schema.py what a rule file is allowed to contain
│   │   ├── engine/         THE ZONING MATH (start here, see section 6)
│   │   ├── capacity_step.py  step 3: run the engine on every lot
│   │   ├── export_web.py   step 4: files for the website
│   │   ├── golden.py       answers the browser must match
│   │   └── validate.py     compare with official figures
│   └── tests/              pytest tests (one file per part of the code)
├── web/                    the website (TypeScript)
│   ├── index.html          the page's structure
│   └── src/
│       ├── main.ts         wires everything together
│       ├── map.ts          the map
│       ├── engine/         the same zoning math, in TypeScript
│       └── ...             charts, search, legend, print
├── reports/pasadena/       generated reports (data quality, capacity, validation)
├── shared/fixtures/        golden.json (Python's answers for the browser test)
└── docs/                   this guide, hand checks, the original plan
```

Folders ending in `.nosync` (`data.nosync`, `pipeline/.venv.nosync`,
`web/node_modules.nosync`) are generated and not in git. The `.nosync` name
keeps iCloud from syncing them (your Desktop syncs to iCloud).

---

## 5. Follow one lot through the whole system

The best way to understand a pipeline is to follow one thing through it. Take
**2314 E Mountain St**.

**Step 1: Download** (`download.py`). The county publishes parcels through an
ArcGIS web service that returns at most 1,000 records per request, so
`download_arcgis_layer()` asks for page after page in a `while` loop until it
has all 40,182 Pasadena records, then saves them as one GeoJSON file. Our
lot arrives as a record with fields like `AIN: "5744002002"`, `Units1: 1`,
`YearBuilt1: 1948`, and a polygon of longitude/latitude points.

**Step 2: Clean** (`adapters/la_assessor.py`, then `clean.py`).
- `load_parcels()` keeps only the columns on the `WHITELIST` (privacy: nothing
  else can leak), renames them (`AIN` → `parcel_id`), adds up the five
  numbered building slots into `existing_units`, and merges condo stacks.
- The polygon is converted from degrees to **feet** (`to_crs("EPSG:2229")`), so
  `.area` gives square feet: 7,252.
- `spatial.assign_zone()` overlaps the lot with the zoning map and keeps the
  zone covering most of it: **RS-6**.
- `transit.distance_to_nearest_ft()` finds the nearest major transit stop:
  4,643 ft.
- The lot gets a list of **flags** for anything odd (ours has none), and is
  written to `parcels.parquet`.

**Step 3: Capacity** (`capacity_step.py` → `engine/`).
- `spatial.lot_dimensions()` estimates width × depth: 50 × 145.1 ft.
- The row becomes a `Lot(...)` object (just numbers) and the RS-6 rules are
  loaded from `RS-6.yaml`.
- `compute_capacity()` runs four limits from `constraints.py`: density 1,
  envelope 2, parking 5 (lot area per unit doesn't apply to RS-6). The
  smallest is 1: the city's answer.
- Then the state paths: ADU → 3, SB 9 → 4. The best is **4, limited by SB 9**.
- `redevelop.py` asks whether it's likely to be rebuilt: no (single-family zone).

**Step 4: Website** (`export_web.py` → `web/`).
- The lot's shape goes into `parcels.pmtiles` with an id number (its `pid`).
- Its numbers go into `parcels.json`, at position `pid` in each list.
- In your browser, `map.ts` colors the shape using those numbers; when you
  move a lever, `web/src/engine/` (the TypeScript copy of the same math)
  recomputes all 30,198 lots in about 30 milliseconds.

Every step of this is written out with arithmetic in
[`docs/HAND_CHECKS.md`](HAND_CHECKS.md), lot #1.

---

## 6. The code, matched to CS50P weeks

Read these after (or while) doing the matching CS50P week. File paths are
under `pipeline/src/zce/` unless they start with `web/`.

### Week 0: Functions, variables
**Read:** `engine/constraints.py`. Start with `round_units()`, then
`lot_area_per_unit_limit()`.

Every constraint is a function with inputs (a rule and a lot) and one output
(a number of homes). Notice the **docstrings** (the `"""..."""` under each
`def`): they say what the function does in words, with an example. Notice
**type hints** like `def round_units(x: float, mode: str) -> int:`: they
don't change how Python runs, but they tell you (and VS Code) what goes in and
what comes out.

### Week 1: Conditionals
**Read:** `round_units()` again (three rounding modes, `if`/`return`), then
`engine/capacity.py` → `compute_capacity()`.

`compute_capacity` is a chain of decisions: Is there a rule file? Is housing
allowed? Is the lot within ½ mile of transit (then no parking minimum)? Is it
in a landmark district (then no SB 9)? Follow each `if` and ask "which real
law is this?". The comments say.

### Week 2: Loops
**Read:** `constraints.py` → `parking_limit()` (a `while` loop that counts
down until the homes and their parking fit), and `capacity_step.py` →
`run_capacity()` (a `for` loop over all 30,198 lots).

Why a loop instead of a formula in `parking_limit`? Parking rounds to whole
spaces and guest spaces only start at 10 homes, so a formula gets edge cases
wrong. Counting down from an upper bound is simple and obviously correct.

### Week 3: Exceptions
**Read:** `download.py` → `_get_json()`: `try`/`except` with **retries**
(wait 1, 2, 4 seconds) because the internet sometimes fails. Then the
`assert` lines at the end of `clean.py` (`assert len(parcels) == n_in`):
these stop the pipeline loudly if something impossible happens, instead of
quietly producing wrong numbers.

### Week 4: Libraries
**Read:** the `import` lines at the top of any file, then `pyproject.toml`.

- `requests`: downloading from the internet (`download.py`).
- `pandas`: tables (think spreadsheets in code): `groupby`, `sum`, columns.
- `geopandas`: pandas plus shapes and maps (`spatial.py`).
- `pydantic`: checking that a YAML file has the right fields (`rules/schema.py`).
- `yaml`: reading `.yaml` files (`config.py`).

`uv` installs these from PyPI (Python's package library) into
`pipeline/.venv.nosync`, the project's private "virtual environment".

### Week 5: Unit tests
**Read:** `pipeline/tests/test_engine.py` from the top. Then run it:

```bash
cd pipeline && UV_PROJECT_ENVIRONMENT=.venv.nosync uv run pytest tests/test_engine.py -v
```

(The `UV_PROJECT_ENVIRONMENT=.venv.nosync` part tells `uv` to use the
project's iCloud-safe environment; `make` commands set it for you.)

Each test sets up a tiny lot, calls one function, and `assert`s the answer,
with the arithmetic in a comment. `@pytest.mark.parametrize` runs one test
with many inputs. Then look at `tests/test_scenario.py` →
`test_permissive_levers_never_reduce_capacity`: instead of one example, it
checks a **rule that must always hold** for many cases. That test caught a
real bug (section 9).

### Week 6: File I/O
**Read:** `config.py` → `load_city()` (open a file, parse YAML), then
`export_web.py` → `write_rules()` (write JSON), then `report.py` (write a
Markdown report with `path.write_text(...)`).

Notice `pathlib.Path` instead of strings for file paths:
`city.raw_dir / "parcels.geojson"` joins paths correctly on any computer.

### Week 7: Regular expressions
**Read:** `adapters/pasadena_zoning.py` → `OVERLAY_PATTERN`, then
`validate.py` → `SITE_ROW` and `_address_key()`.

`OVERLAY_PATTERN` uses `re.VERBOSE` so the pattern can be written across lines
with comments. Its tests are in `tests/test_pasadena_zoning.py`: run them, then
change the pattern and watch which test breaks. `SITE_ROW` pulls each table
row out of a 336-page PDF; the check that it worked is that the parsed
total equals the total printed in the document (10,261).

### Week 8: Object-oriented programming
**Read:** `engine/constraints.py` → `class Lot` and `class EngineAssumptions`
(`@dataclass(frozen=True)`: a class that's mostly data, read-only), then
`rules/schema.py` (Pydantic classes; `Banded.pick()` is a method that looks up
the right row of a table).

`Lot` has a `@property` called `shape_factor`: it looks like a variable
(`lot.shape_factor`) but is computed every time from the lot's other values.

### Week 9: Et cetera
Look for these around the codebase:

- **List comprehensions**: `[name for bit, name in SCREEN_NAMES.items() if not mask & bit]` (`engine/redevelop.py`).
- **`dict` unpacking**: `{**rules.sources, SCENARIO_SOURCE: SCENARIO_CITATION}` (`engine/scenario.py`).
- **Generics**: `Sourced[float]` in `rules/schema.py`, one class used for any value type.
- **Bit masks**: `mask & AGE` in `engine/redevelop.py`, four yes/no answers packed into one number.
- **`__main__.py` and `argparse`**: how `python -m zce clean pasadena` turns into a function call.

---

## 7. Hands-on experiments

Make a branch first, so nothing you try affects the real project:

```bash
git switch -c my-experiments
```

When you're done, go back with `git switch main` (your experiments stay on
their branch). Run `make test` after each change.

**Easy**

1. **Change a rule and see the effect.** In `cities/pasadena/rules/RS-6.yaml`,
   change `max_units_per_lot` from 1 to 2. Run `make capacity` and look at the
   top of `reports/pasadena/capacity_report.md`. Which number changed? Which
   test fails, and why is that a *good* thing? Undo with
   `git checkout cities/pasadena/rules/RS-6.yaml`.
2. **Break a rule file on purpose.** Misspell `max_units_per_lot` as
   `max_unit_per_lot`. Run `make test`. Read the error: Pydantic tells you
   exactly what's wrong. That's what `extra="forbid"` is for.
3. **Change an assumption.** In `city.yaml`, change `avg_unit_net_sqft` from
   850 to 650 (smaller homes). Run `make capacity`. Why does the total go up?

**Medium**

4. **Write a test** in `tests/test_engine.py` for a lot you calculate by hand:
   an RM-48 lot of 20,000 sq ft. Work out `lot_area_per_unit_limit` with a
   calculator first (20,000 ÷ 910, nearest whole number), then assert it.
5. **Add a column to the quality report.** In `report.py`, add the average
   year built per zone category to the "Lots by zone category" table.
   (Hint: `year_built=("year_built", "mean")` inside `.agg(...)`.)
6. **Answer a question with pandas** in `make repl`: which 10 lots allow the
   most new homes? (Hint: `sort_values("net_new_units", ascending=False)`.)

**Hard** (good projects after CS50P)

7. **Add a new reform lever**: "allow 1 extra story everywhere in RM zones".
   You'll touch `engine/scenario.py` (Python), `web/src/engine/scenario.ts`
   (TypeScript, the same logic), `web/src/url.ts` (the share link),
   `web/index.html` (the control), and `golden.py` (a new test scenario).
   Then `make golden` and `make test`: the parity test tells you whether your
   Python and TypeScript agree.
8. **Model one Central District zone.** Read its standards in the zoning
   code (Article 3), write `cities/pasadena/rules/MU-G.yaml`, and see how many
   gray lots turn blue. This is real, useful work.

---

## 8. Things CS50P doesn't cover (yet)

Short explanations; `LEARNING.md` has a paragraph and a link for each.

- **Terminal and `make`.** `make test` runs the commands listed under `test:`
  in the `Makefile`. It's a menu of shortcuts so you don't have to remember
  long commands.
- **Git** saves snapshots ("commits") of the whole project. `git log --oneline`
  lists them; each milestone is one. `git diff` shows what you changed since the
  last commit. GitHub stores a copy online. Learn it with the free
  [Pro Git book](https://git-scm.com/book/en/v2), chapters 1–3.
- **Coordinate systems.** Map data in longitude/latitude is in degrees, which
  aren't a fixed length, so we convert to a system measured in feet before
  measuring areas or distances.
- **GIS / spatial joins.** Joining tables by *where things are* (which zone
  polygon covers this lot?) instead of by a matching ID.
- **The web: HTML, CSS, JavaScript.** `index.html` is the page's structure,
  `style.css` its looks, and TypeScript files (`.ts`) its behavior.
  TypeScript is JavaScript with type hints, like Python's but checked before
  the code runs. Free course: [CS50's Web Programming](https://cs50.harvard.edu/web/).
- **Vector tiles.** The map is cut into square tiles so your phone only
  downloads what's on screen.
- **Two languages, one answer.** The zoning math exists in Python (for the
  data pipeline) and TypeScript (so the website can recompute without a
  server). A test compares them on 3,735 cases so they can't drift apart.
- **CI (continuous integration).** `.github/workflows/` tells GitHub to run
  the tests and rebuild the site on every push.

---

## 9. How this was built: the process

The code is only half of it. This is the process behind it, which matters more
than any one file.

**1. Plan before coding.** `docs/PLAN.md` was written first: milestones, data
sources, the architecture, and the decisions that are expensive to change
(pilot city, frontend, hosting), which were asked about, not guessed.

**2. Look at real data before writing code.** Before writing the parcel
adapter, a quick script counted things. That's how we learned 10,000
"parcels" were condo units stacked on the same shapes, and that 5,000 lots
with "Pasadena" addresses are actually outside the city.

**3. Build in small steps, test each one.** Each milestone ended with passing
tests and a commit. Small steps mean that when something breaks, you know
it was the last thing you changed.

**4. When a number looks wrong, investigate. Don't ignore it.** Some real
examples from this project:

- *"Half the lots are substandard?"* True: Pasadena has thousands of old 50 ft
  lots narrower than today's minimum. The number was right; the flag was
  split in two to say why.
- *"Tiny 60 sq ft slivers get 2 homes?"* A real bug: SB 9 was applied to
  strips of land. Fixed with a minimum lot size, written down as an assumption.
- *"A more permissive rule *lowered* capacity in some districts?"* A real bug,
  found in the printed summary: allowing duplexes switched off the ADU option.
  Fixed in both languages, and a test was added that checks permissive
  levers never lower capacity.
- *"Fourplexes add 19,000 likely homes but only 456 theoretical ones?"* The
  definition was the problem, not the code. Changing it to match real-world
  evidence (2–4 unit buildings add about 8 homes a year in Pasadena) made the
  tool more honest.

**5. Debugging the environment is part of the job.** Python couldn't find the
project's code because iCloud marks files in `.venv` as hidden and Python
skips hidden `.pth` files. Map clicks did nothing because the browser pane
was hidden, so the map never loaded its tiles. Neither was a bug in the code,
and both took real investigation. When something "impossible" happens,
check your assumptions about the environment.

**6. Check the results against the outside world.** Tests prove the code does
what was intended; validation (`reports/pasadena/validation.md`) checks
the intent against reality: state housing counts, the city's own plan, and
what actually got built.

**7. Write it down.** Every assumption sits next to its number in the rule
files; METHODOLOGY.md explains every calculation. Code that explains itself
is code someone else (or you, in six months) can trust and fix.

---

## 10. Glossary

| Term | Meaning |
|---|---|
| **Parcel / lot** | A piece of land with its own tax ID (AIN/APN). |
| **Zone / zoning district** | An area with one set of rules (e.g. RS-6 = single-family, 7,200 sq ft minimum lot). |
| **Specific plan** | A separate rulebook for one area that replaces normal zoning there (e.g. the Central District, downtown). |
| **Overlay** | Extra rules layered on top of a zone (landmark district, hillside, ...). |
| **Setback** | Required empty space between a building and the lot line. |
| **FAR (floor area ratio)** | Total building floor area ÷ lot area. FAR 1.0 on a 10,000 sq ft lot = 10,000 sq ft of building. |
| **Lot coverage** | Share of the lot a building may cover. |
| **Binding constraint** | The rule that sets a lot's limit, the lowest of all the limits. |
| **ADU / JADU** | Accessory dwelling unit (a backyard cottage) / junior ADU (inside the house). |
| **SB 9** | California law allowing two homes per single-family lot, or a lot split with two each. |
| **AB 2097** | California law banning parking minimums within ½ mile of major transit. |
| **Theoretical vs. realistic capacity** | What the rules allow vs. what plausibly gets built. |
| **Pipeline** | A sequence of steps, each reading the previous step's output. |
| **GeoJSON / GeoParquet / PMTiles** | File formats for map data: readable text / compact table / web map tiles. |
| **CRS** | Coordinate reference system: what the numbers in a shape mean (degrees, feet, ...). |
| **Golden test** | A test comparing a program's output with saved, known-good answers. |
| **Regression test** | A test that protects an answer known to be right from being broken later. |
| **CI** | Continuous integration: tests that run automatically on every push. |

---

**Where to go next.** Finish CS50P, then come back to section 7's
experiments. When something here doesn't make sense, that's a good question
to ask (me, or the CS50 community): "What does this line do and why is it
written this way?" is the fastest way to learn from real code.
