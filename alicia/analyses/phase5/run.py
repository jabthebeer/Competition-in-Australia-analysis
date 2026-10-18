"""Forward plan Phase 5: one runner for every case in a Phase 5 specification.

Each case is an evaluation (a re-evaluation of an earlier study, or a first evaluation of a new family). Its
outcomes, cohorts, classes, windows and the estimator layer for each outcome are written in the specification
(``alicia/specs/phase5-*.json``) before any treated post-reform outcome is computed. The layers were chosen in
the blinded power study (docs/power_study.md, section 4).

    uv run python analyses/phase5/run.py --spec phase5-reevaluations --stage design     # blinded design
    uv run python analyses/phase5/run.py --spec phase5-reevaluations --stage dry-run    # blinded dry run
    uv run python analyses/phase5/run.py --spec phase5-reevaluations --stage estimate   # the registered run

Design (blinded): every treated cell is deleted from its first exposed period on (``power_study/run.py:
hide``). Reported per outcome: feasibility; every layer's estimate for each placebo industry group (or CPI
class), giving each layer's no-effect distribution and smallest detectable effect; the registered layer under
the own-class placebo families (states that never adopted, fake dates); placebo event-study coefficients; and
the treated group's own pre-reform event-study coefficients (the pre-trend check).

Dry run: the estimate stage with treated cells still hidden. It must run end to end and estimate nothing.

Estimate: treated cells restored (treated states still end with their window). Every layer's estimate on the
reform's own classes, judged against the same layer's placebo distribution from the design stage (rank
p-value centred on the placebo mean; 90% interval from placebo quantiles), the registered layer marked;
event-study coefficients net of the placebo mean with placebo bands; Benjamini-Hochberg q-values across the
specification's primary outcomes; the registered decision rule and grade.

Writes analyses/phase5/<folder>/design.json, estimate_blind.json or estimate.json.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
import warnings
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("power_prices", HERE.parent / "power_study" / "prices.py")
prices = importlib.util.module_from_spec(_spec)
sys.modules["power_prices"] = prices
_spec.loader.exec_module(prices)
power = prices.power  # analyses/power_study/run.py
batch = power.batch  # analyses/high_evaluability/run.py

from alicia.evaluate import panel  # noqa: E402
from alicia.evaluate.stacked import Cohort  # noqa: E402
from alicia.runner.spec import load  # noqa: E402

SAT = ["cell", ("cls", "fy"), ("state", "fy")]
FOLDERS = {"phase5-reevaluations": "reevaluations", "phase5-new-families": "new_families"}


# ---- case definitions ----------------------------------------------------------------------------------


def quarter(text: str) -> int:
    year, q = text.split("-Q")
    return int(year) * 4 + int(q) - 1


def period(o: dict):
    return quarter if o["kind"] == "price" else int


def cohorts_of(o: dict) -> tuple[Cohort, ...]:
    f = period(o)
    return tuple(
        Cohort(tuple(c["treated"]), f(c["first_post"]), f(c["last_post"]), tuple(c["controls"])) for c in o["cohorts"]
    )


def case_obj(case_id: str, o: dict) -> SimpleNamespace:
    classes = (o["code"],) if o["kind"] == "price" else tuple(o["classes"])
    return SimpleNamespace(id=case_id, classes=classes, cohorts=cohorts_of(o), start=period(o)(o["start"]))


def price_reform(case_id: str, o: dict):
    c = case_obj(case_id, o)
    return prices.PriceReform(
        id=case_id,
        title=case_id,
        records=(),
        codes=(o["code"],),
        cohorts=c.cohorts,
        exclude_subgroups=tuple(o["exclude_subgroups"]),
        start=c.start,
    )


# ---- panels and placebo pools -------------------------------------------------------------------------------


def outcome_panel(case_id: str, o: dict, blind: bool) -> pd.DataFrame:
    c = case_obj(case_id, o)
    if o["kind"] == "price":
        return prices.price_panel(price_reform(case_id, o), c, blind=blind)
    return power.cell_panel(power.cabee(False), c, o["measure"], blind=blind)


def placebo_pool(case_id: str, o: dict, max_placebos: int) -> tuple[list[list[str]], list[str], float | None]:
    """(placebo groups, reasons the outcome is not feasible, treated group's businesses in the base year)."""
    if o["kind"] == "price":
        return [[c] for c in prices.placebo_classes(price_reform(case_id, o), max_placebos)], [], None
    pg = batch.placebo_groups(power.cabee(False), case_obj(case_id, o))
    reasons = []
    if pg["treated_size"] < batch.MIN_TREATED:
        reasons.append(
            f"treated group has {pg['treated_size']:.0f} businesses in the base year (rule: {batch.MIN_TREATED})"
        )
    if len(pg["groups"]) < batch.MIN_PLACEBOS:
        reasons.append(f"only {len(pg['groups'])} placebo groups (rule: {batch.MIN_PLACEBOS})")
    return pg["groups"][:max_placebos], reasons, float(pg["treated_size"])


def own_draws(case_id: str, o: dict) -> dict[str, list[tuple[Cohort, ...]]]:
    c = case_obj(case_id, o)
    if o["kind"] == "price":
        return power.own_class_draws(c, step=4, min_pre=8, first_year={})
    return power.own_class_draws(c)


# ---- event study -----------------------------------------------------------------------------------------------


def event_window(o: dict) -> tuple[int, int]:
    c = case_obj("", o)
    step = 4 if o["kind"] == "price" else 1
    fp = min(x.first_post for x in c.cohorts)
    span = max(x.last_post - x.first_post for x in c.cohorts) // step
    pre = (fp - c.start) // step
    return -min(5, pre), min(5, span)


def event_coefs(df: pd.DataFrame, o: dict, cohorts, classes) -> dict[int, float]:
    """Saturated-effects event study: one coefficient per event year, k = -1 omitted, ends binned."""
    kmin, kmax = event_window(o)
    step = 4 if o["kind"] == "price" else 1
    k = np.full(len(df), np.nan)
    for c in cohorts:
        on = (df["state"].isin(c.treated) & df["cls"].isin(classes) & (df["fy"] <= c.last_post)).to_numpy()
        rel = np.floor((df["fy"].to_numpy() - c.first_post) / step)
        k[on] = rel[on]
    k = np.clip(k, kmin, kmax)
    d = df.copy()
    cols = []
    for kk in range(kmin, kmax + 1):
        col = (k == kk).astype(float)
        if kk == -1 or col.sum() == 0:
            continue
        d[f"k{kk}"] = col
        cols.append(f"k{kk}")
    if not cols:
        return {}
    try:
        fit = panel.feols(d, "y", cols, fe=SAT, weights="w")
    except np.linalg.LinAlgError:
        return {}
    return {int(c[1:]): float(fit.coef[c]) for c in cols}


def band(values: list[dict[int, float]], k: int, level: float) -> tuple[float, float] | None:
    v = np.array([x[k] for x in values if k in x and np.isfinite(x[k])])
    if len(v) < 5:
        return None
    c = v - v.mean()
    lo, hi = np.quantile(c, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


# ---- stages ------------------------------------------------------------------------------------------------------


def num(x, nd: int = 4):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), nd)


