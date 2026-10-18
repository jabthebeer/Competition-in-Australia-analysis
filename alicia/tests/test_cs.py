"""Callaway-Sant'Anna group-time effects (ILLUSTRATIVE data)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from alicia.evaluate import cs


def staggered(seed: int, n: int = 300, t: int = 10, confound: bool = False):
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n)
    cohort = rng.choice([0, 4, 6, 8], size=n, p=[0.4, 0.2, 0.2, 0.2])
    if confound:  # units with high x adopt more often and also trend up faster
        cohort = np.where((x > 0.5) & (rng.random(n) < 0.8), rng.choice([4, 6, 8], size=n), cohort)
    rows = []
    for i in range(n):
        a = rng.normal()
        for tt in range(1, t + 1):
            e = tt - cohort[i]
            tau = (1.0 + 0.5 * e) if cohort[i] and e >= 0 else 0.0
            yv = a + 0.3 * tt + (1.0 * x[i] * tt if confound else 0) + tau + rng.normal(0, 0.5)
            rows.append({"unit": i, "time": tt, "g": cohort[i], "x": x[i], "y": yv, "tau": tau, "cl": i % 25})
    return pd.DataFrame(rows)


def test_group_time_effects_recover_dynamic_effects():
    df = staggered(0)
    res = cs.att_gt(df, "y", "unit", "time", "g")
    assert abs(res.dynamic.loc[0] - 1.0) < 0.15 and abs(res.dynamic.loc[2] - 2.0) < 0.2
    assert res.table.loc[~res.table["post"], "att"].abs().max() < 0.4  # no pre-trends
    truth = df[df["tau"] > 0]["tau"].mean()
    assert abs(res.simple - truth) < 0.3


def test_doubly_robust_covariates_remove_confounded_trends():
    df = staggered(1, confound=True)
    plain = cs.att_gt(df, "y", "unit", "time", "g")
    dr = cs.att_gt(df, "y", "unit", "time", "g", covariates=("x",))
    # Two periods after adoption (true effect 2.0) the confounded trend has run for three periods.
    assert abs(dr.dynamic.loc[2] - 2.0) < 0.3
    assert plain.dynamic.loc[2] - 2.0 > 0.5


def test_not_yet_treated_controls_and_bootstrap():
    df = staggered(2)
    res = cs.att_gt(df, "y", "unit", "time", "g", control="notyet")
    assert abs(res.dynamic.loc[0] - 1.0) < 0.2
    draws = cs.cluster_bootstrap(
        df, "cl", lambda d: cs.att_gt(d, "y", "unit", "time", "g").simple, reps=30, unit="unit"
    )
    assert len(draws) == 30 and 0 < draws.std() < 0.5
