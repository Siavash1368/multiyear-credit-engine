"""Corporate bonds.

Rated corporate bond exposures. Developed in NB06.

v0.1: a stylised bond book generated from a rating mix in configs/portfolios/ (A-09).
One bond per issuer; exposure = statutory carrying value = EAD.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from creditengine.data.rating_agency import RATINGS, rating_index


@dataclass
class BondPortfolio:
    """Arrays of equal length, one entry per issuer."""

    issuer: np.ndarray  # issuer id
    rating: np.ndarray  # initial state index (0 = AAA ... 6 = CCC/C)
    exposure: np.ndarray  # USD
    maturity: np.ndarray  # whole years to maturity
    sector: np.ndarray | None = None  # optional sector label per issuer (multi-factor runs)

    @property
    def n(self) -> int:
        return len(self.issuer)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "issuer": self.issuer,
                "rating": np.array(RATINGS)[self.rating],
                "exposure": self.exposure,
                "maturity": self.maturity,
                **({"sector": self.sector} if self.sector is not None else {}),
            }
        )

    @classmethod
    def from_frame(cls, df: pd.DataFrame) -> BondPortfolio:
        return cls(
            issuer=df["issuer"].to_numpy(),
            rating=rating_index(df["rating"].tolist()),
            exposure=df["exposure"].to_numpy(dtype=float),
            maturity=df["maturity"].to_numpy(dtype=int),
            sector=df["sector"].to_numpy() if "sector" in df else None,
        )

    @classmethod
    def stylised(
        cls,
        total_exposure: float,
        n_issuers: int,
        rating_mix: dict[str, float],
        maturity_years: dict[str, int],
        seed: int = 0,
        n_sectors: int | None = None,
    ) -> BondPortfolio:
        """Illustrative book: issuers split by rating mix; lognormal position sizes scaled to total.

        Maturities are spread uniformly from 1 year to 2 x the average maturity of the rating.
        Optional n_sectors assigns each issuer to one of n_sectors industries at random.
        """
        rng = np.random.default_rng(seed)
        weights = np.array([rating_mix.get(r, 0.0) for r in RATINGS])
        counts = np.round(weights / weights.sum() * n_issuers).astype(int)
        rating = np.repeat(np.arange(len(RATINGS)), counts)
        size = rng.lognormal(mean=0.0, sigma=0.5, size=rating.size)
        # scale sizes so each rating bucket holds its share of total exposure
        exposure = np.empty(rating.size)
        for r in range(len(RATINGS)):
            in_r = rating == r
            if in_r.any():
                exposure[in_r] = size[in_r] / size[in_r].sum() * weights[r] / weights.sum()
        exposure *= total_exposure
        avg_mat = np.array([maturity_years.get(RATINGS[r], 5) for r in rating])
        maturity = rng.integers(1, 2 * avg_mat, endpoint=True)
        issuer = np.array([f"ISS{k:04d}" for k in range(rating.size)])
        # sectors drawn after everything else so the v0.1 book is unchanged
        sector = None if n_sectors is None else rng.integers(0, n_sectors, size=rating.size)
        return cls(
            issuer=issuer, rating=rating, exposure=exposure, maturity=maturity, sector=sector
        )
