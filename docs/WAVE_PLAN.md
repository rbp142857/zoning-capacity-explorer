# Wave plan: covering LA County

Goal: model every jurisdiction in Los Angeles County (88 cities and the
unincorporated county), in an order that gets the most useful coverage soonest.

The numbers come from `make waves` →
[`reports/la_county/city_ranking.md`](../reports/la_county/city_ranking.md), which
combines SCAG's countywide zoning table (parcels and zone codes per city) with
the state's permit reports (homes permitted per year, 2018–2025). Re-run it any
time; the waves below were drawn from the November 2026 run.

## The fact that shapes the plan

Homes permitted per year in buildings of 2+ homes, the kind of building a
city's own zoning controls (ADUs follow state law everywhere, so they don't
tell us which city's rules matter):

| | Jurisdictions | Homes/yr in 2+ unit buildings | Share of county |
|---|---|---|---|
| **City of Los Angeles** | 1 | ~21,300 | **81%** |
| Done: Pasadena, Glendale | 2 | ~970 | 3.7% |
| Long Beach + unincorporated county | 2 | ~1,100 | 4.3% |
| 31 mid-size cities (waves 1 and 2 below) | 31 | ~2,460 | 9.4% |
| The other 53 jurisdictions | 53 | ~340 | **1.3%** |

So "all of LA County" and "where LA County builds housing" are very different
goals. Covering the City of Los Angeles matters more than the other 86
remaining jurisdictions combined. The plan reaches it early (wave 2), after
wave 1 has made the per-city process fast and proven.

## Waves

### Wave 1: eight productive mid-size cities

Simple codes (5–11 zone codes cover 90% of parcels) and real apartment
building. Each is a Glendale-sized job via the SCAG fast path
([ADDING_A_CITY.md](../ADDING_A_CITY.md)).

| City | Parcels | Zone codes (for 90%) | Homes/yr in 2+ unit buildings | All homes/yr |
|---|---|---|---|---|
| Santa Monica | 14,979 | 44 (9) | 260 | 386 |
| El Monte | 16,978 | 25 (7) | 148 | 238 |
| Inglewood | 18,375 | 29 (8) | 146 | 215 |
| West Hollywood | 4,314 | 23 (10) | 146 | 171 |
| Monrovia | 9,783 | 30 (11) | 140 | 188 |
| Santa Clarita | 51,872 | 25 (5) | 128 | 495 |
| Burbank ✅ | 25,423 | 41 (7) | 104 | 321 |
| Duarte | 5,503 | 18 (6) | 103 | 122 |

Together: 147,000 parcels, ~1,175 homes/yr in 2+ unit buildings (4.5%).
Good order: Burbank first (closest to Glendale), then Santa Monica (most
building), then the rest. **Burbank: done** (October 31, 2026; see
METHODOLOGY.md §12). It needed two small engine additions that later cities
can reuse: limits keyed on distance to single-family zoning, and a city
opting a zone out of SB 9.

### Wave 2: City of Los Angeles (its own project)

About 673,000 parcels and 81% of the county's multi-unit building. SCAG lists
259 zone codes, and 15 cover 90% of parcels, but that undercounts the work:
LA's zones carry extra parts the rules depend on:

- **Zone strings** like `[Q]R3-1-O`: base zone (R3), height district (1),
  supplemental districts (O), and conditions (`[Q]`, `[T]`, `D`) written in
  separate ordinances. Plan: model base zone + height district; flag lots
  with conditions as "simplified", as Pasadena's specific plans were.
- **Specific plans and overlay areas** across the city: model the base
  rules first, flag the lots, then the largest plans one by one.
- **Local incentive programs** (for example Transit Oriented Communities)
  that work like state law: an extra "path" on top of the base rules, like
  the ADU and SB 9 paths.
- **Downtown's new zoning code** (Chapter 1A): treat it as its own zone family.

Break it into sub-steps, each shipped and validated on its own:
(a) single-family zones (RE, RS, R1), (b) multifamily (RD, R2, R3, R4, R5),
(c) commercial zones that allow housing, (d) the incentive program path,
(e) the biggest specific plans and Downtown.

### Wave 3: Long Beach, the next 23 cities, and the specific plans already started

