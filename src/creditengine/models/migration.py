"""Rating migration.

Thresholds from matrix rows; matrix powers; generator; cycle-conditional matrices.
Developed in NB04.

CreditMetrics thresholds. For an obligor rated i, the asset return A ~ N(0, 1) is cut into
bins, worst state (D) at the bottom. With states ordered 0 = AAA ... K-1 = D:
    c_{i,j} = N^{-1}( sum_{k >= j} P[i, k] ),   c_{i,0} = +inf,   c_{i,K} = -inf
The obligor moves to state j when c_{i,j+1} < A <= c_{i,j}.
Reference: CreditMetrics Technical Document (1997); Bluhm, Overbeck and Wagner (2010), Section 6.3.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import expm, logm
from scipy.stats import norm


def thresholds(matrix: np.ndarray) -> np.ndarray:
    """Bin edges c_{i,j}, shape (K, K + 1). Row i holds +inf, c_{i,1}, ..., c_{i,K-1}, -inf."""
    matrix = np.asarray(matrix, dtype=float)
    # tail[i, j] = probability of ending in state j or worse
    tail = np.cumsum(matrix[:, ::-1], axis=1)[:, ::-1]
    edges = norm.ppf(np.clip(tail, 0.0, 1.0))
    edges[:, 0] = np.inf
    return np.hstack([edges, np.full((matrix.shape[0], 1), -np.inf)])


def migrate(state: np.ndarray, asset_return: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """New state for each obligor: the number of inner edges c_{i,1..K-1} at or above A.

    state and asset_return have the same shape; edges comes from thresholds().
    Loops over current ratings (at most K) and uses a sorted search, so memory stays small.
    """
    new_state = np.empty_like(state)
    for r in np.unique(state):
        mask = state == r
        ascending = edges[r, -2:0:-1]  # c_{r,K-1} <= ... <= c_{r,1}
        below = np.searchsorted(ascending, asset_return[mask], side="left")
        new_state[mask] = len(ascending) - below
    return new_state


def conditional_matrix(matrix: np.ndarray, rho: float, z: float) -> np.ndarray:
    """Transition matrix given the systematic factor Z (one-factor version of thresholds)."""
    edges = thresholds(matrix)
    cdf = norm.cdf((edges - np.sqrt(rho) * z) / np.sqrt(1.0 - rho))
    cond = cdf[:, :-1] - cdf[:, 1:]
    return cond / cond.sum(axis=1, keepdims=True)


def cumulative_default_from_matrix(matrix: np.ndarray, horizon: int) -> np.ndarray:
    """Cumulative PD by initial state for years 1..horizon: column D of P^n. Shape (K, horizon)."""
    matrix = np.asarray(matrix, dtype=float)
    out = np.empty((matrix.shape[0], horizon))
    power = np.eye(matrix.shape[0])
    for n in range(horizon):
        power = power @ matrix
        out[:, n] = power[:, -1]
    return out


def generator(matrix: np.ndarray) -> np.ndarray:
    """Continuous-time generator Q with expm(Q) ~ P.

    Principal matrix logarithm, then the Israel-Rosenthal-Wei fix: set negative
    off-diagonal rates to zero and reset the diagonal so each row sums to zero.
    """
    q = np.real(logm(np.asarray(matrix, dtype=float)))
    off = q - np.diag(np.diag(q))
    off[off < 0] = 0.0
    return off - np.diag(off.sum(axis=1))


def matrix_at(q: np.ndarray, t: float) -> np.ndarray:
    """Transition matrix over a horizon of t years from a generator: P(t) = expm(Q t)."""
    return expm(q * t)
