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

    kind: Literal["arcgis", "file"]
    url: str
    where: str = "1=1"
    adapter: str | None = None
    publisher: str
    license: str


class Assumptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avg_unit_net_sqft: float
    net_to_gross: float
    parking_stall_sqft: float
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


class CityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    state: str
    analysis_crs: str
    sources: dict[str, Source]
    specific_plan_prefixes: dict[str, str] = {}
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
