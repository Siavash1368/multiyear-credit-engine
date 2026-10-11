"""Simulation engine.

Path-by-path, year-by-year migration, default and loss for a bond book. Developed in NB06.

Each year t on each path:
  1. the cycle Z_t (AR(1), shared by all issuers on the path; or a sector factor, or a
     path supplied by the caller so several asset classes share one economy)
  2. asset returns A_{i,t} = sqrt(rho) Z_t + sqrt(1 - rho) eps_{i,t}
     (Student-t copula option: A is multiplied by a common sqrt(W), then mapped back to the
     Gaussian scale with the same rank, so the rating thresholds are unchanged)
  3. migrate every live, unmatured bond through the CreditMetrics thresholds of its current rating
  4. a move to D books a loss EAD x LGD in year t (LGD optionally linked to Z_t); the bond leaves
Bonds that reach maturity leave the book at par. Static portfolio, no reinvestment (A-05).
The default settings reproduce v0.1 exactly (same random-number sequence).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from creditengine.assets.corporate import BondPortfolio
from creditengine.data.rating_agency import DEFAULT
from creditengine.models.cycle import simulate_factor_paths
from creditengine.models.migration import migrate, thresholds
from creditengine.models.recovery import cycle_mean_lgd, sample_lgd, sample_lgd_conditional
from creditengine.simulation.results import SimulationResult
from creditengine.simulation.sampling import class_factor, factor_paths, t_scale, t_to_gaussian


@dataclass
class SimulationSettings:
    horizon: int = 5  # years (A-05)
    n_paths: int = 10_000
    rho: float | np.ndarray = 0.20  # asset correlation (A-02): one value or one per issuer
    phi: float = 0.50  # cycle persistence (A-03)
    lgd_mean: float = 0.60  # senior unsecured (A-04)
    lgd_std: float = 0.25
    z0: float | None = None  # starting cycle state; None = stationary
    seed: int = 2026
    # v0.2 options; defaults keep the v0.1 model
    z: np.ndarray | None = None  # supplied cycle paths (n_paths, horizon), e.g. a shared economy
    lgd_cycle: float = 0.0  # LGD sensitivity to the cycle (A-13); 0 = independent
    copula: Literal["gaussian", "t"] = "gaussian"  # A-10
    t_nu: float = 6.0  # degrees of freedom for the t copula
    sector_beta: float | None = None  # share of each sector factor that is global (A-11)
    antithetic: bool = False  # antithetic cycle paths (variance reduction)


def _cycle(settings: SimulationSettings, rng: np.random.Generator) -> np.ndarray:
    if settings.z is not None:
        z = np.asarray(settings.z, dtype=float)
        if z.shape != (settings.n_paths, settings.horizon):
            raise ValueError(f"z must have shape {(settings.n_paths, settings.horizon)}")
        return z
    if settings.antithetic:
        return factor_paths(
            settings.n_paths, settings.horizon, settings.phi, rng, settings.z0, True
        )
    return simulate_factor_paths(settings.n_paths, settings.horizon, settings.phi, rng, settings.z0)


def simulate(
    portfolio: BondPortfolio, matrix: np.ndarray, settings: SimulationSettings
) -> SimulationResult:
    """Run the multi-year Monte Carlo and return losses, rating paths and issuer losses."""
    s = settings
    rng = np.random.default_rng(s.seed)
    edges = thresholds(np.asarray(matrix, dtype=float))
    rho = np.broadcast_to(np.asarray(s.rho, dtype=float), (portfolio.n,))  # scalar or per issuer

    z = _cycle(s, rng)
    # factor seen by each issuer: the global cycle, or its sector's factor
    if s.sector_beta is not None and portfolio.sector is not None:
        sectors = np.unique(portfolio.sector)
        z_sector = {k: class_factor(z, s.sector_beta, s.phi, rng) for k in sectors}
        z_issuer = np.stack([z_sector[k] for k in portfolio.sector], axis=2)  # (paths, years, n)
    else:
        z_issuer = None

    state = np.tile(portfolio.rating, (s.n_paths, 1))  # (paths, issuers)
    ratings = np.empty((s.n_paths, s.horizon + 1, portfolio.n), dtype=np.int8)
    ratings[:, 0] = state
    losses = np.zeros((s.n_paths, s.horizon))
    issuer_loss = np.zeros((s.n_paths, portfolio.n))

    for t in range(s.horizon):
        alive = (state != DEFAULT) & (portfolio.maturity[None, :] > t)
        eps = rng.standard_normal(state.shape)
        factor = z[:, t : t + 1] if z_issuer is None else z_issuer[:, t, :]
        asset = np.sqrt(rho) * factor + np.sqrt(1.0 - rho) * eps
        if s.copula == "t":
            asset = t_to_gaussian(asset * t_scale((s.n_paths, 1), s.t_nu, rng), s.t_nu)
        new_state = np.where(alive, migrate(state, asset, edges), state)

        defaulted = alive & (new_state == DEFAULT)
        if s.lgd_cycle == 0.0:
            lgd = sample_lgd(s.lgd_mean, s.lgd_std, state.shape, rng)
        else:
            mean = np.broadcast_to(
                cycle_mean_lgd(z[:, t : t + 1], s.lgd_mean, s.lgd_cycle), state.shape
            )
            lgd = sample_lgd_conditional(mean, s.lgd_std, rng)
        loss_it = defaulted * portfolio.exposure[None, :] * lgd
        losses[:, t] = loss_it.sum(axis=1)
        issuer_loss += loss_it

        state = new_state
        ratings[:, t + 1] = state

    return SimulationResult(
        losses=losses,
        ratings=ratings,
        z=z,
        exposure=portfolio.exposure,
        maturity=portfolio.maturity,
        issuer_loss=issuer_loss,
    )
