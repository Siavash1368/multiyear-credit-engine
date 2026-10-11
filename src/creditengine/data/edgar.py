"""SEC EDGAR and market data.

Merton inputs for listed issuers: balance-sheet liabilities and shares outstanding from SEC XBRL
company facts; daily prices from data/raw/market/prices/. Developed in NB02.
Company facts are public; price files follow the provider's terms and are kept out of Git.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from creditengine.utils.paths import data_dir

COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"


def load_facts(ticker: str) -> dict:
    """Company facts JSON saved as data/raw/sec_edgar/companyfacts/<TICKER>.json."""
    with open(
        data_dir("raw", "sec_edgar", "companyfacts", f"{ticker}.json"), encoding="utf-8"
    ) as fh:
        return json.load(fh)


def latest_fact(
    facts: dict,
    tags: list[str],
    taxonomy: str = "us-gaap",
    unit: str = "USD",
    forms: tuple[str, ...] = ("10-K", "10-Q"),
) -> tuple[float, str] | None:
    """Most recent value (by period end) of the first tag that has data in a 10-K or 10-Q."""
    block = facts.get("facts", {}).get(taxonomy, {})
    for tag in tags:
        items = block.get(tag, {}).get("units", {}).get(unit, [])
        items = [x for x in items if x.get("form") in forms] or items
        if items:
            best = max(items, key=lambda x: (x["end"], x.get("filed", "")))
            return float(best["val"]), best["end"]
    return None


def shares_outstanding(facts: dict) -> tuple[float, str] | None:
    """Latest common shares outstanding from the cover page (dei), else from us-gaap."""
    found = latest_fact(
        facts, ["EntityCommonStockSharesOutstanding"], "dei", "shares", forms=("10-K", "10-Q")
    )
    return found or latest_fact(facts, ["CommonStockSharesOutstanding"], "us-gaap", "shares")


def load_prices(ticker: str, path: str | Path | None = None) -> pd.Series:
    """Daily close prices indexed by date."""
    frame = pd.read_csv(
        path or data_dir("raw", "market", "prices", f"{ticker}.csv"), parse_dates=["date"]
    )
    return frame.set_index("date")["close"].dropna()


def equity_volatility(prices: pd.Series, window: int = 252) -> float:
    """Annualised volatility of daily log returns over the last `window` trading days."""
    r = np.log(prices).diff().dropna().iloc[-window:]
    return float(r.std(ddof=1) * np.sqrt(252))


def merton_inputs(ticker: str, facts_ticker: str | None = None) -> dict[str, float | str]:
    """Equity value, equity volatility and KMV-style default point for one issuer.

    Default point = current liabilities + half of non-current liabilities (A-12).
    """
    facts = load_facts(facts_ticker or ticker)
    prices = load_prices(ticker)
    shares, shares_date = shares_outstanding(facts) or (np.nan, "")
    total, total_end = latest_fact(facts, ["Liabilities"]) or (np.nan, "")
    current, _ = latest_fact(facts, ["LiabilitiesCurrent"]) or (np.nan, "")
    if np.isnan(total):  # some filers do not tag total liabilities
        assets, _ = latest_fact(facts, ["Assets"]) or (np.nan, "")
        equity_book, _ = latest_fact(
            facts,
            [
                "StockholdersEquity",
                "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            ],
        ) or (np.nan, "")
        total = assets - equity_book
    return {
        "ticker": ticker,
        "price_date": prices.index[-1].date().isoformat(),
        "equity": float(prices.iloc[-1] * shares),
        "sigma_e": equity_volatility(prices),
        "current_liabilities": current,
        "total_liabilities": total,
        "default_point": current + 0.5 * (total - current),
        "balance_sheet_date": total_end,
        "shares_date": shares_date,
    }
