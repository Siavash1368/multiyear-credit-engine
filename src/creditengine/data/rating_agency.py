"""Rating-agency tables.

Transition matrices, annual default rates and cumulative default rates entered in data/external/.

Rating scale used everywhere in the engine (index -> state):
    0 AAA, 1 AA, 2 A, 3 BBB, 4 BB, 5 B, 6 CCC/C, 7 D (absorbing)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from creditengine.utils.paths import external_file

RATINGS = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC/C"]
STATES = RATINGS + ["D"]
DEFAULT = len(STATES) - 1  # index of the default state


def rating_index(ratings: list[str] | np.ndarray) -> np.ndarray:
    """Map rating labels to state indices (e.g. "BBB" -> 3)."""
    lookup = {r: i for i, r in enumerate(STATES)}
    return np.array([lookup[r] for r in ratings], dtype=np.int64)


def nr_adjust(raw: pd.DataFrame) -> pd.DataFrame:
    """Remove the NR (withdrawn) column by spreading it pro rata over the other columns.

    Standard treatment (assumption A-01): a withdrawn rating carries no information,
    so each row is rescaled to sum to one without NR.
    """
    no_nr = raw.drop(columns="NR")
    return no_nr.div(no_nr.sum(axis=1), axis=0)


def load_transition_matrix(path: str | Path | None = None) -> pd.DataFrame:
    """One-year matrix as an 8x8 DataFrame (AAA..CCC/C, D), rows sum to one, D absorbing.

    Input CSV is in percent with columns AAA..CCC/C, D, NR (S&P 2025 study, Table 21).
    """
    path = path or external_file("transition_matrix_1y.csv")
    raw = pd.read_csv(path, index_col=0) / 100.0
    matrix = nr_adjust(raw)
    matrix.loc["D"] = 0.0
    matrix.loc["D", "D"] = 1.0
    return matrix.loc[STATES, STATES]


def load_cumulative_default_rates(path: str | Path | None = None) -> pd.DataFrame:
    """Average cumulative default rates (decimal), rows = rating, columns = years 1..15."""
    path = path or external_file("cumulative_default_rates.csv")
    table = pd.read_csv(path, index_col=0) / 100.0
    table.columns = table.columns.astype(int)
    return table.loc[RATINGS]


def load_annual_default_rates(path: str | Path | None = None) -> pd.DataFrame:
    """Annual default rates (decimal), rows = year, columns = rating categories and SG."""
    path = path or external_file("default_rates_annual.csv")
    return pd.read_csv(path, index_col="year") / 100.0
