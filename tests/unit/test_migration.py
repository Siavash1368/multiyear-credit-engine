"""Thresholds reproduce matrix rows (V-02); matrix powers; generator validity."""

import numpy as np
import pytest

from creditengine.models.migration import (
    conditional_matrix,
    cumulative_default_from_matrix,
    generator,
    matrix_at,
    migrate,
    thresholds,
)


def test_thresholds_shape_and_order(toy_matrix):
    edges = thresholds(toy_matrix)
    assert edges.shape == (8, 9)
    assert np.all(edges[:, 0] == np.inf) and np.all(edges[:, -1] == -np.inf)
    assert np.all(edges[:, :-1] >= edges[:, 1:])  # descending from AAA to D


def test_migration_frequencies_match_rows(toy_matrix, rng):
    """V-02: draw A ~ N(0,1) for every starting rating; frequencies equal the matrix rows."""
    edges = thresholds(toy_matrix)
    n = 200_000
    for i in range(7):
        new = migrate(np.full(n, i), rng.standard_normal(n), edges)
        freq = np.bincount(new, minlength=8) / n
        assert np.allclose(freq, toy_matrix[i], atol=3e-3)


def test_default_is_absorbing(toy_matrix, rng):
    edges = thresholds(toy_matrix)
    assert np.all(migrate(np.full(1000, 7), rng.standard_normal(1000), edges) == 7)


def test_conditional_matrix_averages_to_matrix(toy_matrix):
    x, w = np.polynomial.hermite_e.hermegauss(80)
    w = w / w.sum()
    avg = sum(wk * conditional_matrix(toy_matrix, 0.2, xk) for xk, wk in zip(x, w, strict=True))
    assert np.allclose(avg, toy_matrix, atol=1e-8)


def test_bad_year_matrix_has_more_defaults(toy_matrix):
    bad, good = conditional_matrix(toy_matrix, 0.2, -2), conditional_matrix(toy_matrix, 0.2, 2)
    assert np.all(bad[:7, 7] > toy_matrix[:7, 7]) and np.all(good[:7, 7] < toy_matrix[:7, 7])


def test_cumulative_default_equals_matrix_power(toy_matrix):
    cum = cumulative_default_from_matrix(toy_matrix, 5)
    assert np.allclose(cum[:, 4], np.linalg.matrix_power(toy_matrix, 5)[:, 7])
    assert np.all(np.diff(cum, axis=1) >= 0)


def test_generator_is_valid(toy_matrix):
    q = generator(toy_matrix)
    off = q - np.diag(np.diag(q))
    assert np.all(off >= 0)
    assert np.allclose(q.sum(axis=1), 0.0)
    # the zero-floor fix moves expm(Q) slightly away from P; within 0.5 percentage points here
    assert matrix_at(q, 1.0) == pytest.approx(toy_matrix, abs=5e-3)
