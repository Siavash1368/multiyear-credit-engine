"""Backtest.

Correlated (Vasicek) vs independent (binomial) bands for annual default rates. Developed in NB10.

Independent band:  DR in p +/- z sqrt(p (1 - p) / n)      (ignores the shared economy)
Correlated band :  DR in [q_lo, q_hi] of the Vasicek distribution with (p, rho)
Walk-forward test: fit (p, rho) on years before t only, then check whether DR_t falls in the
correlated band; a calibrated model misses about (1 - coverage) of years.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from creditengine.models.cycle import fit_vasicek
from creditengine.validation.closed_form import vasicek_quantile


def binomial_band(p: float, n: int, coverage: float = 0.95) -> tuple[float, float]:
    """Normal-approximation band for the default rate of n independent obligors."""
    half = norm.ppf(0.5 + coverage / 2) * np.sqrt(p * (1 - p) / n)
    return max(p - half, 0.0), p + half


def vasicek_band(p: float, rho: float, coverage: float = 0.95) -> tuple[float, float]:
    """Band for the default rate of a large portfolio that shares one economy."""
    lo, hi = (1 - coverage) / 2, 1 - (1 - coverage) / 2
    return float(vasicek_quantile(lo, p, rho)), float(vasicek_quantile(hi, p, rho))


def walk_forward(
    default_rates: pd.Series, first_test_year: int, coverage: float = 0.95, min_years: int = 10
) -> pd.DataFrame:
    """Out-of-sample check of the correlated band, one year at a time.

    For each test year t >= first_test_year: fit (p, rho) by maximum likelihood on the non-zero
    rates of earlier years, build the band, and record whether DR_t lies inside it.
    """
    rows = []
    for year in default_rates.index[default_rates.index >= first_test_year]:
        history = default_rates.loc[default_rates.index < year]
        history = history[history > 0]
        if len(history) < min_years:
            continue
        p, rho = fit_vasicek(history.to_numpy())
        lo, hi = vasicek_band(p, rho, coverage)
        dr = default_rates.loc[year]
        rows.append(
            {
                "year": year,
                "default_rate": dr,
                "p": p,
                "rho": rho,
                "lo": lo,
                "hi": hi,
                "inside": lo <= dr <= hi,
            }
        )
    return pd.DataFrame(rows).set_index("year")
