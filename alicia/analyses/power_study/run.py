"""Forward plan Phase 3: blinded power study. How much does each layer of the regression framework shrink
the no-effect spread for each evaluable reform?

Outcome: business entry and exit rates (per 100 businesses operating at the start of the financial year),
ANZSIC class x state x financial year, from CABEE. Unit of analysis: a cell (class x state).

Blinding: before anything is computed, every row for a reform's treated classes in its treated states from
the first exposed year on is deleted (``hide``; checked by ``assert_blind``). No estimate of any reform's
effect is made here.

No-effect distribution: placebo industries. For each reform, the same size-matched placebo class groups as
the high-evaluability batch (``analyses/high_evaluability/run.py: placebo_groups``; up to 40), each
assigned the reform's treated states and dates. Every layer is run on the same placebo assignments, so
differences in spread are differences between estimators. Smallest detectable effect (80% power, 5%
two-sided) = 2.8 x the standard deviation of placebo estimates.

Layers (estimates in percentage points of the entry or exit rate):
- ``twoway``: cell and year fixed effects (no macro controls), weighted by businesses;
- ``state_year``: cell and state x year effects (state macro conditions absorbed);
- ``saturated``: cell, class x year and state x year effects (plus national industry cycles);
- ``controls``: cell and year effects plus measured state controls (final demand growth, unemployment,
  population growth, mining share x commodity prices), the fallback where effects cannot be saturated;
- ``imputation``: saturated effects fitted on untreated cells (Borusyak, Jaravel and Spiess), weighted;
- ``sdid``: synthetic DiD on the treated group's rate against all untreated cells, per cohort;
- ``gsynth``: generalised synthetic control on the same matrix, factors chosen by cross-validation.

The registered batch design's spread (stacked DiD net of placebo industries, design stage) is reported
alongside from ``analyses/high_evaluability/design.json``.

    uv run python analyses/power_study/run.py            # all reforms (about 20 minutes)
    uv run python analyses/power_study/run.py --only amr-2021-2022 --max-placebos 10
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BATCH = HERE.parent / "high_evaluability"
sys.path.insert(0, str(BATCH))

import cases as batch_cases  # noqa: E402
import run as batch  # noqa: E402

from alicia.evaluate import covariates, panel, synth  # noqa: E402
from alicia.evaluate.stacked import Cohort  # noqa: E402

MDE_FACTOR = 2.801585
MAX_PLACEBOS = 40
MIN_CELL = 20  # businesses at the start of the base year, for control cells in the synthetic methods
MIN_CLASS_NATIONAL = 100  # businesses in the base year, Australia, for a class to enter the panel
COVARIATES = ("sfd_growth", "unemployment_rate", "population_growth", "commodity_exposure")
LAYERS = ("twoway", "state_year", "saturated", "controls", "imputation", "sdid", "gsynth")
ALL_BUT = batch_cases.ALL_BUT


@dataclass(frozen=True)
class Reform:
    case: batch_cases.Case
    registered: bool  # in the batch: use its registered CABEE vintage and report its design-stage spread
    notes: tuple[str, ...] = ()


def _case(**kw) -> batch_cases.Case:
    base = dict(records=(), family=None, hypothesis="enhancing", division="", design="", price=None)
    return batch_cases.Case(**(base | kw))


REFORMS: tuple[Reform, ...] = tuple(Reform(c, True) for c in batch_cases.CASES) + (
    Reform(
        _case(
            id="wa-trading-hours-weeknight-2010",
            title="Perth weeknight trading (November 2010)",
            records=("wa-trading-hours-weeknight-2010",),
            family="retail-trading-hours",
            classes=("4110", "4251", "4260"),
            cohorts=(Cohort(("WA",), 2011, 2012, ("NSW", "VIC", "QLD", "ACT")),),
            division="G",
            design="WA general retail against the same classes in NSW, Victoria, Queensland and the ACT, "
            "2010-11 and 2011-12 (Sunday trading followed in August 2012).",
            start=2008,
        ),
        False,
        ("Business counts by state are a different outcome from the registered re-evaluation (Perth vs regional WA).",),
    ),
    Reform(
        _case(
            id="amr-2021-2022",
            title="Automatic mutual recognition of occupational registrations (2021-22)",
            records=tuple(f"{s}-amr-2021" for s in ("act", "nsw", "nt", "sa", "tas", "vic")) + ("wa-amr-2022",),
            family="amr-occupational-licensing",
            classes=("3231", "3232", "3233", "6720", "3011"),
            cohorts=(
                Cohort(("ACT", "NSW", "NT", "VIC", "TAS", "SA"), 2022, 2025, ("QLD",)),
                Cohort(("WA",), 2023, 2025, ("QLD",)),
            ),
            division="E",
            design="Staggered: six jurisdictions from 2021-22, WA from 2022-23; Queensland never adopted.",
            start=2017,
        ),
        False,
        (
            "Uses CABEE releases after the registered vintage (to June 2025); 2019-20 to 2021-22 are COVID years.",
            "One never-treated state (Queensland), so comparisons within the treated classes rest on it.",
        ),
    ),
)


# ---- data --------------------------------------------------------------------------------------------


@cache
def cabee(registered: bool) -> pd.DataFrame:
    if registered:
        return batch.cabee()
    p = pd.read_csv(batch.PANEL / "cabee_class_state_fy.csv.gz", dtype={"anzsic": str})
    p = p[p["measure"].isin(["start", "entries", "exits"]) & (p["band"] == "total")]
    return p.pivot_table(index=["fy", "state", "anzsic"], columns="measure", values="value").reset_index()


@cache
def fy_covariates(base_first_year: int) -> pd.DataFrame:
    """State x financial-year means of the quarterly controls (fy named by the year it ends)."""
    q = covariates.state_covariates(base_fy=base_first_year)
    q = q.assign(fy=q["period"].dt.year + (q["period"].dt.month >= 7))
    return q.groupby(["state", "fy"])[list(COVARIATES)].mean().reset_index()


def states_of(cohorts) -> list[str]:
    return sorted({s for c in cohorts for s in c.units})


def hide(df: pd.DataFrame, case) -> pd.DataFrame:
    """Delete the reform's treated cells from first exposure on (and treated states after their window)."""
    drop = pd.Series(False, index=df.index)
    for c in case.cohorts:
        in_tr = df["state"].isin(c.treated)
        drop |= in_tr & df["cls"].isin(case.classes) & (df["fy"] >= c.first_post)
        drop |= in_tr & (df["fy"] > c.last_post)
    return df[~drop]


