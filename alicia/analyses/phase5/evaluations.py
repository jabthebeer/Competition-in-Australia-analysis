"""Write the register's evaluation files for a Phase 5 specification from its estimate.json.

Every number comes from estimate.json (the registered run), table_stats.json (sample sizes for the regression
tables), posthoc.json (checks made after unblinding, labelled as such) and, for re-evaluations, from the
evaluation each case supersedes; only the wording is written here. tests/test_evaluation.py checks the files against the
outputs. New results lead the key insights; the comparison with the earlier (archived) evaluation follows.

    uv run python analyses/phase5/evaluations.py --spec phase5-reevaluations
    uv run python analyses/phase5/evaluations.py --spec phase5-reevaluations --table   # results table (Markdown)

Writes regulation-register/evaluations/<case id>.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from alicia import anzsic, cpi
from alicia.register.evaluation import Evaluation, default_evaluations_dir, write_evaluation
from alicia.runner.spec import load

HERE = Path(__file__).resolve().parent
FOLDERS = {"phase5-reevaluations": "reevaluations", "phase5-new-families": "new_families"}
# When the registered runs were made (set after each run; orders evaluations made on the same day).
RUN_AT = {
    "phase5-reevaluations": dt.datetime(2026, 10, 18, 21, 4, 50, tzinfo=dt.UTC),
    "phase5-new-families": dt.datetime(2026, 10, 18, 21, 4, 29, tzinfo=dt.UTC),
}
PER_100 = "per 100 businesses a year"
LOG_POINTS = "% (log points)"
LAYER_LABELS = {
    "twoway": "Two-way fixed effects",
    "state_year": "Cell and state × year effects",
    "saturated": "Saturated fixed effects",
    "controls": "Two-way with measured state controls",
    "imputation": "Imputation (Borusyak, Jaravel and Spiess)",
    "sdid": "Synthetic DiD",
    "gsynth": "Generalised synthetic control",
}
VERDICT_LABELS = {
    "supports-enhancing": "Supports enhancing",
    "supports-weakening": "Supports weakening",
    "contradicts-enhancing": "Contradicts enhancing",
    "contradicts-weakening": "Contradicts weakening",
    "detects-increase": "Increase detected",
    "detects-decrease": "Decrease detected",
    "inconclusive": "No detectable effect",
    "not-identified": "Not identified",
}
QUESTIONS = {
    "wa-trading-hours-2010-2012-phase5": "did longer shop trading hours in Perth (weeknights from November 2010, "
    "Sundays "
    "from August 2012) change how many general retail businesses opened or closed?",
    "childcare-nqf-2012-phase5": "did the National Quality Framework for childcare change how many childcare "
    "businesses opened or closed in its first year (2011-12)?",
    "heavy-vehicle-national-law-2014-phase5": "did one national law for heavy vehicles (February 2014) change how "
    "many road freight businesses started or closed?",
    "vic-taxi-licensing-2014-phase5": "did Victoria's as-of-right taxi licences (2014) bring new taxi businesses in, "
    "or lower fares?",
    "legal-profession-uniform-law-2015-phase5": "did the Legal Profession Uniform Law (NSW and Victoria, July 2015) "
    "change how many legal practices opened or closed?",
    "rideshare-legalisation-2015-2018-phase5": "did legalising ride-sharing (2015 to 2018) change how many taxi and "
    "ride businesses started or closed, or fares?",
    "nt-container-deposits-2012-phase5": "did the Northern Territory's container deposit scheme (January 2012) change "
    "drink prices in Darwin?",
    "retail-energy-deregulation-2013-2016-phase5": "did removing retail electricity price caps (SA 2013, NSW 2014, "
    "south-east Queensland 2016) lower electricity prices?",
    "fuel-price-reporting-2016-2021": "did making fuel retailers report their prices in real time for publication "
    "(NSW 2016, NT 2017, Queensland 2018, Tasmania 2020, SA 2021) change fuel prices, or the number of fuel retailers?",
    "e-conveyancing-2018-2023": "did requiring property settlements to be lodged electronically (NSW 2018 to "
    "Queensland 2023) change how many legal and conveyancing practices opened or closed?",
}


def s1(v) -> str:
    return "n/a" if v is None else f"{v:+.1f}".replace("-", "−")


def a1(v) -> str:
    return "n/a" if v is None else f"{abs(v):.1f}"


def a2(v) -> str:
    return "" if v is None else f"{abs(v):.2f}"


def fp(p) -> str:
    if p is None:
        return "n/a"
    return "< 0.01" if p < 0.01 else f"{p:.3f}" if p < 0.1 else f"{p:.2f}"


def low1(text: str) -> str:
    """Lower-case the first letter only (keeps "CPI")."""
    return text[:1].lower() + text[1:]


def wu(v, unit: str) -> str:
    """A value with its unit: "−2.8% (log points)", "+1.0 per 100 businesses a year"."""
    return f"{s1(v)}{unit}" if unit.startswith("%") else f"{s1(v)} {unit}"


def fy(year: int) -> str:
    return f"{year - 1}-{str(year)[2:]}"


def reason_text(reason: str) -> str:
    """The run's grade reasons, with layer keys written out."""
    head = "check layers outside the registered 90% interval: "
    if reason.startswith(head):
        names = [LAYER_LABELS[k] for k in reason[len(head) :].split(", ")]
        return f"{' and '.join(names)} (a check layer) lies outside the registered layer's 90% interval"
    return reason


