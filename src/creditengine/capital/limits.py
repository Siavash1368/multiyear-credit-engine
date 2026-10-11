"""Limits.

Risk limits set on capital contribution, not exposure. Developed in NB09.

    utilisation_g = sum of ES capital contributions in group g / limit_g
Above 100%: stop adding to the group, or transfer risk. Above the warning level: review.
"""

from __future__ import annotations

import pandas as pd


def limit_utilisation(
    contributions: pd.Series, limits: pd.Series, warning: float = 0.90
) -> pd.DataFrame:
    """Utilisation of capital limits by group, with a status flag."""
    util = (contributions / limits).rename("utilisation")
    status = pd.Series("ok", index=util.index)
    status[util >= warning] = "review"
    status[util >= 1.0] = "breach"
    return pd.DataFrame(
        {"capital": contributions, "limit": limits, "utilisation": util, "status": status}
    )


def transfer_worth_it(
    protection_cost: float, el_removed: float, capital_removed: float, cost_of_capital: float = 0.10
) -> bool:
    """Risk transfer pays when it costs less than the expected loss and capital cost it removes."""
    return protection_cost < el_removed + cost_of_capital * capital_removed
