"""Attribution.

Link assumptions to outputs: which assumption drives which result. Developed in NB11.
Thin wrapper over validation.sensitivity.tornado that ranks assumptions by their effect.
"""

from __future__ import annotations

import pandas as pd


def rank_drivers(tornado_table: pd.DataFrame, output: str) -> pd.Series:
    """Largest absolute % change of `output` per assumption, sorted from strongest driver."""
    t = tornado_table[tornado_table["parameter"] != "base"]
    return (
        t.groupby("parameter")[f"{output} %chg"]
        .apply(lambda s: s.abs().max())
        .sort_values(ascending=False)
    )
