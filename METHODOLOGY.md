# Methodology

How the Zoning Capacity Explorer estimates what Pasadena's zoning allows, for
readers who want to check or cite it. Written to be followed without a
programming background; file paths point to where each piece lives if you do
want to look.

> **This is an estimate for research and advocacy, not legal or zoning
> advice.** Always confirm with the City of Pasadena before relying on any
> number for a specific property.

## Summary

Four cities are modeled: **Pasadena** (the pilot, using the city's own zoning
map), **Glendale** (the first city added from SCAG's countywide zoning table,
section 11), **Burbank** (section 12) and **Santa Monica** (section 13).

| | Pasadena | Glendale | Burbank | Santa Monica |
|---|---|---|---|---|
| Lots modeled | 27,591 of 30,198 | 34,541 of 35,641 | 24,976 of 25,456 | 14,351 of 14,962 |
| Homes on modeled lots today | 51,582 | 79,516 | 43,358 | 51,036 |
| Legal maximum, city zoning only | 54,342 | 85,625 | 49,761 | 113,611 |
| Legal maximum with state law (SB 9, ADUs, AB 2097), theoretical | 114,385 | 159,577 | 104,968 | 134,346 |
| New homes possible (maximum minus existing), theoretical | 68,323 | 92,798 | 67,382 | 85,765 |
| New homes on lots **likely to redevelop** (a screen, not a forecast) | 4,907 on 753 lots | 13,388 on 1,258 lots | 7,293 on 736 lots | 47,741 on 1,675 lots |
| Residential land where the city allows only one home | 77% | 74% | 74% | 42% |
| Homes permitted per year, 2018–2025 (state reports) | ~424 | ~1,173 | ~321 | ~386 |

- In all four cities, state law (SB 9, ADUs) is what allows more than one
  home on most residential land.
- Pasadena: 2,607 lots in specific plans (mostly the Central District) are
  **not modeled yet**, and that's where most of its new apartments are built.
  Glendale: 62% of new apartment homes are in zones the tool models. Burbank
  built apartments in only five permits, too few to say (section 12). Santa
  Monica: 55% of its new apartment homes were permitted Downtown, which is
  not modeled yet (section 13).

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
   850 sq ft home plus its share of halls and stairs). A lot whose limits
   allow less than that but at least **500 sq ft** still counts as one home:
   the average-size assumption is for counting apartments, and the law
   doesn't require a single house to be that big.
4. **Parking:** 2 spaces per home, plus guest spaces at 10+ homes. We assume
   **surface parking** at 300 sq ft per space and count how many homes fit once
   parking takes its share of the ground. Garages under the building would
   allow more but cost far more.

Lot width and depth come from the smallest rectangle around the lot; irregular
lots are scaled down so they don't get credit for land they don't have. A lot
smaller or narrower than today's minimum for *new* lots is flagged but still
counted, because existing lots can be built on. Fifteen real lots (ten in
Pasadena, five in Glendale) are worked out by hand in
[`docs/HAND_CHECKS.md`](docs/HAND_CHECKS.md); all fifteen match.

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
   theoretical capacity (53,639 homes on 20,134 lots in Pasadena) whichever
   rule allows it.

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

## 11. Glendale

**Zoning data.** Glendale's zones come from SCAG's regional land-use dataset,
which lists every parcel in LA County with its city's zone code (2024 codes,
updated October 2025). It's joined to the county's parcels **by parcel number**,
not by map overlay: 99.2% of Glendale's lots matched; the other 270 are shown
as "no zone". SCAG writes the multifamily zones without the code's hyphen
(`R2250` for R-2250); `cities/glendale/city.yaml` translates them.

**Rules.** 19 zone files from Glendale Municipal Code Title 30 (eCode360,
through Ord. No. 6052, May 19, 2026): single-family (R1, R1R, ROS),
multifamily (R-3050, R-2250, R-1650, R-1250), commercial (C1, C2, C3, CR, CH,
CPD), mixed use (SFMU), and zones without housing (CA, IMU, IMU-R, IND, T).
Glendale's multifamily and commercial density depends on lot width: R-2250
allows one home per 2,250 sq ft, or per 1,800 sq ft on lots 90 ft or wider.

**Choices made because SCAG's table has no overlay maps** (each written in the
rule files):

- **FAR districts** for single-family zones (I, II, III): district I, the most
  restrictive, is used. With one home per lot it only affects reform scenarios.
- **Height districts** for C2 and C3: district I (3 stories) is used.
- **SFMU** density and height depend on what the lot borders (35, 87 or 100
  homes per acre): the middle tier (87, 4 stories) is used for every lot.
- **Historic districts** (Ch. 30.25) aren't in the table, so SB 9's
  historic-district exclusion and the landmark redevelopment screen can't be
  applied in Glendale. SB 9 capacity is somewhat overstated there.
- **IMU-R** allows apartments only with an Administrative Use Permit, a
  discretionary approval, so it's counted as not allowing housing by right.
- Multifamily setbacks use the code's **average** values (23 ft front, 8 ft
  sides) rather than the minimums.

**Not modeled yet:** the Downtown Specific Plan (DSP, about 450 lots), Special
Recreation (SR) and a few small zones: 1,100 lots in all.

**Validation** ([`reports/glendale/validation.md`](reports/glendale/validation.md)):
Glendale permitted about 1,170 homes a year in 2018–2025 (about 690 in
buildings of 5+ homes, 430 ADUs, 11 in 2–4 unit buildings). 62% of new
apartment homes were in modeled zones; at that pace the likely-to-redevelop
estimate equals about 31 years of building.

## 12. Burbank

**Zoning data.** Like Glendale, Burbank's zones come from SCAG's parcel-level
zoning table, joined by parcel number: 99.4% of lots matched (164 show "no
zone"). SCAG spells Burbank's codes the way the code does. The Media
District's residential zones are aliased to the zones the code says they
follow (MDR-3 → R-3, MDR-4 → R-4, BMC §10-1-2124).

**Rules.** 30 zone files from the Burbank Municipal Code, Title 10, Chapter 1
(Code Publishing, through Ord. No. 25-4,036, eff. January 16, 2026):
single-family (R-1, R-1-H), multifamily (R-2, R-3, R-4), commercial zones
where homes are allowed in mixed-use projects (C-2, C-3, C-4, MPC-1 to 3,
BCC-1 to 3, MDC-2 to 4), and 13 zones without housing. Multifamily density
steps up with lot size: R-4 allows one home per 2,000 sq ft of lot under
12,000 sq ft, per 1,400 sq ft from 12,000, and per 1,000 sq ft from 24,000.

**Two things Burbank does differently, and how the tool handles them:**

- **Limits depend on distance to single-family zoning.** In R-2 to R-4, lots
  within 500 ft of an R-1 or R-1-H lot get 2 stories and 60% lot coverage;
  others get 3 stories and 70%. In mixed-use projects the height is 40 ft
  within 150 ft of single-family zoning and 60 ft beyond (80 ft is allowed
  300 ft from all residential zones; we cap it at 60 ft, since density and
  parking limit those lots first). The pipeline measures every lot's distance
  to the nearest single-family-zoned lot, and rule tables can be keyed on
  it, the same way they're keyed on lot area or width. 37% of R-4 lots are
  more than 500 ft away.
- **Density in commercial zones comes from the General Plan**, not the zone
  (27 homes per acre in Corridor Commercial, 58 in the Media District, 87
  Downtown). SCAG's parcel-level General Plan table shows that each
  commercial zone falls almost entirely in one designation (C-3: 96%
  Corridor Commercial; BCC-1: 100% Downtown), so each rule file uses its
  zone's designation. BCC-3 is split; the most common designation (27 per
  acre) is used. Mixed-use projects round the home count **up**
  (§10-1-920(B)(2)(c)).

**Other choices** (each written in the rule files):

- **Mixed use counts as allowing housing.** In the commercial zones, homes
  are allowed as part of a mixed-use project with an Administrative Use
  Permit (AUP), a staff-level approval. That's the city's only local path to
  housing in those zones, so it's counted. (Glendale's IMU-R, where apartments also need an
  AUP, is counted as not allowing housing; a consistent treatment across
  cities is an open question.) Residential-only buildings in commercial zones
  are allowed only where state law requires them, which isn't modeled.
- **SB 9 in R-1-H.** Burbank's code bars SB 9 second homes in its
  horsekeeping zone (§10-1-608.1(A)(3)). We follow the city's code, so those
  750 lots get the ADU path only, and are flagged `sb9_excluded_by_city`.
- **Second homes by conditional use permit** in R-1 are discretionary and not
  counted.
- **Measure One** (Art. 20, extended to 2030) requires voter approval to
  raise the General Plan's housing limits, and community-impact findings for
  residential projects. Neither is a per-lot number; both are noted, not
  modeled.
- Single-family front setbacks are "the average on the block", which we
  can't measure; 20 ft is used.

**Not modeled yet:** planned developments (PD, about 230 lots with 4,500
homes, including large apartment complexes), the hillside area's extra
standards, the 2021–2029 Housing Element Opportunity Sites overlay (site-by-
site densities from the Housing Element), and a few codes that don't appear
in the current code (NSFC, R-5, MDR-5): 480 lots in all.

**Validation** ([`reports/burbank/validation.md`](reports/burbank/validation.md)):
Burbank permitted about 320 homes a year in 2018–2025: 100 in buildings of 5+
homes, 205 ADUs, and 4 in 2–4 unit buildings. Apartment building came from
just five permits, so the "where it was built" table is fragile. The report
says 77% were in modeled zones, but that is one 573-home project at 777 N
Front St (2022), whose parcel number isn't on today's county roll (the site
was re-parceled) and whose map point lands on the neighboring railroad lot.
Of the rest, 93 homes were in a planned development (not modeled), 46 on an
R-4 lot, and 92 couldn't be matched. The likely-to-redevelop estimate (7,300
homes on 736 lots, nearly all in commercial zones) is about 94 years of
Burbank's recent apartment building: its zoning allows far more than gets
built. The Department of Finance housing count still needs its manual
download.

## 13. Santa Monica

**Zoning data.** Zones come from SCAG's parcel-level table, joined by parcel
number: 99.4% of lots matched (85 show "no zone"). SCAG appends overlay codes
to some zones: `-A` (off-street parking overlay, Ch. 9.16) and `-BCH` (Beach
Overlay, Ch. 9.20). Neither changes housing rules, so those lots are aliased
to their base zone, except in three beach areas where the code sets its own
standards (below).

