"""Configuration.

Loading and validating YAML configuration (configs/) into typed settings objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

from creditengine.utils.paths import project_root


class SimulationConfig(BaseModel):
    horizon_years: int
    n_paths: int
    seed: int


class CycleConfig(BaseModel):
    asset_correlation: float | None = None  # used when correlation_source = "fixed"
    correlation_source: Literal["basel_formula", "fixed"] = "basel_formula"
    persistence: float
    start_state: float | None = None


class MigrationConfig(BaseModel):
    matrix_file: str
    nr_treatment: Literal["proportional"] = "proportional"


class RecoveryConfig(BaseModel):
    lgd_mean: float
    lgd_std: float


class OutputConfig(BaseModel):
    quantiles: list[float]
    report_dir: str = "reports"


class BaseConfig(BaseModel):
    simulation: SimulationConfig
    cycle: CycleConfig
    migration: MigrationConfig
    recovery: RecoveryConfig
    outputs: OutputConfig


class PortfolioConfig(BaseModel):
    name: str
    total_exposure_usd: float
    n_issuers: int
    rating_mix: dict[str, float]
    maturity_years: dict[str, int]
    seed: int = 0


def read_yaml(path: str | Path) -> dict:
    """Read a YAML file; relative paths are taken from the project root."""
    path = Path(path)
    if not path.is_absolute():
        path = project_root() / path
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_config(path: str | Path = "configs/base.yaml") -> BaseConfig:
    return BaseConfig(**read_yaml(path))


def load_portfolio_config(path: str | Path) -> PortfolioConfig:
    return PortfolioConfig(**read_yaml(path)["portfolio"])
