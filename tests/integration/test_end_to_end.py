"""Configuration to simulation to capital to report on a small portfolio (marked slow)."""

import numpy as np
import pytest

from creditengine.assets.corporate import BondPortfolio
from creditengine.capital.rbc import rbc_path
from creditengine.config import load_config, load_portfolio_config
from creditengine.data.naic import factor_by_rating, load_portfolio_adjustment
from creditengine.data.rating_agency import STATES, load_transition_matrix
from creditengine.simulation.engine import SimulationSettings, simulate
from creditengine.utils.paths import external_file

needs_data = pytest.mark.skipif(
    not external_file("transition_matrix_1y.csv").exists(),
    reason="S&P tables not entered in data/external/",
)


@pytest.mark.integration
@pytest.mark.slow
@needs_data
def test_config_to_capital():
    cfg = load_config("configs/base.yaml")
    pcfg = load_portfolio_config("configs/portfolios/corporate_bonds.yaml")
    matrix = load_transition_matrix().to_numpy()
    book = BondPortfolio.stylised(
        pcfg.total_exposure_usd, pcfg.n_issuers, pcfg.rating_mix, pcfg.maturity_years, pcfg.seed
    )
    s = SimulationSettings(
        horizon=cfg.simulation.horizon_years, n_paths=1000, phi=cfg.cycle.persistence
    )
    res = simulate(book, matrix, s)
    summary = res.summary()
    assert 0 < summary["EL"] < summary["VaR 99.5%"] <= summary["ES 99.5%"]

    factors = factor_by_rating().reindex(STATES).to_numpy()
    rbc = rbc_path(res, factors, load_portfolio_adjustment())
    assert rbc.shape == (1000, cfg.simulation.horizon_years + 1)
    assert np.all(np.isfinite(rbc)) and np.all(rbc[:, 0] == rbc[0, 0])