def why_not_strong(case: dict, prim: dict, reg: dict, params: dict) -> str:
    """Moderate rather than Strong: what the registered grade rule (run.py: judge) needed and this design has."""
    eoi = params["effect_of_interest"][prim["kind"]]
    states = {s for c in prim["cohorts"] for s in c["treated"]}
    n = len(prim["cohorts"])
    return (
        f"Moderate rather than Strong: the rule needs at least two cohorts, three treated states and a smallest "
        f"detectable effect within {eoi:g}; this design has {n} cohort{'s' if n > 1 else ''}, {len(states)} treated "
        f"state{'s' if len(states) > 1 else ''} and a smallest detectable effect of {a1(reg.get('mde_80'))}."
    )


def posthoc_reading(case_id: str, ph: dict | None) -> tuple[list[str], list[str]]:
    """Insight lines and caveats from posthoc.json (not pre-registered)."""
    if not ph or case_id != ph["vic_fares"]["case"]:
        return [], []
    v = ph["vic_fares"]
    taxi, cap = v["candidate_quarters"].values()
    insight = (
        "After unblinding (not pre-registered): the fall in Melbourne's urban transport fares came all at once in "
        f"{cap['quarter']} ({s1(cap['step'])} points in one quarter, about {abs(cap['step_in_sd']):.0f} times the "
        f"usual quarterly move), not when the taxi reform started ({taxi['quarter']}: {s1(taxi['step'])}). January "
        "2015 is "
        "when public transport fare changes were reported to start (zone 1+2 travel capped at the zone 1 fare; free "
        "CBD trams). The CPI class covers public transport fares as well as taxi fares, and a one-quarter step "
        "of this size looks like a fare-schedule change, not taxi competition building up; the fares result should "
        "not be read as an effect of the taxi reform."
    )
    caveat = (
        "Urban transport fares (secondary): the fall is confounded. It came in 2015-Q1, the quarter public transport "
        "fare changes were reported to start, not in 2014-Q3 (post-unblinding check, analyses/phase5/posthoc.py; "
        "the fare changes are taken from commentary written before them, not checked against PTV's fare tables)."
    )
    return [insight], [caveat]


def confounder_caveat(case: dict, scan: dict | None) -> list[str]:
    """One caveat from confounders.json (not pre-registered): overlapping register changes and series that moved
    most away from the reform period."""
    if not scan:
        return []
    c = next((x for x in scan["cases"] if x["id"] == case["id"]), None)
    if c is None:
        return []
    hits = [h for h in c["register"] if h["relevance"] != "low"]
    labels = {o["key"]: low1(outcome_label(o)) for o in case["outcomes"]}
    moved = [
        f"{labels[k]}, {r['state']}, {r['largest']['period']} ({s1(r['largest']['in_sd'])} × the usual step)"
        for k, rows in c["timing"].items()
        for r in rows
        if r.get("verdict") in ("largest move before the reform", "largest move after the reform period")
    ]
    reg = (
        "other register changes in the same states and industries: "
        + "; ".join(f"{h['title']} ({h['date']}, {h['where']}, {h['relevance']})" for h in hits[:4])
        + (f"; and {len(hits) - 4} more" if len(hits) > 4 else "")
        if hits
        else "no other register change of high or medium relevance"
    )
    when = (
        "the treated series moved most away from the reform period in: " + "; ".join(moved[:4])
        if moved
        else "no treated series moved most away from the reform period"
    )
    return [f"Confounder scan (not pre-registered; docs/confounder_scan.md): {reg}. Timing: {when}."]


def unit_of(o: dict) -> str:
    return LOG_POINTS if o["kind"] == "price" else PER_100


def outcome_id(o: dict) -> str:
    return o["key"] if o["kind"] == "price" else {"entries": "entry-rate", "exits": "exit-rate"}[o["key"]]


def outcome_label(o: dict) -> str:
    if o["kind"] == "price":
        name = next(c["name"] for c in cpi.classes() if c["code"] == o["code"])
        return f"{name}: prices relative to the CPI"
    return "Business entry rate" if o["key"] == "entries" else "Business exit rate"


