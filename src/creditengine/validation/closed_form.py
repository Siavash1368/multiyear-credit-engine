"""Closed-form checks.

Vasicek large-portfolio distribution vs simulation.

For a homogeneous, infinitely granular portfolio (one PD p, one rho) the default fraction X has
    P(X <= x) = N( (sqrt(1 - rho) N^{-1}(x) - N^{-1}(p)) / sqrt(rho) )
    q-quantile = N( (N^{-1}(p) + sqrt(rho) N^{-1}(q)) / sqrt(1 - rho) )
Reference: Vasicek (2002); Bluhm, Overbeck and Wagner (2010), Section 2.5.1.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from creditengine.models.cycle import conditional_pd


def vasicek_cdf(x: np.ndarray | float, p: float, rho: float) -> np.ndarray:
    """P(default fraction <= x)."""
    return norm.cdf((np.sqrt(1.0 - rho) * norm.ppf(x) - norm.ppf(p)) / np.sqrt(rho))


def vasicek_quantile(q: np.ndarray | float, p: float, rho: float) -> np.ndarray:
    """Default fraction at confidence q; equals conditional_pd at Z = N^{-1}(1 - q)."""
    return norm.cdf((norm.ppf(p) + np.sqrt(rho) * norm.ppf(q)) / np.sqrt(1.0 - rho))


def simulate_default_fraction(
    p: float, rho: float, n_obligors: int, n_sims: int, seed: int = 0
) -> np.ndarray:
    """One-period default fraction of a finite homogeneous portfolio (binomial given Z)."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n_sims)
    return rng.binomial(n_obligors, conditional_pd(p, rho, z)) / n_obligors


def vasicek_check(
    p: float,
    rho: float,
    n_obligors: int = 10_000,
    n_sims: int = 200_000,
    quantiles: tuple[float, ...] = (0.5, 0.9, 0.99, 0.995, 0.999),
    seed: int = 0,
) -> pd.DataFrame:
    """Simulated vs closed-form quantiles of the default fraction (validation V-01)."""
    sims = simulate_default_fraction(p, rho, n_obligors, n_sims, seed)
    table = pd.DataFrame(
        {
            "simulated": np.quantile(sims, quantiles),
            "closed_form": vasicek_quantile(np.array(quantiles), p, rho),
        },
        index=pd.Index(quantiles, name="q"),
    )
    table["rel_error"] = table["simulated"] / table["closed_form"] - 1.0
    return table


def compare_cumulative_pd(simulated: pd.DataFrame, published: pd.DataFrame) -> pd.DataFrame:
    """Long table of simulated vs published cumulative default rates and their difference."""
    years = [c for c in simulated.columns if c in published.columns]
    rows = simulated.index.intersection(published.index)
    sim = simulated.loc[rows, years].stack().rename("simulated")
    pub = published.loc[rows, years].stack().rename("published")
    out = pd.concat([sim, pub], axis=1)
    out["difference"] = out["simulated"] - out["published"]
    out.index.names = ["rating", "year"]
    return out
