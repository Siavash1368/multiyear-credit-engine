# Scripts

Command-line entry points. Each wraps engine functions; no model logic lives here.
Run from the repository root. Outputs go to `reports/` (figures and summaries committed; CSV tables not).

| Script | Purpose | Needs |
|---|---|---|
| `calibrate.py` | Fit (PD, ρ) per rating from annual default rates; implied cycle factor; persistence φ | S&P tables in `data/external/` |
| `run_simulation.py` | Multi-year simulation of the bond book: loss summary, RBC path, Vasicek and cumulative-PD checks | S&P matrix |
| `run_portfolio.py` | Whole book (bonds, mortgages, structured): losses, ES contributions, RBC path, tranches, pricing, limits, stress replays → `reports/summary.md` | S&P matrix; FRED spreads for pricing (optional) |
| `run_validation.py` | Backtest bands, cycle vs public proxies, convergence, importance sampling, tornado, closed-form checks → `reports/validation_summary.md` | S&P tables; FRED series |
| `run_merton.py` | Distance to default for listed issuers vs ratings | SEC company facts and price files |
| `download_fred.py` | Download FRED series listed in `data/raw/MANIFEST.md` into `data/raw/fred/` | Internet |
| `download_edgar.py` | Download SEC company facts (User-Agent header required) | Internet |
| `build_interim.py` | Build `data/interim/` from `data/raw/` and `data/external/` | Raw files |
| `make_report.py` | Run calibrate → run_simulation → run_portfolio → run_validation in order | All of the above |

```bash
python scripts/download_fred.py
python scripts/make_report.py            # everything, in order
python scripts/run_portfolio.py          # whole book only
```
