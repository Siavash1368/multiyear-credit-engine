# Structured assets: pool loss to tranche loss

**References:** Bluhm §8.1, §8.3

## 1. Intuition
A tranche is a slice of a pool's losses. The equity slice takes the first losses; senior slices are hit only when the pool loses more than the subordination beneath them. Because a senior tranche only loses in a deep, economy-wide bad state, it behaves like a bet on the economy: it is rarely hit, but when it is, it is hit together with everything else in the book. That is why a thin, mezzanine-like tranche can carry a large share of tail capital while its rating-based RBC is tiny.

## 2. Model
Pool cumulative loss rate *L* (simulated with the bond engine, same economy). Tranche $[a, d]$:

$$\text{TL}(L) = \frac{(L-a)^+ - (L-d)^+}{d-a}$$

Large homogeneous pool closed form (validation):

$$\mathbb E[\text{TL}] = \frac{1}{d-a}\int \Big[(\text{LGD}\cdot \text{PD}(z) - a)^+ - (\text{LGD}\cdot \text{PD}(z) - d)^+\Big]\,\phi(z)\,dz$$

**Correlation:** raising ρ leaves pool EL unchanged but moves expected loss from the equity tranche to the senior tranches.

## 3. Calibration
Pool: 200 obligors (BB 30%, B 65%, CCC 5%), 7-year maturity, ρ = 0.15, LGD 40%/25%. Tranches: equity 0–13%, BB 13–17%, BBB 17–21%, A 21–25%, AA 25–30%, AAA 30–100% (attachments set from pool-loss quantiles). Held: AAA $100m, AA $40m, A $20m (A-08, A-15). Pool factor β = 1.0.

## 4. Implementation
- `assets.structured`: `tranche_loss`, `Tranche`, `capital_structure`, `tranche_table`, `large_pool_tranche_el`, `correlation_sensitivity`.
- `simulation.portfolio.StructuredHolding`; config `configs/portfolios/structured.yaml`.

## 5. Checks
- V-10: tranche losses sum to pool loss; simulated EL vs large-pool formula (4.00% vs 4.05% on [3%, 7%]).
- Correlation table in `reports/summary.md`.

## 6. Limitations
- L-09: loss allocation only; no interest waterfall or O/C, I/C tests.
- L-12: NAIC designation fixed at issue.
