"""Robustness and diagnostics for a Phase 5 specification (NOT pre-registered).

For every feasible outcome, the registered estimator is re-run on variants of the registered panel. Each
variant re-estimates its own no-effect distribution from the same placebo groups (or CPI classes), on the
variant's panel with treated cells hidden, exactly as the design stage did; the treated estimate is then judged
against it:

- as registered (a check: must reproduce estimate.json);
- leave one state out, for every treated and comparison state (a cohort left without treated or comparison
  states is skipped);
- window: the first exposed period only (a year, or four quarters for prices), and the last year dropped;
- pre-period: from four years (business counts) or five years (prices) before the first exposure, where shorter;
- business counts only: unweighted cells, and other CABEE vintages (each year from the mean of the releases
  it is not final in).

Diagnostics:
- sensitivity of the saturated event study to violations of parallel trends (Rambachan and Roth relative
  magnitudes; evaluate/honest.py): the breakdown value and the identified set at Mbar = 1;
- synthetic DiD, wherever it is the registered or a check layer: pre-period fit (RMSE of the demeaned gap over
  the treated pre-period spread), the effective number of control cells and the largest weights.

Written after the registered results were seen: it can show a result is fragile, never make it a finding.

    uv run python analyses/phase5/robustness.py --spec phase5-reevaluations [--workers 4]
    uv run python analyses/phase5/robustness.py --spec phase5-reevaluations --only <case id>
    uv run python analyses/phase5/robustness.py --summary      # Markdown summary of both specifications

Writes analyses/phase5/<folder>/robustness.json.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("phase5_run", HERE / "run.py")
run = importlib.util.module_from_spec(_spec)
sys.modules["phase5_run"] = run
_spec.loader.exec_module(run)
power, prices, batch = run.power, run.prices, run.batch

from alicia.evaluate import honest, synth  # noqa: E402
from alicia.runner.spec import load  # noqa: E402

TOLERANCE = 1e-3
GROUPS = ("As registered", "Leave one state out", "Window and pre-period", "Weights and data")


def q2s(t: int) -> str:
    return f"{t // 4}-Q{t % 4 + 1}"


def fyl(year: int) -> str:
    return f"{year - 1}-{str(year)[2:]}"


def with_cohorts(o: dict, fn) -> dict | None:
    """A copy of the outcome with each cohort passed through fn (which returns None to drop it)."""
    o2 = copy.deepcopy(o)
    o2["cohorts"] = [c for c in (fn(dict(c)) for c in o2["cohorts"]) if c]
    if not o2["cohorts"] or any(not c["treated"] or not c["controls"] for c in o2["cohorts"]):
        return None
    return o2


def variants(o: dict) -> list[tuple[str, str, dict, str | None]]:
    """(group, label, outcome definition, data transform)."""
    price = o["kind"] == "price"
    to_t = run.period(o)
    out: list[tuple[str, str, dict, str | None]] = [("As registered", "As registered", o, None)]
    for s in power.states_of(run.cohorts_of(o)):

        def drop(c, s=s):
            treated = [x for x in c["treated"] if x != s]
            return c | {"treated": treated, "controls": [x for x in c["controls"] if x != s]} if treated else None

        o2 = with_cohorts(o, drop)
        if o2:
            out.append(("Leave one state out", f"Without {s}", o2, None))
    span = 3 if price else 0
    back = 4 if price else 1
    fmt = q2s if price else int

    def first_only(c):
        return c | {"last_post": fmt(min(to_t(c["last_post"]), to_t(c["first_post"]) + span))}

    def drop_last(c):
        last = to_t(c["last_post"]) - back
        return c | {"last_post": fmt(last)} if last >= to_t(c["first_post"]) else c

    if any(to_t(c["last_post"]) > to_t(c["first_post"]) + span for c in o["cohorts"]):
        out.append(("Window and pre-period", "First exposed year only", with_cohorts(o, first_only), None))
        dropped = with_cohorts(o, drop_last)
        if dropped and dropped["cohorts"] != with_cohorts(o, first_only)["cohorts"]:
            out.append(("Window and pre-period", "Last year dropped", dropped, None))
    first = min(to_t(c["first_post"]) for c in o["cohorts"])
    later = first - (20 if price else 4)
    if later > to_t(o["start"]):
        out.append(
            (
                "Window and pre-period",
                f"Pre-period from {fmt(later) if price else fyl(later)}",
                o | {"start": fmt(later)},
                None,
            )
        )
    if not price:
        out.append(("Weights and data", "Unweighted cells", o, "unweighted"))
        out.append(("Weights and data", "Other CABEE vintages", o, "vintage"))
    return [v for v in out if v[2] is not None]


@cache
def cabee(vintage: bool) -> pd.DataFrame:
    w = power.cabee(False)
    if not vintage:
        return w
    ov = pd.read_csv(batch.PANEL / "cabee_class_state_fy_overlaps.csv.gz", dtype={"anzsic": str})
    ov = ov[(ov["band"] == "total") & ov["measure"].isin(["start", "entries", "exits"])]
    ov = ov.pivot_table(index=["fy", "state", "anzsic"], columns="measure", values="value", aggfunc="mean")
    ov = ov.reset_index()
    return pd.concat([w[~w["fy"].isin(ov["fy"].unique())], ov], ignore_index=True)


def panel(case_id: str, o: dict, blind: bool, transform: str | None) -> pd.DataFrame:
    c = run.case_obj(case_id, o)
    if o["kind"] == "price":
        df = prices.price_panel(run.price_reform(case_id, o), c, blind=blind)
    else:
        df = power.cell_panel(cabee(transform == "vintage"), c, o["measure"], blind=blind)
    if transform == "unweighted":
        df = df.assign(w=1.0)
    return df


def estimate_variant(case_id: str, o: dict, layer: str, groups: list, transform: str | None) -> dict:
    c = run.case_obj(case_id, o)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        blind = panel(case_id, o, True, transform)
        plac = [power.estimate_all(blind, c.cohorts, c.start, g, (layer,))[layer] for g in groups]
        df = panel(case_id, o, False, transform)
        est = power.estimate_all(df, c.cohorts, c.start, list(c.classes), (layer,))[layer]
    s = batch.summarise(est, plac)
    return {k: s[k] for k in ("estimate", "plain", "placebo_sd", "p", "interval_90", "mde_80", "placebos")}


def sensitivity(event: dict) -> dict | None:
    """Relative-magnitudes breakdown for the average post-reform effect of the saturated event study."""
    ks = sorted(int(k) for k, v in event.items() if v.get("net") is not None)
    pre = [k for k in ks if k <= -2]
    post = [k for k in ks if k >= 0]
    if not pre or not post:
        return None
    beta = np.array([event[str(k)]["net"] for k in pre + post], float)
    b1 = honest.relative_magnitudes(beta, len(pre), 1.0)
    return {
        "pre_periods": len(pre) + 1,
        "post_periods": len(post),
        "average_post": round(float(beta[len(pre) :].mean()), 3),
        "breakdown_rm": round(honest.breakdown(beta, len(pre), "RM"), 3),
        "set_rm1": [round(b1.lower, 3), round(b1.upper, 3)],
    }


def sdid_diagnostics(case_id: str, o: dict) -> list[dict]:
    c = run.case_obj(case_id, o)
    df = power.assign(panel(case_id, o, False, None), c.cohorts, list(c.classes))
    out = []
    for cohort in c.cohorts:
        names: list = []
        m = power._matrix(df, c.cohorts, c.start, cohort, list(c.classes), names)
        if m is None or m[2] < 2:
            continue
        y, mask, t0, _ = m
        fit = synth.sdid(y, mask)
        yc, ytr = y[:-1], y[-1]
        gap = ytr[:t0] - fit.omega @ yc[:, :t0]
        spread = float(np.std(ytr[:t0] - ytr[:t0].mean()))
        top = np.argsort(fit.omega)[::-1][:3]
        out.append(
            {
                "treated": list(cohort.treated),
                "first": q2s(cohort.first_post) if o["kind"] == "price" else fyl(cohort.first_post),
                "controls": int(len(fit.omega)),
                "effective_controls": round(float(1 / np.sum(fit.omega**2)), 1),
                "fit_ratio": round(float(np.std(gap - gap.mean())) / spread, 3) if spread > 0 else None,
                "top_weights": [[str(names[i]), round(float(fit.omega[i]), 3)] for i in top],
                "estimate": round(fit.estimate, 3),
            }
        )
    return out


def outcome_task(args: tuple) -> tuple[str, str, dict]:
    case_id, o, d, registered = args
    t0 = time.time()
    layer = o["layer"]
    groups = d["placebo_groups"]
    rows = []
    for group, label, o2, transform in variants(o):
        res = estimate_variant(case_id, o2, layer, groups, transform)
        rows.append({"group": group, "label": label, **res})
    base = rows[0]
    if base["plain"] is not None and abs(base["plain"] - registered["plain"]) > TOLERANCE:
        raise AssertionError(f"{case_id} {o['key']}: as-registered variant does not reproduce estimate.json")
    sd = None
    if "sdid" in (layer, *o.get("checks", [])):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sd = sdid_diagnostics(case_id, o)
    print(f"  {case_id} {o['key']}: {len(rows)} variants in {time.time() - t0:.0f}s", flush=True)
    return case_id, o["key"], {"layer": layer, "variants": rows, "sdid": sd}


def fmt(v, nd: int = 2) -> str:
    return "n/a" if v is None else f"{v:+.{nd}f}".replace("-", "−")


def fp(p) -> str:
    return "n/a" if p is None else ("< 0.01" if p < 0.01 else f"{p:.3f}" if p < 0.1 else f"{p:.2f}")


def summary() -> str:
    """Markdown for docs/robustness_phase5.md: primary outcomes across variants, programme-wide q-values, and
    the synthetic DiD diagnostics."""
    rows, pvals, labels, sd_rows = [], {}, {}, []
    for spec_id, folder in run.FOLDERS.items():
        spec = load(spec_id)
        est = {c["id"]: c for c in json.loads((HERE / folder / "estimate.json").read_text("utf-8"))["cases"]}
        rob = {c["id"]: c for c in json.loads((HERE / folder / "robustness.json").read_text("utf-8"))["cases"]}
        for case in spec.cases:
            for o in case["outcomes"]:
                r = est[case["id"]]["outcomes"][o["key"]]
                if not r["feasible"]["ok"]:
                    continue
                key = f"{case['id']}:{o['key']}"
                pvals[key] = r["registered"]["p"]
                labels[key] = (case["title"].split(":")[0], o["key"], o["role"], r.get("pre_inside_95"))
                rb = rob[case["id"]]["outcomes"][o["key"]]
                v = [x for x in rb["variants"][1:] if x["estimate"] is not None]
                reg = r["registered"]
                same = sum(np.sign(x["estimate"]) == np.sign(reg["estimate"]) for x in v)
                sig = sum(x["p"] is not None and x["p"] < 0.05 for x in v)
                worst = max(v, key=lambda x: abs(x["estimate"] - reg["estimate"]), default=None)
                sens = rb.get("sensitivity") or {}
                if o["role"] == "primary":
                    rows.append(
                        f"| {labels[key][0]} | {o['key']} | {fmt(reg['estimate'])} | {fp(reg['p'])} | "
                        f"{same} of {len(v)} | {sig} of {len(v)} | "
                        f"{fmt(min(x['estimate'] for x in v))} to {fmt(max(x['estimate'] for x in v))} | "
                        f"{worst['label'] if worst else 'n/a'} | {sens.get('breakdown_rm', 'n/a')} |"
                    )
                for d in rb.get("sdid") or []:
                    sd_rows.append(
                        f"| {labels[key][0]} | {o['key']} | {'/'.join(d['treated'])} {d['first']} | {d['controls']} | "
                        f"{d['effective_controls']} | {d['fit_ratio']} | "
                        + ", ".join(f"{n} ({w})" for n, w in d["top_weights"])
                        + f" | {fmt(d['estimate'])} |"
                    )
    q_all = batch.bh({k: v for k, v in pvals.items() if v is not None})
    prim = {k: v for k, v in pvals.items() if v is not None and labels[k][2] == "primary"}
    q_prim = batch.bh(prim)
    out = [
        "| Evaluation | Primary outcome | Registered estimate | p | Variants with the same sign | Variants with "
        "p < 0.05 | Range | Variant furthest from the registered estimate | Pre-trend breakdown M̄ |",
        "|---|---|---|---|---|---|---|---|---|",
        *rows,
        "",
        "**Programme-wide q-values** (Benjamini-Hochberg across all Phase 5 outcomes, and across primary outcomes "
        "only). Outcomes with p < 0.10:",
        "",
        "| Evaluation | Outcome | Role | Pre-trend check | p | q (all 25) | q (10 primaries) |",
        "|---|---|---|---|---|---|---|",
    ]
    for k in sorted(pvals, key=lambda k: pvals[k] if pvals[k] is not None else 1):
        if pvals[k] is None or pvals[k] >= 0.10:
            continue
        name, key, role, pre = labels[k]
        out.append(
            f"| {name} | {key} | {role} | {'fail' if pre is False else 'pass'} | {fp(pvals[k])} | {fp(q_all[k])} | "
            f"{fp(q_prim.get(k)) if k in q_prim else '—'} |"
        )
    out += [
        "",
        "**Synthetic DiD diagnostics** (wherever it is the registered or a check layer; estimates are plain, before "
        "the placebo mean is netted out):",
        "",
        "| Evaluation | Outcome | Cohort | Control cells | Effective controls | Pre-fit ratio | Largest weights | "
        "Estimate |",
        "|---|---|---|---|---|---|---|---|",
        *sd_rows,
    ]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--summary", action="store_true", help="print the Markdown summary of both specifications")
    ap.add_argument("--spec", choices=sorted(run.FOLDERS))
    ap.add_argument("--only", help="one case id (output written to robustness_<id>.json)")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    if args.summary:
        print(summary())
        return
    if not args.spec:
        ap.error("--spec is required")
    spec = load(args.spec)
    folder = HERE / run.FOLDERS[args.spec]
    design = {c["id"]: c for c in json.loads((folder / "design.json").read_text("utf-8"))["cases"]}
    est = {c["id"]: c for c in json.loads((folder / "estimate.json").read_text("utf-8"))["cases"]}
    if not batch.FIRST_YEAR:
        batch.FIRST_YEAR.update(power.cabee(True).groupby("state")["fy"].min().astype(int).to_dict())
    cabee(False), cabee(True), prices.relative_prices()  # load before the workers fork
    tasks = [
        (case["id"], o, design[case["id"]]["outcomes"][o["key"]], est[case["id"]]["outcomes"][o["key"]]["registered"])
        for case in spec.cases
        if not args.only or case["id"] == args.only
        for o in case["outcomes"]
        if est[case["id"]]["outcomes"][o["key"]]["feasible"]["ok"]
    ]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        done = list(pool.map(outcome_task, tasks))
    cases = []
    for case in spec.cases:
        outs = {k: v for cid, k, v in done if cid == case["id"]}
        if not outs:
            continue
        for k, v in outs.items():
            v["sensitivity"] = sensitivity(est[case["id"]]["outcomes"][k].get("event") or {})
            v["own_class"] = est[case["id"]]["outcomes"][k].get("own_class") or {}
        cases.append({"id": case["id"], "outcomes": outs})
    out = {
        "spec": args.spec,
        "preregistered": False,
        "note": "Written after the registered results were seen; robustness only, never a finding.",
        "cases": cases,
    }
    name = f"robustness_{args.only}.json" if args.only else "robustness.json"
    (folder / name).write_text(json.dumps(out, indent=1, ensure_ascii=False, allow_nan=False) + "\n", "utf-8")
    print(f"wrote {folder / name}")


if __name__ == "__main__":
    main()