**Rules.** 31 zone files from the Santa Monica Municipal Code, Article 9
(eCode360, through Ord. No. 2862CCS, adopted July 28, 2026):

- **Single-family:** R1 (one home, FAR 0.45, 2 stories) and OP1 (Ocean Park).
- **Multifamily:** R2, R3, R4 (one home per 1,500, 1,250 and 900 sq ft of
  lot; FAR 1.0, 1.5, 2.0; 30, 40, 45 ft) and Ocean Park's OPD, OP2, OP3, OP4,
  plus three beach areas of R2 and R3 that Table 9.08.030 treats separately:
  north of the Pier (R2-NP), between Neilson Way and Barnard Way (R2-OPB:
  single homes and duplexes only) and around Appian Way (R3-APW).
- **Mixed-use, commercial, employment and Bergamot zones** that allow housing
  by right: MUBL, MUB, GC, NC, IC, OC, HMU, BTV, MUC, CAC, CCS.
- **No housing:** PL, OS.

**Four things Santa Monica does differently, and how the tool handles them:**

- **No parking minimums for housing** outside R1 and OP1 (§9.28.060), so
  parking never limits a multifamily or mixed-use lot here.
- **No density limit in the commercial zones.** Since the 2024 Housing
  Element rezoning (Program 1.J), housing projects in the mixed-use,
  commercial, employment and Bergamot zones have their own standards (Tables
  9.11.030.B, 9.12.030.B, 9.13.030.B): a floor-area ratio and a height, and
  no homes-per-acre cap. The number of homes follows from floor area: FAR ×
  lot area ÷ 1,062.5 sq ft per home. This is why Santa Monica's commercial
  capacity is so much larger than Burbank's, whose commercial zones cap
  density at 27 to 87 homes per acre.
- **Standards differ by street within one zone.** GC allows FAR 3.25 and
  70 ft on Santa Monica Blvd, 2.5 and 55 ft on Lincoln Blvd, 2.0 and 45 ft on
  Pico Blvd; MUBL and NC differ by street too. SCAG's table has one code per
  zone, so the pipeline picks the rule file from the lot's address
  (`zone_splits` in city.yaml): street name first, then ZIP code (90405 is
  the part of the city south of the I-10). A corner lot addressed on a side
  street gets the zone's default. Where the code's values differ within one
  street (MUBL on Pico west of Lincoln, MUC north of Pennsylvania Ave), we
  use the lower values.
- **Rounding:** fractions of 0.5 or more round up (§9.04.020). Ocean Park's
  rule (one more home if the leftover land is at least half the per-home
  area) works out the same.

**A finding worth knowing.** In the multifamily zones (R2 to R4, OP2 to
OP4), 38,500 homes exist today but current zoning allows only 32,200 on the
same lots: 2,700 of 5,700 lots have more homes than the zone now permits,
mostly older apartment buildings. Rebuilding those lots under today's rules
would lose homes, so they almost never pass the redevelopment screens.
Nearly all the "likely" new homes (44,900 of 47,700) are on commercial-zone
lots.

**Other choices** (each written in the rule files):

- Housing projects in the commercial zones use the table's housing
  standards; 100% affordable projects get about 10 ft and 0.5 FAR more, not
  modeled (like the state density bonus).
- Story limits: housing projects have none in most zones, so stories are
  what fits under the height limit (an 11 ft ground floor, then 10 ft
  floors). FAR binds first on nearly every lot.
- All floor area in a mixed-use building is counted as housing; required
  ground-floor commercial space on some boulevards isn't subtracted.
- Projects of 10 or fewer homes may use 4 ft side and rear setbacks (state
  law SB 684 and SB 1123, written into the tables); we use the standard
  setbacks, which rarely bind.
- R1 and OP1 duplexes and lot splits (§9.31.125) are Santa Monica's SB 9
  rules, modeled by the state-law path.
- **SB 79** (2025 transit upzoning) is not modeled anywhere, and Santa Monica
  has temporarily exempted qualifying parcels from it (Ch. 9.06, Ord. No.
  2861CCS, until a year after its next Housing Element).
- Ord. No. 2865CCS (September 22, 2026) amends the base districts but wasn't
  in the online code when the rules were read; the rule files need a re-check
  once it's codified.

**Not modeled yet:** the **Downtown Community Plan** districts (LT, NV, BC,
TA, OT, WT: 469 lots, 5,200 homes), whose standards are in the plan's
Chapter 4 rather than the zoning code; the Civic Center (CC), Oceanfront
(OF) and mobile home park (RMH) districts; and the airport. 611 lots in all.

**Validation** ([`reports/santa_monica/validation.md`](reports/santa_monica/validation.md)):
Santa Monica permitted about 386 homes a year in 2018–2025: 250 in buildings
of 5+ homes, 93 ADUs, and 10 in 2–4 unit buildings. **55% of the homes in 5+
unit buildings were permitted Downtown** (LT 644, TA 437, NV 28), and 35% in
modeled zones (mostly MUBL and NC). So the city's biggest building area is
the part this tool doesn't model yet; it joins Pasadena's Central District
in wave 3 (docs/WAVE_PLAN.md). In the modeled zones, the likely-to-redevelop
estimate (47,700 homes) is about 550 years of recent building there: the
zoning allows far more than the market builds. The Department of Finance
housing count still needs its manual download.

## 14. Los Angeles (in progress)