def industries(o: dict) -> str:
    return ", ".join(f"{c} {anzsic.name(c)}" for c in o["classes"])


def finding(r: dict) -> str:
    if not r["feasible"]["ok"] or r.get("pre_inside_95") is False:
        return "not-identified"
    reg = r["registered"]
    if reg["p"] is not None and reg["p"] < 0.05:
        return "increase" if reg["estimate"] > 0 else "decrease"
    return "no-detectable-effect"


def interval(res: dict) -> dict | None:
    lo, hi = res["interval_90"]
    return None if lo is None else {"low": lo, "high": hi, "level": 0.9}


def outcome_result(o: dict, r: dict, grade: str | None, primary: bool) -> dict | None:
    reg = r.get("registered")
    if not reg or reg["estimate"] is None:
        return None
    lo, hi = reg["interval_90"]
    pool = "placebo CPI classes in the same cities" if o["kind"] == "price" else "placebo industry groups"
    checks = "; ".join(
        f"{LAYER_LABELS[k]} {s1(v['estimate'])}" + ("" if v["inside_registered_90"] else " (outside the 90% interval)")
        for k, v in r["checks"].items()
    )
    own = "; ".join(
        f"{fam.replace('_', ' and ')} p = {fp(v['p'])} ({v['draws']} draws)" for fam, v in r["own_class"].items()
    )
    what = industries(o) if o["kind"] == "business" else "capital cities"
    note = (
        f"Registered layer: {LAYER_LABELS[r['layer']]}. Net of a placebo mean of {s1(reg['placebo_mean'])}; plain "
        f"estimate {s1(reg['plain'])}. {what[0].upper() + what[1:]}."
        + (f" Checks: {checks}." if checks else "")
        + (f" Own-class placebos: {own}." if own else "")
        + (
            " Not identified: a pre-reform year lies outside its 95% placebo band."
            if r.get("pre_inside_95") is False
            else ""
        )
    )
    return {
        "id": outcome_id(o),
        "label": outcome_label(o),
        "category": "prices" if o["kind"] == "price" else "competition",
        "role": o["role"],
        "unit": unit_of(o),
        "baseline": r["mean"] if o["kind"] == "business" else None,
        "baseline_label": "Average rate in the panel" if o["kind"] == "business" else None,
        "estimate": reg["estimate"],
        "interval": interval(reg),
        "no_effect_range": {
            "low": round(reg["estimate"] - hi, 3),
            "high": round(reg["estimate"] - lo, 3),
            "basis": f"90% range across {reg['placebos']} {pool}",
        },
        "p_value": reg["p"],
        "inference": f"Rank among {reg['placebos']} {pool} (two-sided)",
        "mde_80": reg["mde_80"],
        "finding": finding(r),
        "grade": grade if primary else None,
        "preregistered": True,
        "note": note,
    }


def event_study(o: dict, r: dict) -> dict | None:
    ev = r.get("event") or {}
    pts = []
    single = len(o["cohorts"]) == 1
    for k, v in sorted(((int(k), v) for k, v in ev.items()), key=lambda kv: kv[0]):
        if v["net"] is None:
            continue
        if o["kind"] == "business" and single:
            label = fy(int(o["cohorts"][0]["first_post"]) + k)
        else:
            label = f"year {k:+d}" if k else "year 0"
        b = v["band_90"]
        pts.append(
            {"period": label, "k": k, "estimate": v["net"], "low": b[0] if b else None, "high": b[1] if b else None}
        )
    if len(pts) < 2:
        return None
    return {
        "outcome": outcome_id(o),
        "title": f"{outcome_label(o)}, year by year (saturated effects, net of placebos)",
        "unit": unit_of(o),
        "reference": "The year before the first exposed year (k = −1) is the reference",
        "band": "90% range of placebo estimates around each coefficient",
        "points": pts,
        "markers": [{"k": -0.5, "label": "Reform"}],
        "caption": "Coefficients from the event-study version of the saturated model, net of the mean placebo "
        "coefficient; years before −5 and after +5 are pooled at the ends.",
    }


def estimator_rows(o: dict, r: dict) -> list[dict]:
    rows = []
    for layer, res in (r.get("layers") or {}).items():
        rows.append(
            {
                "outcome": outcome_id(o),
                "layer": layer,
                "label": LAYER_LABELS[layer],
                "estimate": res["estimate"],
                "interval": interval(res),
                "p_value": res["p"],
                "mde_80": res["mde_80"],
                "registered": layer == r["layer"],
            }
        )
    return rows


