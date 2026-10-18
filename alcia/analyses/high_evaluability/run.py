"""High-evaluability batch: design stage (--blind) and the registered estimation.

Implements docs/pap_high_evaluability.md for every case in cases.py:
- entry and exit rates, stacked difference-in-differences net of placebo industry groups;
- year-by-year (event-study) estimates, robustness variants, decision rule and grade;
- productivity and real pay per worker (descriptive), against placebo divisions;
- prices where a CPI class matches, against placebo CPI classes.

    uv run python analyses/high_evaluability/run.py --blind   # design stage: treated outcomes hidden
    uv run python analyses/high_evaluability/run.py           # the registered analysis (unblinded)

Writes design.json or estimate.json next to this file.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from cases import CASES, Case, PriceSpec

from alcia import anzsic
from alcia.evaluate.did import Placebo
from alcia.evaluate.stacked import Cohort, blind_cohorts, stacked, stacked_event
from alcia.outcomes import productivity
from alcia.outcomes.abs_series import CITY_STATE, fetch_cpi
from alcia.outcomes.cabee import as_registered
from alcia.pipeline.store import PROCESSED

HERE = Path(__file__).resolve().parent
PANEL = PROCESSED / "abs_cabee"
CPI_CLASSES = json.loads((HERE.parents[1] / "src" / "alcia" / "data" / "cpi17_classes.json").read_text())["classes"]
SEED = 20261015
DRAWS = 1000
MIN_TREATED = 100  # businesses in the treated group in the base year
MIN_CLASS = 50  # businesses in a placebo class (treated states, base year)
MIN_PLACEBOS = 19  # so that p can reach 0.05
SIZE_BANDS = ((0.5, 2.0), (0.25, 4.0), (0.1, 10.0))
EFFECT_OF_INTEREST = 5.0
PROD_START = 2001
DIVISIONS = "ABCDEFGHIJKLMNOPQRS"
BLIND = False


# --- helpers -------------------------------------------------------------------------------------


def num(x, nd: int = 3):
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) else round(x, nd)


def series(s: pd.Series, nd: int = 3) -> dict:
    return {str(k): num(v, nd) for k, v in s.items()}


def hide(df: pd.DataFrame, cohorts) -> pd.DataFrame:
    return blind_cohorts(df, cohorts) if BLIND else df


def treated_states(cohorts) -> list[str]:
    return sorted({s for c in cohorts for s in c.treated})


def control_states(cohorts) -> list[str]:
    return sorted({s for c in cohorts for s in c.controls})


def summarise(est: float, placebos: list[float]) -> dict:
    """Net estimate, centred placebo rank p-value, 90% and 95% intervals, smallest detectable effect."""
    plac = pd.Series([p for p in placebos if not math.isnan(p)], dtype=float)
    if len(plac) < 2:
        empty = ("placebo_mean", "placebo_sd", "mde_80", "p")
        return (
            {"estimate": None, "plain": num(est), "placebos": int(len(plac))}
            | dict.fromkeys(empty)
            | {
                "interval_90": [None, None],
                "interval_95": [None, None],
            }
        )
    shock = float(plac.mean())
    centred = Placebo(plac - shock)
    net = est - shock
    ok = not math.isnan(net)
    lo90, hi90 = centred.interval(net, 0.90) if ok else (float("nan"),) * 2
    lo95, hi95 = centred.interval(net, 0.95) if ok else (float("nan"),) * 2
    return {
        "estimate": num(net),
        "plain": num(est),
        "placebo_mean": num(shock),
        "placebos": int(len(plac)),
        "placebo_sd": num(centred.sd),
        "mde_80": num(centred.mde),
        "p": num(centred.p_value(net), 4) if ok else None,
        "interval_90": [num(lo90), num(hi90)],
        "interval_95": [num(lo95), num(hi95)],
    }


# --- business counts -----------------------------------------------------------------------------


def cabee(path: str = "cabee_class_state_fy.csv.gz", employing: bool = False) -> pd.DataFrame:
    p = as_registered(pd.read_csv(PANEL / path, dtype={"anzsic": str}))
    p = p[p["measure"].isin(["start", "entries", "exits"])]
    keys = ["fy", "state", "anzsic"]
    tot = p[p["band"] == "total"].pivot_table(index=keys, columns="measure", values="value")
    if employing:
        non = p[p["band"] == "nonemp"].pivot_table(index=keys, columns="measure", values="value")
        tot = tot.sub(non.reindex(tot.index).fillna(0))
    return tot.reset_index()


def overlap_vintage(w: pd.DataFrame) -> pd.DataFrame:
    ov = as_registered(pd.read_csv(PANEL / "cabee_class_state_fy_overlaps.csv.gz", dtype={"anzsic": str}))
    ov = ov[(ov["band"] == "total") & ov["measure"].isin(["start", "entries", "exits"])]
    ov = ov.pivot_table(index=["fy", "state", "anzsic"], columns="measure", values="value").reset_index()
    return pd.concat([w[~w["fy"].isin(ov["fy"].unique())], ov], ignore_index=True)


class Rates:
    """Group entry or exit rates (per 100 businesses at the start of the year), by state and year.

    Counts are held as class x state x year arrays so that thousands of placebo groups are cheap."""

    def __init__(self, w: pd.DataFrame):
        self.classes = {c: i for i, c in enumerate(sorted(w["anzsic"].unique()))}
        self.states = sorted(w["state"].unique())
        self.years = sorted(int(y) for y in w["fy"].unique())
        shape = (len(self.classes), len(self.states), len(self.years))
        si = {s: i for i, s in enumerate(self.states)}
        yi = {y: i for i, y in enumerate(self.years)}
        ci = w["anzsic"].map(self.classes).to_numpy()
        sj = w["state"].map(si).to_numpy()
        yk = w["fy"].astype(int).map(yi).to_numpy()
        self.present = np.zeros(shape, bool)
        self.present[ci, sj, yk] = True
        self.arr = {}
        for m in ("start", "entries", "exits"):
            a = np.zeros(shape)
            a[ci, sj, yk] = w[m].fillna(0).to_numpy(float)
            self.arr[m] = a
        grid = np.array([(s, y) for s in self.states for y in self.years], dtype=object)
        self.unit, self.time = grid[:, 0], grid[:, 1].astype(int)

    def panel(self, classes, measure: str) -> pd.DataFrame:
        idx = [self.classes[c] for c in classes if c in self.classes]
        start = self.arr["start"][idx].sum(0).ravel()
        m = self.arr[measure][idx].sum(0).ravel()
        ok = self.present[idx].any(0).ravel() & (start > 0)
        return pd.DataFrame({"unit": self.unit[ok], "time": self.time[ok], "y": 100 * m[ok] / start[ok]})


FIRST_YEAR: dict[str, int] = {}  # first financial year each state appears in CABEE (NT: 2009-10)


def complete(g: pd.DataFrame, cohorts, start) -> bool:
    """Every treated state has every year of its cohort's window (from its first year in CABEE)."""
    for c in cohorts:
        for s in c.treated:
            need = set(range(max(start, FIRST_YEAR.get(s, start)), c.last_post + 1))
            if not need <= set(g.loc[g["unit"] == s, "time"]):
                return False
    return True


