# Hand-checked parcels

Ten real Pasadena lots, one or two per common zone, worked out by hand from
the Zoning Code text (Municode, September 2, 2026) and compared with the
engine. All ten match. They're also locked in as regression tests in
`pipeline/tests/test_real_parcels.py`, so a future change that alters any of
these answers fails the tests.

Shared assumptions (from `cities/pasadena/city.yaml`): each new home uses
**1,062.5 sq ft** of building (850 sq ft inside the home ÷ 0.80), and each
surface parking space takes **300 sq ft** of ground. "Shape factor" is lot
area ÷ (width × depth); all ten lots are near-rectangles (≥ 0.99).

Lot inputs come from the pipeline: area from the county parcel polygon,
width and depth from its minimum rotated rectangle, and distance to the
nearest major transit stop (SCAG). How to read a row:
**density / land per home / envelope / parking** are the four local limits;
the lowest is the city's answer, then state law (ADU, SB 9) can allow more.

---

### 1. 2314 E Mountain St · RS-6 · 7,252 sq ft (50 × 145.1 ft)

- **Density:** 1 home per lot (Table 2-3) → **1**
- **Envelope:** side setbacks 10% of 50 ft = 5 ft (min 5); front 25, rear 25.
  Buildable 40 × 95.1 = 3,804 sq ft. Coverage: lot over 7,200 sq ft → 35% =
  2,538 sq ft. × 2 stories = 5,076 sq ft. Floor-area formula (lot < 12,000):
  30% × 7,252 + 500 = **2,676 sq ft** → 2,676 ÷ 1,062.5 = 2.5 → **2**
- **Parking:** ground = 7,252 − 25 ft front strip (1,250) = 6,002 sq ft. Each
  home: 1,062.5 ÷ 2 stories = 531 sq ft of footprint + 2 × 300 parking =
  1,131. 5 homes = 5,656 fits; 6 = 6,788 doesn't → **5**
- City answer: **1** (density). ADU path: 1 + ADU + JADU = 3. SB 9: not in a
  landmark district, ≥ 2,400 sq ft → split + 2 each = **4**.
- **Result: 4 homes, limited by SB 9.** Engine: 4, `state_law:sb9` ✓

### 2. 1776 Orangewood St · RS-6, landmark district LD-25 · 6,196 sq ft (49.5 × 125.6)

- Density **1**. Envelope: sides 5 ft; 39.5 × 75.6 = 2,986 sq ft; no coverage
  limit (≤ 7,200 sq ft); floor-area formula 30% × 6,196 + 500 = 2,359 → **2**.
  Parking: ground 4,963; 4 homes = 4,525 fits, 5 don't → **4**.
- SB 9 doesn't apply in a landmark district. ADU path → **3**.
- **Result: 3 homes, limited by ADU law.** Engine: 3, `state_law:adu` ✓

### 3. 1510 Sierra Madre Villa Ave · RS-2 · 21,474 sq ft (110.2 × 195.1)

- Density **1**. Envelope: sides 10% × 110.2 = 11 → capped at 10 ft;
  90.2 × 145.1 = 13,088. Coverage (≥ 12,000): max(35% = 7,516, 4,800) = 7,516
  × 2 = 15,032. Floor-area formula (12,000–24,000): 20% × 21,474 + 1,700 =
  **5,995** → 5.6 → **5**. Parking **16**.
- SB 9 → **4**. **Result: 4, SB 9.** Engine: 4, `state_law:sb9` ✓

### 4. 667 N Oakland Ave · RM-12 · 8,417 sq ft (60.1 × 140.3)

- Density **2** per lot (Table 2-3). Envelope: sides 6 ft; front 25, rear 10;
  coverage 35% = 2,946 × 2 = 5,892 → 5; floor-area formula for RM-12
  (< 12,000): 35% × 8,417 + 500 per home → n × 1,062.5 ≤ 2,946 + 500n →
  n ≤ 2,946 ÷ 562.5 = 5.2 → **5**. Parking: 6 homes fit (6,788 ≤ 6,917) → **6**.
- City answer **2**. ADU path (a house + ADU + JADU fits) → **3**.
- **Result: 3, ADU law.** Engine: 3, `state_law:adu` ✓

