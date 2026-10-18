"""Stacked difference-in-differences, on SIMULATED panels with known effects (not real data)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alcia.evaluate.stacked import Cohort, blind_cohorts, did, event, stacked, stacked_event


def panel(adopt: dict[str, int], effect=1.0, years=range(2008, 2019), n_never=3, noise=0.0, seed=3, dynamic=0.0):
    """Units adopt in the given years (others never); the effect may grow by `dynamic` a year."""
    rng = np.random.default_rng(seed)
    shock = {t: rng.normal(0, 1) for t in years}
    units = {**adopt, **{f"N{i}": None for i in range(n_never)}}
    rows = []
    for u, g in units.items():
        level = rng.normal(10, 2)
        for t in years:
            eff = effect + dynamic * (t - g) if g is not None and t >= g else 0.0
            rows.append({"unit": u, "time": t, "y": level + shock[t] + eff + rng.normal(0, noise)})
    return pd.DataFrame(rows)


def test_did_with_several_treated_units_recovers_the_effect():
    df = panel({"A": 2012, "B": 2012}, effect=2.0)
    assert did(df, ["A", "B"], 2012) == pytest.approx(2.0, abs=1e-9)


def test_stacked_avoids_forbidden_comparisons_under_dynamic_effects():
    # Effects that grow over time bias plain two-way fixed effects under staggered timing.
    df = panel({"A": 2011, "B": 2014}, effect=1.0, dynamic=1.0, n_never=3)
    never = ("N0", "N1", "N2")
    cohorts = [Cohort(("A",), 2011, 2018, never), Cohort(("B",), 2014, 2018, never)]
    # Truth: average effect over each cohort's post years, weighted equally.
    truth_a = np.mean([1 + (t - 2011) for t in range(2011, 2019)])
    truth_b = np.mean([1 + (t - 2014) for t in range(2014, 2019)])
    assert stacked(df, cohorts, 2008) == pytest.approx((truth_a + truth_b) / 2, abs=1e-9)


def test_stacked_event_is_flat_before_and_matches_the_dynamic_path_after():
    df = panel({"A": 2011, "B": 2013}, effect=1.0, dynamic=0.5)
    never = ("N0", "N1", "N2")
    es = stacked_event(df, [Cohort(("A",), 2011, 2018, never), Cohort(("B",), 2013, 2018, never)], 2008)
    assert all(es.loc[k] == pytest.approx(0, abs=1e-9) for k in es.index if k < -1)
    assert all(es.loc[k] == pytest.approx(1 + 0.5 * k, abs=1e-9) for k in es.index if k >= 0)
    assert event(df, ["A"], 2011).loc[0] == pytest.approx(1.0, abs=1e-9)


def test_blinding_hides_each_cohort_from_its_own_date():
    df = panel({"A": 2011, "B": 2014})
    cohorts = [Cohort(("A",), 2011, 2018, ("N0",)), Cohort(("B",), 2014, 2018, ("N0",))]
    b = blind_cohorts(df, cohorts)
    assert b.query("unit == 'A' and time >= 2011")["y"].isna().all()
    assert b.query("unit == 'B' and time < 2014")["y"].notna().all()
    assert b.query("unit == 'B' and time >= 2014")["y"].isna().all()
    assert np.isnan(stacked(b, cohorts, 2008))


def test_on_off_stagger_recovers_planted_effects():
    """ILLUSTRATIVE simulated panel: early units adopt at t=10, the late unit at t=14."""
    import numpy as np

    from alcia.evaluate import stagger

    rng = np.random.default_rng(1)
    rows = []
    for u in ["L", "E1", "E2", "E3"]:
        for t in range(24):
            seasonal = 2.0 * (t % 4 == 0) if u == "L" else 0.0  # the late unit has its own season
            adopt = 14 if u == "L" else 10
            effect = 5.0 if t >= adopt else 0.0
            rows.append({"unit": u, "time": t, "y": 0.3 * t + seasonal + effect + rng.normal(0, 0.01)})
    df = pd.DataFrame(rows)
    w = stagger.Windows(pre_start=2, t1=10, t2=14, end=21)
    est = stagger.estimates(df, "L", ["E1", "E2", "E3"], w, season=lambda t: t % 4)
    assert abs(est["early"] - 5.0) < 0.1 and abs(est["late"] - 5.0) < 0.1 and abs(est["pooled"] - 5.0) < 0.1
    assert abs(est["off_vs_pre"]) < 0.1  # the gap closes once the late unit catches up
    path = stagger.event_path(df, "L", ["E1", "E2", "E3"], w, season=lambda t: t % 4)
    assert abs(path.loc[11] + 5.0) < 0.1 and abs(path.loc[15]) < 0.1
    null = stagger.Null(pd.Series(rng.normal(0, 1, 999)))
    assert null.p_value(10.0) == 1 / 1000 and null.interval(0.0)[0] < 0 < null.interval(0.0)[1]
    assert 2.5 < null.mde < 3.1
