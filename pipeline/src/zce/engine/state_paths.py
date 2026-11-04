"""What SB 79 and the State Density Bonus Law could allow on one lot.

These are reported apart from max_units. Both come with conditions the data
can't test, such as affordable homes, tenant history and local delay plans, so
adding them to "allowed today" would overstate what a lot can do by default.

Ported to web/src/engine/statePaths.ts. shared/fixtures/state_paths.json holds
cases both versions must match.
"""

from math import ceil, floor

# Gov. Code §65912.157(a): (height ft, homes per acre, residential FAR).
SB79_STANDARDS = {
    (1, "quarter"): (75, 120, 3.5),
    (1, "half"): (65, 100, 3.0),
    (2, "quarter"): (65, 100, 3.0),
    (2, "half"): (55, 80, 2.5),
}
QUARTER_MILE_FT = 1320
HALF_MILE_FT = 2640
ADJACENT_FT = 200  # §65912.156(a); adjacent sites get +40 per acre and +1 FAR (§65912.157(e))
MIN_HOMES = 5  # §65912.157(a), and §65915(i) for the density bonus
SQFT_PER_ACRE = 43560


def sb79_units(area_sqft, dist_t1_ft, dist_t2_ft, zone_eligible, half_mile_applies, gross_sqft_per_unit):
    """Most homes SB 79's standards allow, or None if the lot doesn't qualify."""
    if not zone_eligible:
        return None
    best = None
    for tier, dist in ((1, dist_t1_ft), (2, dist_t2_ft)):
        if dist is None:
            continue
        if dist <= QUARTER_MILE_FT:
            band = "quarter"
        elif dist <= HALF_MILE_FT and half_mile_applies:
            band = "half"
        else:
            continue
        _, per_acre, far = SB79_STANDARDS[(tier, band)]
        if dist <= ADJACENT_FT:
            per_acre, far = per_acre + 40, far + 1
        units = min(floor(area_sqft / SQFT_PER_ACRE * per_acre), floor(area_sqft * far / gross_sqft_per_unit))
        if best is None or units > best:
            best = units
    return best if best is not None and best >= MIN_HOMES else None


def density_bonus_units(limits, share):
    """Homes with a density bonus of `share` (0.5 = 50%), or None if it can't be worked out.

    The bonus applies to the maximum density, so it needs a numeric density and
    at least 5 homes before the bonus. Fractions round up (§65915(f)(5)).
    Physical limits aren't applied, since waivers can lift them (§65915(e)).
    """
    base = [limits[k] for k in ("density", "lot_area_per_unit") if limits.get(k) is not None]
    if not base or min(base) < MIN_HOMES:
        return None
    return ceil(round(min(base) * (1 + share), 6))
