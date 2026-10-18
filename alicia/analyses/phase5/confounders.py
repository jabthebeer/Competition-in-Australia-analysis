"""Confounder scan for a Phase 5 specification: other changes near each reform, and when each treated series moved.

Two parts, for every case and outcome:

1. Register overlap (uses no outcome data, so it can run before unblinding). Other register records with a
   commencement from a year before the window to its end, in a treated or comparison state (or national),
   that touch the same ANZSIC class, group, subdivision or division, or name the same CPI class in their
   price series. Plus the confounders each case's own records already list.
2. Timing (uses outcome data). For each cohort and treated state, the treated series' gap against the
   comparison states, net of the same states' other industries for business counts; for prices, the class is
   already relative to All groups. Steps from one period to the next are scaled by the spread of pre-reform
   steps. A step of 3 or more spreads anywhere but the reform period (or the one after) is flagged: something
   other than the reform may have moved the series. With --blind the scan stops before the first exposed period
   (pre-reform jumps only), so it can be part of a design stage.

Written after the Phase 5 results were seen, for those specifications it is NOT pre-registered: it can only add
caveats. New specifications run it blind at the design stage (docs/specification_runner.md).

    uv run python analyses/phase5/confounders.py --spec phase5-reevaluations           # writes confounders.json
    uv run python analyses/phase5/confounders.py --spec phase5-reevaluations --table   # Markdown tables
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("phase5_run", HERE / "run.py")
run = importlib.util.module_from_spec(_spec)
sys.modules["phase5_run"] = run
_spec.loader.exec_module(run)
power, prices = run.power, run.prices

from alicia import anzsic, cpi  # noqa: E402
from alicia.register.catalogue import load_records  # noqa: E402
from alicia.runner.spec import load  # noqa: E402

FLAG_SD = 3.0  # a step this many pre-reform spreads from zero is flagged
CLOSE = ("same class", "same group", "names the same CPI class")


def relevance(where: str, rel: str) -> str:
    """High: a close match in a treated state. Medium: a looser match in a treated state, or a close one in a
    comparison state (it moves the comparison). Low: national changes (common to all states, so absorbed by period
    effects unless exposure differs) and division-level matches."""
    if where == "treated state" and rel in CLOSE:
        return "high"
    if (where == "treated state" and not rel.startswith("same division")) or (
        where == "comparison state" and rel in CLOSE
    ):
        return "medium"
    return "low"


LEAD = {"price": 4, "business": 1}  # periods before the window searched for register overlap


def fy_of(d: dt.date) -> int:
    return d.year + (d.month >= 7)


def quarter_of(d: dt.date) -> int:
    return d.year * 4 + (d.month - 1) // 3


def label(kind: str, t: int) -> str:
    return f"{t // 4}-Q{t % 4 + 1}" if kind == "price" else f"{t - 1}-{str(t)[2:]}"


def primary_date(r) -> dt.date | None:
    c = next((c for c in r.dates.commenced if c.primary), r.dates.commenced[0] if r.dates.commenced else None)
    return c.date if c else None


def relation(code: str, cls: str) -> str | None:
    """How a record's ANZSIC code relates to an outcome class (4 digits)."""
    if len(code) == 1:
        return "same division" if anzsic.division(cls) == code else None
    if len(code) == 4:
        if code == cls:
            return "same class"
        if code[:3] == cls[:3]:
            return "same group"
        return "same subdivision" if code[:2] == cls[:2] else None
    return f"covers the class ({'group' if len(code) == 3 else 'subdivision'} {code})" if cls.startswith(code) else None


