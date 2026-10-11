# Roadmap

| Phase | Notebooks | Deliverable | Status |
|---|---|---|---|
| 1. Core corporate engine | NB01 → NB03 → NB04 → NB06 | Multi-year migration Monte Carlo for a bond book | ✅ v0.1 engine |
| 2. Insurer view | NB05 → NB09 → NB10 | Cycle-linked LGD, RBC capital path, ES allocation, pricing, limits, backtests, tornado, convergence | ✅ v0.2 engine |
| 3. Other asset classes | NB07 → NB08 | Commercial mortgages (property value, NOI, DSCR/LTV, CM categories, balloon risk); structured tranches | ✅ v0.2 engine (simplified, see L-09, L-13) |
| 4. Structural and communication | NB02 → NB11 → NB12 | Merton on listed issuers; assumption-to-output reporting; ML challenger | ✅ Merton and reporting in v0.2; ML challenger later |
| 5. Notebooks | NB01–NB12 | One notebook per component, walking through the engine step by step | In progress: outline, theory and checklist in place for NB01–NB12; code being filled in |

## Next (v0.3)
- Through-the-cycle matrix calibration so simulated cumulative default rates match published ones (L-01, L-02)
- Rating-dependent ρ inside the migration loop (L-05)
- Hold defaulted bonds to workout with NAIC 6 capital (L-07)
- Re-designate structured tranches from simulated collateral losses (L-12)

## Later
- Cash-flow waterfall with O/C and I/C tests for structured assets (L-09)
- Fit commercial mortgage behaviour to public CMBS loan-level data (L-13)
- Reinvestment rule for a dynamic book (L-06)
- Spread-driven mark-to-market view (L-14)
- Regional factors for commercial real estate
