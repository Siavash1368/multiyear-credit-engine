"""Build data/interim/cycle_annual.csv: one row per year with the credit-cycle evidence.

Columns: S&P annual default rates (BB, B, SG), implied cycle factor Z from single-B, and public
proxies from FRED (business-loan charge-offs, CRE charge-offs, Baa-Aaa spread, unemployment,
recession share). Usage: python scripts/build_interim.py
"""

from __future__ import annotations

from creditengine.data import fred
from creditengine.data.rating_agency import load_annual_default_rates
from creditengine.models.cycle import fit_vasicek, implied_factor
from creditengine.utils.paths import data_dir


def main() -> None:
    rates = load_annual_default_rates()[["BB", "B", "SG"]]
    p, rho = fit_vasicek(rates["B"][rates["B"] > 0].to_numpy())
    frame = rates.copy()
    frame["implied_z"] = implied_factor(p, rho, rates["B"].clip(lower=1e-4).to_numpy())
    proxies = {
        "chargeoff_business_loans": ("CORBLACBS", "mean"),
        "chargeoff_cre": ("CORCREXFACBS", "mean"),
        "delinquency_cre": ("DRCRELEXFACBS", "mean"),
        "unemployment": ("UNRATE", "mean"),
        "recession_share": ("USREC", "mean"),
    }
    for name, (series, how) in proxies.items():
        try:
            frame[name] = fred.annual(fred.load(series), how)
        except FileNotFoundError:
            print(f"missing {series}; run scripts/download_fred.py")
    try:
        frame["baa_minus_aaa"] = fred.annual(fred.load("BAA")) - fred.annual(fred.load("AAA"))
    except FileNotFoundError:
        pass
    out = data_dir("interim", "cycle_annual.csv")
    frame.to_csv(out)
    print(f"wrote {out} ({len(frame)} years)")


if __name__ == "__main__":
    main()
