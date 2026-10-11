"""Structured assets.

Pool loss to tranche loss; thickness; correlation sensitivity; large-pool closed form.
Developed in NB08.

The collateral pool is simulated with the same multi-year migration engine as the bonds, on the
same economy. The contract then slices the pool's cumulative loss rate L:
    tranche loss (share of tranche) = [ max(L - a, 0) - max(L - d, 0) ] / (d - a)
a = attachment (subordination below the tranche), d = detachment. Loss-allocation view: no
interest waterfall or coverage-test cash diversion yet (A-08, L-09).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import norm

from creditengine.models.cycle import conditional_pd


def tranche_loss(pool_loss: np.ndarray | float, attach: float, detach: float) -> np.ndarray:
    """Loss of a tranche as a share of its notional, for pool loss rate(s) in [0, 1]."""
    if not 0.0 <= attach < detach <= 1.0:
        raise ValueError("Need 0 <= attach < detach <= 1.")
    pool = np.asarray(pool_loss, dtype=float)
    return (np.maximum(pool - attach, 0.0) - np.maximum(pool - detach, 0.0)) / (detach - attach)


@dataclass
class Tranche:
    name: str
    attach: float
    detach: float
    designation: str  # NAIC designation used for capital (e.g. "1.A")

    @property
    def thickness(self) -> float:
        return self.detach - self.attach


def capital_structure(tranches: list[Tranche]) -> None:
    """Check tranches tile [0, 1] without gaps or overlaps (validation V-10)."""
    ordered = sorted(tranches, key=lambda t: t.attach)
    if ordered[0].attach != 0.0 or not np.isclose(ordered[-1].detach, 1.0):
        raise ValueError("Tranches must start at 0 and end at 1.")
    for lo, hi in zip(ordered[:-1], ordered[1:], strict=True):
        if not np.isclose(lo.detach, hi.attach):
            raise ValueError(f"Gap or overlap between {lo.name} and {hi.name}.")


def tranche_table(pool_loss: np.ndarray, tranches: list[Tranche], q: float = 0.995) -> pd.DataFrame:
    """Per tranche: expected loss, probability of any loss, tail loss (share of notional)."""
    rows = {}
    for tr in tranches:
        loss = tranche_loss(pool_loss, tr.attach, tr.detach)
        tail = loss[pool_loss >= np.quantile(pool_loss, q)]
        rows[tr.name] = {
            "attach": tr.attach,
            "detach": tr.detach,
            "thickness": tr.thickness,
            "EL": loss.mean(),
            "P(loss>0)": (loss > 0).mean(),
            f"ES {q:.1%}": tail.mean(),
        }
    return pd.DataFrame(rows).T


def large_pool_tranche_el(
    pd_: float, rho: float, lgd: float, attach: float, detach: float, n_grid: int = 4001
) -> float:
    """Expected tranche loss for an infinitely granular one-period pool (closed-form check).

    Pool loss rate given Z is lgd * PD(Z); integrate the tranche payoff over Z ~ N(0, 1).
    """
    z = np.linspace(-8.0, 8.0, n_grid)
    w = norm.pdf(z)
    w /= w.sum()
    pool = lgd * conditional_pd(pd_, rho, z)
    return float((tranche_loss(pool, attach, detach) * w).sum())


def correlation_sensitivity(
    pd_: float, lgd: float, tranches: list[Tranche], rhos: tuple[float, ...]
) -> pd.DataFrame:
    """Large-pool expected tranche loss for several asset correlations (pool EL is constant)."""
    data = {
        f"rho={r:.0%}": {
            "pool EL": pd_ * lgd,
            **{t.name: large_pool_tranche_el(pd_, r, lgd, t.attach, t.detach) for t in tranches},
        }
        for r in rhos
    }
    return pd.DataFrame(data).T
