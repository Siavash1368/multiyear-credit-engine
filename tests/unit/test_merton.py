"""Asset value and volatility solver converges; DD and PD match hand-worked examples."""

import numpy as np
import pytest

from creditengine.models.merton import (
    default_probability,
    distance_to_default,
    equity_from_assets,
    kmv_default_point,
    solve_assets,
)


def test_distance_to_default_hand_example():
    # V = 100, D = 80, mu = 5%, sigma_V = 20%, T = 1:
    # DD = (ln 1.25 + 0.05 - 0.02) / 0.20 = 1.2657
    assert distance_to_default(100, 80, 0.05, 0.20, 1.0) == pytest.approx(1.2657, abs=1e-4)
    assert default_probability(100, 80, 0.05, 0.20, 1.0) == pytest.approx(0.1028, abs=1e-4)


def test_solver_round_trip():
    v_true, s_true, d, r = 120.0, 0.25, 90.0, 0.04
    equity, sigma_e = equity_from_assets(v_true, s_true, d, r, 1.0)
    v, s = solve_assets(equity, sigma_e, d, r, 1.0)
    assert v == pytest.approx(v_true, rel=1e-6)
    assert s == pytest.approx(s_true, rel=1e-6)


def test_pd_falls_as_leverage_falls():
    pds = [default_probability(100, d, 0.05, 0.2) for d in (90, 70, 50)]
    assert np.all(np.diff(pds) < 0)


def test_kmv_default_point():
    assert kmv_default_point(30, 40) == 50
