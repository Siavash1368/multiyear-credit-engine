# Loss measures: EL, UL, VaR, ES

**References:** Bluhm §1.1–1.2, §5.1

## 1. Intuition
A credit book loses money in two ways. The **expected loss** is the average cost of doing business and belongs in the price. The **unexpected loss** is the swing around that average in a bad year; it is what capital must absorb. The tail measures (VaR and ES) answer: "how bad is a 1-in-200 outcome, and how bad on average once we are past it?"

## 2. Model
For issuer *i* with exposure $E_i$, default indicator $D_i$ and loss given default $\text{LGD}_i$:

$$L = \sum_i E_i  \text{LGD}_i   D_i, \qquad \text{EL} = \mathbb E[L] = \sum_i E_i \overline{\text{LGD}}_i \text{PD}_i$$

$$\text{VaR}_q = \inf\{\ell : P(L \le \ell) \ge q\}, \qquad \text{ES}_q = \mathbb E[L \mid L \ge \text{VaR}_q]$$

$$\text{EC}_q = \text{ES}_q - \text{EL}$$

Here *L* is the cumulative five-year loss along one simulated path (A-05). EL is additive across assets; VaR and ES are not, which is why they need allocation (see 09).

## 3. Calibration
No parameters of its own. Level q = 99.5% (Solvency II-style one-in-200; configurable in `configs/base.yaml`).

## 4. Implementation
- `simulation.results.SimulationResult` — path losses, `summary(q)` returns EL, StdDev, VaR, ES.
- `capital.allocation.es_contributions` — splits ES back to assets.

## 5. Checks
- V-01 (Vasicek quantile check), V-07 (bootstrap s.e. of ES: 3.0m on 107.0m at 20,000 paths).

## 6. Limitations
- ES at 99.5% rests on ~100 tail paths at 20,000 paths; standard error is reported every run (V-07).
- Default-only loss; no spread mark-to-market (L-14).
