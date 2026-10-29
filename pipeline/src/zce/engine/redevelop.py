"""Realistic vs. theoretical capacity: which lots are likely to redevelop.

Theoretical capacity counts every home the rules allow, as if every lot were
rebuilt. Most won't be: a recent or valuable building, many owners, or a
small gain discourage rebuilding. Planners screen lots with simple rules of
thumb; a lot passing every screen is a "redevelopment candidate", and its
extra homes count toward the realistic estimate.

Two kinds of screens:
- STATIC (depend only on the lot): building age, building vs. land value,
  condo ownership, historic district. Computed once in the pipeline and sent
  to the browser as a bit mask.
- DYNAMIC (depend on the rules): does zoning allow at least N times what's
  there? Recomputed for every scenario, here and in web/src/engine/redevelop.ts.

The realistic estimate uses LOCAL capacity (the city's rules, or a reform
scenario), not the state-law ADU/SB 9 path: adding an ADU or a second house
usually keeps the existing home, so it isn't redevelopment. Those additions
are reported separately.

This is a screen, not a prediction: it doesn't say when, or how many, of the
candidates will actually be rebuilt.
"""

from dataclasses import dataclass

# Bit positions of the static screens in the mask (1 = passed).
AGE, VALUE, OWNERSHIP, HISTORIC = 1, 2, 4, 8
ALL_STATIC = AGE | VALUE | OWNERSHIP | HISTORIC
SCREEN_NAMES = {AGE: "building_too_new", VALUE: "building_worth_more_than_land",
                OWNERSHIP: "condo_many_owners", HISTORIC: "historic_district"}


@dataclass(frozen=True)
class Screens:
    as_of_year: int
    min_capacity_multiple: float
    min_net_new_units: int
    min_building_age_years: int
    max_improvement_to_land_ratio: float
    exclude_condos: bool
    exclude_overlay_prefixes: tuple[str, ...]


def static_mask(
    s: Screens,
    *,
    year_built: float | None,
    land_value: float | None,
    improvement_value: float | None,
    existing_units: float | None,
    is_condo: bool,
    overlays: tuple[str, ...],
) -> int:
    """Which static screens a lot passes, as a bit mask."""
    nan = lambda v: v is None or v != v  # noqa: E731  (NaN is the only value not equal to itself)
    vacant = (nan(existing_units) or existing_units == 0) and (nan(improvement_value) or improvement_value == 0)
    mask = 0
    if vacant or (not nan(year_built) and s.as_of_year - year_built >= s.min_building_age_years):
        mask |= AGE
    # Unknown values (mostly exempt public land) fail: we can't tell.
    if vacant or (not nan(land_value) and land_value > 0 and not nan(improvement_value)
                  and improvement_value / land_value < s.max_improvement_to_land_ratio):
        mask |= VALUE
    if not (s.exclude_condos and is_condo):
        mask |= OWNERSHIP
    if not any(o.startswith(p) for o in overlays for p in s.exclude_overlay_prefixes):
        mask |= HISTORIC
    return mask


@dataclass(frozen=True)
class Redevelopment:
    likely: bool
    realistic_new_units: int
    failed: tuple[str, ...]  # why not, in plain codes (empty if likely)


def redevelopment(
    s: Screens, mask: int, local_units: int | None, existing_units: float | None
) -> Redevelopment:
    """Is this lot a redevelopment candidate under these rules, and how many homes would it add?"""
    if local_units is None:
        return Redevelopment(False, 0, ("not_modeled",))
    existing = 0 if existing_units is None or existing_units != existing_units else int(existing_units)
    failed = [name for bit, name in SCREEN_NAMES.items() if not mask & bit]
    if local_units < s.min_capacity_multiple * max(existing, 1) or local_units - existing < s.min_net_new_units:
        failed.insert(0, "zoning_allows_too_little_more")
    if failed:
        return Redevelopment(False, 0, tuple(failed))
    return Redevelopment(True, max(0, local_units - existing), ())


def screens_from_config(cfg) -> Screens:
    """Build Screens from city.yaml's `redevelopment` section (a pydantic model)."""
    return Screens(
        as_of_year=cfg.as_of_year,
        min_capacity_multiple=cfg.min_capacity_multiple,
        min_net_new_units=cfg.min_net_new_units,
        min_building_age_years=cfg.min_building_age_years,
        max_improvement_to_land_ratio=cfg.max_improvement_to_land_ratio,
        exclude_condos=cfg.exclude_condos,
        exclude_overlay_prefixes=tuple(cfg.exclude_overlay_prefixes),
    )