LA is being added in steps and is not on the site yet. It has a zoning adapter
and 259 rule files from the Los Angeles Municipal Code (American Legal and the
city's zoning.lacity.gov, read November 1, 2026), covering 668,189 of its 672,322
lots (99.4%). A lot looks for a
file named for its zone and height district, then its zone alone, so `R1-1` and
`R1-1XL` use `R1`, while `R3-1XL` has its own file because the height district
changes the floor area.

**Not modeled yet:** 4,133 lots, mostly in specific plan zones (Warner Center,
Central City West, Exposition and others).

**Zones.**

- **Single-family:** R1, RS, RA, RE (a map showing only RE means RE11), RE9, RE11,
  RE15, RE20, RE40, A1, A2, R1V1, R1V2, R1V3, R1R3, R1H1, RU, RZ2.5, RZ3, RZ4, RW1.
- **Apartments:** R2, RD1.5 through RD6, R3, R4, R5, RAS3, RAS4.
- **Commercial, with homes allowed:** CR, C1, C1.5, C2, C4, C5, CM.
- **No housing:** MR1, M1, MR2, M2, M3, P, OS, PF.

**Chapter 1A (downtown and Boyle Heights).** 174 zone strings, 16,221 lots, each
with its own file. A string like `[H3-MU3-3][RX2-2L]` reads as Form, Frontage and
Standards District, then Use and Density District. We use base FAR, not bonus
FAR, so these sit far below what projects reach through the public benefit
programs. We don't count homes in IX3, IX4 and IX6, which allow them only with
manufacturing, as 100% affordable, or with Productive Space, and in P2 and A1.
Inclusionary districts (`S` in the use tables) count all their homes, though a
share must be affordable. Amenity space, frontage, step-back and width rules
are not modeled, so these can be too high.

**How floor area works in LA.** It's a multiple of the "buildable area", the lot
minus required yards (§12.21.1 A), not of the lot. Commercial Height District 1
is 1.5 times, other Height District 1 zones are 3 times, Height District 2 is 6, 3
is 10, 4 is 13. Height District 1XL allows two stories. In apartment zones the
multiple equals the engine's story count. In commercial Height District 1 the
multiple is its own field, `max_buildable_multiple`, because the 1.5 limit isn't a
story count and the parking math needs real stories.

**Homes in commercial zones.** Commercial zones borrow their density from
apartment zones: C1 and CM use R3's 800 sq ft per home, C1.5, C2, C4, C5 and CR
use R4's 400. Their numbers assume an all-residential building.

**What's simplified, and which way it pushes the numbers:**

- **Incentive programs are left out, the biggest gap.** The state density bonus,
  Transit Oriented Communities and Executive Directive 1 let many projects exceed
  base zoning, so these are base-zoning numbers: too low for what can really be
  built. This is the next thing to model.
- **Surface parking is conservative.** The engine assumes parking on the ground,
  but many LA apartments park under the building. Parking is the limit on about
  11,200 lots outside the half-mile transit area, which understates them.
- **Parking of 1.5 spaces per home** is the code's figure for 3 habitable rooms;
  larger homes need 2, smaller ones 1.
- **Rent-stabilized buildings aren't identified.** Replacing them has its own
  rules, and the realistic estimate doesn't screen for them, so it is too high.
- **Conditions (`Q`, `T`, `D`) are flagged, not read.** A `D` limit often lowers
  floor area, such as in `C2-2D`, which we treat as `C2-2`, so these can be too high.
- **Hillside lots use flat-lot rules.** 28,581 single-family lots in the `H` overlay
  really follow §12.21 C.10 (floor area by slope). They are flagged.
- **SB 9 in fire zones is overcounted.** Executive Order N-32-25 suspends SB 9 in
  Very High Fire Hazard Severity Zones in the Palisades and Eaton burn areas, and
  a mayoral order stops applications in the Palisades. We don't have those zones
  yet, so those lots wrongly show SB 9 homes.
- **SB 9 in A1 and A2 is left out.** These zones also allow farming, so they may
  not count as single-family under SB 9. We could not find the city's reading, so
  2,585 lots stay at the ADU path (conservative). Check this before relying on it.
- **Small lots keep one home.** A lot too small for one home's share of land is
  given one home. The code says so directly only for single-family zones.
- **Industrial zones get no homes,** since their use lists allow only a guard's or
  caretaker's home, though their sections still set lot-area rules for dwellings.
  Worth a second reading: 9,000+ homes already stand on these lots.
- **Other left-outs:** the 20% floor-area bonus in RA, RE and RS; encroachment
  planes; transitional heights next to single-family zones; Coastal Zone rules.
- **No rule file:** RZ5 and R1P (not found in the code sections checked), RMP
  (mobile home parks), RW2 and one-off zones such as A1(UV).

## 15. El Monte

Not on the site yet: publishing a new city's site files is the owner's call.

**Zoning data.** Zones come from SCAG's parcel table. 96.3% of lots are modeled.
Not modeled: the specific plans (SP-4 Downtown Main Street, 277 lots, plus SP-1 to
SP-3), 125 lots with no zone, RMP, and SCAG's `OP` (110 lots) and `RR` (19 lots),
which aren't in the code's Table 17.14-1. `OP` may be the code's OMU, but we
don't assume so.

**Rules.** 17 zone files from Title 17, rewritten in 2025 by Ord. No. 3053:
R-1A, R-1B, R-1C, R-2, R-3, R-4, MMU, C-1, C-2, C-3, and no homes in M-1, M-2, PF,
OS, AP, RT, RW.

**How El Monte differs:**

- **Density by frontage.** R-1B and R-3 allow more homes on wider lots. We use lot
  width for street frontage.
- **R-1B allows several detached houses** at 7,260 to 8,720 sq ft of land each.
- **FAR is low and rises with project size.** R-2, R-3 and R-4 are 0.40, 0.50 and
  0.60 for three homes. The 0.60 to 0.80 row includes a bonus of up to 0.20 earned
  with points (§17.24.050.C), which we leave out, so numbers lean low.
- **Homes in commercial zones** have their own table: FAR 0.60, 3 stories, 1,740 or
  1,450 sq ft per home. Major arterials need a 15,000 sq ft lot, and we have no
  arterial map, so small arterial lots can be too high. Some areas of Valley
  Boulevard bar homes; not modeled, also too high.
- **MMU needs 20,000 sq ft for homes,** so smaller lots show none, though many could
  combine with neighbors.

**Left out:** upper-story setbacks, open space per home, buffers next to R zones,
the Rurban Homestead Overlay, and the Valley Entryway Overlay. SB 9 follows state
law; El Monte's own SB 9 rules weren't checked.

## 16. Inglewood

Not on the site yet: publishing a new city's site files is the owner's call.

**Zoning data.** SCAG's table. Only 81% of lots are modeled, and the gap matters:
four Transit Oriented Development plan areas (Downtown, Fairview Heights,
Westchester/Veterans, Crenshaw/Imperial, 3,045 lots) appear in SCAG only by plan
name, without the MU-1 to MU-4 zones and the plan's own standards. These are where
Inglewood means to grow, so the city's capacity is well understated until its own
zoning map and the plan are added. Also not modeled: other specific plans, 219
lots with no zone, and a few small zones.

**Rules.** 16 zone files from Chapter 12: R-1, R-1Z, R-1½, R-2, R-2A, R-3, R-4, R-M,
and no homes counted in C-2, C-2A, C-3, C-S, C-R, M-1L, P-1 and O-S.

**How Inglewood differs:**

- **R-2 and R-2A use a stepped schedule:** 2,500 sq ft each for 1 or 2 homes, then
  8,000 or 9,000 sq ft for 3, and 3,000 or 4,000 more per extra home.
- **R-3 and R-4 have two densities.** The higher one needs both 12,000 sq ft and 80
  ft of width.
- **Two parking spaces per home,** enclosed, at any size.
- **Commercial zones mostly bar new homes.** C-2 allows mixed use only around
  Crenshaw and Manchester, which we don't map, so those lots are too low.

**Worth a second reading:** P-1 lots show 1,496 homes today but zero allowed. Article
17 has no dwelling use, yet so many homes suggest parking zones may sit over
residential ones in practice. R-1Z's rear yard wasn't read; one home binds anyway.
Article 35 (ADUs) wasn't checked against the state path.

## 17. West Hollywood

Not on the site yet: publishing a new city's site files is the owner's call.

**Zoning data.** SCAG's table. 94.4% of lots are modeled. Not modeled: the
SSP zone (151 lots), other specific plans, and 78 lots SCAG doesn't match.

**Rules.** 17 zone files from Title 19: R1A, R1B, R1C, R2, R3A, R3B, R3C, R4A, R4B,
R4B-C, CN1, CC1, CC2, CA, CR, and no homes in CN2 and PF.

**How West Hollywood differs:**

- **R1-B and R2 use a stepped table** (Table 2-4), so "single-family" R1-B allows two
  homes on small lots and more on large ones.
- **Commercial zones have no density limit.** Homes are limited by FAR. We count the
  whole FAR as homes, which runs high, since a project must be mixed use. The
  Mixed-Use Incentive Overlay's extra FAR and the commercial-only overlay aren't in
  our data; one pushes numbers low and the other high.
- **Older buildings beat today's zoning:** R3 and R4 hold many lots with more homes
  than now allowed, which caps net new capacity.

**Worth a second reading:** R4B-C's FAR of 0.58 is printed in Table 2-3 and used as
printed, though it looks low for four stories (11 lots).

## 18. Monrovia

Not on the site yet: publishing a new city's site files is the owner's call.

**Zoning data.** SCAG's table. 85% of lots are modeled. The gap is planned
developments: 1,186 lots coded `PD`, each with its own ordinance. Also not modeled:
HC-D (72 lots; downtown's Chapter 17.14 wasn't read for density), specific plans,
HWP, ANF, 71 lots with no zone, and SCAG codes such as `1/5` that aren't in the code.

**Rules.** 17 zone files from Title 17: RF, RE, RL, RM2500, RM3000, RM3500, RM4000
(`/PUD` versions use the same files), RM/RH, RH, and no homes counted in NC, C-R/S,
RCC, RCM, O/RD/LM, BE, M and P/QP.

**How Monrovia differs:**

- **Home size has a sliding scale** in single-family zones, such as 40% of the first
  5,000 sq ft, 35% of the next 5,000, and 15% of the rest.
- **RM/RH and RH change at 15,000 sq ft.** Below it, homes are counted per lot area.
  Above it, there's no density limit, only 75% FAR, so large lots jump in capacity.
- **Six or more homes need more parking:** 2.5 spaces per home.

**Judgment calls:** lots smaller than a zone's minimum still get its density, since
we read the minimum as applying to new lots. RH sets no story limit in the code; we use
3, and FAR limits first. RM/RH uses RM's height. NC homes aren't counted, since the code
allows them only where the Land Use Element says, which we have no map of.

## 19. Santa Clarita

Not on the site yet: publishing a new city's site files is the owner's call.

**Zoning data.** SCAG's table. 88.1% of lots are modeled. Not modeled: specific plans
(3,713 lots), 1,287 lots with no zone, and PI, CP and the OS zones, whose rules weren't
read. The OS zones likely allow no homes.

**Rules.** 17 zone files from Title 17: NU1 to NU5, UR1 to UR5, MX-C, MX-N, and no homes
counted in CC, CN, CR, BP and I.

**Judgment calls, please review:**

- **Density is per gross acre.** We use lot area, so small infill numbers lean low and
  numbers for a lot within a larger project can differ.
- **The use chart's multifamily row didn't come through cell by cell.** We count
  multifamily homes in UR3 to UR5, as each zone's text describes, and not in CC and CR
  (single-family and two-family are marked X there), which may be too low. Read
  this row directly before relying on the commercial numbers.
- **Large single-family lots show one home,** since subdividing isn't modeled, so
  NU and UR1 are too low where lots could be split.
- **BP lots hold 2,570 homes today** but allow none, which suggests that SCAG's zones or
  planned developments don't tell the whole story there.

## 20. Duarte

Not on the site yet: publishing a new city's site files is the owner's call.

**Zoning data.** SCAG's table. 89.9% of lots are modeled. Not modeled: specific plans
(468 lots), O (71 lots), RMH and 11 lots with no zone.

**Rules.** 14 zone files from the Development Code: R1, R1A, R1B, R1D, R1E, R2, R3, R4,
and no homes in CG, CP, CF, H, M and PF. R-1F isn't on the map.

**How Duarte differs:** R-2 has no density table, so we cap it at two homes, since
multi-family isn't allowed there. Parking is heavy: 2 garage spaces per home plus
half a space more in apartments. R-3 and R-4 can go higher with a use permit, which
we don't count. M lots show 742 homes today but allow none, worth a second look.

## 21. Long Beach (residential zones only so far)

Not on the site yet: publishing a new city's site files is the owner's call.

**Zoning data.** SCAG's table has 174 zone codes. 70,010 of 87,365 lots (80.1%) are
modeled, and the rest hold 68,123 of 191,022 homes.

**Rules.** 14 files from Chapter 21.31: R-1-S, R-1-M, R-1-N, R-1-L, R-2-S, R-2-I, R-2-N,
R-2-A, R-2-L, R-3-S, R-3-4, R-3-T, R-4-R, R-4-N. Height-overlay versions such as
`R-2-N (HL-25/2)` use the same file; the overlay's lower height isn't modeled.

**Not done, and this is where Long Beach grows:** the newer mixed-use and multifamily
zones (MFR-L, MFR-M, MU-1 to MU-3, RMU3, RMU4), neighborhood commercial (CN*, CC*),
PD-30 and the other planned developments (3,882 lots), specific plans (2,990
lots), and institutional and industrial zones. Capacity is well understated until
those are done, which is why this city is marked ⚠️ in WAVE_PLAN.

**Judgment calls:** the density table sets bands by both area and width; we use area,
which can run high on narrow lots. R-2-A also allows three-family homes under a note
we didn't read, so it can run low. Parking uses 1.5 per home, for one bedroom.

## 22. Lancaster (residential zones only so far)

Not on the site yet. 8 files from Chapter 17.08 cover 43,082 of 52,372 lots (82.3%): RR-2.5,
RR-1, SRR, R-15,000, R-10,000, R-7000, MDR and HDR. Not done: specific plans (3,201 lots),
TOD (1,263), the MU zones, commercial and industrial zones, and 1,690 lots with no zone.

Judgment calls: where the code sets a sum of two side yards, we use half per side.
Corner-lot duplexes aren't modeled. MDR and HDR use the 55 ft height for smaller
complexes; larger ones can reach 72 ft. Open space and landscaping shares aren't
modeled, so those two can run high.

## 23. Gardena

Not on the site yet. 23 files from Title 18 cover 11,108 of 12,110 lots (91.7%): R1, R2, R3,
R4, Housing Overlay versions of commercial and industrial zones (`C3-HO-5` and so on),
and no homes in C3, M1 and M2. Not done: specific plans, the `-MUO` zones, HB, CR, O, CP,
C2, AMU and R6.

**What stands out:** Housing Overlays allow far more than the base zones, up to 70 homes
per acre on land where housing is otherwise barred, and that's where most new capacity
is. Their numbers use residential-only height; mixed-use gets more. R-3 and R-4 round
density up at .5; other zones' rounding wasn't stated, so we round down. M1 and C3 show
1,777 homes today but allow none, worth a second look.

## 24. Norwalk (R-1, R-2, R-3 so far)

Not on the site yet. 3 files from Chapter 17.05, including 2025's Ord. 25-1762, cover 20,444
of 21,751 lots (94%), since R-1 is 19,716 of them. Not done: R-4, R-H, commercial and
manufacturing zones, specific plans, and 128 lots with no zone. These zones aren't marked as
no-housing, as their chapters weren't read for homes.

**What stands out:** the 2025 FAR limits, 0.40 in R-1, 0.45 in R-2 and 0.50 in R-3, now
often limit homes as tightly as density. R-1's FAR means a 5,000 sq ft lot barely holds
one average new home.

## 25. Santa Fe Springs (R-1, R-3, R-4 so far)

Not on the site yet. 3 files from Chapter 155 cover 3,473 of 5,656 lots (61.4%). Much of the
rest is industrial land (M-1, M-2, ML), whose rules weren't read, so those lots are "not
modeled", not zero. Also not done: MU, C-1, C-4, A-1, and RR.

Judgment calls: `-PD` and `-D` lots use the base zone's rules, though a PD can set its own.
The city's site didn't load in our browser because of a certificate error, so the citations
are all to the code on Municode. Minimum lot sizes are read as applying to new lots.

## 26. Whittier (R-1 to R-4 so far)

Not on the site yet. 4 files from Title 18 cover 18,779 of 21,964 lots (85.5%). Not done: the
Specific Plan zone (809 lots), R-E and H-R, the MU zones, C-O, C-2, INV, MED, and others.

Whittier sets density by lot-size steps, and its height limit is 35 ft in every one of
these zones. **Parking wasn't read, so it isn't modeled here,** which can run high. R-4's
optional development standards allow more on small lots; we use base figures.

## 27. Arcadia (residential zones so far)

Not on the site yet. 6 files from §9102.01 cover 12,159 of 13,375 lots (90.9%): R-1, R-M, SCAG's
`R`, R-2, R-3, R-3-R. Not done: MU, DMU, CBD, commercial and industrial zones, R-R, OS, and
the SP-ALC plan. Ord. No. 2400 changed density and added zones recently; the Municode text
we read has R-3 at 40 per acre, which may be the updated figure.

**Judgment calls, please review:** SCAG's `R` isn't a zone in the code; we read it as R-0, as
its lots are large. It's capped at one home either way, so little depends on it. Floor area
uses the schedule for north of Huntington Drive; south allows more. Parking wasn't read.

## 28. South Gate (NL and NM so far)

Not on the site yet. 2 files from Chapter 11.25 cover 13,817 of 16,268 lots (84.9%). Not done: the
mixed-use and corridor zones (MS, TMU, HMU, CDR, CC, UN), and industrial and other zones. Parking wasn't read.

**Open question, please review:** NL's table allows 5 homes per acre and "max. 2 separate living
units" on a 5,000 sq ft lot. We read the second unit as an ADU, so one main home. NL lots
average about 1.4 homes today, so a duplex reading is plausible and would raise local capacity
a lot. State-law numbers (SB 9) are unaffected.

## 29. Culver City (residential zones so far)

Not on the site yet. 5 files from §17.210.020 cover 7,343 of 9,453 lots (77.7%): R1, R2, RLD, RMD,
RHD. Not done: the mixed-use zones (MU-1, MU-2, MU-I, MU-HD, MU-N, MU-MD, MU-DT, 1,510 lots), PD
(351), and others.

**How Culver City differs:** there's no minimum parking anywhere in the city, so parking never
limits homes here. Density is per gross acre, and we use the lot. R3 is in the code's table but
not on SCAG's map.

## 30. Montebello (residential zones so far)

Not on the site yet. 5 files from Chapter 17.10 cover 10,647 of 12,284 lots (86.7%): R-1, R-A, R-2,
R-3, R-4. Not done: C-1, C-2, C-M, C-R, M-1, M-2, and 386 lots with no zone.

**What stands out:** a 25 ft height limit in R-2, R-3 and R-4, and R-3's density equals R-2's. So
local zoning allows fewer homes than already exist: 16,732 against 18,911. A limit of 1 bedroom
per 1,000 sq ft of lot also applies and isn't modeled. We use the south of Beverly Boulevard
minimum lot size in R-1.

## 31. Rolling Hills Estates (R-A zones so far)

Not on the site yet. 4 files from Chapter 17.06 cover 1,979 of 3,232 lots (61.2%): RA-20,000,
RA-15,000, RA-10,000, RAE. All allow one home per lot. Not done: RPD (1,031 lots), CG-MU-OD, the
commercial zones and others. The lot coverage formula and parking weren't read in detail,
since one home binds first. The minimum lot sizes come from a search summary of §17.04.080.

## 32. West Covina (residential zones so far)

Not on the site yet. 6 files from Chapter 26, Article II cover 18,790 of 24,211 lots (77.6%): R-1, R-A,
MF-8, MF-15, MF-20, MF-45. Not done: PCD-1 (3,799 lots), SP (834), the T-4 and T-5 transect zones,
commercial and others.

Judgment calls: SCAG drops the lot-size suffix (R-1-6,000 up to 40,000), so all R-1 lots use the
smallest yards and minimum. Lower MF heights within 100 ft of single-family zones aren't modeled.
Parking wasn't read.

## 33. Westlake Village (most zones)

Not on the site yet. 11 files from Article 9 and two city district pages cover 2,930 of 2,976 lots (98.5%):
R-1, RPD, MHP, CPD, CR, BP, PI, OS, MU-SP No. 1, and the Corsa and Lindero districts of the North Business
Park Specific Plan. Not done: that plan's La Baya, Cedar Valley, Office, BP, CPD and PI districts (42 lots),
because its PDF is over the size our reader takes and no city page gives their standards.

Judgment calls, most of them conservative:

- **RPD (1,412 lots) counts one home per lot.** §9.6.080 ties homes to each site's General Plan designation,
  and we have no parcel map of those. Existing multifamily sites therefore show no new homes.
- **No SB 9 in RPD.** §9.14.090 names seven numbered RPD zones as single-family, but SCAG drops the number.
- **MHP counts one home per lot** (§9.7.040). The state ADU path still applies, which likely runs high.
- **MU-SP No. 1 counts no homes.** Only Planning Area F allows them, and we have no map of planning areas.
- **Corsa and Lindero run high.** The districts are capped at 145 and 462 homes, and the engine has no
  district cap: we get 306 and 637. The city's FAQ calls the 35-per-acre figure in the plan a typo, so we use its 32.

## 34. Alhambra (base zones)

Not on the site yet. 11 files from Title 23 cover 15,058 of 15,609 lots (96.5%). Not done: VSP (393 lots)
and the named specific plans (79 lots more), whose texts aren't in the code, and 79 lots with no zone.

**The zoning table is older than the code.** SCAG's Alhambra records are dated 2018 and use the names from
before the January 2024 code (Ord. 4823). We read R-1, R-2 and R-3 as RL, RM and RH, the zones implementing the
same General Plan designations. This is our reading, not a table in the code, and a lot rezoned since 2018 would
be wrong. CBD, EMC, PO, PF and OS keep their names.

Conservative calls: old CPD (298 lots) could be CMU (48 per acre) or AC (no homes), so it counts none. IPD and PO
need a conditional use permit for homes, so they count none, and P no longer exists. RH uses 24 or 43 per acre;
the 64-per-acre downtown area and the taller limits near freeways aren't mapped, so those lots run low.

## 35. Palmdale (base zones)

Not on the site yet. 27 files from Title 17 cover 41,206 of 47,732 lots (86.3%). Not done: SP (6,091 lots) and
435 lots with no zone. SCAG's Palmdale records are dated 2023 and use the current zone names, except the three below.

Judgment calls: homes count only where a table gives a residential density. EMPFX (742 lots), CA and IND aren't
names in the tables we read. IND is treated like LI and HI, and EMPFX and CA count no homes. UT, OS and the PF zones
count none, and their chapters weren't read. RC counts none, because its homes are limited to two areas we don't
map. SFR side yards use the 7.5 ft average of 5 and 10. RN 1 is read as attached and detached homes, with 2 stories
instead of the table's 2.5. Multifamily parking uses 1.5 spaces and 0.2 guest, the two-bedroom figure for 5 or more homes.

## 36. Carson (base zones)

Not on the site yet. 15 files from Article IX cover 19,829 of 21,183 lots (93.6%). Not done: SP (786 lots) and 568
lots with no zone. SCAG's Carson records are dated 2016. The code on eCode360, dated July 2026, still uses the same
zone names, so no name matching was needed, but a lot rezoned since 2016 would be wrong. City drafts from 2023 and 2024
describe a replacement code with LDR, MDR and HDR districts, which we did not find in the code as published.

Judgment calls: the code limits RS and RM to 30 ft without a story count, so we fit 2 stories. Front and rear yards use
the fixed 20 and 15 ft, which runs low on lots under 100 ft deep, because the code takes the lesser of that or a percent of
depth. Coverage uses RM's 40%, not the 70% with structured parking. MU zones need a conditional use permit and 100 ft of
frontage; we count them, and narrower lots are flagged, not zeroed. The Mixed-Use Residential overlay isn't in our data, so
CG, CN and CR count no homes. ML, MH, OS and SU count none, and we didn't read their uses.

## 37. Azusa (neighborhoods and corridors)

Not on the site yet. 21 files from Chapter 88 cover 7,134 of 8,553 lots (83.4%). Not done: SP-MN (1,050 lots), the downtown
codes DTC, DTV and DCC (126 lots, which the code sends to the Azusa TOD Specific Plan), the University zones MU, RM and RMO
(68 lots, likely DU-MU, DU-RM and DU-RMO), and 175 lots with no zone.

**The map is old.** SCAG's Azusa records are dated 2005, the year this code was adopted. The TOD Specific Plan came in 2020 (Ord.
2020-02), and we have no map of it, so corridor and neighborhood lots it changed would be wrong.

