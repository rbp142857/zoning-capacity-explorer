# Methodology (draft)

*Draft as of milestone 3. Data sources, validation against official figures,
and the realistic redevelopment estimate are added in later milestones.*

This tool estimates the **maximum number of homes the zoning rules legally
allow** on each lot in Pasadena, and what limits that number. It is an
estimate for research and advocacy, **not legal or zoning advice**. Always
confirm with the City of Pasadena.

## 1. From the zoning code to rule files

We read Pasadena's Zoning Code (Title 17 of the Municipal Code, Municode
version of September 2, 2026) and wrote each zone's numbers into a
structured file, one per zone, in `cities/pasadena/rules/`. Every number
cites the section and table it came from. Where the code is ambiguous, or a
table is hard to read, the file says what we assumed and why.

16 zones are modeled: single-family (RS-1, RS-2, RS-4, RS-6), multifamily
(RM-12, RM-16, RM-16-1, RM-32, RM-48), commercial zones that allow housing
(CO, CL, CL-2), and zones that don't allow housing (CG, IG, OS, PS).

## 2. How many homes fit on one lot

For each lot we work out several separate limits. The **lowest** one is the
answer, and we record which limit it was (the *binding constraint*).

1. **Density.** Some zones cap homes per lot (RS: 1, RM-12: 2) or per acre
   (CL-2: 16 per acre).
2. **Land per home.** Other zones require a minimum amount of lot per home
   (RM-32: 1,360 sq ft per home). A 13,600 sq ft lot therefore allows 10.
   Pasadena's rounding rules are applied exactly as written.
3. **Building size (envelope).** We subtract the required front, side and
   rear setbacks, then apply limits on how much of the lot may be covered
   and, in multifamily zones, Pasadena's required garden space (29% to 37% of
   the lot). That gives the largest building footprint. We multiply by the
   number of stories the height limit allows, cap the result by any
   floor-area limit, and divide by the floor area one home uses: **1,062 sq ft**
   (an 850 sq ft home plus its share of halls and stairs).
4. **Parking.** Pasadena requires 2 covered spaces per home, plus guest
   spaces in buildings with 10 or more homes. We assume surface parking at
   300 sq ft per space including the driveway aisle, and count how many homes
   still fit once their parking takes its share of the lot. Garages under the
   building would allow more homes but cost much more; the feasibility
   milestone will look at that.

If housing isn't allowed in a zone, the answer is 0 ("use not permitted").
A lot smaller or narrower than today's minimum for new lots is **flagged,
not zeroed**, because existing lots can still be built on.

## 3. State law

California law overrides city zoning in several ways. We calculate local
zoning first, then each state law, and keep both numbers.

- **ADUs (Gov. Code §66314 and following):** any lot where a house fits can
  have that house plus a backyard unit and a junior unit inside the house,
  for 3 homes in total. We count this as an alternative to the local answer
  (whichever is larger), so it also applies in zones like RM-12 where the
  city allows 2.
