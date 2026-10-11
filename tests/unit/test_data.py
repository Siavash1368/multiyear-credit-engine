"""Transition matrix rows sum to one; default column monotone; NAIC factors match citations."""

import numpy as np
import pandas as pd
import pytest

from creditengine.data.naic import (
    factor_by_rating,
    load_bond_factors,
    load_portfolio_adjustment,
)
from creditengine.data.rating_agency import (
    RATINGS,
    STATES,
    load_annual_default_rates,
    load_cumulative_default_rates,
    load_transition_matrix,
    nr_adjust,
    rating_index,
)
from creditengine.utils.paths import external_file

needs_data = pytest.mark.skipif(
    not external_file("transition_matrix_1y.csv").exists(),
    reason="S&P tables not entered in data/external/",
)


def test_nr_adjust_rescales_rows():
    raw = pd.DataFrame({"A": [0.5], "D": [0.1], "NR": [0.4]})
    out = nr_adjust(raw)
    assert np.allclose(out.to_numpy(), [[0.5 / 0.6, 0.1 / 0.6]])


def test_rating_index():
    assert list(rating_index(["AAA", "BBB", "D"])) == [0, 3, 7]


@needs_data
def test_transition_matrix_shape_and_rows():
    m = load_transition_matrix()
    assert list(m.index) == STATES and list(m.columns) == STATES
    assert np.allclose(m.sum(axis=1), 1.0)
    assert m.loc["D", "D"] == 1.0
    assert np.all(np.diff(m["D"].to_numpy()[:-1]) >= 0)  # worse rating, higher PD


@needs_data
def test_cumulative_rates_increase_with_horizon():
    c = load_cumulative_default_rates()
    assert list(c.index) == RATINGS
    assert (c.diff(axis=1).iloc[:, 1:] >= 0).all().all()
    assert c.loc["BBB", 1] == 0.0013  # S&P 2025 study, Table 24


@needs_data
def test_annual_rates_match_table_4_statistics():
    dr = load_annual_default_rates()
    assert dr.index.min() == 1981 and dr.index.max() == 2025
    assert round(dr["B"].max(), 4) == 0.1384  # Table 4 maximum
    assert round(dr["CCC/C"].std() * 100, 2) == 11.47  # Table 4 standard deviation


def test_naic_factors_cited_values():
    f = load_bond_factors()
    assert f["1.A"] == 0.0029 and f["2.B"] == 0.0163 and f["4.B"] == 0.0832
    assert f.max() == 0.30  # 30% cap
    assert np.all(np.diff(f.to_numpy()) >= 0)


def test_factor_by_rating_covers_all_states():
    f = factor_by_rating()
    assert set(f.index) == set(STATES)
    assert f.notna().all()


def test_portfolio_adjustment_table():
    tiers = load_portfolio_adjustment()
    assert list(tiers["factor"]) == [7.50, 1.75, 0.90, 0.85, 0.75]
