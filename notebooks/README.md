# Notebooks

Research layer. Each notebook develops one model component, then hands its functions to the engine in `src/creditengine/`.
The engine is complete for v0.2; the notebooks hold the outline, theory and checklist and are being filled in on top of it.

| NB | File | Component | Engine module | Assumptions |
|---|---|---|---|---|
| 01 | `01_data_foundation.ipynb` | Data foundation | `data` | A-01, A-06 |
| 02 | `02_merton_structural_model.ipynb` | Merton structural model | `models.merton`, `data.edgar` | A-12 |
| 03 | `03_credit_cycle.ipynb` | Credit cycle | `models.cycle` | A-02, A-03 |
| 04 | `04_rating_migration.ipynb` | Rating migration | `models.migration` | A-01 |
| 05 | `05_recovery_lgd.ipynb` | Recovery and LGD | `models.recovery` | A-04, A-13 |
| 06 | `06_corporate_bond_portfolio_mc.ipynb` | Corporate bond portfolio Monte Carlo | `simulation`, `assets.corporate` | A-05, A-10, A-11 |
| 07 | `07_commercial_mortgage_loans.ipynb` | Commercial mortgage loans | `assets.cre` | A-07, A-14 |
| 08 | `08_structured_assets.ipynb` | Structured assets | `assets.structured` | A-08, A-15 |
| 09 | `09_capital_pricing_limits.ipynb` | Capital, pricing and limits | `capital` | A-06 |
| 10 | `10_model_validation.ipynb` | Model validation | `validation` | All |
| 11 | `11_assumptions_outputs_reporting.ipynb` | Assumptions, outputs and reporting | `reporting` | All |
| 12 | `12_ml_challenger_optional.ipynb` | ML challenger (optional) | `models.challenger` | A-12 |

## Conventions
- Run notebooks in order; each reads only from `data/` and earlier outputs.
- Outputs are stripped before commit (`nbstripout`).
- Every notebook ends with a validation checklist and the list of functions moved to the engine.
