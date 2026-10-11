# Data dictionary

## Rating-agency tables (`data/external/`, local only)
| File | Field | Type | Unit | Description |
|---|---|---|---|---|
| `transition_matrix_1y.csv` | `from` | str | | Rating at the start of the year (AAA … CCC/C) |
| | `AAA` … `CCC/C`, `D` | float | % | Share of issuers in each rating one year later |
| | `NR` | float | % | Share whose rating was withdrawn (removed pro rata in code, A-01) |
| `cumulative_default_rates.csv` | `rating` | str | | Starting rating |
| | `1` … `15` | float | % | Average cumulative default rate after n years |
| `default_rates_annual.csv` | `year` | int | | Calendar year 1981–2025 |
| | `AAA` … `CCC/C` | float | % | Annual issuer default rate by rating |
| | `SG` | float | % | Speculative-grade default rate |

## NAIC and Academy tables (`data/external/`)
| File | Field | Type | Unit | Description |
|---|---|---|---|---|
| `naic_bond_factors.csv` | `moodys` | str | | Moody's notch (Aaa … Caa3, Default) |
| | `naic_designation` | str | | NAIC designation 1.A … 6 |
| | `factor_pct` | float | % | Pre-tax C-1 base factor |
| `naic_portfolio_adjustment.csv` | `tier`, `issuers_in_tier`, `factor` | int, int, float | | Issuer-count tiers and multipliers |
| `rating_scale_map.csv` | `sp_category`, `moodys_notch`, `naic_designation` | str | | Letter category → middle notch → designation (A-06) |
| CM1–CM7 grid | in code: `assets.cre.cm_category`, `CM_FACTORS` | | | NAIC Life RBC instructions, Figures 4 and 5; factors 0.90%, 1.75%, 3.00%, 5.00%, 7.50%, 18%, 23% |

## FRED series (`data/raw/fred/<folder>/<ID>.csv`)
| Field | Type | Unit | Description |
|---|---|---|---|
| `observation_date` | date | | Observation date (daily, weekly, monthly or quarterly) |
| `<SERIES_ID>` | float | % or index | Value; `.` = missing. Series list in `data.fred.SERIES` and `data/raw/MANIFEST.md` |

## Interim panel (`data/interim/cycle_annual.csv`)
| Field | Unit | Description |
|---|---|---|
| `year` | | Calendar year |
| `BB`, `B`, `SG` | decimal | Annual default rates |
| `implied_z` | std. normal | Cycle factor implied by the single-B default rate |
| `chargeoff_business_loans`, `chargeoff_cre`, `delinquency_cre` | % | Bank charge-off and delinquency rates (annual mean) |
| `unemployment`, `recession_share` | %, share | Unemployment rate; share of months in NBER recession |
| `baa_minus_aaa` | % | Moody's Baa minus Aaa yield |

## SEC company facts and prices (Merton inputs, local only)
| Source | Field | Description |
|---|---|---|
| `data/raw/sec_edgar/companyfacts/<T>.json` | `dei:EntityCommonStockSharesOutstanding` | Shares outstanding (latest) |
| | `us-gaap:Liabilities`, `us-gaap:LiabilitiesCurrent` | Total and current liabilities (latest 10-K/10-Q) |
| `data/raw/market/prices/<T>.csv` | `date`, `close`, `adj_close`, `volume` | Daily prices |

## Simulation outputs
| Object | Shape | Description |
|---|---|---|
| `SimulationResult.losses` | paths × years | Bond loss booked each year (USD) |
| `SimulationResult.ratings` | paths × (years+1) × issuers | Rating state index; 7 = default |
| `SimulationResult.issuer_loss` | paths × issuers | Loss over the horizon by issuer |
| `CREResult.category` | paths × (years+1) × loans | CM category 1–5; 0 once the loan has left |
| `BookResult.asset_loss` | paths × assets | Horizon loss by asset across all classes (contributions) |
| `BookResult.rbc_by_class` | class → paths × (years+1) | Required RBC path |
