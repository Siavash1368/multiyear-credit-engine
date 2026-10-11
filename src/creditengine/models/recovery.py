"""Recovery and LGD.

Beta LGD by seniority; recovery linked to the credit cycle. Developed in NB05.

v0.1: LGD drawn from a beta distribution fitted by moments (A-04).
v0.2: optional cycle link (A-13). The mean LGD moves with the systematic factor Z:
    mean(Z) = N(a - b Z),   a = N^{-1}(mean) * sqrt(1 + b^2)
so that the average over Z ~ N(0, 1) is still the long-run mean, and b > 0 makes bad years
(low Z) lose more per default. b = 0 gives back the v0.1 model.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def beta_parameters(mean: float, std: float) -> tuple[float, float]:
    """Beta (a, b) with the given mean and standard deviation (method of moments)."""
    var = std**2
    if not 0.0 < mean < 1.0 or var >= mean * (1.0 - mean):
        raise ValueError("Need 0 < mean < 1 and std^2 < mean (1 - mean).")
    k = mean * (1.0 - mean) / var - 1.0
    return mean * k, (1.0 - mean) * k


def sample_lgd(mean: float, std: float, size: int | tuple[int, ...], rng: np.random.Generator):
    """Draw loss-given-default values in [0, 1]."""
    a, b = beta_parameters(mean, std)
    return rng.beta(a, b, size=size)


def cycle_mean_lgd(z: np.ndarray | float, mean: float, sensitivity: float) -> np.ndarray:
    """Mean LGD given the cycle: N(a - b Z) with a set so that E_Z[mean(Z)] = mean."""
    a = norm.ppf(mean) * np.sqrt(1.0 + sensitivity**2)
    return norm.cdf(a - sensitivity * np.asarray(z, dtype=float))


def sample_lgd_conditional(mean: np.ndarray, std: float, rng: np.random.Generator) -> np.ndarray:
    """Beta LGD with an element-wise mean (same shape as mean) and a common std.

    The std is capped at 90% of the largest value a beta with that mean allows.
    """
    mean = np.clip(np.asarray(mean, dtype=float), 1e-4, 1.0 - 1e-4)
    var = np.minimum(std**2, 0.81 * mean * (1.0 - mean))
    k = mean * (1.0 - mean) / var - 1.0
    return rng.beta(mean * k, (1.0 - mean) * k)
