"""FRED access.

Download and load FRED series listed in data/raw/MANIFEST.md (public data, St. Louis Fed).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from creditengine.utils.paths import data_dir

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"

SERIES = {
    "credit_cycle": ["CORBLACBS", "DRBLACBS", "CORCACBS"],
    "macro": ["USREC", "UNRATE", "GDPC1", "NFCI"],
    "rates": ["DGS1", "DGS5", "DGS10", "T10Y2Y"],
    "spreads": [
        "AAA",
        "BAA",
        "AAA10Y",
        "BAA10Y",
        "BAMLC0A0CM",
        "BAMLC0A1CAAA",
        "BAMLC0A2CAA",
        "BAMLC0A3CA",
        "BAMLC0A4CBBB",
        "BAMLH0A0HYM2",
        "BAMLH0A1HYBB",
        "BAMLH0A2HYB",
        "BAMLH0A3HYC",
    ],
    "commercial_real_estate": ["DRCRELEXFACBS", "CORCREXFACBS", "COMREPUSQ159N"],
}


def series_path(series: str) -> Path:
    """Local CSV path for a series, from the folder it belongs to in SERIES."""
    for folder, ids in SERIES.items():
        if series in ids:
            return data_dir("raw", "fred", folder, f"{series}.csv")
    raise KeyError(f"{series} is not in the FRED manifest")


def download(series: str, timeout: int = 30) -> Path:
    """Download one series to data/raw/fred/<folder>/<series>.csv and return the path."""
    import requests

    path = series_path(series)
    path.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(URL.format(series=series), timeout=timeout)
    resp.raise_for_status()
    path.write_bytes(resp.content)
    return path


def load(series: str, path: str | Path | None = None) -> pd.Series:
    """Load a downloaded series as a float Series indexed by date ('.' = missing)."""
    frame = pd.read_csv(path or series_path(series))
    date_col = frame.columns[0]
    values = pd.to_numeric(frame[frame.columns[1]], errors="coerce")
    return pd.Series(values.to_numpy(), index=pd.to_datetime(frame[date_col]), name=series).dropna()


def annual(series: pd.Series, how: str = "mean") -> pd.Series:
    """Calendar-year aggregate (mean, max or last), indexed by integer year."""
    grouped = series.groupby(series.index.year)
    out = getattr(grouped, how)()
    out.index.name = "year"
    return out
