"""I/O helpers.

Read and write tables under data/ and reports/ in one place.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_table(path: str | Path, **kwargs) -> pd.DataFrame:
    """Read CSV or Parquet by extension."""
    path = Path(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path, **kwargs)
    return pd.read_csv(path, **kwargs)


def write_table(df: pd.DataFrame, path: str | Path) -> Path:
    """Write CSV or Parquet by extension, creating the folder if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".parquet":
        df.to_parquet(path)
    else:
        df.to_csv(path)
    return path
