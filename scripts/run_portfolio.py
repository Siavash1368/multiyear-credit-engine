"""Run the whole stylised book: bonds + commercial mortgages + structured tranches on one economy.

Usage: python scripts/run_portfolio.py [--paths 20000]

Writes to reports/:
  tables/book_loss_summary.csv, book_contrib_class.csv, book_contrib_group.csv, book_rbc.csv,
  tables/tranche_table.csv, tranche_correlation.csv, pricing.csv, stress.csv, limits.csv
  figures/book_contributions.png, book_capital_path.png, tranche_correlation.png
  summary.md (every number quoted in the README "Whole book" section)
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from creditengine.assets.book import load_book
from creditengine.assets.structured import correlation_sensitivity, tranche_table
from creditengine.capital.allocation import contribution_table, es_contributions
from creditengine.capital.limits import limit_utilisation
from creditengine.capital.pricing import annual_pd, breakeven_spread
from creditengine.config import load_config
from creditengine.data import fred
from creditengine.data.naic import factor_by_rating, load_portfolio_adjustment
from creditengine.data.rating_agency import (
    DEFAULT,
    RATINGS,
    load_annual_default_rates,
    load_cumulative_default_rates,
    load_transition_matrix,
)
from creditengine.models.cycle import basel_correlation, fit_vasicek, implied_factor
from creditengine.reporting import figures
from creditengine.reporting.summary import write_summary
from creditengine.simulation.portfolio import BookSettings, simulate_book
from creditengine.simulation.results import expected_shortfall, value_at_risk
from creditengine.utils.paths import project_root, reports_dir

Q = 0.995
OAS = {
    "AAA": "BAMLC0A1CAAA",
    "AA": "BAMLC0A2CAA",
    "A": "BAMLC0A3CA",
    "BBB": "BAMLC0A4CBBB",
    "BB": "BAMLH0A1HYBB",
    "B": "BAMLH0A2HYB",
    "CCC/C": "BAMLH0A3HYC",
}


def loss_stats(loss: np.ndarray) -> dict[str, float]:
    return {
        "EL": loss.mean(),
        "StdDev": loss.std(),
        f"VaR {Q:.1%}": value_at_risk(loss, Q),
        f"ES {Q:.1%}": expected_shortfall(loss, Q),
        "EC (ES - EL)": expected_shortfall(loss, Q) - loss.mean(),
    }


def implied_path(start_year: int, horizon: int) -> np.ndarray:
    """Implied global cycle for a historical window, from single-B default rates."""
    rates = load_annual_default_rates()["B"]
    p, rho = fit_vasicek(rates[rates > 0].to_numpy())
    z = pd.Series(implied_factor(p, rho, rates.clip(lower=1e-4).to_numpy()), index=rates.index)
    return z.loc[start_year : start_year + horizon - 1].to_numpy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", type=int, default=None)
    args = parser.parse_args()

    cfg = load_config("configs/base.yaml")
    tables, figs = reports_dir("tables"), reports_dir("figures")
    book = load_book()
    matrix = load_transition_matrix(project_root() / cfg.migration.matrix_file).to_numpy()
    bond_factors = factor_by_rating().reindex(RATINGS + ["D"]).to_numpy()
    tiers = load_portfolio_adjustment()
    rho = basel_correlation(matrix[:-1, DEFAULT])[book.bonds.rating]
    n_paths = args.paths or cfg.simulation.n_paths

    def run(**over) -> object:
        s = BookSettings(
            horizon=cfg.simulation.horizon_years,
            n_paths=n_paths,
            phi=cfg.cycle.persistence,
            seed=cfg.simulation.seed,
            beta_cre=book.beta_cre,
            beta_pool=book.beta_pool,
            bond_rho=rho,
            bond_lgd_mean=cfg.recovery.lgd_mean,
            bond_lgd_std=cfg.recovery.lgd_std,
        )
        for k, v in over.items():
            setattr(s, k, v)
        return simulate_book(
            book.bonds,
            book.cre,
            book.structured,
            matrix,
            bond_factors,
            tiers,
            book.tranche_factor,
            s,
            book.cre_settings,
        )

    res = run()
    labels = res.labels

    # 1. losses by class and total; diversification
    summary = pd.DataFrame({k: loss_stats(v.sum(axis=1)) for k, v in res.losses_by_class.items()})
    summary["whole book"] = pd.Series(loss_stats(res.total_loss))
    standalone_ec = summary.loc["EC (ES - EL)", list(res.losses_by_class)].sum()
    diversification = 1.0 - summary.loc["EC (ES - EL)", "whole book"] / standalone_ec
    summary.to_csv(tables / "book_loss_summary.csv")

    # 2. contributions
    by_class = contribution_table(res.asset_loss, res.exposure, labels["asset_class"], Q)
    by_group = contribution_table(res.asset_loss, res.exposure, labels["group"], Q)
    by_class.to_csv(tables / "book_contrib_class.csv")
    by_group.to_csv(tables / "book_contrib_group.csv")
    figures.contributions(
        by_class,
        figs / "book_contributions.png",
        "Exposure, expected loss and tail capital by asset class",
    )

    # 3. statutory capital path
    rbc = pd.DataFrame(
        {
            k: {
                "year 0": v[0, 0],
                "year 5 median": np.median(v[:, -1]),
                "year 5 p99.5": np.percentile(v[:, -1], 99.5),
            }
            for k, v in {**res.rbc_by_class, "whole book": res.rbc_total}.items()
        }
    ).T
    rbc.to_csv(tables / "book_rbc.csv")
    figures.capital_by_class(res.rbc_by_class, figs / "book_capital_path.png")

    # 4. structured: tranches on the simulated pool; correlation sensitivity (closed form)
    tr_table = tranche_table(res.pool_loss_rate, book.structured.tranches, Q)
    tr_table.to_csv(tables / "tranche_table.csv")
    pool_pd = float(np.mean(matrix[book.structured.pool.rating, DEFAULT]))
    corr = correlation_sensitivity(
        pool_pd,
        book.structured.pool_lgd_mean,
        book.structured.tranches,
        (0.05, 0.10, 0.15, 0.20, 0.30, 0.40),
    )
    corr.to_csv(tables / "tranche_correlation.csv")
    figures.tranche_correlation(corr, figs / "tranche_correlation.png")

    # 5. pricing: break-even spread by rating vs market option-adjusted spread
    cum5 = load_cumulative_default_rates()[5]
    fac = factor_by_rating()
    rows = []
    for r in RATINGS:
        el = annual_pd(cum5[r], 5) * cfg.recovery.lgd_mean
        s_star = float(breakeven_spread(el, fac[r]))
        row = {
            "rating": r,
            "annual EL bp": 1e4 * el,
            "RBC factor %": 100 * fac[r],
            "capital cost bp": 1e4 * (s_star - el),
            "break-even bp": 1e4 * s_star,
        }
        try:
            oas = fred.load(OAS[r])
            row.update(
                {"market OAS bp": 100 * oas.iloc[-1], "OAS date": oas.index[-1].date().isoformat()}
            )
        except (FileNotFoundError, KeyError):
            row.update({"market OAS bp": np.nan, "OAS date": ""})
        rows.append(row)
    pricing = pd.DataFrame(rows).set_index("rating")
    pricing["cushion bp"] = pricing["market OAS bp"] - pricing["break-even bp"]
    pricing.to_csv(tables / "pricing.csv")

    # 6. limits on ES capital by asset class
    ec_total = float(summary.loc["EC (ES - EL)", "whole book"])
    rc_class = (
        pd.Series(es_contributions(res.asset_loss, Q))
        .groupby(labels["asset_class"].to_numpy())
        .sum()
    )
    limits = pd.Series(book.limits_share) * ec_total
    util = limit_utilisation(rc_class, limits.reindex(rc_class.index))
    util.to_csv(tables / "limits.csv")

    # 7. stress: replay historical cycles as the global path (other shocks still random)
    stress_rows = {"base (stochastic)": res}
    for name, start in [("replay 2000-2004", 2000), ("replay 2008-2012", 2008)]:
        path = implied_path(start, cfg.simulation.horizon_years)
        stress_rows[f"{name} Z={np.round(path, 2).tolist()}"] = run(
            global_path=path, n_paths=min(n_paths, 5000)
        )
    stress = pd.DataFrame(
        {
            k: {
                "mean 5y loss": r.total_loss.mean(),
                "bonds": r.losses_by_class["corporate bonds"].sum(1).mean(),
                "mortgages": r.losses_by_class["commercial mortgages"].sum(1).mean(),
                "structured": r.losses_by_class["structured"].sum(1).mean(),
                "RBC year 5 median": np.median(r.rbc_total[:, -1]),
            }
            for k, r in stress_rows.items()
        }
    ).T
    stress.to_csv(tables / "stress.csv")

    write_summary(
        reports_dir() / "summary.md",
        {
            "Whole book: five-year loss by asset class (USD)": summary,
            "Contributions by asset class (ES 99.5%)": by_class,
            "Contributions by rating, property type and tranche": by_group,
            "Statutory capital (USD, pre-tax)": rbc,
            "Tranches on the simulated collateral pool": tr_table,
            "Tranche expected loss vs correlation (large pool, closed form)": corr,
            "Break-even spread vs market spread": pricing,
            "Capital limits by asset class": util,
            "Stress: historical cycle replays (USD)": stress,
        },
        notes=[
            f"Diversification benefit (1 - book EC / sum of standalone EC): {diversification:.1%}",
            f"Paths: {n_paths}; seed {cfg.simulation.seed}; ES level {Q:.1%}",
        ],
    )
    pd.set_option("display.float_format", "{:,.2f}".format)
    print((summary / 1e6).round(2).to_string())
    print(f"\nDiversification benefit: {diversification:.1%}\n")
    print(by_class.round(2).to_string(), "\n")
    print((rbc / 1e6).round(2).to_string(), "\n")
    print(tr_table.round(4).to_string(), "\n")
    print(pricing.round(1).to_string(), "\n")
    print(util.round(3).to_string(), "\n")
    print((stress / 1e6).round(2).to_string())


if __name__ == "__main__":
    main()
