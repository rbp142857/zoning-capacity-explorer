# Methodology

How the Zoning Capacity Explorer estimates what Pasadena's zoning allows, for
readers who want to check or cite it. Written to be followed without a
programming background; file paths point to where each piece lives if you do
want to look.

> **This is an estimate for research and advocacy, not legal or zoning
> advice.** Always confirm with the City of Pasadena before relying on any
> number for a specific property.

## Summary

| | Homes | |
|---|---|---|
| Homes on modeled lots today | 51,582 | Assessor roll |
| Legal maximum, city zoning only | 54,203 | |
| Legal maximum with state law (SB 9, ADUs, AB 2097) | 114,213 | theoretical |
| New homes possible (maximum minus existing) | 68,222 | theoretical |
| New homes on lots **likely to redevelop** | 4,907 on 753 lots | a screen, not a forecast |

- 77% of residential land allows only one home under the city's own zoning;
  state law (SB 9, ADUs) is what allows more there.
- 2,607 lots (specific plans and planned developments, mostly the Central
  District) are **not modeled yet**. That's where most new apartment buildings
  are being built (section 8), so the citywide totals undercount.

## 1. What the tool measures

For every lot, the **maximum number of homes the rules allow** if the lot were
rebuilt, and **which rule sets that limit** (the *binding constraint*: the
rule a reform would have to change to allow more). Separately, it flags lots
where rebuilding is **plausible** under common planning screens (section 6).

## 2. Data

| Data | Source | Date retrieved | Terms |
|---|---|---|---|
| Lot boundaries, building records, assessed values | Los Angeles County Office of the Assessor (2026 roll) | 2026-10-28 | Public record; no owner names in the source; attribution given |
| Zoning districts and overlays | City of Pasadena zoning map (updated Jan 16, 2026) | 2026-10-28 | Published by the city; attribution given |
| Specific plan areas, council districts, city boundary | City of Pasadena | 2026-10-28 | Published by the city |
| Major transit stops (PRC §21064.3, AB 2553) | SCAG, Connect SoCal 2024, base year 2022 | 2026-10-28 | Planning data; attribution given |
| Metro rail stations | LA Metro GTFS | 2026-10-28 | LA Metro developer terms |
| Zoning Code text | Pasadena Municipal Code Title 17, Municode version of Sep 2, 2026 | 2026-10-28 | Public law |
| Housing permits and completions | HCD Annual Progress Reports, Table A2 (data.ca.gov) | 2026-10-29 | Open data |
| Housing Element sites inventory | City of Pasadena 2021–2029 Housing Element (adopted Jul 18, 2022) | manual download | Public document |
| Official housing-unit counts | California Department of Finance, E-5 (May 2026) | manual download | Public data |

The exact URLs are in `cities/pasadena/city.yaml`, and each download's date is
recorded in `data.nosync/raw/pasadena/_manifest.json`.

**Cleaning.** The Assessor gives each condo unit its own record on a shared
polygon; we merge these into one lot per building (40,182 records become 30,198
lots). Each lot is matched to the zone covering most of it. Lots are **flagged,
never dropped**: every data problem is counted in
[`reports/pasadena/quality_report.md`](reports/pasadena/quality_report.md).

**Privacy.** The tool is about rules and land, not owners. We keep only an
explicit list of columns, so owner names or mailing addresses can't reach the
site even if a source adds them; a test checks this.

## 3. From the zoning code to rule files

Each zone's standards are written into a structured file
(`cities/pasadena/rules/RS-6.yaml` and so on) where **every number cites its
code section**. Where the code is ambiguous, the file states what we assumed
and why, next to the number (for example, how a table cell spanning two
columns was read). 16 zones are modeled: single-family (RS-1, RS-2, RS-4,
RS-6), multifamily (RM-12, RM-16, RM-16-1, RM-32, RM-48), commercial zones that
allow housing (CO, CL, CL-2), and zones that don't (CG, IG, OS, PS).

## 4. How many homes fit on one lot

Four separate limits are computed; the **lowest** is the city's answer.

