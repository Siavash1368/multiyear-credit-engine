"""Whole book on one economy: bonds + mortgages + tranches, with a synthetic matrix."""

import numpy as np
import pandas as pd

from creditengine.assets.book import load_book
from creditengine.capital.allocation import es_contributions
from creditengine.data.naic import factor_by_rating, load_portfolio_adjustment
from creditengine.data.rating_agency import STATES
from creditengine.simulation.portfolio import BookSettings, simulate_book


def test_whole_book_runs_and_reconciles(toy_matrix):
    book = load_book()
    s = BookSettings(n_paths=600, beta_cre=book.beta_cre, beta_pool=book.beta_pool, seed=3)
    res = simulate_book(
        book.bonds,
        book.cre,
        book.structured,
        toy_matrix,
        factor_by_rating().reindex(STATES).to_numpy(),
        load_portfolio_adjustment(),
        book.tranche_factor,
        s,
        book.cre_settings,
    )
    by_class = {k: v.sum() for k, v in res.losses_by_class.items()}
    assert np.isclose(res.asset_loss.sum(), sum(by_class.values()))
    assert np.isclose(res.exposure.sum(), 1e9)
    assert set(res.labels["asset_class"]) == {
        "corporate bonds",
        "commercial mortgages",
        "structured",
    }
    rc = es_contributions(res.asset_loss, 0.99)
    total = res.total_loss
    assert np.isclose(rc.sum(), total[total >= np.quantile(total, 0.99)].mean() - total.mean())
    for v in res.rbc_by_class.values():
        assert v.shape == (600, 6) and np.all(v >= 0)
    assert isinstance(res.labels, pd.DataFrame)
