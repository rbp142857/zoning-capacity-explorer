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

## Los Angeles (single-family zones)

Checked against the Los Angeles Municipal Code (American Legal, read November 1,
2026). One home needs 1,062.5 gross sq ft in the envelope math. Lots within ½
mile of a major transit stop need no parking (AB 2097). SB 9 gives 4 homes
with a split, and ADU law gives 3, so local capacity only sets the answer where
neither applies. The map shows the zone with its height district (`R1-1`); the
rule file is the zone alone (`R1`).

### L1. 10548 McClemont Ave · R1 · 5,088 sq ft (50 × 101.9)

- Density: 1 home (§12.08 C.4). Envelope: FAR 0.45 (§12.08 C.5.(a)) = 2,290 sq ft → 2.2 → **2**.
- **Result: 4, SB 9.** Engine: 4 ✓

### L2. 16428 Gunther St · RS · 11,183 sq ft (124.2 × 201)

- Density: 1. Envelope: lot is over 9,000 sq ft, so 40% = 4,473 sq ft, above the 4,050 floor (§12.07.1 C.5) → 4.2 → **4**.
- **Result: 4, SB 9.** Engine: 4 ✓

### L3. 9447 Haines Canyon Ave · RE11 · 11,183 sq ft (76.2 × 158.1)

- Density: 1. Envelope: under 15,000 sq ft, so 40% = 4,473 sq ft (§12.07.01 C.5) → 4.2 → **4**.
- **Result: 4, SB 9.** Engine: 4 ✓

### L4. 14937 Bledsoe St · RA · 84,415 sq ft (346.4 × 423.7)

- Density: 1. Envelope: over 20,000 sq ft, so 20% = 16,883 sq ft, above the 5,000 floor (§12.07 C.5) → 15.9 → **15**.
- **Result: 4, SB 9.** Engine: 4 ✓

### L5. 3400 Corinth Ave · R1V2 · 6,126 sq ft (60 × 102.9)

- Density: 1. Envelope: 6,001–7,000 sq ft row of Table 12.08 C.5.(b), RFAR .53 = 3,247 sq ft → 3.1 → **3**. 1,549 ft from transit: no parking.
- **Result: 4, SB 9.** Engine: 4 ✓

### L6. 1224 Hauser Blvd · R1R3 · 6,076 sq ft (60 × 101.4)

- Density: 1. Envelope: 6,001–7,000 sq ft row of Table 12.08 C.5.(d), RFAR .43 = 2,613 sq ft → 2.5 → **2**.
- **Result: 4, SB 9.** Engine: 4 ✓

### L7. 10466 Glory Ave · RE40 · 54,198 sq ft (148.2 × 366.9)

- Density: 1. Envelope: 35% = 18,969 sq ft (§12.07.01 C.5) → 17.9 → **17**.
- **Result: 4, SB 9.** Engine: 4 ✓

### L8. 931 S Cochran Ave · R1, HPOZ · 7,949 sq ft (57.3 × 138.7)

- Density: 1. Envelope: FAR 0.45 = 3,577 sq ft → 3.4 → **3**. In a Historic Preservation Overlay Zone, so no SB 9.
- **Result: 3, ADU law (house, ADU, junior ADU).** Engine: 3 ✓

### L9. 9300 Reverie Rd · A1 · 296,744 sq ft (617.6 × 680)

- Density: 2.5 acres per home, at most 2 (§12.05 C.4): 2.7 → **2**. Envelope: yards leave 567.6 × 630, scaled by the lot's shape (0.707) = 252,670 sq ft; 3 stories → 713 homes (not the limit). SB 9 left out in A1 (see METHODOLOGY).
- **Result: 3, ADU law.** Engine: 3 ✓

### L10. 8800 Wentworth St · A2 · 70,395 sq ft (225.6 × 454.9)

- Density: under the 2-acre minimum (§12.06 C.2), so it keeps its **1** home. SB 9 left out in A2.
- **Result: 3, ADU law.** Engine: 3 ✓

## Los Angeles (apartment and commercial zones)

LA caps floor area at a multiple of the "buildable area", the lot minus required
yards (§12.21.1 A): 3 times in residential Height District 1, 1.5 times in
commercial Height District 1, 6 times in Height District 2. 1XL allows 2 stories.
Parking is surface parking at 1.5 spaces per home (rounded up per project) and 300
sq ft per space, within reach of the ground left after the front yard. "Shape" is
the lot's area over its width times depth.

### L11. 2276 Ewing St · R2 · 7,502 sq ft (50 × 150.6)

- Lot area: 2,500 per home (§12.09 C.4) = 3, but R2 allows 2 homes. Local: **2**. ADU law: 3.
- **Result: 3, ADU law.** 3 homes today. Engine: 3 ✓

### L12. 1925 W 35th St · RD1.5 · 6,907 sq ft (50 × 138.3)

- Lot area: 1,500 per home (§12.09.1 C.4) → 4.6 → **4**.
- Envelope: 40 × 108.3 × 0.999 = 4,327; × 3 = 12,981 sq ft → 12. Parking: 7 homes need 11 spaces, 2,479 + 3,300 = 5,779 of 6,158 sq ft; 8 don't fit.
- **Result: 4, lot area.** Engine: 4 ✓

### L13. 1501 S Dunsmuir Ave · RD2 · 6,100 sq ft (50 × 122.1)

- Lot area: 2,000 per home → **3**. Envelope: 40 × 92.1 × 0.999 × 3 = 11,043 sq ft → 10.
- **Result: 3, lot area.** Engine: 3 ✓

### L14. 7124 Flight Ave · R3 · 7,201 sq ft (60 × 120)

- Lot area: 800 per home (§12.10 C.4) → 9. Envelope: 48 × 90 × 3 = 12,960 sq ft → 12.
- Parking: 6,301 sq ft of ground. 7 homes: 2,479 + 3,300 = 5,779 fits. 8 homes: 2,833 + 3,600 = 6,433 doesn't → **7**.
- **Result: 7, parking.** 6 homes today. Engine: 7 ✓

### L15. 1069 S Cloverdale Ave · R3, HPOZ · 6,905 sq ft (50 × 138.1)