# Regression table: one column per estimator layer, in the power study's order.
TABLE_COLUMNS = (
    ("twoway", "Two-way FE", "Fixed effects"),
    ("state_year", "State × period FE", "Fixed effects"),
    ("saturated", "Saturated FE", "Fixed effects"),
    ("controls", "Two-way + controls", "Fixed effects"),
    ("imputation", "Imputation", "Fixed effects"),
    ("sdid", "Synthetic DiD", "Synthetic comparison"),
    ("gsynth", "Generalised SC", "Synthetic comparison"),
)
TABLE_FOOTER = (
    ("Cell FE", "twoway state_year saturated controls imputation sdid gsynth"),
    ("Period FE", "twoway state_year saturated controls imputation sdid gsynth"),
    ("Class × period FE", "saturated imputation"),
    ("State × period FE", "state_year saturated imputation"),
    ("Measured state controls", "controls"),
    ("Synthetic weights", "sdid"),
    ("Interactive FE (factors)", "gsynth"),
)


def regression_table(spec_id: str, case: dict, res: dict, stats: dict, q_values: dict) -> dict:
    """The case's estimates in the usual academic layout: estimators across, one panel per outcome."""
    layers = [k for k, _, _ in TABLE_COLUMNS]
    only = lambda key, value: [value if k == key else None for k in layers]  # noqa: E731
    panels, samples = [], []
    for o in case["outcomes"]:
        r, st = res["outcomes"][o["key"]], stats.get(o["key"])
        if not r["feasible"]["ok"] or st is None:
            continue
        letter = "ABCDEFGH"[len(panels)]
        price = o["kind"] == "price"
        unit = "100 × log points" if price else PER_100
        coefs = [
            None
            if r["layers"][k]["estimate"] is None
            else {
                "estimate": r["layers"][k]["estimate"],
                "spread": r["layers"][k]["placebo_sd"],
                "p_value": r["layers"][k]["p"],
                "registered": k == o["layer"],
            }
            for k in layers
        ]
        rows = [
            {"label": "Reform × post (β)", "coefficients": coefs},
            {"label": "Observations", "values": [f"{st['layers'][k]['nobs']:,}" for k in layers]},
            {"label": "Units (cells)", "values": [f"{st['layers'][k]['units']:,}" for k in layers]},
            {
                "label": "Placebo groups",
                "values": [str(r["layers"][k]["placebos"]) for k in layers],
            },
            {"label": "MDE (80% power)", "values": [a2(r["layers"][k]["mde_80"]) for k in layers]},
        ]
        if not price:
            rows.append(
                {"label": "Pre-reform mean, treated", "values": [f"{st['pre_mean_treated']:.2f}"] * len(layers)}
            )
        pre = {True: "Pass", False: "Fail"}.get(r["pre_inside_95"])
        if pre:
            rows.append({"label": "Pre-trend test (k ≤ −2)", "values": only("saturated", pre)})
        q = q_values.get(f"{case['id']}:{o['key']}")
        if o["role"] == "primary" and q is not None:
            rows.append({"label": "BH q-value", "values": only(o["layer"], f"{q:.3f}")})
        cells = f"{st['treated_cells']} treated cell{'s' if st['treated_cells'] > 1 else ''}"
        panels.append(
            {"title": f"Panel {letter}. {outcome_label(o)}, {unit} ({o['role']} outcome; {cells})", "rows": rows}
        )
        what = (
            "100 × log of the CPI class relative to All groups, CPI class × capital city × quarter, unweighted"
            if price
            else "per 100 businesses operating at the start of the financial year, ANZSIC class × state, weighted "
            "by those businesses"
        )
        sample = (
            f"{what}; {st['periods'][0]} to {st['periods'][1]} ({st['n_periods']} periods), {st['classes']} "
            f"classes, {len(st['states'])} {'cities' if price else 'states'}."
        )
        samples.append((letter, "" if price else o["key"], sample))
    folder = FOLDERS[spec_id]
    merged: dict[str, list[tuple[str, str]]] = {}
    for letter, measure, sample in samples:
        merged.setdefault(sample, []).append((letter, measure))
    described = []
    for sample, items in merged.items():
        letters = [x[0] for x in items]
        head = f"Panel {letters[0]}" if len(letters) == 1 else f"Panels {', '.join(letters[:-1])} and {letters[-1]}"
        measures = " and ".join(x[1] for x in items if x[1])
        described.append(f"{head}: {measures + ' ' if measures else ''}{sample}")
    notes = [
        *described,
        "Each column applies one estimator to the same panel. β is the average effect on the reform's classes in "
        "treated states (cities) over the window, net of the mean of the same estimator across the placebo groups. "
        "Columns (6) and (7) compare the treated group's average with reweighted untreated cells over each "
        "cohort's window; their observations and units are summed over cohorts.",
        "The placebo standard deviation is the spread of the same estimator across up to 40 placebo industry "
        "groups (or CPI classes) given the reform's states and dates: the randomization-inference analogue of a "
        "standard error. p-values rank the estimate among the centred placebo estimates; with 40 placebos the "
        "smallest attainable is about 0.024, so *** cannot occur. Clustered standard errors are not reported: with "
        "seven or eight states they are unreliable, and the registered inference uses placebos.",
        "MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard "
        "deviation). Placebo groups: placebo industry groups (business outcomes) or CPI classes (prices). "
        "Pre-trend test: every event-study coefficient with k ≤ −2 (saturated model, net of the placebo mean) lies "
        "inside its 95% placebo band; a failure means the outcome is not identified. BH q-value: Benjamini–Hochberg "
        "across the specification's primary outcomes.",
        f"Source: alicia/analyses/phase5/{folder}/estimate.json (registered run, {RUN_AT[spec_id]:%d %B %Y}) and "
        "table_stats.json (samples, re-fitted to check every estimate reproduces).",
    ]
    return {
        "id": f"{case['id']}-estimators",
        "title": case["title"],
        "columns": [{"label": lab, "group": grp} for _, lab, grp in TABLE_COLUMNS],
        "panels": panels,
        "footer": [
            {"label": lab, "values": ["Yes" if k in on.split() else "No" for k in layers]} for lab, on in TABLE_FOOTER
        ],
        "spread_label": "Placebo standard deviation",
        "notes": notes,
    }


