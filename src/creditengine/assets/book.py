"""Whole book.

Build the stylised general-account book (bonds, commercial mortgages, structured tranches) from
configs/portfolios/insurer_book.yaml. Illustrative portfolios only (A-09).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from creditengine.assets.corporate import BondPortfolio
from creditengine.assets.cre import CREPortfolio, CRESettings
from creditengine.assets.structured import Tranche, capital_structure
from creditengine.config import read_yaml
from creditengine.data.naic import load_bond_factors
from creditengine.data.rating_agency import RATINGS
from creditengine.simulation.portfolio import StructuredHolding


@dataclass
class Book:
    bonds: BondPortfolio
    cre: CREPortfolio
    cre_settings: CRESettings
    structured: StructuredHolding
    tranche_factor: dict[str, float]  # NAIC designation -> pre-tax factor
    beta_cre: float
    beta_pool: float
    limits_share: dict[str, float]


def load_book(
    path: str = "configs/portfolios/insurer_book.yaml", bond_n_sectors: int | None = None
) -> Book:
    cfg = read_yaml(path)
    parts = cfg["book"]

    b = read_yaml(parts["corporate_bonds"]["config"])["portfolio"]
    bonds = BondPortfolio.stylised(
        parts["corporate_bonds"].get("total_exposure_usd", b["total_exposure_usd"]),
        b["n_issuers"],
        b["rating_mix"],
        b["maturity_years"],
        b.get("seed", 0),
        bond_n_sectors,
    )

    c_all = read_yaml(parts["commercial_mortgages"]["config"])
    c = c_all["portfolio"]
    cre = CREPortfolio.stylised(
        c["total_balance_usd"],
        c["n_loans"],
        c["type_mix"],
        c["ltv_mean"],
        c["ltv_sd"],
        c["dscr_mean"],
        c["dscr_sd"],
        c["office_ltv_add"],
        c["office_dscr_cut"],
        c["rate"],
        c["amort_years"],
        c["max_maturity"],
        c.get("seed", 0),
    )
    cre_settings = CRESettings(**c_all["behaviour"])

    st = read_yaml(parts["structured"]["config"])
    pool_cfg = st["pool"]
    mix = pool_cfg["rating_mix"]
    counts = {r: int(round(mix.get(r, 0.0) * pool_cfg["n_obligors"])) for r in RATINGS}
    rating = np.repeat(np.arange(len(RATINGS)), [counts[r] for r in RATINGS])
    pool = BondPortfolio(
        issuer=np.array([f"POOL{k:04d}" for k in range(rating.size)]),
        rating=rating,
        exposure=np.ones(rating.size),
        maturity=np.full(rating.size, pool_cfg["maturity_years"]),
    )
    tranches = [Tranche(**t) for t in st["tranches"]]
    capital_structure(tranches)
    structured = StructuredHolding(
        pool=pool,
        pool_rho=pool_cfg["asset_correlation"],
        pool_lgd_mean=pool_cfg["lgd_mean"],
        pool_lgd_std=pool_cfg["lgd_std"],
        tranches=tranches,
        notional={k: float(v) for k, v in st["held_usd"].items()},
    )
    factors = load_bond_factors()
    tranche_factor = {t.designation: float(factors[t.designation]) for t in tranches}

    econ = cfg["economy"]
    return Book(
        bonds,
        cre,
        cre_settings,
        structured,
        tranche_factor,
        econ["beta_cre"],
        econ["beta_pool"],
        cfg["limits_share_of_ec"],
    )
