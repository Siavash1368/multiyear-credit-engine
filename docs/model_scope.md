# Model scope

## 1. Purpose
A multi-year, Merton-approach credit risk model for an insurer's general-account credit book. It supports three decisions:

| Decision | Question | Output used |
|---|---|---|
| Underwriting | Does this asset's spread pay for its expected loss and the capital it uses? | Break-even spread, marginal ES capital, RAROC |
| Risk limits and allocation | Which asset classes, sectors and ratings drive the tail, and are they within appetite? | ES capital contributions, limit utilisation |
| Capital planning and stress | How do losses and statutory capital develop over several years, in a base and a stressed cycle? | Loss distribution by year, RBC path, scenario replays |

## 2. Intended use and users
| Use | User | Output consumed |
|---|---|---|
| Portfolio risk view | Investment risk, asset managers | EL, VaR, ES by year and asset class |
| Capital view | Actuarial / capital management | RBC path (median and tail), EC |
| Pricing support | Specialty finance underwriting; later product pricing | Break-even spreads, capital cost |
| Model governance | Model validation | Validation suite, assumption and limitation registers |

This repository is a public-data prototype on stylised portfolios. It is not calibrated to, and does not describe, any company's holdings or models.

## 3. In scope
| Item | Detail |
|---|---|
| Asset classes | Corporate bonds; commercial mortgage loans; structured assets (tranches of a collateral pool) |
| Risk types | Default; rating migration; LGD (optionally linked to the cycle); CRE value and income risk; prepayment and balloon refinance risk |
| Dependence | One persistent global credit cycle; asset-class and sector factors that share it; Gaussian copula (champion) and Student-t copula (challenger) |
| Horizon | Five years, annual steps |
| Measures | EL, standard deviation, VaR and ES (95%, 99%, 99.5%); economic capital (ES − EL); NAIC RBC path; capital contributions; break-even spreads |
| Capital frameworks | NAIC Life RBC C-1: bond designations with the portfolio adjustment; CM1–CM7 for commercial mortgages; tranche designation for structured |

## 4. Out of scope
| Item | Reason | Planned |
|---|---|---|
| Spread-driven mark-to-market | Statutory, held-to-maturity view first | Later |
| Interest-rate risk and ALM | Credit engine feeds ALM (losses, capital); does not replace it | — |
| Interest waterfall and coverage tests (O/C, I/C) for structured deals | Loss-allocation view first (L-09) | v0.3 |
| Reinvestment of maturing assets | Static book (L-06) | v0.3 |
| Tranche rating migration | Tranche designation held fixed (L-12) | v0.3 |
| Proprietary data | Public-data prototype (A-09) | — |

## 5. Model outputs
| Output | Script | File |
|---|---|---|
| Bond book: loss summary, RBC path, closed-form checks | `run_simulation.py` | `reports/tables/loss_summary.csv`, `rbc_path.csv`, `validation_*.csv` |
| Whole book: losses by class, contributions, capital, tranches, pricing, limits, stress | `run_portfolio.py` | `reports/summary.md`, `reports/tables/book_*.csv` |
| Validation suite | `run_validation.py` | `reports/validation_summary.md` |
| Merton on listed issuers | `run_merton.py` | `reports/tables/merton_listed.csv` |

## 6. Model owner and change log
| Version | Date | Change | Author |
|---|---|---|---|
| 0.1.0 | 2026-10-10 | Corporate bond engine, RBC path, closed-form validation | Siavash Feizi |
| 0.2.0 | 2026-10-11 | Commercial mortgages, structured tranches, whole book on one economy, allocation, pricing, limits, stress, validation suite, Merton on listed issuers | Siavash Feizi |
