# Commercial mortgage loans: property value, NOI, CM categories

**References:** NAIC Life RBC instructions

## 1. Intuition
A commercial mortgage is Merton on a building. The borrower keeps paying while the rent covers the debt; walks away when the building is worth less than the loan **and** the rent no longer covers payments; and can be stuck at maturity if no lender will refinance the balloon. The insurer's loss is the loan balance minus what the building fetches after costs.

## 2. Model
For loan *j* with property type sharing the CRE factor $Z^{\text{cre}}_t$:

$$\ln V_{t} = \ln V_{t-1} + \mu_V - \tfrac12\sigma_V^2 + \sigma_V\big(\sqrt{\rho_V}\,Z^{\text{cre}}_t + \sqrt{1-\rho_V}\,\varepsilon_{jt}\big)$$

$$\ln \text{NOI}_{t} = \ln \text{NOI}_{t-1} + g - \tfrac12\sigma_N^2 + \sigma_N\big(\sqrt{\rho_N}\,Z^{\text{cre}}_t + \sqrt{1-\rho_N}\,\xi_{jt}\big)$$

$$\text{DSCR}_t = \frac{\text{NOI}_t}{\text{debt service}}, \qquad \text{LTV}_t = \frac{B_t}{V_t}$$

- **Term default (double trigger):** $\text{DSCR}_t < 1$ and $\text{LTV}_t > 1$.
- **Balloon default:** at maturity, $\text{LTV}_T > \text{LTV}^{\max}_{\text{refi}}$ or $\text{NOI}_T / \text{DS}_{\text{refi}} < \text{DSCR}^{\min}_{\text{refi}}$.
- **Loss:** $\max(B_t - (1-\kappa)V_t,\ 0)$.
- **Prepayment:** constant annual probability for surviving loans.
- **Link to the economy (A-14):** $Z^{\text{cre}} = \sqrt{\beta}\,G + \sqrt{1-\beta}\,H$.

Closed-form check: balloon default ≈ Merton on the building,
$P(V_T < B_T) = N\!\left(-\dfrac{\ln(V_0/B_T) + (\mu_V - \frac12\sigma_V^2)T}{\sigma_V\sqrt T}\right)$.

**Statutory capital:** each year the loan's DSCR and LTV place it in NAIC CM1–CM5 (hotels and higher-risk cells move down); factors 0.90%, 1.75%, 3.00%, 5.00%, 7.50% (CM6/CM7 for delinquent and foreclosed loans).

## 3. Calibration
Illustrative (A-07, L-13): value drift 2%, vol 15%, ρ_V 0.35; NOI growth 2%, vol 8%, ρ_N 0.30; κ = 25%; prepay 3%; refinance needs LTV ≤ 100% and DSCR ≥ 1.0 at 6%; β = 0.5. Book: $170m, 60 loans, apartment 42%, industrial 22%, retail 22%, office 12% (higher LTV, lower DSCR), hotel 2%.

## 4. Implementation
- `assets.cre`: `CREPortfolio.stylised`, `CRESettings`, `simulate_cre`, `cm_category`, `balloon_default_probability`.
- Config: `configs/portfolios/commercial_mortgages.yaml`.

## 5. Checks
- V-12: 14 NAIC grid cells; balloon PD 7.82% simulated vs 7.81% closed form.
- `tests/unit/test_cre.py`: double trigger (low DSCR alone does not default).

## 6. Limitations
- L-13: behaviour not fitted to loan-level data.
- No regional factor; one CRE factor for all property types.
