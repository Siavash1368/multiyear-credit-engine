"""Conditional PD formula; implied factor inversion; rho and phi recovered on synthetic data.

Validation V-04.
"""

import numpy as np
import pytest

from creditengine.models.cycle import (
    basel_correlation,
    conditional_pd,
    fit_persistence,
    fit_vasicek,
    implied_factor,
    simulate_factor_paths,
)


def test_conditional_pd_averages_to_unconditional():
    # E_Z[PD(Z)] = PD, integrated with Gauss-Hermite quadrature
    x, w = np.polynomial.hermite_e.hermegauss(80)
    w = w / w.sum()
    for pd_, rho in [(0.001, 0.24), (0.03, 0.15), (0.25, 0.12)]:
        assert np.sum(w * conditional_pd(pd_, rho, x)) == pytest.approx(pd_, rel=1e-6)


def test_bad_year_raises_pd():
    assert conditional_pd(0.02, 0.2, -2.0) > 0.02 > conditional_pd(0.02, 0.2, 2.0)


def test_implied_factor_inverts_conditional_pd():
    z = np.array([-2.5, -1.0, 0.0, 1.5])
    dr = conditional_pd(0.03, 0.15, z)
    assert np.allclose(implied_factor(0.03, 0.15, dr), z)


def test_basel_correlation_bounds():
    assert basel_correlation(0.0) == pytest.approx(0.24)
    assert basel_correlation(1.0) == pytest.approx(0.12)


def test_fit_vasicek_recovers_parameters(rng):
    z = rng.standard_normal(20_000)
    dr = conditional_pd(0.03, 0.12, z)
    pd_hat, rho_hat = fit_vasicek(dr)
    assert pd_hat == pytest.approx(0.03, rel=0.02)
    assert rho_hat == pytest.approx(0.12, rel=0.03)


def test_factor_paths_are_stationary_ar1(rng):
    z = simulate_factor_paths(20_000, 6, phi=0.6, rng=rng)
    assert z.shape == (20_000, 6)
    assert z.var(axis=0) == pytest.approx(np.ones(6), abs=0.03)
    assert np.corrcoef(z[:, 2], z[:, 3])[0, 1] == pytest.approx(0.6, abs=0.02)


def test_fit_persistence_recovers_phi(rng):
    z = simulate_factor_paths(1, 20_000, phi=0.5, rng=rng).ravel()
    assert fit_persistence(z) == pytest.approx(0.5, abs=0.02)


def test_recession_start(rng):
    z = simulate_factor_paths(20_000, 3, phi=0.5, rng=rng, z0=-2.0)
    assert z[:, 0].mean() == pytest.approx(-1.0, abs=0.03)  # phi * z0
