"""Write the register's evaluation files for the high-evaluability batch from estimate.json.

Every number comes from estimate.json (the registered run); only the wording is written here, and
tests/test_evaluation.py checks the files against the outputs. Readings made after unblinding are
marked as such in the text (see docs/results_high_evaluability.md and the plan's section 11).

Run: uv run python analyses/high_evaluability/evaluations.py
Writes: regulation-register/evaluations/<case id>.json
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from cases import CASES, Case

from alcia.register.evaluation import Evaluation, write_evaluation

HERE = Path(__file__).resolve().parent
PER_100 = "per 100 businesses a year"
LOG_POINTS = "% (log points)"
DOCS = [
    {"label": "Results", "path": "docs/results_high_evaluability.md"},
    {"label": "Pre-analysis plan", "path": "docs/pap_high_evaluability.md"},
    {"label": "Case definitions", "path": "alcia/analyses/high_evaluability/cases.py"},
    {"label": "Estimation code", "path": "alcia/analyses/high_evaluability/run.py"},
]
DIVISION_NAMES = {
    "C": "manufacturing",
    "D": "electricity, gas, water and waste services",
    "I": "transport, postal and warehousing",
    "M": "professional, scientific and technical services",
    "Q": "health care and social assistance",
}


def s1(v: float | None) -> str:
    """Signed, one decimal, true minus."""
    return "n/a" if v is None else f"{v:+.1f}".replace("-", "−")


def fp(p: float | None) -> str:
    return "n/a" if p is None else ("< 0.01" if p < 0.01 else f"{p:.2f}")


def fy(year: int) -> str:
    return f"{year - 1}-{str(year)[2:]}"


def no_effect(res: dict, basis: str) -> dict:
    """The centred placebo range (5th to 95th percentile), from the estimate and its 90% interval."""
    lo, hi = res["interval_90"]
    d = res["estimate"]
    return {"low": round(d - hi, 3), "high": round(d - lo, 3), "basis": basis}


def finding(res: dict) -> str:
    if res["p"] is not None and res["p"] < 0.05:
        return "increase" if res["estimate"] > 0 else "decrease"
    return "no-detectable-effect"


def business_outcome(r: dict, case: Case, measure: str, grade: str) -> dict | None:
    e = r[measure]
    if not e:
        return None
    m = e["main"]
    word = "entry" if measure == "entries" else "exit"
    not_identified = grade == "Not identified"
    return {
        "id": f"{word}-rate",
        "label": f"Business {word} rate",
        "category": "competition",
        "role": "primary" if measure == "entries" else "secondary",
        "unit": PER_100,
        "estimate": m["estimate"],
        "interval": {"low": m["interval_90"][0], "high": m["interval_90"][1], "level": 0.9},
        "no_effect_range": no_effect(m, f"90% range across {m['placebos']} placebo industry groups"),
        "p_value": m["p"],
        "inference": "Rank among placebo industry groups (two-sided)",
        "mde_80": m["mde_80"],
        "finding": "not-identified" if not_identified else finding(m),
        "grade": grade,
        "preregistered": True,
        "note": (
            f"Net of a change of {s1(m['placebo_mean'])} per 100 in unaffected industries in the same states. "
            f"Plain comparison: {s1(m['plain'])}."
            + (" Not identified: the states diverged before the reform." if not_identified else "")
        ),
    }


def price_outcomes(r: dict, case: Case, judgements: dict) -> list[dict]:
    pr = r["prices"]
    if not pr:
        return []
    out = []
    for code, v in pr["classes"].items():
        slug = v["name"].lower().split(",")[0].replace(" ", "-")
        base = {
            "category": "prices",
            "role": "descriptive" if pr["role"] == "descriptive" else "secondary",
            "unit": LOG_POINTS,
            "inference": f"Rank among {v['placebos']} placebo CPI classes in the same cities",
            "preregistered": True,
        }
        fnd = "descriptive-only" if pr["role"] == "descriptive" else judgements.get(code, finding(v))
        out.append(
            base
            | {
                "id": f"price-{slug}",
                "label": f"{v['name']}: prices relative to the CPI",
                "estimate": v["estimate"],
                "interval": {"low": v["interval_90"][0], "high": v["interval_90"][1], "level": 0.9},
                "no_effect_range": no_effect(v, f"90% range across {v['placebos']} placebo CPI classes"),
                "p_value": v["p"],
                "mde_80": v["mde_80"],
                "finding": fnd,
                "grade": "Not identified" if fnd == "not-identified" else None,
                "note": f"Expected {pr['expected']}. Plain estimate {s1(v['plain'])}."
                + (" The not-identified reading was made after unblinding." if fnd == "not-identified" else ""),
            }
        )
        d = v["detrended"]
        if d["estimate"] is not None:
            out.append(
                base
                | {
                    "id": f"price-{slug}-detrended",
                    "label": f"{v['name']}: each city's pre-reform trend removed",
                    "estimate": d["estimate"],
                    "interval": {"low": d["interval_90"][0], "high": d["interval_90"][1], "level": 0.9},
                    "no_effect_range": no_effect(d, f"90% range across {v['placebos']} placebo CPI classes"),
                    "p_value": d["p"],
                    "finding": "descriptive-only" if pr["role"] == "descriptive" else finding(d),
                    "note": "Registered robustness check (decision E-31).",
                }
            )
    return out


def productivity_outcomes(r: dict, case: Case) -> list[dict]:
    out = []
    for var, v in r["productivity"].items():
        if v["estimate"] is None:
            continue
        label = "Output per worker" if var == "gva_per_worker" else "Real pay per worker"
        out.append(
            {
                "id": "output-per-worker" if var == "gva_per_worker" else "real-pay-per-worker",
                "label": f"{label}, {DIVISION_NAMES.get(case.division, case.division)}",
                "category": "productivity",
                "role": "descriptive",
                "unit": LOG_POINTS,
                "estimate": v["estimate"],
                "no_effect_range": no_effect(v, f"90% range across {v['placebos']} other industry divisions"),
                "p_value": v["p"],
                "inference": "Rank among the other industry divisions in the same states",
                "finding": "descriptive-only",
                "preregistered": True,
                "note": "Division-level data dilute the reform's industry; descriptive only.",
            }
        )
    return out


def event_studies(r: dict, case: Case) -> list[dict]:
    single = len(case.cohorts) == 1
    first = case.cohorts[0].first_post
    period = (lambda k: fy(first + k)) if single else (lambda k: f"year {k:+d}".replace("-", "−"))
    reference = fy(first - 1) if single else "the year before adoption"
    marker = [{"k": -0.5, "label": "Reform" if single else "Adoption"}]
    out = []
    for measure, oid, title in (
        ("entries", "entry-rate", "Business entries"),
        ("exits", "exit-rate", "Business exits"),
    ):
        e = r[measure]
        if not e:
            continue
        ks = sorted(int(k) for k in e["event"]["net"]) + [-1]
        pts = []
        for k in sorted(set(ks)):
            if k == -1:
                pts.append({"period": period(k), "k": k, "estimate": 0.0, "low": None, "high": None})
            else:
                lo, hi = e["event"]["band_90"][str(k)]
                pts.append({"period": period(k), "k": k, "estimate": e["event"]["net"][str(k)], "low": lo, "high": hi})
        out.append(
            {
                "outcome": oid,
                "title": f"{title}, year by year",
                "unit": PER_100,
                "reference": reference,
                "band": "90% range across placebo industry groups",
                "points": pts,
                "markers": marker,
                "caption": "Treated states relative to comparison states, net of unaffected industries"
                + ("." if single else "; years counted from each state's adoption."),
            }
        )
    if r["prices"]:
        code, v = next(iter(r["prices"]["classes"].items()))
        slug = v["name"].lower().split(",")[0].replace(" ", "-")
        pts = [{"period": period(-1), "k": -1, "estimate": 0.0, "low": None, "high": None}]
        for k, val in v["event_net"].items():
            lo, hi = v["event_band_90"][k]
            pts.append({"period": period(int(k)), "k": int(k), "estimate": val, "low": lo, "high": hi})
        pts.sort(key=lambda p: p["k"])
        out.append(
            {
                "outcome": f"price-{slug}",
                "title": f"{v['name']} prices, year by year",
                "unit": LOG_POINTS,
                "reference": reference,
                "band": "90% range across placebo CPI classes",
                "points": pts,
                "markers": marker,
                "caption": "Financial-year averages, relative to the all-groups CPI, treated cities against "
                "comparison cities, net of other CPI classes.",
            }
        )
    return out


def text(case: Case, r: dict) -> dict:
    """Wording per case. Numbers are filled in from the results."""
    e, x = r["entries"], r["exits"]
    em, xm = (e["main"] if e else None), (x["main"] if x else None)
    pr = r["prices"]["classes"] if r["prices"] else {}
    prod = r["productivity"]
    gva = prod["gva_per_worker"]["estimate"]

    def iv(m):
        return f"90% interval {s1(m['interval_90'][0])} to {s1(m['interval_90'][1])}"

    if case.id == "nt-container-deposits-2012":
        sd, beer = pr["115520"], pr["40087"]
        return {
            "finding_label": "Not measurable",
            "headline": "Too few NT businesses make beverages or recover materials (12 in 2010-11) to measure "
            "entry or exit. Darwin soft-drink prices rose "
            f"{s1(sd['estimate'])}% relative to other capitals (p = {fp(sd['p'])}), but they were "
            "already rising before the scheme; with each city's trend removed the change is "
            f"{s1(sd['detrended']['estimate'])}%.",
            "category_summaries": {
                "competition": "Not measurable. The NT has too few beverage manufacturers and recyclers for "
                "business counts to show an effect.",
                "prices": f"No detectable effect. Soft drinks {s1(sd['estimate'])}%, beer {s1(beer['estimate'])}%; "
                "neither stands out from other prices, and the soft-drink rise began before the scheme.",
                "productivity": "Not measurable. Manufacturing output per worker varies too much across "
                "industries. Shown for description only.",
            },
            "caveats": [
                "Business counts: 12 treated businesses in the base year, below the plan's minimum of 100, so no "
                "entry or exit estimate is made.",
                "Prices: a 10-cent deposit is a few per cent of a drink's price, well below the smallest effect "
                f"these data can detect ({sd['mde_80']:.0f}%).",
            ],
        }
    if case.id == "childcare-nqf-2012":
        return {
            "finding_label": "No detectable effect",
            "headline": "In 2011-12, the framework's first year, childcare business entry in the states that "
            f"had it changed by {s1(em['estimate'])} per 100 relative to WA, which started seven months later "
            f"({iv(em)}); exits by {s1(xm['estimate'])} ({iv(xm)}). Neither is distinguishable from zero.",
            "category_summaries": {
                "competition": "No detectable first-year effect on entry or exit. With one comparison state, "
                f"only effects above about {em['mde_80']:.0f} per 100 could have been detected.",
                "prices": "Descriptive only. Childcare fees move with subsidies, and only two quarters separate "
                "the states.",
                "productivity": "Not measurable. Childcare is a small part of health care and social "
                "assistance. Shown for description only.",
            },
            "caveats": [
                "Only the first year can be compared: WA adopted the same framework in August 2012.",
                "WA is the only comparison state; its mining boom is netted out using unaffected WA industries.",
            ],
        }
    if case.id == "retail-energy-deregulation-2013-2016":
        el = pr["40055"]
        return {
            "finding_label": "Not measurable",
            "headline": "Business counts cannot measure this reform: the three states had 59 electricity "
            "retailers in the base year, each counted in its head-office state. Electricity prices in the "
            f"deregulating states rose {s1(el['estimate'])}% relative to the regulated states (p = {fp(el['p'])}), "
            "but they had been rising faster for more than a decade before; with each city's trend removed "
            f"the change is {s1(el['detrended']['estimate'])}% (p = {fp(el['detrended']['p'])}).",
            "category_summaries": {
                "competition": "Not measurable with business counts: too few retailers, each placed at its "
                "head office.",
                "prices": "No effect identified. The registered estimate continues a long pre-existing rise "
                "(network charges); with trends removed it is close to zero.",
                "productivity": "Not measurable at division level. Shown for description only.",
            },
            "caveats": [
                "The price grade (Not identified) is a judgement made after unblinding, based on the registered "
                "detrended check and the year-by-year path.",
                "The carbon price (2012-14) applied in every state; network charges and the 2016-17 wholesale "
                "price spike did not.",
                "Prices stop at June 2019, before the default market offer re-regulated standing offers.",
            ],
        }
    if case.id == "heavy-vehicle-national-law-2014":
        return {
            "finding_label": "No detectable effect",
            "headline": "Road freight business entry in the six jurisdictions that adopted the Heavy Vehicle "
            f"National Law changed by {s1(em['estimate'])} per 100 a year relative to WA and the NT, net of "
            f"other industries ({iv(em)}); exits by {s1(xm['estimate'])} ({iv(xm)}). Neither is "
            "distinguishable from zero.",
            "category_summaries": {
                "competition": "No detectable effect on entry or exit. A rise in entry of more than about "
                f"{em['interval_90'][1]:.1f} per 100 is ruled out, if road freight would otherwise have tracked "
                "WA and the NT; a fall is not.",
                "productivity": f"Not measurable. Transport output per worker fell {s1(gva)}% relative to WA and "
                "the NT, far more than a freight law could plausibly cause; it most likely reflects the "
                "resources boom there. Shown for description only.",
            },
            "caveats": [
                "WA and the NT are the only comparison jurisdictions, and both rode the resources cycle. "
                "Unaffected industries in the same states net out the common part of that cycle.",
                "The pre-reform years pass the check, but the largest pre-reform gap (2010-11) is "
                f"{e['event']['net']['-3']:+.1f} per 100.",
            ],
        }
    if case.id == "vic-taxi-licensing-2014":
        fare = pr["40086"]
        return {
            "finding_label": "No detectable effect",
            "headline": "In 2014-15, the first year of as-of-right taxi licences, entry into Victorian taxi "
            f"and road transport changed by {s1(em['estimate'])} per 100 relative to other states "
            f"({iv(em)}); exits by {s1(xm['estimate'])}. Neither is distinguishable from zero. Unlicensed "
            "UberX arrived in Melbourne the same year.",
            "category_summaries": {
                "competition": "No detectable first-year effect. A rise in entry of more than about "
                f"{em['interval_90'][1]:.1f} per 100 in 2014-15 is ruled out.",
                "prices": f"Descriptive only. Melbourne urban transport fares fell {s1(fare['estimate'])}% "
                "relative to other capitals, most likely because of public transport fare changes from "
                "January 2015, not taxis.",
                "productivity": "Not measurable at division level. Shown for description only.",
            },
            "caveats": [
                "Only 2014-15 is usable: ride-share legalisation and driver GST registration followed.",
                "The fare reading (public transport changes from January 2015, including the free CBD tram "
                "zone) was made after unblinding.",
            ],
        }
    if case.id == "legal-profession-uniform-law-2015":
        return {
            "finding_label": "No detectable effect",
            "headline": "Legal services business entry in NSW and Victoria changed by "
            f"{s1(em['estimate'])} per 100 a year in the three years after the Uniform Law, relative to other "
            f"states and net of other industries ({iv(em)}); exits by {s1(xm['estimate'])} ({iv(xm)}). "
            "Neither is distinguishable from zero.",
            "category_summaries": {
                "competition": "No detectable effect. Exit changes beyond about "
                f"{max(abs(xm['interval_90'][0]), abs(xm['interval_90'][1])):.0f} per 100 are ruled out; for "
                f"entry, a rise of more than about {em['interval_90'][1]:.1f} per 100 is ruled out, a fall is not.",
                "productivity": "Not measurable. Legal services are a small part of professional services. "
                "Shown for description only.",
            },
            "caveats": [
                "Three post-reform years (2015-16 to 2017-18); later years overlap COVID.",
                "The Uniform Law mainly lowers costs for firms practising in both states, which business "
                "counts by main state cannot see directly.",
            ],
        }
    if case.id == "rideshare-legalisation-2015-2018":
        return {
            "finding_label": "Not identified",
            "headline": "Not identified. Taxi and road-transport entry in the legalising states was already "
            "far above the comparison states in the years before legalisation, so the comparison fails its "
            "pre-reform check. Ride-sharing also ran before it was legal, and drivers had to register for GST "
            "from August 2015 wherever it ran.",
            "category_summaries": {
                "competition": "Not identified: the states diverged before legalisation, so no estimate is headlined.",
                "prices": "Descriptive only. Urban transport fares are mostly public transport.",
                "productivity": "Not measurable at division level. Shown for description only.",
            },
            "caveats": [
                "Legal dates are not the economic dates: Uber operated in most capitals before legalisation.",
                "Estimates are shown for transparency but are not graded as findings.",
            ],
        }
    raise KeyError(case.id)


def build(case: Case, r: dict) -> dict:
    t = text(case, r)
    grade = r["grade"]
    judgements = {"40055": "not-identified"} if case.id == "retail-energy-deregulation-2013-2016" else {}
    outcomes = [
        o
        for o in (business_outcome(r, case, "entries", grade), business_outcome(r, case, "exits", grade))
        if o is not None
    ]
    outcomes += price_outcomes(r, case, judgements) + productivity_outcomes(r, case)
    tr = sorted({s for c in case.cohorts for s in c.treated})
    ctl = sorted({s for c in case.cohorts for s in c.controls})
    first = min(c.first_post for c in case.cohorts)
    last = max(c.last_post for c in case.cohorts)
    reasons = r["grade_reasons"]
    grade_reason = (
        " ".join(x[0].upper() + x[1:].rstrip(".") + "." for x in reasons)
        if reasons
        else (
            "Passes the plan's pre-reform check and robustness variants; one or few treated states, so only large "
            "effects are detectable."
        )
    )
    return {
        "id": case.id,
        "title": case.title,
        "records": list(case.records),
        "family": case.family,
        "evaluated_on": dt.date(2026, 10, 15).isoformat(),
        "hypothesis": case.hypothesis,
        "design": f"{case.design} Method: stacked difference-in-differences, net of the same comparison for "
        "unaffected industries in the same states.",
        "comparison": f"Treated: {', '.join(tr)}. Comparison: {', '.join(ctl)}.",
        "window": f"{fy(case.start)} to {fy(last)} (first exposed year {fy(first)})",
        # Plan section 7: a not-identified case has no headline verdict.
        "verdict": "not-identified" if grade == "Not identified" else r["verdict"],
        "finding_label": t["finding_label"],
        "grade": grade,
        "grade_reason": grade_reason,
        "headline": t["headline"],
        "category_summaries": t["category_summaries"],
        "preregistered": True,
        "outcomes": outcomes,
        "event_studies": event_studies(r, case),
        "caveats": t["caveats"],
        "documents": DOCS,
        "built_by": "alcia/analyses/high_evaluability/evaluations.py",
    }


def main() -> None:
    est = json.loads((HERE / "estimate.json").read_text(encoding="utf-8"))
    results = {r["id"]: r for r in est["cases"]}
    for case in CASES:
        path = write_evaluation(Evaluation.model_validate(build(case, results[case.id])))
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