def method(case: dict, prim: dict) -> dict:
    price = prim["kind"] == "price"
    i, s, t = ("c", "j", "q") if price else ("c", "s", "t")
    sat = f"y_{{{i}{s}{t}}} = α_{{{i}{s}}} + δ_{{{i}{t}}} + γ_{{{s}{t}}} + β·D_{{{i}{s}{t}}} + ε_{{{i}{s}{t}}}"
    eqs = {
        "saturated": ("Saturated fixed effects", sat),
        "twoway": (
            "Two-way fixed effects",
            f"y_{{{i}{s}{t}}} = α_{{{i}{s}}} + λ_{{{t}}} + β·D_{{{i}{s}{t}}} + ε_{{{i}{s}{t}}}",
        ),
        "sdid": (
            "Synthetic DiD",
            "hat{τ} = arg min over (μ, α, β, τ) of Σ_{i,t} (y_{it} − μ − α_{i} − β_{t} − D_{it}·τ)^{2} "
            "· hat{ω}_{i} · hat{λ}_{t}",
        ),
    }
    label, text = eqs[prim["layer"]]
    terms = [
        {
            "symbol": f"y_{{{i}{s}{t}}}",
            "meaning": "100 × log of the CPI class relative to All groups in city j, quarter q"
            if price
            else "Entries (or exits) per 100 businesses operating at the start of year t, class c, state s",
        },
        {
            "symbol": f"D_{{{i}{s}{t}}}",
            "meaning": "1 for the reform's class in a treated state (or city) from its first exposed period to the "
            "end of its window",
        },
    ]
    if prim["layer"] == "saturated":
        terms += [
            {"symbol": f"α_{{{i}{s}}}", "meaning": "a level for each class in each state"},
            {
                "symbol": f"δ_{{{i}{t}}}",
                "meaning": "each class's national movement in each period (industry cycles, product-wide price swings)",
            },
            {"symbol": f"γ_{{{s}{t}}}", "meaning": "each state's movement in each period (state booms and slumps)"},
        ]
    elif prim["layer"] == "sdid":
        terms += [
            {
                "symbol": "hat{ω}_{i}",
                "meaning": "weights on comparison cells, chosen so their pre-reform path matches the treated group's",
            },
            {
                "symbol": "hat{λ}_{t}",
                "meaning": "weights on pre-reform periods, chosen to resemble the post-reform periods",
            },
        ]
    else:
        terms += [{"symbol": f"λ_{{{t}}}", "meaning": "a common movement in each period"}]
    return {
        "summary": f"{LAYER_LABELS[prim['layer']]} on "
        f"{'CPI classes by capital city and quarter' if price else 'ANZSIC classes by state and financial year'}, "
        "the layer chosen for this reform in the blinded power study, with every other layer reported side by side.",
        "equations": [
            {"label": label, "text": text},
            {
                "label": "Year by year",
                "text": f"y_{{{i}{s}{t}}} = α_{{{i}{s}}} + δ_{{{i}{t}}} + γ_{{{s}{t}}} "
                f"+ Σ_{{k≠−1}} β_{{k}}·1[{t} − T_{{{s}}} = k]·T_{{{i}{s}}} + ε_{{{i}{s}{t}}}",
            },
        ],
        "terms": terms,
        "estimand": "The average change in the outcome for the reform's classes in treated states over the window, "
        "beyond the same classes elsewhere and the treated states' other classes, net of the mean placebo estimate.",
        "identification": "Without the reform, the treated classes in treated states would have moved like the same "
        "classes elsewhere plus their states' other classes (parallel trends in the saturated model; for synthetic "
        "DiD, like the weighted comparison cells).",
        "inference": "The same estimator applied to up to 40 placebo industry groups (or CPI classes) at the "
        "reform's states and dates gives the no-effect distribution: the p-value is the share of centred placebo "
        "estimates at least as large; the 90% interval subtracts their 5th and 95th percentiles. Benjamini-Hochberg "
        "q-values across the specification's primary outcomes. Placebo states and fake dates check the reform's own "
        "classes.",
        "steps": [
            "Registered the layer, outcomes, windows and placebo pools in the specification before any treated "
            "post-reform outcome was computed.",
            "Design stage: hid treated cells from first exposure, computed every layer's placebo distribution, the "
            "own-class placebos and the pre-reform event-study check.",
            "Committed the design and plan, ran a blinded dry run, then one registered run with treated cells "
            "restored.",
            "Judged the registered layer's estimate against its placebo distribution; reported every other layer "
            "side by side.",
        ],
    }