def register_overlap(case: dict, records: dict) -> list[dict]:
    own = set(case["records"])
    hits: dict[str, dict] = {}
    for o in case["outcomes"]:
        kind = "price" if o["kind"] == "price" else "business"
        to_t = run.period(o)
        cls_name = next((c["name"] for c in cpi.classes() if c["code"] == o.get("code")), None)
        for c in o["cohorts"]:
            lo, hi = to_t(c["first_post"]) - LEAD[kind], to_t(c["last_post"])
            where = {**dict.fromkeys(c["controls"], "comparison state"), **dict.fromkeys(c["treated"], "treated state")}
            for r in records.values():
                if r.id in own:
                    continue
                d = primary_date(r)
                if d is None:
                    continue
                t = quarter_of(d) if kind == "price" else fy_of(d)
                place = "national" if r.jurisdiction == "CTH" else where.get(r.jurisdiction)
                if place is None or not lo <= t <= hi:
                    continue
                if kind == "price":
                    why = (
                        "names the same CPI class"
                        if cls_name and cls_name in cpi.matched_classes(r.price_series)
                        else None
                    )
                else:
                    rel = [relation(i.anzsic, cls) for i in r.industries for cls in o["classes"]]
                    why = next((x for x in ("same class", "same group") if x in rel), None) or next(
                        (x for x in rel if x), None
                    )
                if not why:
                    continue
                key = r.id
                timing = "in window" if t >= to_t(c["first_post"]) else "in the year before"
                hit = hits.setdefault(
                    key,
                    {
                        "record": r.id,
                        "title": r.title,
                        "jurisdiction": r.jurisdiction,
                        "date": d.isoformat(),
                        "where": place,
                        "relation": why,
                        "relevance": relevance(place, why),
                        "timing": timing,
                        "outcomes": [],
                    },
                )
                if o["key"] not in hit["outcomes"]:
                    hit["outcomes"].append(o["key"])
    rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(hits.values(), key=lambda h: (rank[h["relevance"]], h["date"]))


def business_gap(w: pd.DataFrame, o: dict, state: str, controls: list[str], start: int, last: int) -> pd.Series:
    """(treated classes' rate - other classes' rate) in the state, less the same in the comparison states."""
    d = w[(w["fy"].between(start, last)) & (w["anzsic"].str.len() == 4) & (w["anzsic"] != "9999")]
    d = d.assign(tr=d["anzsic"].isin(o["classes"]))
    measure = o["measure"]

    def rate(states: list[str], treated: bool) -> pd.Series:
        g = d[d["state"].isin(states) & (d["tr"] == treated)].groupby("fy")[[measure, "start"]].sum()
        return 100 * g[measure] / g["start"]

    return (rate([state], True) - rate([state], False)) - (rate(controls, True) - rate(controls, False))


def price_gap(rel: pd.DataFrame, o: dict, state: str, controls: list[str], start: int, last: int) -> pd.Series:
    d = rel[(rel["cls"] == o["code"]) & rel["t"].between(start, last)].pivot(index="t", columns="state", values="y")
    return d[state] - d[[s for s in controls if s in d]].mean(axis=1)