def design_outcome(case_id: str, o: dict, max_placebos: int) -> dict:
    t0 = time.time()
    c = case_obj(case_id, o)
    groups, reasons, size = placebo_pool(case_id, o, max_placebos)
    out = {
        "key": o["key"],
        "kind": o["kind"],
        "layer": o["layer"],
        "checks": o.get("checks", []),
        "feasible": {"ok": not reasons, "reasons": reasons, "treated_size": size},
    }
    if reasons:
        return out
    df = outcome_panel(case_id, o, blind=True)
    power.assert_blind(df, c)
    rows = [power.estimate_all(df, c.cohorts, c.start, g) for g in groups]
    own = {}
    for fam, draws in own_draws(case_id, o).items():
        est = []
        for cohorts in draws:
            last = max(x.last_post for x in cohorts)
            est.append(power.estimate_all(df[df["fy"] <= last], cohorts, c.start, list(c.classes), (o["layer"],)))
        v = [r[o["layer"]] for r in est]
        own[fam] = {
            "draws": len(draws),
            "estimates": [num(x) for x in v],
            "cohorts": [power.describe(x) for x in draws],
        }
    ev_placebo = [event_coefs(df, o, c.cohorts, g) for g in groups]
    ev_treated_pre = event_coefs(df, o, c.cohorts, list(c.classes))  # only pre-reform rows are left
    shock = {k: float(np.mean([e[k] for e in ev_placebo if k in e])) for k in ev_treated_pre}
    inside = []
    for k, v in ev_treated_pre.items():
        b = band(ev_placebo, k, 0.95)
        if k <= -2 and b is not None:
            inside.append(b[0] <= v - shock[k] <= b[1])
    out |= {
        "cells": int(df["cell"].nunique()),
        "rows": int(len(df)),
        "mean": num(np.average(df["y"], weights=df["w"]), 3),
        "placebo_groups": groups,
        "placebo_estimates": [{k: num(v) for k, v in r.items()} for r in rows],
        "layers": power.layer_table(rows),
        "own_class": own,
        "event": {
            "window": list(event_window(o)),
            "placebo": [{str(k): num(v) for k, v in e.items()} for e in ev_placebo],
            "treated_pre": {str(k): num(v) for k, v in ev_treated_pre.items()},
            "pre_inside_95": all(inside) if inside else None,
        },
    }
    print(
        f"  {case_id} {o['key']}: {len(groups)} placebos in {time.time() - t0:.0f}s; registered {o['layer']} "
        f"MDE {out['layers'][o['layer']]['mde']}; pre-trend inside 95%: {out['event']['pre_inside_95']}",
        flush=True,
    )
    return out


