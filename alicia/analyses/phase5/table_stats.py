"""Sample statistics for the Phase 5 regression tables (derived; estimates nothing new).

For each case and outcome, rebuild the registered run's panel (treated cells restored, as in run.py's estimate
stage) and record what a regression table reports under each estimator: observations, units, treated cells,
periods, states, classes and the treated group's pre-reform mean. Every layer is re-fitted and its estimate
checked against estimate.json, so the table's sample is the one the registered estimates came from.

    uv run python analyses/phase5/table_stats.py --spec phase5-reevaluations

Writes analyses/phase5/<folder>/table_stats.json.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import warnings
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("phase5_run", HERE / "run.py")
run = importlib.util.module_from_spec(_spec)
sys.modules["phase5_run"] = run
_spec.loader.exec_module(run)
power, prices = run.power, run.prices

from alicia.evaluate import panel  # noqa: E402
from alicia.runner.spec import load  # noqa: E402

FE = {"twoway": ["cell", "fy"], "state_year": ["cell", ("state", "fy")], "saturated": run.SAT}
TOLERANCE = 1e-3  # estimate.json rounds to 4 decimals


def label(o: dict, t: int) -> str:
    return f"{t // 4}-Q{t % 4 + 1}" if o["kind"] == "price" else f"{t - 1}-{str(t)[2:]}"


def outcome_stats(case_id: str, o: dict, registered: dict) -> dict:
    c = run.case_obj(case_id, o)
    classes = list(c.classes)
    df = run.outcome_panel(case_id, o, blind=False)
    d = power.assign(df, c.cohorts, classes)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        est = power.estimate_all(df, c.cohorts, c.start, classes)
    diffs = {
        k: abs(est[k] - registered[k]["plain"])
        for k in est
        if registered[k]["plain"] is not None and np.isfinite(est[k])
    }
    layers = {}
    for k, fe in FE.items():
        layers[k] = {"nobs": panel.feols(d, "y", ["D"], fe=fe, weights="w").nobs, "units": int(d["cell"].nunique())}
    dc = d.dropna(subset=list(power.COVARIATES))
    layers["controls"] = {"nobs": int(len(dc)), "units": int(dc["cell"].nunique())}
    layers["imputation"] = {"nobs": int(len(d)), "units": int(d["cell"].nunique())}
    for k in ("sdid", "gsynth"):
        units = obs = 0
        for cohort in c.cohorts:
            m = power._matrix(d, c.cohorts, c.start, cohort, classes)
            if m is None or m[2] < 2:
                continue
            units += m[0].shape[0]
            obs += m[0].size
        layers[k] = {"nobs": obs, "units": units}
    treated = d["cls"].isin(classes) & d["state"].isin({s for x in c.cohorts for s in x.treated})
    pre = np.zeros(len(d), bool)
    for x in c.cohorts:
        pre |= (d["cls"].isin(classes) & d["state"].isin(x.treated) & (d["fy"] < x.first_post)).to_numpy()
    return {
        "reproduces": all(v < TOLERANCE for v in diffs.values()),
        "max_abs_difference": round(max(diffs.values()), 6) if diffs else None,
        "layers": layers,
        "cells": int(d["cell"].nunique()),
        "treated_cells": int(d.loc[treated, "cell"].nunique()),
        "treated_observations": int(d["D"].sum()),
        "periods": [label(o, int(d["fy"].min())), label(o, int(d["fy"].max()))],
        "n_periods": int(d["fy"].nunique()),
        "states": sorted(d["state"].unique().tolist()),
        "classes": int(d["cls"].nunique()),
        "pre_mean_treated": round(float(np.average(d.loc[pre, "y"], weights=d.loc[pre, "w"])), 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True, choices=sorted(run.FOLDERS))
    args = ap.parse_args()
    spec = load(args.spec)
    folder = HERE / run.FOLDERS[args.spec]
    est = json.loads((folder / "estimate.json").read_text("utf-8"))
    by_id = {x["id"]: x for x in est["cases"]}
    out = {"spec": args.spec, "source": "estimate stage panels (treated cells restored)", "cases": []}
    for case in spec.cases:
        res = by_id[case["id"]]
        outs = {}
        for o in case["outcomes"]:
            r = res["outcomes"][o["key"]]
            if not r["feasible"]["ok"]:
                continue
            outs[o["key"]] = outcome_stats(case["id"], o, r["layers"])
            s = outs[o["key"]]
            print(f"  {case['id']} {o['key']}: N={s['layers']['saturated']['nobs']} reproduces={s['reproduces']}")
        out["cases"].append({"id": case["id"], "outcomes": outs})
    bad = [(c["id"], k) for c in out["cases"] for k, v in c["outcomes"].items() if not v["reproduces"]]
    if bad:
        raise SystemExit(f"re-fitted estimates differ from estimate.json: {bad}")
    path = folder / "table_stats.json"
    path.write_text(json.dumps(out, indent=1) + "\n", "utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