Judgment calls: low-density lots count one home, because Table 2-1 allows no duplexes there. Corridors count all-residential
buildings at 27 homes per acre, using the 40 ft mixed-use height, which can run high. Multifamily parking uses the 2 spaces for two
to four bedrooms plus 1 guest space per 3 homes at five or more; single-home parking wasn't read. DE, DW and DWL count no homes, on a partial
read of the use table. OS, Ins and Rec count none, and their uses weren't read.

## 38. Lomita (most zones)

Not on the site yet. 18 files cover 4,209 of 4,270 lots (98.6%). Not done: R1P (22 lots), the Crenshaw Blvd plan (5 lots), and 34 lots with no zone.

**The zoning table is older than the code.** SCAG's records are from 2023. The code's residential article was reenacted in June 2026 (Ord. 891)
with A-1, R-1, R-2 and R-3. We read R1 and A1 as R-1 and A-1, and R1-6000, R1-7000 and R1-7500 as R-1. We read the number in RVD zones as sq ft per home, which is
our inference, and keep that density as long as it fits the new zone: RVD2500 is R-2; RVD2200, RVD1500, RVD1452 and RVD1000 are R-3; RVD5000 is R-1.
A city rezoning under the new code could change any of these.

Conservative calls: commercial zones count no homes, because homes need a conditional use permit in a mixed-use project, and stand-alone homes are
limited to a Housing overlay we don't have. Lots in the overlay run low. Stories aren't in the code, so we fit 2 at 27 ft and 3 at 35 ft. South of Pacific Coast Highway the limit is 16 ft and one story
without a variation permit, which we don't map, so those lots run high.