def decide(hypothesis: str, kind: str, measure: str, est: float, sig: bool) -> str:
    if not sig:
        return "inconclusive"
    if hypothesis == "mixed":
        return "detects-increase" if est > 0 else "detects-decrease"
    # Enhancing competition: more entry, lower prices. Weakening: the reverse.
    good = est > 0 if kind == "business" else est < 0
    if measure == "exits":
        good = est < 0
    return f"supports-{hypothesis}" if good else f"contradicts-{hypothesis}"


def estimate_outcome(case_id: str, o: dict, d: dict, blind: bool) -> dict:
    out = {k: d[k] for k in ("key", "kind", "layer", "checks", "feasible")}
    if not d["feasible"]["ok"]:
        return out
    c = case_obj(case_id, o)
    df = outcome_panel(case_id, o, blind=blind)
    if blind:
        power.assert_blind(df, c)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        est = power.estimate_all(df, c.cohorts, c.start, list(c.classes))
    plac = {layer: [r[layer] for r in d["placebo_estimates"] if r[layer] is not None] for layer in power.LAYERS}
    layers = {layer: batch.summarise(est[layer], plac[layer]) for layer in power.LAYERS}
    reg = layers[o["layer"]]
    own = {}
    for fam, f in d["own_class"].items():
        v = pd.Series([x for x in f["estimates"] if x is not None], dtype=float)
        if len(v) >= 10 and reg["plain"] is not None:
            cen = v - v.mean()
            own[fam] = {
                "draws": int(len(v)),
                "p": num((1 + (cen.abs() >= abs(reg["plain"] - v.mean())).sum()) / (len(v) + 1)),
            }
    checks = {}
    for layer in o.get("checks", []):
        e = layers[layer]["estimate"]
        lo, hi = reg["interval_90"]
        checks[layer] = {
            "estimate": e,
            "inside_registered_90": None if e is None or lo is None else bool(lo <= e <= hi),
            "same_sign": None if e is None or reg["estimate"] is None else bool(np.sign(e) == np.sign(reg["estimate"])),
        }
    ev_treated = event_coefs(df, o, c.cohorts, list(c.classes))
    ev_placebo = [{int(k): v for k, v in e.items() if v is not None} for e in d["event"]["placebo"]]
    event = {}
    for k, v in sorted(ev_treated.items()):
        shock = float(np.mean([e[k] for e in ev_placebo if k in e])) if any(k in e for e in ev_placebo) else 0.0
        b90, b95 = band(ev_placebo, k, 0.90), band(ev_placebo, k, 0.95)
        event[str(k)] = {
            "plain": num(v),
            "net": num(v - shock),
            "band_90": [num(v - shock - b90[1]), num(v - shock - b90[0])] if b90 else None,
            "no_effect_90": [num(b90[0]), num(b90[1])] if b90 else None,
            "inside_95": None if b95 is None else bool(b95[0] <= v - shock <= b95[1]),
        }
    return out | {
        "mean": d["mean"],
        "layers": layers,
        "registered": reg,
        "checks": checks,
        "own_class": own,
        "event": event,
        "pre_inside_95": d["event"]["pre_inside_95"],
    }


