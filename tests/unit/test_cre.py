"""Commercial mortgages: NAIC CM grid (V-12), amortisation, triggers, Merton balloon check."""

import numpy as np
import pytest

from creditengine.assets.cre import (
    CM_FACTORS,
    CREPortfolio,
    CRESettings,
    annual_payment,
    balance_after,
    balloon_default_probability,
    cm_category,
    simulate_cre,
)


@pytest.mark.parametrize(
    "dscr, ltv, expected",
    [
        (1.60, 0.65, 1),
        (2.50, 0.84, 1),  # CM1: DSC >= 1.50 and LTV < 85%
        (1.20, 0.50, 2),
        (1.00, 0.70, 2),  # CM2 cells
        (1.30, 0.90, 2),
        (1.60, 0.90, 2),
        (1.80, 1.10, 2),
        (0.90, 0.70, 3),
        (1.00, 0.90, 3),
        (1.60, 1.05, 3),  # CM3 cells
        (0.90, 0.95, 4),
        (1.00, 1.10, 4),  # CM4 cells
        (0.88, 1.08, 5),
        (0.50, 1.50, 5),  # CM5: DSC < 0.95 and LTV >= 105%
    ],
)
def test_cm_grid_standard(dscr, ltv, expected):
    assert cm_category(np.array([dscr]), np.array([ltv]))[0] == expected


def test_cm_grid_hotel_stricter():
    # a loan that is CM1 as an apartment is not CM1 as a hotel
    assert cm_category(np.array([1.60]), np.array([0.65]))[0] == 1
    assert cm_category(np.array([1.60]), np.array([0.65]), hotel=True)[0] > 1
    assert cm_category(np.array([1.90]), np.array([0.55]), hotel=True)[0] == 1


def test_amortisation():
    pay = annual_payment(100.0, 0.05, 25)
    assert np.isclose(balance_after(100.0, 0.05, 25, 25), 0.0, atol=1e-8)
    assert np.isclose(balance_after(100.0, 0.05, 25, 1), 100 * 1.05 - pay)


def _one_loan(value, noi, maturity=5, amort=10_000, ptype="apartment"):
    return CREPortfolio(
        loan_id=np.array(["L"]),
        property_type=np.array([ptype]),
        balance=np.array([10.0]),
        value=np.array([value]),
        noi=np.array([noi]),
        rate=np.array([0.05]),
        amort_years=np.array([amort]),
        maturity=np.array([maturity]),
    )


def test_balloon_default_matches_merton():
    """Interest-only loan, no term trigger: P(default) = P(V_T < B) = N(-DD)."""
    loan = _one_loan(value=15.4, noi=1e6)
    z = np.random.default_rng(1).standard_normal((60_000, 5))
    res = simulate_cre(loan, z, CRESettings(prepay_rate=0.0, refi_dscr_min=0.0, seed=2))
    expected = balloon_default_probability(15.4, 10.0, 0.02, 0.15, 5)
    assert abs((res.default_year > 0).mean() - expected) < 0.004


def test_double_trigger_needs_negative_equity():
    """Income below debt service alone does not default a loan with plenty of equity."""
    loan = _one_loan(value=40.0, noi=0.1, maturity=20)  # DSCR << 1 but LTV 25%
    z = np.zeros((2_000, 3))
    res = simulate_cre(loan, z, CRESettings(prepay_rate=0.0, value_vol=0.05, seed=3))
    assert res.default_rate() == 0.0


def test_losses_and_capital_consistent():
    book = CREPortfolio.stylised(1e8, 30, {"apartment": 0.5, "office": 0.5}, seed=1)
    assert np.isclose(book.balance.sum(), 1e8)
    z = np.random.default_rng(4).standard_normal((500, 5))
    res = simulate_cre(book, z, CRESettings(seed=5))
    assert np.allclose(res.losses.sum(axis=1), res.loan_loss.sum(axis=1))
    assert np.all(res.loan_loss <= book.balance[None, :] + 1e-6)
    rbc = res.rbc_path()
    assert rbc.shape == (500, 6)
    assert np.isclose(
        rbc[0, 0],
        sum(CM_FACTORS[c] * b for c, b in zip(res.category[0, 0], book.balance, strict=True)),
    )
