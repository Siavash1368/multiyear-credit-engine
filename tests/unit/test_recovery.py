"""Beta LGD moments; cycle link direction."""

import pytest

from creditengine.models.recovery import beta_parameters, sample_lgd


def test_beta_moments(rng):
    draws = sample_lgd(0.6, 0.25, 200_000, rng)
    assert draws.mean() == pytest.approx(0.6, abs=0.003)
    assert draws.std() == pytest.approx(0.25, abs=0.003)
    assert draws.min() >= 0.0 and draws.max() <= 1.0


def test_invalid_moments_raise():
    with pytest.raises(ValueError):
        beta_parameters(0.6, 0.6)  # variance too large for a beta


def test_cycle_lgd_keeps_long_run_mean():
    import numpy as np

    from creditengine.models.recovery import cycle_mean_lgd

    z = np.random.default_rng(0).standard_normal(400_000)
    assert cycle_mean_lgd(z, 0.6, 1.0).mean() == pytest.approx(0.6, abs=0.002)
    assert cycle_mean_lgd(-2.0, 0.6, 1.0) > 0.6 > cycle_mean_lgd(2.0, 0.6, 1.0)
