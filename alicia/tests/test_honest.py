"""Rambachan-Roth style sensitivity bounds."""

from __future__ import annotations

import numpy as np
import pytest

from alicia.evaluate import honest


def test_relative_magnitudes_bounds_scale_with_the_largest_pre_step():
    # pre: beta_-3 = 0.2, beta_-2 = -0.1 (reference -1 = 0): steps 0.3 and 0.1 -> largest 0.3
    beta = np.array([0.2, -0.1, 1.0, 1.2])
    b = honest.relative_magnitudes(beta, 2, mbar=1.0)
    # average of two post periods: |sum_{t>=0} l| + |sum_{t>=1} l| = 1 + 0.5 = 1.5, times 0.3
    assert b.lower == pytest.approx(1.1 - 0.45) and b.upper == pytest.approx(1.1 + 0.45)
    assert honest.relative_magnitudes(beta, 2, mbar=0.0).lower == pytest.approx(1.1)
    assert honest.breakdown(beta, 2, "RM") == pytest.approx(1.1 / 0.45)


def test_smoothness_extrapolates_the_pre_trend():
    # A linear pre-trend of slope 0.1 continues: delta_0 = 0.1, delta_1 = 0.2
    beta = np.array([-0.2, -0.1, 0.1, 0.2])
    b = honest.smoothness(beta, 2, m=0.0)
    assert b.feasible and b.lower == pytest.approx(0.0) and b.upper == pytest.approx(0.0)
    wide = honest.smoothness(beta, 2, m=0.05)
    assert wide.lower < 0 < wide.upper
    # M large enough to include zero from an effect of 1 on a flat pre-trend
    flat = np.array([0.0, 0.0, 1.0, 1.0])
    m = honest.breakdown(flat, 2, "SD")
    assert honest.smoothness(flat, 2, m=m).lower == pytest.approx(0.0, abs=1e-9)


def test_smoothness_flags_pre_periods_that_break_the_bound():
    beta = np.array([0.5, -0.5, 0.0])  # large pre-period curvature
    assert not honest.smoothness(beta, 2, m=0.1).feasible
    assert honest.breakdown(beta, 2, "SD") >= 1.0


def test_confidence_interval_adds_sampling_error():
    beta = np.array([0.0, 0.0, 1.0])
    b = honest.relative_magnitudes(beta, 2, mbar=1.0, se_post=0.2)
    assert b.ci_lower == pytest.approx(1.0 - 1.645 * 0.2)
