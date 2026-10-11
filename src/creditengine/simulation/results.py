"""Simulation results.

Container for simulated losses, ratings and capital; summary statistics.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from creditengine.data.rating_agency import DEFAULT, RATINGS


def value_at_risk(losses: np.ndarray, q: float) -> float:
    """Loss quantile at confidence q (e.g. 0.995)."""
    return float(np.quantile(losses, q))


def expected_shortfall(losses: np.ndarray, q: float) -> float:
    """Mean loss in the tail at or beyond VaR_q.

    With continuous LGD there are no ties at VaR, so this equals the average of the worst
    (1 - q) share of paths up to Monte Carlo error.
    """
    var = value_at_risk(losses, q)
    return float(losses[losses >= var].mean())


@dataclass
class SimulationResult:
    losses: np.ndarray  # (paths, years), USD loss booked in each year
    ratings: np.ndarray  # (paths, years + 1, issuers), state index; column 0 = start
    z: np.ndarray  # (paths, years), systematic factor
    exposure: np.ndarray  # (issuers,)
    maturity: np.ndarray  # (issuers,)
    issuer_loss: np.ndarray | None = None  # (paths, issuers), loss over the horizon

    @property
    def total_loss(self) -> np.ndarray:
        """Cumulative loss over the full horizon, one value per path."""
        return self.losses.sum(axis=1)

    def summary(self, quantiles: tuple[float, ...] = (0.95, 0.99, 0.995)) -> pd.Series:
        """EL, standard deviation, VaR and ES of the horizon loss (USD)."""
        loss = self.total_loss
        out = {"EL": loss.mean(), "StdDev": loss.std()}
        for q in quantiles:
            out[f"VaR {q:.1%}"] = value_at_risk(loss, q)
            out[f"ES {q:.1%}"] = expected_shortfall(loss, q)
        return pd.Series(out)

    def loss_by_year(self) -> pd.DataFrame:
        """Mean and 99.5% quantile of the loss booked in each year."""
        years = np.arange(1, self.losses.shape[1] + 1)
        return pd.DataFrame(
            {"EL": self.losses.mean(axis=0), "q99.5": np.quantile(self.losses, 0.995, axis=0)},
            index=pd.Index(years, name="year"),
        )

    def cumulative_default_rates(self, ignore_maturity: bool = True) -> pd.DataFrame:
        """Simulated cumulative default rate by initial rating and year (issuer-weighted).

        Compare with S&P Table 24. With ignore_maturity=True only issuers whose bond is still
        outstanding at the horizon count, so maturity does not censor the default rate.
        """
        start = self.ratings[0, 0]
        horizon = self.losses.shape[1]
        keep = self.maturity >= horizon if ignore_maturity else np.ones_like(start, dtype=bool)
        is_default = self.ratings[:, 1:, :] == DEFAULT  # (paths, years, issuers)
        rows = {}
        for r, name in enumerate(RATINGS):
            cols = keep & (start == r)
            if cols.any():
                rows[name] = is_default[:, :, cols].mean(axis=(0, 2))
        return pd.DataFrame(rows, index=pd.Index(range(1, horizon + 1), name="year")).T