### 5. 1060 E Orange Grove Blvd · RM-16 · 11,676 sq ft (103.2 × 114)

- Land per home: 11,676 ÷ 2,750 = 4.25; RM-16 rounds up only above .75 → **4**.
- Envelope: 80–160 ft wide → 32% garden → 68% × 11,676 = 7,940 × 2 stories
  = 15,879 → **14**. Parking: 2,186 ft from a major transit stop → AB 2097,
  no minimum.
- **Result: 4, land per home.** 4 homes already there → 0 new. Engine: 4 ✓

### 6. 534 N Los Robles Ave · RM-32 · 12,192 sq ft (62 × 196.9), 3,056 ft from transit

- Land per home: 12,192 ÷ 1,360 = 8.96 → nearest → **9**.
- Envelope: < 80 ft wide → 32% garden → 8,291 sq ft; ≥ 60 ft wide → 2.4
  stories (§17.22.070.F, our averaging) → 19,897 → **18**.
- Parking (outside ½ mile): ground = 8,291 (the garden cap is tighter than
  the front strip). Each home 1,062.5 ÷ 2.4 = 443 + 600 = 1,043. 7 homes =
  3,099 + 14 spaces × 300 = 7,299 fits; 8 homes = 3,542 + 16 × 300 = 8,342
  doesn't → **7**.
- **Result: 7, parking.** 10 homes there today (a 1984 building that's
  legally nonconforming). Engine: 7, `parking` ✓

### 7. 233 N Wilson Ave · RM-32 · 6,476 sq ft (52 × 125), 1,040 ft from transit

- Small-lot table (§17.22.070.A.2), 5,500–6,999 sq ft → **4**.
- Envelope: < 60 ft wide → 2 stories; buildable (52 − 10) × (125 − 20) =
  4,410 × shape factor 0.996 = 4,394 sq ft, just under the 68% garden cap
  (4,404) → × 2 = 8,787 → **8**. Parking: AB 2097, none.
- **Result: 4, small-lot table.** 1 home there (built 1921) → 4 ≥ 2 × 1 and
  +3 new; old, cheaper than land, not a condo or landmark → **likely to
  redevelop, +3**. Engine: 4, likely, +3 ✓

### 8. 180 S Catalina Ave · RM-48 · 10,445 sq ft (60.1 × 174.1), 2,511 ft from transit

- Land per home: 10,445 ÷ 910 = 11.48 → nearest → **11**.
- Envelope: 32% garden → 7,103 × 3 stories = 21,308 → **20**. Parking: AB 2097.
- **Result: 11, land per home.** 10 there → +1; not likely (11 < 2 × 10).
  Engine: 11 ✓

### 9. 1864 E Washington Blvd · CL · 10,003 sq ft (100 × 100.6)

