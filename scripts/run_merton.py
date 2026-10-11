"""Merton on listed issuers (NB02, validation V-08): distance to default from equity markets
compared with agency ratings.

Usage: python scripts/run_merton.py
Inputs: data/raw/market/prices/<TICKER>.csv, data/raw/sec_edgar/companyfacts/<TICKER>.json,
1-year Treasury from FRED (DGS1). Writes reports/tables/merton_listed.csv and
reports/figures/merton_dd_vs_rating.png.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

from creditengine.data import fred  # noqa: E402
from creditengine.data.edgar import merton_inputs  # noqa: E402
from creditengine.data.rating_agency import DEFAULT, RATINGS, load_transition_matrix  # noqa: E402
from creditengine.models.merton import (  # noqa: E402
    default_probability,
    distance_to_default,
    solve_assets,
)
from creditengine.utils.paths import reports_dir  # noqa: E402

# Indicative issuer ratings as listed in data/raw/MANIFEST.md (confirm before any real use)
UNIVERSE = {
    "MSFT": "AAA",
    "JNJ": "AAA",
    "AAPL": "AA+",
    "XOM": "AA-",
    "NFLX": "A",
    "T": "BBB",
    "KHC": "BBB",
    "F": "BBB-",
    "BA": "BBB-",
    "OXY": "BBB-",
    "HCA": "BBB-",
    "DAL": "BBB-",
    "CCL": "BB+",
    "M": "BB+",
    "AAL": "B+",
}
FACTS_FILE = {"XOM": "XOM_CIK0000034088"}  # legacy Exxon Mobil Corp filings (see MANIFEST)


def letter(notch: str) -> str:
    base = notch.rstrip("+-")
    return "CCC/C" if base.startswith("CCC") else base


def main() -> None:
    try:
        r = float(fred.load("DGS1").iloc[-1]) / 100.0
    except FileNotFoundError:
        r = 0.04
    pd_rating = pd.Series(load_transition_matrix().to_numpy()[:-1, DEFAULT], index=RATINGS)
    rows = []
    for ticker, notch in UNIVERSE.items():
        try:
            x = merton_inputs(ticker, FACTS_FILE.get(ticker))
        except (FileNotFoundError, KeyError) as exc:
            print(f"skip {ticker}: {exc}")
            continue
        v, s_v = solve_assets(x["equity"], x["sigma_e"], x["default_point"], r)
        dd = distance_to_default(v, x["default_point"], r, s_v)
        rows.append(
            {
                "ticker": ticker,
                "rating": notch,
                "letter": letter(notch),
                "equity $bn": x["equity"] / 1e9,
                "sigma_E": x["sigma_e"],
                "default point $bn": x["default_point"] / 1e9,
                "assets $bn": v / 1e9,
                "sigma_V": s_v,
                "leverage D/V": x["default_point"] / v,
                "DD": dd,
                "Merton PD %": 100 * default_probability(v, x["default_point"], r, s_v),
                "rating PD %": 100 * pd_rating[letter(notch)],
                "price date": x["price_date"],
                "balance sheet": x["balance_sheet_date"],
            }
        )
    table = pd.DataFrame(rows).set_index("ticker")
    rank = table["letter"].map({k: i for i, k in enumerate(RATINGS)})
    rho_s = spearmanr(table["DD"], -rank).statistic
    table.to_csv(reports_dir("tables") / "merton_listed.csv")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.scatter(rank + np.linspace(-0.15, 0.15, len(rank)), table["DD"], color="#4C72B0")
    for t, (x_, y_) in zip(table.index, zip(rank, table["DD"], strict=True), strict=True):
        ax.annotate(t, (x_, y_), fontsize=7, xytext=(4, 2), textcoords="offset points")
    ax.set_xticks(range(len(RATINGS)), RATINGS)
    ax.set_xlabel("Agency rating (letter)")
    ax.set_ylabel("Merton distance to default")
    ax.set_title(f"Market-implied DD vs ratings (Spearman {rho_s:.2f}, r = {r:.2%})")
    fig.tight_layout()
    fig.savefig(reports_dir("figures") / "merton_dd_vs_rating.png", dpi=150)
    plt.close(fig)

    pd.set_option("display.float_format", "{:,.3f}".format)
    print(table.drop(columns=["price date", "balance sheet"]).to_string())
    print(f"\nSpearman rank correlation, DD vs rating: {rho_s:.2f}  (1-year rate {r:.2%})")


if __name__ == "__main__":
    main()
