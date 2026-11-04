# Using this tool

Zoning Capacity Explorer estimates what zoning allows across LA County, and how a rule change would alter that. It works best for **many lots at once**. An error on one lot matters little in a citywide total, but it could matter a lot if you're deciding about that lot.

**Good for:** citywide estimates, comparing reforms, research, reporting, and first looks.
**Not for:** deciding whether to buy, sell or build on a lot. Confirm with the city, and with a land use attorney or consultant.

## Before you quote a number

1. **Check the city's level** in [coverage.md](../reports/la_county/coverage.md). A Partial city's totals run low, because lots in missing plans count as nothing, and those are often where it builds most.
2. **Say which number you mean.**
   - *Theoretical new homes* assumes every lot is rebuilt to the maximum. It will never happen. It also includes government, quarry and similar land, which the site reports separately.
   - *New homes on lots likely to redevelop* counts lots passing the screens in METHODOLOGY.md section 6. It's a screen, not a forecast of how many or when.
   - Neither considers rents, construction costs, financing or whether anyone wants to build.
3. **Mention what isn't modeled**, such as LA's TOC and other bonus programs, site-specific `Q`, `T` and `D` conditions, many specific plans, and design review or CEQA. "By right" means only that no use permit is needed.
4. **Link your scenario** so readers can see the exact settings.

SB 79 and density bonus figures are separate from the main totals. They ignore local delay plans and several conditions, and they haven't had an attorney's review, so they're best treated as rough.

## How accurate is it?

See [accuracy.md](../reports/la_county/accuracy.md), which compares real permitted buildings with this tool's number for the same lot. It can catch numbers that are too low, but it can't show that a number is too high. Most hand checks in recent cities review engine results rather than redo the arithmetic independently.

## By use

### Advocates and journalists
Use the map and the reform levers, then share the link or print the one-page summary. To make a claim such as "this reform allows X more homes in Y", prefer the likely-to-redevelop figure alongside the theoretical one, and say both are estimates.

### Researchers and planners
| What | Where |
|---|---|
| Every rule value, with code section, link and written assumption | [rules.csv](../reports/la_county/rules.csv) |
| City totals and completeness | [coverage.csv](../reports/la_county/coverage.csv) |
| Permit comparison | [accuracy_by_city.csv](../reports/la_county/accuracy_by_city.csv), [accuracy_cases.csv](../reports/la_county/accuracy_cases.csv) |
| Lots in the cities on the map | "Download these lots as CSV" under "Using and citing this data" on the site |
| Method | [METHODOLOGY.md](../METHODOLOGY.md) |

Lot files hold parcel numbers, zones and capacity. They have no owner names or mailing addresses. Zoning and parcel data come from public agencies, some without an explicit open license, so check each source in the city's `city.yaml` before reusing them commercially. Rule files and documentation are CC BY 4.0, and code is MIT.

### Reform studies
Write the scenario in a small YAML file ([example](../studies/transit_upzone_example.yaml)), then run:

```
cd pipeline && .venv.nosync/bin/python -m zce study ../studies/your_file.yaml
```

This writes a report and CSV to `reports/studies/`, with city and transit-distance tables and the limits spelled out. A misspelled lever stops the run with an error. Levers are listed in `pipeline/src/zce/engine/scenario.py`. The `housing_in_cg` lever only acts in cities with zones named CG and CL.

### Developers and brokers
Fine for a free first look at an area. It doesn't replace due diligence, because it omits the site-specific rules and bonus paths that often decide a project. Every lot needs confirming with the city.

## Citing

Zoning Capacity Explorer, [date you accessed it], https://rbp142857.github.io/zoning-capacity-explorer/. See also [CITATION.cff](../CITATION.cff). Please include your scenario link.

## Found a mistake?

Open an [issue on GitHub](https://github.com/rbp142857/zoning-capacity-explorer/issues) with the parcel or zone and, if you can, the code section.
