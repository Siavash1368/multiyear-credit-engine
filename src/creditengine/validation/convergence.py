"""Convergence.

How precise are the simulated tail numbers? Developed in NB10.

    SE(EL)        = sigma_L / sqrt(S)
    SE(VaR_q)     ~ sqrt(q (1 - q) / S) / f_L(VaR_q)      (estimated here by the bootstrap)
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from creditengine.simulation.results import expected_shortfall, value_at_risk


def bootstrap_se(
    losses: np.ndarray, q: float = 0.995, n_boot: int = 200, seed: int = 0
) -> dict[str, float]:
    """Bootstrap standard errors of EL, VaR_q and ES_q from one set of simulated losses."""
    rng = np.random.default_rng(seed)
    n = len(losses)
    stats = np.empty((n_boot, 3))
    for b in range(n_boot):
        x = losses[rng.integers(0, n, n)]
        stats[b] = x.mean(), value_at_risk(x, q), expected_shortfall(x, q)
    se = stats.std(axis=0, ddof=1)
    return {"EL": se[0], f"VaR {q:.1%}": se[1], f"ES {q:.1%}": se[2]}


def seed_study(
    run: Callable[[int, int], np.ndarray],
    path_counts: list[int],
    seeds: list[int],
    q: float = 0.995,
) -> pd.DataFrame:
    """Mean and spread across seeds of EL, VaR and ES for each number of paths.

    run(n_paths, seed) must return simulated horizon losses.
    """
    rows = []
    for n in path_counts:
        vals = np.array(
            [
                [x.mean(), value_at_risk(x, q), expected_shortfall(x, q)]
                for x in (run(n, s) for s in seeds)
            ]
        )
        rows.append(
            {
                "paths": n,
                "EL": vals[:, 0].mean(),
                "EL sd": vals[:, 0].std(ddof=1),
                "VaR": vals[:, 1].mean(),
                "VaR sd": vals[:, 1].std(ddof=1),
                "ES": vals[:, 2].mean(),
                "ES sd": vals[:, 2].std(ddof=1),
            }
        )
    return pd.DataFrame(rows).set_index("paths")