def placebo_groups(w: pd.DataFrame, case: Case) -> dict:
    """Classes outside the treated divisions, size-matched to the treated group in the treated states."""
    base_fy = min(c.first_post for c in case.cohorts) - 1
    states = treated_states(case.cohorts)
    base = w[(w["fy"] == base_fy) & w["state"].isin(states)].groupby("anzsic")["start"].sum()
    t_size = float(base.reindex(list(case.classes)).fillna(0).sum())
    divs = {anzsic.division(c) for c in case.classes}
    eligible = sorted(
        c
        for c in base.index
        if len(c) == 4
        and c != "9999"
        and anzsic.division(c) not in divs
        and c not in case.classes
        and base[c] >= MIN_CLASS
    )
    k = len(case.classes)
    groups, band = [], None
    for lo, hi in SIZE_BANDS:
        if k == 1:
            groups = [[c] for c in eligible if lo * t_size <= base[c] <= hi * t_size]
        else:
            rng = np.random.default_rng(SEED)
            groups = []
            for _ in range(DRAWS):
                pick = sorted(rng.choice(eligible, size=k, replace=False))
                if lo * t_size <= float(base[pick].sum()) <= hi * t_size:
                    groups.append(pick)
        band = (lo, hi)
        if len(groups) >= MIN_PLACEBOS:
            break
    return {"base_fy": base_fy, "treated_size": t_size, "eligible": len(eligible), "band": band, "groups": groups}


def entry_estimate(rates: Rates, case: Case, measure: str, groups, cohorts=None, classes=None) -> dict:
    cohorts = cohorts or case.cohorts
    t = hide(rates.panel(classes or case.classes, measure), cohorts)
    est = stacked(t, cohorts, case.start)
    plac = []
    for g in groups:
        gp = rates.panel(g, measure)
        if complete(gp, cohorts, case.start):
            plac.append(stacked(gp, cohorts, case.start))
    return summarise(est, plac)


