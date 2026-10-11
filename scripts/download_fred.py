"""Download all FRED series listed in data/raw/MANIFEST.md into data/raw/fred/.

Usage: python scripts/download_fred.py [--only CORBLACBS BAA ...]

Public data (Federal Reserve Bank of St. Louis). ICE BofA series (BAML*) carry ICE's terms and are
kept out of Git (.gitignore); download them locally.
"""

from __future__ import annotations

import argparse

from creditengine.data import fred


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args()
    ids = args.only or [s for group in fred.SERIES.values() for s in group]
    for series in ids:
        try:
            path = fred.download(series)
            print(f"ok   {series:14s} -> {path}")
        except Exception as exc:  # network or unknown id: report and continue
            print(f"fail {series:14s} {exc}")


if __name__ == "__main__":
    main()