def timing(case: dict, blind: bool, w: pd.DataFrame, rel: pd.DataFrame) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for o in case["outcomes"]:
        kind = "price" if o["kind"] == "price" else "business"
        to_t = run.period(o)
        start = to_t(o["start"])
        rows = []
        for c in o["cohorts"]:
            first, last = to_t(c["first_post"]), to_t(c["last_post"])
            for s in c["treated"]:
                end = first - 1 if blind else last
                if kind == "price":
                    gap = price_gap(rel, o, s, c["controls"], start, end)
                else:
                    gap = business_gap(w, o, s, c["controls"], start, end)
                gap = gap.dropna()
                step = gap.diff().dropna()
                pre = step[step.index < first]
                if len(pre) < 3:
                    rows.append({"state": s, "reform": label(kind, first), "note": "fewer than 3 pre-reform steps"})
                    continue
                sd = float(pre.std(ddof=1))
                look = step[step.index >= first - (4 if kind == "price" else 2)]
                big = look[(look.abs() / sd) >= FLAG_SD]
                at_reform = [t for t in (first, first + 1) if t in step.index]
                top = look.abs().idxmax() if len(look) else None
                if blind or top is None:
                    verdict = "pre-reform jump" if len(big) else "no large pre-reform move"
                elif abs(look[top]) / sd < FLAG_SD:
                    verdict = "no large move"
                elif top in at_reform:
                    verdict = "largest move at the reform"
                elif top < first:
                    verdict = "largest move before the reform"
                else:
                    verdict = "largest move after the reform period"
                rows.append(
                    {
                        "state": s,
                        "reform": label(kind, first),
                        "step_sd": round(sd, 3),
                        "pre_steps": int(len(pre)),
                        "at_reform": {label(kind, t): round(float(step[t] / sd), 2) for t in at_reform},
                        "largest": None
                        if top is None
                        else {
                            "period": label(kind, int(top)),
                            "step": round(float(look[top]), 3),
                            "in_sd": round(float(look[top] / sd), 2),
                        },
                        "flagged": {label(kind, int(t)): round(float(v / sd), 2) for t, v in big.items()},
                        "verdict": verdict,
                    }
                )
        out[o["key"]] = rows
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True, choices=sorted(run.FOLDERS))
    ap.add_argument("--blind", action="store_true", help="timing on pre-reform periods only (design stage)")
    ap.add_argument("--table", action="store_true", help="print Markdown tables from confounders.json")
    args = ap.parse_args()
    folder = HERE / run.FOLDERS[args.spec]
    path = folder / ("confounders_blind.json" if args.blind else "confounders.json")
    if args.table:
        print(tables(json.loads(path.read_text("utf-8"))))
        return
    spec = load(args.spec)
    records = {r.id: r for r in load_records().records}
    w, rel = power.cabee(False), prices.relative_prices()
    cases = []
    for case in spec.cases:
        known = {rid: list(records[rid].confounders) for rid in case["records"] if records[rid].confounders}
        cases.append(
            {
                "id": case["id"],
                "title": case["title"],
                "known": known,
                "register": register_overlap(case, records),
                "timing": timing(case, args.blind, w, rel),
            }
        )
        print(f"  {case['id']}: {len(cases[-1]['register'])} register overlaps", flush=True)
    out = {
        "spec": args.spec,
        "preregistered": False,
        "mode": "BLIND: pre-reform periods only"
        if args.blind
        else "post-hoc: written after the registered results were seen",
        "flag_sd": FLAG_SD,
        "cases": cases,
    }
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", "utf-8")
    print(f"wrote {path}")


def tables(data: dict) -> str:
    lines = [f"Mode: {data['mode']}.", ""]
    for c in data["cases"]:
        lines += [f"### {c['title']}", ""]
        shown = [h for h in c["register"] if h["relevance"] != "low"]
        low = len(c["register"]) - len(shown)
        if shown:
            lines += [
                "| Relevance | Other change | Where | Date | Relation | Timing | Outcomes |",
                "|---|---|---|---|---|---|---|",
            ]
            lines += [
                f"| {h['relevance']} | {h['title']} (`{h['record']}`) | {h['where']} ({h['jurisdiction']}) | "
                f"{h['date']} | {h['relation']} | {h['timing']} | {', '.join(h['outcomes'])} |"
                for h in shown
            ]
        else:
            lines.append("No other register change of high or medium relevance in or just before the window.")
        if low:
            lines.append(
                f"\nPlus {low} of low relevance (national, or a division-level match), listed in confounders.json."
            )
        lines.append("")
        rows = [(k, r) for k, rs in c["timing"].items() for r in rs]
        if rows:
            lines += [
                "| Outcome | State | Reform period | Step there (× pre-reform spread) "
                "| Largest step (period, × spread) "
                "| Verdict |",
                "|---|---|---|---|---|---|",
            ]
            for k, r in rows:
                if "note" in r:
                    lines.append(f"| {k} | {r['state']} | {r['reform']} | — | — | {r['note']} |")
                    continue
                at = ", ".join(f"{p}: {v:+.1f}" for p, v in r["at_reform"].items()) or "—"
                big = r["largest"]
                top = f"{big['period']}: {big['in_sd']:+.1f}" if big else "—"
                lines.append(f"| {k} | {r['state']} | {r['reform']} | {at} | {top} | {r['verdict']} |")
            lines.append("")
        if c["known"]:
            lines += [
                "Already listed in the records: " + "; ".join(f"{', '.join(v)} (`{k}`)" for k, v in c["known"].items()),
                "",
            ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
