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

- **ADUs (Gov. Code §66314 and following):** a lot with one house can add a
  backyard unit and a junior unit inside the house, for 3 homes in total.
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