OLD_FOUND = {
    "inconclusive": "no detectable effect",
    "not-identified": "that the effect could not be identified",
    "detects-increase": "an increase",
    "detects-decrease": "a decrease",
}


def compare(prim: dict, reg: dict, verdict: str, old: dict) -> str:
    """The new result against the archived evaluation it supersedes (same outcome where the earlier one had it)."""
    same = [x for x in old["outcomes"] if x["id"] == outcome_id(prim)]
    oo = (same or [x for x in old["outcomes"] if x["role"] == "primary"] or old["outcomes"])[0]
    found = OLD_FOUND.get(old["verdict"], low1(VERDICT_LABELS[old["verdict"]]))
    text = (
        f"Compared with the earlier evaluation ({old['evaluated_on']}, now archived): it found {found} "
        f"({low1(oo['label'])} {wu(oo['estimate'], oo['unit'])}). "
    )
    text += "The conclusion is unchanged" if verdict == old["verdict"] else "The conclusion has changed"
    if same and oo.get("mde_80") and reg.get("mde_80"):
        better = reg["mde_80"] < oo["mde_80"]
        text += (
            f"; the smallest detectable effect is now {a1(reg['mde_80'])}, "
            f"{'down' if better else 'up'} from {a1(oo['mde_80'])}"
        )
    return text + ". This evaluation uses the estimator chosen in the blinded power study and the latest data."


def insights(case: dict, res: dict, old: dict | None, ph: dict | None = None) -> list[str]:
    outs = res["outcomes"]
    prim = next(o for o in case["outcomes"] if o["role"] == "primary")
    pr = outs[prim["key"]]
    reg = pr.get("registered") or {}
    unit = " per 100 businesses a year" if prim["kind"] == "business" else "% relative to other prices"
    lines = [f"The question: {QUESTIONS[case['id']]}", f"The comparison: {case['design']}"]
    if res["verdict"] == "not-identified":
        why = reason_text(res["grade_reasons"][0]) if res["grade_reasons"] else "the design checks failed"
        drift = ", so the treated group was already moving apart before the reform" if pr["feasible"]["ok"] else ""
        est_ = f" The registered layer's estimate ({s1(reg['estimate'])}{unit}) is not an effect." if reg else ""
        lines.append(f"What we found: the effect cannot be identified: {why}{drift}.{est_}")
    else:
        found = "a change too large to be chance" if finding(pr) in ("increase", "decrease") else "no detectable change"
        lines.append(
            f"What we found: {found}. {outcome_label(prim)}: {s1(reg['estimate'])}{unit} (90% interval "
            f"{s1(reg['interval_90'][0])} to {s1(reg['interval_90'][1])}; p = {fp(reg['p'])})."
        )
    off = [(k, v) for k, v in pr["checks"].items() if v["inside_registered_90"] is False]
    if off and res["verdict"] != "not-identified":
        lines.append(
            "The estimators disagree: "
            + "; ".join(f"{low1(LAYER_LABELS[k])} gives {s1(v['estimate'])}" for k, v in off)
            + f", outside the registered layer's 90% interval, so the grade is {res['grade']}."
        )
    sec, flagged = [], False
    for o in case["outcomes"]:
        r = outs[o["key"]]
        g = r.get("registered") or {}
        if o is prim or g.get("estimate") is None:
            continue
        tail = ""
        if finding(r) == "not-identified":
            tail = "; not identified: a pre-reform year lies outside its placebo band"
        flagged |= finding(r) in ("increase", "decrease")
        sec.append(f"{low1(outcome_label(o))} {s1(g['estimate'])} (p = {fp(g['p'])}{tail})")
    if sec:
        lines.append(
            "Other outcomes: "
            + "; ".join(sec)
            + "."
            + (
                " Secondary outcomes are outside the registered decision rule and not adjusted for testing several "
                "outcomes, so a p-value below 0.05 among them is a lead, not a finding."
                if flagged
                else ""
            )
        )
    if reg.get("mde_80") is not None:
        lines.append(f"How precise: only changes larger than about {a1(reg['mde_80'])}{unit} could have been detected.")
    lines += posthoc_reading(case["id"], ph)[0]
    if old:
        lines.append(compare(prim, reg, res["verdict"], old))
    meaning = {
        "inconclusive": "What it means: no effect is detectable with public state-level data; an effect smaller than "
        "the detectable size cannot be ruled out.",
        "not-identified": "What it means: these data cannot separate the reform from what was already happening.",
    }.get(
        res["verdict"],
        "What it means: the registered decision rule detects an effect; see the in-depth section "
        "for its size, the checks and the caveats.",
    )
    lines.append(meaning)
    return lines


