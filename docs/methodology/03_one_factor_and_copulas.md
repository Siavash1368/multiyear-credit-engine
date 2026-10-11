# One-factor model, Gaussian and t copulas

**References:** Bluhm §2.5.1, §2.6; Vasicek (2002); Li (2000)

## 1. Intuition
Defaults cluster because firms share an economy. Each obligor's asset return mixes one common factor *Z* (the state of the economy) with its own noise. In a bad year (low *Z*) every firm is closer to its threshold, so many default together. The **copula** decides how strongly extreme moves line up; a Student-t copula adds joint crashes that the Gaussian one does not have.

## 2. Model
$$X_i = \sqrt{\rho}\,Z + \sqrt{1-\rho}\,\varepsilon_i, \qquad Z,\varepsilon_i \sim N(0,1)\ \text{i.i.d.}$$

$$D_i = \mathbf 1\{X_i < c_i\}, \qquad c_i = N^{-1}(\text{PD}_i)$$

$$\text{PD}_i(Z) = N\!\left(\frac{N^{-1}(\text{PD}_i) - \sqrt{\rho}\,Z}{\sqrt{1-\rho}}\right)$$

Large homogeneous pool (Vasicek): the default fraction equals $\text{PD}(Z)$, so

$$P(\text{DR} \le x) = N\!\left(\frac{\sqrt{1-\rho}\,N^{-1}(x) - N^{-1}(\text{PD})}{\sqrt{\rho}}\right)$$

**Sectors (A-11):** $Z_k = \sqrt{\beta}\,G + \sqrt{1-\beta}\,H_k$; β = 1 is one factor; β < 1 lets sectors diversify.

**t copula (A-10):** $X_i^{t} = X_i / \sqrt{W/\nu}$, $W \sim \chi^2_\nu$ common to all issuers; map back with $\tilde X_i = N^{-1}(t_\nu(X_i^t))$ so each one-year PD is unchanged and only the joint tail changes.

## 3. Calibration
ρ from the Basel IRB corporate formula on each issuer's one-year PD (A-02); cross-check fitted by moments from S&P annual default rates. ν = 6. Sector β = 0.5 over 8 sectors (challenger).

## 4. Implementation
- `models.cycle.conditional_pd`, `basel_correlation`, `fit_vasicek`.
- `simulation.sampling`: `factor_paths`, `class_factor`, `t_scale`, `t_to_gaussian`.
- `simulation.engine.SimulationSettings(copula="t", t_nu=6, sector_beta=0.5)`.

## 5. Checks
- V-01: engine default fraction vs Vasicek quantile (18.1% vs 18.0% at 99.5%).
- `tests/unit/test_simulation.py`: challengers keep one-year PDs.
- V-06: t copula ES +66% with EL unchanged; sector β = 0.5 ES −31%.

## 6. Limitations
- L-03: base case is Gaussian with one factor (challengers built).
- L-05: ρ fixed at the initial rating.
