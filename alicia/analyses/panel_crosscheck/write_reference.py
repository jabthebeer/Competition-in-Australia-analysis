"""Write the reference panel and the Python estimates that analysis/crosscheck_panel_estimators.R checks.

The panel is synthetic (ILLUSTRATIVE, from ``panel.simulate_panel``): 8 states x 10 industries x 30
periods, four states adopting in two industries at staggered dates, effects that grow with time since
adoption, a state boom after adoption, industry cycles and a covariate. The synthetic-control family
and gsynth use the first cohort (period 12) against never-treated cells. Run from ``alicia/``:

    uv run python analyses/panel_crosscheck/write_reference.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from alicia.evaluate import cs, panel, synth

OUT = Path(__file__).resolve().parents[3] / "analysis" / "crosscheck"
SATURATED = [("state", "industry"), ("industry", "period"), ("state", "period")]
ADOPTION = {(0, 0): 12, (0, 1): 12, (1, 0): 16, (1, 1): 16, (2, 0): 20, (2, 1): 20, (3, 0): 24, (3, 1): 24}


def main() -> None:
    df = panel.simulate_panel(
        seed=2026,
        n_states=8,
        n_industries=10,
        n_periods=30,
        adoption=ADOPTION,
        effect=lambda e: 1.0 + 0.2 * e,
        control=0.8,
    )
    df["cell"] = df["state"] * 100 + df["industry"]
    df["gname"] = df["first_treated"].where(df["first_treated"] >= 0, 0)  # didimputation: 0 = never treated
    df["period1"] = df["period"] + 1  # didimputation needs positive periods; gname is shifted the same way
    df.loc[df["gname"] > 0, "gname"] += 1
    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["state", "industry", "period", "period1", "cell", "gname", "y", "D", "x", "event_time", "true_tau"]
    df[cols].to_csv(OUT / "panel_reference.csv", index=False, float_format="%.10g")

    sat = panel.feols(df, "y", ["D", "x"], fe=SATURATED, cluster="state", small="cluster")
    two = panel.feols(df, "y", ["D", "x"], fe=["cell", "period"], cluster="state", small="cluster")
    imp = panel.imputation(df, "y", "D", fe=SATURATED, controls=["x"], event_time="event_time")
    imp2 = panel.imputation(df, "y", "D", fe=["cell", "period"], controls=["x"], event_time="event_time")
    wb = panel.wild_cluster_bootstrap(
        df, "y", ["D", "x"], "D", "state", fe=SATURATED, reps=9999, seed=1, small="cluster"
    )

    # One adoption date for the synthetic-control family: cohort 12 against never-treated cells.
    single = df[df["first_treated"].isin([12, -1])]
    wide = single.pivot(index="cell", columns="period", values="y")
    treated_cells = sorted(single.loc[single["first_treated"] == 12, "cell"].unique())
    order = [c for c in wide.index if c not in treated_cells] + treated_cells  # controls first, as synthdid
    y = wide.loc[order].to_numpy()
    tr = np.zeros_like(y, bool)
    tr[-len(treated_cells) :, 12:] = True
    sd = {m: synth.sdid(y, tr, method=m).estimate for m in ("sdid", "sc", "did")}
    gs = synth.gsynth(y, tr, r=2)
    gt = cs.att_gt(df.assign(g=df["gname"]), "y", "cell", "period1", "g")
    result = {
        "note": "Python estimates on panel_reference.csv (synthetic, ILLUSTRATIVE). Compare with the R script.",
        "feols_saturated": sat.summary(),
        "feols_twoway": two.summary(),
        "imputation_saturated": {"att": imp.att, "by_event": {str(int(k)): v for k, v in imp.by_event.items()}},
        "imputation_twoway": {"att": imp2.att, "by_event": {str(int(k)): v for k, v in imp2.by_event.items()}},
        "wild_cluster_bootstrap_saturated": wb,
        "synth_single_cohort": {"treated_cells": [int(c) for c in treated_cells], "T0": 12, **sd},
        "gsynth_single_cohort_r2": {"att": gs.att},
        "cs_never_treated": {"simple": gt.simple, "dynamic": {str(int(k)): v for k, v in gt.dynamic.items()}},
        "true_att": float(df.loc[df["D"] == 1, "true_tau"].mean()),
    }
    (OUT / "panel_reference_python.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "note"}, indent=1)[:1500])


if __name__ == "__main__":
    main()
