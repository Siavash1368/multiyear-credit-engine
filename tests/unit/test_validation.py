"""Vasicek quantile function; backtest band construction."""

import numpy as np
import pandas as pd
import pytest

from creditengine.assets.corporate import BondPortfolio
from creditengine.simulation.engine import SimulationSettings, simulate
from creditengine.validation.closed_form import (
    compare_cumulative_pd,
    vasicek_cdf,
    vasicek_check,
    vasicek_quantile,
)


def test_quantile_inverts_cdf():
    q = np.array([0.1, 0.5, 0.9, 0.995])
    x = vasicek_quantile(q, 0.02, 0.15)
    assert np.allclose(vasicek_cdf(x, 0.02, 0.15), q)


def test_binomial_simulation_matches_closed_form():
    table = vasicek_check(0.02, 0.15, n_obligors=20_000, n_sims=100_000)
    assert np.all(np.abs(table["rel_error"]) < 0.03)


@pytest.mark.slow
def test_engine_matches_vasicek(toy_matrix):
    """V-01: one year, 1,000 homogeneous issuers, engine default fraction vs closed form."""
    rating = 5
    book = BondPortfolio(
        issuer=np.arange(1000),
        rating=np.full(1000, rating),
        exposure=np.ones(1000),
        maturity=np.ones(1000, dtype=int),
    )
    s = SimulationSettings(horizon=1, n_paths=20_000, rho=0.15, phi=0.0, seed=4)
    frac = (simulate(book, toy_matrix, s).ratings[:, 1, :] == 7).mean(axis=1)
    q = np.array([0.5, 0.9, 0.99])
    closed = vasicek_quantile(q, toy_matrix[rating, 7], 0.15)
    assert np.allclose(np.quantile(frac, q), closed, rtol=0.06)


def test_compare_cumulative_pd_layout():
    sim = pd.DataFrame([[0.01, 0.02]], index=["BBB"], columns=[1, 2])
    pub = pd.DataFrame([[0.01, 0.03]], index=["BBB"], columns=[1, 2])
    out = compare_cumulative_pd(sim, pub)
    assert out.loc[("BBB", 2), "difference"] == pytest.approx(-0.01)
