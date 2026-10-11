# Model limitations

| ID | Limitation | Impact on results | Mitigation | Status |
|---|---|---|---|---|
| L-01 | Time-homogeneous Markov migration | Overstates speculative-grade multi-year default (V-03: B 5-year 21.9% vs 15.3% published) | Through-the-cycle recalibration; non-Markov adjustments | Open (v0.3) |
| L-02 | Average matrix used with a persistent cycle | Double counts part of the cycle in multi-year PDs | Calibrate the matrix so the simulated average matches published cumulative rates | Open (v0.3) |
| L-03 | Gaussian copula, one factor | No tail dependence; no sector or regional cycles | Student-t copula and sector factors built as challengers (A-10, A-11); tornado shows the size of the effect | Mitigated (challenger built) |
| L-04 | LGD independent of the cycle in the base case | Understates tail loss (recoveries fall in bad years) | Cycle-linked LGD built (A-13): ES +67% with b = 1 | Mitigated (challenger built) |
| L-05 | ρ fixed at the initial rating | Correlation does not change as a bond migrates | Rating-dependent ρ in the loop | Open |
| L-06 | Static book, no reinvestment | Capital path falls as assets mature or prepay | Reinvestment rule | Open |
| L-07 | Defaulted bonds written off at once | No NAIC 6 capital held on defaulted bonds | Hold defaulted bonds to workout | Open |
| L-08 | Letter-category ratings mapped to the middle notch | RBC factor within a category is approximate | Notch-level matrix (S&P Table 23) | Open |
| L-09 | Structured: no cash-flow waterfall, no O/C or I/C tests, homogeneous pool | Tranche losses follow pool losses directly; ignores diversion of cash to senior notes and reinvestment period | Cash-flow waterfall with coverage tests | Open |
| L-10 | Backtest years with zero defaults | Five of the seven BB band breaks are zero-default years, where the lower band is above zero; the test is weak for low-PD ratings | Pool ratings (SG series passes 26 of 26); use counts with issuer numbers | Known |
| L-11 | Merton: normal asset returns, one-year horizon, historical equity vol | Raw N(−DD) is far too small for investment grade; useful for ranking, not as a PD | Map DD to PD empirically (rank to rating PDs) | Known |
| L-12 | Structured designation fixed at issue | Capital on tranches does not rise as the collateral pool deteriorates | Re-designate from simulated tranche loss each year | Open |
| L-13 | Commercial mortgage behaviour not fitted to loan data | Default and loss levels are illustrative | Fit to public CMBS loan-level data (SEC Form ABS-EE) or Fannie Mae multifamily data | Open |
| L-14 | Default-only view (no spread mark-to-market) | Economic capital ignores market value changes from migration | Spread-driven value view | Open |
