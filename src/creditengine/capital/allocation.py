"""Capital allocation.

Who causes the risk: contributions that add up to the portfolio total. Developed in NB09.

Euler principle: RC_i = w_i dR/dw_i, and sum_i RC_i = R for a risk measure R that scales with
exposure. For expected shortfall at level q, estimated from simulated paths,
    RC_i = E[L_i | L >= VaR_q] - E[L_i]          (contribution to EC = ES - EL)
For the standard deviation (benchmark),
    RC_i = Cov(L_i, L) / sigma_L                   (contribution to sigma_L)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def es_contributions(asset_loss: np.ndarray, q: float = 0.995) -> np.ndarray:
    """Expected-shortfall capital contribution of each asset; sums to ES_q - EL.

    asset_loss has shape (paths, assets); the portfolio loss is its row sum.
    """
    total = asset_loss.sum(axis=1)
    tail = total >= np.quantile(total, q)
    return asset_loss[tail].mean(axis=0) - asset_loss.mean(axis=0)


def sd_contributions(asset_loss: np.ndarray) -> np.ndarray:
    """Standard-deviation contribution of each asset; sums to the portfolio standard deviation."""
    total = asset_loss.sum(axis=1)
    centred = asset_loss - asset_loss.mean(axis=0)
    cov = centred.T @ (total - total.mean()) / len(total)
    return cov / total.std()


def contribution_table(
    asset_loss: np.ndarray,
    exposure: np.ndarray,
    groups: np.ndarray | pd.Series,
    q: float = 0.995,
) -> pd.DataFrame:
    """Exposure, EL, variance and ES-capital shares by group (asset class, rating, sector).

    Shares are in percent; 'EC per 100' is ES capital per 100 of exposure in the group.
    """
    frame = pd.DataFrame(
        {
            "group": np.asarray(groups),
            "exposure": exposure,
            "EL": asset_loss.mean(axis=0),
            "sd_rc": sd_contributions(asset_loss),
            "es_rc": es_contributions(asset_loss, q),
        }
    )
    g = frame.groupby("group", sort=False).sum()
    out = pd.DataFrame(
        {
            "exposure %": 100 * g["exposure"] / g["exposure"].sum(),
            "EL %": 100 * g["EL"] / g["EL"].sum(),
            "variance %": 100 * g["sd_rc"] / g["sd_rc"].sum(),
            "ES capital %": 100 * g["es_rc"] / g["es_rc"].sum(),
            "EC per 100": 100 * g["es_rc"] / g["exposure"],
        }
    )
    return out