- **SB 9 (Gov. Code §65852.21, §66411.7):** in single-family zones, two homes
  per lot; or a one-time split into two lots with two homes each, for 4 in
  total, if the lot is at least 2,400 sq ft. SB 9 does not apply in
  designated historic districts (Pasadena's landmark overlay districts), so
  those lots get the ADU path instead.
- **AB 2097 (Gov. Code §65863.2):** no parking minimums within ½ mile of a
  major transit stop, using SCAG's official list of stops.
- **Not yet modeled:** SB 79 (2025 transit-oriented upzoning) and the State
  Density Bonus Law. Capacity near transit is therefore **underestimated**.

## 4. What these numbers are not

- They are **theoretical maximums**, not predictions. Most lots will never be
  rebuilt, and many that are won't use their full allowance. A separate,
  clearly labeled "likely to redevelop" estimate comes in milestone 7.
- **Not yet modeled:** 2,607 lots in specific-plan-only districts (such as
  the Central District's mixed-use zones) and planned developments. They are
  reported separately rather than counted as zero.
- **Simplified:** hillside overlay standards, neighborhood-compatibility
  floor-area limits, blockface-average setbacks, encroachment planes, and
  extra setbacks next to single-family zones. Each simplification is listed
  in the rule files and counted in `reports/pasadena/capacity_report.md`.
- **SB 9 caveat:** SB 9 can't be used where it would demolish rent-restricted
  or recently rented housing. We have no tenancy data, so SB 9 capacity is
  overstated on rented lots.

## 5. Reform scenarios

The "Reform scenario" panel changes the rules and recalculates every lot in
your browser. Each lever, and what we assume when we apply it:

| Lever | What changes |
|---|---|
| Homes per lot in single-family zones | The city's one-home-per-lot cap becomes 2, 3, 4 or 6. Floor-area, setback and parking limits still apply, so on many lots the building envelope, not the cap, becomes the limit. |
| Minimum lot size in single-family zones | A lot may be split into as many lots of the new minimum size as fit; each gets the per-lot allowance. We don't check street frontage or access for the new lots. |
| Parking per home | Replaces the 2-space requirement in every zone (0 removes parking minimums, and guest parking with them). |
| No parking minimums near transit | Widens AB 2097's ½-mile radius (it can't be narrowed: that's state law). |
| Near major transit: extra stories / density | For multifamily and commercial zones within the chosen distance: stories are added; floor-area ratio grows in proportion so the extra stories are usable; required land per home is divided by the density factor. |
| Housing in General Commercial (CG) | CG lots use CL's housing standards (RM-32 density and gardens) with CG's own 45 ft height (4 stories) and FAR 0.80. |
| ADU homes per house | The ADU path adds 3 or 4 homes to a single-family lot instead of 2. |

A finding the tool makes visible: **legalizing fourplexes in single-family
zones adds little on its own** (about 2,400 homes citywide, even with parking
minimums removed, on top of roughly 114,000 already allowed). SB 9 already allows up to four homes on most such lots,
and the city's floor-area limits mean a typical 7,200 sq ft lot fits only two
homes of average size under local rules. A fourplex reform that also raised
the floor-area limit would show a different result.

The browser and the Python pipeline run the same calculations: an automated
test checks that both give identical answers for 415 lots under 9 scenarios,
and in development the page checks every lot under today's rules.

## 6. Checks that guard the numbers

- **Python and browser agree:** 415 lots x 9 scenarios are computed by both
  engines and compared exactly on every test run.
- **Reforms only add:** every lever loosens a rule, so a test checks that no
  lever lowers any lot's capacity. This test caught a real bug: allowing
  duplexes used to switch off the ADU option (house + ADU + junior ADU) on
  some lots, so a "more permissive" scenario lowered their capacity.

## 7. Realistic vs. theoretical capacity

Every number above is **theoretical**: the homes the rules allow if every lot
were rebuilt to the maximum. Most lots never will be. The **"likely to
redevelop"** estimate counts only lots that pass every one of these common
planning screens (thresholds in `cities/pasadena/city.yaml`):

1. **Zoning allows at least twice the homes already there, and at least 3 more.**
   Demolishing a house to gain one or two homes rarely pays for itself.
2. **The building is at least 50 years old** (or the lot is vacant).
3. **The building is assessed at less than the land.**
4. **Not a condo** (many owners rarely agree to sell together).
5. **Not in a landmark (historic) district** (demolition needs special review).

Only the city's own allowance (or a reform scenario's) counts toward this
estimate, not the state-law paths: adding an ADU, or a second house under SB 9,
usually keeps the existing home, and few eligible owners have used SB 9 so
far. Those homes are reported separately as theoretical capacity.

**Under today's rules: 4,907 new homes on 753 lots** pass every screen, compared
with 68,222 theoretical new homes. Nearly every other lot fails screen 1.

What this is **not**: a forecast. It doesn't say when, or how many, of these
lots will be rebuilt; that depends on rents, construction costs, interest
rates and owners' choices (the optional feasibility milestone looks at costs).

Caveats we want readers to know:

- **Prop 13 weakens screen 3.** When a property sells, the assessor puts most
  of the price into land value. In Pasadena the building-to-land ratio is
  about 1.7 for owners who bought before 1980 but about 0.4 for buyers since
  2010, so this screen mostly flags recently sold properties. It passes 77% of
  lots; the other screens do most of the work.
- **City rules and SB 9 are treated differently.** A fourplex allowed by a
  city reform counts toward the realistic estimate; the same fourplex allowed
  through SB 9 (lot split plus two homes each) doesn't. We chose this because
  SB 9 has seen little use and comes with owner-occupancy and tenant
  conditions a city rule might not have. It means a fourplex reform raises
  the realistic estimate (by about 7,800) far more than its theoretical
  capacity (by about 460). Readers who disagree with this choice should
  focus on the theoretical numbers for single-family zones.
- Under the transit upzoning scenario (+2 stories, double density within ½
  mile), the realistic estimate rises by about 6,500 homes. Reforms that
  double allowances on older multifamily lots move it most.