- Lot area: 800 per home → 8.6 → **8**. 1,107 ft from transit: no parking.
- **Result: 8, lot area.** Engine: 8 ✓

### L16. 2100 N Cahuenga Blvd · R3-1XL · 6,638 sq ft (50 × 132.9)

- Lot area: **8**. Envelope: 40 × 102.9 × 0.999 × 2 stories = 8,223 sq ft → 7.
- Parking: 5,889 sq ft of ground. 6 homes: 3,188 + 2,700 = 5,888 just fits; 7 don't → **6**.
- **Result: 6, parking.** Engine: 6 ✓

### L17. 11124 La Maida St · R4-2 · 7,749 sq ft (50 × 155.1)

- Lot area: 400 per home (§12.11 C.4) → 19. Envelope: 6 times buildable, rear yard 18 ft: 40 × 122.1 × 0.999 × 6 = 29,281 sq ft → 27.
- Parking: 7,000 sq ft of ground. 10 homes: 1,771 + 4,500 fits; 11 homes: 1,948 + 5,100 doesn't → **10**.
- **Result: 10, parking.** Engine: 10 ✓

### L18. 7802 Foothill Blvd · C2-1VL · 10,466 sq ft (79.4 × 172.1)

- Lot area: R4's 400 per home (§12.14 C.3) → 26. Envelope: no front yard, R4 side yards at 3 stories (6 ft), 15 ft rear: 67.4 × 157.1 × 0.766 = 8,110 sq ft buildable; × 1.5 = 12,165 → 11.4 → **11**. Parking fits 12.
- **Result: 11, envelope.** Vacant today. Engine: 11 ✓

### L19. 4801 S Broadway · C2-1VL · 6,740 sq ft (67.4 × 100.1)

- Envelope: 55.4 × 85.1 × 0.999 × 1.5 = 7,065 sq ft → 6.6 → **6**. Near transit: no parking.
- **Result: 6, envelope.** Engine: 6 ✓

### L20. 4615 Lankershim Blvd · C2-2 · 6,340 sq ft (50 × 139.9)

- Lot area: 15. Envelope: 40 × 121.9 × 0.906 × 6 = 26,518 sq ft → 24.
- Parking: 10 homes: 1,771 + 4,500 = 6,271 of 6,340 fits; 11 don't → **10**.
- **Result: 10, parking.** Engine: 10 ✓

### L21. 17827 Chatsworth St · C1-1XL · 6,847 sq ft (50 × 137)

- Lot area: R3's 800 per home (§12.13 C.4) → 8. Envelope: 40 × 112 × 1.0 × 1.5 = 6,717 sq ft → **6**. Parking fits 6 too; envelope comes first in the tie order.
- **Result: 6, envelope.** Engine: 6 ✓

### L22. 3731 S Grand Ave · CM-1 · 6,907 sq ft (48.3 × 143.2)

- Lot area: R3's 800 per home (§12.17.1 C.2) → 8. Envelope: 38.6 × 128.2 × 0.999 × 1.5 = 7,420 sq ft → 7.0 → **6**, just short of 7.
- **Result: 6, envelope.** Engine: 6 ✓

### L23. 18428 Gault St · M1 · 14,995 sq ft (100 × 150)

- M1 allows MR1 uses and C2's commercial uses, so homes only for a guard or caretaker.
- **Result: 0, not allowed.** Engine: 0 ✓

## Los Angeles (Chapter 1A, downtown and Boyle Heights)

Read on zoning.lacity.gov. The zone string gives the Form District (floor area,
yards), the Use District (are homes allowed) and the Density District (lot area
per home). Base floor area only, without public benefit bonuses.

### L24. 960 N Broadway · [DM5-SH2-5][CX1-FA] · 8,598 sq ft

- FA density: floor area is the only limit. DM5 base FAR 6.0 (Sec. 2B.16.5) = 51,588 sq ft → 48.6 → **48**. Near transit, and Package A needs no parking.
- **Result: 48, envelope.** Engine: 48 ✓

### L25. 770 S Grand Avenue · [HB5-G1-5][CX3-FA] · 129,533 sq ft

- HB5 base FAR 9.0 (Sec. 2B.20.5) = 1,165,797 sq ft → **1,097**.
- **Result: 1,097, envelope.** 700 homes today. Engine: 1,097 ✓

### L26. 3216 Eagle St · [H3-MU3-3][RX2-2L] · 5,112 sq ft

- 2L density: 2 homes per lot (Div. 6B.1). H3 FAR 0.6 (Sec. 2B.3.3) = 3,067 sq ft → 2.9 → 2. Local: **2**. ADU law: 3.
- **Result: 3, ADU law.** Engine: 3 ✓

### L27. 647 Camulos St · [VN1-MU3-3][RX2-15] · 5,600 sq ft

- 15 density: 1,500 sq ft per home (Div. 6B.2) → 3.7 → **3**. VN1 FAR 1.0 (Sec. 2B.4.1) = 5,600 sq ft → 5.
- **Result: 3, lot area.** Engine: 3 ✓

### L28. 2624 E Cesar E Chavez Ave · [LM3-CC1-4][CX5-8] · 4,000 sq ft

- 8 density: 800 per home → **5**. LM3 FAR 1.5 (Sec. 2B.9.3) = 6,000 sq ft → 5.6 → 5. A tie; lot area comes first.
- **Result: 5, lot area.** Engine: 5 ✓

### L29. 525 E 6th St · [MB2-G1-5][IX1-FA] · 6,019 sq ft

- MB2 base FAR 3.0 (Sec. 2B.14.2) = 18,057 sq ft → 16.99 → **16**. No height limit, so floor area sets the answer.
- **Result: 16, envelope.** Engine: 16 ✓

## El Monte

Checked against the El Monte Municipal Code, Title 17 (Municode, Ord. No. 3053),
read November 1, 2026.

### E1. 11421 Elmcrest St · R-1A · 9,546 sq ft (60 × 160)

- Density: 1 home. Floor area: 8,001 to 12,000 sq ft row, 30% = 2,864 sq ft, above the 2,800 floor → 2.7 → 2.
- **Result: 4, SB 9.** Engine: 4 ✓

### E2. 4726 Maxson Rd · R-1B · 13,472 sq ft (73 × 201.8)

