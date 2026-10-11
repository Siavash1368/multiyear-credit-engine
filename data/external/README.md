# External reference tables

Small tables entered by hand from published PDFs. Each row below gives the source, the table, and the date entered.

| File | Contents | Source | In Git? |
|---|---|---|---|
| `transition_matrix_1y.csv` | One-year average global corporate transition matrix, 1981–2025, percent, with D and NR columns (NR removed in code) | S&P Global Ratings, *2025 Annual Global Corporate Default and Rating Transition Study* (18 Mar 2026), Table 21 (= Table 33) | No (local only) |
| `cumulative_default_rates.csv` | Average cumulative default rates by rating, years 1–15, percent | Same study, Table 24 | No (local only) |
| `default_rates_annual.csv` | Annual default rates by rating, 1981–2025, percent; `SG` = speculative-grade rate | Same study, Table 3 (ratings) and Table 1 (`SG`) | No (local only) |
| `naic_bond_factors.csv` | Pre-tax C-1 base factors by NAIC designation 1.A–6 (Moody's notch shown); 6 = 30% cap | American Academy of Actuaries C1 Work Group, letter to the NAIC Life RBC (E) Working Group, 11 Mar 2021, Attachment 1 p. 2 ("3.5.2021 Update"), in the LRBCWG materials of 30 Mar 2021 | Yes |
| `naic_portfolio_adjustment.csv` | Portfolio adjustment factors by issuer-count tier | Same letter, Attachment 1 p. 3 ("3.5.2021 Update") | Yes |
| `rating_scale_map.csv` | S&P letter category → representative Moody's notch and NAIC designation (middle notch of each category) | Modelling assumption A-06 | Yes |

Entered: 10 Oct 2026. Checks run on entry: matrix rows sum to 100 ± 0.02; Table 24 year 1 equals the matrix D column; Table 3 minimum, maximum and standard deviation match Table 4.

## Why the S&P files are not in Git

S&P's terms restrict reproduction of its content. The three S&P files stay on your machine (see `.gitignore`).
Without them, the unit tests that need them are skipped and everything else runs on a synthetic matrix.

To rebuild them, download the study (free registration at spglobal.com/ratings) and enter the tables above in the same layout:

```
transition_matrix_1y.csv      from,AAA,AA,A,BBB,BB,B,CCC/C,D,NR      (7 rows, percent)
cumulative_default_rates.csv  rating,1,2,...,15                      (7 rows, percent)
default_rates_annual.csv      year,AAA,AA,A,BBB,BB,B,CCC/C,SG        (1981-2025, percent)
```

## Built into code (no file needed)

| Table | Where | Source |
|---|---|---|
| NAIC CM1–CM7 commercial mortgage factors and DSC/LTV grid | `src/creditengine/assets/cre.py` (`CM_FACTORS`, `cm_category`) | NAIC Life RBC instructions, mortgage experience adjustment (Figures 4 and 5) |

## Planned

| File | Contents | Source | Version |
|---|---|---|---|
| `recovery_rates_by_seniority.csv` | Average recovery by debt seniority | Rating-agency recovery study | v0.3 |
| `naic_clo_factors.csv` | Structured tranche factors (if they differ from bond designations) | NAIC | later |
