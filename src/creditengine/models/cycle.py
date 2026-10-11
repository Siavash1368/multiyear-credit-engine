"""Credit cycle.

One-factor conditional PD; implied factor; fit of rho and phi; AR(1) factor paths.
Developed in NB03.

Asset return of obligor i in year t (sign convention: low Z = bad year):
    A_{i,t} = sqrt(rho) Z_t + sqrt(1 - rho) eps_{i,t}
    Z_t     = phi Z_{t-1} + sqrt(1 - phi^2) eta_t          (stationary N(0, 1))
Default when A_{i,t} < c = N^{-1}(PD). Conditional on Z:
    PD(Z) = N( (N^{-1}(PD) - sqrt(rho) Z) / sqrt(1 - rho) )
Reference: Bluhm, Overbeck and Wagner (2010), Section 2.5.1; Vasicek (2002).
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def conditional_pd(pd: np.ndarray | float, rho: float, z: np.ndarray | float) -> np.ndarray:
    """Default probability given the systematic factor Z."""
    return norm.cdf((norm.ppf(pd) - np.sqrt(rho) * z) / np.sqrt(1.0 - rho))


def implied_factor(pd: float, rho: float, default_rate: np.ndarray | float) -> np.ndarray:
    """Invert conditional_pd: the Z that makes PD(Z) equal an observed default rate."""
    return (norm.ppf(pd) - np.sqrt(1.0 - rho) * norm.ppf(default_rate)) / np.sqrt(rho)


def basel_correlation(pd: np.ndarray | float) -> np.ndarray:
    """Basel II IRB corporate asset correlation: 12% (high PD) to 24% (low PD)."""
    weight = (1.0 - np.exp(-50.0 * pd)) / (1.0 - np.exp(-50.0))
    return 0.12 * weight + 0.24 * (1.0 - weight)


def fit_vasicek(default_rates: np.ndarray) -> tuple[float, float]:
    """Closed-form maximum likelihood of (PD, rho) from a series of annual default rates.

    If DR ~ Vasicek(PD, rho) then x = N^{-1}(DR) is normal with
        mean = N^{-1}(PD) / sqrt(1 - rho),  variance = rho / (1 - rho).
    So the MLE is the sample mean and variance of x. Zero rates must be removed first.
    """
    x = norm.ppf(np.asarray(default_rates, dtype=float))
    mean, var = x.mean(), x.var()
    rho = var / (1.0 + var)
    pd = norm.cdf(mean * np.sqrt(1.0 - rho))
    return float(pd), float(rho)


def fit_persistence(z: np.ndarray) -> float:
    """AR(1) coefficient phi of a factor series: lag-1 OLS slope through the origin."""
    z = np.asarray(z, dtype=float)
    return float(np.sum(z[1:] * z[:-1]) / np.sum(z[:-1] ** 2))


def simulate_factor_paths(
    n_paths: int,
    n_years: int,
    phi: float,
    rng: np.random.Generator,
    z0: float | None = None,
) -> np.ndarray:
    """AR(1) systematic factor paths, shape (n_paths, n_years).

    z0=None starts from the stationary distribution (Z_0 ~ N(0, 1));
    a number starts every path from that state (e.g. z0=-2 for a recession start).
    """
    z = np.empty((n_paths, n_years))
    z_prev = rng.standard_normal(n_paths) if z0 is None else np.full(n_paths, z0)
    for t in range(n_years):
        z[:, t] = phi * z_prev + np.sqrt(1.0 - phi**2) * rng.standard_normal(n_paths)
        z_prev = z[:, t]
    return z