- Land per home: 8,720 sq ft at up to 100 ft of frontage → 1. Floor area: 25% = 3,368, below the 3,600 floor, so 3,600 → 3.4 → 3.
- **Result: 4, SB 9.** 2 homes today. Engine: 4 ✓

### E3. 12043 Cherrylee Dr · R-1C · 33,763 sq ft (133.4 × 254.9)

- Density: 1. Floor area: over 20,000 sq ft, 20% = 6,753 sq ft → 6.4 → 6.
- **Result: 4, SB 9.** Engine: 4 ✓

### E4. 11066 McGirk Ave · R-2 · 6,010 sq ft (60 × 102.4)

- Land per home: 5,445 → **1**. FAR 0.40 = 2,404 sq ft → 2. ADU law: 3.
- **Result: 3, ADU law.** Engine: 3 ✓

### E5. 3641 Durfee Ave · R-3 · 22,937 sq ft (81.4 × 283)

- Land per home: 4,356 under 100 ft of frontage → 5.3 → **5**. FAR 0.50 = 11,469 sq ft → 10.
- **Result: 5, lot area.** 13 homes stand here today, more than zoning now allows. Engine: 5 ✓

### E6. 9743 Valley Blvd · R-4 · 42,178 sq ft (100.1 × 634.9)

- Land per home: 1,740 → 24. FAR 0.60 = 25,307 sq ft → 23.8 → **23**.
- **Result: 23, envelope.** Engine: 23 ✓

### E7. 3141 Peck Rd · C-3 · 52,139 sq ft (195.5 × 367.3)

- Land per home: 1,450 at 30,000 sq ft or more → 35. FAR 0.60 = 31,283 sq ft → 29.4 → **29**. 2,176 ft from transit: no parking.
- **Result: 29, envelope.** Engine: 29 ✓

### E8. 2822 Durfee Ave · MMU · 34,445 sq ft (140 × 248.9)

- Land per home: 1,400 in the 30,001 to 35,000 sq ft row → 24.6 → **24**.
- **Result: 24, lot area.** Engine: 24 ✓

### E9. 12315 Dahlia Ave · M-1 · 11,605 sq ft (80.2 × 148)

- The use matrix allows no homes in M-1.
- **Result: 0, not allowed.** Engine: 0 ✓

## Inglewood

Checked against the Inglewood Municipal Code, Chapter 12 (eCode360), read
November 1, 2026.

### I1. 9120 S 8th Ave · R-1 · 8,505 sq ft

- One home per family at 6,000 sq ft (Article 2). 2,015 ft from transit: no parking.
- **Result: 4, SB 9.** Engine: 4 ✓

### I2. 3249 W 108th St · R-2 · 6,066 sq ft

- 2,500 sq ft each for 1 or 2 homes (Article 3) → **2**. ADU law: 3.
- **Result: 3, ADU law.** Engine: 3 ✓

### I3. 3714 W 105th St · R-2 · 14,588 sq ft

- 3 homes need 8,000 sq ft, and each extra home 3,000 more: 4 at 11,000, 5 at 14,000, 6 at 17,000 → **5**.
- **Result: 5, lot area.** Engine: 5 ✓

### I4. 500 E Fairview Blvd · R-2A · 12,771 sq ft

- 3 homes need 9,000 sq ft, and each extra home 4,000 more: 4 at 13,000 → **3**.
- **Result: 3, lot area.** 4 homes stand here today. Engine: 3 ✓

### I5. 134 E Spruce Ave · R-3 · 9,625 sq ft (50 wide)

- Under 12,000 sq ft: 1,400 per home (Article 4) → 6.9 → **6**.
- **Result: 6, lot area.** Engine: 6 ✓

### I6. 709 Venice Way · R-3 · 18,503 sq ft (80 wide)

- At least 12,000 sq ft and 80 ft wide: 1,100 per home → 16.8 → **16**.
- **Result: 16, lot area.** Engine: 16 ✓

### I7. 816 N Market St · R-4 · 12,476 sq ft (50 wide)

- Big enough but under 80 ft wide, so 1,250 per home (Article 5) → 9.98 → **9**.
- **Result: 9, lot area.** Engine: 9 ✓

### I8. 910 Myrtle Ave · R-M · 12,260 sq ft (52.5 wide)

- Residential-only follows R-3; under 80 ft wide: 1,400 per home → 8.8 → **8**.
- **Result: 8, lot area.** Engine: 8 ✓

### I9. 400 E Kelso St · C-2 · 31,107 sq ft

- No new dwellings in C-2 outside one mixed-use area around Crenshaw and Manchester, which this lot isn't in.
- **Result: 0, not counted.** Engine: 0 ✓

## West Hollywood

Checked against the West Hollywood Municipal Code, Title 19 (eCode360), read
November 1, 2026. Most of the city is within ½ mile of a major transit stop, so
parking rarely applies.

### W1. 419 Huntley Dr · R1-B · 6,004 sq ft

- Table 2-4: 2 homes under 8,500 sq ft. FAR 0.5 = 3,002 sq ft → 2.8 → 2.
- **Result: 4, SB 9.** Engine: 4 ✓

### W2. 1249 N Ogden Dr · R2 · 7,484 sq ft

- Table 2-4: 3 homes from 4,000 to 7,999 sq ft → **3**.
- **Result: 3, lot area.** 10 homes stand here today, far more than zoning now allows. Engine: 3 ✓

### W3. 1015 N Stanley Ave · R3-B · 6,495 sq ft

- 1,210 sq ft per home (Table 2-3) → 5.4 → **5**.
- **Result: 5, lot area.** 9 homes today. Engine: 5 ✓

### W4. 1217 Havenhurst Dr · R4-A · 15,240 sq ft

- 872 sq ft per home → 17.5 → **17**.
- **Result: 17, lot area.** 19 homes today. Engine: 17 ✓

### W5. 1342 N Crescent Heights Blvd · R4-B · 14,983 sq ft

- 872 sq ft per home → 17.2 → **17**.
- **Result: 17, lot area.** Engine: 17 ✓

### W6. 1019 N Fairfax Ave · CC1 · 6,672 sq ft

