"""Synthetic control family, factor models, matrix completion and conformal inference (ILLUSTRATIVE data)."""

from __future__ import annotations

import numpy as np
import pytest

from alicia.evaluate import synth


def factor_panel(seed: int, n: int = 30, t: int = 30, t0: int = 20, effect: float = 2.0, noise: float = 0.3):
    """One treated unit (row 0) with a high loading on a factor that rises after t0."""
    rng = np.random.default_rng(seed)
    f = np.r_[np.sin(np.arange(t0) / 3), np.linspace(1, 4, t - t0)]  # the factor jumps up after t0
    lam = rng.uniform(-1, 3, n)
    lam[0] = 2.0
    y = rng.normal(0, 1, (n, 1)) + rng.normal(0, 1, (1, t)) + np.outer(lam, f) + rng.normal(0, noise, (n, t))
    treated = np.zeros((n, t), bool)
    treated[0, t0:] = True
    y[treated] += effect
    return y, treated


def test_simplex_weights_recover_a_convex_combination():
    rng = np.random.default_rng(0)
    a = rng.normal(size=(40, 5))
    w_true = np.array([0.5, 0.3, 0.2, 0.0, 0.0])
    w = synth.simplex_weights(
        np.column_stack([a, a @ w_true]), zeta=1e-8, intercept=False, max_iter=20000, min_decrease=1e-12
    )
    assert np.allclose(w, w_true, atol=0.02) and abs(w.sum() - 1) < 1e-9


def test_factor_methods_recover_an_effect_that_did_gets_wrong():
    est = {"did": [], "sc": [], "sdid": [], "gsynth": []}
    for seed in range(12):
        y, tr = factor_panel(seed)
        for m in ("did", "sc", "sdid"):
            est[m].append(synth.sdid(y, tr, method=m).estimate)
        est["gsynth"].append(synth.gsynth(y, tr).att)
    mean = {k: np.mean(v) for k, v in est.items()}
    assert abs(mean["gsynth"] - 2.0) < 0.2
    assert abs(mean["sdid"] - 2.0) < 0.5
    assert abs(mean["sc"] - 2.0) < 0.5
    assert abs(mean["did"] - 2.0) > 1.0  # the treated unit's loading is not the average loading


def test_gsynth_cross_validation_finds_one_factor():
    picks = [synth.gsynth(*factor_panel(seed)).r for seed in range(8)]
    assert sum(r == 1 for r in picks) >= 6


def test_gsynth_handles_staggered_adoption():
    y, tr = factor_panel(3, n=40, t=30, t0=20)
    tr[1, 24:] = True  # a second unit treated later
    y[1, 24:] += 2.0
    g = synth.gsynth(y, tr, r=1)
    assert abs(g.att - 2.0) < 0.4 and np.isnan(g.att_by_period[:20]).all()


def test_matrix_completion_is_close():
    y, tr = factor_panel(5, n=25, t=25, t0=18)
    mc = synth.mc_nnm(y, tr, grid=6, folds=3)
    assert abs(mc.att - 2.0) < 0.6


def test_sdid_requires_a_single_adoption_date():
    y, tr = factor_panel(1)
    tr[1, 25:] = True
    with pytest.raises(ValueError):
        synth.sdid(y, tr)


def test_conformal_inference_covers_the_truth_and_rejects_far_values():
    rng = np.random.default_rng(2)
    t, t0 = 40, 30
    yc = rng.normal(0, 1, (10, t)) + np.linspace(0, 3, t)
    ytr = yc.mean(axis=0) + 1.0 + rng.normal(0, 0.5, t)
    ytr[t0:] += 3.0
    assert synth.conformal_pvalue(ytr, yc, t0, theta=3.0) > 0.1
    assert synth.conformal_pvalue(ytr, yc, t0, theta=0.0) <= 0.05
    ci = synth.conformal_interval(ytr, yc, t0, grid=np.linspace(0, 6, 61))
    assert ci is not None and ci[0] < 3.0 < ci[1]
    p_sc = synth.conformal_pvalue(ytr, yc, t0, theta=3.0, fit=synth.fit_sc)
    assert p_sc > 0.05
