# Recovery and LGD linked to the cycle

**References:** Altman, Brady, Resti, Sironi (2005)

## 1. Intuition
How much is lost when a borrower defaults is itself uncertain, and it is worse in bad years: many firms sell assets at once, so prices and recoveries fall exactly when defaults rise. Ignoring this link understates the tail even when the average loss is right.

## 2. Model
Beta LGD by moments (mean *m*, standard deviation *s*):

$$k = \frac{m(1-m)}{s^2} - 1, \qquad \text{LGD} \sim \text{Beta}(m k,\ (1-m) k)$$

Cycle link (A-13):

$$m(Z) = N(a - bZ), \qquad a = N^{-1}(m)\sqrt{1+b^2}$$

The choice of *a* keeps $\mathbb E_Z[m(Z)] = m$, so b changes only how losses move with the cycle, not the long-run average. b = 0 gives the independent model. The standard deviation is capped at 90% of the largest value a beta with mean $m(Z)$ allows.

## 3. Calibration
- Bonds: mean 60%, std 25% (senior unsecured, A-04).
- Structured collateral (senior loans): mean 40%, std 25%.
- Commercial mortgages: loss from collateral, not a beta draw (see 07).
- Base b = 0; challenger b = 1.

## 4. Implementation
- `models.recovery`: `beta_parameters`, `sample_lgd`, `cycle_mean_lgd`, `sample_lgd_conditional`.
- `SimulationSettings(lgd_cycle=b)`; `BookSettings(lgd_cycle=b)`.

## 5. Checks
- `tests/unit/test_recovery.py`: moments; cycle mean averages back to *m* over Z ~ N(0,1).
- V-06: b = 1 raises EL by 35% and ES by 67% — the single largest driver of tail loss.

## 6. Limitations
- L-04: base case keeps b = 0; the challenger shows the size of the gap.
- Seniority-level recovery table not yet loaded.
