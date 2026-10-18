"""Write the register's evaluation file for the Perth weeknight re-evaluation from estimate.json.

Every number comes from estimate.json (the registered run) or design.json; only the wording is
written here, and tests/test_evaluation.py checks the file against the outputs.

Run: uv run python analyses/wa_weeknight_2010/evaluation.py
Writes: regulation-register/evaluations/wa-trading-hours-weeknight-2010-new-data.json
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from alcia.register.evaluation import Evaluation, write_evaluation

HERE = Path(__file__).resolve().parent
EV_ID = "wa-trading-hours-weeknight-2010-new-data"
LOG = "% (log points)"
GAP = "log points (x100)"


def s1(v: float) -> str:
    return f"{v:+.1f}".replace("-", "−")


def fp(p: float) -> str:
    return "< 0.01" if p < 0.01 else f"{p:.2f}"


def no_effect(res: dict, basis: str) -> dict:
    """The centred no-effect range (5th to 95th percentile of the placebo estimates)."""
    n = res["null"]
    return {"low": n["q05"], "high": n["q95"], "basis": basis}


def outcome(oid: str, label: str, category: str, role: str, unit: str, res: dict, basis: str, inference: str, **kw):
    return {
        "id": oid,
        "label": label,
        "category": category,
        "role": role,
        "unit": unit,
        "estimate": res["estimate"],
        "interval": {"low": res["interval_90"][0], "high": res["interval_90"][1], "level": 0.9},
        "no_effect_range": no_effect(res, basis),
        "p_value": res["p"],
        "inference": inference,
        "mde_80": res["null"]["mde_80"],
        "preregistered": True,
        **kw,
    }


def points(es: list[dict], quarters_from: dt.date | None = None, last_pre: dt.date | None = None) -> list[dict]:
    """Event-study points; with `quarters_from`/`last_pre`, three-month bins are labelled by their first
    month (post bins start at the reform month, pre bins end at the last pre month)."""

    def months(k: int) -> str:
        if k >= 0:
            m0 = quarters_from.year * 12 + quarters_from.month - 1 + 3 * k
        else:
            m0 = last_pre.year * 12 + last_pre.month - 1 + 3 * (k + 1) - 2
        return f"{dt.date(m0 // 12, m0 % 12 + 1, 1):%b %Y}"  # first month of the three-month bin

    return [
        {
            "period": months(p["k"]) if quarters_from else p["period"],
            "k": p["k"],
            "estimate": p["estimate"],
            "low": p["low"],
            "high": p["high"],
        }
        for p in es
    ]


def main() -> None:
    e = json.loads((HERE / "estimate.json").read_text("utf-8"))
    d = json.loads((HERE / "design.json").read_text("utf-8"))
    assert not e["blind"], "estimate.json must be the unblinded run"
    a, c = e["A"], e["C"]
    a2, c2, b = e["A_secondary"], e["C_secondary"], e["B_descriptive"]
    base = d["baselines"]
    turnover_base = round(sum(base["turnover_aud_m_per_month_2009_10"][k] for k in ("RT01", "4251", "4260")), 1)
    a_basis = f"90% range of {a['null']['n']} estimates at fake dates since 1995 and in comparison states"
    c_basis = f"90% range of {c['null']['n']} placebo industries and states of a similar size"
    a_inf = "Rank among fake-date and comparison-state estimates (two-sided)"
    c_inf = "Rank among placebo industries in every state and retail in comparison states (two-sided)"
    det, food = a2["detrended"], a2["triple_diff_food"]
    fragile = (
        f"Two registered robustness checks reach p < 0.10 in opposite directions: removing each state's "
        f"pre-reform trend gives {s1(det['estimate'])} (p = {fp(det['p'])}); netting out cafes, restaurants and "
        f"takeaway gives {s1(food['estimate'])} (p = {fp(food['p'])}). The turnover result depends on the comparison."
    )
    outcomes = [
        outcome(
            "retail-businesses-perth",
            "Retail businesses in metropolitan Perth relative to regional WA",
            "competition",
            "primary",
            GAP,
            c,
            c_basis,
            c_inf,
            baseline=float(base["retail_businesses_june_2010"]["cap"]),
            baseline_label="Retail businesses in metropolitan Perth, June 2010",
            finding=c["finding"],
            grade="Moderate",
            note=(
                "Perth minus rest-of-WA gap in log retail businesses, net of the same gap for other industries, "
                "against capital-vs-regional gaps in NSW, Victoria, Queensland, Tasmania and the NT. "
                f"Small businesses only: {s1(c2['small_businesses']['estimate'])}; Mandurah in Perth: "
                f"{s1(c2['with_mandurah']['estimate'])}; WA outback left out: {s1(c2['without_outback']['estimate'])}."
            ),
        ),
        outcome(
            "general-retail-turnover",
            "Turnover of supermarkets, clothing and department stores",
            "productivity",
            "primary",
            LOG,
            a,
            a_basis,
            a_inf,
            baseline=turnover_base,
            baseline_label="WA turnover of these stores, $m a month, 2009-10",
            finding=a["finding"],
            grade="Moderate",
            note="WA against NSW, Victoria, Queensland and the ACT, monthly, seasonally adjusted. " + fragile,
        ),
        outcome(
            "supermarket-turnover",
            "Supermarket and grocery turnover",
            "productivity",
            "secondary",
            LOG,
            a2["only_RT01"],
            a_basis,
            a_inf,
            finding="increase"
            if a2["only_RT01"]["p"] < 0.10 and a2["only_RT01"]["estimate"] > 0
            else ("decrease" if a2["only_RT01"]["p"] < 0.10 else "no-detectable-effect"),
        ),
        outcome(
            "general-retail-hours",
            "Hours worked in supermarkets, clothing and department stores",
            "productivity",
            "descriptive",
            LOG,
            b["hours"],
            f"90% range of {b['hours']['null']['n']} fake-date and comparison-state estimates",
            "Rank among fake-date and comparison-state estimates (two-sided)",
            finding="descriptive-only",
            note=(
                "Descriptive only: WA failed the fake-date test at the design stage (estimate "
                f"{s1(d['B_hours']['wa_fake_date_test']['estimate'])} at a fake date in Oct 2008, p = "
                f"{fp(d['B_hours']['wa_fake_date_test']['p'])}). Employment: {s1(b['employment']['estimate'])}."
            ),
        ),
    ]
    supermarket_share = a2["supermarket_share"]
    outcomes.append(
        {
            "id": "supermarket-share-of-food",
            "label": "Supermarkets relative to specialised food stores (turnover)",
            "category": "competition",
            "role": "secondary",
            "unit": LOG,
            "estimate": supermarket_share["estimate"],
            "no_effect_range": no_effect(supermarket_share, a_basis),
            "p_value": supermarket_share["p"],
            "inference": a_inf,
            "mde_80": supermarket_share["null"]["mde_80"],
            "finding": "no-detectable-effect" if supermarket_share["p"] >= 0.10 else "increase",
            "preregistered": True,
            "note": "Too noisy to be informative: the smallest detectable effect is about 55%.",
        }
    )
    reform_c = -1 + 4 / 12  # 1 Nov 2010, between June 2010 (k = -1) and June 2011 (k = 0)
    ev = {
        "id": EV_ID,
        "title": "Perth 9pm weeknight trading (2010), re-evaluated with new data",
        "records": ["wa-trading-hours-weeknight-2010"],
        "family": "retail-trading-hours",
        "follows": "wa-trading-hours-2010-2012",
        "evaluated_on": dt.date(2026, 10, 18).isoformat(),
        "hypothesis": "enhancing",
        "design": (
            "Difference-in-differences with one treated state, on data the first evaluation did not use: retail "
            "business counts by place (metropolitan Perth against regional WA, retail against other industries, "
            "set against the same capital-versus-regional contrast in other states), monthly turnover of the "
            "general retail shops covered (WA against other states), and hours worked (descriptive)."
        ),
        "comparison": (
            "Business counts: regional WA and capital-vs-rest gaps in NSW, Victoria, Queensland, Tasmania and the NT. "
            "Turnover: NSW, Victoria, Queensland and the ACT. SA excluded (Adelaide trading change in 2012)."
        ),
        "window": (
            "Weeknight trading only: November 2010 to mid-2012, before Sunday trading began (26 Aug 2012). Business "
            "counts at 30 June 2009-2012; turnover monthly, July 2008 to July 2012."
        ),
        "verdict": "inconclusive",
        "finding_label": "No detectable effect",
        "grade": "Moderate",
        "grade_reason": (
            "One treated state caps the grade at Moderate. The plan's design checks pass for both primary outcomes and "
            "the business-count result holds in every robustness check; the turnover result does not (see caveats)."
        ),
        "headline": (
            f"Letting Perth's general retail shops open until 9pm on weeknights (November 2010) made no detectable "
            f"difference to the number of retail businesses in Perth compared with regional WA "
            f"({s1(c['estimate'])} log points, 90% interval {s1(c['interval_90'][0])} to {s1(c['interval_90'][1])}) or "
            f"to the turnover of supermarkets, clothing and department stores ({s1(a['estimate'])}%, "
            f"{s1(a['interval_90'][0])} to {s1(a['interval_90'][1])}). Effects of about 10% or more in either can be "
            f"ruled out; smaller ones cannot."
        ),
        "category_summaries": {
            "competition": (
                f"No detectable change in the number of retail businesses. Metropolitan Perth's retail business count "
                f"moved {s1(c['estimate'])} log points relative to regional WA and other industries (p = "
                f"{fp(c['p'])}); small businesses alone {s1(c2['small_businesses']['estimate'])}."
            ),
            "productivity": (
                f"No detectable change in sales, and the result is fragile. Turnover of the stores covered: "
                f"{s1(a['estimate'])}% (p = {fp(a['p'])}). Hours worked are descriptive only: "
                f"{s1(b['hours']['estimate'])}%."
            ),
            "prices": (
                "Not re-estimated. The first evaluation's food-price estimate reflected a trend that began before "
                "the reform."
            ),
        },
        "preregistered": True,
        "outcomes": outcomes,
        "event_studies": [
            {
                "outcome": "retail-businesses-perth",
                "title": "Retail businesses, Perth relative to regional WA",
                "unit": GAP,
                "reference": "June 2010",
                "band": "90% range across placebo industries and states",
                "points": points(c["event_study"]),
                "markers": [{"k": reform_c, "label": "9pm weeknights (1 Nov 2010)"}],
                "caption": "Counts at 30 June each year; Sunday trading began after June 2012.",
            },
            {
                "outcome": "general-retail-turnover",
                "title": "Turnover of supermarkets, clothing and department stores, WA vs other states",
                "unit": LOG,
                "reference": "Apr-Jun 2010",
                "band": "90% range across fake dates and comparison states",
                "points": points(a["event_study"], dt.date(2010, 11, 1), dt.date(2010, 6, 1)),
                "markers": [{"k": -0.5, "label": "9pm weeknights (1 Nov 2010)"}],
                "caption": (
                    "Three-month bins, each labelled by its first month, from Jul 2008 to Jul 2012; Jul-Oct 2010 "
                    "(special trading precincts) left out."
                ),
            },
            {
                "outcome": "general-retail-hours",
                "title": "Hours worked in the same stores (descriptive)",
                "unit": LOG,
                "reference": "May 2010",
                "band": "90% range across fake dates and comparison states",
                "points": points(b["hours"]["event_study"]),
                "markers": [{"k": -0.5, "label": "9pm weeknights (1 Nov 2010)"}],
                "caption": "Mid-quarter months; WA's hours swung widely before the reform, so no finding is drawn.",
            },
        ],
        "caveats": [
            fragile,
            "With one treated state, effects smaller than about 10% cannot be told apart from what happens without a "
            "reform.",
            "Business counts are a proxy for competition: they show neither prices nor market shares, and only reach "
            "June 2012.",
            "The turnover estimate does not net out WA-specific demand (the mining boom); the variant that does is the "
            "food-services comparison above.",
            "Choices made at the design stage on hidden outcomes are listed in the plan (section 7), including "
            "outcomes dropped for lack of data (business exits inferred from names) or failed checks (hours).",
        ],
        "documents": [
            {"label": "Results", "path": "docs/results_wa_weeknight_2010.md"},
            {"label": "Pre-analysis plan", "path": "docs/pap_wa_weeknight_2010.md"},
            {"label": "Design review (blinded)", "path": "alcia/analyses/wa_weeknight_2010/design.json"},
            {"label": "Estimation code", "path": "alcia/analyses/wa_weeknight_2010/estimate.py"},
            {"label": "Earlier evaluation", "path": "docs/results_wa_trading_hours.md"},
        ],
        "built_by": "alcia/analyses/wa_weeknight_2010/evaluation.py",
    }
    path = write_evaluation(Evaluation.model_validate(ev))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