- FAR 1.5 (Table 2-6) = 10,008 sq ft → 9.4 → **9**. No density limit.
- **Result: 9, envelope.** Engine: 9 ✓

### W7. 7906 Santa Monica Blvd · CC2 · 9,375 sq ft

- FAR 2.0 = 18,750 sq ft → 17.6 → **17**.
- **Result: 17, envelope.** Engine: 17 ✓

### W8. 369 N Robertson Blvd · CN1 · 13,343 sq ft

- FAR 1.0 = 13,343 sq ft → 12.6 → **12**.
- **Result: 12, envelope.** Engine: 12 ✓

### W9. 500 N Doheny Dr · CN2 · 5,174 sq ft

- Mixed-use projects aren't allowed in CN2 (Table 2-5 note 12).
- **Result: 0, not allowed.** Engine: 0 ✓

## Monrovia

Checked against the Monrovia Municipal Code, Title 17 (American Legal), read
November 1, 2026.

### M1. 438 Kirkwood Ln · RL · 7,093 sq ft

- One home. Floor area (§17.12.020): 40% of the first 5,000 + 35% of the rest = 2,000 + 733 = 2,733 sq ft → 2.6 → 2.
- **Result: 4, SB 9.** Engine: 4 ✓

### M2. 523 W Hillcrest Blvd · RE · 19,141 sq ft

- Floor area: 2,000 + 1,750 + 15% of 9,141 = 5,121 sq ft → 4.8 → 4.
- **Result: 4, SB 9.** Engine: 4 ✓

### M3. Unaddressed lot · RF · 55,280 sq ft

- Floor area (§17.12.010): 35% of 20,000 + 10% of 35,280 = 10,528 sq ft → 9.9 → 9.
- **Result: 4, SB 9.** Engine: 4 ✓

### M4. 816 Bonita St · RM3500 · 8,252 sq ft

- 3,500 per home → 2.4 → **2**. FAR 40% = 3,301 sq ft → 3. ADU law: 3.
- **Result: 3, ADU law.** Engine: 3 ✓

### M5. 1703 Alamitas Ave · RM4000 · 16,421 sq ft

- 4,000 per home → 4.1 → **4**. FAR 40% = 6,568 sq ft → 6.
- **Result: 4, lot area.** Engine: 4 ✓

### M6. 856 W Olive Ave · RM/RH · 17,297 sq ft (142.6 × 179.4)

- Over 15,000 sq ft: no density limit, FAR 75% = 12,973 sq ft → 12.
- Parking: 14,887 sq ft of ground left after the front yard. 11 homes: 5,844 + 28 spaces (8,400) fits. 12 homes: 6,375 + 30 spaces (9,000) doesn't → **11**.
- **Result: 11, parking.** Engine: 11 ✓

### M7. 526 Fano St D · RM/RH · 2,753 sq ft

- Under 15,000 sq ft and under 5,000: 1 home at 2,500 sq ft each. ADU law: 3.
- **Result: 3, ADU law.** Engine: 3 ✓

### M8. 543 W Duarte Rd · RH · 23,281 sq ft

- Over 15,000 sq ft: FAR 75% = 17,461 sq ft → 16.4 → **16**. Near transit: no parking.
- **Result: 16, envelope.** Engine: 16 ✓

### M9. 950 W Foothill Blvd · NC · 19,596 sq ft

- Homes in NC are marked LUE (only where the Land Use Element allows). We have no map, so none counted.
- **Result: 0, not counted.** Engine: 0 ✓

## Santa Clarita

Checked against the Santa Clarita Municipal Code, Title 17 (eCode360), read
November 1, 2026. Density is per acre, so land per home is 43,560 divided by it.

### C1. 19771 Terri Dr · UR2 · 22,211 sq ft

- Single-family only (Ch. 17.42) → 1 home. **Result: 4, SB 9.** Engine: 4 ✓

### C2. 23453 Darcy Ln · UR1 · 9,287 sq ft

- Single-family only → 1 home. **Result: 4, SB 9.** Engine: 4 ✓

### C3. 15906 Pashley St · NU5 · 109,170 sq ft

- Single-family only → 1 home; subdividing isn't modeled. **Result: 4, SB 9.** Engine: 4 ✓

### C4. 26476 Township St · UR3 · 7,736 sq ft

- 11 per acre = 3,960 sq ft per home → 1.95 → **1**. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### C5. 28494 N Herrera Street · UR4 · 31,130 sq ft

- 18 per acre = 2,420 sq ft per home → 12.9 → **12**. **Result: 12, lot area.** 14 homes today. Engine: 12 ✓

### C6. 27905 Tyler Ln · UR5 · 61,197 sq ft

- 30 per acre = 1,452 sq ft per home → 42.1 → **42**. **Result: 42, lot area.** 52 homes today. Engine: 42 ✓

### C7. 23310 Cinema Dr · MX-C · 40,532 sq ft

- 30 per acre = 1,452 sq ft per home → 27.9 → **27**. **Result: 27, lot area.** Engine: 27 ✓

### C8. 22432 12th St · MX-N · 4,869 sq ft

- 18 per acre = 2,420 sq ft per home → **2**. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### C9. 17737 Sierra Hwy · CC · 14,644 sq ft

- Homes not counted in CC (see METHODOLOGY). **Result: 0.** Engine: 0 ✓

## Duarte

Checked against the Duarte Development Code (Municode, through Ord. No. 927), read
November 1, 2026.

### D1 to D3. R1, R1A and R1D lots

- 1835 Bradbury Ave, 2621 Starcrest Dr, 2228 High Mesa Dr: one home each (Table 2-1 and 2-3). **Result: 4, SB 9.** Engine: 4 ✓

### D4. 1709 3rd St · R2 · 7,412 sq ft

- Two-family at most (Table 2-1) → **2**. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### D5. 1392 3rd St · R3 · 6,424 sq ft (60.5 × 106.7)

- 2,074 sq ft per home (Table 2-4) → 3.1 → **3**. Envelope: 50.5 × 56.7 × 0.995 × 3 stories = 8,547 sq ft → 8.
- **Result: 3, lot area.** 4 homes today. Engine: 3 ✓

### D6. 1709 Huntington Dr · R4 · 28,287 sq ft

