"""NAIC factors.

Bond designation factors, CM1-CM7 categories and CLO factors.

v0.1 covers bonds only: Academy C1 Work Group pre-tax base factors (March 2021 update),
the companion portfolio adjustment, and the S&P letter -> NAIC designation map (A-06).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from creditengine.utils.paths import external_file

FACTOR_CAP = 0.30  # Academy recommends capping the base factor at 30%


def load_bond_factors(path: str | Path | None = None) -> pd.Series:
    """Pre-tax base factor (decimal) indexed by NAIC designation (1.A ... 6), capped at 30%."""
    path = path or external_file("naic_bond_factors.csv")
    table = pd.read_csv(path, dtype={"naic_designation": str})
    factors = table.set_index("naic_designation")["factor_pct"] / 100.0
    return factors.clip(upper=FACTOR_CAP)


def load_portfolio_adjustment(path: str | Path | None = None) -> pd.DataFrame:
    """Issuer-count tiers and factors. Last tier has no upper bound (issuers_in_tier is NaN)."""
    path = path or external_file("naic_portfolio_adjustment.csv")
    return pd.read_csv(path)


def load_rating_map(path: str | Path | None = None) -> pd.DataFrame:
    """S&P letter category -> representative Moody's notch and NAIC designation."""
    path = path or external_file("rating_scale_map.csv")
    return pd.read_csv(path, dtype=str).set_index("sp_category")


def factor_by_rating(
    factors: pd.Series | None = None, rating_map: pd.DataFrame | None = None
) -> pd.Series:
    """RBC base factor for each engine state (AAA ... CCC/C, D)."""
    factors = load_bond_factors() if factors is None else factors
    rating_map = load_rating_map() if rating_map is None else rating_map
    return rating_map["naic_designation"].map(factors)
