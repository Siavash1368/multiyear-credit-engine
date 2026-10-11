"""Structured: tranche algebra, conservation (V-10), large-pool closed form, correlation effect."""

import numpy as np
import pytest

from creditengine.assets.structured import (
    Tranche,
    capital_structure,
    correlation_sensitivity,
    large_pool_tranche_el,
    tranche_loss,
)
from creditengine.validation.closed_form import simulate_default_fraction

STACK = [
    Tranche("equity", 0.0, 0.03, "6"),
    Tranche("mezz", 0.03, 0.07, "2.B"),
    Tranche("senior", 0.07, 0.15, "1.F"),
    Tranche("super", 0.15, 1.0, "1.A"),
]


def test_tranche_boundaries():
    assert tranche_loss(0.03, 0.03, 0.07) == 0.0
    assert tranche_loss(0.07, 0.03, 0.07) == pytest.approx(1.0)
    assert tranche_loss(0.05, 0.03, 0.07) == pytest.approx(0.5)


def test_conservation():
    """Tranche losses in dollars add back to the pool loss (V-10)."""
    pool = np.random.default_rng(0).uniform(0, 0.4, 1000)
    total = sum(t.thickness * tranche_loss(pool, t.attach, t.detach) for t in STACK)
    assert np.allclose(total, pool)


def test_capital_structure_checks():
    capital_structure(STACK)
    with pytest.raises(ValueError):
        capital_structure(STACK[:2])


def test_closed_form_matches_large_simulated_pool():
    frac = simulate_default_fraction(0.02, 0.2, 10_000, 100_000, seed=3)
    for t in STACK[:3]:
        sim = tranche_loss(0.6 * frac, t.attach, t.detach).mean()
        assert sim == pytest.approx(
            large_pool_tranche_el(0.02, 0.2, 0.6, t.attach, t.detach), rel=0.05, abs=2e-4
        )


def test_correlation_moves_risk_from_equity_to_senior():
    table = correlation_sensitivity(0.02, 0.6, STACK, (0.05, 0.2, 0.4))
    assert np.allclose(table["pool EL"], 0.012)
    assert table["equity"].is_monotonic_decreasing
    assert table["senior"].is_monotonic_increasing
    # expected losses still add up to the pool's expected loss
    el = sum(t.thickness * table[t.name] for t in STACK)
    assert np.allclose(el, 0.012, atol=1e-6)