- 1,556 sq ft per home → 18.2 → **18**. **Result: 18, lot area.** Engine: 18 ✓

### D7. 1475 Huntington Dr · CG · 16,967 sq ft

- Table 2-5 lists no dwellings. **Result: 0, not allowed.** Engine: 0 ✓

## Long Beach (residential zones)

Checked against the Long Beach Municipal Code, Title 21 (Municode, Ch. 21.31), read
November 1, 2026.

### B1. 5507 E Pageantry St · R-1-N · 5,214 sq ft

- One home. FAR 0.6 = 3,128 sq ft → 2.9 → 2. **Result: 4, SB 9.** Engine: 4 ✓

### B2. 5521 E Sorrento Dr · R-1-S · 3,287 sq ft

- One home. FAR 1.2 = 3,944 sq ft → 3.7 → 3. **Result: 4, SB 9.** Engine: 4 ✓

### B3. 771 Freeman Ave · R-2-N · 6,754 sq ft

- 2 per lot; 3,000 per home → **2**. FAR 0.6 = 4,052 sq ft → 3. ADU law: 3. **Result: 3, ADU law.** 4 homes today. Engine: 3 ✓

### B4. 3901 E 4th St · R-3-T · 38,283 sq ft

- Over 15,000 sq ft: 2,400 per home (Table 31-2B) → 15.95 → **15**. **Result: 15, lot area.** Engine: 15 ✓

### B5. 3637 E Ocean Blvd · R-4-R · 11,217 sq ft

- 3,201 to 15,000 sq ft: 1,500 per home → 7.5 → **7**. **Result: 7, lot area.** Engine: 7 ✓

### B6. 2907 Claremore Ln · R-4-R · 25,626 sq ft

- Over 15,000 sq ft: 1,450 per home → 17.7 → **17**. **Result: 17, lot area.** Engine: 17 ✓

### B7. 3737 Atlantic Ave · R-4-N · 58,572 sq ft

- Over 22,500 sq ft: 975 per home → 60.1 → **60**. **Result: 60, lot area.** 169 homes stand here today. Engine: 60 ✓

## Lancaster (residential zones)

Checked against the Lancaster Municipal Code, Ch. 17.08 (Municode), read November 1, 2026.

### N1 to N3. R-7000, R-10,000 and RR-1 lots

- 1132 Langhorn St, 1723 Granville Way, 43710 Ryckebosch Ln: one home each. **Result: 4, SB 9.** Engine: 4 ✓

### N4. 45537 Corkwood Ave · MDR · 6,000 sq ft

- 15 per acre = 2,904 sq ft per home → 2.07 → **2**. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### N5. 902 W Newgrove St · HDR · 8,232 sq ft

- 30 per acre = 1,452 sq ft per home → 5.7 → **5**. **Result: 5, lot area.** Engine: 5 ✓

## Gardena

Checked against the Gardena Municipal Code, Title 18 (eCode360), read November 1, 2026.

### G1. 1911 W 160th St · R-1 · 5,006 sq ft

- One home (§18.12.050). **Result: 4, SB 9.** Engine: 4 ✓

### G2. 1658 W 166th St · R-3 · 7,500 sq ft

- 17 per acre → 2.93, rounded up at .5 (§18.16.050) → **3**. **Result: 3, lot area.** Engine: 3 ✓

### G3. 14807 S Normandie Ave · R-4 · 18,438 sq ft

- Under ½ acre: 25 per acre → 10.6, rounded up → **11**. **Result: 11, lot area.** 19 homes today. Engine: 11 ✓

### G4. 15210 S Ave A · R-4 · 30,894 sq ft

- ½ acre or more: 30 per acre → 21.3 → **21**. **Result: 21, lot area.** Engine: 21 ✓

### G5. 16321 S Western Ave · C3-HO-5 · 12,904 sq ft

- HO-5: 50 per acre (Ch. 18.21) → 14.8 → **14**. **Result: 14, lot area.** Engine: 14 ✓

### G6. 1957 W 144th St · C3-HO-6 · 9,774 sq ft (70 × 140)

- HO-6: 70 per acre → 15.7 → 15. Parking at 1.5 per home, 6 stories: 14 homes 2,479 + 6,300 fits in 9,425 sq ft; 15 homes 2,656 + 6,900 doesn't → **14**.
- **Result: 14, parking.** Engine: 14 ✓

### G7. 1440 W 178th St · M1-HO-4 · 17,182 sq ft

- HO-4: 30 per acre → 11.8 → **11**. **Result: 11, lot area.** Engine: 11 ✓

## Norwalk (residential zones)

Checked against the Norwalk Municipal Code, Ch. 17.05 (eCode360), read November 1, 2026.

### O1. 13508 Leibacher Ave · R-1 · 5,196 sq ft

- One home. FAR 0.40 = 2,078 sq ft → 1.96 → 1. **Result: 4, SB 9.** Engine: 4 ✓

### O2. 11037 Barnwall St · R-2 · 15,059 sq ft

- At 9,000 sq ft or more: 2,722 per home → 5.5 → **5**. FAR 0.45 = 6,777 sq ft → 6. **Result: 5, lot area.** 10 homes today. Engine: 5 ✓

### O3. 12165 Pine St · R-3 · 6,791 sq ft

- 5,000 to 6,999 sq ft: 3 homes. FAR 0.50 = 3,396 sq ft → 3. **Result: 3, lot area.** Engine: 3 ✓

### O4. 12226 Sproul St · R-3 · 11,157 sq ft

- 1,980 per home → 5.6 → **5**. FAR 0.50 → 5. **Result: 5, lot area.** Engine: 5 ✓

### O5. 11433 Excelsior Dr · R-2 · 43,864 sq ft

- 2,722 per home → 16.1 → **16**. **Result: 16, lot area.** Engine: 16 ✓

## Santa Fe Springs (residential zones)

Checked against the Santa Fe Springs Code of Ordinances, Ch. 155 (Municode), read November 1, 2026.

### F1. 11030 Davenrich St · R-1 · 7,471 sq ft

- One home (§155.066). Coverage 40% × 2 stories = 5,977 sq ft → 5.6 → 5. **Result: 4, SB 9.** Engine: 4 ✓

