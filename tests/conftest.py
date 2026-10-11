"""Shared pytest fixtures: small synthetic portfolios, a toy transition matrix, fixed seeds."""

from __future__ import annotations

import numpy as np
import pytest

from creditengine.assets.corporate import BondPortfolio


@pytest.fixture
def toy_matrix() -> np.ndarray:
    """Synthetic 8-state matrix (AAA ... CCC/C, D): rows sum to one, D absorbing.

    Shaped like a real rating matrix but made up, so tests run without licensed data.
    """
    pd_1y = np.array([0.0002, 0.0005, 0.001, 0.003, 0.01, 0.04, 0.25])
    k = len(pd_1y)
    m = np.zeros((k + 1, k + 1))
    for i in range(k):
        m[i, k] = pd_1y[i]
        up, down = (0.04 if i > 0 else 0.0), (0.06 if i < k - 1 else 0.0)
        if i > 0:
            m[i, i - 1] = up
        if i < k - 1:
            m[i, i + 1] = down
        m[i, i] = 1.0 - up - down - pd_1y[i]
    m[k, k] = 1.0
    return m


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(12345)


@pytest.fixture
def small_book() -> BondPortfolio:
    """20 issuers per rating, unit exposure, all bonds outlive a 5-year horizon."""
    rating = np.repeat(np.arange(7), 20)
    return BondPortfolio(
        issuer=np.arange(rating.size),
        rating=rating,
        exposure=np.ones(rating.size),
        maturity=np.full(rating.size, 5),
    )
