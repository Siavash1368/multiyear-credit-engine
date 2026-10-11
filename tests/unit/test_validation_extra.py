"""Backtest bands, convergence, sensitivity, FRED loader, EDGAR facts."""

import json

import numpy as np
import pandas as pd
import pytest

from creditengine.data import fred
from creditengine.data.edgar import latest_fact
from creditengine.models.cycle import conditional_pd
from creditengine.validation.backtest import binomial_band, vasicek_band, walk_forward
from creditengine.validation.convergence import bootstrap_se, seed_study
from creditengine.validation.sensitivity import tornado


def test_correlated_band_is_wider():
    lo_b, hi_b = binomial_band(0.02, 500)
    lo_v, hi_v = vasicek_band(0.02, 0.2)
    assert lo_v < lo_b < 0.02 < hi_b < hi_v
    assert hi_v == pytest.approx(0.094, abs=0.001)


def test_walk_forward_on_a_true_vasicek_series():
    rng = np.random.default_rng(0)
    years = np.arange(1900, 2026)
    dr = pd.Series(conditional_pd(0.03, 0.15, rng.standard_normal(len(years))), index=years)
    walk = walk_forward(dr, first_test_year=1950)
    assert (~walk["inside"]).mean() < 0.12  # about 5% expected


def test_bootstrap_and_seed_study():
    x = np.random.default_rng(0).lognormal(size=5000)
    se = bootstrap_se(x, 0.99, n_boot=50)
    assert all(v > 0 for v in se.values())
    t = seed_study(lambda n, s: np.random.default_rng(s).lognormal(size=n), [500, 2000], [1, 2, 3])
    assert list(t.index) == [500, 2000] and t.loc[2000, "EL sd"] < t.loc[500, "EL sd"] * 1.5


def test_tornado_structure():
    t = tornado(lambda p: {"y": p["a"] * 2 + p["b"]}, {"a": 1.0, "b": 1.0}, {"a": (0.5, 2.0)})
    assert list(t["parameter"]) == ["base", "a", "a"]
    assert t.loc[t["side"] == "high", "y %chg"].iloc[0] == pytest.approx(100 * (5 / 3 - 1))


def test_fred_loader(tmp_path):
    f = tmp_path / "X.csv"
    f.write_text("observation_date,X\n2020-01-01,1.0\n2020-04-01,.\n2021-01-01,3.0\n")
    s = fred.load("X", f)
    assert len(s) == 2 and fred.annual(s).to_dict() == {2020: 1.0, 2021: 3.0}


def test_latest_fact_picks_latest_period():
    facts = {
        "facts": {
            "us-gaap": {
                "Liabilities": {
                    "units": {
                        "USD": [
                            {"end": "2024-12-31", "val": 1, "form": "10-K"},
                            {"end": "2025-06-30", "val": 2, "form": "10-Q"},
                            {"end": "2023-12-31", "val": 3, "form": "10-K"},
                        ]
                    }
                }
            }
        }
    }
    assert latest_fact(json.loads(json.dumps(facts)), ["Liabilities"]) == (2.0, "2025-06-30")