### F2. 10800 Pioneer Blvd · R-3 · 193,333 sq ft

- 25 per acre = 1,742.4 sq ft per home → 110.96 → **110**. **Result: 110, lot area.** 107 homes today. Engine: 110 ✓

### F3. 12341 Heritage Springs Dr · R-3 · 59,585 sq ft

- 1,742.4 sq ft per home → 34.2 → **34**. **Result: 34, lot area.** Engine: 34 ✓

## Whittier (residential zones)

Checked against the Whittier Municipal Code, Title 18 (Municode), read November 1, 2026.

### H1. 14854 Carnell St · R-1 · 15,981 sq ft

- One home (§18.16.020). **Result: 4, SB 9.** Engine: 4 ✓

### H2. 13719 Mar Vista St · R-2 · 15,104 sq ft

- 3,000 sq ft per home (§18.18.020) → 5.03 → **5**. **Result: 5, lot area.** Engine: 5 ✓

### H3. 7703 Comstock Ave · R-3 · 7,035 sq ft

- Over 7,000 sq ft: 1,750 per home (§18.20.020) → 4.02 → **4**. **Result: 4, lot area.** 8 homes today. Engine: 4 ✓

### H4. 7727 Newlin Ave · R-4 · 5,965 sq ft

- 7,000 sq ft or less: 2,050 per home (§18.22.020) → **2**. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### H5. 7723 Milton Ave · R-4 · 7,196 sq ft

- 7,001 to 19,999 sq ft: 1,400 per home → 5.1 → **5**. **Result: 5, lot area.** Engine: 5 ✓

### H6. 8930 Painter Ave · R-4 · 119,792 sq ft

- 20,000 sq ft or more: 1,250 per home → 95.8 → **95**. **Result: 95, lot area.** Engine: 95 ✓

## Arcadia (residential zones)

Checked against the Arcadia Development Code (Municode), read November 1, 2026.

### A1. 45 W Magna Vista Ave · R-1 · 11,655 sq ft

- One home. Floor area: 4,375 + 35% of 1,655 = 4,954 sq ft → 4.7 → 4. **Result: 4, SB 9.** Engine: 4 ✓

### A2. 462 Arbolada Dr · R (read as R-0) · 20,494 sq ft

- One home. Floor area: 7,375 + 20% of 494 = 7,474 sq ft → 7. **Result: 4, SB 9.** Engine: 4 ✓

### A3. 307 Genoa St · R-2 · 10,144 sq ft

- 3,750 per home → 2.7 → **2**. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### A4. 135 Diamond St · R-3 · 7,966 sq ft

- 1,089 per home (40 per acre) → 7.3 → **7**. **Result: 7, lot area.** Engine: 7 ✓

### A5. 437 S Baldwin Ave · R-3-R · 11,000 sq ft (50.1 × 219.9)

- 1,450 per home → 7. Envelope: 18 ft, one story: 30.1 × 184.9 × 0.998 = 5,556 sq ft → 5.2 → **5**. **Result: 5, envelope.** Engine: 5 ✓

## South Gate (NL and NM)

Checked against the South Gate Municipal Code, Ch. 11.25 (eCode360), read November 1, 2026.

### Q1. 8976 Annetta Ave · NL · 5,108 sq ft

- One main home (see METHODOLOGY section 28). **Result: 4, SB 9.** Engine: 4 ✓

### Q2. 9739 Elizabeth Ave · NM · 4,177 sq ft

- 20 per acre = 2,178 sq ft per home → 1.9 → **1**. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### Q3. 4100 Firestone Blvd · NM · 18,030 sq ft

- 2,178 sq ft per home → 8.3 → **8**. **Result: 8, lot area.** Engine: 8 ✓

## Culver City (residential zones)

Checked against the Culver City Municipal Code, §17.210.020 (American Legal), read November 1, 2026.
The city has no minimum parking (§17.320.020).

### V1. 10826 Franklin Ave · R1 · 4,987 sq ft

- One home. FAR 0.45 = 2,244 sq ft → 2.1 → 2. **Result: 4, SB 9.** Engine: 4 ✓

### V2. 4174 Baldwin Ave · R2 · 6,755 sq ft

- 2 per parcel. Floor area: 1,500 + 40% = 4,202 sq ft → 3.95 → 3. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### V3. 3845 Sawtelle Blvd · RLD · 6,299 sq ft

- 35 per acre = 1,244.57 sq ft per home → 5.06 → **5**. **Result: 5, lot area.** Engine: 5 ✓

### V4. 4450 Overland Ave · RMD · 9,504 sq ft

- 50 per acre = 871.2 sq ft per home → 10.9 → **10**. **Result: 10, lot area.** Engine: 10 ✓

### V5. 6060 Buckingham Pkwy · RHD · 35,407 sq ft

- 70 per acre = 622.29 sq ft per home → 56.9 → **56**. **Result: 56, lot area.** 50 homes today. Engine: 56 ✓

## Montebello (residential zones)

Checked against the Montebello Municipal Code, Exhibit 17.10.020 (Municode), read November 1, 2026.

### T1, T2. 1319 Via Camille (R-1), 641 N Maple Ave (R-A)

- One home per lot. **Result: 4, SB 9.** Engine: 4 ✓

### T3. 817 Palm Pl · R-2 · 4,982 sq ft

- 3,000 per home → **1**. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### T4. 216 N 4th St · R-3 · 6,753 sq ft

- 3,000 per home → **2**. ADU law: 3. **Result: 3, ADU law.** 4 homes today. Engine: 3 ✓

### T5. 633 N Taylor Ave · R-4 · 48,727 sq ft

- 2,000 per home → 24.4 → **24**. **Result: 24, lot area.** 41 homes today. Engine: 24 ✓

## Rolling Hills Estates (R-A zones)

Checked against the Rolling Hills Estates Municipal Code, Ch. 17.06 (Municode), read November 1, 2026.

### R1 to R3. 78 Dapplegray Ln, 5228 Bluemound Rd, 2 Strawberry Ln

- §17.06.050 allows one dwelling per lot. SB 9 path: 4. **Result: 4, SB 9.** Engine: 4 ✓

## West Covina (R-1, R-A and MF zones)

