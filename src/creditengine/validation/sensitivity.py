"""Sensitivity.

Link assumptions to outputs: move one assumption at a time and record the outputs (tornado).
Developed in NB10 and NB11.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd


def tornado(
    run: Callable[[dict], dict[str, float]],
    base: dict,
    shocks: dict[str, tuple[object, object]],
) -> pd.DataFrame:
    """One-at-a-time sensitivity.

    run(params) returns named outputs (e.g. EL, ES). shocks maps a parameter to its (low, high)
    values. Result: one row per parameter and side with the outputs and their % change from base.
    """
    base_out = run(base)
    rows = [{"parameter": "base", "side": "", "value": "", **base_out}]
    for name, (low, high) in shocks.items():
        for side, value in (("low", low), ("high", high)):
            out = run({**base, name: value})
            rows.append({"parameter": name, "side": side, "value": value, **out})
    table = pd.DataFrame(rows)
    for key, ref in base_out.items():
        table[f"{key} %chg"] = 100 * (table[key] / ref - 1.0)
    return table