- Land per home (CL uses RM-32's density): 10,003 ÷ 1,360 = 7.36 → **7**.
- Envelope: FAR 0.70 × 10,003 = **7,002 sq ft** (tighter than 29% garden ×
  3 stories) → 6.6 → **6**. Parking: 7 homes fit (6,679 ≤ 7,102), 8 don't → **7**.
- **Result: 6, building envelope (FAR).** No homes today (a 1951 store).
  Not likely: the store is assessed at $1.45M vs. $0.81M for the land.
  Engine: 6, `envelope`, not likely ✓

### 10. 960 N Lake Ave · CO · 9,242 sq ft (50 × 185), North Lake overlay SP-1a

- Land per home (CO uses RM-48's): 9,242 ÷ 910 = 10.16 → **10**.
- Envelope: setbacks 20 front, 10 sides, 10 rear → 30 × 155 = 4,650 × 4
  stories = 18,584; FAR 0.80 × 9,242 = **7,394** → 6.96 → **6**.
- Parking (3,841 ft from transit): ground = 68% garden cap = 6,285; each home
  1,062.5 ÷ 4 = 266 + 600 = 866; 7 homes = 6,059 fits, 8 = 6,925 doesn't → **7**.
- **Result: 6, envelope (FAR).** A 1912 store worth a third of its land →
  **likely to redevelop, +6**. Engine: 6, `envelope`, likely, +6 ✓
- ⚠️ Caveat this check surfaced: the **North Lake Specific Plan overlay
  (SP-1a)** may set its own standards for this lot. The engine applies only
  the base CO rules to overlay lots like this; that's listed under "Not yet
  modeled" in METHODOLOGY.md.

---

# Glendale (5 lots)

Glendale Municipal Code Title 30, eCode360 version through Ord. No. 6052
(May 19, 2026). Same shared assumptions as Pasadena, plus a **500 sq ft
minimum home**: a lot whose limits allow at least that much floor area holds
one home even if it's less than the average 1,062.5 sq ft unit. Zones come from
SCAG's countywide table, which has no overlays, so FAR district I and the
most restrictive height districts are used (see the rule files).

### G1. 1248 Thompson Ave · R1 · 6,837 sq ft (42.7 × 161.5 ft)

- Density **1**. Envelope: front 25, sides 6, rear 6 → 30.7 × 130.5 = 4,006;
  coverage 40% = 2,735 × 2 stories = 5,470; FAR district I: 30% × 6,837 =
  **2,051 sq ft** → 1.9 → **1**. Parking: ground = 60% (40% open space) =
  4,102; 3 homes = 3,394 fits, 4 = 4,525 doesn't → **3**.
- City answer 1; ADU path 3; SB 9 (≥ 2,400 sq ft) **4**. Engine: 4, `state_law:sb9` ✓

### G2. 1056 Kildonan Dr · R1R (hillside) · 10,560 sq ft (92.5 × 115.3)

- Density **1**. Envelope: front 15, sides 10, rear 10 → 72.5 × 90.3 = 6,547;
  coverage 40% = 4,224 × 2 = 8,448; FAR over 10,000 sq ft: 0.10 × 10,560 +
  2,000 = **3,056** → **2**. Parking **5**.
- SB 9 → **4**. Not likely to redevelop (single-family zone; built 1979).
  Engine: 4 ✓

### G3. 651 Salem St · R-2250 · 7,056 sq ft (50.9 × 139.3)

- Land per home (under 90 ft wide): 7,056 ÷ 2,250 = 3.1 → **3**.
- Envelope: coverage 50% = 3,528 × 3 stories = 10,584; FAR 0.85 × 7,056 =
  **5,998** → **5**. Parking (3,372 ft from transit): ground = 80% (20% open
  space) = 5,645; each home 354 + 600; at 4+ homes add ¼ guest space each.
  5 homes = 1,771 + 11 spaces × 300 = 5,071 fits; 6 = 2,125 + 14 × 300 = 6,325
  doesn't → **5**.
- **Result: 3, land per home.** The house (1918) is assessed at $8k against
  $237k of land, but zoning allows only +2 homes, under the 3-home minimum, so
  it's **not** counted as likely. Engine: 3 ✓

### G4. 325 N Howard St · R-1250 · 14,999 sq ft (99.6 × 151.4), 1,674 ft from transit

- Land per home: 90 ft or wider → **1,000 sq ft per home**: 14,999 ÷ 1,000 =
  14.999 → rounded down → **14**.
- Envelope: coverage 60% = 8,999 × 3 = 26,998; FAR 1.2 × 14,999 = **17,999** →
  **16**. Parking: AB 2097, none.
- **Result: 14, land per home.** 18 homes today (a 1963 building that's legally
  nonconforming), so 0 new. Engine: 14 ✓

### G5. 1109 N Brand Blvd · C3 · 8,709 sq ft (40 × 218.4)

- Land per home: under 90 ft wide → 8,709 ÷ 1,250 = 6.97 → **6**.
- Envelope: no FAR or coverage limit; sides 5, rear 5 → 30 × 213.4 = 6,402 ×
  3 stories (height district I) = 19,147 → **18**. Parking: 8 homes = 2,833 +
  18 spaces × 300 = 8,233 fits; 9 = 3,188 + 20 × 300 = 9,188 doesn't → **8**.
- **Result: 6, land per home.** A 1950 commercial building worth about a
  third of its land, no homes today → **likely to redevelop, +6**. Engine: 6 ✓

---

# Burbank (6 lots)

Burbank Municipal Code Title 10, Chapter 1, Code Publishing version through
Ord. No. 25-4,036 (eff. January 16, 2026). Same shared assumptions as Glendale
(1,062.5 sq ft per new home, 300 sq ft per parking space, 500 sq ft minimum
home). Two things are new in Burbank:

- **Distance to single-family zoning** changes the limits. In R-2 to R-4,
  lots within 500 ft of an R-1 or R-1-H lot get 2 stories and 60% coverage,
  others 3 stories and 70%. In mixed-use projects, lots within 150 ft get
  40 ft (3 stories), others 60 ft (5 stories). The pipeline measures this
  from lot edge to lot edge.
- **Commercial-zone density comes from the General Plan** (homes per acre by
  designation), and mixed-use projects round the home count **up**.

### B1. 1065 E Grinnell Dr · R-1 · 7,850 sq ft (50 × 157.3 ft)

- Density **1**. Envelope: front 20 (assumed), sides 10% of width = 5,
  rear 15 → 40 × 122.3 = 4,892 (× 0.998 shape); coverage 50% = 3,925 × 2
  stories = 7,850; FAR: 0.30 × 7,850 + 750 = **3,105 sq ft** → **2**.
  Parking: ground = 7,850 − 998 front strip = 6,852; 6 homes = 3,188 + 12 ×
  300 = 6,788 fits, 7 doesn't → **6**.
- City answer 1; ADU path 3; SB 9 **4**. Engine: 4, `state_law:sb9` ✓

### B2. 438 S Lamer St · R-1-H (horsekeeping) · 10,125 sq ft (75 × 135.1)

- Density **1**. FAR: 0.30 × 10,125 + 750 = **3,788 sq ft** → **3**.
- Burbank's code bars SB 9 in R-1-H (§10-1-608.1(A)(3)), so no SB 9 path;
  ADU path **3**. Engine: 3, `state_law:adu`, flag `sb9_excluded_by_city` ✓

### B3. 1919 W Alameda Ave · R-4 · 10,583 sq ft (97.9 × 109), 21 ft from R-1

- Land per home (lot under 12,000 sq ft): 10,583 ÷ 2,000 = 5.29 → **5**.
- Envelope (within 500 ft of R-1): coverage 60% = 6,350 × **2** stories =
  12,700 → **11**. Parking: ground = 10,583 − 1,651 front strip = 8,932;
  7 homes = 3,719 + 16 spaces (14 + 1.75 guest, rounded) × 300 = 8,519
  fits; 8 = 4,250 + 18 × 300 = 9,650 doesn't → **7**.
- **Result: 5, land per home.** Engine: 5 ✓

### B4. 520 E Orange Grove Ave · R-4 · 12,303 sq ft (101.7 × 121.6), 1,428 ft from R-1

- Land per home (12,000 to 23,999 sq ft): 12,303 ÷ 1,400 = 8.79 → **8**.
- Envelope (more than 500 ft from R-1): setbacks 87.7 × 97.6 = 8,559
  (× 0.995) = 8,515, under 70% coverage (8,612) → 8,515 × **3** stories =
  25,545 → **24**. Parking: AB 2097 (2,439 ft from a major transit stop), none.
- **Result: 8, land per home.** Engine: 8 ✓

### B5. 2907 W Burbank Blvd · C-3 (Corridor Commercial) · 7,861 sq ft (75 × 105.5), 20 ft from R-1

- Density: 27 per acre × 7,861 ÷ 43,560 = 4.87 → rounded **up** → **5**.
- Envelope (within 150 ft of R-1 → 40 ft, 3 stories): front 5, rear 10,
  sides 0 → 75 × 90.5 = 6,788 (× 0.994) × 3 = 20,230 → **19**. Parking 1.5
  per home: ground = 7,861 − 373 = 7,488; 9 homes = 3,188 + 14 × 300 = 7,388
  fits, 10 doesn't → **9**.
- **Result: 5, density.** Engine: 5 ✓

### B6. 300 E Olive Ave · BCC-2 (Downtown) · 31,000 sq ft (155 × 200.1), 2,517 ft from R-1

- Density: 87 per acre × 31,000 ÷ 43,560 = 61.9 → rounded **up** → **62**.
- Envelope (5 stories): 155 × 185.1 = 28,690 (× 0.9995) × 5 = 143,380 →
  **134**. Parking: AB 2097 (1,175 ft from transit), none.
- **Result: 62, density.** A commercial building, no homes today. Engine: 62 ✓

---

# Santa Monica (7 lots)

Santa Monica Municipal Code Article 9 (eCode360, through Ord. No. 2862CCS,
adopted July 28, 2026). Same shared assumptions as Burbank. What's different:

- **No parking minimums for housing** anywhere except R1 and OP1 (§9.28.060),
  so parking never limits multifamily or mixed-use lots.
- **Commercial, employment and Bergamot zones have no density limit** for
  housing projects: the number of homes follows from the floor-area ratio
  (FAR) and height alone (Tables 9.11.030.B, 9.12.030.B, 9.13.030.B).
- **Standards differ by street within one zone** (GC on Santa Monica Blvd
  allows FAR 3.25 and 70 ft, on Pico Blvd 2.0 and 45 ft). The lot's address
  picks the rule file (`zone_splits` in city.yaml).
- **Rounding:** fractions of 0.5 or more round up (§9.04.020; in Ocean Park,
  an extra home if the leftover land is at least half the per-home area).

### S1. 1723 Robson Ave · R1 · 5,106 sq ft (50 × 102.1 ft)

- Density **1**. FAR 0.45 (two-story home) = **2,298 sq ft** → **2**;
  setbacks (front 20, sides 15% = 7.5, rear 15) leave 35 × 67.1 = 2,349 × 2
  stories, more than the FAR. Parking (5,719 ft from a major transit stop, so
  required): ground = 5,106 − 1,000 front strip = 4,106; 3 homes = 1,594 + 6
  × 300 = 3,394 fits, 4 = 2,125 + 2,400 doesn't → **3**.
- City answer 1; ADU path 3; SB 9 **4**. Engine: 4, `state_law:sb9` ✓

### S2. 2013 18th St · R2 · 7,991 sq ft (50 × 160)

- Land per home: 7,991 ÷ 1,500 = 5.33 → **5** (0.33 rounds down).
- Envelope: FAR 1.0 = 7,991 sq ft → **7**. Setbacks 34 × 125 = 4,250 × 3
  stories and 30% planting area leave more than the FAR. Parking: none required.
- **Result: 5, land per home.** 3 homes today. Engine: 5 ✓

### S3. 2428 Beverley Ave · OP2 · 7,124 sq ft (50.1 × 142.6)

- Land per home: 7,124 ÷ 2,000 = 3.56; the leftover 1,124 sq ft is at least
  1,000, so one more home (§9.09.030(A)(1)) → **4**.
- Envelope: FAR 1.0 = 7,124 sq ft → **6**.
- **Result: 4, land per home.** 4 homes today, so no net gain. Engine: 4 ✓

### S4. 1438 15th St · R3 · 7,491 sq ft (50 × 150)

- Land per home: 7,491 ÷ 1,250 = 5.99 → **6**.
- Envelope: FAR 1.5 = 11,237 sq ft → **10**.
- **Result: 6, land per home.** 7 homes today (more than the zone now
  allows, common in Santa Monica's older apartment areas). Engine: 6 ✓

### S5. 1501 17th St · MUBL (north of I-10) · 7,500 sq ft (50 × 150)

- No density limit. Envelope: FAR 3.25 = 24,375 sq ft; the building (no
  front or side setback, 10 ft rear: 50 × 140 × 6 stories) is larger, so FAR
  binds → 24,375 ÷ 1,062.5 = 22.9 → **22**.
- **Result: 22, envelope.** 5 homes in a 1949 building today; it passes the
  redevelopment screens. Engine: 22 ✓

### S6. 728 Montana Ave · NC (Montana Ave) · 6,006 sq ft (60.1 × 100.1)

- No density limit. Envelope: FAR 2.5 = 15,015 sq ft → 14.1 → **14**.
- **Result: 14, envelope.** Engine: 14 ✓

### S7. 2452 Lincoln Blvd · GC (Lincoln Blvd) · 7,518 sq ft (78.2 × 110.1)

- No density limit. Envelope: FAR 2.5 = 18,795 sq ft → 17.7 → **17**.
- **Result: 17, envelope.** 16 homes today. Engine: 17 ✓
