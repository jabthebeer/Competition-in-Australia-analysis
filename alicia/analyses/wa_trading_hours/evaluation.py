"""Write the register's evaluation file for the trading-hours case from the analysis outputs.

Every number comes from estimate.json (the registered run) or posthoc.json (checks labelled
not pre-registered); only the wording is written here. tests/test_evaluation.py checks the
file against both.

Run: uv run python analyses/wa_trading_hours/evaluation.py
Writes: regulation-register/evaluations/wa-trading-hours-2010-2012.json
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from alicia.register.evaluation import Evaluation, write_evaluation

HERE = Path(__file__).resolve().parent
PER_100 = "per 100 businesses a year"
LOG_POINTS = "% (log points)"
MARKERS = [{"k": -0.5, "label": "Weeknights"}, {"k": 1.5, "label": "Sundays"}]  # start of first exposed years


def signed(v: float) -> str:
    """One decimal with a sign and a true minus: +0.8, \u22122.4."""
    return f"{v:+.1f}".replace("-", "\u2212")


def fy(year: int) -> str:
    """Financial year named by its ending year: 2011 -> '2010-11'."""
    return f"{year - 1}-{str(year)[2:]}"


def placebo_range(placebos: dict, basis: str) -> dict:
    values = list(placebos.values())
    return {"low": min(values), "high": max(values), "basis": basis}


def competition_outcome(est: dict, measure: str, label: str, role: str) -> dict:
    e = est[measure]
    p = e["primary"]
    d, (lo, hi) = p["delta"], p["interval_90"]
    word = "entry" if measure == "entries" else "exit"
    return {
        "id": f"{word}-rate",
        "label": label,
        "category": "competition",
        "role": role,
        "unit": PER_100,
        "baseline": e["raw_means"]["wa_pre"],
        "baseline_label": "WA rate before the reform (2007-08 to 2009-10)",
        "estimate": d,
        "interval": {"low": lo, "high": hi, "level": 0.9},
        # The placebo distribution centred on zero: estimate minus the interval's ends.
        "no_effect_range": {
            "low": round(d - hi, 3),
            "high": round(d - lo, 3),
            "basis": f"90% range across {p['placebo_groups']} placebo groups of unaffected WA industries",
        },
        "p_value": p["p_industry_placebo"],
        "inference": "Rank among placebo industry groups (two-sided)",
        "mde_80": p["mde_80pc"],
        "finding": "no-detectable-effect" if p["p_industry_placebo"] >= 0.05 else ("increase" if d > 0 else "decrease"),
        "grade": e["grade"]["grade"],
        "preregistered": True,
        "note": (
            f"Net of a WA-wide change of {signed(p['wa_wide_shock_placebo_mean'])} per 100 in unaffected WA "
            f"industries. Plain WA-versus-states comparison: {signed(p['delta_T_plain_did'])}; "
            f"triple difference: {signed(e['triple_difference']['estimate'])}."
        ),
    }


def event_study(est: dict, measure: str, title: str) -> dict:
    ev = est[measure]["event_study"]
    points = []
    for k in range(-3, 8):
        if k == -1:
            points.append({"period": fy(2011 + k), "k": k, "estimate": 0.0, "low": None, "high": None})
            continue
        lo, hi = ev["net_band_90"][str(k)]
        points.append({"period": fy(2011 + k), "k": k, "estimate": ev["net"][str(k)], "low": lo, "high": hi})
    return {
        "outcome": "entry-rate" if measure == "entries" else "exit-rate",
        "title": title,
        "unit": PER_100,
        "reference": "2009-10",
        "band": "90% range across placebo industry groups",
        "points": points,
        "markers": MARKERS,
        "caption": "WA general retail relative to comparison states, net of unaffected WA industries.",
    }


def build() -> dict:
    est = json.loads((HERE / "estimate.json").read_text(encoding="utf-8"))
    post = json.loads((HERE / "posthoc.json").read_text(encoding="utf-8"))
    entry = competition_outcome(est, "entries", "Business entry rate", "primary")
    exit_ = competition_outcome(est, "exits", "Business exit rate", "secondary")

    food = est["prices"]["Food and non-alcoholic beverages"]
    trend = post["food_price_trend_check"]
    gva = est["descriptive_productivity_and_pay"]["gva_per_worker"]
    pay = est["descriptive_productivity_and_pay"]["real_coe_per_worker"]
    shown = post["descriptive_placebos_for_display"]
    states = "Range across the 6 comparison states"
    capitals = "Range across the 6 comparison capitals"
    outcomes = [
        entry,
        exit_,
        {
            "id": "food-prices",
            "label": "Food prices, Perth vs other capitals",
            "category": "prices",
            "role": "secondary",
            "unit": LOG_POINTS,
            "estimate": food["estimate_log_points"],
            "no_effect_range": placebo_range(food["state_placebos"], capitals),
            "p_value": food["p_state_placebo"],
            "inference": "Rank among comparison capitals (smallest possible p is 0.14)",
            "mde_80": food["mde_80pc"],
            "finding": "not-identified",
            "grade": "Not identified",
            "preregistered": True,
            "note": (
                "Continues a fall that began before the reform: Perth's relative food price fell "
                f"{-trend['perth_gap_slope_before_log_points_per_year']:.2f} log points a year before it and "
                f"{-trend['perth_gap_slope_after_log_points_per_year']:.2f} after. The grade is a judgement made "
                "after unblinding."
            ),
        },
        {
            "id": "food-prices-detrended",
            "label": "Food prices, each city's pre-reform trend removed",
            "category": "prices",
            "role": "secondary",
            "unit": LOG_POINTS,
            "estimate": trend["after_removing_each_citys_pre_reform_trend"],
            "no_effect_range": placebo_range(trend["state_placebos_detrended"], capitals),
            "p_value": trend["p_state_placebo_detrended"],
            "inference": "Rank among comparison capitals",
            "finding": "no-detectable-effect",
            "preregistered": False,
            "note": "Not pre-registered: added after unblinding to test whether the fall was a trend.",
        },
        {
            "id": "output-per-worker",
            "label": "Retail output per worker",
            "category": "productivity",
            "role": "descriptive",
            "unit": LOG_POINTS,
            "estimate": gva["estimate_log_points"],
            "no_effect_range": placebo_range(shown["gva_per_worker"]["state_placebos"], states),
            "p_value": gva["p_state_placebo"],
            "inference": "Rank among comparison states",
            "finding": "descriptive-only",
            "preregistered": True,
            "note": f"Real value added per employed person, {gva['years']}. Not blind: see the results, section 7.",
        },
        {
            "id": "real-pay-per-worker",
            "label": "Retail real pay per worker",
            "category": "productivity",
            "role": "descriptive",
            "unit": LOG_POINTS,
            "estimate": pay["estimate_log_points"],
            "no_effect_range": placebo_range(shown["real_coe_per_worker"]["state_placebos"], states),
            "p_value": pay["p_state_placebo"],
            "inference": "Rank among comparison states",
            "finding": "descriptive-only",
            "preregistered": True,
            "note": f"Compensation of employees per employed person, deflated by each capital's CPI, {pay['years']}.",
        },
    ]

    gap = food["perth_gap_vs_other_capitals_by_fy_relative_to_2009_10"]
    food_points = [
        {"period": fy(int(y)), "k": int(y) - 2011, "estimate": v, "low": None, "high": None}
        for y, v in gap.items()
        if 2001 <= int(y) <= 2019  # full financial years only (the series runs 2000-Q1 to 2019-Q4)
    ]
    rm = est["entries"]["event_study"]["sensitivity_net"]["relative_magnitude_breakdown"]
    e, x = entry, exit_
    ev = {
        "id": "wa-trading-hours-2010-2012",
        "title": "Perth retail trading-hours deregulation (2010 and 2012)",
        "records": ["wa-trading-hours-weeknight-2010", "wa-trading-hours-sunday-2012"],
        "family": "retail-trading-hours",
        "evaluated_on": dt.date(2026, 10, 15).isoformat(),
        "hypothesis": "enhancing",
        "design": (
            "Difference-in-differences with one treated state: WA general retail (supermarkets, clothing and "
            f"department stores) against comparison states, net of the same comparison for "
            f"{est['entries']['primary']['placebo_groups']} groups of unaffected WA industries."
        ),
        "comparison": "NSW, Victoria, Queensland, Tasmania, ACT and NT (SA excluded: Adelaide trading change in 2012)",
        "window": f"{est['window']} (before COVID)",
        "verdict": "inconclusive" if est["entries"]["decision"]["verdict"] == "inconclusive" else "supports-enhancing",
        "finding_label": "No detectable effect",
        "grade": est["entries"]["grade"]["grade"],
        "grade_reason": (
            "One treated state and three pre-reform years, so parallel trends cannot be checked well. "
            "The plan's diagnostics pass, and every robustness variant stays inside the main interval."
        ),
        "headline": (
            "Perth's move to 9pm weeknight trading (November 2010) and Sunday trading (August 2012) had no detectable "
            "effect on how many general retail businesses started or closed. "
            f"Entry changed by {signed(e['estimate'])} per 100 businesses a year "
            f"(90% interval {signed(e['interval']['low'])} to {signed(e['interval']['high'])}), "
            f"exit by {signed(x['estimate'])} ({signed(x['interval']['low'])} to {signed(x['interval']['high'])})."
        ),
        "category_summaries": {
            "competition": "No detectable effect on business entry or exit. Large effects are ruled out if WA "
            "retail would otherwise have tracked other states.",
            "prices": "No effect identified. Perth's food prices fell relative to other capitals, but they were "
            "already falling before the reform.",
            "productivity": "Not measurable with public data. The spread across comparison states dwarfs any "
            "plausible effect, so these are shown for description only.",
        },
        "preregistered": True,
        "outcomes": outcomes,
        "event_studies": [
            event_study(est, "entries", "Business entries, year by year"),
            event_study(est, "exits", "Business exits, year by year"),
            {
                "outcome": "food-prices",
                "title": "Food prices: Perth vs other capitals",
                "unit": LOG_POINTS,
                "reference": "2009-10",
                "points": food_points,
                "markers": MARKERS,
                "caption": "Perth's food prices relative to its all-groups CPI, minus the same for the comparison "
                "capitals. The fall starts well before the reform.",
            },
        ],
        "caveats": [
            "The sign is fragile: a post-reform drift much smaller than the pre-reform year-to-year swings would "
            f"flip it (relative-magnitudes breakdown {rm:.2f}; below 1 means the swings are enough).",
            "The reform covered metropolitan Perth, but the data are for all of WA. A Perth-only effect would be "
            "about a quarter larger than measured.",
            "Business counts cannot show who gained. Longer hours may shift sales from small shops to large chains "
            "without changing the totals.",
            "Output per worker was seen once before the design review, so that reading is not blind.",
            "Both register records are drafts: dates verified against the WA register; industries and direction "
            "not yet reviewed by a person.",
        ],
        "documents": [
            {"label": "Results", "path": "docs/results_wa_trading_hours.md"},
            {"label": "Pre-analysis plan", "path": "docs/pap_wa_trading_hours.md"},
            {"label": "Design-stage review", "path": "docs/robustness_review_wa_trading_hours.md"},
            {"label": "Estimation code", "path": "alicia/analyses/wa_trading_hours/estimate.py"},
        ],
        "built_by": "alicia/analyses/wa_trading_hours/evaluation.py",
    }
    return ev


def main() -> None:
    path = write_evaluation(Evaluation.model_validate(build()))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