## 39. Hawthorne (most zones)

Not on the site yet. 16 files cover 11,199 of 11,536 lots (97.1%). Not done: SP (281 lots) and 56 lots with no zone. SCAG's records are dated 2016, and the code
still uses the same zone names, though Ord. 2263 reorganized its residential standards in June 2026. A lot rezoned since 2016 would be wrong.

Judgment calls: R-2 counts two homes at 7,000 sq ft and one below, reading the duplex minimum with §17.21.020. R-3 and R-4 count one home under 5,000 sq ft, and 1,452 sq ft per home above it.
Stories come from §17.21.025 at 22 ft (2); it says nothing for 45 and 60 ft, so we fit 3 and 5. The 12 ft limit on narrow small lots and per-home open space aren't modeled, so those run high.
The Mixed Use Overlay counts all-residential buildings at 30 per acre, which runs high unless 20% of homes are affordable, since it otherwise requires commercial space.

Conservative calls: plain C-3, C-R, C-2, C-M, M-1, M-2, UOS, H, P and AMP count no homes, and most of their use lists weren't read closely. The Housing overlay isn't in our data, so lots there run low.

## 40. San Gabriel (residential zones)

Not on the site yet. 17 files cover 8,308 of 8,351 lots (99.5%), but only the residential zones count homes. 43 lots have no zone. SCAG's records are dated 2016, and the code still uses the same
residential names, though a lot rezoned since 2016 would be wrong.

**Letter suffixes.** SCAG shows R-1 V, R-2 G, R-3 A, C-1 M, C-3 M and GMD. None of those letters are in §153.015's list of zones. We read R-1 V, R-2 G and R-3 A (231 lots) as overlays on the base zone with its rules, which
may miss added limits. This is an open decision.

Judgment calls: R-1's coverage and FAR of 35%, and R-3's coverage of 60%, come from city handouts, not sections of the code we read; R-3's handout is from 2014. R-3 uses its yards at three stories (21, 15 and 16 ft). R-1's and R-1A's parking wasn't read.

Conservative calls: C-1 and C-3 count no homes. They allow mixed use under §153.164, which we could not open, so mixed-use sites run low. MD (73 lots), GMD, MF, PF/OS and P-1 count none, and their uses weren't read. M-1 counts none, per the use table.

## 41. Monterey Park (residential zones)

Not on the site yet. 12 files cover 13,209 of 13,300 lots (99.3%), but only R-1, R-2 and R-3 count homes. Not done: GVC-S and GVN-S (73 lots) and 18 lots with no zone. SCAG's records are from 2025.

**Density.** Table 21.08F sets maximum homes by lot, and we could not read it on eCode360. We use the per-acre maximums in §21.08. A city summary shows the top tiers match that density, and says lower tiers cover smaller lots, so smaller lots may run high.
**R-3 conflict.** The chapter says 25 homes per acre. A city handout dated October 2024 (Ord. 2247) says 30, and the Housing Element called 25 inconsistent with the General Plan. We use 25 and record the question as an open decision.

Other calls: parking uses 1 space for 2 or fewer bedrooms, with no guest parking; larger homes need more. Open space of up to 850 sq ft per home isn't modeled, so R-2 and R-3 can run high. N-S, C-B, R-S and C-S allow mixed use only in General Plan Mixed-Use areas we have no map of, so they count none and those lots run low. S-C and C-P are marked X. O-P, O-S and S-P count none, and their uses weren't read.

## 42. Agoura Hills (most zones)

Not on the site yet. 17 files cover 6,427 of 6,531 lots (98.4%); RS, RM, RL, RV, RH, CS-MU and OS-R count homes. Not done: SP (83 lots, 475 homes on the roll) and 21 lots with no zone. The SP lots matter most: 278 of the 296 homes permitted in 5+ unit buildings in 2018-2025 are there, in specific plans such as Agoura Village that we haven't read. §9497 sends those lots to each plan. SCAG's records are from July 2016, and we haven't checked for rezoning since, so newer zones such as the Affordable Housing overlay's sites may not show.

**Density.** The code sets density by a number after the zone, such as RM-10 or RH-25, and SCAG drops it. RM uses RM-6 (6,000 sq ft per home) and RH uses RH-15 (2,400), the lowest of each range, so lots zoned higher run low.
**Parking.** RM, RH and CS-MU use 2.5 spaces per home, the §9654.2 figure for one bedroom and up. Studios need 1.5.
**OS-R.** One home per lot is allowed, but only with a conditional use permit (§§9482 and 9483). We count it, with its 50, 25 and 50 ft yards and 10% coverage, and ADUs under §9484. We don't apply SB 9, since this is an open space district. This is an open decision.

Other calls: we have no slope data, so the hillside rules (§9652, lots over 10% average slope) aren't modeled and hilly lots can run high. RS uses 20 ft front and rear yards and 9 ft sides at every size; lots of 10,000 sq ft or more really need 25, 25 and 11, so they can run high, though their 35% coverage usually binds first. CS-MU counts each lot alone, ignoring its 5-acre project minimum and required commercial space, so small lots run high. The Affordable Housing overlay isn't in our data, so its sites run low. CRS and BP-M allow only a caretaker's residence, which we don't count. The assessor counts some hotels as homes in those zones, so the existing-homes column runs high there. Section 1 of the validation is skipped until the state's E-5 file is saved; no city has it yet.

Rule file check added: a `lot_coverage` band written with `value` under 1 now fails to load. `value` means square feet in those bands, and the first Agoura draft's RS file showed zero local homes on 4,530 lots because of it. No other city's files had this mistake.

## 43. Torrance (most zones)

Not on the site yet. 22 files cover 32,150 of 33,738 lots (95.3%). Not done: PD (602 lots), DT (223), the Hawthorne Boulevard Corridor plan's H- codes (420), 176 lots with no zone, and about 170 lots with codes like A1/R2 or R1(RP). SCAG's records are from August 2025. The gaps matter: of 145 homes permitted in 5+ unit buildings in 2018-2025, 130 are on unmodeled lots, 78 of them in DT. Article 40 allows homes in DT with a conditional use permit but gives no density, so we left it out.

**R-3 floor area.** §91.7.9 sets FAR 0.6 without garages. Since Ord. 3896 and 3897, developments of 3 to 7 homes get 1.0 and of 8 to 10 homes get 1.25, counting garages. We pick by the homes a lot's area allows, so lots of 17,600 sq ft or more fall back to 0.6, and FAR limits them below 1,600 sq ft per home. R-3-3 works the same way, with a cap of 3 homes.
**C-1 and C-2.** Homes need a conditional use permit. Each article points to R-4's lot area (1,000 sq ft) and also says 1,600 per home. We use 1,600 and record it as an open decision.
**-PP codes.** These mark precise plans (Ch. 6, Art. 2), which can set site-specific height and bulk we have no text for. They use the base zone's rules, so some can run high.

Other calls: parking uses 2 spaces, the figure for 2 bedrooms or fewer; 3 bedrooms or more need 3. R-3 and similar zones use 2 stories, since more needs a permit. R-4, C-1 and C-2 limit height to 50 ft, and we fit 4 stories. R-5 has no fixed height, so we assume 6 stories and its table's FAR of 0.78. A-1 gets no SB 9, as with LA's A1 and A2. R-TH uses 12 homes per acre and sets no yards. Open space per home isn't modeled in the apartment zones, so they can run high. Not in our data: the Housing Corridor Overlay and the religious and higher education housing overlay, so those sites run low, and the hillside overlay, so those lots can run high.

Known artifact: 54 lots show 0 homes because surface parking takes the room, 43 of them single townhome lots in R-TH with homes on them today. Their real parking is in shared areas the lot-by-lot model can't see. R-1's 6,000 sq ft minimum flags about 15,000 smaller existing lots; it doesn't reduce their capacity.

## 44. Artesia (most zones)

Not on the site yet. 13 files cover 3,719 of 3,793 lots (98.0%); R-1, M-R, M-D-R, M-C-R, C-O and A-1 count homes. Not done: five specific plans (52 lots) and 22 lots with no zone. SCAG's records are from December 2022. Of 81 homes permitted in 5+ unit buildings in 2018-2025, 64 are on unmodeled lots, 26 of them in the Arkansas Street plan.

**Rounding.** M-R and C-O round to the nearest home, with exactly .5 rounding up (§§9-2.2904 and 9-2.3503), so a lot can get a home it's slightly short of.
**M-C-R.** It allows R-1's uses, so one home per lot. We treat it as commercial, so ADU law applies and SB 9 doesn't.
**C-O.** Condominiums only, at 3,000 sq ft per home and 2 stories (Art. 36). Its 60,000 sq ft minimum flags most of these lots but doesn't reduce them.

Other calls: M-R parking uses 2 spaces plus about 1 guest space per 3 homes at 4 or more homes; more bedrooms need more. Outdoor living space isn't modeled, so M-R can run high. A-1 gets no SB 9, as an open decision. C-G, C-S-P, CPD, M-1, M-2 and OS-R list no homes; M-1's shelters aren't counted. We couldn't confirm H-D's uses, so its 2 lots count none. The Housing Opportunity (Art. 29.7) and Mixed-Use (Art. 48) overlays aren't in our data, so their sites run low.

## 45. Avalon (most zones)

Not on the site yet. 8 files cover 1,037 of 1,054 lots (98.4%); HD-R, MD-R, LD-R and SC count homes. Not done: PB-SP (7 lots), 8 lots with no zone, HD-R-CH (1 lot with 62 homes) and LI (1 lot). SCAG's records are from September 2018, and we haven't checked for rezoning since.

