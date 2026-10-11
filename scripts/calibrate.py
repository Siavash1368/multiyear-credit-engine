"""Calibrate cycle, migration and recovery parameters into data/processed/.

Usage: python scripts/calibrate.py --config configs/base.yaml

v0.1: fits (PD, rho) per rating from S&P annual default rates (closed-form Vasicek MLE),
the implied cycle factor Z_t from the 'B' series, and its AR(1) persistence phi.
Writes reports/tables/cycle_calibration.csv and reports/tables/implied_factor.csv.
"""

from __future__ import annotations

import pandas as pd

from creditengine.data.rating_agency import load_annual_default_rates
from creditengine.models.cycle import (
    basel_correlation,
    fit_persistence,
    fit_vasicek,
    implied_factor,
)
from creditengine.utils.paths import reports_dir


def main() -> None:
    rates = load_annual_default_rates()
    rows = []
    for col in ["BB", "B", "CCC/C", "SG"]:
        series = rates[col][rates[col] > 0]  # zero years have no probit; dropped (noted in A-02)
        pd_hat, rho_hat = fit_vasicek(series.to_numpy())
        rows.append(
            {
                "series": col,
                "years_used": len(series),
                "pd_fitted": pd_hat,
                "rho_fitted": rho_hat,
                "rho_basel": float(basel_correlation(pd_hat)),
            }
        )
    table = pd.DataFrame(rows).set_index("series")

    pd_b, rho_b = table.loc["B", ["pd_fitted", "rho_fitted"]]
    z = pd.Series(implied_factor(pd_b, rho_b, rates["B"].to_numpy()), index=rates.index, name="z")
    table["phi_fitted_from_B"] = fit_persistence(z.to_numpy())

    out = reports_dir("tables")
    table.to_csv(out / "cycle_calibration.csv")
    z.to_csv(out / "implied_factor.csv")
    print(table.round(4).to_string())
    print("\nWorst implied-factor years:\n", z.nsmallest(5).round(2).to_string())


if __name__ == "__main__":
    main()
