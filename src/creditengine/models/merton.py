"""Merton structural model.

Asset value and volatility from equity; distance to default; PD. Developed in NB02.

Equity is a call on the firm's assets V with strike equal to the default point D:
    E       = V N(d1) - D e^{-rT} N(d2)
    sigma_E = (V / E) N(d1) sigma_V
Distance to default under drift mu:
    DD = [ln(V/D) + (mu - sigma_V^2 / 2) T] / (sigma_V sqrt(T)),   PD = N(-DD)
Reference: Bluhm, Overbeck and Wagner (2010), Sections 3.3-3.4.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import fsolve
from scipy.stats import norm


def distance_to_default(
    asset_value: float, default_point: float, mu: float, sigma_v: float, horizon: float = 1.0
) -> float:
    """Number of asset-volatility standard deviations between V and D at the horizon."""
    drift = (mu - 0.5 * sigma_v**2) * horizon
    return (np.log(asset_value / default_point) + drift) / (sigma_v * np.sqrt(horizon))


def default_probability(
    asset_value: float, default_point: float, mu: float, sigma_v: float, horizon: float = 1.0
) -> float:
    """Merton PD = N(-DD)."""
    return norm.cdf(-distance_to_default(asset_value, default_point, mu, sigma_v, horizon))


def equity_from_assets(
    asset_value: float, sigma_v: float, default_point: float, r: float, horizon: float = 1.0
) -> tuple[float, float]:
    """Black-Scholes equity value and equity volatility implied by (V, sigma_V)."""
    d1 = (np.log(asset_value / default_point) + (r + 0.5 * sigma_v**2) * horizon) / (
        sigma_v * np.sqrt(horizon)
    )
    d2 = d1 - sigma_v * np.sqrt(horizon)
    equity = asset_value * norm.cdf(d1) - default_point * np.exp(-r * horizon) * norm.cdf(d2)
    sigma_e = asset_value / equity * norm.cdf(d1) * sigma_v
    return equity, sigma_e


def solve_assets(
    equity: float, sigma_e: float, default_point: float, r: float, horizon: float = 1.0
) -> tuple[float, float]:
    """Back out (V, sigma_V) from observed equity value and equity volatility.

    Two equations, two unknowns; solved with scipy fsolve.
    Starting point: V = E + D, sigma_V = sigma_E * E / (E + D).
    """

    def equations(x: np.ndarray) -> list[float]:
        v, s = x
        e_model, se_model = equity_from_assets(v, s, default_point, r, horizon)
        return [e_model - equity, se_model - sigma_e]

    v0 = equity + default_point
    s0 = sigma_e * equity / v0
    v, s = fsolve(equations, x0=[v0, s0], xtol=1e-12)
    return float(v), float(s)


def kmv_default_point(short_term_debt: float, long_term_debt: float) -> float:
    """KMV convention: default point = short-term debt + half of long-term debt (A-12)."""
    return short_term_debt + 0.5 * long_term_debt
