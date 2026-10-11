# Merton structural model and distance to default

**References:** Bluhm §3.3–3.4; Merton (1974)

## 1. Intuition
A firm defaults when the value of what it owns falls below what it owes. Equity is a call option on the firm's assets, so the share price and its volatility reveal the market value and riskiness of the assets. **Distance to default** counts how many standard deviations of asset value separate the firm from its default point.

## 2. Model
Asset value $V_t$ follows geometric Brownian motion with volatility $\sigma_V$. With default point *D*, horizon *T* and rate *r*:

$$E = V N(d_1) - D e^{-rT} N(d_2), \quad d_1 = \frac{\ln(V/D) + (r + \tfrac12\sigma_V^2)T}{\sigma_V\sqrt T}, \quad d_2 = d_1 - \sigma_V\sqrt T$$

$$\sigma_E E = N(d_1) \sigma_V V$$

Two equations, two unknowns $(V, \sigma_V)$. Then

$$\text{DD} = \frac{\ln(V/D) + (\mu - \tfrac12\sigma_V^2)T}{\sigma_V\sqrt T}, \qquad \text{PD}^{\text{Merton}} = N(-\text{DD})$$

The same idea drives the whole engine: an obligor's "asset return" crossing a threshold $c = N^{-1}(\text{PD})$ is a default (one-factor model, 03), and a building's value falling below the loan balance is a mortgage default (07).

## 3. Calibration
- Equity value = last close × shares outstanding (SEC XBRL `dei:EntityCommonStockSharesOutstanding`).
- $\sigma_E$ = 252-day historical volatility of daily log returns.
- Default point *D* = current liabilities + ½ non-current liabilities (KMV convention, A-12).
- *r* = 1-year Treasury (FRED DGS1); *T* = 1 year.

## 4. Implementation
- `models.merton`: `distance_to_default`, `default_probability`, `equity_from_assets`, `solve_assets` (`scipy.optimize.fsolve`), `kmv_default_point`.
- `data.edgar.merton_inputs` builds the inputs; `scripts/run_merton.py` runs 15 listed issuers.

## 5. Checks
- `tests/unit/test_merton.py`: round trip (assets → equity → assets).
- V-08: Spearman rank correlation of DD with ratings = 0.90.

## 6. Limitations
- L-11: normal tails make raw $N(-\text{DD})$ far too small for investment grade; use DD for ranking and early warning, map to observed default rates for levels.
- Consolidated balance sheets with finance arms (Ford) look more levered than the operating company.
