"""Capital allocation, pricing and limits: contributions add up; pricing identities."""

import numpy as np
import pandas as pd
import pytest

from creditengine.capital.allocation import contribution_table, es_contributions, sd_contributions
from creditengine.capital.limits import limit_utilisation, transfer_worth_it
from creditengine.capital.pricing import annual_pd, breakeven_spread, raroc
from creditengine.simulation.results import expected_shortfall


@pytest.fixture
def losses():
    rng = np.random.default_rng(0)
    z = rng.standard_normal((20_000, 1))
    return np.maximum(0, rng.standard_normal((20_000, 6)) + 1.5 * z * np.arange(1, 7) / 6)


def test_es_contributions_add_up(losses):
    total = losses.sum(axis=1)
    assert es_contributions(losses, 0.99).sum() == pytest.approx(
        expected_shortfall(total, 0.99) - total.mean()
    )


def test_sd_contributions_add_up(losses):
    assert sd_contributions(losses).sum() == pytest.approx(losses.sum(axis=1).std())


def test_contribution_table_shares(losses):
    t = contribution_table(losses, np.ones(6), np.array(list("aabbcc")))
    for col in ["exposure %", "EL %", "variance %", "ES capital %"]:
        assert t[col].sum() == pytest.approx(100)
    # the most systematic pair carries the largest share of tail capital
    assert t["ES capital %"].idxmax() == "c"


def test_pricing():
    assert annual_pd(1 - 0.99**5, 5) == pytest.approx(0.01)
    s = breakeven_spread(0.0016, 0.0163, 2.0, 0.10)
    assert float(s) == pytest.approx(0.0016 + 0.00326)
    assert raroc(0.01, 0.002, 0.04) == pytest.approx(0.2)


def test_limits_and_transfer():
    u = limit_utilisation(
        pd.Series({"a": 50.0, "b": 95.0, "c": 120.0}),
        pd.Series({"a": 100.0, "b": 100.0, "c": 100.0}),
    )
    assert list(u["status"]) == ["ok", "review", "breach"]
    assert transfer_worth_it(1.0, 0.5, 10.0) and not transfer_worth_it(2.0, 0.5, 10.0)