- **Long Beach**: 87,000 parcels, ~590 homes/yr; 177 zone codes (20 for
  90%), many of them planned-development districts. Treat like a small LA.
- **23 cities with 30–100 homes/yr in 2+ unit buildings:** Lancaster,
  Gardena, Norwalk, Santa Fe Springs, Whittier, Arcadia, South Gate, Culver
  City, Montebello, Pomona, Rolling Hills Estates, West Covina, Westlake
  Village, Alhambra, Palmdale, Carson, Azusa, Lomita, Hawthorne, San Gabriel,
  Monterey Park, Agoura Hills, Torrance. Together ~1,280 homes/yr (4.9%),
  122 zone codes for 90% of their parcels.
- **Specific plans in done cities:** Pasadena's Central District (where 60%
  of Pasadena's new apartments are) and Glendale's Downtown Specific Plan.

### Wave 4: unincorporated LA County

312,000 parcels in scattered areas from East LA to the Antelope Valley, ~510
homes/yr in 2+ unit buildings. One code (Title 22) but 259 zone codes (32
for 90%) and many community standards districts. Do it after LA, reusing
what that wave teaches about suffixes and overlays.

### Wave 5: the long tail (53 jurisdictions)

Together 1.3% of the county's multi-unit building. Many are almost entirely
single-family (in 20 of them, 1–4 zone codes cover 90% of parcels), so each
is quicker than Glendale, but each still needs its code read and its lots
checked. Batch them by neighborhood of the county (South Bay, San Gabriel
Valley, Gateway cities, ...) so shared patterns carry over:

Artesia, Avalon, Baldwin Park, Bell, Bell Gardens, Bellflower, Beverly Hills,
Bradbury, Calabasas, Cerritos, Claremont, Commerce, Compton, Covina, Cudahy,
Diamond Bar, Downey, El Segundo, Glendora, Hawaiian Gardens, Hermosa Beach,
Hidden Hills, Huntington Park, Industry, Irwindale, La Cañada Flintridge, La
Habra Heights, La Mirada, La Puente, La Verne, Lakewood, Lawndale, Lynwood,
Malibu, Manhattan Beach, Maywood, Palos Verdes Estates, Paramount, Pico
Rivera, Rancho Palos Verdes, Redondo Beach, Rolling Hills, Rosemead, San
Dimas, San Fernando, San Marino, Sierra Madre, Signal Hill, South El Monte,
South Pasadena, Temple City, Vernon, Walnut.

## Definition of done, for every city

The same bar Pasadena and Glendale met. It's what makes the data trustworthy,
and later, worth paying for:

1. Rule files for the zones covering at least 90% of the city's residential
   parcels, every value cited, every judgment call written next to it.
2. At least 5 lots checked by hand against the code text, added to
   `docs/HAND_CHECKS.md` and `tests/test_real_parcels.py`.
3. `make validate`: existing homes vs. the state's count, and where recent
   permits were built vs. what's modeled.
4. A section in METHODOLOGY.md: data source, assumptions, what's not modeled.
5. `make test` passes, including the golden and every-lot parity tests.
6. The code version (ordinance number and date) recorded in the rule files,
   so later code changes can be spotted.

## Effort, honestly

- **Glendale** took one working session, including building the multi-city
  setup. A similar city should now take about one session.
- **Wave 1:** about 8 sessions.
- **City of Los Angeles:** many sessions, likely 10–20 across its sub-steps.
- **Waves 3–5:** roughly 25 cities, then 53 smaller ones (2–3 per session).

That's many months of steady work. The order above means that after wave 2,
the tool covers about **90% of the county's multi-unit housing production**,
which is the point where it's genuinely useful to builders and advocates,
and where testing monetization makes sense, rather than waiting for all 89.

## Keeping it current

Cities amend their codes all the time. Each rule file records the code
version it was read from (Glendale: through Ord. No. 6052, May 19, 2026). A
useful addition after wave 1: a script that checks each code host for a newer
ordinance number and lists the cities whose rules need a re-check.

## Caveats on the ranking

- Zone-code counts come from SCAG's table and only approximate effort:
  Pasadena shows 195 codes there because SCAG includes some suffixes, while
  LA's 15 codes for 90% hide its suffixes and conditions.
- Permits measure where building happened in 2018–2025, under the rules of
  that time; reforms can shift where building happens next.