def assert_blind(df: pd.DataFrame, case) -> None:
    for c in case.cohorts:
        bad = df["state"].isin(c.treated) & df["cls"].isin(case.classes) & (df["fy"] >= c.first_post)
        if bad.any():
            raise AssertionError(f"{case.id}: treated outcomes visible after first exposure")


def cell_panel(w: pd.DataFrame, case, measure: str) -> pd.DataFrame:
    base_fy = min(c.first_post for c in case.cohorts) - 1
    last = max(c.last_post for c in case.cohorts)
    d = w[(w["fy"] >= case.start) & (w["fy"] <= last) & w["state"].isin(states_of(case.cohorts))]
    d = d[(d["anzsic"].str.len() == 4) & (d["anzsic"] != "9999") & (d["start"] > 0)]
    national = d[d["fy"] == base_fy].groupby("anzsic")["start"].sum()
    keep = set(national[national >= MIN_CLASS_NATIONAL].index) | set(case.classes)
    d = d[d["anzsic"].isin(keep)]
    out = pd.DataFrame(
        {
            "cls": d["anzsic"].to_numpy(),
            "state": d["state"].to_numpy(),
            "fy": d["fy"].astype(int).to_numpy(),
            "y": 100 * d[measure].fillna(0).to_numpy(float) / d["start"].to_numpy(float),
            "w": d["start"].to_numpy(float),
        }
    )
    out["cell"] = out["cls"] + ":" + out["state"]
    base = out[out["fy"] == base_fy].set_index("cell")["w"]
    out["base"] = out["cell"].map(base).fillna(0.0)
    cov = fy_covariates(base_fy - 1)
    out = out.merge(cov, on=["state", "fy"], how="left")
    return hide(out, case).reset_index(drop=True)


