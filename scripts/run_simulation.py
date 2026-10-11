"""Run the multi-year simulation for a portfolio configuration.

Usage: python scripts/run_simulation.py --config configs/base.yaml

Writes to reports/:
  tables/loss_summary.csv, loss_by_year.csv, rbc_path.csv,
  tables/validation_vasicek.csv, validation_cumulative_pd.csv
  figures/loss_distribution.png, capital_path.png, cumulative_pd_check.png
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from creditengine.assets.corporate import BondPortfolio
from creditengine.capital.rbc import rbc_path
from creditengine.config import load_config, load_portfolio_config
from creditengine.data.naic import factor_by_rating, load_portfolio_adjustment
from creditengine.data.rating_agency import (
    DEFAULT,
    RATINGS,
    load_cumulative_default_rates,
    load_transition_matrix,
)
from creditengine.models.cycle import basel_correlation
from creditengine.models.migration import cumulative_default_from_matrix
from creditengine.reporting import figures
from creditengine.simulation.engine import SimulationSettings, simulate
from creditengine.utils.paths import project_root, reports_dir
from creditengine.validation.closed_form import compare_cumulative_pd, vasicek_quantile


def issuer_correlation(cfg, matrix: np.ndarray, rating: np.ndarray) -> np.ndarray | float:
    """rho per issuer: Basel formula on the 1-year PD of the initial rating, or one fixed value."""
    if cfg.cycle.correlation_source == "fixed":
        return float(cfg.cycle.asset_correlation)
    return basel_correlation(matrix[:-1, DEFAULT])[rating]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/base.yaml")
    parser.add_argument("--portfolio", default="configs/portfolios/corporate_bonds.yaml")
    parser.add_argument("--paths", type=int, default=None, help="override n_paths")
    args = parser.parse_args()

    cfg = load_config(args.config)
    pcfg = load_portfolio_config(args.portfolio)
    tables, figs = reports_dir("tables"), reports_dir("figures")

    # 1. Inputs
    matrix_df = load_transition_matrix(project_root() / cfg.migration.matrix_file)
    matrix = matrix_df.to_numpy()
    published = load_cumulative_default_rates()
    book = BondPortfolio.stylised(
        pcfg.total_exposure_usd, pcfg.n_issuers, pcfg.rating_mix, pcfg.maturity_years, pcfg.seed
    )
    book.to_frame().to_csv(tables / "portfolio.csv", index=False)

    # 2. Simulate the bond book
    settings = SimulationSettings(
        horizon=cfg.simulation.horizon_years,
        n_paths=args.paths or cfg.simulation.n_paths,
        rho=issuer_correlation(cfg, matrix, book.rating),
        phi=cfg.cycle.persistence,
        lgd_mean=cfg.recovery.lgd_mean,
        lgd_std=cfg.recovery.lgd_std,
        z0=cfg.cycle.start_state,
        seed=cfg.simulation.seed,
    )
    result = simulate(book, matrix, settings)
    summary = result.summary(tuple(cfg.outputs.quantiles))
    summary.to_csv(tables / "loss_summary.csv", header=["usd"])
    result.loss_by_year().to_csv(tables / "loss_by_year.csv")

    # 3. Statutory capital path
    factors = factor_by_rating().reindex(RATINGS + ["D"]).to_numpy()
    rbc = rbc_path(result, factors, load_portfolio_adjustment())
    pcts = [5, 50, 95, 99.5]
    rbc_table = pd.DataFrame(
        np.percentile(rbc, pcts, axis=0).T, columns=[f"p{p}" for p in pcts]
    ).rename_axis("year")
    rbc_table.to_csv(tables / "rbc_path.csv")

    # 4. Validation run: 100 issuers per rating, every bond outlives the horizon
    n_per = 100
    rating = np.repeat(np.arange(len(RATINGS)), n_per)
    check_book = BondPortfolio(
        issuer=np.arange(rating.size),
        rating=rating,
        exposure=np.ones(rating.size),
        maturity=np.full(rating.size, settings.horizon),
    )
    # (a) phi = 0: independent years, so the simulation must reproduce P^n (engine check)
    # (b) configured phi: a persistent cycle adds clustering on top of P^n (model finding)
    base = {**settings.__dict__, "n_paths": 4000, "rho": 0.20}
    sim_phi0 = simulate(check_book, matrix, SimulationSettings(**{**base, "phi": 0.0}))
    sim_cum = simulate(check_book, matrix, SimulationSettings(**base)).cumulative_default_rates()
    years = list(range(1, settings.horizon + 1))
    power = pd.DataFrame(
        cumulative_default_from_matrix(matrix, settings.horizon)[:-1], index=RATINGS, columns=years
    )
    cum_table = compare_cumulative_pd(sim_cum, published[years])
    cum_table["matrix_power"] = power.stack().reindex(cum_table.index).to_numpy()
    phi0 = sim_phi0.cumulative_default_rates().stack()
    cum_table["simulated_phi0"] = phi0.reindex(cum_table.index).to_numpy()
    cum_table.to_csv(tables / "validation_cumulative_pd.csv")

    # Vasicek check: one year, 1,000 'B' issuers, fixed rho, engine vs closed form
    p_b = matrix[RATINGS.index("B"), DEFAULT]
    vas_book = BondPortfolio(
        issuer=np.arange(1000),
        rating=np.full(1000, RATINGS.index("B")),
        exposure=np.ones(1000),
        maturity=np.ones(1000, dtype=int),
    )
    vas_settings = SimulationSettings(horizon=1, n_paths=20_000, rho=0.15, phi=0.0, seed=1)
    year1 = simulate(vas_book, matrix, vas_settings).ratings[:, 1, :]
    frac = (year1 == DEFAULT).mean(axis=1)  # default fraction on each path
    qs = np.array([0.5, 0.9, 0.99, 0.995])
    vas = pd.DataFrame(
        {"engine": np.quantile(frac, qs), "closed_form": vasicek_quantile(qs, p_b, 0.15)},
        index=pd.Index(qs, name="q"),
    )
    vas.to_csv(tables / "validation_vasicek.csv")

    # 5. Figures
    q_top = max(cfg.outputs.quantiles)
    figures.loss_distribution(
        result.total_loss,
        summary[f"VaR {q_top:.1%}"],
        summary[f"ES {q_top:.1%}"],
        figs / "loss_distribution.png",
        q_label=f"{q_top:.1%}",
    )
    figures.capital_path(rbc, figs / "capital_path.png")
    figures.cumulative_pd_check(sim_cum, power, published, figs / "cumulative_pd_check.png")

    pd.set_option("display.float_format", "{:,.4f}".format)
    print("Loss summary (USD m):\n", (summary / 1e6).round(2).to_string())
    print("\nRBC path (USD m):\n", (rbc_table / 1e6).round(2).to_string())
    print("\nVasicek check (default fraction):\n", vas.to_string())
    print("\nCumulative PD check:\n", cum_table.round(4).to_string())


if __name__ == "__main__":
    main()
