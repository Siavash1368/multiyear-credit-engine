# Monte Carlo design and variance reduction

**References:** Bluhm §2.8.1–2.8.2, §2.8.6

## 1. Intuition
Capital lives in the far tail, where few simulated paths land. The design aims for (1) reproducibility — same seed, same answer; (2) a known error on every tail number; and (3) fewer wasted paths by pushing simulations toward the bad states that matter.

## 2. Model
One path = one five-year history:

1. Global cycle $G_t$ (AR(1)); class factors $Z_k$ from $G$ (A-11, A-14).
2. For each year and asset: asset return → new rating or default (05); mortgages: value and NOI → default or prepay (07).
3. LGD drawn given the cycle (06); losses accumulated; RBC recomputed (09).

Path count *n* = 20,000 by default.

**Conditional independence:** given *Z*, defaults are independent, so the pool's conditional distribution is known; this gives the closed-form checks.

**Importance sampling:** draw $Z \sim N(\mu, 1)$ with μ < 0 and weight each path by

$$w(Z) = \frac{\phi(Z)}{\phi(Z-\mu)} = e^{-\mu Z + \mu^2/2}$$

**Antithetic draws** (optional): pair *Z* with −*Z*. **Sobol** quasi-random normals are available for low-dimensional checks.

**Errors:** bootstrap standard errors of EL, VaR and ES; seed study across path counts.

## 3. Calibration
Seed 2026 (configs); n = 20,000; q = 99.5%; IS shift μ = −2.5 in the tail-probability check.

## 4. Implementation
- `simulation.engine.simulate`, `simulation.portfolio.simulate_book`, `simulation.sampling`.
- `validation.convergence.bootstrap_se`, `seed_study`; `validation.sensitivity.tornado`.

## 5. Checks
- V-07: at 20,000 paths, ES 107.0m with bootstrap s.e. 3.0m (2.8%).
- Importance sampling cuts the standard error of P(loss rate > 8%) by 6.8×.
- `tests/unit/test_sampling.py`: IS estimate unbiased against the closed form.

## 6. Limitations
- IS is applied in the validation check, not yet inside the full book run.
- Path count is a trade-off: ES standard error falls roughly as $1/\sqrt n$.
