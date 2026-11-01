"""The zoning math: one function per constraint.

Each function answers "how many units does THIS rule allow on THIS lot?"
and returns an int, or None when the rule doesn't apply to the zone. The
final capacity is the minimum over all of them (see capacity.py).

No GIS here: a lot is just a few numbers (area, width, depth). That keeps the
math easy to read, easy to test with a calculator, and easy to port to the
browser in milestone 5.

Units used throughout: square feet and feet.
"""

import math
from dataclasses import dataclass, field

from zce.rules.schema import Band, Banded, SideSetback, ZoneRules

SQFT_PER_ACRE = 43_560


@dataclass(frozen=True)
class Lot:
    """Everything the engine needs to know about a parcel."""

    area_sqft: float
    width_ft: float  # short side of the lot's bounding rectangle (assumed street frontage)
    depth_ft: float  # long side
    overlays: tuple[str, ...] = ()
    dist_major_transit_ft: float | None = None
    existing_units: float | None = None
    dist_single_family_ft: float | None = None  # to the nearest single-family-zoned lot

    @property
    def shape_factor(self) -> float:
        """How much of its bounding rectangle the lot fills (1.0 = a perfect rectangle).

        Setbacks are computed on the rectangle, then scaled by this factor so
        an irregular lot doesn't get credit for area it doesn't have.
        """
        rect = self.width_ft * self.depth_ft
        return min(1.0, self.area_sqft / rect) if rect > 0 else 0.0


@dataclass(frozen=True)
class EngineAssumptions:
    """Numbers the code doesn't give us (see city.yaml -> assumptions)."""

    gross_sqft_per_unit: float  # building floor area per unit, incl. hallways
    parking_stall_sqft: float  # surface area per parking space, incl. aisle share
    min_home_sqft: float = 0  # smallest house counted (see city.yaml)
    extra: dict = field(default_factory=dict)


# --- Small helpers -----------------------------------------------------------


def round_units(x: float, mode: str) -> int:
    """Round a fractional unit count the way the code says to.

    floor            1.99 -> 1   (the default: you can't build part of a home)
    up_above_0_75    2.76 -> 3, 2.75 -> 2   (Pasadena RM-16)
    nearest_half_up  2.5 -> 3, 2.49 -> 2    (Pasadena RM-32/RM-48)
    up               2.01 -> 3, 2.0 -> 2    (Burbank mixed use)
    """
    # Tiny tolerance so 2.9999999 (floating-point noise) counts as 3.
    whole = math.floor(x + 1e-9)
    fraction = x - whole
    if mode == "floor":
        return whole
    if mode == "up_above_0_75":
        return whole + 1 if fraction > 0.75 + 1e-9 else whole
    if mode == "nearest_half_up":
        return whole + 1 if fraction >= 0.5 - 1e-9 else whole
    if mode == "up":
        return whole + 1 if fraction > 1e-9 else whole
    raise ValueError(f"unknown rounding mode {mode!r}")


def _pick(rule_value, lot: Lot) -> Band | float | None:
    """Resolve a plain number or a Banded table to the value for this lot."""
    if isinstance(rule_value, Banded):
        return rule_value.pick(lot.area_sqft, lot.width_ft, lot.dist_single_family_ft)
    return rule_value


def _band_area(band: Band, lot: Lot, units: int = 0) -> float | None:
    """Evaluate a band's area formula: share x lot + plus + per-unit, at least `at_least`."""
    if band.share is None:
        return None if band.value is None else band.value
    area = band.share * lot.area_sqft + band.plus_sqft + band.plus_sqft_per_unit * units
    return max(area, band.at_least_sqft)


def _number(rule_value, lot: Lot) -> float | None:
    """A rule that resolves to a single number (stories, height, share)."""
    picked = _pick(rule_value, lot)
    if isinstance(picked, Band):
        return picked.value if picked.share is None else picked.share
    return picked


def side_setback_ft(rule_value: float | SideSetback, lot: Lot) -> float:
    if isinstance(rule_value, SideSetback):
        return min(max(rule_value.pct_of_width * lot.width_ft, rule_value.min_ft), rule_value.max_ft)
    return rule_value


# --- Constraint 1: density (units per lot, units per acre) --------------------


def density_limit(rules: ZoneRules, lot: Lot) -> int | None:
    """Units allowed by a flat cap per lot or a units-per-acre rate."""
    limits = []
    if rules.max_units_per_lot is not None:
        limits.append(rules.max_units_per_lot.value)
    if rules.units_per_acre is not None:
        mode = rules.density_rounding.value if rules.density_rounding else "floor"
        limits.append(round_units(lot.area_sqft / SQFT_PER_ACRE * rules.units_per_acre.value, mode))
    return min(limits) if limits else None


# --- Constraint 2: minimum lot area per unit ------------------------------------


def lot_area_per_unit_limit(rules: ZoneRules, lot: Lot) -> int | None:
    """Units allowed when each unit needs a minimum slice of land.

    Example: RM-32 needs 1,360 sf of lot per unit, so a 13,600 sf lot allows
    13,600 / 1,360 = 10 units. Lots below `small_lot_units_below_sqft` use a
    lookup table instead (Pasadena §17.22.070.A.2).
    """
    if (
        rules.small_lot_units is not None
        and rules.small_lot_units_below_sqft is not None
        and lot.area_sqft < rules.small_lot_units_below_sqft
    ):
        return int(rules.small_lot_units.value.pick(lot.area_sqft, lot.width_ft, lot.dist_single_family_ft).value)
    if rules.lot_area_per_unit_sqft is None:
        return None
    mode = rules.density_rounding.value if rules.density_rounding else "floor"
    return round_units(lot.area_sqft / _number(rules.lot_area_per_unit_sqft.value, lot), mode)


