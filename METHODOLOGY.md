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