def judge(case: dict, outs: dict, q: dict, params: dict) -> tuple[str, str, list[str]]:
    """The registered decision rule and grade for one case."""
    prim = next(o for o in case["outcomes"] if o["role"] == "primary")
    r = outs[prim["key"]]
    reasons = []
    if not r["feasible"]["ok"]:
        return "not-identified", "Not identified", r["feasible"]["reasons"]
    if r.get("pre_inside_95") is False:
        return (
            "not-identified",
            "Not identified",
            ["a pre-reform year of the primary outcome lies outside its 95% placebo band"],
        )
    reg = r["registered"]
    if reg["estimate"] is None:
        return "hidden", "hidden", []
    checks_ok = all(v["same_sign"] is not False for v in r["checks"].values())
    sig = (
        reg["p"] is not None and reg["p"] < params["alpha"] and q.get(f"{case['id']}:{prim['key']}", 1.0) < params["q"]
    )
    verdict = decide(case["hypothesis"], prim["kind"], prim.get("measure", ""), reg["estimate"], sig and checks_ok)
    outside = [k for k, v in r["checks"].items() if v["inside_registered_90"] is False]
    grade = "Moderate"
    if outside:
        grade = "Weak"
        reasons.append(f"check layers outside the registered 90% interval: {', '.join(outside)}")
    else:
        cohorts = cohorts_of(prim)
        states = {s for c in cohorts for s in c.treated}
        eoi = params["effect_of_interest"][prim["kind"]]
        if len(cohorts) >= 2 and len(states) >= 3 and (reg["mde_80"] or 99) <= eoi:
            grade = "Strong"
            reasons.append(f"several cohorts and states; smallest detectable effect within {eoi}")
    cap = case.get("grade_cap")
    order = ["Not identified", "Weak", "Moderate", "Strong"]
    if cap and order.index(grade) > order.index(cap[0]):
        grade = cap[0]
        reasons.append(f"capped before unblinding: {cap[1]}")
    if not reasons:
        reasons.append("design checks passed; registered layer and checks agree")
    return verdict, grade, reasons


def bh(pvals: dict[str, float]) -> dict[str, float]:
    return batch.bh(pvals) if pvals else {}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True, choices=sorted(FOLDERS))
    ap.add_argument("--stage", required=True, choices=["design", "dry-run", "estimate"])
    ap.add_argument("--only", help="one case id (for checking; output not written over the registered files)")
    ap.add_argument("--max-placebos", type=int, help="with --only: fewer placebos, for a quick check")
    args = ap.parse_args()
    spec = load(args.spec)
    params = dict(spec.parameters)
    if args.only and args.max_placebos:
        params["max_placebos"] = args.max_placebos
    folder = HERE / FOLDERS[args.spec]
    folder.mkdir(exist_ok=True)
    if not batch.FIRST_YEAR:
        batch.FIRST_YEAR.update(power.cabee(True).groupby("state")["fy"].min().astype(int).to_dict())
    cases = [c for c in spec.cases if not args.only or c["id"] == args.only]

    if args.stage == "design":
        report = {
            "spec": spec.id,
            "plan": spec.plan,
            "mode": "BLIND: treated cells hidden from first exposure",
            "cases": [],
        }
        for case in cases:
            print(case["id"], flush=True)
            report["cases"].append(
                {
                    "id": case["id"],
                    "outcomes": {
                        o["key"]: design_outcome(case["id"], o, params["max_placebos"]) for o in case["outcomes"]
                    },
                }
            )
        name = "design.json" if not args.only else f"check_design_{args.only}.json"
    else:
        blind = args.stage == "dry-run"
        design = json.loads(
            (folder / ("design.json" if not args.only else f"check_design_{args.only}.json")).read_text("utf-8")
        )
        by_id = {c["id"]: c for c in design["cases"]}
        results = []
        for case in cases:
            d = by_id[case["id"]]
            outs = {o["key"]: estimate_outcome(case["id"], o, d["outcomes"][o["key"]], blind) for o in case["outcomes"]}
            results.append((case, outs))
        pvals = {
            f"{case['id']}:{o['key']}": outs[o["key"]]["registered"]["p"]
            for case, outs in results
            for o in case["outcomes"]
            if o["role"] == "primary" and outs[o["key"]].get("registered", {}).get("p") is not None
        }
        q = bh(pvals)
        report = {
            "spec": spec.id,
            "plan": spec.plan,
            "mode": "DRY RUN: treated cells hidden" if blind else "UNBLINDED: registered run",
            "q_values": {k: num(v) for k, v in q.items()},
            "cases": [],
        }
        for case, outs in results:
            verdict, grade, reasons = judge(case, outs, q, params)
            report["cases"].append(
                {"id": case["id"], "verdict": verdict, "grade": grade, "grade_reasons": reasons, "outcomes": outs}
            )
            prim = next(o for o in case["outcomes"] if o["role"] == "primary")
            reg = outs[prim["key"]].get("registered") or {}
            print(f"{case['id']}: {verdict}, {grade}; {prim['key']} {reg.get('estimate')} p={reg.get('p')}", flush=True)
        name = "estimate_blind.json" if blind else "estimate.json"
        if args.only:
            name = f"check_{args.stage}_{args.only}.json"
    (folder / name).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {folder / name}")


if __name__ == "__main__":
    main()
