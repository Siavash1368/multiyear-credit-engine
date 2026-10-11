"""Paths.

Project root and data directory resolution.
"""

from __future__ import annotations

from pathlib import Path

# src/creditengine/utils/paths.py -> project root is three levels above the package folder
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def project_root() -> Path:
    """Repository root (the folder that holds pyproject.toml)."""
    return PROJECT_ROOT


def data_dir(*parts: str) -> Path:
    """Path under data/, e.g. data_dir("external", "transition_matrix_1y.csv")."""
    return PROJECT_ROOT.joinpath("data", *parts)


def external_file(name: str) -> Path:
    """Path to a hand-entered reference table in data/external/."""
    return data_dir("external", name)


def reports_dir(*parts: str) -> Path:
    """Path under reports/ (created if missing)."""
    path = PROJECT_ROOT.joinpath("reports", *parts)
    path.mkdir(parents=True, exist_ok=True)
    return path
