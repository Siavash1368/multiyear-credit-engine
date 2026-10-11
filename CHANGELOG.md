# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [0.2.0] - 2026-10-11

### Added
- **Whole insurer book** (`simulation.portfolio.simulate_book`, `assets.book.load_book`): corporate bonds, commercial mortgages and structured tranches on one shared economy (global AR(1) cycle plus asset-class factors), USD 1bn stylised general account.
- **Commercial mortgages** (`assets.cre`): property value and NOI paths, DSCR/LTV, double-trigger term default, balloon refinance default, prepayment, collateral-shortfall loss, NAIC CM category each year, balloon closed form.
- **Structured assets** (`assets.structured`): tranche loss from pool loss, capital-structure checks, tranche table, large-pool closed form, correlation sensitivity.
- **Challengers** in `simulation.engine`: cycle-linked LGD (A-13), Student-t copula (A-10), sector factors (A-11), antithetic draws, externally supplied factor paths (stress replays), issuer-level loss output.
- `simulation.sampling`: factor paths, class factors, t mapping, Sobol normals, importance sampling for the tail.
- **Capital**: Euler ES and variance contributions (`capital.allocation`), break-even spread and RAROC (`capital.pricing`), limit utilisation and risk-transfer test (`capital.limits`).
- **Validation**: walk-forward Vasicek and binomial backtest bands (`validation.backtest`), bootstrap and seed convergence (`validation.convergence`), tornado (`validation.sensitivity`).
- **Data**: FRED loader and downloader (`data.fred`), SEC XBRL company facts and Merton inputs (`data.edgar`).
- **Merton on listed issuers** (`scripts/run_merton.py`): distance to default for 15 issuers vs ratings.
- Scripts `run_portfolio.py`, `run_validation.py`, `run_merton.py`, `download_fred.py`, `build_interim.py`, `make_report.py`; generated `reports/summary.md` and `reports/validation_summary.md`; six new figures.
- GitHub Actions CI (ruff + pytest on Python 3.11 and 3.12).
- Documentation: model scope, data dictionary, ten methodology notes, assumption register A-01–A-15, limitations L-01–L-14, validation results V-01–V-13 and monitoring triggers.
- 94 tests (90 run without the licensed S&P files).

### Changed
- Version 0.2.0; README rewritten around whole-book results.
- `BondPortfolio.stylised` accepts an optional sector count; the v0.1 book is unchanged.

## [0.1.0] - 2026-10-10

### Added
- Data loaders for the S&P 2025 study tables (one-year matrix with pro-rata NR removal, cumulative and annual default rates) and Academy/NAIC C-1 bond factors with the portfolio adjustment.
- `models.cycle`: one-factor conditional PD, implied factor, Basel IRB correlation, closed-form Vasicek fit of (PD, ρ), AR(1) persistence fit, AR(1) factor paths.
- `models.migration`: CreditMetrics thresholds, migration step, cycle-conditional matrices, matrix-power cumulative PDs, generator with Israel-Rosenthal-Wei fix.
- `models.merton`: distance to default, PD, asset value and volatility from equity, KMV default point.
- `models.recovery`: beta LGD by moments.
- `simulation`: multi-year Monte Carlo for a bond book (migration, default, LGD, maturity run-off); EL, VaR, ES; simulated cumulative default rates.
- `capital.rbc`: required C-1 bond RBC per path and year.
- `validation.closed_form`: Vasicek distribution and quantiles; comparison with published cumulative default rates.
- Scripts `calibrate.py` and `run_simulation.py`; three README figures.
- 47 tests (unit and integration); assumption register, validation results and limitations filled in for v0.1.

## [0.0.1] - 2026-10-09

### Added
- Repository skeleton: package layout, notebooks NB01–NB12, configuration, documentation templates, data manifest.