Checked against the West Covina Municipal Code, Ch. 26 Art. II (Municode), read November 1, 2026.

### W-1. 521 S Astell Ave · R-1 · 9,408 sq ft

- One home. Floor area: 3,100 + 20% of 1,908 = 3,482 sq ft → 3.3 → 3. **Result: 4, SB 9.** Engine: 4 ✓

### W-2. 3330 E Holt Ave · R-A · 15,109 sq ft

- One home. Floor area: 3,600 + 20% of 5,109 = 4,622 sq ft → 4.3 → 4. **Result: 4, SB 9.** Engine: 4 ✓

### W-3. 1912 Tanglewood Dr · MF-8 · 5,724 sq ft

- 8 per net acre = 5,445 sq ft per home → **1**. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### W-4. 1799 Aspen Village Way · MF-15 · 28,350 sq ft

- 15 per acre = 2,904 sq ft per home → 9.8 → **9**. **Result: 9, lot area.** Engine: 9 ✓

### W-5. 223 S Bandy Ave · MF-20 · 6,759 sq ft

- 20 per acre = 2,178 sq ft per home → 3.1 → **3**. **Result: 3, lot area.** Engine: 3 ✓

### W-6. 2117 E Garvey Ave N · MF-45 · 6,200 sq ft

- 45 per acre = 968 sq ft per home → 6.4 → **6**. **Result: 6, lot area.** Engine: 6 ✓

## Westlake Village

Rules: Westlake Village Municipal Code, Article 9, read on Municode 2026-11-01, plus the city's pages for the two mixed-use districts. The yards area is scaled by lot area ÷ (width × depth), as the engine does for irregular lots.

### WL-1. 6156 Hedgewall Dr · R-1 · 8,256 sq ft, 75.1 × 110.5 ft

- One home (§9.5.020) → **1**.
- Sides 10% of width = 7.51 ft each; front 20, rear 25. (75.1 − 15.02) × (110.5 − 45) = 3,935; × 0.995 = 3,915; × 2 stories = 7,830 ÷ 1,062.5 = 7.4 → 7.
- SB 9: 4. **Result: 4, SB 9.** Engine: 4 ✓

### WL-2. 6148 Hedgewall Dr · R-1 · 7,803 sq ft, 71.0 × 110.5 ft

- Under the 8,000 sq ft minimum, but a lot that exists keeps its one home → **1**.
- (71 − 14.2) × 65.5 = 3,720; × 0.995 = 3,700; × 2 = 7,400 ÷ 1,062.5 = 6.96 → 6.
- SB 9: 4. **Result: 4, SB 9.** Engine: 4 ✓

### WL-3. 3956 Freshwind Cir · RPD · 10,390 sq ft, 112.0 × 137.4 ft

- Homes follow the General Plan designation, which we have no map of: one per lot (assumed) → **1**.
- Sides capped at 10 ft: (112 − 20) × 92.4 = 8,501; × 0.675 = 5,739; × 2 = 11,478 ÷ 1,062.5 = 10.8 → 10.
- ADU law: 3. No SB 9 (conservative; see methodology). **Result: 3, ADU law.** Engine: 3 ✓

### WL-4. 1 Sherwood Dr · MHP · 5,595 sq ft, 75.5 × 94.6 ft

- §9.7.040: one home per mobile home lot → **1**.
- Front 15, others 5: 65.5 × 74.6 = 4,886; × 0.783 = 3,827; × 1 story ÷ 1,062.5 = 3.6 → 3.
- ADU law: 3, which likely runs high here. **Result: 3, ADU law.** Engine: 3 ✓

### WL-5. 5711 Corsa Ave · Mixed-Use Corsa · 56,092 sq ft

- 20 per acre = 2,178 sq ft per home → 25.75 → **25**.
- 40% coverage = 22,437 × 3 stories = 67,310 ÷ 1,062.5 = 63.
- **Result: 25, lot area.** Engine: 25 ✓

### WL-6. 5701 Lindero Canyon Rd · Mixed-Use Lindero · 330,577 sq ft

- 32 per acre = 1,361.25 sq ft per home → 242.85 → **242**.
- 40% coverage = 132,231 × 3 = 396,692 ÷ 1,062.5 = 373.
- **Result: 242, lot area.** Engine: 242 ✓

## Alhambra

Rules: Alhambra Municipal Code, Title 23, read on American Legal 2026-11-01. SCAG's R-1, R-2 and R-3 are read as RL, RM and RH (see methodology).

### AL-1. 2600 Orange Grove Ave · R-1 (RL) · 6,137 sq ft

- One detached home → **1**. FAR 0.40 = 2,455 ÷ 1,062.5 = 2.3 → 2.
- SB 9: 4. **Result: 4, SB 9.** Engine: 4 ✓

### AL-2. 2040 S 3rd St · R-2 (RM) · 7,015 sq ft

- 18 per acre = 2,420 sq ft per home → 2.9 → **2**.
- 45% coverage = 3,157 × 3 stories = 9,470 ÷ 1,062.5 = 8.9 → 8.
- ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### AL-3. 1850 Garvey Ave · R-3 (RH) · 7,925 sq ft

- Under 10,000 sq ft: 24 per acre = 1,815 sq ft per home → 4.4 → **4**. **Result: 4, lot area.** Engine: 4 ✓

### AL-4. 2916 W Ramona Rd · R-3 (RH) · 12,451 sq ft, 103.2 × 122.1 ft

- At 10,000 sq ft and up: 43 per acre = 1,013 sq ft per home → 12.3 → 12.
- Parking: 12,451 − front strip (15 × 103.2 × 0.988 = 1,530) = 10,921 of ground. 11 homes: 2,338 + 28 spaces (8,400) = 10,738 fits. 12 homes: 2,550 + 30 spaces (9,000) doesn't → **11**.
- **Result: 11, parking.** Engine: 11 ✓ (The lot has 12 homes today, so no net new.)

### AL-5. 150 N Garfield Ave · CBD · 11,332 sq ft

- 64 per acre = 680.6 sq ft per home → 16.6 → 16.
- Parking at 1.5 + 0.3 guest: 15 homes: 3,188 + 27 spaces (8,100) = 11,288 fits. 16 homes: 3,400 + 29 spaces (8,700) doesn't → **15**.
- **Result: 15, parking.** Engine: 15 ✓

