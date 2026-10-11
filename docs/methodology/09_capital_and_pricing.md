# Statutory capital, capital allocation, pricing and limits

**References:** Bluhm §5.1–5.2; NAIC; American Academy of Actuaries (2021)

## 1. Intuition
Two capital views run side by side. **Statutory RBC** is the regulator's rule: a factor per rating bucket, recomputed each year as bonds migrate, so the engine shows how required capital could drift up in a bad cycle. **Economic capital** (ES − EL) is the model's own view of tail risk. Allocating economic capital to each asset shows where the tail actually comes from; comparing it with limits and with spreads tells the business what to hold, what to cut and what a new purchase must earn.

## 2. Model
**RBC (bonds):** $\text{RBC}_t = \text{PA}(n_t)\sum_i f_{d(i,t)}\,E_{i,t}$, with $f_d$ the pre-tax factor for NAIC designation *d* and PA the portfolio adjustment by issuer count. Mortgages use CM factors (07); tranches use their designation factor (A-15).

**Euler ES allocation:**
$$\text{EC}_i = \mathbb E[L_i \mid L \ge \text{VaR}_q] - \mathbb E[L_i], \qquad \sum_i \text{EC}_i = \text{ES}_q - \text{EL}$$

**Variance contribution:** $\text{Cov}(L_i, L)/\text{Var}(L)$.

**Diversification:** $1 - \text{EC}_{\text{book}} / \sum_k \text{EC}_k^{\text{standalone}}$.

**Break-even spread:**
$$s^* = \underbrace{\text{PD}^{\text{ann}}\cdot \overline{\text{LGD}}}_{\text{annual EL}} + k\cdot f_d \cdot \text{CoC} + \text{expenses}, \qquad \text{PD}^{\text{ann}} = 1 - (1-\text{PD}^{\text{cum}}_T)^{1/T}$$

**RAROC:** $(s - \text{EL} - \text{expenses}) / \text{capital}$.

**Limits:** utilisation = allocated EC / (limit share × book EC); ≥ 90% review, > 100% breach. A risk transfer pays when its cost < EL removed + CoC × capital removed.

## 3. Calibration
Academy C1WG factors (Mar 2021) and portfolio adjustment; k = 2; CoC = 10% (A-06). Market spreads: ICE BofA option-adjusted spreads from FRED (not committed). Limits: bonds 70%, mortgages 15%, structured 15% of book EC.

## 4. Implementation
- `capital.rbc`, `capital.allocation`, `capital.pricing`, `capital.limits`.
- `scripts/run_portfolio.py` writes contribution, pricing, limits and stress tables.

## 5. Checks
- V-11: RBC at t = 0 equals a hand calculation.
- `tests/unit/test_allocation.py`: Euler contributions add up to the total.

## 6. Limitations
- L-07: defaulted bonds leave the book (no NAIC 6 capital).
- L-08: middle-notch mapping.
- Spreads compensate for more than default (liquidity, mark-to-market risk), so the cushion is not pure profit.
