"""Whole-book simulation.

Bonds, commercial mortgages and structured tranches on ONE simulated economy (NB06-NB09).

    G_t           global credit cycle, AR(1)
    Z_bond = G    corporate bonds follow the global credit cycle
    Z_cre         = sqrt(beta_cre) G + sqrt(1 - beta_cre) H      commercial real estate cycle
    Z_pool        = sqrt(beta_pool) G + ...                      collateral of the structured pool
Each class is simulated with its own engine on its factor. Losses are then stacked asset by asset,
so the whole book has one loss distribution, one capital path and contributions that add up.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from creditengine.assets.corporate import BondPortfolio
from creditengine.assets.cre import CREPortfolio, CRESettings, simulate_cre
from creditengine.assets.structured import Tranche, tranche_loss
from creditengine.capital.rbc import rbc_path
from creditengine.simulation.engine import SimulationSettings, simulate
from creditengine.simulation.sampling import class_factor, factor_paths


@dataclass
class StructuredHolding:
    """Tranches held by the insurer, all on one collateral pool."""

    pool: BondPortfolio  # collateral obligors (unit or actual exposures)
    pool_rho: float
    pool_lgd_mean: float
    pool_lgd_std: float
    tranches: list[Tranche]
    notional: dict[str, float]  # tranche name -> amount held (USD)


@dataclass
class BookSettings:
    horizon: int = 5
    n_paths: int = 20_000
    phi: float = 0.5
    z0: float | None = None
    seed: int = 2026
    beta_cre: float = 0.5  # share of the CRE cycle that is the global credit cycle
    beta_pool: float = 1.0
    bond_rho: float | np.ndarray = 0.20
    bond_lgd_mean: float = 0.60
    bond_lgd_std: float = 0.25
    lgd_cycle: float = 0.0
    global_path: np.ndarray | None = None  # fixed scenario for G, shape (horizon,)


@dataclass
class BookResult:
    asset_loss: np.ndarray  # (paths, assets) horizon loss per asset
    exposure: np.ndarray  # (assets,)
    labels: pd.DataFrame  # asset_class, group, id for each asset column
    losses_by_class: dict[str, np.ndarray]  # class -> (paths, years)
    rbc_by_class: dict[str, np.ndarray]  # class -> (paths, years + 1)
    pool_loss_rate: np.ndarray  # (paths,) cumulative collateral loss rate
    factors: dict[str, np.ndarray] = field(default_factory=dict)

    @property
    def total_loss(self) -> np.ndarray:
        return self.asset_loss.sum(axis=1)

    @property
    def losses_by_year(self) -> np.ndarray:
        return sum(self.losses_by_class.values())

    @property
    def rbc_total(self) -> np.ndarray:
        return sum(self.rbc_by_class.values())


def simulate_book(
    bonds: BondPortfolio,
    cre: CREPortfolio,
    structured: StructuredHolding,
    matrix: np.ndarray,
    bond_factor_by_state: np.ndarray,
    pa_tiers: pd.DataFrame,
    tranche_factor: dict[str, float],
    settings: BookSettings,
    cre_settings: CRESettings | None = None,
) -> BookResult:
    """Simulate the three asset classes on one economy and stack the results."""
    s = settings
    rng = np.random.default_rng(s.seed)
    if s.global_path is not None:
        g = np.tile(np.asarray(s.global_path, dtype=float), (s.n_paths, 1))
    else:
        g = factor_paths(s.n_paths, s.horizon, s.phi, rng, s.z0)
    z_cre = class_factor(g, s.beta_cre, s.phi, rng)
    z_pool = class_factor(g, s.beta_pool, s.phi, rng)

    common = dict(horizon=s.horizon, n_paths=s.n_paths, phi=s.phi, lgd_cycle=s.lgd_cycle)
    bond_res = simulate(
        bonds,
        matrix,
        SimulationSettings(
            **common,
            rho=s.bond_rho,
            lgd_mean=s.bond_lgd_mean,
            lgd_std=s.bond_lgd_std,
            z=g,
            seed=s.seed + 1,
        ),
    )
    cre_res = simulate_cre(cre, z_cre, cre_settings or CRESettings(seed=s.seed + 2))
    pool_res = simulate(
        structured.pool,
        matrix,
        SimulationSettings(
            **common,
            rho=structured.pool_rho,
            lgd_mean=structured.pool_lgd_mean,
            lgd_std=structured.pool_lgd_std,
            z=z_pool,
            seed=s.seed + 3,
        ),
    )

    # structured: cumulative pool loss rate by year -> tranche losses by year
    pool_cum = np.cumsum(pool_res.losses, axis=1) / structured.pool.exposure.sum()
    tr_loss_cols, tr_year, tr_rbc = (
        [],
        np.zeros((s.n_paths, s.horizon)),
        np.zeros((s.n_paths, s.horizon + 1)),
    )
    for tr in structured.tranches:
        held = structured.notional.get(tr.name, 0.0)
        if held == 0.0:
            continue
        cum = tranche_loss(pool_cum, tr.attach, tr.detach)  # (paths, years), share of tranche
        cum0 = np.hstack([np.zeros((s.n_paths, 1)), cum])
        tr_year += held * np.diff(cum0, axis=1)
        tr_loss_cols.append(held * cum[:, -1])
        tr_rbc += held * (1.0 - cum0) * tranche_factor[tr.designation]
    held_names = [t.name for t in structured.tranches if structured.notional.get(t.name, 0.0) > 0]

    asset_loss = np.hstack([bond_res.issuer_loss, cre_res.loan_loss, np.column_stack(tr_loss_cols)])
    exposure = np.concatenate(
        [bonds.exposure, cre.balance, [structured.notional[n] for n in held_names]]
    )
    from creditengine.data.rating_agency import RATINGS

    labels = pd.DataFrame(
        {
            "asset_class": ["corporate bonds"] * bonds.n
            + ["commercial mortgages"] * cre.n
            + ["structured"] * len(held_names),
            "group": list(np.array(RATINGS)[bonds.rating])
            + list(cre.property_type)
            + [f"tranche {n}" for n in held_names],
            "id": list(bonds.issuer) + list(cre.loan_id) + held_names,
        }
    )
    return BookResult(
        asset_loss=asset_loss,
        exposure=exposure,
        labels=labels,
        losses_by_class={
            "corporate bonds": bond_res.losses,
            "commercial mortgages": cre_res.losses,
            "structured": tr_year,
        },
        rbc_by_class={
            "corporate bonds": rbc_path(bond_res, bond_factor_by_state, pa_tiers),
            "commercial mortgages": cre_res.rbc_path(),
            "structured": tr_rbc,
        },
        pool_loss_rate=pool_cum[:, -1],
        factors={"global": g, "cre": z_cre, "pool": z_pool},
    )
