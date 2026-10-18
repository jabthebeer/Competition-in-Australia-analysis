"""Panel estimators on synthetic panels with planted effects and shocks (ILLUSTRATIVE data)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alicia.evaluate import panel

SATURATED = [("state", "industry"), ("industry", "period"), ("state", "period")]


def _dummy_ols(df, y, x, fe, cluster):
    """Reference: explicit dummy-variable regression with CR1 standard errors."""
    parts = [df[x].to_numpy(float)]
    for f in fe:
        cols = [f] if isinstance(f, str) else list(f)
        key = df[cols].astype(str).agg("|".join, axis=1)
        parts.append(pd.get_dummies(key, drop_first=True, dtype=float).to_numpy())
    X = np.column_stack([np.ones(len(df)), *parts])
    keep = np.linalg.matrix_rank(X)
    beta, *_ = np.linalg.lstsq(X, df[y].to_numpy(float), rcond=None)
    u = df[y].to_numpy(float) - X @ beta
    # Cluster-robust variance for the first len(x) slopes via the FWL residualised regressors.
    xt = panel.absorb(df[x].to_numpy(float), [panel.codes(df, f) for f in fe])
    bread = np.linalg.inv(xt.T @ xt)
    cl = pd.factorize(df[cluster])[0]
    g = cl.max() + 1
    sg = np.zeros((g, len(x)))
    np.add.at(sg, cl, xt * u[:, None])
    n = len(df)
    v = g / (g - 1) * (n - 1) / (n - len(x)) * bread @ sg.T @ sg @ bread
    return beta[1 : 1 + len(x)], np.sqrt(np.diag(v)), keep


def test_absorb_matches_dummy_variable_regression_on_an_unbalanced_panel():
    df = panel.simulate_panel(seed=1, n_states=5, n_industries=4, n_periods=10, adoption={(0, 0): 5}, control=0.5)
    df = df.sample(frac=0.85, random_state=3).reset_index(drop=True)  # unbalanced
    fit = panel.feols(df, "y", ["D", "x"], fe=SATURATED, cluster="state")
    beta, se, _ = _dummy_ols(df, "y", ["D", "x"], SATURATED, "state")
    assert np.allclose(fit.coef.to_numpy(), beta, atol=1e-7)
    assert np.allclose(fit.se.to_numpy(), se, atol=1e-7)


def test_saturated_fixed_effects_remove_a_state_boom_and_industry_cycles():
    # The treated state booms after adoption (state x period shock) and industries have their own cycles.
    est = {"twoway": [], "saturated": []}
    for seed in range(20):
        df = panel.simulate_panel(seed=seed, effect=2.0, state_shock=3.0, industry_shock=3.0)
        est["twoway"].append(panel.feols(df, "y", ["D"], fe=[("state", "industry"), "period"]).coef["D"])
        est["saturated"].append(panel.feols(df, "y", ["D"], fe=SATURATED).coef["D"])
    assert abs(np.mean(est["saturated"]) - 2.0) < 0.15
    assert np.mean(est["twoway"]) - 2.0 > 1.5  # the boom is credited to the reform without g_st


def test_imputation_recovers_staggered_dynamic_effects():
    # Four states adopt in two industries at different dates; effects grow with time since adoption.
    adoption = {(0, 0): 10, (1, 0): 18, (2, 0): 26, (3, 0): 34, (0, 1): 10, (1, 1): 18, (2, 1): 26, (3, 1): 34}
    att, att_true = [], []
    for seed in range(10):
        df = panel.simulate_panel(seed=seed, adoption=adoption, effect=lambda e: 0.5 * e, n_periods=44)
        imp = panel.imputation(df, "y", "D", fe=SATURATED, event_time="event_time")
        att.append(imp.att)
        att_true.append(df.loc[df["D"] == 1, "true_tau"].mean())
        assert imp.n_unidentified == 0
        true_by_e = df[df["D"] == 1].groupby("event_time")["true_tau"].mean()
        assert np.allclose(imp.by_event.loc[[0, 5, 9]], true_by_e.loc[[0, 5, 9]], atol=2.5)
    assert abs(np.mean(att) - np.mean(att_true)) < 0.3


def test_static_regression_misweights_dynamic_effects_when_every_cell_is_eventually_treated():
    # Cell and period effects only; cohorts adopt at 8, 14, 20 and 26 (the last serves as not yet treated).
    att, static, truth = [], [], []
    for seed in range(8):
        adoption = {(s, i): (8, 14, 20, 26)[(2 * s + i) % 4] for s in range(4) for i in range(2)}
        df = panel.simulate_panel(
            seed=seed,
            n_states=4,
            n_industries=2,
            n_periods=26,
            adoption=adoption,
            effect=lambda e: 0.5 * e,
            state_shock=0.0,
            industry_shock=0.0,
        )
        fe = [("state", "industry"), "period"]
        att.append(panel.imputation(df, "y", "D", fe=fe).att)
        static.append(panel.feols(df, "y", ["D"], fe=fe).coef["D"])
        truth.append(df.loc[df["D"] == 1, "true_tau"].mean())
    assert abs(np.mean(att) - np.mean(truth)) < 0.4
    assert np.mean(truth) - np.mean(static) > 1.0  # long-run effects get too little weight


def test_imputation_with_a_control_correlated_with_treatment():
    est = []
    for seed in range(10):
        df = panel.simulate_panel(seed=seed, control=1.5, effect=2.0)
        imp = panel.imputation(df, "y", "D", fe=SATURATED, controls=["x"])
        est.append(imp.att)
        assert abs(imp.beta["x"] - 1.0) < 0.1
    assert abs(np.mean(est) - 2.0) < 0.3


def test_imputation_marks_effects_it_cannot_identify():
    df = panel.simulate_panel(seed=0, n_states=4, n_industries=3, n_periods=8, adoption={(0, 0): 0})
    imp = panel.imputation(df, "y", "D", fe=SATURATED)  # the cell is treated in every period
    assert imp.n_unidentified == imp.n_treated and np.isnan(imp.att)


def test_wild_cluster_bootstrap_agrees_with_the_regression_and_detects_a_large_effect():
    df = panel.simulate_panel(seed=4, n_states=12, adoption={(a, 0): 20 for a in range(6)}, effect=3.0)
    fit = panel.feols(df, "y", ["D"], fe=SATURATED, cluster="state")
    wb = panel.wild_cluster_bootstrap(df, "y", ["D"], "D", "state", fe=SATURATED, reps=399, seed=1)
    assert wb["t"] == pytest.approx(fit.t("D")) and wb["clusters"] == 12
    assert wb["p_value"] < 0.05
    null = panel.wild_cluster_bootstrap(df, "y", ["D"], "D", "state", fe=SATURATED, reps=399, null=fit.coef["D"])
    assert null["p_value"] > 0.5  # testing the estimate itself


def test_wild_cluster_bootstrap_size_under_the_null():
    rejections = 0
    for seed in range(40):
        df = panel.simulate_panel(seed=100 + seed, n_states=10, adoption={(a, 0): 20 for a in range(5)}, effect=0.0)
        wb = panel.wild_cluster_bootstrap(df, "y", ["D"], "D", "state", fe=SATURATED, reps=199, seed=seed)
        rejections += wb["p_value"] < 0.10
    assert rejections <= 9  # about 4 expected at the 10% level


def test_placebo_null_gives_randomization_inference_across_cells():
    df = panel.simulate_panel(seed=7, effect=4.0, noise=0.5)

    def estimate(cell):
        s, i = cell
        d = df.assign(P=((df["state"] == s) & (df["industry"] == i) & (df["period"] >= 24)).astype(float))
        return panel.feols(d[(d["state"] != 0) | (d["industry"] != 0) | (d["P"] == 1)], "y", ["P"], fe=SATURATED).coef[
            "P"
        ]

    placebos = [(s, i) for s in range(1, 8) for i in range(1, 12)]
    null = panel.placebo_null(estimate, placebos)
    est = panel.feols(df, "y", ["D"], fe=SATURATED).coef["D"]
    assert null.p_value(est) < 0.05
    lo, hi = null.interval(est)
    assert lo < 4.0 < hi


def test_shift_share_builds_exposure_weighted_shocks():
    weights = pd.Series({("WA", "mining"): 0.4, ("WA", "other"): 0.6, ("NSW", "mining"): 0.02, ("NSW", "other"): 0.98})
    shocks = pd.DataFrame({"mining": [0.0, 1.0], "other": [0.0, 0.1]}, index=["2020", "2021"])
    out = panel.shift_share(weights, shocks)
    assert out.loc["2021", "WA"] == pytest.approx(0.46) and out.loc["2021", "NSW"] == pytest.approx(0.118)


def test_imputation_first_stage_weights_match_weighted_least_squares():
    df = panel.simulate_panel(seed=11, n_states=5, n_industries=4, n_periods=12, adoption={(0, 0): 8})
    df["w"] = np.random.default_rng(0).integers(5, 500, len(df)).astype(float)
    imp = panel.imputation(df, "y", "D", fe=SATURATED, weights="w", first_stage_weights=True)
    # Reference: weighted dummy regression on untreated rows, predictions for treated rows.
    un, tr = df[df["D"] == 0], df[df["D"] == 1]
    keys = [un.assign(k=un[list(f)].astype(str).agg("|".join, axis=1))["k"] for f in SATURATED]
    cats = [pd.Categorical(k) for k in keys]
    x = np.column_stack([np.ones(len(un))] + [pd.get_dummies(c, drop_first=True, dtype=float).to_numpy() for c in cats])
    sw = np.sqrt(un["w"].to_numpy())
    b, *_ = np.linalg.lstsq(x * sw[:, None], un["y"].to_numpy() * sw, rcond=None)
    tk = [tr.assign(k=tr[list(f)].astype(str).agg("|".join, axis=1))["k"] for f in SATURATED]
    xt = np.column_stack(
        [np.ones(len(tr))]
        + [
            pd.get_dummies(pd.Categorical(k, categories=c.categories), drop_first=True, dtype=float).to_numpy()
            for k, c in zip(tk, cats, strict=True)
        ]
    )
    tau = tr["y"].to_numpy() - xt @ b
    assert imp.att == pytest.approx(np.average(tau, weights=tr["w"]), abs=1e-6)
