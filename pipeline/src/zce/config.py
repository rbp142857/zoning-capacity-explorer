"""Load and validate a city's city.yaml.

We use Pydantic models so a typo in city.yaml (a missing URL, a misspelled key)
fails loudly at startup instead of halfway through a download.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict

# Repository root = two levels above this package's src/ folder.
REPO_ROOT = Path(__file__).resolve().parents[3]
CITIES_DIR = REPO_ROOT / "cities"
# git-ignored; the pipeline recreates it. The ".nosync" suffix tells iCloud
# Drive not to sync it (raw downloads are 100+ MB), which matters because this
# repo lives on an iCloud-synced Desktop.
DATA_DIR = REPO_ROOT / "data.nosync"


class Source(BaseModel):
    # extra="forbid" turns unknown keys into errors, which catches typos.
    model_config = ConfigDict(extra="forbid")

    kind: Literal["arcgis", "file", "ckan", "manual"]
    url: str
    where: str = "1=1"
    # For kind "ckan" (data.ca.gov datastore): which table, and row filters.
    resource_id: str | None = None
    filters: dict[str, str] = {}
    # Validation-only sources aren't needed to build the map.
    validation_only: bool = False
    # For kind "arcgis": False downloads attributes only (no shapes), saved
    # as <name>.json. Used for SCAG's zoning table, which we join by parcel
    # number rather than by shape.
    geometry: bool = True
    # For area layers (districts, specific plans): the field holding the name.
    name_field: str | None = None
    # For kind "manual": the file name to save the download as. Used for
    # servers that refuse automated downloads; a person downloads the file
    # in a browser and saves it into data.nosync/raw/<city>/.
    filename: str | None = None
    adapter: str | None = None
    publisher: str
    license: str


class Assumptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avg_unit_net_sqft: float
    net_to_gross: float
    parking_stall_sqft: float
    # The smallest house we count: a lot whose building-size limits allow at
    # least this much floor area can hold one home, even if that's less than
    # the average new unit above.
    min_home_sqft: float
    parking_mode: Literal["surface"]
    state_law_path: str

    @property
    def gross_sqft_per_unit(self) -> float:
        """Building floor area one unit uses, including its share of hallways."""
        return self.avg_unit_net_sqft / self.net_to_gross


class RedevelopmentScreens(BaseModel):
    model_config = ConfigDict(extra="forbid")

    as_of_year: int
    min_capacity_multiple: float
    min_net_new_units: int
    min_building_age_years: int
    max_improvement_to_land_ratio: float
    exclude_condos: bool
    exclude_overlay_prefixes: list[str]
    exclude_single_family_zones: bool


class MapView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    center: tuple[float, float]  # [longitude, latitude]
    zoom: float


class CityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    state: str
    analysis_crs: str
    sources: dict[str, Source]
    specific_plan_prefixes: dict[str, str] = {}
    # Zone codes as spelled in the zoning data -> as spelled in the code and
    # the rule files (e.g. SCAG writes "R2250" for Glendale's "R-2250").
    zone_aliases: dict[str, str] = {}
    # Name of this city in other agencies' data (DOF E-5, HCD reports).
    official_name: str
    map: MapView
    assumptions: Assumptions
    redevelopment: RedevelopmentScreens

    @property
    def rules_dir(self) -> Path:
        return CITIES_DIR / self.id / "rules"

    @property
    def state_law_file(self) -> Path:
        return REPO_ROOT / self.assumptions.state_law_path

    @property
    def raw_dir(self) -> Path:
        return DATA_DIR / "raw" / self.id

    @property
    def clean_dir(self) -> Path:
        return DATA_DIR / "clean" / self.id


def load_city(city_id: str) -> CityConfig:
    path = CITIES_DIR / city_id / "city.yaml"
    with open(path) as f:
        return CityConfig.model_validate(yaml.safe_load(f))
