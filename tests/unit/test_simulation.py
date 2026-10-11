"""Reproducibility with fixed seed; antithetic pairing; loss aggregation."""

import numpy as np
import pytest

from creditengine.assets.corporate import BondPortfolio
from creditengine.simulation.engine import SimulationSettings, simulate
from creditengine.simulation.results import expected_shortfall, value_at_risk


def test_same_seed_same_result(small_book, toy_matrix):
    s = SimulationSettings(horizon=3, n_paths=200, seed=1)
    a, b = simulate(small_book, toy_matrix, s), simulate(small_book, toy_matrix, s)
    assert np.array_equal(a.losses, b.losses) and np.array_equal(a.ratings, b.ratings)


def test_independent_years_reproduce_matrix_powers(small_book, toy_matrix):
    """With phi = 0 the expected cumulative default rate is P^n (V-03, engine side)."""
    s = SimulationSettings(horizon=3, n_paths=20_000, rho=0.2, phi=0.0, seed=3)
    sim = simulate(small_book, toy_matrix, s).cumulative_default_rates()
    power3 = np.linalg.matrix_power(toy_matrix, 3)[:7, 7]
    assert np.allclose(sim[3].to_numpy(), power3, rtol=0.05, atol=2e-4)


def test_losses_bounded_by_exposure(small_book, toy_matrix):
    res = simulate(small_book, toy_matrix, SimulationSettings(horizon=5, n_paths=500))
    assert np.all(res.losses >= 0)
    assert np.all(res.total_loss <= small_book.exposure.sum())


def test_matured_bonds_stop_migrating(toy_matrix):
    book = BondPortfolio(
        issuer=np.arange(50),
        rating=np.full(50, 5),
        exposure=np.ones(50),
        maturity=np.ones(50, dtype=int),
    )
    res = simulate(book, toy_matrix, SimulationSettings(horizon=4, n_paths=300))
    assert np.array_equal(res.ratings[:, 1], res.ratings[:, 4])  # frozen after year 1
    assert np.all(res.losses[:, 1:] == 0)


def test_stylised_book_matches_config():
    mix = {"A": 0.5, "BBB": 0.5}
    book = BondPortfolio.stylised(1e9, 100, mix, {"A": 8, "BBB": 8}, seed=0)
    assert book.n == 100
    assert book.exposure.sum() == pytest.approx(1e9)
    assert book.exposure[book.rating == 2].sum() == pytest.approx(5e8)


def test_var_and_es():
    losses = np.arange(1, 1001, dtype=float)
    assert value_at_risk(losses, 0.99) == pytest.approx(990.01)
    assert expected_shortfall(losses, 0.99) == pytest.approx(np.mean(np.arange(991, 1001)))


def test_issuer_losses_add_up(small_book, toy_matrix):
    res = simulate(small_book, toy_matrix, SimulationSettings(horizon=3, n_paths=400, seed=2))
    assert np.allclose(res.issuer_loss.sum(axis=1), res.total_loss)


def test_supplied_cycle_is_used(small_book, toy_matrix):
    z = np.full((300, 3), -3.0)
    bad = simulate(small_book, toy_matrix, SimulationSettings(horizon=3, n_paths=300, z=z, seed=1))
    good = simulate(
        small_book, toy_matrix, SimulationSettings(horizon=3, n_paths=300, z=-z, seed=1)
    )
    assert bad.total_loss.mean() > 5 * good.total_loss.mean()


@pytest.mark.parametrize(
    "options", [{"copula": "t", "t_nu": 5.0}, {"sector_beta": 0.5}, {"lgd_cycle": 1.0}]
)
def test_challengers_keep_one_year_default_rates(toy_matrix, options):
    """t copula and sector factors change the joint tail, not each issuer's PD."""
    rating = np.repeat(np.arange(7), 30)
    book = BondPortfolio(
        issuer=np.arange(rating.size),
        rating=rating,
        exposure=np.ones(rating.size),
        maturity=np.full(rating.size, 1),
        sector=rating % 3,
    )
    res = simulate(
        book, toy_matrix, SimulationSettings(horizon=1, n_paths=20_000, seed=4, **options)
    )
    sim = res.cumulative_default_rates()[1].to_numpy()
    assert np.allclose(sim, toy_matrix[:7, 7], rtol=0.1, atol=5e-4)