def event_paths(rates: Rates, case: Case, measure: str, groups) -> dict:
    t = hide(rates.panel(case.classes, measure), case.cohorts)
    raw = stacked_event(t, case.cohorts, case.start)
    plac = []
    for g in groups:
        gp = rates.panel(g, measure)
        if complete(gp, case.cohorts, case.start):
            plac.append(stacked_event(gp, case.cohorts, case.start))
    P = pd.DataFrame(plac)
    shock = P.mean()
    centred = P - shock
    net = raw.reindex(shock.index) - shock
    pre = [k for k in shock.index if k < -1]
    inside = None
    if pre and not net[pre].isna().any():
        inside = bool(all(centred[k].quantile(0.025) <= net[k] <= centred[k].quantile(0.975) for k in pre))
    band = lambda lo, hi: {  # noqa: E731
        str(k): [num(net[k] - centred[k].quantile(hi)), num(net[k] - centred[k].quantile(lo))] for k in net.index
    }
    return {
        "net": series(net),
        "band_90": band(0.05, 0.95),
        "band_95": band(0.025, 0.975),
        "pre_inside_95": inside,
        "pre_years": len(pre) + 1,
    }


def variants(case: Case) -> dict[str, dict]:
    """Robustness variants (plan section 6): name -> overrides."""
    out: dict[str, dict] = {"vintage_overlap": {"w": "overlap"}, "employing_only": {"w": "employing"}}
    for s in control_states(case.cohorts):
        cohorts = tuple(
            Cohort(c.treated, c.first_post, c.last_post, tuple(x for x in c.controls if x != s)) for c in case.cohorts
        )
        cohorts = tuple(c for c in cohorts if c.controls)
        if cohorts:
            out[f"leave_out_control_{s}"] = {"cohorts": cohorts}
    tr = treated_states(case.cohorts)
    if len(tr) > 1:
        for s in tr:
            cohorts = tuple(
                Cohort(tuple(x for x in c.treated if x != s), c.first_post, c.last_post, c.controls)
                for c in case.cohorts
            )
            out[f"leave_out_treated_{s}"] = {"cohorts": tuple(c for c in cohorts if c.treated)}
    if case.extend_to_2019:
        out["add_2018_19"] = {"cohorts": tuple(Cohort(c.treated, c.first_post, 2019, c.controls) for c in case.cohorts)}
    return out


# --- productivity and pay --------------------------------------------------------------------------


def productivity_result(prod: pd.DataFrame, case: Case) -> dict:
    out = {}
    last = max(c.last_post for c in case.cohorts)
    for var, label in (("gva_per_worker", "Output per worker"), ("real_coe_per_worker", "Real pay per worker")):
        est, plac = float("nan"), []
        for d in DIVISIONS:
            g = prod[(prod["division"] == d) & prod["fy"].between(PROD_START, last)].dropna(subset=[var])
            g = g.rename(columns={"state": "unit", "fy": "time"})
            g = g.assign(y=100 * np.log(g[var]))[["unit", "time", "y"]]
            if g.empty:
                continue
            if d == case.division:
                est = stacked(hide(g, case.cohorts), case.cohorts, PROD_START)
            else:
                plac.append(stacked(g, case.cohorts, PROD_START))
        out[var] = {"label": label, "division": case.division, **summarise(est, plac)}
    return out


def productivity_panel(cpi_q: pd.DataFrame) -> pd.DataFrame:
    allg = cpi_q[cpi_q["index_code"] == "10001"].copy()
    allg["fy"] = allg["q"] // 4 + (allg["q"] % 4 >= 2)
    cpi = allg.groupby(["fy", "state"])["value"].agg(["mean", "count"]).reset_index()
    cpi = cpi[cpi["count"] == 4].rename(columns={"mean": "cpi"})[["fy", "state", "cpi"]]
    return productivity.panel(cpi)


# --- prices ----------------------------------------------------------------------------------------


def cpi_quarterly() -> pd.DataFrame:
    codes = ["10001", *[c["code"] for c in CPI_CLASSES]]
    raw = fetch_cpi(codes, start="2001-Q1", end="2019-Q4")
    raw["state"] = raw["city"].map(CITY_STATE)
    raw["q"] = raw["period"].str[:4].astype(int) * 4 + raw["period"].str[-1].astype(int) - 1
    return raw


