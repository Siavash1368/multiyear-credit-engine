# Model documentation

Structure follows common model risk management practice (development documentation). Each section points to the file that holds the detail.

## 1. Executive summary
A multi-year (five-year, annual-step) Monte Carlo credit risk engine for a stylised USD 1bn life-insurer general account: corporate bonds, commercial mortgages and structured tranches on one shared, persistent credit cycle. It produces expected loss, VaR, expected shortfall, economic capital and its allocation, the path of statutory (NAIC RBC) capital, break-even spreads, limit utilisation and stress replays. Key results: [`../README.md`](../README.md) and [`../reports/summary.md`](../reports/summary.md).

## 2. Model purpose and use
Portfolio credit risk measurement, capital planning, risk appetite and limits, asset-allocation and pricing support. See [`model_scope.md`](model_scope.md).

## 3. Model scope
[`model_scope.md`](model_scope.md)

## 4. Data
[`data_dictionary.md`](data_dictionary.md), [`../data/README.md`](../data/README.md), [`../data/raw/MANIFEST.md`](../data/raw/MANIFEST.md)

## 5. Methodology
[`methodology/`](methodology/) — ten notes, from loss measures to simulation design.

## 6. Assumptions
[`assumption_register.md`](assumption_register.md) (A-01 – A-15)

## 7. Implementation
Python package `src/creditengine/` (data → models → assets → simulation → capital → validation → reporting); configuration in `configs/`; entry points in `scripts/`; 94 tests in `tests/`; CI on every push (ruff + pytest). Fixed seeds make every number reproducible.

## 8. Outcomes analysis and validation
[`validation_plan.md`](validation_plan.md) (V-01 – V-13) and [`../reports/validation_summary.md`](../reports/validation_summary.md)

## 9. Limitations and compensating controls
[`limitations.md`](limitations.md) (L-01 – L-14)

## 10. Ongoing monitoring
Triggers and actions: [`validation_plan.md#ongoing-monitoring-proposed`](validation_plan.md#ongoing-monitoring-proposed)

## 11. Change log
[`../CHANGELOG.md`](../CHANGELOG.md); planned work in [`roadmap.md`](roadmap.md)