def build(spec_id: str) -> list[Evaluation]:
    spec = load(spec_id)
    est = json.loads((HERE / FOLDERS[spec_id] / "estimate.json").read_text("utf-8"))
    ph_path = HERE / FOLDERS[spec_id] / "posthoc.json"
    ph = json.loads(ph_path.read_text("utf-8")) if ph_path.exists() else None
    ts = json.loads((HERE / FOLDERS[spec_id] / "table_stats.json").read_text("utf-8"))
    cf_path = HERE / FOLDERS[spec_id] / "confounders.json"
    scan = json.loads(cf_path.read_text("utf-8")) if cf_path.exists() else None
    stats = {c["id"]: c["outcomes"] for c in ts["cases"]}
    by_id = {c["id"]: c for c in est["cases"]}
    out = []
    for case in spec.cases:
        res = by_id[case["id"]]
        prim = next(o for o in case["outcomes"] if o["role"] == "primary")
        outcomes, events, rows = [], [], []
        for o in case["outcomes"]:
            r = res["outcomes"][o["key"]]
            oc = outcome_result(o, r, res["grade"], o is prim)
            if oc:
                outcomes.append(oc)
                rows += estimator_rows(o, r)
                if (e := event_study(o, r)) is not None:
                    events.append(e)
        old = None
        if case["supersedes"]:
            old = json.loads((default_evaluations_dir() / f"{case['supersedes'][0]}.json").read_text("utf-8"))
        reg = res["outcomes"][prim["key"]].get("registered") or {}
        comp = [o for o in outcomes if o["category"] == "competition"]
        prices_ = [o for o in outcomes if o["category"] == "prices"]

        def summary(items):
            if not items:
                return "Not measured in this evaluation."
            return " ".join(
                f"{x['label']}: {wu(x['estimate'], x['unit'])} (p = {fp(x['p_value'])}; detectable from "
                f"{a1(x['mde_80'])})."
                for x in items
            )

        first = [c["first_post"] for c in prim["cohorts"]]
        last = [c["last_post"] for c in prim["cohorts"]]
        window = (
            f"{min(first)} to {max(last)} (quarters)"
            if prim["kind"] == "price"
            else f"{fy(min(first))} to {fy(max(last))}"
        )
        verdict = res["verdict"]
        headline = (
            f"{VERDICT_LABELS[verdict]}: {low1(outcome_label(prim))} {wu(reg.get('estimate'), unit_of(prim))} "
            f"(p = {fp(reg.get('p'))}), {low1(LAYER_LABELS[prim['layer']])}"
            + ("." if verdict == "not-identified" else f", grade {res['grade']}.")
        )
        reasons = [reason_text(x) for x in res["grade_reasons"] if not x.startswith("design checks passed")]
        if res["grade"] == "Moderate":
            reasons.append(why_not_strong(case, prim, reg, spec.parameters))
        caveats = [
            *reasons,
            *posthoc_reading(case["id"], ph)[1],
            *confounder_caveat(case, scan),
            "Re-evaluation: the earlier results were known when this specification was written; the estimator layers "
            "were fixed beforehand by the blinded power study."
            if case["supersedes"]
            else "First evaluation of a draft register family: dates and industries are not yet checked by a person.",
        ]
        ev = {
            "id": case["id"],
            "title": case["title"],
            "records": case["records"],
            "family": case["family"],
            "follows": case["follows"],
            "evaluated_on": "2026-10-18",
            "hypothesis": case["hypothesis"],
            "design": case["design"],
            "comparison": "; ".join(
                f"{'/'.join(c['treated'])} from {c['first_post']} against {'/'.join(c['controls'])}"
                for c in prim["cohorts"]
            ),
            "window": window,
            "verdict": verdict,
            "finding_label": VERDICT_LABELS[verdict],
            "grade": res["grade"],
            "grade_reason": "; ".join(reason_text(x) for x in res["grade_reasons"]),
            "headline": headline,
            "category_summaries": {
                "competition": summary(comp),
                "prices": summary(prices_),
                "productivity": "Not measured in this evaluation.",
            },
            "key_insights": insights(case, res, old, ph),
            "method": method(case, prim),
            "preregistered": True,
            "outcomes": outcomes,
            "event_studies": events,
            "caveats": caveats,
            "documents": [
                {"label": "Results", "path": "docs/results_phase5.md"},
                {"label": "Pre-analysis plan", "path": "docs/pap_phase5.md"},
                {"label": "Specification", "path": f"alicia/specs/{spec_id}.json"},
                {"label": "Estimation code", "path": "alicia/analyses/phase5/run.py"},
            ],
            "built_by": "alicia/analyses/phase5/evaluations.py",
            "supersedes": case["supersedes"],
            "evaluated_at": RUN_AT[spec_id].isoformat(),
            "estimators": rows,
            "tables": [regression_table(spec_id, case, res, stats[case["id"]], est["q_values"])],
        }
        out.append(Evaluation.model_validate(ev))
    return out