**Don't trust the city total.** One 169-acre lot mapped HD-R gets 6,748 of the 7,704 HD-R homes, and 6,739 of the 6,963 "likely to redevelop" homes. That's what 40 homes per acre gives on paper, but the lot is far larger than any other HD-R lot, and the slopes, fire access and the Annual Growth Policy (Ch. 9-12) aren't modeled. It's more than twice the 2,593 homes on the whole city's roll. The map may also be wrong for this lot. We report it as computed and record it as an open decision. Likewise, three LD-R parcels of 251 to 514 acres get 1,119 of that zone's 1,529 local homes.

**Slopes.** Avalon's limits depend on slope, and we have no slope data. HD-R, MD-R and SC use the standards for lots of 14 degrees or less. Hillside lots allow 3 stories but less floor area at two levels, so they can differ either way. LD-R's density runs from 10 homes per acre under 30 degrees to 1 at 50 degrees or more; we use 1 per acre, and lots under an acre keep one home, so gentler lots run low.
**SC.** Homes need a conditional use permit and follow HD's standards (§9-6.303(b)).

Other calls: parking is 1 space per home. MD-R's attached and clustered homes need a conditional use permit, but we count them up to the density. C and R/R list hotels and mobile home parks but no other homes, so they count none. We didn't read P's uses, so its 9 lots count none. The Article 5 low and moderate income zone isn't among SCAG's codes, unless that's what LI means. Avalon's inclusionary and growth rules aren't modeled.

## 46. Baldwin Park (most zones)

Not on the site yet. 11 files cover 13,516 of 13,598 lots (99.4%); R1, RG, R3, MU-1 and MU-2 count homes. Not done: 82 lots with no zone. SCAG's records are from January 2017, and we haven't checked for rezoning since. Of 130 homes permitted in 5+ unit buildings in 2018-2025, 56 couldn't be placed on a zoned lot.

**R-1.** SCAG writes R1 for both R-1 and R-1-7,500, so all use R-1's rules, and the stricter R-1-7,500 lots can run high. The use table lists single-family homes only, while the zone's intent, amended by Ord. 1503, mentions duplexes. We use one home and record it as an open decision.
**MU-2.** Density is 15 homes per acre under 20,000 sq ft and 30 above it. The table doesn't cover exactly 20,000 sq ft; we use 30.
**Mixed use.** All new development must include commercial space, which we don't subtract, so MU-1 and MU-2 can run high. Parking uses the apartment figure, as the code has no separate mixed-use one that we found.

Other calls: heights are limits in feet, so we fit 2 stories at 27 and 35 ft and 4 at 50 ft. Parking uses 2 spaces plus 1 guest space per 3 homes. Open space per home isn't modeled in R-G, R-3, MU-1 or MU-2. Yards next to R-1 aren't modeled. C-1, C-2, F-C, I-C, I and OS list no homes. The Sierra Vista, Housing Element re-use and planned development overlays and any specific plans aren't in our data.

Known artifact: 351 lots show 0 homes, 319 because their yards leave too little building and 32 because surface parking takes the room. Most are narrow small-lot homes (about 20 ft wide) built under other approvals, with about 270 homes on them today. Reports count them as no capacity, not as homes to lose.

Pipeline fix: the assessor roll here has a record with no parcel number sharing a shape with numbered ones, which crashed the condo merge. Such records now stay in the lot, and only real parcel numbers are listed.

## 47. Bell (most zones)

Not on the site yet. 7 files cover 4,170 of 4,231 lots (98.6%); R1, R2, R3 and C3R count homes. Not done: POL (24 lots), T (4), LAR (1) and 32 lots with no zone. We didn't find POL or LAR in the chapters we read. SCAG's records are from November 2018, and we haven't checked for rezoning since. The state's reports show no homes permitted in 5+ unit buildings in 2019-2025, so the permit check tells us little here.

**C-3R (369 lots).** §17.28.020 allows R-3's principal uses and lists residential uses with a conditional use permit, but Chapter 17.28 states no density. We apply R-3's 1,452 sq ft per home, its 50% coverage, its 3 stories and 35 ft, and its side and rear yards, though the zone itself allows 70 ft and full coverage outside yards and parking. This drives 3,381 homes and is an open decision.
**R-3.** Most of the city's lots are here. One home per 1,452 sq ft (30 per acre) binds on nearly every lot. Its 7,200 sq ft and 60 ft minimums apply to lots created after 1989, so older lots are flagged but keep their capacity. Private open space of 150 sq ft per home isn't modeled, so these can run high.
**R-1 and R-2.** We found no coverage or floor area limit in these chapters, so yards and 2 stories set the envelope. The one- and two-home limits bind anyway.

Other calls: parking uses 2 spaces per home, plus 1 per 3 multifamily homes as guest space. Fronts use the stated 25 and 15 ft, not the block's average, which can be less. C3 lists no homes; CM and M allow only caretakers' quarters, which we don't count. The Mixed-Use and Planned Development overlays aren't in our data, so those sites can differ.

Known artifact: 18 lots show 0 homes because yards or parking leave too little room; most are slivers or narrow small lots, with 2 homes on them today.

## 48. Bell Gardens (most zones)

Not on the site yet. 11 files cover 4,080 of 4,094 lots (99.7%); R-1, R-2, R-3, R-4 and M-U count homes. Not done: MPD (3 lots) and 11 lots with no zone. SCAG's records are from April 2023. All 19 homes permitted in 5+ unit buildings in 2018-2025 are on modeled lots.