# ---- estimators on one placebo assignment ----------------------------------------------------------------


def assign(df: pd.DataFrame, cohorts, classes) -> pd.DataFrame:
    d = np.zeros(len(df))
    for c in cohorts:
        on = df["state"].isin(c.treated) & df["cls"].isin(classes) & df["fy"].between(c.first_post, c.last_post)
        d[on.to_numpy()] = 1.0
    return df.assign(D=d)


def _matrix(df: pd.DataFrame, case, cohort: Cohort, classes) -> tuple[np.ndarray, np.ndarray, int, np.ndarray] | None:
    """Cells complete over the cohort's window: controls (untreated) then the treated group's average row."""
    years = list(range(case.start, cohort.last_post + 1))
    sub = df[df["state"].isin(cohort.units) & df["fy"].between(years[0], years[-1])]
    other_treated = {s for c in case.cohorts if c is not cohort for s in c.treated}
    sub = sub[~(sub["cls"].isin(classes) & sub["state"].isin(other_treated))]
    wide = sub.pivot(index="cell", columns="fy", values="y").reindex(columns=years)
    wide = wide.dropna()
    meta = sub.drop_duplicates("cell").set_index("cell").loc[wide.index]
    is_tr = meta["cls"].isin(classes) & meta["state"].isin(cohort.treated)
    ctrl = wide[~is_tr & (meta["base"] >= MIN_CELL)]
    tr = wide[is_tr]
    if tr.empty or len(ctrl) < 5:
        return None
    wts = meta.loc[is_tr, "base"].to_numpy(float)
    wts = wts if wts.sum() > 0 else np.ones(len(wts))
    row = np.average(tr.to_numpy(), axis=0, weights=wts)
    y = np.vstack([ctrl.to_numpy(), row])
    t0 = years.index(cohort.first_post)
    mask = np.zeros_like(y, bool)
    mask[-1, t0:] = True
    return y, mask, t0, wts


def synthetic(df: pd.DataFrame, case, classes, method: str) -> float:
    ests, weights = [], []
    for c in case.cohorts:
        m = _matrix(df, case, c, classes)
        if m is None:
            continue
        y, mask, t0, wts = m
        if t0 < 2:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            est = synth.sdid(y, mask).estimate if method == "sdid" else synth.gsynth(y, mask, rmax=3).att
        ests.append(est)
        weights.append(wts.sum() * (c.last_post - c.first_post + 1))
    return float(np.average(ests, weights=weights)) if ests else float("nan")


def estimate_all(df: pd.DataFrame, case, classes, layers=LAYERS) -> dict[str, float]:
    d = assign(df, case.cohorts, classes)
    out: dict[str, float] = {}
    sat = ["cell", ("cls", "fy"), ("state", "fy")]
    for layer in layers:
        try:
            if layer == "twoway":
                out[layer] = panel.feols(d, "y", ["D"], fe=["cell", "fy"], weights="w").coef["D"]
            elif layer == "state_year":
                out[layer] = panel.feols(d, "y", ["D"], fe=["cell", ("state", "fy")], weights="w").coef["D"]
            elif layer == "saturated":
                out[layer] = panel.feols(d, "y", ["D"], fe=sat, weights="w").coef["D"]
            elif layer == "controls":
                dc = d.dropna(subset=list(COVARIATES))
                out[layer] = panel.feols(dc, "y", ["D", *COVARIATES], fe=["cell", "fy"], weights="w").coef["D"]
            elif layer == "imputation":
                imp = panel.imputation(d, "y", "D", fe=sat, weights="w", first_stage_weights=True, tol=1e-9)
                out[layer] = imp.att
            else:
                out[layer] = synthetic(d, case, classes, layer)
        except (np.linalg.LinAlgError, ValueError, RuntimeError) as e:
            print(f"    {layer}: {type(e).__name__}: {e}", flush=True)
            out[layer] = float("nan")
    return {k: float(v) for k, v in out.items()}


# ---- study -------------------------------------------------------------------------------------------------


