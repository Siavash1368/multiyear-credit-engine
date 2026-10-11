"""Sampling: antithetic paths, class factors, t copula mapping, importance sampling."""

import numpy as np
import pytest
from scipy.stats import norm

from creditengine.models.cycle import simulate_factor_paths
from creditengine.simulation.sampling import (
    class_factor,
    factor_paths,
    large_pool_tail_probability,
    sobol_normals,
    t_to_gaussian,
)


def test_antithetic_pairs(rng):
    z = factor_paths(1000, 4, 0.5, rng, antithetic=True)
    assert np.allclose(z[:500], -z[500:])
    assert abs(z.mean()) < 1e-12


def test_class_factor_moments(rng):
    g = simulate_factor_paths(50_000, 3, 0.5, rng)
    zk = class_factor(g, 0.5, 0.5, rng)
    assert zk.std() == pytest.approx(1.0, abs=0.02)
    assert np.corrcoef(g[:, 0], zk[:, 0])[0, 1] == pytest.approx(np.sqrt(0.5), abs=0.02)


def test_t_mapping_keeps_order():
    x = np.linspace(-5, 5, 101)
    y = t_to_gaussian(x, 6)
    assert np.all(np.diff(y) > 0) and abs(y[50]) < 1e-12


def test_sobol_shape():
    u = sobol_normals(1024, 5, seed=1)
    assert u.shape == (1024, 5) and abs(u.mean()) < 0.02


def test_importance_sampling_unbiased_and_tighter():
    p, rho, lgd, x = 0.02, 0.2, 0.6, 0.08
    z_star = (norm.ppf(p) - np.sqrt(1 - rho) * norm.ppf(x / lgd)) / np.sqrt(rho)
    exact = norm.cdf(z_star)
    rng = np.random.default_rng(1)
    plain = large_pool_tail_probability(p, rho, lgd, x, 50_000, rng)
    shifted = large_pool_tail_probability(p, rho, lgd, x, 50_000, rng, shift=z_star)
    assert abs(shifted[0] - exact) < 3 * shifted[1]
    assert shifted[1] < plain[1] / 3