### AL-6. 1129 E Main St · EMC · 7,410 sq ft

- 30 per acre = 1,452 sq ft per home → 5.1 → **5**. **Result: 5, lot area.** Engine: 5 ✓

## Palmdale

Rules: Palmdale Municipal Code, Title 17, read on eCode360 2026-11-01.

### PA-1. 4648 Paseo Hermoso · SFR 3 · 7,755 sq ft

- One home → **1**. 50% coverage = 3,877 × 2 stories = 7,755 ÷ 1,062.5 = 7.3 → 7.
- SB 9: 4. **Result: 4, SB 9.** Engine: 4 ✓

### PA-2. 40332 Tesoro Ln · SFR 1 · 24,183 sq ft

- One home → **1**. 30% coverage = 7,255 × 2 = 14,510 ÷ 1,062.5 = 13.7 → 13.
- SB 9: 4. **Result: 4, SB 9.** Engine: 4 ✓

### PA-3. 2637 E Avenue Q4 · RN 1 · 11,402 sq ft

- 10 per acre = 4,356 sq ft per home → 2.6 → **2**. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### PA-4. 39039 Yucca Tree St · RN 2 · 11,204 sq ft

- 20 per acre = 2,178 sq ft per home → 5.1 → **5**. **Result: 5, lot area.** Engine: 5 ✓

### PA-5. 1623 Watling Dr · RN 3 · 19,348 sq ft

- 30 per acre = 1,452 sq ft per home → 13.3 → **13**. **Result: 13, lot area.** Engine: 13 ✓

### PA-6. 38533 11th St E · RN 4 · 22,134 sq ft

- 50 per acre = 871.2 sq ft per home → 25.4 → **25**. **Result: 25, lot area.** Engine: 25 ✓

### PA-7. 1358 E Palmdale Blvd · MU 1 · 17,794 sq ft

- 20 per acre = 2,178 sq ft per home → 8.2 → **8**. **Result: 8, lot area.** Engine: 8 ✓ (This lot fronts Palmdale Boulevard, where the frontage must hold nonresidential space, so it can run high.)

### PA-8. 803 W Palmdale Blvd · MEDFX · 21,802 sq ft

- 30 per acre = 1,452 sq ft per home → 15.01 → **15**. **Result: 15, lot area.** Engine: 15 ✓

## Carson

Rules: Carson Municipal Code, Article IX, read on eCode360 2026-11-01. A fraction of one-half or more permits another home (§9124.1).

### CA-1. 559 E 169th St · RS · 5,530 sq ft

- One dwelling per lot (§9124.1) → **1**. Sides 5 ft, front 20, rear 15: 44.9 × 65.7 = 2,950 × 2 stories = 5,900 ÷ 1,062.5 = 5.6 → 5.
- SB 9: 4. **Result: 4, SB 9.** Engine: 4 ✓

### CA-2. 118 W 234th St · RM-8 · 6,424 sq ft

- 8 per acre = 5,445 sq ft per home → 1.2 → **1**. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### CA-3. 750 Alondra Blvd · RM-12 · 12,158 sq ft

- 12 per acre = 3,630 sq ft per home → 3.35 → **3**. **Result: 3, lot area.** Engine: 3 ✓

### CA-4. 21105 S Santa Fe Ave · RM-25 · 8,772 sq ft

- 25 per acre = 1,742.4 sq ft per home → 5.03 → **5**. **Result: 5, lot area.** Engine: 5 ✓

### CA-5. 2543 E Carson St · RM-25 · 39,819 sq ft

- 39,819 ÷ 1,742.4 = 22.85, and the fraction rounds up → **23**. **Result: 23, lot area.** Engine: 23 ✓

### CA-6. 714 E Carson St · MU-CS · 51,680 sq ft

- 35 per acre = 1,244.57 sq ft per home → 41.5, which rounds up → **42**. **Result: 42, lot area.** Engine: 42 ✓ (86 homes today, so no net new.)

### CA-7. 440 E Sepulveda Blvd · MU-SB · 18,595 sq ft, 94 ft wide

- 25 per acre = 1,742.4 sq ft per home → 10.67, which rounds up → **11**. **Result: 11, lot area.** Engine: 11 ✓ (Under the 100 ft frontage for multiple-family, so the engine flags it.)

## Azusa

Rules: Azusa Development Code, Chapter 88, read on Municode 2026-11-01. Stories use the code's 2.5.

### AZ-1. 1350 N Alameda Ave · NG3-Low · 8,518 sq ft, 71.9 × 122.0 ft

- One home (no duplexes in the low column) → **1**.
- Yards 25, 25, 5 each side: 61.9 × 72 = 4,457; × 0.971 = 4,328; × 2.5 = 10,820 ÷ 1,062.5 = 10.2 → 10.
- SB 9: 4. **Result: 4, SB 9.** Engine: 4 ✓

### AZ-2. 556 W 11th St · NG1-Low · 7,374 sq ft, 53.0 × 139.3 ft

- One home → **1**. Yards 20, 20, 5: 43 × 99.3 = 4,270; × 0.999 = 4,265; × 2.5 = 10,662 ÷ 1,062.5 = 10.03 → 10.
- SB 9: 4. **Result: 4, SB 9.** Engine: 4 ✓

### AZ-3. 309 N Soldano Ave · NG2-Med · 7,569 sq ft

- 15 per acre = 2,904 sq ft per home → 2.6 → **2**. ADU law: 3. **Result: 3, ADU law.** Engine: 3 ✓

### AZ-4. 1325 N Azusa Ave · NG3-Mod · 20,271 sq ft

- 27 per acre = 1,613.33 sq ft per home → 12.6 → **12**. **Result: 12, lot area.** Engine: 12 ✓

### AZ-5. 246 N Azusa Ave · CAZ · 13,830 sq ft

- 27 per acre → 8.6 → **8**. **Result: 8, lot area.** Engine: 8 ✓

### AZ-6. 843 W Arrow Hwy · CAH · 32,862 sq ft

- 27 per acre → 20.4 → **20**. **Result: 20, lot area.** Engine: 20 ✓
