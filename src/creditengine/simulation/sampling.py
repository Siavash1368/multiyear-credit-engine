"""Sampling.

Factor draws for the Monte Carlo engine and variance reduction. Developed in NB06.

    * AR(1) factor paths, optionally antithetic (Z, -Z) pairs
    * asset-class factors that share a global cycle:  Z_k = sqrt(beta) G + sqrt(1 - beta) H_k
    * Student-t copula scale  W = nu / chi2_nu  (one common "panic" multiplier per path and year)
    * Sobol (quasi-random) standard normals
    * importance sampling for a one-period large-pool tail, with likelihood-ratio weights
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm, qmc
from scipy.stats import t as student_t

from creditengine.models.cycle import conditional_pd, simulate_factor_paths


def factor_paths(
    n_paths: int,
    n_years: int,
    phi: float,
    rng: np.random.Generator,
    z0: float | None = None,
    antithetic: bool = False,
) -> np.ndarray:
    """AR(1) factor paths, shape (n_paths, n_years). Antithetic: second half is minus the first.

    Mirroring is exact for a zero-mean Gaussian AR(1) started from a symmetric state, so each
    pair (Z, -Z) is two equally likely economies. Not used with a fixed non-zero start z0.
    """
    if not antithetic:
        return simulate_factor_paths(n_paths, n_years, phi, rng, z0)
    if z0 not in (None, 0.0):
        raise ValueError("Antithetic paths need a symmetric start (z0 None or 0).")
    half = simulate_factor_paths((n_paths + 1) // 2, n_years, phi, rng, z0)
    return np.vstack([half, -half])[:n_paths]


def class_factor(
    global_paths: np.ndarray, beta: float, phi: float, rng: np.random.Generator
) -> np.ndarray:
    """Factor for an asset class or sector that is partly the global cycle and partly its own.

    Z_k = sqrt(beta) G + sqrt(1 - beta) H_k, with H_k an independent AR(1) of the same
    persistence, so Z_k is again a stationary N(0, 1) AR(1) and Corr(Z_k, G) = sqrt(beta).
    """
    if beta >= 1.0:
        return global_paths
    own = simulate_factor_paths(global_paths.shape[0], global_paths.shape[1], phi, rng)
    return np.sqrt(beta) * global_paths + np.sqrt(1.0 - beta) * own


def t_scale(shape: tuple[int, ...], nu: float, rng: np.random.Generator) -> np.ndarray:
    """Common scale sqrt(W), W = nu / chi2_nu, one draw per path and year (Student-t copula)."""
    return np.sqrt(nu / rng.chisquare(nu, size=shape))


def t_to_gaussian(x: np.ndarray, nu: float) -> np.ndarray:
    """Map Student-t(nu) variables to standard normals with the same rank (same copula).

    Lets the Gaussian rating thresholds be reused: Phi^{-1}(t_nu(x)).
    """
    u = np.clip(student_t.cdf(x, nu), 1e-15, 1.0 - 1e-15)
    return norm.ppf(u)


def sobol_normals(n: int, d: int, seed: int = 0) -> np.ndarray:
    """n x d quasi-random standard normals (scrambled Sobol). n should be a power of 2."""
    u = qmc.Sobol(d=d, scramble=True, seed=seed).random(n)
    return norm.ppf(np.clip(u, 1e-12, 1.0 - 1e-12))


def large_pool_tail_probability(
    pd: float,
    rho: float,
    lgd: float,
    threshold: float,
    n_sims: int,
    rng: np.random.Generator,
    shift: float = 0.0,
) -> tuple[float, float]:
    """P(loss rate > threshold) in the large-pool model, with optional importance sampling.

    Draw Z ~ N(shift, 1) instead of N(0, 1) and weight each draw by the likelihood ratio
        w(Z) = exp(-shift * Z + shift^2 / 2).
    A negative shift sends more draws into bad years. Returns (estimate, standard error).
    """
    z = rng.standard_normal(n_sims) + shift
    weight = np.exp(-shift * z + 0.5 * shift**2)
    hit = (lgd * conditional_pd(pd, rho, z) > threshold).astype(float)
    sample = hit * weight
    return float(sample.mean()), float(sample.std(ddof=1) / np.sqrt(n_sims))