# --- Constraint 3: buildable envelope ---------------------------------------------


def setback_area_sqft(rules: ZoneRules, lot: Lot) -> float:
    """Ground area left after front, side and rear setbacks.

    We treat the lot as its bounding rectangle (width x depth), subtract the
    setbacks, then scale by the shape factor for irregular lots.
    """
    s = rules.setbacks
    usable_width = lot.width_ft - 2 * side_setback_ft(s.side_ft.value, lot)
    usable_depth = lot.depth_ft - s.front_ft.value - s.rear_ft.value
    return max(0.0, usable_width) * max(0.0, usable_depth) * lot.shape_factor


def max_footprint_sqft(rules: ZoneRules, lot: Lot) -> float:
    """Largest building footprint: the tightest of setbacks, coverage and open space."""
    caps = [setback_area_sqft(rules, lot)]
    if rules.lot_coverage is not None:
        picked = _pick(rules.lot_coverage.value, lot)
        cap = _band_area(picked, lot) if isinstance(picked, Band) else picked * lot.area_sqft
        if cap is not None:  # None = "no maximum" for this lot size
            caps.append(cap)
    if rules.min_open_space_share is not None:
        caps.append(lot.area_sqft * (1 - _number(rules.min_open_space_share.value, lot)))
    return min(caps)


def envelope_limit(rules: ZoneRules, lot: Lot, a: EngineAssumptions) -> int:
    """Units that physically fit in the largest legal building.

    floor area = footprint x stories, capped by FAR and any floor-area
    formula; units = floor area / gross floor area per unit.
    """
    stories = _number(rules.max_stories.value, lot) or 0
    floor_area = max_footprint_sqft(rules, lot) * stories
    if rules.max_far is not None:
        floor_area = min(floor_area, rules.max_far.value * lot.area_sqft)

    units = math.floor(floor_area / a.gross_sqft_per_unit + 1e-9)

    if rules.max_floor_area is not None:
        band = rules.max_floor_area.value.pick(lot.area_sqft, lot.width_ft, lot.dist_single_family_ft)
        if band.plus_sqft_per_unit:
            # Allowance grows with each unit (e.g. RM-12: 35% of lot + 500 sf per
            # unit). Solve n x gross <= share x lot + per_unit x n for n.
            fixed = band.share * lot.area_sqft + band.plus_sqft
            per_unit_net = a.gross_sqft_per_unit - band.plus_sqft_per_unit
            by_formula = math.floor(fixed / per_unit_net + 1e-9) if per_unit_net > 0 else units
        else:
            by_formula = math.floor(_band_area(band, lot) / a.gross_sqft_per_unit + 1e-9)
        units = min(units, by_formula)
        floor_area = min(floor_area, fixed + band.plus_sqft_per_unit if band.plus_sqft_per_unit else _band_area(band, lot))

    # A lot too small for an average-size new unit can still hold one small
    # house, as long as the limits allow at least min_home_sqft of floor area.
    if units < 1 and a.min_home_sqft and floor_area >= a.min_home_sqft:
        units = 1
    return max(0, units)


# --- Constraint 4: parking ---------------------------------------------------------


def required_stalls(rules: ZoneRules, units: int) -> int:
    """Parking spaces required for `units` homes (fractions of .5 round up, §17.46.040.G)."""
    if rules.parking_per_unit is None:
        return 0
    stalls = units * rules.parking_per_unit.value
    if rules.guest_parking_per_unit and units >= (rules.guest_parking_min_units or 0):
        stalls += units * rules.guest_parking_per_unit.value
    return round_units(stalls, "nearest_half_up")


def parking_limit(rules: ZoneRules, lot: Lot, a: EngineAssumptions, exempt: bool = False) -> int | None:
    """Units that fit once required SURFACE parking takes its share of the ground.

    The ground available for building + parking is the lot minus the front
    setback strip (parking isn't allowed there) and minus required open
    space. A unit takes (gross unit size / stories) of footprint plus its
    parking stalls. We find the largest unit count that fits.

    Returns None when no parking is required (or state law exempts the lot),
    i.e. this constraint doesn't apply.
    """
    if exempt or rules.parking_per_unit is None or rules.parking_per_unit.value == 0:
        return None
    stories = _number(rules.max_stories.value, lot) or 0
    if stories <= 0:
        return 0

    front_strip = rules.setbacks.front_ft.value * lot.width_ft * lot.shape_factor
    ground = lot.area_sqft - front_strip
    if rules.min_open_space_share is not None:
        ground = min(ground, lot.area_sqft * (1 - _number(rules.min_open_space_share.value, lot)))
    footprint_per_unit = a.gross_sqft_per_unit / stories

    def fits(n: int) -> bool:
        return n * footprint_per_unit + required_stalls(rules, n) * a.parking_stall_sqft <= ground + 1e-6

    # Start from a generous upper bound and step down; stall rounding and the
    # guest-parking threshold make a closed-form answer error-prone.
    n = max(0, math.ceil(ground / footprint_per_unit))
    while n > 0 and not fits(n):
        n -= 1
    return n
