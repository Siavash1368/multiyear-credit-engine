# Validation plan and results

Results come from `scripts/run_simulation.py`, `scripts/run_portfolio.py`, `scripts/run_validation.py`
and `scripts/run_merton.py`; full tables are in `reports/summary.md` and `reports/validation_summary.md`.

| ID | Test | What it checks | Acceptance criterion | Where | Result (v0.2) |
|---|---|---|---|---|---|
| V-01 | Vasicek closed form | Engine one-year default fraction (1,000 'B' issuers, ρ = 0.15) vs analytical quantiles | Within 6% at q ≤ 0.99 | `tests/unit/test_validation.py`, `run_simulation.py` | ✅ q99.5: 18.1% engine vs 18.0% closed form |
| V-02 | One-year migration replication | Simulated migration frequencies vs matrix rows | Within 0.3 pp per cell (200k draws) | `tests/unit/test_migration.py` | ✅ Pass |
| V-03 | Multi-year migration | Simulation vs Pⁿ vs S&P cumulative default rates | φ = 0: simulation equals Pⁿ within MC error | `tests/unit/test_simulation.py` | ✅ Engine check passes. Finding below |
| V-04 | Cycle parameter recovery | Fit recovers ρ and φ on synthetic data | ρ within 3%, φ within 0.02 | `tests/unit/test_cycle.py` | ✅ Pass |
| V-05 | Correlated backtest | Annual default rates 2000–2025 inside walk-forward 95% Vasicek bands (parameters fit only on earlier years) vs independent binomial bands | About 5% outside; far fewer breaks than the independent band | `validation/backtest.py`, `run_validation.py` | ✅ SG 0 of 26 outside (independent band: 14 of 26). B 3 of 26 (independent: 21). ⚠ BB 7 of 26, 5 of them zero-default years (L-10) |
| V-06 | Sensitivity (tornado) | ES and RBC response to PD, ρ, φ, LGD, LGD cycle link, copula, sector structure | Signs as expected; drivers ranked | `validation/sensitivity.py` | ✅ ES: LGD cycle +67%, t copula +66%, φ −36%/+32%, sector β −31%, ρ −20%/+23%, LGD −15%/+21%, PD −10%/+9% |
| V-07 | Convergence | Spread of EL, VaR, ES across seeds and path counts; bootstrap standard errors | ES s.e. < 3% of ES at the production path count | `validation/convergence.py` | ✅ 20,000 paths: ES 107.0m, bootstrap s.e. 3.0m (2.8%). Importance sampling cuts the tail-probability s.e. 6.8× |
| V-08 | Merton benchmark | Distance to default on 15 listed issuers vs their ratings | Spearman rank correlation > 0.6 | `run_merton.py` | ✅ Spearman 0.90. Ford lowest DD among BBB names (captive finance arm). Raw N(−DD) too low for IG (L-11) |
| V-09 | Stress replay | Implied-factor paths of 2000–04 and 2008–12 replayed through the whole book | Losses above base for a severe path | `run_portfolio.py` | ✅ 2000–04: 23.4m vs 10.8m base. 2008–12: 10.7m (one bad year, then fast recovery in the S&P implied factor) |
| V-10 | Tranche conservation and closed form | Tranche losses sum to pool loss; simulated tranche EL vs large-pool formula | Exact sum; EL within 2% relative | `tests/unit/test_structured.py`, `run_validation.py` | ✅ e.g. [3%, 7%]: 4.00% simulated vs 4.05% closed form |
| V-11 | Capital hand-check | RBC at t = 0 equals a hand calculation | Exact | `tests/unit/test_capital.py` | ✅ Pass |
| V-12 | Commercial mortgage checks | DSCR/LTV → CM1–CM5 matches the NAIC grid; balloon default vs Merton closed form | All grid cells; PD within MC error | `tests/unit/test_cre.py`, `run_validation.py` | ✅ 14 grid cells pass; balloon PD 7.82% simulated vs 7.81% closed form |
| V-13 | Cycle factor vs economy | Implied Z vs public proxies | Negative correlation | `run_validation.py` | ✅ Business-loan charge-offs −0.64; recession share −0.33; Baa–Aaa spread −0.27 |

## V-03 finding

| Rating | 5-year S&P published | 5-year Pⁿ | 5-year simulated (φ = 0.5) |
|---|---|---|---|
| A | 0.38% | 0.35% | 0.43% |
| BBB | 1.33% | 1.23% | 1.50% |
| BB | 5.59% | 5.83% | 6.54% |
| B | 15.34% | 21.93% | 22.30% |

1. **Markov gap:** Pⁿ overstates speculative-grade default (B: 21.9% vs 15.3% at year 5). Reasons: non-Markov rating behaviour, and the pro-rata NR adjustment raises the one-year B default rate from 2.87% to 3.28%.
2. **Cycle effect:** a persistent cycle (φ > 0) raises multi-year default rates above Pⁿ, because bad years cluster. The average matrix already contains past cycles, so v0.3 will calibrate a through-the-cycle matrix so that the simulated average matches the published rates (L-01, L-02).

## Ongoing monitoring (proposed)

| Metric | Trigger | Action |
|---|---|---|
| Annual default rate vs Vasicek band | Outside the 95% band two years in a row | Re-fit ρ and φ |
| Implied Z this year | Below −1.5 | Run the stress replay and refresh the capital path |
| ES contribution vs limit | Above 90% (review) or 100% (breach) | Escalate; test a transfer of risk |
| Break-even vs market spread | Cushion below zero for a rating bucket | Review new purchases in that bucket |
| ES standard error | Above 3% of ES | Increase paths or use importance sampling |
