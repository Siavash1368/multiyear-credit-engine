# Credit cycle: implied factor, ρ and φ calibration

**References:** Bluhm §2.7, §8.4.5

## 1. Intuition
Bad credit years come in runs: 2001–02, 2008–09. A model that draws a fresh, independent economy every year misses this and understates multi-year tail loss. The engine backs out the economy's state each year from observed default rates, then lets it carry over from one year to the next.

## 2. Model
Implied factor from an observed default rate $\text{DR}_t$ (inverse of the conditional PD):

$$\hat Z_t = \frac{N^{-1}(\text{PD}) - \sqrt{1-\rho} N^{-1}(\text{DR}_t)}{\sqrt{\rho}}$$

AR(1) cycle, stationary with unit variance:

$$Z_t = \varphi Z_{t-1} + \sqrt{1-\varphi^2} \eta_t, \qquad \eta_t \sim N(0,1)$$

Fit of (PD, ρ) by moments of the probit-transformed rates: with $y_t = N^{-1}(\text{DR}_t)$,

$$\text{Var}(y) = \frac{\rho}{1-\rho}, \qquad \mathbb E[y] = \frac{N^{-1}(\text{PD})}{\sqrt{1-\rho}}$$

## 3. Calibration
- Data: S&P annual default rates by rating, 1981–2025 (Table 3), speculative-grade rate (Table 1).
- Fitted ρ: 0.11 (BB), 0.13 (B), 0.12 (CCC/C); years with zero defaults dropped.
- φ = 0.54 from the 'B' implied factor; 0.50 used (A-03).

## 4. Implementation
- `models.cycle`: `implied_factor`, `fit_vasicek`, `fit_persistence`, `simulate_factor_paths`.
- `simulation.sampling.factor_paths` (with optional antithetic draws).
- `scripts/calibrate.py` writes `reports/tables/cycle_calibration.csv` and `implied_factor.csv`.

## 5. Checks
- V-04: synthetic recovery of ρ and φ.
- V-05: walk-forward backtest bands (SG 0 of 26 years outside).
- V-13: implied *Z* vs business-loan charge-offs, correlation −0.64.
- V-09: replays of 2000–04 and 2008–12 implied paths.

## 6. Limitations
- L-02: the average matrix already contains past cycles.
- L-10: zero-default years make the test weak for low-PD ratings.