def table(spec_id: str) -> str:
    spec = load(spec_id)
    est = json.loads((HERE / FOLDERS[spec_id] / "estimate.json").read_text("utf-8"))
    by_id = {c["id"]: c for c in est["cases"]}
    lines = [
        "| Evaluation | Outcome | Layer | Estimate | 90% interval | p | q | MDE | Pre-trend check | Verdict | Grade |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for case in spec.cases:
        res = by_id[case["id"]]
        for o in case["outcomes"]:
            r = res["outcomes"][o["key"]]
            reg = r.get("registered") or {}
            q = est["q_values"].get(f"{case['id']}:{o['key']}")
            lo, hi = reg.get("interval_90", [None, None])
            pre = {True: "pass", False: "fail", None: "n/a"}[r.get("pre_inside_95")]
            lines.append(
                f"| {case['title'] if o is case['outcomes'][0] else ''} | {outcome_label(o)} ({o['role']}) | "
                f"{LAYER_LABELS[o['layer']]} | {s1(reg.get('estimate'))} | {s1(lo)} to {s1(hi)} | {fp(reg.get('p'))} | "
                f"{fp(q)} | {a1(reg.get('mde_80'))} | {pre} | "
                + (f"{VERDICT_LABELS[res['verdict']]} | {res['grade']} |" if o is case["outcomes"][0] else " | |")
            )
    return "\n".join(lines)


def design_table(spec_id: str) -> str:
    """The blinded design stage, for the plan: feasibility, registered layer's MDE, own-class draws, pre-trend check."""
    spec = load(spec_id)
    des = json.loads((HERE / FOLDERS[spec_id] / "design.json").read_text("utf-8"))
    by_id = {c["id"]: c for c in des["cases"]}
    lines = [
        "| Evaluation | Outcome | Registered layer | Placebos | MDE (registered) | Smallest MDE (layer) "
        "| Own-class draws | Pre-trend check |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for case in spec.cases:
        for o in case["outcomes"]:
            d = by_id[case["id"]]["outcomes"][o["key"]]
            name = case["title"] if o is case["outcomes"][0] else ""
            if not d["feasible"]["ok"]:
                lines.append(
                    f"| {name} | {outcome_label(o)} | — | — | — | — | — | "
                    f"not feasible: {'; '.join(d['feasible']['reasons'])} |"
                )
                continue
            lay = d["layers"]
            ok = {k: v["mde"] for k, v in lay.items() if v["mde"] is not None}
            best = min(ok, key=ok.get)
            own = ", ".join(f"{k.replace('_', ' and ')} {v['draws']}" for k, v in d["own_class"].items() if v["draws"])
            pre = {True: "pass", False: "fail", None: "n/a"}[d["event"]["pre_inside_95"]]
            lines.append(
                f"| {name} | {outcome_label(o)} ({o['role']}) | {LAYER_LABELS[o['layer']]} | "
                f"{len(d['placebo_groups'])} | "
                f"{a1(lay[o['layer']]['mde'])} | {a1(ok[best])} ({LAYER_LABELS[best]}) | {own or '—'} | {pre} |"
            )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True, choices=sorted(FOLDERS))
    ap.add_argument("--table", action="store_true", help="print the results table instead of writing files")
    ap.add_argument("--design-table", action="store_true", help="print the blinded design-stage table")
    args = ap.parse_args()
    if args.design_table:
        print(design_table(args.spec))
        return
    if args.table:
        print(table(args.spec))
        return
    for ev in build(args.spec):
        print(f"wrote {write_evaluation(ev)}")


if __name__ == "__main__":
    main()
