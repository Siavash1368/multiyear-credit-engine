"""NAIC RBC.

C-1 capital by designation or CM category, per path and year. Developed in NB09.

v0.1 bonds, pre-tax (A-06):
    base RBC_t      = sum_i factor(rating_{i,t}) x carrying value_i     (live, unmatured bonds)
    portfolio adj.  = issuer-weighted average of the tier factors (first 10 issuers 7.50, ...)
    RBC_t           = base RBC_t x portfolio adj.(number of live issuers)
Defaulted bonds are written off when they default and leave the book (no NAIC 6 holding).
Source: American Academy of Actuaries C1 Work Group letter to the NAIC LRBC (E) Working Group,
March 2021 (LRBCWG materials, 30 March 2021).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from creditengine.data.rating_agency import DEFAULT
from creditengine.simulation.results import SimulationResult


def portfolio_adjustment(n_issuers: np.ndarray | int, tiers: pd.DataFrame) -> np.ndarray:
    """Weighted-average tier factor for a portfolio with n_issuers issuers."""
    n = np.asarray(n_issuers, dtype=float)
    sizes = tiers["issuers_in_tier"].fillna(np.inf).to_numpy()
    factors = tiers["factor"].to_numpy()
    lower = np.concatenate([[0.0], np.cumsum(sizes[:-1])])  # first issuer count of each tier
    in_tier = np.clip(n[..., None] - lower, 0.0, sizes)  # issuers falling in each tier
    weighted = (in_tier * factors).sum(axis=-1)
    return np.divide(weighted, n, out=np.zeros_like(n), where=n > 0)


def base_rbc(rating: np.ndarray, exposure: np.ndarray, factor_by_state: np.ndarray) -> float:
    """Sum of factor x carrying value for one snapshot of ratings (no portfolio adjustment)."""
    return float((factor_by_state[rating] * exposure).sum())


def rbc_path(
    result: SimulationResult, factor_by_state: np.ndarray, tiers: pd.DataFrame
) -> np.ndarray:
    """Required C-1 bond capital per path at t = 0, 1, ..., horizon. Shape (paths, years + 1)."""
    n_paths, n_times, _ = result.ratings.shape
    rbc = np.zeros((n_paths, n_times))
    for t in range(n_times):
        state = result.ratings[:, t, :]
        live = (state != DEFAULT) & (result.maturity[None, :] > t)
        base = (factor_by_state[state] * result.exposure[None, :] * live).sum(axis=1)
        rbc[:, t] = base * portfolio_adjustment(live.sum(axis=1), tiers)
    return rbc


def rbc_ratio_to_exposure(rbc: np.ndarray, result: SimulationResult) -> np.ndarray:
    """RBC divided by live carrying value at each time (capital per dollar held)."""
    n_times = rbc.shape[1]
    live_value = np.stack(
        [
            ((result.ratings[:, t, :] != DEFAULT) & (result.maturity[None, :] > t))
            @ result.exposure
            for t in range(n_times)
        ],
        axis=1,
    )
    return np.divide(rbc, live_value, out=np.zeros_like(rbc), where=live_value > 0)
