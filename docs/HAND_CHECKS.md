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
