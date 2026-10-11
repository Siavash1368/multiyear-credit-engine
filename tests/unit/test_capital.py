"""RBC per path equals a hand calculation (V-11); break-even spread components."""

import numpy as np
import pandas as pd
import pytest

from creditengine.capital.rbc import base_rbc, portfolio_adjustment, rbc_path
from creditengine.simulation.engine import SimulationSettings, simulate

TIERS = pd.DataFrame(
    {"issuers_in_tier": [10, 90, 100, 300, np.nan], "factor": [7.50, 1.75, 0.90, 0.85, 0.75]}
)


@pytest.mark.parametrize(
    "n, expected",
    [
        (10, 7.50),
        (100, (10 * 7.5 + 90 * 1.75) / 100),
        (200, (10 * 7.5 + 90 * 1.75 + 100 * 0.9) / 200),
        (1000, (10 * 7.5 + 90 * 1.75 + 100 * 0.9 + 300 * 0.85 + 500 * 0.75) / 1000),
    ],
)
def test_portfolio_adjustment_hand_values(n, expected):
    assert portfolio_adjustment(n, TIERS) == pytest.approx(expected)


def test_portfolio_adjustment_zero_issuers():
    assert portfolio_adjustment(0, TIERS) == 0.0


def test_rbc_at_start_equals_hand_calculation(small_book, toy_matrix):
    """V-11: at t = 0 every path holds the initial book."""
    factors = np.array([0.0029, 0.0055, 0.0102, 0.0163, 0.0466, 0.0832, 0.2280, 0.30])
    res = simulate(small_book, toy_matrix, SimulationSettings(horizon=2, n_paths=50))
    rbc = rbc_path(res, factors, TIERS)
    hand = base_rbc(small_book.rating, small_book.exposure, factors)
    hand *= (10 * 7.5 + 90 * 1.75 + 40 * 0.9) / 140  # 140 issuers
    assert np.allclose(rbc[:, 0], hand)


def test_defaults_and_maturities_leave_the_book(small_book, toy_matrix):
    factors = np.full(8, 0.01)
    res = simulate(small_book, toy_matrix, SimulationSettings(horizon=5, n_paths=50))
    rbc = rbc_path(res, factors, TIERS)
    assert np.all(rbc[:, 5] == 0.0)  # all bonds mature at year 5
