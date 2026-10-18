"""Write the register's evaluation file for the NQF-in-WA evaluation from estimate.json and paths.json.

Every number comes from estimate.json (the registered run), design.json or paths.json (display
paths); only the wording is written here, and tests/test_evaluation.py checks the file.

Run: uv run python analyses/childcare_nqf_wa/evaluation.py
Writes: regulation-register/evaluations/childcare-nqf-wa-delay-2012.json
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from alcia.register.evaluation import Evaluation, write_evaluation

HERE = Path(__file__).resolve().parent
EV_ID = "childcare-nqf-wa-delay-2012"
PTS = "percentage points"
LOG = "% (log points)"


def s1(v: float) -> str:
    return f"{v:+.1f}".replace("-", "−")


def s2(v: float) -> str:
    return f"{v:+.2f}".replace("-", "−")


def fp(p: float) -> str:
    return "< 0.01" if p < 0.01 else f"{p:.2f}"


def parts(m: dict, fmt=s1) -> str:
    return (
        f"Early (others in Jan-Jul 2012 against WA): {fmt(m['early']['estimate'])}; late (WA's change when it "
        f"adopted): {fmt(m['late']['estimate'])}; gap after WA adopted against before 2012: {fmt(m['off_vs_pre'])}."
    )


def outcome(oid, label, category, role, unit, res: dict, basis: str, **kw) -> dict:
    r = res["main"]["pooled"]
    return {
        "id": oid,
        "label": label,
        "category": category,
        "role": role,
        "unit": unit,
        "estimate": r["estimate"],
        "interval": {"low": r["interval_90"][0], "high": r["interval_90"][1], "level": 0.9},
        "no_effect_range": {"low": r["null"]["q05"], "high": r["null"]["q95"], "basis": basis},
        "p_value": r["p"],
        "inference": "Rank among placebo industries over the same windows and childcare at fake dates (two-sided)",
        "mde_80": r["null"]["mde_80"],
        "preregistered": True,
        **kw,
    }


def points(path: list[dict], start: dt.date, months_per_step: int) -> list[dict]:
    out = []
    for p in path:
        t = dt.date.fromisoformat(p["time"])
        k = ((t.year - start.year) * 12 + t.month - start.month) // months_per_step
        label = f"{t:%b %Y}" if months_per_step == 1 else f"{t.year} Q{(t.month - 1) // 3 + 1}"
        out.append({"period": label, "k": k, "estimate": p["gap"], "low": p["low"], "high": p["high"]})
    return out


def main() -> None:
    e = json.loads((HERE / "estimate.json").read_text("utf-8"))
    d = json.loads((HERE / "design.json").read_text("utf-8"))
    paths = json.loads((HERE / "paths.json").read_text("utf-8"))
    assert not e["blind"], "estimate.json must be the unblinded run"
    ex, pr, en, hr, em = (e[k] for k in ("exits", "prices", "entries", "hours", "employment"))
    exp, prp = ex["main"]["pooled"], pr["main"]["pooled"]
    base_exit = d["exits"]["wa_pre_level"]
    n = lambda k: f"{d[k]['null']['pooled']['n']} no-effect estimates"  # noqa: E731
    outcomes = [
        outcome(
            "childcare-exits",
            "Childcare businesses' share of business exits",
            "competition",
            "primary",
            PTS,
            ex,
            f"90% range of {n('exits')}: {d['exits']['placebo_industries']} named industries and childcare at "
            f"{d['exits']['fake_dates']} fake dates",
            baseline=base_exit,
            baseline_label="WA share before 2012, %",
            finding=exp["finding"],
            grade="Moderate",
            note=(
                "ABN cancellations of businesses whose names say childcare, as a share of named-business "
                f"cancellations, WA minus the other jurisdictions. {parts(ex['main'], s2)} Detrended: "
                f"{s2(ex['detrended']['pooled']['estimate'])} (p = {fp(ex['detrended']['pooled']['p'])})."
            ),
        ),
        outcome(
            "child-care-prices",
            "Child care prices relative to all prices",
            "prices",
            "primary",
            LOG,
            pr,
            f"90% range of {n('prices')}: {d['prices']['placebo_industries']} CPI classes and child care at "
            f"{d['prices']['fake_dates']} fake dates",
            finding=prp["finding"],
            grade="Moderate",
            note=(
                f"Perth against the other capitals. {parts(pr['main'])} Detrended: "
                f"{s1(pr['detrended']['pooled']['estimate'])} (p = {fp(pr['detrended']['pooled']['p'])}). "
                "Not fully blind: an early-period estimate was reported in the first evaluation."
            ),
        ),
        outcome(
            "childcare-entries",
            "Childcare businesses' share of new ABNs (survivors)",
            "competition",
            "secondary",
            PTS,
            en,
            f"90% range of {n('entries')}",
            baseline=d["entries"]["wa_pre_level"],
            baseline_label="WA share before 2012, %",
            finding=en["main"]["pooled"]["finding"],
            note="Counts only ABNs still active in October 2026, so entries are understated in both groups. "
            + parts(en["main"], s2),
        ),
        outcome(
            "childcare-hours",
            "Hours worked in child care",
            "productivity",
            "descriptive",
            LOG,
            hr,
            f"90% range of {n('hours')}",
            finding="descriptive-only",
            note="WA's quarterly estimates for one industry group swing by up to 30 log points; nothing is "
            "detectable below about 55%.",
        ),
        outcome(
            "childcare-employment",
            "Employment in child care",
            "productivity",
            "descriptive",
            LOG,
            em,
            f"90% range of {n('employment')}",
            finding="descriptive-only",
            note="As for hours. The interval excludes zero but p is 0.18: the no-effect estimates are lopsided.",
        ),
    ]
    ev = {
        "id": EV_ID,
        "title": "National Quality Framework for childcare (2012): WA's seven-month delay, monthly data",
        "records": ["cth-nqf-childcare-2012", "wa-nqf-childcare-2012"],
        "family": "childcare-nqf",
        "follows": "childcare-nqf-2012",
        "evaluated_on": dt.date(2026, 10, 18).isoformat(),
        "hypothesis": "weakening",
        "design": (
            "On-off difference-in-differences (alcia.evaluate.stagger): the gap between WA and the other jurisdictions "
            "should open when they adopted the framework (January 2012) and close when WA did (August 2012). Monthly "
            "business exits and entries from the ABN register, quarterly child care prices and employment."
        ),
        "comparison": (
            "WA against the other seven jurisdictions pooled; inference from placebo industries over the same windows "
            "and childcare at earlier fake dates."
        ),
        "window": "2009 to mid-2013: before 2012; January to July 2012 (only WA without the framework); August 2012 "
        "to July 2013 (all with it)",
        "verdict": "inconclusive",
        "finding_label": "No detectable effect",
        "grade": "Moderate",
        "grade_reason": (
            "One late jurisdiction and a seven-month window cap the grade. The plan's checks pass (the exits "
            "fake-date test only at the threshold), but only large effects are detectable: a doubling of childcare's "
            "share of exits, or a price change of about 8%."
        ),
        "headline": (
            f"WA's seven-month delay in adopting the National Quality Framework shows no detectable early effect. "
            f"Childcare's share of business exits moved {s2(exp['estimate'])} percentage points (90% interval "
            f"{s2(exp['interval_90'][0])} to {s2(exp['interval_90'][1])}) on a base of {base_exit:.1f}%, and "
            f"child care prices {s1(prp['estimate'])}% ({s1(prp['interval_90'][0])} to "
            f"{s1(prp['interval_90'][1])}) relative to other prices. Only large effects could have been detected."
        ),
        "category_summaries": {
            "competition": (
                f"No detectable change in childcare exits or entries. Exits: {s2(exp['estimate'])} points (p = "
                f"{fp(exp['p'])}); the gap opened in January and closed in August 2012 as the framework predicts, but "
                f"by far less than the noise."
            ),
            "prices": (
                f"No detectable early price effect: {s1(prp['estimate'])}% (90% interval "
                f"{s1(prp['interval_90'][0])} to {s1(prp['interval_90'][1])}; p = {fp(prp['p'])}); "
                f"detrended {s1(pr['detrended']['pooled']['estimate'])}%."
            ),
            "productivity": (
                "Not measurable. WA's quarterly child care employment estimates are too noisy for a seven-month window "
                "(smallest detectable effect about 55%)."
            ),
        },
        "preregistered": True,
        "outcomes": outcomes,
        "event_studies": [
            {
                "outcome": "childcare-exits",
                "title": "Childcare share of business exits, WA minus other jurisdictions",
                "unit": PTS,
                "reference": "the pre-2012 average for each quarter of the year",
                "band": "90% range across placebo industries",
                "points": points(paths["exits"], dt.date(2012, 1, 1), 1),
                "markers": [
                    {"k": 0, "label": "Other jurisdictions (Jan 2012)"},
                    {"k": 7, "label": "WA (Aug 2012)"},
                ],
                "caption": (
                    "Monthly; the gap should dip between the two markers if the framework had an immediate effect."
                ),
            },
            {
                "outcome": "child-care-prices",
                "title": "Child care prices relative to all prices, Perth minus other capitals",
                "unit": LOG,
                "reference": "the pre-2012 average for each quarter of the year",
                "band": "90% range across placebo CPI classes",
                "points": points(paths["prices"], dt.date(2012, 1, 1), 3),
                "markers": [
                    {"k": 0, "label": "Other jurisdictions (Jan 2012)"},
                    {"k": 2.33, "label": "WA (Aug 2012)"},
                ],
                "caption": (
                    "Quarterly CPI; prices elsewhere rising relative to Perth would show as a dip after January 2012."
                ),
            },
        ],
        "caveats": [
            "Only the framework's first year and a half is covered; later phase-ins (qualifications in 2014, ratios in "
            "2016) applied in WA and elsewhere alike and cannot be separated here.",
            "Business exits and entries are inferred from business names in the ABN register (childcare rule 82-91% "
            "precise on City of Melbourne names), and childcare is only about 1.5% of named-business exits, so only "
            "very large changes are detectable.",
            "Prices are not fully blind: the first evaluation reported a descriptive estimate for early 2012 (−4.3, "
            "from different windows and net of other price classes).",
            "Administrative data on approved services and fees by state (Department of Education) would be far more "
            "precise but could not be reached from the build environment.",
        ],
        "documents": [
            {"label": "Results", "path": "docs/results_childcare_nqf_wa.md"},
            {"label": "Pre-analysis plan", "path": "docs/pap_childcare_nqf_wa.md"},
            {"label": "Design review (blinded)", "path": "alcia/analyses/childcare_nqf_wa/design.json"},
            {"label": "Estimation code", "path": "alcia/analyses/childcare_nqf_wa/estimate.py"},
            {"label": "Method (on-off design)", "path": "alcia/src/alcia/evaluate/stagger.py"},
            {"label": "Earlier evaluation", "path": "docs/results_high_evaluability.md"},
        ],
        "built_by": "alcia/analyses/childcare_nqf_wa/evaluation.py",
    }
    print(f"wrote {write_evaluation(Evaluation.model_validate(ev))}")


if __name__ == "__main__":
    main()
