# Zoning Capacity Explorer

An open-source tool that shows what zoning legally allows on every parcel in a
city, and how much housing a proposed rule change would enable. The pilot city
is **Pasadena, California**.

> **Disclaimer:** this is an estimate for research and advocacy, not legal or
> zoning advice. Always confirm with the city before relying on it.

## Status

| Milestone | State |
|---|---|
| 1. Pilot city research | ✅ Pasadena chosen |
| 2. Data pipeline + data quality report | ✅ built (transit distance is a learning exercise, see below) |
| 3. Rule files + capacity engine | next |
| 4–9. Map, scenarios, UI, redevelopment estimate, docs, pro forma | planned |

Latest data quality report: [reports/pasadena/quality_report.md](reports/pasadena/quality_report.md)

## How it fits together

```
cities/pasadena/city.yaml        where the data comes from, which CRS to measure in
        │
        ▼  make download         ArcGIS layers + GTFS → data.nosync/raw/pasadena/
        ▼  make clean            adapters → spatial joins → flags
data.nosync/clean/pasadena/parcels.parquet   one row per lot, zoning attached
reports/pasadena/quality_report.md           counts of every flag (committed)
```

- `pipeline/src/zce/adapters/`: turn each publisher's format into our common
  columns. `la_assessor.py` is shared by every LA County city.
- `pipeline/src/zce/spatial.py`: parcel ↔ zone (largest overlap), parcel ↔
  council district and specific plan.
- `pipeline/src/zce/transit.py`: transit stops, plus the exercise function.
- `pipeline/src/zce/clean.py`: runs it all and adds flags. Lots are flagged, never dropped.

## Running it locally

You need [uv](https://docs.astral.sh/uv/) (`pip install uv`) and `make`.

```bash
make setup
```

```bash
make all CITY=pasadena
```

```bash
make test
```

The download is about 120 MB and takes a minute or two. Raw data is never
committed; `make download` fetches it again and records dates in
`data.nosync/raw/pasadena/_manifest.json`.

**Why `.nosync`?** This repo lives on an iCloud-synced Desktop. iCloud skips
folders ending in `.nosync`, which keeps 100+ MB of data out of iCloud, and
it avoids a real bug: iCloud marks files in synced `.venv` folders as hidden,
and Python ignores hidden `.pth` files, so `import zce` fails. The Makefile
points uv at `pipeline/.venv.nosync` for that reason.

## 🧑‍🎓 Current exercise

Write `distance_to_nearest_ft()` in
[pipeline/src/zce/transit.py](pipeline/src/zce/transit.py). The comment above
it is the spec. Read the "Coordinate systems" and "Spatial joins" sections of
[LEARNING.md](LEARNING.md) first, then:

```bash
make exercise
```

When all 7 tests pass, run `make clean` again; the report's "Distance to
transit" section will fill in.

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

Exact URLs and license notes are in [cities/pasadena/city.yaml](cities/pasadena/city.yaml).

## License

Code: [MIT](LICENSE). Rule files (`cities/**/rules/`) and documentation: CC BY 4.0.

MIT lets anyone reuse the code for anything, including commercial tools,
which maximizes adoption by other cities and advocates. The tradeoff is that
someone could build a closed product on it. AGPL would force anyone who hosts
a modified version to publish their changes, but it scares off many
government and nonprofit users. CC BY on the rule files and methodology asks
for attribution, which is what you want for numbers people cite.
