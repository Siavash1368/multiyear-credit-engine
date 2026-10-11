"""Validation suite (NB10): backtest, cycle proxies, convergence, variance reduction,
sensitivity (tornado), model-form challengers, tranche and mortgage closed-form checks.

Usage: python scripts/run_validation.py [--paths 10000]

Writes reports/tables/val_*.csv, reports/figures/backtest_bands.png, tornado_es.png and
reports/validation_summary.md.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from creditengine.assets.corporate import BondPortfolio
from creditengine.assets.cre import (
    CREPortfolio,
    CRESettings,
    balloon_default_probability,
    simulate_cre,
)
from creditengine.assets.structured import large_pool_tranche_el, tranche_loss
from creditengine.capital.rbc import rbc_path
from creditengine.config import load_config, load_portfolio_config
from creditengine.data import fred
from creditengine.data.naic import factor_by_rating, load_portfolio_adjustment
from creditengine.data.rating_agency import (
    DEFAULT,
    RATINGS,
    load_annual_default_rates,
    load_transition_matrix,
)
from creditengine.models.cycle import basel_correlation, fit_vasicek, implied_factor
from creditengine.reporting import figures
from creditengine.reporting.attribution import rank_drivers
from creditengine.reporting.summary import write_summary
from creditengine.simulation.engine import SimulationSettings, simulate
from creditengine.simulation.results import expected_shortfall
from creditengine.simulation.sampling import large_pool_tail_probability
from creditengine.utils.paths import reports_dir
from creditengine.validation.backtest import binomial_band, walk_forward
from creditengine.validation.closed_form import simulate_default_fraction
from creditengine.validation.convergence import bootstrap_se, seed_study
from creditengine.validation.sensitivity import tornado

Q = 0.995


def scale_pd(matrix: np.ndarray, k: float) -> np.ndarray:
    """Multiply every one-year PD by k and take the difference from staying in the same rating."""
    m = matrix.copy()
    extra = (k - 1.0) * m[:-1, DEFAULT]
    m[:-1, DEFAULT] += extra
    m[np.arange(len(m) - 1), np.arange(len(m) - 1)] -= extra
    return m


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", type=int, default=20_000)
    args = parser.parse_args()
    cfg = load_config("configs/base.yaml")
    pcfg = load_portfolio_config("configs/portfolios/corporate_bonds.yaml")
    tables, figs = reports_dir("tables"), reports_dir("figures")
    matrix = load_transition_matrix().to_numpy()
    rates = load_annual_default_rates()
    out: dict[str, pd.DataFrame] = {}
    notes: list[str] = []

    # V-05 backtest: out-of-sample correlated bands, walk forward from 2000
    bt_rows, walks = [], {}
    for col in ["BB", "B", "SG"]:
        walk = walk_forward(rates[col], first_test_year=2000)
        walks[col] = walk
        p, rho = fit_vasicek(rates[col][rates[col] > 0].to_numpy())
        lo_b, hi_b = binomial_band(p, 500)
        dr = rates[col].loc[2000:]
        outside = ~walk["inside"]
        bt_rows.append(
            {
                "series": col,
                "test years": len(walk),
                "outside correlated band": int(outside.sum()),
                "of which zero-default years": int((outside & (walk["default_rate"] == 0)).sum()),
                "share outside (expect ~5%)": (~walk["inside"]).mean(),
                "outside independent band, n=500 (illustrative)": int(
                    ((dr < lo_b) | (dr > hi_b)).sum()
                ),
            }
        )
    out["V-05 Backtest: walk-forward 95% bands, test years 2000-2025"] = pd.DataFrame(
        bt_rows
    ).set_index("series")
    figures.backtest_bands(
        walks["SG"],
        figs / "backtest_bands.png",
        "Speculative-grade default rate vs out-of-sample correlated band",
    )

    # Cycle proxies: implied Z (single-B) vs public series
    p_b, rho_b = fit_vasicek(rates["B"][rates["B"] > 0].to_numpy())
    z = pd.Series(
        implied_factor(p_b, rho_b, rates["B"].clip(lower=1e-4).to_numpy()), index=rates.index
    )
    proxies = {}
    try:
        proxies["business-loan charge-off rate"] = fred.annual(fred.load("CORBLACBS"))
        proxies["Baa minus Aaa yield"] = fred.annual(fred.load("BAA")) - fred.annual(
            fred.load("AAA")
        )
        proxies["recession share of year"] = fred.annual(fred.load("USREC"))
    except FileNotFoundError:
        notes.append("FRED files missing: cycle-proxy check skipped (run scripts/download_fred.py)")
    if proxies:
        rows = []
        for name, series in proxies.items():
            both = pd.concat([z.rename("z"), series.rename("x")], axis=1).dropna()
            rows.append(
                {
                    "proxy": name,
                    "years": len(both),
                    "corr with implied Z": both["z"].corr(both["x"]),
                }
            )
        out["Implied cycle vs public proxies (expect negative)"] = pd.DataFrame(rows).set_index(
            "proxy"
        )

    # Convergence: seed study and bootstrap on the bond book (V-07)
    book = BondPortfolio.stylised(
        pcfg.total_exposure_usd, pcfg.n_issuers, pcfg.rating_mix, pcfg.maturity_years, pcfg.seed
    )
    rho_i = basel_correlation(matrix[:-1, DEFAULT])[book.rating]
    base = SimulationSettings(
        horizon=cfg.simulation.horizon_years,
        rho=rho_i,
        phi=cfg.cycle.persistence,
        lgd_mean=cfg.recovery.lgd_mean,
        lgd_std=cfg.recovery.lgd_std,
    )

    def run_losses(n: int, seed: int) -> np.ndarray:
        s = SimulationSettings(**{**base.__dict__, "n_paths": n, "seed": seed})
        return simulate(book, matrix, s).total_loss

    conv = seed_study(run_losses, [2_500, 5_000, 10_000, 20_000], seeds=[1, 2, 3, 4, 5], q=Q)
    out["V-07 Convergence: mean and spread across 5 seeds (USD)"] = conv
    boot = pd.DataFrame(
        [bootstrap_se(run_losses(20_000, cfg.simulation.seed), Q)], index=["20,000 paths"]
    )
    out["V-07 Bootstrap standard errors (USD)"] = boot

    # Variance reduction: importance sampling on a large-pool tail probability
    rng = np.random.default_rng(0)
    plain = large_pool_tail_probability(0.02, 0.20, 0.6, 0.08, 20_000, rng, shift=0.0)
    shifted = large_pool_tail_probability(0.02, 0.20, 0.6, 0.08, 20_000, rng, shift=-2.5)
    out["Importance sampling: P(loss rate > 8%), PD 2%, rho 20%, LGD 60%"] = pd.DataFrame(
        [
            {"method": "plain Monte Carlo", "estimate": plain[0], "std error": plain[1]},
            {
                "method": "shifted economy (mu = -2.5) + weights",
                "estimate": shifted[0],
                "std error": shifted[1],
            },
        ]
    ).set_index("method")
    notes.append(
        f"Importance sampling cuts the standard error by a factor of {plain[1] / shifted[1]:.1f}"
    )

    # V-06 Sensitivity / attribution: tornado on the bond book
    factors = factor_by_rating().reindex(RATINGS + ["D"]).to_numpy()
    tiers = load_portfolio_adjustment()
    sector_book = BondPortfolio.stylised(
        pcfg.total_exposure_usd,
        pcfg.n_issuers,
        pcfg.rating_mix,
        pcfg.maturity_years,
        pcfg.seed,
        n_sectors=8,
    )

    def run_params(p: dict) -> dict[str, float]:
        m = scale_pd(matrix, p["pd_scale"])
        bk = sector_book if p["sector_beta"] < 1.0 else book
        s = SimulationSettings(
            horizon=base.horizon,
            n_paths=args.paths,
            seed=cfg.simulation.seed,
            rho=rho_i * p["rho_scale"],
            phi=p["phi"],
            lgd_mean=p["lgd_mean"],
            lgd_std=base.lgd_std,
            lgd_cycle=p["lgd_cycle"],
            copula=p["copula"],
            t_nu=6.0,
            sector_beta=p["sector_beta"] if p["sector_beta"] < 1.0 else None,
        )
        r = simulate(bk, m, s)
        loss = r.total_loss
        rbc = rbc_path(r, factors, tiers)
        return {
            "EL": loss.mean(),
            "ES": expected_shortfall(loss, Q),
            "RBC5 p99.5": float(np.percentile(rbc[:, -1], 99.5)),
        }

    base_p = {
        "pd_scale": 1.0,
        "rho_scale": 1.0,
        "phi": cfg.cycle.persistence,
        "lgd_mean": cfg.recovery.lgd_mean,
        "lgd_cycle": 0.0,
        "copula": "gaussian",
        "sector_beta": 1.0,
    }
    shocks = {
        "pd_scale": (0.8, 1.2),
        "rho_scale": (0.75, 1.25),
        "phi": (0.0, 0.7),
        "lgd_mean": (0.5, 0.7),
        "lgd_cycle": (0.0, 1.0),
        "copula": ("gaussian", "t"),
        "sector_beta": (1.0, 0.5),
    }
    tor = tornado(run_params, base_p, shocks)
    out["V-06 Tornado on the bond book (USD; % change vs base)"] = tor.set_index(
        ["parameter", "side"]
    )
    figures.tornado(tor, "ES", figs / "tornado_es.png")
    notes.append(
        "ES drivers, strongest first: "
        + ", ".join(f"{k} ({v:.0f}%)" for k, v in rank_drivers(tor, "ES").items())
    )

    # Tranche closed form vs finite simulated pool (one period)
    frac = simulate_default_fraction(0.02, 0.20, 10_000, 100_000, seed=3)
    tr_rows = []
    for a, d in [(0.0, 0.03), (0.03, 0.07), (0.07, 0.15)]:
        tr_rows.append(
            {
                "tranche": f"[{a:.0%}, {d:.0%}]",
                "simulated EL": tranche_loss(0.6 * frac, a, d).mean(),
                "closed form EL": large_pool_tranche_el(0.02, 0.20, 0.6, a, d),
            }
        )
    out["Tranche EL: 10,000-name pool vs large-pool formula"] = pd.DataFrame(tr_rows).set_index(
        "tranche"
    )

    # Commercial mortgage: balloon default vs Merton closed form (interest-only, no term trigger)
    loan = CREPortfolio(
        loan_id=np.array(["T1"]),
        property_type=np.array(["apartment"]),
        balance=np.array([10e6]),
        value=np.array([15.4e6]),
        noi=np.array([50e6]),
        rate=np.array([0.05]),
        amort_years=np.array([10_000]),
        maturity=np.array([5]),
    )
    sett = CRESettings(value_drift=0.02, value_vol=0.15, prepay_rate=0.0, refi_dscr_min=0.0, seed=9)
    zc = np.random.default_rng(10).standard_normal((100_000, 5))
    sim_pd = (simulate_cre(loan, zc, sett).default_year > 0).mean()
    out["Mortgage balloon default vs Merton closed form (LTV 65%, vol 15%, 5 years)"] = (
        pd.DataFrame(
            [
                {
                    "simulated": sim_pd,
                    "closed form N(-DD)": balloon_default_probability(15.4e6, 10e6, 0.02, 0.15, 5),
                }
            ],
            index=["balloon PD"],
        )
    )

    for title, df in out.items():
        df.to_csv(
            tables
            / (
                "val_"
                + "".join(ch if ch.isalnum() else "_" for ch in title[:40]).strip("_")
                + ".csv"
            )
        )
    write_summary(reports_dir() / "validation_summary.md", out, notes)
    pd.set_option("display.float_format", "{:,.4f}".format)
    for title, df in out.items():
        print(f"\n== {title}\n{df.to_string()}")
    print("\n" + "\n".join(notes))


if __name__ == "__main__":
    main()