1. **Density:** a cap per lot (RS: 1, RM-12: 2) or per acre (CL-2: 16).
2. **Land per home:** a minimum amount of lot per home (RM-32: 1,360 sq ft),
   with Pasadena's own rounding rules and its small-lot table for RM-32/RM-48.
3. **Building size (envelope):** the lot minus setbacks, then limits on lot
   coverage and, in multifamily zones, required garden space (29–37% of the
   lot); times the stories the height limit allows; capped by any floor-area
   limit; divided by the floor area one home uses: **1,062.5 sq ft** (an
   850 sq ft home plus its share of halls and stairs).
4. **Parking:** 2 spaces per home, plus guest spaces at 10+ homes. We assume
   **surface parking** at 300 sq ft per space and count how many homes fit once
   parking takes its share of the ground. Garages under the building would
   allow more but cost far more.

Lot width and depth come from the smallest rectangle around the lot; irregular
lots are scaled down so they don't get credit for land they don't have. A lot
smaller or narrower than today's minimum for *new* lots is flagged but still
counted, because existing lots can be built on. Ten real lots are worked out
by hand in [`docs/HAND_CHECKS.md`](docs/HAND_CHECKS.md); all ten match.

## 5. State law

California law overrides city zoning. We compute the city's answer first, then
each state path, and keep both numbers (`cities/_california/state_overrides.yaml`).

- **ADUs (Gov. Code §66314 and following):** wherever a house fits, the owner
  may build the house plus a backyard ADU and a junior ADU: 3 homes. Counted
  as an alternative to the city's answer (whichever is larger).
- **SB 9 (Gov. Code §65852.21, §66411.7):** in single-family zones, 2 homes per
  lot, or a lot split with 2 homes on each (4), if the lot is at least 2,400 sq
  ft. Not in landmark (historic) districts. We can't check the rule against
  demolishing recently rented housing (no tenancy data), so SB 9 capacity is
  overstated on rented lots.
- **AB 2097 (Gov. Code §65863.2):** no parking minimums within ½ mile of a
  major transit stop (measured from the lot's nearest edge).
- **Not modeled yet:** SB 79 (2025 transit-oriented upzoning) and the State
  Density Bonus Law. Capacity near transit is therefore **underestimated**.

## 6. Theoretical vs. likely to redevelop

The numbers above are **theoretical**: every lot rebuilt to the maximum. Most
never will be. A lot counts as **likely to redevelop** only if it passes all of
these screens (thresholds in `cities/pasadena/city.yaml`):

1. Zoning allows **at least twice** the homes already there **and at least 3
   more** (tearing down a house to gain one or two homes rarely pays).
2. The building is **50+ years old**, or the lot is vacant.
3. The building is **assessed at less than the land**.
4. **Not a condo** (many owners rarely sell together).
5. **Not in a landmark district** (demolition needs special review).
6. **Not in a single-family zone.** Small-scale infill on single-family lots
   (SB 9, ADUs, or a city duplex/fourplex reform) has produced few homes
   wherever it's been allowed: in Pasadena, buildings of 2–4 homes added about
   8 homes a year in 2018–2025 (section 8). It's reported separately as
   theoretical capacity (53,546 homes on 20,134 lots) whichever rule allows it.

Only the city's (or a reform scenario's) own allowance counts here. **Today:
4,907 homes on 753 lots.** This is a **screen, not a forecast**: it shows
where rebuilding is plausible, not when or whether it will happen.

Caveats:

- **Prop 13 weakens screen 3.** On a sale the assessor puts most of the price
  into land, so the building-to-land ratio is about 1.7 for owners who bought
  before 1980 but about 0.4 for buyers since 2010. The screen passes 77% of
  lots and mostly flags recently sold ones; the other screens do the work.
- **Single-family reforms show no "likely" gain, by design**, because of
  screen 6. Their effect is better read from the theoretical numbers and local
  permit trends. (An earlier draft counted a city fourplex as likely but not
  the same building under SB 9; that inconsistency overstated the reform.)

## 7. Reform scenarios

The "Reform scenario" panel changes the rules and recalculates every lot in
your browser, using the same calculations as the pipeline.

