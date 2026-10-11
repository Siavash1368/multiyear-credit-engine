"""Run every result-producing script in order and refresh reports/.

Usage: python scripts/make_report.py
Order: calibrate -> bond book (v0.1) -> whole book -> validation.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

SCRIPTS = ["calibrate.py", "run_simulation.py", "run_portfolio.py", "run_validation.py"]


def main() -> None:
    here = Path(__file__).parent
    for name in SCRIPTS:
        print(f"\n===== {name} =====")
        sys.argv = [name]
        runpy.run_path(str(here / name), run_name="__main__")


if __name__ == "__main__":
    main()
