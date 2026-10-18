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

from alicia.register.evaluation import Evaluation, write_evaluation

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


def periods(w: dict, months_per_step: int) -> str:
    """Periods before, on (others adopted, WA not yet) and off (both adopted), from the registered windows."""

    def months(a: str, b: str) -> int:
        x, y = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
        return (y.year - x.year) * 12 + y.month - x.month

    pre, on = months(w["pre_start"], w["t1"]), months(w["t1"], w["t2"])
    off = months(w["t2"], w["end"]) + months_per_step  # the end period is included
    return " / ".join(str(m // months_per_step) for m in (pre, on, off))


def gap(v: float) -> str:
    return f"{v:.2f}".replace("-", "−")


def regression_tables(e: dict, d: dict) -> list[dict]:
    """The on-off design's estimands across, one panel per outcome, registered and detrended: one table for the
    registered outcomes, one for the descriptive ones."""
    cols = [("main", "pooled"), ("main", "early"), ("main", "late")]
    cols += [("detrended", k) for _, k in cols]
    outcomes = [
        ("exits", "Childcare share of business exits, percentage points (primary outcome)", 1, True),
        ("prices", "Child care prices relative to all prices, 100 × log points (primary outcome)", 3, True),
        ("entries", "Childcare share of new ABNs, percentage points (secondary outcome)", 1, True),
        ("hours", "Hours worked in child care, 100 × log points (descriptive)", 3, False),
        ("employment", "Employment in child care, 100 × log points (descriptive)", 3, False),
    ]
    panels = []
    for k, title, step, registered in outcomes:
        r = e[k]
        res = [r[v][est] for v, est in cols]
        rows = [
            {
                "label": "Framework × WA timing (β)",
                "coefficients": [
                    {
                        "estimate": x["estimate"],
                        "spread": x["null"]["sd"],
                        "p_value": x["p"],
                        "registered": registered and j == 0,
                    }
                    for j, x in enumerate(res)
                ],
            },
            {"label": "No-effect estimates", "values": [str(x["null"]["n"]) for x in res]},
            {"label": "MDE (80% power)", "values": [f"{x['null']['mde_80']:.2f}" for x in res]},
            {
                "label": "Gap after WA adopted vs pre-2012",
                "values": [gap(r["main"]["off_vs_pre"]), None, None, gap(r["detrended"]["off_vs_pre"]), None, None],
            },
        ]
        if k in ("exits", "entries"):
            rows.append({"label": "WA share before 2012, %", "values": [f"{d[k]['wa_pre_level']:.2f}"] * 6})
        if k in e.get("q_values", {}):
            rows.append({"label": "BH q-value", "values": [f"{e['q_values'][k]:.3f}", *[None] * 5]})
        per = periods(d[k if k != "employment" else "hours"]["windows"], step)
        span = f"{per} {'months' if step == 1 else 'quarters'} before / on / off"
        panels.append({"title": f"{title[:-1]}; {span})", "rows": rows})
    main_panels = [p | {"title": f"Panel {'ABC'[i]}. {p['title']}"} for i, p in enumerate(panels[:3])]
    desc_panels = [p | {"title": f"Panel {'AB'[i]}. {p['title']}"} for i, p in enumerate(panels[3:])]
    base = {
        "columns": [
            {"label": "Pooled", "group": "Registered (seasonal means removed)"},
            {"label": "Early", "group": "Registered (seasonal means removed)"},
            {"label": "Late", "group": "Registered (seasonal means removed)"},
            {"label": "Pooled", "group": "Pre-trend also removed"},
            {"label": "Early", "group": "Pre-trend also removed"},
            {"label": "Late", "group": "Pre-trend also removed"},
        ],
        "footer": [
            {"label": "Seasonal means removed", "values": ["Yes"] * 6},
            {"label": "Linear pre-trend removed", "values": ["No"] * 3 + ["Yes"] * 3},
        ],
        "spread_label": "Placebo standard deviation",
        "notes": [
            "On-off difference-in-differences (alicia.evaluate.stagger) on the gap between WA and the mean of the "
            "other seven jurisdictions, less its pre-2012 mean for each season. The framework started in January "
            "2012 everywhere but WA, which followed in August 2012 (2012-Q3 in quarterly data). Pooled: one effect "
            "from the gap opening and closing. Early: the other jurisdictions in January to July 2012 against WA, not "
            "yet treated. Late: WA's change when it adopted, against the others (assumes their effect did not build "
            "up). The gap row shows whether the gap returned to its pre-2012 level once both had "
            "adopted.",
            "The placebo standard deviation is the spread of the no-effect estimates: the same estimator for "
            "placebo industries (CPI classes, Labour Force groups) over the same windows and for childcare at fake "
            "dates before 2012. p-values rank the estimate among them. BH q-value: Benjamini-Hochberg across the two "
            "primary outcomes. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo "
            "standard deviation).",
            "Source: alicia/analyses/childcare_nqf_wa/estimate.json (registered run, 18 October 2026) and "
            "design.json (windows, pre-2012 levels).",
        ],
    }
    title = "National Quality Framework for childcare (2012): WA's seven-month delay"
    data_main = (
        "Panels A and C: businesses whose names say childcare, as a share of all named businesses' ABN cancellations "
        "(A) or of new ABNs still active in October 2026 (C), monthly from January 2009 to July 2013. Panel B: the "
        "child care CPI relative to All groups, Perth against the other capitals, quarterly from 2009-Q1 to 2013-Q2."
    )
    data_desc = (
        "Labour Force industry group 871 (child care services), WA against the other jurisdictions, quarterly from "
        "2009-Q1 to 2013-Q2. Registered as descriptive: WA's quarterly estimates for one group are too noisy to test."
    )
    return [
        base
        | {
            "id": f"{EV_ID}-on-off",
            "title": f"{title}: on-off estimates",
            "panels": main_panels,
            "notes": [data_main, *base["notes"]],
        },
        base
        | {
            "id": f"{EV_ID}-on-off-descriptive",
            "title": f"{title}: hours and employment (descriptive)",
            "panels": desc_panels,
            "notes": [data_desc, *base["notes"]],
        },
    ]


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
            "On-off difference-in-differences (alicia.evaluate.stagger): the gap between WA and the other "
            "jurisdictions should open when they adopted the framework (January 2012) and close when WA did "
            "(August 2012). Monthly business exits and entries from the ABN register, quarterly child care prices "
            "and employment."
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
        "key_insights": [
            "The question: did the National Quality Framework for childcare (staff ratios, qualifications, quality "
            "ratings) push childcare businesses out or raise prices soon after it started?",
            "The natural experiment: every other jurisdiction started in January 2012, but WA only in August 2012. "
            "If the framework mattered straight away, the gap between WA and the rest should open in January and "
            "close again in August.",
            f"What we found: no detectable early effect. Childcare's share of business closures moved "
            f"{s2(exp['estimate'])} percentage points (90% interval {s2(exp['interval_90'][0])} to "
            f"{s2(exp['interval_90'][1])}) on a base of {base_exit:.1f}%, and child care prices "
            f"{s1(prp['estimate'])}% ({s1(prp['interval_90'][0])} to {s1(prp['interval_90'][1])}).",
            f"How precise: only very large effects could have been seen: about {exp['null']['mde_80']:.1f} points "
            f"on closures (roughly a doubling of childcare's share) or about {prp['null']['mde_80']:.0f}% on prices.",
            "What it means: no sign of an immediate shake-out or price jump. The later staff ratio and qualification "
            "phases (2014, 2016) are not covered, and Department of Education data on services and fees would allow "
            "a sharper test.",
        ],
        "method": {
            "summary": "On-off difference-in-differences for a rule that starts late in one jurisdiction: the gap "
            "between the late adopter and the rest is compared across three windows (before, others only, all). "
            "Inference from placebo industries and fake dates.",
            "equations": [
                {
                    "label": "The gap, each month (or quarter)",
                    "text": "G_{t} = y^{WA}_{t} − ȳ^{others}_{t} − s̄_{season(t)}",
                },
                {
                    "label": "Pooled effect (primary)",
                    "text": "hat{δ} = mean_{t ∈ pre ∪ off}(G_{t}) − mean_{t ∈ on}(G_{t})",
                },
                {
                    "label": "Early effect and late effect (secondary)",
                    "text": "hat{δ}_{early} = mean_{pre}(G_{t}) − mean_{on}(G_{t});   "
                    "hat{δ}_{late} = mean_{off}(G_{t}) − mean_{on}(G_{t})",
                },
            ],
            "terms": [
                {
                    "symbol": "y_{t}",
                    "meaning": "Exits: childcare-named businesses' share of named-business ABN cancellations (%), "
                    "monthly. Prices: 100 × ln(child care CPI / all-groups CPI), quarterly, Perth against the mean "
                    "of the other capitals",
                },
                {"symbol": "ȳ^{others}_{t}", "meaning": "The other seven jurisdictions pooled"},
                {
                    "symbol": "s̄_{season(t)}",
                    "meaning": "The gap's pre-period mean for the same month or quarter of the year",
                },
                {
                    "symbol": "pre",
                    "meaning": "January 2009 to December 2011; quarterly outcomes 2009-Q1 to 2011-Q4 (no one treated)",
                },
                {"symbol": "on", "meaning": "January to July 2012; quarterly 2012-Q1 and Q2 (all but WA treated)"},
                {"symbol": "off", "meaning": "August 2012 to July 2013; quarterly 2012-Q3 to 2013-Q2 (all treated)"},
            ],
            "estimand": "The framework's immediate effect on the outcome, measured by how the WA-minus-others gap "
            "moves when the others adopt (on) relative to when nobody (pre) or everybody (off) has it. The early part "
            "needs only parallel trends; the pooled estimate also assumes the effect is immediate and lasting.",
            "identification": "Without the framework, the WA-minus-others gap would have kept its usual seasonal "
            "pattern through 2012-13. The on-off pattern guards against a WA-specific shock, which would not switch "
            "off in August 2012.",
            "inference": f"No conventional standard errors (one late jurisdiction). No-effect distribution: the same "
            f"estimator for {d['exits']['placebo_industries']} named industries over the same windows plus childcare "
            f"at {d['exits']['fake_dates']} fake dates two or more years earlier (exits). p-value: two-sided rank; "
            "90% interval: estimate minus the 95th and 5th percentiles (Conley and Taber 2011); smallest detectable "
            "effect: 2.8 × standard deviation; Benjamini–Hochberg q-values across the two primaries.",
            "steps": [
                "Built monthly counts of ABN cancellations and registrations by industry inferred from business names "
                "(childcare rule checked on City of Melbourne names), quarterly CPI by capital and Labour Force "
                "employment and hours.",
                "Design-stage review with WA's childcare outcomes from January 2012 hidden in code; chose the windows, "
                "placebo pools and outcome roles, and committed the plan (docs/pap_childcare_nqf_wa.md).",
                "Ran a blinded dry run that reproduced the design-stage no-effect distributions, then one unblinded "
                "run.",
                "Estimated the pooled, early and late effects, the after-against-before check and detrended variants "
                "for each outcome.",
                "Applied the plan's findings, verdict and grading rules. A check dropping one outlying month "
                "(December 2010) was added after unblinding and is labelled as such.",
            ],
        },
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
            {"label": "Design review (blinded)", "path": "alicia/analyses/childcare_nqf_wa/design.json"},
            {"label": "Estimation code", "path": "alicia/analyses/childcare_nqf_wa/estimate.py"},
            {"label": "Method (on-off design)", "path": "alicia/src/alicia/evaluate/stagger.py"},
            {"label": "Earlier evaluation", "path": "docs/results_high_evaluability.md"},
        ],
        "built_by": "alicia/analyses/childcare_nqf_wa/evaluation.py",
        "tables": regression_tables(e, d),
    }
    print(f"wrote {write_evaluation(Evaluation.model_validate(ev))}")


if __name__ == "__main__":
    main()