| Lever | What changes |
|---|---|
| Homes per lot, single-family zones | The one-home cap becomes 2, 3, 4 or 6. Floor-area, setback and parking limits still apply. |
| Minimum lot size, single-family zones | A lot may be split into as many lots of the new size as fit, each with the per-lot allowance. Street access isn't checked, so this is optimistic. |
| Parking per home | Replaces the 2-space requirement everywhere (0 removes it). |
| No parking minimums near transit | Widens AB 2097's ½-mile radius (it can't be narrowed). |
| Near transit: stories / density | For multifamily and commercial zones in the chosen radius: extra stories (with floor-area ratio raised in proportion) and less land required per home. |
| Housing in General Commercial (CG) | CG uses CL's housing standards with CG's 45 ft height and FAR 0.80. |
| ADU homes per house | The ADU path adds 3 or 4 homes instead of 2. |

What the presets show:

| Scenario | Theoretical change | Likely-to-redevelop change |
|---|---|---|
| Fourplexes in single-family zones | +456 | +0 (screen 6) |
| No parking minimums within 1 mile of transit | +1,948 | +500 |
| Upzone near transit (+2 stories, double density within ½ mile) | +15,700 | +6,503 |

Fourplex legalization adds little on its own: SB 9 already allows four homes on
most single-family lots, and the city's floor-area limits fit only about two
average-size homes on a typical 7,200 sq ft lot. A reform that also raised
the floor-area limit would show more.

## 8. Validation against official figures

Generated by `make validate` into
[`reports/pasadena/validation.md`](reports/pasadena/validation.md):

- **Existing homes vs. the Department of Finance.** The Assessor roll counts
  66,582 homes on all lots; DOF's 2020 Census benchmark is 61,643. Differences
  of a few percent are expected (how ADUs and mixed-use buildings are
  recorded); see the report for the current year's comparison.
- **The city's Housing Element sites inventory** (10,261 homes on ~550
  parcels) is compared parcel by parcel with our capacity. Housing Elements
  must use *realistic* capacity, so the city's numbers should sit below our
  theoretical maximum; most of the inventory is in specific plans we don't
  model yet.
- **What actually gets built (HCD Annual Progress Reports, 2018–2025):** about
  **424 homes a year** were permitted, of which about 260 in buildings of 5+
  homes, 130 ADUs, and only about 8 in buildings of 2–4 homes. **81%** of the
  homes in new 5+ unit buildings were in specific-plan areas (60% in the
  Central District). In the zones we model, 5+ unit buildings added about 50
  homes a year, so the 4,907 "likely" homes there represent many decades of
  building at recent rates: zoning isn't the only thing holding back
  construction in those zones.

## 9. Not modeled yet, and simplifications

- **Specific plans and planned developments** (2,607 lots), including the
  Central District, where most new apartments are being built. These lots are
  shown in gray and excluded from totals, not counted as zero.
- **Overlays** that can add their own standards: hillside (HD), the North Lake
  specific plan overlay (SP-1a), and others. Base-zone rules are used, and
  hillside lots are flagged.
- **Simplified standards:** neighborhood-compatibility floor-area limits,
  blockface-average front setbacks, encroachment planes, building-separation
  rules, extra setbacks next to single-family zones.
- **State laws not modeled:** SB 79, Density Bonus Law, multifamily ADUs (SB 1211).
- **Lot geometry:** width and depth are estimated from each lot's shape;
  corner and irregular lots may face the "wrong" way.

## 10. How the numbers are kept correct

- **Unit tests** for every constraint, with hand-calculated example lots.
- **Ten real lots** checked by hand against the code text (`docs/HAND_CHECKS.md`).
- **Python and browser agree:** the browser recalculates scenarios with a
  TypeScript copy of the engine; 415 lots × 9 scenarios are compared exactly
  on every test run, and in development the page checks all 30,198 lots.
- **Reforms only add:** every lever loosens a rule, so a test checks that no
  lever lowers any lot's capacity. (It caught a real bug.)
- **Sanity checks** in the pipeline: no negative capacity, nothing dropped,
  every flag counted.
