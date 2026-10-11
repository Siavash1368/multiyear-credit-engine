"""Download SEC XBRL company facts (and, optionally, daily prices) for the Merton issuers.

Usage:
    python scripts/download_edgar.py --user-agent "Your Name your@email.com"
    python scripts/download_edgar.py --user-agent "..." --prices      # also prices via yfinance

SEC asks every client to send a User-Agent with a name and contact e-mail and to stay under
10 requests per second. Company facts are public domain; price files follow the provider's terms
and are kept out of Git (data/raw/market/ is git-ignored).
"""

from __future__ import annotations

import argparse
import json
import time

import requests

from creditengine.data.edgar import COMPANYFACTS_URL
from creditengine.utils.paths import data_dir

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
TICKERS = ["MSFT", "JNJ", "AAPL", "XOM", "NFLX", "T", "KHC", "F", "BA", "OXY", "HCA", "DAL",
           "CCL", "M", "AAL"]  # fmt: skip
FILE_NAME = {"XOM": "XOM_CIK0000034088"}  # matches run_merton.FACTS_FILE


def cik_map(headers: dict[str, str]) -> dict[str, int]:
    rows = requests.get(TICKERS_URL, headers=headers, timeout=30).json().values()
    return {row["ticker"].upper(): int(row["cik_str"]) for row in rows}


def download_facts(tickers: list[str], user_agent: str) -> None:
    headers = {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}
    ciks = cik_map(headers)
    out = data_dir("raw", "sec_edgar", "companyfacts")
    out.mkdir(parents=True, exist_ok=True)
    for t in tickers:
        if t not in ciks:
            print(f"fail {t:6s} no CIK found")
            continue
        resp = requests.get(COMPANYFACTS_URL.format(cik=ciks[t]), headers=headers, timeout=60)
        if resp.status_code != 200:
            print(f"fail {t:6s} HTTP {resp.status_code}")
            continue
        path = out / f"{FILE_NAME.get(t, t)}.json"
        path.write_text(json.dumps(resp.json()), encoding="utf-8")
        print(f"ok   {t:6s} CIK {ciks[t]:010d} -> {path}")
        time.sleep(0.15)  # stay well under SEC's rate limit


def download_prices(tickers: list[str], period: str = "2y") -> None:
    try:
        import yfinance as yf
    except ImportError:
        print("yfinance not installed: pip install yfinance")
        return
    out = data_dir("raw", "market", "prices")
    out.mkdir(parents=True, exist_ok=True)
    for t in tickers:
        hist = yf.Ticker(t).history(period=period, auto_adjust=False)
        if hist.empty:
            print(f"fail {t:6s} no prices")
            continue
        frame = hist[["Close"]].rename(columns={"Close": "close"})
        frame.index = frame.index.tz_localize(None).normalize()
        frame.index.name = "date"
        frame.to_csv(out / f"{t}.csv")
        print(f"ok   {t:6s} {len(frame)} days -> {out / f'{t}.csv'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-agent", required=True, help='e.g. "Jane Doe jane@example.com"')
    parser.add_argument("--tickers", nargs="*", default=TICKERS)
    parser.add_argument("--prices", action="store_true", help="also download prices (yfinance)")
    args = parser.parse_args()
    download_facts([t.upper() for t in args.tickers], args.user_agent)
    if args.prices:
        download_prices([t.upper() for t in args.tickers])


if __name__ == "__main__":
    main()
