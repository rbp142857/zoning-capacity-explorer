"""Pydantic schema for zoning rule files (cities/<city>/rules/*.yaml).

Design goals:
- Every number carries a citation. A value is written as
      max_units_per_lot: {value: 1, source: T2-3}
  where "T2-3" is a key in the file's `sources:` list, which in turn holds
  the code section and URL. Validation fails if a citation key is unknown.
- Ambiguity is written down, not hidden. Any value can carry an
  `assumption:` explaining a judgment call we made reading the code.
- Rules are DATA, not code, so the same files can be read by the browser
  (milestone 5) and by people who don't read Python.

The engine (zce.engine) only reads these objects; it never touches YAML or GIS.
"""

import math
from pathlib import Path
from typing import Generic, Literal, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

T = TypeVar("T")


class Strict(BaseModel):
    # Unknown keys are errors, so a typo like "max_unit_per_lot" fails loudly.
    model_config = ConfigDict(extra="forbid", frozen=True)


class Citation(Strict):
    section: str  # e.g. "PMC §17.22.040, Table 2-3"
    url: str


class Sourced(Strict, Generic[T]):
    """A rule value plus where it came from."""

    value: T
    source: str  # a key into the rule file's `sources`
    assumption: str | None = None  # how we resolved any ambiguity


class Band(Strict):
    """One row of a lookup table keyed on lot area or lot width.

    A band applies when the key is < `below` (the last band has no `below`
    and catches everything else). Bands must be listed in increasing order.
    The band's result is:  share x lot_area + plus_sqft + plus_sqft_per_unit x units,
    but never less than at_least_sqft. `value` is used for plain lookups
    (height, stories, units) where there is no "share of lot".
    """

    below: float | None = None
    value: float | None = None  # None means "no limit" for this band
    share: float | None = None
    plus_sqft: float = 0
    plus_sqft_per_unit: float = 0
    at_least_sqft: float = 0


class Banded(Strict):
    # dist_single_family_ft: distance to the nearest lot in a single-family
    # zone (Burbank: lower height limits near single-family neighborhoods).
    by: Literal["lot_area_sqft", "lot_width_ft", "dist_single_family_ft"]
    bands: list[Band]

    @model_validator(mode="after")
    def _ordered(self):
        bounds = [b.below for b in self.bands]
        if bounds[-1] is not None:
            raise ValueError("the last band must have no `below` (it catches the rest)")
        if any(b is None for b in bounds[:-1]) or bounds[:-1] != sorted(bounds[:-1]):
            raise ValueError("bands must be in increasing order of `below`")
        return self

    def pick(self, lot_area_sqft: float, lot_width_ft: float, dist_single_family_ft: float | None = None) -> Band:
        if self.by == "dist_single_family_ft":
            # Unknown distance = no single-family zone in the city: "far".
            key = math.inf if dist_single_family_ft is None else dist_single_family_ft
        else:
            key = lot_area_sqft if self.by == "lot_area_sqft" else lot_width_ft
        for band in self.bands:
            if band.below is None or key < band.below:
                return band
        raise AssertionError("unreachable: last band has no upper bound")


class SideSetback(Strict):
    """Side setback as a share of lot width, clamped to [min_ft, max_ft]."""

    pct_of_width: float
    min_ft: float
    max_ft: float


class Setbacks(Strict):
    front_ft: Sourced[float]
    side_ft: Sourced[float | SideSetback]  # each side
    rear_ft: Sourced[float]


HousingType = Literal["single_family", "two_unit", "multifamily", "mixed_use"]
Rounding = Literal["floor", "up_above_0_75", "nearest_half_up", "up"]


class ZoneRules(Strict):
    zone: str  # must match base_zone in the parcel data, e.g. "RS-6"
    name: str
    family: Literal["single_family", "multifamily", "commercial", "nonresidential"]
    sources: dict[str, Citation]

    residential_allowed: Sourced[bool]
    housing_types: Sourced[list[HousingType]]

    # Lot size: applies to NEW lots (subdivision). Existing smaller lots can
    # still be built on, so the engine flags them but does not zero them out.
    min_lot_area_sqft: Sourced[float] | None = None
    min_lot_width_ft: Sourced[float] | None = None

    # Density: any of these may be set; the engine applies all that are.
    max_units_per_lot: Sourced[int] | None = None
    # A number, or a table by lot width/area (e.g. Glendale: less land per
    # home on lots 90 ft or wider).
    lot_area_per_unit_sqft: Sourced[float | Banded] | None = None
    units_per_acre: Sourced[float] | None = None
    small_lot_units: Sourced[Banded] | None = None  # table of units by lot area
    small_lot_units_below_sqft: float | None = None  # lots under this use the table
    density_rounding: Sourced[Rounding] | None = None

    # Building envelope
    setbacks: Setbacks
    max_height_ft: Sourced[float | Banded] | None = None
    max_stories: Sourced[float | Banded]
    lot_coverage: Sourced[float | Banded] | None = None  # share of lot, or banded rule
    max_floor_area: Sourced[Banded] | None = None  # banded floor-area formula
    max_far: Sourced[float] | None = None  # floor area ratio
    min_open_space_share: Sourced[float | Banded] | None = None  # e.g. Pasadena gardens

    # Parking (spaces per unit). Guest spaces only kick in at a project size.
    parking_per_unit: Sourced[float] | None = None
    guest_parking_per_unit: Sourced[float] | None = None
    guest_parking_min_units: int | None = None

    # False where the city's code says SB 9 doesn't apply to the zone
    # (Burbank's horsekeeping zone). None/True: state law decides.
    sb9_allowed: Sourced[bool] | None = None

    simplifications: list[str] = []  # things the MVP deliberately leaves out

    @model_validator(mode="after")
    def _citations_exist(self):
        """Every `source:` key used in the file must be defined in `sources:`."""
        missing = sorted(k for k in _source_keys(self) if k not in self.sources)
        if missing:
            raise ValueError(f"{self.zone}: unknown source keys {missing}")
        return self


def _source_keys(obj) -> set[str]:
    """Collect every `source` field anywhere inside a rules object."""
    keys: set[str] = set()
    if isinstance(obj, Sourced):
        keys.add(obj.source)
    if isinstance(obj, BaseModel):
        for name in type(obj).model_fields:
            if name != "sources":
                keys |= _source_keys(getattr(obj, name))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            keys |= _source_keys(item)
    return keys


# --- State law ---------------------------------------------------------------


class StateLaw(Strict):
    id: str  # e.g. "sb9"
    name: str
    status: Literal["modeled", "not_modeled"]
    summary: str
    citation: Citation
    assumptions: list[str] = []
    params: dict[str, float | int | str | list[str]] = {}


class StateOverrides(Strict):
    state: str
    as_of: str  # date the summaries were last checked
    laws: list[StateLaw]

    def get(self, law_id: str) -> StateLaw | None:
        return next((law for law in self.laws if law.id == law_id and law.status == "modeled"), None)


# --- Loading -----------------------------------------------------------------


def load_zone_rules(rules_dir: Path) -> dict[str, ZoneRules]:
    rules = {}
    for path in sorted(rules_dir.glob("*.yaml")):
        zone = ZoneRules.model_validate(yaml.safe_load(path.read_text()))
        if zone.zone in rules:
            raise ValueError(f"zone {zone.zone} defined twice (second time in {path.name})")
        rules[zone.zone] = zone
    return rules


def load_state_overrides(path: Path) -> StateOverrides:
    return StateOverrides.model_validate(yaml.safe_load(path.read_text()))