def relative_prices(raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    allg = raw[raw["index_code"] == "10001"].set_index(["state", "q"])["value"]
    out = {}
    for code, g in raw[raw["index_code"] != "10001"].groupby("index_code"):
        rel = (100 * np.log(g.set_index(["state", "q"])["value"] / allg)).dropna().reset_index()
        rel.columns = ["unit", "time", "y"]
        out[code] = rel
    return out


def detrend(df: pd.DataFrame, before: int) -> pd.DataFrame:
    """Remove each unit's linear trend fitted on periods before `before`."""
    parts = []
    for _, g in df.groupby("unit"):
        pre = g[(g["time"] < before) & g["y"].notna()]
        if len(pre) < 8:
            continue
        slope, icept = np.polyfit(pre["time"].to_numpy(float), pre["y"].to_numpy(float), 1)
        parts.append(g.assign(y=g["y"] - (icept + slope * g["time"])))
    return pd.concat(parts, ignore_index=True) if parts else df.iloc[0:0]


def to_fy(df: pd.DataFrame) -> pd.DataFrame:
    d = df.assign(fy=df["time"] // 4 + (df["time"] % 4 >= 2))
    n = d.groupby(["unit", "fy"])["y"].transform("count")
    d = d[n == 4]
    return d.groupby(["unit", "fy"])["y"].mean().reset_index().rename(columns={"fy": "time"})


def price_result(rel: dict[str, pd.DataFrame], case: Case, spec: PriceSpec) -> dict:
    by_name = {c["code"]: c for c in CPI_CLASSES}
    placebo_codes = [
        c["code"] for c in CPI_CLASSES if c["subgroup"] not in spec.exclude_subgroups and c["code"] not in spec.codes
    ]
    first = min(c.first_post for c in spec.cohorts)
    out = {"role": spec.role, "expected": spec.expected, "placebo_classes": len(placebo_codes), "classes": {}}
    for code in spec.codes:
        t = hide(rel[code], spec.cohorts)
        res = summarise(
            stacked(t, spec.cohorts, spec.start), [stacked(rel[c], spec.cohorts, spec.start) for c in placebo_codes]
        )
        dt = summarise(
            stacked(detrend(t, first), spec.cohorts, spec.start),
            [stacked(detrend(rel[c], first), spec.cohorts, spec.start) for c in placebo_codes],
        )
        # Year by year (financial-year averages, the case's FY cohorts), net of the placebo-class mean.
        tf = hide(to_fy(rel[code]), case.cohorts)
        raw = stacked_event(tf, case.cohorts, 2001)
        P = pd.DataFrame([stacked_event(to_fy(rel[c]), case.cohorts, 2001) for c in placebo_codes])
        shock = P.mean()
        centred = P - shock
        net = raw.reindex(shock.index) - shock
        out["classes"][code] = {
            "name": by_name[code]["name"],
            **res,
            "detrended": {k: dt.get(k) for k in ("estimate", "p", "interval_90")},
            "event_net": series(net),
            "event_band_90": {
                str(k): [num(net[k] - centred[k].quantile(0.95)), num(net[k] - centred[k].quantile(0.05))]
                for k in net.index
            },
        }
    return out


# --- decision rule, grade and multiple testing -----------------------------------------------------


def decide(case: Case, entry: dict, vintage: dict, q: float | None) -> str:
    d, p = entry["estimate"], entry["p"]
    if d is None or p is None:
        return "hidden" if BLIND else "not-identified"
    sig = p < 0.05 and q is not None and q < 0.10
    same = (
        np.sign(entry["plain"]) == np.sign(d)
        and vintage["estimate"] is not None
        and np.sign(vintage["estimate"]) == np.sign(d)
    )
    if not (sig and same):
        return "inconclusive"
    if case.hypothesis == "mixed":
        return "detects-increase" if d > 0 else "detects-decrease"
    predicted = 1 if case.hypothesis == "enhancing" else -1
    if np.sign(d) == predicted:
        return f"supports-{case.hypothesis}"
    return f"contradicts-{case.hypothesis}"


def grade(case: Case, feasible: dict, events: dict, entry: dict, robust: dict) -> tuple[str, list[str]]:
    reasons = []
    if not feasible["ok"]:
        return "Not identified", feasible["reasons"]
    if events["pre_inside_95"] is False:
        return "Not identified", ["a pre-reform year lies outside its 95% placebo band"]
    if entry["estimate"] is None:
        return "hidden", []
    lo, hi = entry["interval_90"]
    outside = [k for k, v in robust.items() if v["estimate"] is None or not lo <= v["estimate"] <= hi]
    g = "Moderate"
    if outside:
        g = "Weak"
        reasons.append(f"robustness variants outside the main 90% interval: {', '.join(outside)}")
    elif (
        len(case.cohorts) >= 2
        and len(treated_states(case.cohorts)) >= 3
        and (entry["mde_80"] or 99) <= EFFECT_OF_INTEREST
    ):
        g = "Strong"
    order = ["Not identified", "Weak", "Moderate", "Strong"]
    if case.grade_cap and order.index(g) > order.index(case.grade_cap[0]):
        g = case.grade_cap[0]
        reasons.append(case.grade_cap[1])
    return g, reasons


def bh(pvals: dict[str, float]) -> dict[str, float]:
    """Benjamini-Hochberg q-values."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    q, running = {}, 1.0
    for i, (k, p) in reversed(list(enumerate(items, start=1))):
        running = min(running, p * m / i)
        q[k] = running
    return q


# --- main ------------------------------------------------------------------------------------------


def run_case(case: Case, panels: dict, rel: dict, prod: pd.DataFrame) -> dict:
    w = panels["own"]
    pg = placebo_groups(w, case)
    reasons = []
    if pg["treated_size"] < MIN_TREATED:
        reasons.append(
            f"treated group has {pg['treated_size']:.0f} businesses in the base year (rule: at least {MIN_TREATED})"
        )
    if len(pg["groups"]) < MIN_PLACEBOS:
        reasons.append(f"only {len(pg['groups'])} placebo groups (rule: at least {MIN_PLACEBOS})")
    feasible = {"ok": not reasons, "reasons": reasons}
    out = {
        "id": case.id,
        "title": case.title,
        "hypothesis": case.hypothesis,
        "classes": list(case.classes),
        "cohorts": [c.__dict__ for c in case.cohorts],
        "placebo_design": {k: v for k, v in pg.items() if k != "groups"} | {"groups": len(pg["groups"])},
        "feasible": feasible,
    }
    rates = {k: Rates(v) for k, v in panels.items()}
    for measure in ("entries", "exits"):
        if not feasible["ok"]:
            out[measure] = None
            continue
        main = entry_estimate(rates["own"], case, measure, pg["groups"])
        events = event_paths(rates["own"], case, measure, pg["groups"])
        robust = {}
        for name, v in variants(case).items():
            r = rates[v["w"]] if "w" in v else rates["own"]
            res = entry_estimate(r, case, measure, pg["groups"], cohorts=v.get("cohorts"))
            robust[name] = {k: res.get(k) for k in ("estimate", "plain", "p", "interval_90", "placebos")}
        out[measure] = {"main": main, "event": events, "robustness": robust}
    out["productivity"] = productivity_result(prod, case)
    out["prices"] = price_result(rel, case, case.price) if case.price else None
    return out


def main() -> None:
    global BLIND
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--blind", action="store_true", help="design stage: treated outcomes hidden")
    ap.add_argument("--only", help="run one case id (for checking)")
    args = ap.parse_args()
    BLIND = args.blind
    own = cabee()
    FIRST_YEAR.update(own.groupby("state")["fy"].min().astype(int).to_dict())
    panels = {"own": own, "overlap": overlap_vintage(own), "employing": cabee(employing=True)}
    raw = cpi_quarterly()
    rel = relative_prices(raw)
    prod = productivity_panel(raw)
    results = [run_case(c, panels, rel, prod) for c in CASES if not args.only or c.id == args.only]

    # Multiple testing across the batch's primary outcomes (entry), then decision and grade.
    pvals = {
        r["id"]: r["entries"]["main"]["p"] for r in results if r["entries"] and r["entries"]["main"]["p"] is not None
    }
    qvals = bh(pvals)
    for r in results:
        case = next(c for c in CASES if c.id == r["id"])
        if r["entries"] is None:
            r["verdict"], (r["grade"], r["grade_reasons"]) = (
                "not-identified",
                ("Not identified", r["feasible"]["reasons"]),
            )
            continue
        r["q_bh"] = num(qvals.get(r["id"]), 4)
        r["verdict"] = decide(
            case, r["entries"]["main"], r["entries"]["robustness"]["vintage_overlap"], qvals.get(r["id"])
        )
        r["grade"], r["grade_reasons"] = grade(
            case, r["feasible"], r["entries"]["event"], r["entries"]["main"], r["entries"]["robustness"]
        )

    report = {
        "plan": "docs/pap_high_evaluability.md",
        "mode": "DESIGN STAGE: treated outcomes hidden" if BLIND else "UNBLINDED: registered analysis",
        "units": "entries or exits per 100 businesses operating at the start of the financial year; "
        "productivity, pay and prices in log points (about %)",
        "cases": results,
    }
    name = "design.json" if BLIND else "estimate.json"
    if args.only:
        name = f"check_{args.only}_{'blind' if BLIND else 'open'}.json"
    (HERE / name).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {HERE / name}")


if __name__ == "__main__":
    main()