def registered_spread(case_id: str) -> dict[str, dict | None]:
    design = json.loads((BATCH / "design.json").read_text("utf-8"))
    row = next((c for c in design["cases"] if c["id"] == case_id), None)
    out: dict[str, dict | None] = {}
    for m in ("entries", "exits"):
        main = (row or {}).get(m) and row[m]["main"]
        out[m] = {"sd": main["placebo_sd"], "mde": main["mde_80"], "n": main["placebos"]} if main else None
    return out


def summarise(values: list[float]) -> dict:
    v = np.array([x for x in values if np.isfinite(x)])
    if len(v) < 3:
        return {"n": int(len(v)), "sd": None, "mde": None, "mean": None, "rms": None}
    sd = float(v.std(ddof=1))
    return {
        "n": int(len(v)),
        "sd": round(sd, 3),
        "mde": round(MDE_FACTOR * sd, 3),
        "mean": round(float(v.mean()), 3),
        "rms": round(float(np.sqrt((v**2).mean())), 3),
    }


def run_reform(r: Reform, max_placebos: int) -> dict:
    case = r.case
    w = cabee(r.registered)
    if not batch.FIRST_YEAR:
        batch.FIRST_YEAR.update(cabee(True).groupby("state")["fy"].min().astype(int).to_dict())
    pg = batch.placebo_groups(w, case)
    reasons = []
    if pg["treated_size"] < batch.MIN_TREATED:
        reasons.append(
            f"treated group has {pg['treated_size']:.0f} businesses in the base year (rule: {batch.MIN_TREATED})"
        )
    if len(pg["groups"]) < batch.MIN_PLACEBOS:
        reasons.append(f"only {len(pg['groups'])} placebo groups (rule: {batch.MIN_PLACEBOS})")
    out = {
        "id": case.id,
        "title": case.title,
        "classes": list(case.classes),
        "cohorts": [c.__dict__ for c in case.cohorts],
        "start": case.start,
        "registered_vintage": r.registered,
        "notes": list(r.notes),
        "placebo_groups": min(len(pg["groups"]), max_placebos),
        "treated_size": pg["treated_size"],
        "feasible": {"ok": not reasons, "reasons": reasons},
        "registered_design": registered_spread(case.id) if r.registered else None,
        "outcomes": {},
    }
    if reasons:
        return out
    groups = pg["groups"][:max_placebos]
    for measure in ("entries", "exits"):
        df = cell_panel(w, case, measure)
        assert_blind(df, case)
        t = time.time()
        rows = []
        for g in groups:
            rows.append(estimate_all(df, case, g))
        res = {layer: summarise([row[layer] for row in rows]) for layer in LAYERS}
        base = res["twoway"]["sd"]
        for layer in LAYERS:
            sd = res[layer]["sd"]
            res[layer]["ratio_to_twoway"] = round(sd / base, 3) if sd is not None and base else None
        out["outcomes"][measure] = {
            "cells": int(df["cell"].nunique()),
            "rows": int(len(df)),
            "mean_rate": round(float(np.average(df["y"], weights=df["w"])), 2),
            "layers": res,
            "placebo_estimates": [
                {k: round(v, 4) for k, v in row.items()} | {"classes": g} for row, g in zip(rows, groups, strict=True)
            ],
        }
        print(
            f"  {measure}: {len(groups)} placebos in {time.time() - t:.0f}s; "
            + ", ".join(f"{k} {res[k]['mde']}" for k in LAYERS),
            flush=True,
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="one reform id")
    ap.add_argument("--max-placebos", type=int, default=MAX_PLACEBOS)
    args = ap.parse_args()
    results = []
    for r in REFORMS:
        if args.only and r.case.id != args.only:
            continue
        print(r.case.id, flush=True)
        results.append(run_reform(r, args.max_placebos))
    report = {
        "plan": "docs/forward_plan_macro_controls.md (Phase 3)",
        "mode": "BLIND: treated cells hidden from first exposure; placebo industries only",
        "units": "percentage points of the entry or exit rate (per 100 businesses at the start of the year)",
        "mde": "2.8 x standard deviation of placebo estimates (80% power, 5% two-sided)",
        "layers": list(LAYERS),
        "reforms": results,
    }
    name = "power.json" if not args.only else f"check_{args.only}.json"
    (HERE / name).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {HERE / name}")


if __name__ == "__main__":
    main()
