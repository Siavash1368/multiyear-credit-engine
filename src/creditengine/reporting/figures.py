"""Figures.

Standard charts used across notebooks and reports.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # file output only; no display needed
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def loss_distribution(
    total_loss: np.ndarray, var: float, es: float, path: str | Path, q_label: str = "99.5%"
) -> None:
    """Histogram of the horizon loss with EL, VaR and ES marked (USD millions)."""
    loss = total_loss / 1e6
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(loss, bins=120, color="#4C72B0", alpha=0.85)
    for value, label, style in [
        (loss.mean(), "EL", "-"),
        (var / 1e6, f"VaR {q_label}", "--"),
        (es / 1e6, f"ES {q_label}", ":"),
    ]:
        ax.axvline(value, color="black", linestyle=style, label=f"{label}: {value:,.1f}")
    ax.set_xlabel("Cumulative credit loss over the horizon (USD m)")
    ax.set_ylabel("Number of paths")
    ax.set_title("Multi-year loss distribution")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def capital_path(rbc: np.ndarray, path: str | Path) -> None:
    """Median and percentile bands of required RBC by year (USD millions)."""
    rbc_m = rbc / 1e6
    years = np.arange(rbc.shape[1])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for lo, hi, alpha in [(5, 95, 0.25), (0.5, 99.5, 0.12)]:
        ax.fill_between(
            years,
            np.percentile(rbc_m, lo, axis=0),
            np.percentile(rbc_m, hi, axis=0),
            color="#DD8452",
            alpha=alpha,
            label=f"{lo}th-{hi}th percentile",
        )
    ax.plot(years, np.median(rbc_m, axis=0), color="#DD8452", label="Median")
    ax.set_xlabel("Year")
    ax.set_ylabel("Required C-1 bond RBC (USD m, pre-tax)")
    ax.set_title("Statutory capital path as ratings migrate (book runs off as bonds mature)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def cumulative_pd_check(
    simulated: pd.DataFrame,
    matrix_power: pd.DataFrame,
    published: pd.DataFrame,
    path: str | Path,
    ratings: tuple[str, ...] = ("A", "BBB", "BB", "B"),
) -> None:
    """Cumulative default rates: simulation vs matrix powers vs S&P published averages."""
    fig, axes = plt.subplots(1, len(ratings), figsize=(3.2 * len(ratings), 3.6))
    for ax, r in zip(axes, ratings, strict=True):
        years = simulated.columns
        ax.plot(years, 100 * published.loc[r, years], "k-o", ms=3, label="S&P published")
        ax.plot(years, 100 * matrix_power.loc[r, years], "C1--", label="Matrix power $P^n$")
        ax.plot(years, 100 * simulated.loc[r], "C0:", lw=2, label="Simulation")
        ax.set_title(r)
        ax.set_xlabel("Year")
    axes[0].set_ylabel("Cumulative default rate (%)")
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def contributions(table: pd.DataFrame, path: str | Path, title: str) -> None:
    """Share of exposure, expected loss and ES capital by group (side-by-side bars)."""
    cols = ["exposure %", "EL %", "ES capital %"]
    ax = table[cols].plot.bar(figsize=(8, 4.5), color=["#9AA5B1", "#4C72B0", "#C44E52"], width=0.8)
    ax.set_ylabel("Share of portfolio total (%)")
    ax.set_xlabel("")
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=0)
    ax.legend(["Exposure", "Expected loss", "ES 99.5% capital"])
    fig = ax.get_figure()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def capital_by_class(rbc_by_class: dict[str, np.ndarray], path: str | Path) -> None:
    """Median statutory capital by asset class (stacked) with the total's 99.5th percentile."""
    years = np.arange(next(iter(rbc_by_class.values())).shape[1])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    medians = [np.median(v, axis=0) / 1e6 for v in rbc_by_class.values()]
    ax.stackplot(
        years,
        medians,
        labels=[f"{k} (median)" for k in rbc_by_class],
        alpha=0.75,
        colors=["#4C72B0", "#55A868", "#DD8452"],
    )
    total = sum(rbc_by_class.values()) / 1e6
    ax.plot(years, np.percentile(total, 99.5, axis=0), "k--", label="Total, 99.5th percentile")
    ax.set_xlabel("Year")
    ax.set_ylabel("Required RBC (USD m, pre-tax)")
    ax.set_title("Statutory capital path of the whole book")
    ax.legend(fontsize=8, loc="center right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def tranche_correlation(table: pd.DataFrame, path: str | Path) -> None:
    """Expected tranche loss vs asset correlation (pool expected loss held fixed)."""
    rhos = [float(i.split("=")[1].rstrip("%")) for i in table.index]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for col in [c for c in table.columns if c != "pool EL"]:
        ax.plot(rhos, 100 * table[col], "-o", ms=4, label=col)
    ax.set_yscale("symlog", linthresh=0.1)
    ax.set_xlabel("Asset correlation (%)")
    ax.set_ylabel("Expected loss, share of tranche (%)")
    ax.set_title("Same pool, same expected loss: correlation moves risk from equity to senior")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def tornado(table: pd.DataFrame, output: str, path: str | Path) -> None:
    """Tornado chart: % change of one output when each assumption moves low / high."""
    t = table[table["parameter"] != "base"]
    col = f"{output} %chg"
    pivot = t.pivot_table(index="parameter", columns="side", values=col, aggfunc="first").fillna(
        0.0
    )
    order = (pivot.abs().max(axis=1)).sort_values().index
    pivot = pivot.loc[order]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    y = np.arange(len(pivot))
    ax.barh(y, pivot.get("low", 0.0), color="#4C72B0", label="low")
    ax.barh(y, pivot.get("high", 0.0), color="#C44E52", label="high")
    ax.set_yticks(y, pivot.index)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel(f"Change in {output} (%)")
    ax.set_title(f"Which assumption drives {output}?")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def backtest_bands(walk: pd.DataFrame, path: str | Path, title: str) -> None:
    """Observed default rate against the out-of-sample correlated (Vasicek) 95% band."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    yrs = walk.index
    ax.fill_between(
        yrs,
        100 * walk["lo"],
        100 * walk["hi"],
        color="#4C72B0",
        alpha=0.2,
        label="Correlated 95% band (fitted on earlier years)",
    )
    inside = walk["inside"].astype(bool)
    ax.plot(yrs[inside], 100 * walk["default_rate"][inside], "ko", ms=4, label="Observed, inside")
    ax.plot(
        yrs[~inside], 100 * walk["default_rate"][~inside], "rx", ms=7, label="Observed, outside"
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual default rate (%)")
    ax.set_title(title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
