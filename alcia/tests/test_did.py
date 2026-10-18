"""Single-treated-unit DiD toolkit, on SIMULATED panels with known effects (not real data)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alcia.evaluate.did import blind, event_study, placebo_in_space, plant, recovery, twfe


def simulated(n_units=8, years=range(2008, 2019), effect=0.0, treated="U0", first_post=2011, noise=0.0, seed=1):
    """y = unit level + common year shock + effect for the treated unit after first_post + noise."""
    rng = np.random.default_rng(seed)
    rows = []
    year_shock = {t: rng.normal(0, 1) for t in years}
    for i in range(n_units):
        u = f"U{i}"
        level = rng.normal(10, 2)
        for t in years:
            y = level + year_shock[t] + (effect if (u == treated and t >= first_post) else 0) + rng.normal(0, noise)
            rows.append({"unit": u, "time": t, "y": y})
    return pd.DataFrame(rows)


def test_twfe_recovers_a_known_effect_without_noise():
    df = simulated(effect=1.5)
    assert twfe(df, "U0", 2011) == pytest.approx(1.5, abs=1e-9)
    assert twfe(simulated(effect=0.0), "U0", 2011) == pytest.approx(0.0, abs=1e-9)


def test_event_study_is_flat_before_and_steps_after():
    es = event_study(simulated(effect=2.0), "U0", 2011)
    assert es.loc[-3] == pytest.approx(0, abs=1e-9) and es.loc[-2] == pytest.approx(0, abs=1e-9)
    assert all(es.loc[k] == pytest.approx(2.0, abs=1e-9) for k in range(0, 8))


def test_blinding_hides_only_treated_post_period():
    df = blind(simulated(effect=5.0), "U0", 2011)
    assert df.loc[(df.unit == "U0") & (df.time >= 2011), "y"].isna().all()
    assert df.loc[(df.unit == "U0") & (df.time < 2011), "y"].notna().all()
    assert df.loc[df.unit != "U0", "y"].notna().all()
    # With the treated post period hidden, no effect can be estimated.
    assert np.isnan(twfe(df, "U0", 2011))


def test_placebo_distribution_and_p_values():
    df = simulated(noise=0.3, effect=0.0)
    placebo = placebo_in_space(df, "U0", 2011)
    assert len(placebo.estimates) == 7
    assert placebo.min_p == pytest.approx(1 / 8)
    assert placebo.p_value(1e9) == pytest.approx(1 / 8)
    assert placebo.p_value(0.0) == pytest.approx(1.0)
    assert placebo.mde == pytest.approx(2.801585 * placebo.sd)


def test_planting_and_recovery_detect_large_effects():
    df = simulated(noise=0.2, effect=0.0, n_units=10)
    assert plant(df, "U3", 2011, 1.0).query("unit == 'U3' and time >= 2011")["y"].sum() == pytest.approx(
        df.query("unit == 'U3' and time >= 2011")["y"].sum() + 8.0
    )
    rec = recovery(df, "U0", 2011, [0.0, 3.0])
    big = rec[rec.planted == 3.0]
    assert (big["estimate"].sub(3.0).abs() < 0.5).all()
    assert (big["p"] == big["p"].min()).mean() > 0.8  # the planted unit ranks most extreme almost always
