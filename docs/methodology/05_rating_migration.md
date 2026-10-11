# Rating migration: thresholds, matrix powers, generators

**References:** Bluhm §6.3, §8.4.1; CreditMetrics (1997)

## 1. Intuition
Most capital is lost not through defaults but through downgrades: a BBB bond falling to BB moves into a much higher RBC factor. The engine therefore tracks every rating each year, not just default. The same asset return that decides default also decides the new rating, by cutting the normal distribution into slices whose sizes match the transition matrix row.

## 2. Model
For a bond rated *r*, with states ordered from AAA (best) to D (worst):

$$c_{r,k} = N^{-1}\big(P(\text{end in state } k \text{ or worse})\big) = N^{-1}\Big(\sum_{j \ge k} p_{rj}\Big)$$

New state = *k* such that $c_{r,k+1} < X_i \le c_{r,k}$; the lowest slice $X_i \le c_{r,D} = N^{-1}(\text{PD}_r)$ is default. Given the cycle *Z*, the conditional matrix is

$$p_{rk}(Z) = N\left(\frac{c_{r,k} - \sqrt\rho Z}{\sqrt{1-\rho}}\right) - N\left(\frac{c_{r,k+1} - \sqrt\rho Z}{\sqrt{1-\rho}}\right)$$

Multi-year without cycle: $P^{(n)} = P^n$; the D column gives cumulative PDs. Generator $Q = \log P$ (with negative off-diagonals set to zero) gives $P(t) = e^{Qt}$ for fractional years.

Withdrawn ratings (NR) are removed pro rata: $\tilde p_{rk} = p_{rk} / (1 - p_{r,\text{NR}})$.

## 3. Calibration
S&P global corporate average one-year matrix, 1981–2025 (A-01).

## 4. Implementation
- `models.migration`: `thresholds`, `migrate`, `conditional_matrix`, `cumulative_default_from_matrix`, `generator`, `matrix_at`.
- `data.rating_agency`: loads the matrix and removes NR.

## 5. Checks
- V-02: simulated one-year migration matches matrix rows within 0.3 pp.
- V-03: φ = 0 simulation equals $P^n$; comparison with published cumulative rates.

## 6. Limitations
- L-01: Markov assumption overstates speculative-grade multi-year default (B 5-year 21.9% vs 15.3%).
- L-08: letter categories only.
