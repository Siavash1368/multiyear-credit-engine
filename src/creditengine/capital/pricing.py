"""Pricing.

Break-even spread and capital-adjusted return. Developed in NB09.

    break-even spread  s* = EL per year + k x capital factor x cost of capital + expenses
    RAROC              = (spread - EL - expenses) / capital
An asset adds value when its spread clears s*; adding it raises the portfolio's return on capital
when its own RAROC on marginal capital is above the hurdle rate.
"""

from __future__ import annotations

import numpy as np


def annual_pd(cumulative_pd: float, years: int) -> float:
    """Average annual PD that compounds to a cumulative PD over `years`."""
    return 1.0 - (1.0 - cumulative_pd) ** (1.0 / years)


def breakeven_spread(
    annual_el: float | np.ndarray,
    capital_factor: float | np.ndarray,
    capital_multiple: float = 2.0,
    cost_of_capital: float = 0.10,
    expenses: float = 0.0,
) -> np.ndarray:
    """Spread (decimal per year) that pays for expected loss, capital and expenses (A-06)."""
    return (
        np.asarray(annual_el)
        + capital_multiple * np.asarray(capital_factor) * cost_of_capital
        + expenses
    )


def raroc(spread: float, annual_el: float, capital: float, expenses: float = 0.0) -> float:
    """Risk-adjusted return on capital, all per unit of exposure per year."""
    return (spread - annual_el - expenses) / capital