**R-3.** Density depends on lot size: under 5,000 sq ft one home, then 2,500, 2,000 and 1,750 sq ft per home at 5,000, 15,000 and 43,560 sq ft. Those are the apartment figures. Condominiums need a conditional use permit and may reach 2,000, 1,625 and 1,400 sq ft per home, so condominium sites run low.
**R-4 (107 lots).** §9.10.010 names R-4 (its history note cites Ord. 929 of 2023, though we didn't read that ordinance), but the use and standards tables have no R-4 column that we could find. It should allow more than R-3, so we use R-3's standards as a low bound and record it as an open decision. This drives 660 local homes.
**R-2.** One home under 5,000 sq ft, then 2,500 sq ft per home, up to 3.
**M-U.** 30 homes per acre on lots of 15,000 sq ft or more in the standards table. Commercial space isn't subtracted, and §9.12.020 limits commercial FAR, so we don't apply an FAR limit to homes. M-U can run high.

Other calls: the residential table limits height to 35 ft without a story limit, and we fit 2. M-U's 60 ft fits 4. At 5 or more rental homes, 20% common open space and 75 sq ft private open space per home aren't modeled. Added second-story setbacks aren't modeled. C-S's 30 homes per acre is for senior housing only, so we count none. C-4 and C-M allow no homes, per §9.12.020; M-1 and P-I list none; O-S allows only a caretaker's residence. Overlays, including the Housing Element re-use sites, aren't in our data.

## 49. Bellflower (most zones)

Not on the site yet. 10 files cover 11,814 of 11,938 lots (99.0%); S-F, R-1, A-E, R-2 and R-3 count homes. Not done: four specific plan codes (87 lots, 419 homes), SCH (3 lots, 350 homes) and 34 lots with no zone. SCAG's records are from April 2023. Of 18 homes permitted in 5+ unit buildings in 2018-2025, 13 are in SP No. 7.

**Town Center (130 lots).** §17.48.130 lets the Planning Commission approve homes on the second floor and above, but the chapter states no density. We count none and record it as an open decision, so this area runs low.
**R-1.** §17.24.100 sets 5,000 sq ft per home, and §17.24.110 covers lots with two or more single-family homes, so larger lots count more than one. SCAG drops any larger-lot suffix, so those lots can run high.
**R-2 and R-3.** Side and rear yards depend on the wall: 8 ft for living and bedroom walls, 5 ft for secondary walls. We use 8. R-3 applies its 25% group open space; private open space isn't added. R-2's open space wasn't applied. The 2/3 rule for top stories isn't modeled in either, so floor area can run high, though density binds on most lots. Parking uses 2 spaces plus 1 visitor space per home.
**A-E.** 9,900 sq ft per home, 30% roof area and 40% floor area, which a conditional use permit can raise. Rear yards grow with depth; we use the 15 ft minimum. SB 9 isn't applied, as an open decision.

Other calls: C-G, M-1, Public Uses and Open Space list no homes. The roll shows homes in C-G and M-1 (2,191 and 1,799), which may be mobile home parks or older uses; we didn't check them. These lots count no capacity. The Housing Opportunity and planned development overlays aren't in our data, so those sites run low.

Known artifact: 202 lots show 0 homes because yards or parking leave too little room, mostly narrow R-2 lots, with 160 homes on them today.

## 50. Beverly Hills (most zones)

Not on the site yet. 11 files cover 7,982 of 8,065 lots (99.0%); only R-1 and R-4 count homes, through aliases for their variants. Not done: PRG (56 lots), two specific plans (6 lots), C-3B and C-Z (1 lot each) and 19 lots with no zone. SCAG's records are from May 2023. Of 136 homes permitted in 5+ unit buildings in 2018-2025, 54 are on C-3 lots, where we count none, and 33 couldn't be placed on a zoned lot.

**C-3.** §10-3-1601 lists no homes, but the city has several mixed-use overlays (Arts. 18.7, 19.3, 19.8, 19.9, 19.95) that aren't in our data. The 54 permitted homes suggest they're being used, so commercial lots run low.
**R-4 density.** §10-3-2801 sets density by lot width and by site: within 170 ft of a single-family lot, on a street under 34 ft wide, or neither. We have no street widths, so all sites use the strictest set: 1,700, 1,450 or 1,200 sq ft per home for lots under 60, 60 to 120, and over 120 ft wide. A remainder over 75% rounds up. Other sites can reach 900 sq ft per home, so many lots run low. We leave out the efficiency bonus home. This is an open decision.
**R-4 aliases.** Article 14 restricts R-4X2 as Article 12. R-4X1, R-3, R-4-P and RMCP allow multiple-family homes, and we use R-4's standards for them. R-4-P's other uses need a planned development; RMCP also allows convenience retail.
**Existing homes.** R-4 lots hold 10,762 homes against 6,984 allowed. §10-3-2801.E lets lawful existing homes be rebuilt, which we don't count as new capacity.
**Heights.** Districts A, B and C allow 33, 45 and 55 ft. We have no district map, so all use A's 33 ft and 3 stories.

**R-1.** R-1 and R-1.X through R-1.8X give the same one-family use (Arts. 5 to 11). We use the Central Area's floor area of 1,500 sq ft plus 40% of the lot. The Hillside and Trousdale standards aren't modeled, and we have no map of those areas. Front and rear yards are assumed, and we didn't read all of §10-3-2406's side yard rules; the one-home limit binds either way.

We didn't read C-3A, P-S, S or T-1's uses or all of C-5's, and assumed C-3T-1 and C-3T-3 follow C-3T-2; all count no homes.

Known artifact: 50 R-4 lots end at parking, mostly large lots, with 1,452 homes on them today. The surface parking model likely runs low where real projects use garages.

## 51. Bradbury (all mapped zones)

Not on the site yet. 6 files cover 418 of 426 lots (98.1%); only 8 lots with no zone are left. Every housing zone allows one home per lot. SCAG's records are from December 2015, and we haven't checked for rezoning since. The state's reports show no homes permitted in 5+ unit buildings in 2020-2025.

**SB 9.** Unlike Torrance, Artesia and Bellflower, Bradbury's own code names its A-1, A-2 and A-5 zones as single-family zones for SB 9 (Ch. 85, Art. IV), so SB 9 applies to them here. But it excludes very high fire hazard zones, as state law does, and we have no fire map. Much of the city is in the foothills, so the SB 9 total of 4 homes per lot likely runs high.

Other calls: R-7,500 uses the two-story limits of 35% coverage and FAR 0.50, with a 25 ft front. Second stories also need 20 ft side and 30 ft rear yards, not modeled. R-20,000 and the A zones limit height to 28 ft, and we fit 2 stories. Ridgeline rules (Ch. 43), the 50 ft private street setback and parking aren't modeled; the one-home limit binds anyway. Many lots are smaller than their zone's minimum (177 flagged), which doesn't reduce their capacity here. OS allows no homes. The Affordable Housing Overlay (Ch. 88) isn't in our data.

## 52. Calabasas (all mapped zones)

Not on the site yet. 16 files cover 7,321 of 7,332 lots (99.8%); only 11 lots with no zone are left. SCAG's records are from March 2023. All 158 homes permitted in 5+ unit buildings in 2018-2025 are on modeled lots, but 78 of them are on PF land, where we count none; we didn't look into how those were approved.

**RM density.** The table allows 24 homes per acre, but a zoning map suffix can set less (the code's example is RM-12D), and SCAG drops suffixes. We can't see which lots have one, so RM uses 24 and can run high. Densities above the minimum of 20 also need the impact findings in Ch. 17.60, not modeled. This is an open decision, and it drives 5,866 local homes.
**HM, OS and REC.** Each allows one home per lot. We don't apply SB 9 in these districts; ADU law applies. Table 2-7 is merged across columns, so we read its yards for HM and OS as 50, 25 and 50 ft, and REC's as set by a development plan.
**CMU and CT.** Homes need a conditional use permit, at up to 24 and 20 per acre, with FAR 1.0. Commercial space isn't subtracted, so these can run high. Table 2-6's rear yard row is merged, and we read 20 ft for CMU and 30 ft for CT.
**RMH.** One 45-acre mobile home park, at 8 homes per acre, shows 361 homes. The assessor counts it as 1 home, so its net new figure of 360 is false: the park already holds its homes.

Other calls: multifamily parking uses the two-bedroom figure of 2 spaces plus 1 guest per 3 homes. We have no slope data, so the hillside rules (§17.20.150) aren't modeled, and much of the city is hilly, so totals can run high. CL, CO and CB allow no homes under Table 2-6; CR lists none in Table 2-2; OS-DR and PF allow none under Table 2-7. The Affordable Housing overlay isn't in our data, so its sites run low.

Known artifact: 324 lots show 0 homes because yards leave too little room, 303 of them small RM lots such as townhomes, with 300 homes on them today.

## 53. Cerritos (most zones)

Not on the site yet. 15 files cover 14,759 of 15,310 lots (96.4%); RS-5000, RS-6500, ADP-4 (through RS-6500), RM and ADP-3 count homes. Not done: 14 other Area Development Plans (528 lots, 1,119 homes), A (2 lots) and 21 lots with no zone. Area Development Plans replace normal zoning, so each needs its own chapter read. SCAG's records are from March 2023. The state's reports show no homes permitted in 5+ unit buildings in 2019-2025.

**RM.** Multi-family use needs a 3-acre lot (§22.23.700), so smaller RM lots count one single-family home, even though many hold more today. RM holds 1,262 homes against 525 allowed. Up to 20 homes per acre applies above that, and the approving authority sets the exact number, so large lots can run high. We didn't capture the zone's height limit and fit 2 stories.
**ADP-3.** 1 home per 3,260 sq ft on parcels of an acre or more; smaller parcels are single-family under RS-6500's standards. We use RS-6500's yards and coverage everywhere, an assumption for larger parcels. Most lots here are single townhomes or small homes.
**ADP-4.** Single-family only, under RS-6500's standards. Its added standards, which govern where stricter, weren't read; the one-home limit binds.
**RS.** Coverage is 40%, or 45% for RS-5000 lots meeting the chapter's other standards, with FAR 0.70. SB 9 is what lifts these lots above one home.

Other calls: OS allows only caretakers' residences, and we don't count its 295 homes on the roll; we didn't check what those are. CN lists no homes. We didn't read the uses of COP, CC, CR, M, MC, MC-1, MC-2, M-1 or OS-1, which count none. We wrote MC's name from the Ch. 22.29 title without checking the map symbol.

## 54. Commerce (Title 19, most zones ⚠️)

Commerce's zones come from Commerce Municipal Code Title 19 (Municode, Supp. 15, through Ord. 829, read November 2, 2026). Eight rule files cover 3,918 of 4,022 lots (97.4%). The other 104 have no zone in SCAG's data. SCAG's zoning here dates from 2016.

**R-1.** One home per lot, with a 40% floor area limit and 45% coverage. SB 9 is what lifts these lots above one home.
**R-2.** The table's two figures match its density range: 3,000 sq ft per home for two detached homes (14.52 per acre) and 5,000 per duplex home (8.71 per acre). We use 3,000, with two homes at most, so the count assumes detached homes.
**R-3.** 2,000 sq ft per home. A note says rounding up "may allow" more density; we round down. Lots under the 7,500 sq ft minimum count one home, which covers 255 of the zone's 414 lots, though the table also permits duplexes. R-3 holds 1,120 homes on the roll against 1,539 at our maximum, and some lots are already far over: 7141 E Gage Ave has 15 homes where the rule gives 5.
**C-2.** Its use table permits multifamily and single-family homes outright but states no density, so its floor area ratio of 0.5, coverage and parking set the count. That gives 1,969 homes, mostly paper: four lots over 400,000 sq ft hold 1,000 of them.
**Manufacturing and PF.** C/M-1, M-1, M-2 and PF allow only caretaker quarters, art studios with an associated residence (C/M-1 and M-1), or a caretaker dwelling with a conditional use permit (PF). We count none, though the roll shows 635 homes in these zones.

Not modeled: the Modelo Specific Plan (§19.16.020), which isn't in SCAG's data and whose standards we didn't read; the Planned Development overlay (Chapter 19.15); the conditional use permit for homes over 2,300 sq ft.

## 55. Compton (Chapter 30, most zones ⚠️)

Compton's zones come from Compton Municipal Code Chapter 30 (eCode360, through July 14, 2026, read November 3, 2026). Ten rule files cover 19,490 of 19,633 lots (99.3%). The other 143 are 130 lots with no zone and 13 in SP, a zone whose plans we didn't read. SCAG's zoning here dates from 2023.

**PR zones.** §30-17.2 combines the parking zone with residential zones. SCAG's PRL, PRM and PRH use R-L's, R-M's and R-H's rules.
**R-L and R-A.** 5,000 and 10,000 sq ft per home. The code allows more than one home on a lot only if each could be legally divided off and fits the original subdivision. We don't test that, so large lots can run high: local rules give 14,128 homes on R-L's 11,057 lots. SB 9 is what lifts most of these lots above one home.
**R-M and R-H.** 2,500 and 1,500 sq ft per home. Five or more homes on a parcel need a conditional use permit, which we assume is granted. Parking assumes attached homes with two or fewer bedrooms: 1.5 spaces plus a quarter guest space. The code limits height to 35 ft, not stories, and we fit 3.
**C-L.** Homes need a conditional use permit, then 1,500 sq ft per home with R-H's yards. This matters: C-L adds 14,372 homes under local rules, more than R-H, and its largest lots are shopping centers such as 101 Towne Center Dr at 308 homes. The state's reports show no homes permitted in 5+ unit buildings in 2019 to 2023, so treat this as a legal limit, not a forecast.
**C-M, M-L, M-H, B and P.** C-M, M-L and M-H prohibit homes apart from small caretakers' quarters and permitted live-work units; B prohibits buildings; P alone is parking. We count none, though the roll shows 805 homes in these zones.

Not modeled: senior homes at 1,250 sq ft each; unit size limits; R-H's open space; Planned Development (§30-18); the Emergency Shelter Overlay. §30-20.2 accepts a smaller lot's area only if its deed predates September 20, 1946; we count one home on every smaller lot, since we can't tell.

## 56. Claremont (Title 16, most zones ⚠️)

Claremont's zones come from Claremont Municipal Code Title 16 (eCode360, through Ord. 2026-02 of July 14, 2026, read November 2 and 3, 2026). 31 rule files cover 9,526 of 10,014 lots (95.1%). The other 488 are 368 lots in Specific Plan areas, 118 with no zone, and one each coded HDRO and LA COUNTY. SCAG's zoning here dates from 2016.

**The biggest gap is the Housing Opportunity Site Overlay.** Chapter 16.014 (2024) allows 30 to 60 homes per acre on the Housing Element's sites, with a minimum of 20 per acre. SCAG's 2016 data doesn't show it, and we have no map, so these sites count their older base zone and run low. We read the MFR 30 table and part of MFR 60's.
**Specific Plan areas.** Chapter 16.081 lists them, but each plan is a separate document we didn't read. SP2 and SP5 to SP9 hold most of those lots, and the areas have 834 homes on the roll in all. Their homes aren't counted.

**RS, RR, HC and AV.** One home per lot. Floor area limits apply: 2,000 sq ft plus 15% of the lot, up to each zone's cap (1,500 plus 25% in AV), and they include attached garages. SB 9 is what lifts these lots above one home.
**RM.** 4,000, 3,000 and 2,000 sq ft per home. Lots in RM (3000) and RM (2000) under 12,000 sq ft use 4,000, and any RM lot under 8,000 sq ft gets one home, as the chapter says. Outdoor living area, 400 sq ft per bedroom on larger homes, isn't modeled and could bind before density. Parking uses the rate for homes of 720 sq ft or more.
**MU1, MU2 and MU3.** 22, 22 and 15 homes per acre, with parking at 2 spaces plus a half guest space. The one-acre minimum applies to new lots; most MU lots are smaller, and we count them. The Planning Commission reviews many projects.
**CP.** Multiple-family homes with a conditional use permit at 3,000 sq ft each, under RM (3000)'s standards. The roll shows 1,261 homes against 770 under local rules. Lots under 8,000 sq ft count none.
**CN, CL, CH, CV.** Homes need a conditional use permit as part of a mixed-use project, with no stated density. We count none, and the same for CF, B/IP and CR.
**IE and IR.** Campus and senior housing under master plans, with no density we could find. We count none, though the roll shows 2,316 homes in IE and 322 in IR.
**H (Hillside).** The slope tables set 1.08 to 19.61 acres per home, and homes are allowed only in a mapped overlay near two roads. We have neither slope data nor that map, so each lot counts one home with no SB 9. This may count lots where no home is allowed.
**P/RC, WP, P and CR.** We searched these chapters for residential uses rather than reading each in full, and found none.

The state's reports show 14 homes a year in 5+ unit buildings, 2018 to 2025. Half of the matched ones fall in zones we don't model.

## 57. Covina (Title 17, most zones ⚠️)

Covina's zones come from Covina Municipal Code Title 17 (eCode360, read November 3, 2026). 25 rule files cover 9,885 of 11,599 lots (85.2%). SCAG's zoning here dates from 2022.

**The big gaps are plans, not zones.** 1,170 lots are in Planned Community Development (PCD) districts, each built to its own precise plan (Chapter 17.58), so we don't use the underlying zone. 428 are in the Town Center Specific Plan (TCSP), and 40 in the CFSP and CBSP plans, which we didn't read. The rest are 73 with no zone, two in A-1 and A-2, and one coded COUNTY. Of homes permitted in 5+ unit buildings since 2018, 96% of those we matched fall in these unmodeled areas, so the totals here miss where Covina builds most. The Affordable Housing and Mixed-Use Overlay (Chapter 17.31) and the Mixed-Use Overlay (Chapter 17.59) aren't in SCAG's data and aren't modeled.

**R-1 and E.** One home per lot. R-1-8500 uses R-1-7500's standards (§17.24.050), and R-1-10,000, R-1-20,000 and the estate zones set their own side yards. We found a 35% coverage limit only in R-1-7500, R-1-8500 and E-1. The code allows two and one-half stories; we fit 2. SB 9 is what lifts these lots above one home.
**RD.** The zone names give square feet per home, including RD-1500 and RD-1250, but Table 17.28.040 caps high-density zones at 22 per acre, which is 1,980 sq ft per home, and that's what we use. Under 15,000 sq ft, attached homes can't meet the lot minimum and detached homes aren't allowed in RD 3000 or less, so note 2 limits existing lots to the bottom of the range, 14.1 per acre, or 3,090 sq ft per home. These are conservative readings, and they run below what's on the ground: RD-1250 and RD-1500 hold 2,134 homes on the roll against 1,542 under local rules. Medium zones (RD-3400 and up) use the table's 10 per acre under 15,000 sq ft. We apply the second-story yards to the whole building. Open space and the 2021 objective design standards aren't modeled.
**Commercial and other zones.** C-2 lists residential as prohibited, and M-1 allows only security staff housing. C-P prohibits residences except as §17.34.020 provides, yet applies RD-1500's standards to residential uses; we count none. We didn't read the uses of C-3, C-3A, C-4, C-5, TC-C, TC-P, R-R or R-TP, and count none. The roll shows 885 homes in M-1 and 419 in R-TP.

## 58. Cudahy (Title 20, most zones ⚠️)

Cudahy's zones come from Cudahy Municipal Code Title 20 (ICC Code Solutions, through Ord. 772 of August 18, 2026, read November 3, 2026). 12 rule files cover 1,616 of 1,624 lots (99.5%). The other eight are five with no zone and three coded R, which isn't a zone the code lists. SCAG's zoning here dates from 2018, the year of this code's Ord. 690, and uses its zone names. SCAG writes HDR as HDR-G, which we treat as HDR; we didn't find what the G means.

**LDR, MDR and HDR.** 15, 25 and 40 homes per acre, with two, three and four stories. All three permit single-family homes, duplexes, triplexes and apartments, so we treat none as a single-family zone and don't apply SB 9, including in LDR. Side yards add 2 ft per story above the first, which can be waived. LDR's 25% private open space is applied; the 280 sq ft of total open space per home isn't. HDR requires new projects to reach 20 homes per acre, also not modeled. Lots under one home's share of land keep one home.
**CMU and CivicMU.** We use the residential-only 30 homes per acre. Mixed-use projects may reach 40, with more stories in exchange for community benefits, so large sites here run low. §20.28.020.D expressly allows stand-alone residential only in CMU, though the table gives CivicMU a residential-only density too.
**I-Ind.** Multifamily homes with a conditional use permit, at 30 homes per acre, which we assume is granted.
**NC, Ent, LI, P, S and LAR.** NC needs a conditional use permit and lists density as N/A. Ent allows homes only in mixed-use projects, not on the ground floor, with density N/A. LI allows only live/work units. We count none. Cudahy's capacity is mostly in multifamily zones, and nearly all 5+ unit permits since 2019 match to modeled zones. The River and Urban Agriculture overlays and Planned Developments aren't in SCAG's data.

## 59. Diamond Bar (Title 22, most zones ⚠️)

Diamond Bar's zones come from Diamond Bar City Code Title 22 (Municode, read November 3, 2026). 15 rule files cover 14,066 of 14,402 lots (97.7%). SCAG's zoning here dates from 2023.

Not modeled: 120 lots with no zone, which hold 813 homes on the roll; 135 in SP and SUB-PA areas, whose plans we didn't read; 35 labeled Town Center Mixed Use, governed by the Town Center Specific Plan, which is a separate document (§22.11.030); 26 labeled Transit Oriented and 18 labeled Neighborhood Mixed Use, which Chapter 22.11 no longer lists after Ord. 03(2026); and two labeled Public Facility, also unlisted.

**RR, RL and RLM.** One home per lot, with 30% or 40% coverage. The per-acre figures (3 and 5) apply to gross acreage in subdivisions. The code limits height to 35 ft, and we fit 2 stories. Unequal side yards are averaged. SB 9 is what lifts these lots above one home.
**RM, RMH and RH.** 12, 16 and 20 homes per gross acre, with 30% coverage and parking at 2 spaces plus a half guest space. We use the lot's area rather than gross acreage. Several built complexes exceed these limits on the roll. RH-30, at 30 per acre on 5-acre sites, is in the code, but SCAG doesn't show it, so any RH-30 sites count as RH or something older and run low.
**Hillside.** Chapter 22.22 can lower density and change yards on sloped lots. Much of this city is hilly and we have no slope data, so those lots can run high, including what SB 9 adds. We didn't read that chapter.
**OS.** One home per existing parcel, unless the county previously restricted building there, which we can't tell. It counts 67 homes on lots where the roll shows 3, so this may overstate; we don't apply SB 9.
**Commercial and industrial.** OP, OB, CO, C-1, C-2, C-3 and I list no homes apart from single-room occupancy and supportive housing, which we don't count. PK lots use REC's no-homes rule, and C-3-PD/Hotel uses C-3's. The roll shows 197 homes in OB.

The state's reports show no homes permitted in 5+ unit buildings in 2018 to 2025; ADUs make up most of what gets built.

## 60. By-right homes, building size and net add (November 2026)

Every rule file can now say how its zone permits homes, in `approval`: `by_right` (no use permit or similar discretionary approval), `conditional`, `mixed` or `not_allowed`, with a citation. `by_right_max_units` records a project size above which discretionary review starts. A file with no `approval` is **not confirmed**, and we never fill one in by guess.

`by_right_units` follows from that. A by-right zone gets the lot's maximum, up to any cap. A conditional or not-allowed zone gets only its SB 9 homes, or 0. A mixed or unconfirmed zone gets its SB 9 homes, or "not confirmed" where SB 9 doesn't apply. SB 9 counts everywhere because its approval is ministerial. The ADU path doesn't count unless the zone is by right, since it needs a house to go with.

**What "by right" doesn't cover.** It means the zone's use list needs no use permit. Design review, hillside review, coastal permits, CEQA and specific plans aren't checked, except where a rule file says so. So it's a ceiling on what's truly by right, not a promise of approval. Pasadena's mixed-use projects over 25,000 sq ft need a Conditional Use Permit, which isn't capped, so those can run high.

**How the values were set.** LA's LAMC zones and all of Pasadena were read from the code on November 2, 2026. LA's multi-family and commercial zones are by right up to 49 homes, because 50 or more needs Project Review (§16.05 C.1.(b)). LA's Chapter 1A districts where homes are allowed, CM's joint living uses, RU, PF and P aren't confirmed. Elsewhere, 91 files were set only from what they already recorded, without rereading the code. Burbank's and Glendale's administrative use permits count as conditional, though they are staff-level.

**Second pass (November 2026).** Use lists read from the code for Long Beach, Lancaster, Glendale, Norwalk, West Covina, Arcadia, Inglewood, Hawthorne, Gardena, Bell, Bell Gardens, Bellflower, Artesia, Covina's residential zones, and part of Santa Monica, Carson, Claremont and Monterey Park. Some cities' permitted homes still go through plot plan, design, site plan or director's review, noted in each file and not checked. American Legal's site refused requests (HTTP 403) partway through, so cities hosted there wait for a later pass. Inglewood's P-1 permits R-3 uses and Bellflower's T-C permits upper-floor homes, though our rule files count none there. We left both files unchanged and recorded this as an open decision.

**Coverage.** 983,243 of 1,385,457 modeled lots (71.0%) have a confirmed approval. Outside LA it's 333,550 of 717,268 (46.5%), and 15 of the 50 cities have none.

**The site.** The lot panel now shows the building's square footage, by-right homes, net add under today's rules, and net add by right. `building_sqft` comes from the Assessor and doesn't enter any calculation. It's in `parcels.json` for the four cities whose site files are in the repo. Net add by right is worked out in the panel, not stored.

