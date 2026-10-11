"""Commercial mortgage loans.

Merton on the building: property value and NOI paths driven by the credit cycle; term and
balloon default; prepayment; loss as a collateral shortfall; NAIC CM1-CM7 category each year.
Developed in NB07.

Per loan and year t (all shocks standard normal; Z_t is the commercial real estate factor):
    ln V_t   = ln V_{t-1}   + mu_v - sigma_v^2/2 + sigma_v (sqrt(rho_v) Z_t + sqrt(1-rho_v) e_t)
    ln NOI_t = ln NOI_{t-1} + g    - sigma_n^2/2 + sigma_n (sqrt(rho_n) Z_t + sqrt(1-rho_n) u_t)
    DSCR_t = NOI_t / debt service,   LTV_t = balance_t / V_t
    term default    : DSCR_t < 1 and LTV_t > 1          (cannot pay and no equity left)
    balloon default : at maturity, LTV_T > refi_ltv_max or NOI_T / refi debt service < refi_dscr_min
    loss            : max(balance - (1 - kappa) V, 0)   (shortfall after selling costs kappa)
    prepayment      : constant annual probability for loans that do not default
Defaulted, prepaid and matured loans leave the book (A-05, A-07).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

PROPERTY_TYPES = ["apartment", "industrial", "retail", "office", "hotel"]
# NAIC Figure 4 applies to office, industrial, retail and multifamily; Figure 5 to hotel/specialty
CM_FACTORS = {1: 0.0090, 2: 0.0175, 3: 0.0300, 4: 0.0500, 5: 0.0750, 6: 0.18, 7: 0.23}


def annual_payment(balance: np.ndarray | float, rate: float, amort_years: int) -> np.ndarray:
    """Level annual payment that amortises balance over amort_years at rate."""
    return np.asarray(balance) * rate / (1.0 - (1.0 + rate) ** (-amort_years))


def balance_after(
    balance: np.ndarray | float, rate: float, amort_years: int, years: np.ndarray | int
) -> np.ndarray:
    """Remaining balance after `years` level annual payments."""
    pay = annual_payment(balance, rate, amort_years)
    growth = (1.0 + rate) ** np.asarray(years)
    return np.asarray(balance) * growth - pay * (growth - 1.0) / rate


def cm_category(dscr: np.ndarray, ltv: np.ndarray, hotel: np.ndarray | bool = False) -> np.ndarray:
    """NAIC commercial mortgage category CM1..CM5 for loans in good standing (V-12).

    Office, industrial, retail, multifamily: NAIC Life RBC instructions, Figure 4.
    Hotel and specialty commercial: Figure 5. Inputs are arrays of the same shape.
    """
    d = np.asarray(dscr, dtype=float)
    v = np.asarray(ltv, dtype=float)
    hotel = np.broadcast_to(np.asarray(hotel, dtype=bool), d.shape)

    std = np.full(d.shape, 5, dtype=np.int8)  # default bucket; overwritten in order of priority
    rules = [
        (4, (d < 0.95) & (v >= 0.85) & (v < 1.05)),
        (4, (d >= 0.95) & (d < 1.15) & (v >= 1.00)),
        (3, (d < 0.95) & (v >= 0.55) & (v < 0.85)),
        (3, (d >= 0.95) & (d < 1.15) & (v >= 0.75) & (v < 1.00)),
        (3, (d >= 1.15) & (d < 1.75) & (v >= 1.00)),
        (2, (d < 1.50) & (v < 0.55)),
        (2, (d >= 0.95) & (d < 1.50) & (v >= 0.55) & (v < 0.75)),
        (2, (d >= 1.15) & (d < 1.50) & (v >= 0.75) & (v < 1.00)),
        (2, (d >= 1.50) & (v >= 0.85) & (v < 1.00)),
        (2, (d >= 1.75) & (v >= 1.00)),
        (1, (d >= 1.50) & (v < 0.85)),
    ]
    for cat, mask in rules:
        std[mask] = cat

    htl = np.full(d.shape, 5, dtype=np.int8)
    rules_h = [
        (4, (d < 0.90) & (v < 0.90)),
        (4, (d >= 0.90) & (d < 1.10) & (v >= 0.80) & (v < 0.90)),
        (4, (d >= 1.10) & (d < 1.45) & (v >= 0.80)),
        (3, (d >= 0.90) & (d < 1.45) & (v < 0.80)),
        (3, (d >= 1.45) & (d < 1.85) & (v >= 0.70)),
        (3, (d >= 1.85) & (v >= 1.15)),
        (2, (d >= 1.45) & (d < 1.85) & (v < 0.70)),
        (2, (d >= 1.85) & (v >= 0.60) & (v < 1.15)),
        (1, (d >= 1.85) & (v < 0.60)),
    ]
    for cat, mask in rules_h:
        htl[mask] = cat
    return np.where(hotel, htl, std)


@dataclass
class CREPortfolio:
    """Arrays of equal length, one entry per loan. Money in USD."""

    loan_id: np.ndarray
    property_type: np.ndarray  # labels from PROPERTY_TYPES
    balance: np.ndarray  # current principal
    value: np.ndarray  # current property value
    noi: np.ndarray  # current net operating income (annual)
    rate: np.ndarray  # loan interest rate
    amort_years: np.ndarray  # amortisation period
    maturity: np.ndarray  # whole years to balloon

    @property
    def n(self) -> int:
        return len(self.loan_id)

    @property
    def debt_service(self) -> np.ndarray:
        return annual_payment(self.balance, self.rate, self.amort_years)

    @property
    def dscr(self) -> np.ndarray:
        return self.noi / self.debt_service

    @property
    def ltv(self) -> np.ndarray:
        return self.balance / self.value

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "loan_id": self.loan_id,
                "property_type": self.property_type,
                "balance": self.balance,
                "value": self.value,
                "noi": self.noi,
                "rate": self.rate,
                "amort_years": self.amort_years,
                "maturity": self.maturity,
                "dscr": self.dscr,
                "ltv": self.ltv,
            }
        )

    @classmethod
    def stylised(
        cls,
        total_balance: float,
        n_loans: int,
        type_mix: dict[str, float],
        ltv_mean: float = 0.60,
        ltv_sd: float = 0.12,
        dscr_mean: float = 2.0,
        dscr_sd: float = 0.45,
        office_ltv_add: float = 0.12,
        office_dscr_cut: float = 0.45,
        rate: float = 0.05,
        amort_years: int = 25,
        max_maturity: int = 10,
        seed: int = 0,
    ) -> CREPortfolio:
        """Illustrative book (A-09): loan sizes lognormal; LTV and DSCR drawn around the means.

        Office loans are drawn weaker (higher LTV, lower DSCR) to mirror the post-2020 pocket.
        """
        rng = np.random.default_rng(seed)
        types = np.array(list(type_mix))
        weights = np.array([type_mix[t] for t in types], dtype=float)
        counts = np.round(weights / weights.sum() * n_loans).astype(int)
        ptype = np.repeat(types, counts)
        n = ptype.size
        size = rng.lognormal(0.0, 0.6, n)
        balance = np.empty(n)
        for t, w in zip(types, weights / weights.sum(), strict=True):
            m = ptype == t
            if m.any():
                balance[m] = size[m] / size[m].sum() * w * total_balance
        office = ptype == "office"
        ltv = np.clip(rng.normal(ltv_mean, ltv_sd, n) + office * office_ltv_add, 0.30, 0.95)
        dscr = np.clip(rng.normal(dscr_mean, dscr_sd, n) - office * office_dscr_cut, 1.10, 3.50)
        rate_arr = np.full(n, rate)
        amort = np.full(n, amort_years)
        ds = annual_payment(balance, rate, amort_years)
        return cls(
            loan_id=np.array([f"CML{k:04d}" for k in range(n)]),
            property_type=ptype,
            balance=balance,
            value=balance / ltv,
            noi=dscr * ds,
            rate=rate_arr,
            amort_years=amort,
            maturity=rng.integers(1, max_maturity, endpoint=True, size=n),
        )


@dataclass
class CRESettings:
    """Property and loan behaviour (A-07). Values are illustrative and declared."""

    value_drift: float = 0.02
    value_vol: float = 0.15
    value_rho: float = 0.35  # share of property-value variance from the CRE cycle
    noi_growth: float = 0.02
    noi_vol: float = 0.08
    noi_rho: float = 0.30
    selling_cost: float = 0.25  # kappa: legal, time and fire-sale discount
    prepay_rate: float = 0.03  # annual probability of voluntary prepayment
    refi_ltv_max: float = 1.00
    refi_dscr_min: float = 1.00
    refi_rate: float = 0.06
    term_trigger_ltv: float = 1.00  # double trigger: DSCR < 1 and LTV above this
    seed: int = 7


@dataclass
class CREResult:
    losses: np.ndarray  # (paths, years) loss booked each year
    loan_loss: np.ndarray  # (paths, loans) loss over the horizon
    category: np.ndarray  # (paths, years + 1, loans) CM1..CM5; 0 once the loan has left
    balance: np.ndarray  # (paths, years + 1, loans) outstanding balance; 0 once left
    default_year: np.ndarray  # (paths, loans) year of default, 0 = no default
    balloon_default: np.ndarray  # (paths, loans) bool, default happened at the balloon

    @property
    def total_loss(self) -> np.ndarray:
        return self.losses.sum(axis=1)

    def rbc_path(self) -> np.ndarray:
        """Required capital by path and year: balance x CM factor for live loans."""
        factor = np.vectorize(lambda c: CM_FACTORS.get(int(c), 0.0))(self.category)
        return (factor * self.balance).sum(axis=2)

    def default_rate(self) -> float:
        """Share of loans that default within the horizon, averaged over paths."""
        return float((self.default_year > 0).mean())


def simulate_cre(portfolio: CREPortfolio, z: np.ndarray, settings: CRESettings) -> CREResult:
    """Simulate the loan book along given CRE-cycle paths z of shape (paths, years)."""
    s = settings
    rng = np.random.default_rng(s.seed)
    n_paths, horizon = z.shape
    n = portfolio.n
    hotel = portfolio.property_type == "hotel"

    log_v = np.tile(np.log(portfolio.value), (n_paths, 1))
    log_noi = np.tile(np.log(portfolio.noi), (n_paths, 1))
    ds = portfolio.debt_service
    alive = np.ones((n_paths, n), dtype=bool)

    losses = np.zeros((n_paths, horizon))
    loan_loss = np.zeros((n_paths, n))
    category = np.zeros((n_paths, horizon + 1, n), dtype=np.int8)
    balance = np.zeros((n_paths, horizon + 1, n))
    default_year = np.zeros((n_paths, n), dtype=np.int16)
    balloon_default = np.zeros((n_paths, n), dtype=bool)

    balance[:, 0] = portfolio.balance
    category[:, 0] = cm_category(
        np.tile(portfolio.dscr, (n_paths, 1)), np.tile(portfolio.ltv, (n_paths, 1)), hotel
    )

    for t in range(1, horizon + 1):
        zt = z[:, t - 1 : t]
        e = rng.standard_normal((n_paths, n))
        u = rng.standard_normal((n_paths, n))
        log_v += (
            s.value_drift
            - 0.5 * s.value_vol**2
            + s.value_vol * (np.sqrt(s.value_rho) * zt + np.sqrt(1 - s.value_rho) * e)
        )
        log_noi += (
            s.noi_growth
            - 0.5 * s.noi_vol**2
            + s.noi_vol * (np.sqrt(s.noi_rho) * zt + np.sqrt(1 - s.noi_rho) * u)
        )
        value, noi = np.exp(log_v), np.exp(log_noi)
        bal = balance_after(portfolio.balance, portfolio.rate, portfolio.amort_years, t)[None, :]
        dscr, ltv = noi / ds, bal / value

        at_balloon = portfolio.maturity[None, :] == t
        refi_ds = bal * s.refi_rate / (1.0 - (1.0 + s.refi_rate) ** (-portfolio.amort_years))
        term_def = (dscr < 1.0) & (ltv > s.term_trigger_ltv)
        balloon_def = at_balloon & ((ltv > s.refi_ltv_max) | (noi / refi_ds < s.refi_dscr_min))
        default = alive & (term_def | balloon_def)

        loss = np.where(default, np.maximum(bal - (1.0 - s.selling_cost) * value, 0.0), 0.0)
        losses[:, t - 1] = loss.sum(axis=1)
        loan_loss += loss
        default_year[default] = t
        balloon_default |= default & balloon_def & ~term_def

        prepaid = alive & ~default & (rng.random((n_paths, n)) < s.prepay_rate)
        matured = alive & ~default & at_balloon
        alive &= ~(default | prepaid | matured)

        balance[:, t] = np.where(alive, bal, 0.0)
        category[:, t] = np.where(alive, cm_category(dscr, ltv, hotel), 0)

    return CREResult(losses, loan_loss, category, balance, default_year, balloon_default)


def balloon_default_probability(
    value: float, balance: float, drift: float, vol: float, years: float
) -> float:
    """Merton closed form for an interest-only loan: P(V_T < B) = N(-DD) (validation)."""
    from scipy.stats import norm

    dd = (np.log(value / balance) + (drift - 0.5 * vol**2) * years) / (vol * np.sqrt(years))
    return float(norm.cdf(-dd))
