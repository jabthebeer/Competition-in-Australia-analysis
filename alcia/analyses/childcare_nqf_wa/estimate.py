"""Registered estimation for the NQF-in-WA evaluation (docs/pap_childcare_nqf_wa.md).

--blind: dry run with WA's childcare outcomes hidden from January 2012; it must reproduce the design
stage's no-effect distributions (design.json) and estimate nothing for WA. Without --blind: the one
registered run, written to estimate.json.

Run: uv run python analyses/childcare_nqf_wa/estimate.py [--blind]
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd
import spec

from alcia.evaluate.stagger import Null

HERE = Path(__file__).resolve().parent
ESTIMANDS = ("pooled", "early", "late", "off_vs_pre")


def num(x, nd: int = 3):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), nd)


def result(est: float, null: pd.Series) -> dict:
    n = Null(null)
    ok = not math.isnan(est)
    lo90, hi90 = n.interval(est, 0.9) if ok else (None, None)
    return {
        "estimate": num(est),
        "p": num(n.p_value(est), 4) if ok else None,
        "interval_90": [num(lo90), num(hi90)],
        "null": n.summary(),
    }


def finding(r: dict) -> str:
    if r["p"] is None:
        return "not-identified"
    if r["p"] < 0.10:
        return "increase" if r["estimate"] > 0 else "decrease"
    return "no-detectable-effect"


def outcome(childcare, placebos, windows, first_data, hide: bool, season=spec.quarter) -> dict:
    data = spec.hide(childcare, windows.t1) if hide else childcare
    out = {}
    for trend in (False, True):
        nul = spec.null(placebos, data, windows, first_data, season, trend)
        est = spec.estimate(data, windows, season, trend)
        key = "detrended" if trend else "main"
        out[key] = {e: result(est[e], nul[e]) for e in ESTIMANDS if e != "off_vs_pre"}
        out[key]["off_vs_pre"] = num(est["off_vs_pre"])
    out["main"]["pooled"]["finding"] = finding(out["main"]["pooled"])
    gaps = spec.path(data, windows, season)
    out["path"] = [{"time": str(t.date()), "gap": num(v)} for t, v in gaps.items()]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blind", action="store_true")
    hide = ap.parse_args().blind

    abn = spec.abn_counts()
    ent = spec.abn_counts("abn_active_since")
    hours, emp = spec.lfs("hours_actual"), spec.lfs("employed")
    groups = spec.lfs_placebos(hours)
    rel = spec.cpi()
    classes = [c for c in spec.cpi_placebos() if c in rel.index.get_level_values(0)]
    abn_start, lfs_start = pd.Timestamp("1999-07-01"), pd.Timestamp("1985-01-01")
    out = {
        "blind": hide,
        "exits": outcome(
            spec.abn_panel(abn, spec.CHILDCARE_CLASS),
            {c: spec.abn_panel(abn, c) for c in spec.abn_placebos(abn)},
            spec.MONTHLY,
            abn_start,
            hide,
        ),
        "prices": outcome(
            spec.cpi_panel(rel, spec.CPI_CHILD_CARE),
            {c: spec.cpi_panel(rel, c) for c in classes},
            spec.QUARTERLY,
            rel.index.get_level_values("period").min(),
            hide,
        ),
        "entries": outcome(
            spec.abn_panel(ent, spec.CHILDCARE_CLASS),
            {c: spec.abn_panel(ent, c) for c in spec.abn_placebos(ent)},
            spec.MONTHLY,
            abn_start,
            hide,
        ),
        "hours": outcome(
            spec.lfs_panel(hours, spec.CHILDCARE_GROUP),
            {g: spec.lfs_panel(hours, g) for g in groups},
            spec.QUARTERLY,
            lfs_start,
            hide,
        ),
        "employment": outcome(
            spec.lfs_panel(emp, spec.CHILDCARE_GROUP),
            {g: spec.lfs_panel(emp, g) for g in groups},
            spec.QUARTERLY,
            lfs_start,
            hide,
        ),
    }
    ps = {k: out[k]["main"]["pooled"]["p"] for k in ("exits", "prices") if out[k]["main"]["pooled"]["p"] is not None}
    if ps:
        items = sorted(ps.items(), key=lambda kv: kv[1])
        q, qs = 1.0, {}
        for i in range(len(items) - 1, -1, -1):
            q = min(q, items[i][1] * len(items) / (i + 1))
            qs[items[i][0]] = round(q, 4)
        out["q_values"] = qs

    design = json.loads((HERE / "design.json").read_text("utf-8"))
    for k in ("exits", "prices", "entries", "hours"):
        for e in ("pooled", "early", "late"):
            got, want = out[k]["main"][e]["null"], design[k]["null"][e]
            assert got["n"] == want["n"] and abs(got["sd"] - want["sd"]) < 1e-6, f"{k}/{e}: null differs"
    out["null_matches_design_stage"] = True

    name = "estimate_blind.json" if hide else "estimate.json"
    (HERE / name).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for k in ("exits", "prices", "entries", "hours", "employment"):
        m = out[k]["main"]
        print(
            f"{k:10s} pooled={m['pooled']['estimate']} p={m['pooled']['p']} 90%={m['pooled']['interval_90']} "
            f"early={m['early']['estimate']} late={m['late']['estimate']} off-pre={m['off_vs_pre']} "
            f"| detrended pooled={out[k]['detrended']['pooled']['estimate']} p={out[k]['detrended']['pooled']['p']}"
        )
    print("q:", out.get("q_values"), "->", name)


if __name__ == "__main__":
    main()
