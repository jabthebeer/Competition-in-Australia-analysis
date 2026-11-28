"""Compliance cost: the staff time each requirement on the register costs the businesses it binds, a year
(DECISIONS E-700; methods note ``docs/compliance_costs.md``).

The method follows the Office of Impact Analysis (OIA) *Regulatory Burden Measurement Framework* (July 2026). Its
labour formula (p. 9, traceability R-39) is time required × labour cost × times performed × number of entities. Here,
for each requirement and each industry class and state it reaches:

    cost a year = $91.54 × (hours to start × new businesses a year + hours each year × businesses operating)

- **$91.54 an hour** is the framework's default work rate (p. 12), read from the burden calculator
  (``regulatory-burden-tool/src/engine/parameters.ts``).
- **Hours** come from the requirement's kind (``regulation-register/compliance-cost-assumptions.json``), or, for a
  costed licence, from the licence costs (E-175): renewal hours divided by the years between renewals. All are
  assumed, with a low and a high value.
- **Businesses** are the ABS Counts of Australian Businesses (by class, state and employment size, latest June) that
  the requirement's size test lets it bind: the phase 5 counting rules (E-178, ``menu/exposure.py``). New businesses
  are the ABS entries over the year, in the same size bands.

Every business that enters pays the start-up hours once, so in a steady state the yearly cost is entrants × start-up
hours plus the stock × yearly hours. That is the same as the framework's yearly average over 10 years for a steady
flow of entrants, with no discounting and constant prices (pp. 6–7).

An **upper bound** (a rule that binds only some of the businesses counted: above a size threshold the bands can't pin
down, of some legal forms, or doing an activity) is shown as "up to" and kept out of the headline totals. Where that
upper bound covers a quarter or more of the businesses in the rule's jurisdiction, it says nothing useful, so the rule
is not costed and says why.

**Left out**, as the page says: the substantive cost of meeting a standard (equipment, building work, training,
premiums), delay costs, fees paid to government (shown beside the figure, never in it: the framework excludes them,
p. 4), and effects on competition and prices (excluded too). No business is assumed to comply anyway, so figures lean
high. A council's rule is not costed, because business counts by council are not in the panel.

This module is pure: it takes the requirements, the counts and the assumptions and returns plain dicts.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from ..menu import exposure as X
from ..pipeline import schema, store
from ..register.requirements import Requirement
from ..register.severity import severity

ROOT = Path(__file__).resolve().parents[4]
ASSUMPTIONS = ROOT / "regulation-register" / "compliance-cost-assumptions.json"
COSTINGS = ROOT / "regulation-register" / "costings"
TASKS = ROOT / "regulation-register" / "compliance-tasks.json"
EVIDENCE = ("sourced", "analogue", "calculated", "assumed")
PARAMETERS = ROOT / "regulatory-burden-tool" / "src" / "engine" / "parameters.ts"
SCENARIOS = ("low", "central", "high")
CLASS_TIERS = ("cth", "state", "cthUpper", "stateUpper")  # exact figures, and upper bounds apart
FALLBACK_RATE = 91.54  # RBM p. 12, if the calculator's parameters can't be read


def work_rate(path: Path = PARAMETERS) -> float:
    """The OIA work rate, from the burden calculator's parameters (as ``scripts/licence_costs.py`` reads it)."""
    if not path.exists():
        return FALLBACK_RATE
    m = re.search(r'hourly:\s*"([\d.]+)"', path.read_text("utf-8"))
    return float(m.group(1)) if m else FALLBACK_RATE


def load_cards(folder: Path = COSTINGS, rate: float | None = None) -> tuple[dict[str, dict], dict[str, dict]]:
    """The costing cards (E-702), as ``(by requirement id, by family)``. A card that gives dollars gets its hours
    here: the dollars an entity a year ÷ the work rate, split into hours to start and each year by ``start_share``."""
    rate = work_rate() if rate is None else rate
    by_req: dict[str, dict] = {}
    by_family: dict[str, dict] = {}
    if not folder.exists():
        return by_req, by_family
    for f in sorted(folder.glob("*.json")):
        card = json.loads(f.read_text("utf-8"))
        card["file"] = f.name
        sc = card.get("source_cost")
        if sc:
            per = sc["cost_a_year"] / sc["entities"] / rate
            mult = {"low": sc["range"]["low"], "central": 1.0, "high": sc["range"]["high"]}
            share = sc.get("start_share", 0)
            card["start_hours"] = {s: round(per * mult[s] * share, 1) for s in SCENARIOS}
            card["yearly_hours"] = {s: round(per * mult[s] * (1 - share), 1) for s in SCENARIOS}
        target = card["applies_to"]
        (by_req if "requirement" in target else by_family)[target.get("requirement") or target["family"]] = card
    return by_req, by_family


def load_assumptions(path: Path = ASSUMPTIONS, cards: Path = COSTINGS, tasks: Path = TASKS) -> dict:
    """The hours for each kind, with the costing cards beside them (``overrides`` by requirement id, ``families``)
    and the recurring task of each kind with the frequency phrases (``tasks``, E-703)."""
    a = json.loads(path.read_text("utf-8"))
    a["overrides"], a["families"] = load_cards(cards)
    a["tasks"] = json.loads(tasks.read_text("utf-8")) if tasks.exists() else None
    return a


def frequency(q: Requirement, rules: dict) -> dict | None:
    """How often the requirement's recurring task is done, from its own words (E-703): its ``what`` first, then its
    title, then the quotes from its law. ``{"times", "name", "phrase", "where"}``, or None when no frequency phrase
    is found."""
    texts = [("what", q.what), ("title", q.title)]
    texts += [(f"quote from {s.locator or s.title}", s.quote or "") for s in q.sources]
    skip = re.compile(rules["not_a_frequency"], re.I)
    for where, text in texts:
        found = []
        for f in rules["frequencies"]:
            for m in re.finditer(f["pattern"], text, re.I):
                if skip.match(text[m.end() :]):
                    continue
                times = f["times_a_year"]
                if times == "1/n":
                    n = m.group(1).lower()
                    times = 1 / float(rules["numbers"].get(n, n))
                lo, hi = max(0, m.start() - 40), min(len(text), m.end() + 40)
                found.append(
                    (
                        m.start(),
                        {"times": float(times), "name": f["name"], "phrase": text[lo:hi].strip(), "where": where},
                    )
                )
                break
        if found:
            return min(found, key=lambda x: x[0])[1]
    return None


@dataclass(frozen=True)
class Flows:
    """Businesses operating at the end of the latest financial year, and entries over it, by class and state, for
    each size basis (``exposure.BASES``)."""

    stock: dict[str, dict[tuple[str, str], float]]
    entries: dict[str, dict[tuple[str, str], float]]
    year: int  # the June the counts are for
    all_by_class: dict[str, float] = field(default_factory=dict)  # every business, Australia, by class

    def sum(self, which: str, basis: str, pairs) -> float:
        src = (self.stock if which == "stock" else self.entries)[basis]
        return sum(src.get(p, 0.0) for p in sorted(pairs))


BAND_SETS = {
    "all": ("non-employing", "1-19 employees", "20-199 employees", "200+ employees"),
    "employing": ("1-19 employees", "20-199 employees", "200+ employees"),
    "20+": ("20-199 employees", "200+ employees"),
    "200+": ("200+ employees",),
}


def flows_from(df) -> Flows | None:
    """Flows from the CABEE class-by-state panel (``data/processed/abs_cabee/class_state_fy.parquet``)."""
    df = df[df["geo_code"].isin(schema.STATES) & df["industry_code"].str.fullmatch(r"\d{4}")]
    df = df[df["breakdown"] != ""]
    if df.empty:
        return None
    last = df["period"].max()
    df = df[df["period"] == last]

    def table(measure: str, bands) -> dict:
        x = df[(df["measure"] == measure) & df["breakdown"].isin(bands)]
        return {k: float(v) for k, v in x.groupby(["industry_code", "geo_code"])["value"].sum().items()}

    stock = {b: table("businesses_end", bands) for b, bands in BAND_SETS.items()}
    entries = {b: table("entries", bands) for b, bands in BAND_SETS.items()}
    by_class: dict[str, float] = {}
    for (c, _), v in sorted(stock["all"].items()):
        by_class[c] = by_class.get(c, 0.0) + v
    return Flows(stock, entries, int(last.year) + 1, by_class)


@lru_cache(maxsize=1)
def load_flows() -> Flows | None:
    import pandas as pd

    path = store.PROCESSED / "abs_cabee" / "class_state_fy.parquet"
    if not path.exists():
        return None
    cols = ["measure", "industry_code", "geo_code", "breakdown", "period", "value"]
    return flows_from(pd.read_parquet(path, columns=cols))


def hours_for(q: Requirement, assumptions: dict, licences: dict[str, dict]) -> dict | None:
    """The hours to start and each year (low, central, high), the fees beside them, and where the hours come from;
    None when the requirement's kind is not costed."""
    over = assumptions.get("overrides", {}).get(q.id) or assumptions.get("families", {}).get(q.family or "")
    if over:
        return {
            "start": over["start_hours"],
            "yearly": over["yearly_hours"],
            "from": "override",
            "basis": over["basis"],
            "task": over.get("task") or assumptions["kinds"][q.kind]["task"],
            "feesStart": None,
            "feesYearly": None,
            "entities": over.get("entities"),
            "evidence": over["evidence"],
            "card": over["file"],
        }
    lic = licences.get(q.id)
    if lic:
        k = max(int(lic["renewal_years"]), 1)
        sh, rh = lic["start_hours"], lic["renewal_hours"]
        renew_fees = lic.get("renewal_fees")
        return {
            "start": sh,
            "yearly": {s: rh[s] / k for s in SCENARIOS},
            "from": "licence",
            "basis": f"The licence costs (DECISIONS E-175): staff time to apply, and to renew every {k} "
            f"year{'s' if k > 1 else ''}, assumed as for every licence; fees quoted from the fee regulations.",
            "task": f"Apply for the licence ({lic['licence']}), then renew it "
            + ("every year" if k == 1 else f"every {k} years"),
            "renewalYears": k,
            "feesStart": lic.get("entry_fees"),
            "feesYearly": renew_fees / k if renew_fees is not None else None,
        }
    kind = assumptions["kinds"].get(q.kind)
    if not kind or kind.get("costed") is False:
        return None
    rules = assumptions.get("tasks")
    task = (rules or {}).get("kinds", {}).get(q.kind)
    freq = frequency(q, rules) if task else None
    if freq:
        times = freq["times"]
        return {
            "start": kind["start_hours"],
            "yearly": {s: task["hours_a_time"][s] * times for s in SCENARIOS},
            "from": "tasks",
            "basis": f"{task['task']}, {freq['name']} ({times:g} times a year), as the requirement's {freq['where']} "
            f"says: '{freq['phrase']}'. The hours each time are assumed.",
            "task": f"{task['task']} ({freq['name']})",
            "feesStart": None,
            "feesYearly": None,
            "evidence": "calculated",
            "frequency": {**freq, "hoursATime": task["hours_a_time"]},
        }
    return {
        "start": kind["start_hours"],
        "yearly": kind["yearly_hours"],
        "from": "kind",
        "basis": kind["basis"],
        "task": kind["task"],
        "feesStart": None,
        "feesYearly": None,
    }


def upper_bound(q: Requirement) -> tuple[bool, list[str]]:
    """Whether the businesses counted are only an upper bound, and why (the same tests as the impact classes)."""
    why = []
    _, size_upper = X.size_basis(q.triggers)
    if size_upper:
        why.append("it binds only businesses above a size threshold the ABS size bands can't pin down")
    if X.form_limited(q):
        why.append("it binds only some legal forms, and the counts are not split by legal form")
    if X.conditional(q) or severity(q)["bound"] == "some":
        why.append("it binds only the businesses doing some activity, and the whole industry is counted")
    return bool(why), why


def cost_requirement(q: Requirement, flows: Flows | None, assumptions: dict, licences: dict[str, dict], rate: float):
    """One requirement's compliance cost, with every number its working shows, and its cost by class (summed over
    states). ``(row, by_class)``; a row that is not costed says why and has no figures."""
    row = {
        "id": q.id,
        "title": q.title,
        "jurisdiction": q.jurisdiction,
        "tier": q.tier,
        "kind": q.kind,
        "records": list(q.records),
        "costed": False,
        "why": None,
    }
    h = hours_for(q, assumptions, licences)
    if q.tier == "local":
        row["why"] = "A council's rule: business counts by council are not in the panel, so it is not costed."
        return row, {}
    if h is None:
        row["why"] = assumptions["kinds"].get(q.kind, {}).get("basis") or "Its kind has no assumed hours."
        return row, {}
    if flows is None:
        row["why"] = "The business counts have not been built."
        return row, {}
    basis, _ = X.size_basis(q.triggers)
    upper, why_upper = upper_bound(q)
    pairs = X.requirement_pairs(q)
    ents = h.get("entities")
    if ents:
        # A regulator's list of the entities bound replaces the ABS counts, so the count is exact (DECISIONS E-701).
        alloc = entity_classes(ents, flows, q.jurisdiction)
        stock, new, upper, why_upper = sum(alloc.values()), 0.0, False, []
    else:
        stock = flows.sum("stock", basis, pairs)
        new = flows.sum("entries", basis, pairs)
    home = schema.STATES if q.jurisdiction == "CTH" else (q.jurisdiction,)
    base = sum(v for (_, s), v in sorted(flows.stock["all"].items()) if s in home)
    share = 100 * stock / base if base else 0.0
    if upper and share >= X.WIDE_SHARE:
        # An upper bound over much of the economy says nothing about the businesses actually bound.
        row["why"] = (
            f"Not counted: it binds only some businesses ({'; '.join(why_upper)}), across industries holding "
            f"{share:.0f}% of the businesses in its jurisdiction, so the ABS counts can't say how many it binds."
        )
        row["withheld"] = True
        return row, {}
    per_start = {s: h["start"][s] * rate for s in SCENARIOS}
    per_year = {s: h["yearly"][s] * rate for s in SCENARIOS}
    cost = {s: per_start[s] * new + per_year[s] * stock for s in SCENARIOS}
    fees = None
    if h["feesStart"] is not None or h["feesYearly"] is not None:
        fees = (h["feesStart"] or 0.0) * new + (h["feesYearly"] or 0.0) * stock
    row.update(
        {
            "costed": True,
            "task": h["task"],
            "hoursFrom": h["from"],
            "evidence": h.get("evidence", "assumed"),
            "card": h.get("card"),
            "frequency": h.get("frequency"),
            "basisText": h["basis"],
            "rate": rate,
            "sizeBasis": basis,
            "sizeBasisLabel": ents["label"] if ents else X.BASIS_LABELS[basis],
            "countsFrom": ents["label"] if ents else "abs",
            "upper": upper,
            "upperWhy": why_upper,
            "states": sorted({s for _, s in pairs}, key=schema.STATES.index),
            "classes": len(alloc) if ents else len({c for c, _ in pairs}),
            "businesses": round(stock),
            "share": round(share, 1),
            "newPerYear": round(new),
            "startHours": h["start"],
            "yearlyHours": h["yearly"],
            "perBusinessStart": per_start,
            "perBusinessYear": per_year,
            "cost": cost,
            "feesStart": h["feesStart"],
            "feesYearly": h["feesYearly"],
            "feesTotal": fees,
            "year": flows.year,
        }
    )
    by_class: dict[str, dict[str, float]] = {}
    if ents:
        for c, n in sorted(alloc.items()):
            by_class[c] = {k: per_year[k] * n for k in SCENARIOS}
        return row, by_class
    for c, s in sorted(pairs):
        st = flows.stock[basis].get((c, s), 0.0)
        en = flows.entries[basis].get((c, s), 0.0)
        if not (st or en):
            continue
        acc = by_class.setdefault(c, dict.fromkeys(SCENARIOS, 0.0))
        for k in SCENARIOS:
            acc[k] += per_start[k] * en + per_year[k] * st
    return row, by_class


def entity_classes(ents: dict, flows: Flows, jurisdiction: str = "CTH") -> dict[str, float]:
    """The entities a regulator lists, by ANZSIC class: each group's count goes to its classes in proportion to the
    ABS businesses in them (evenly where the ABS counts none). A group limited to some ``states`` counts only for a
    requirement of one of them (or a Commonwealth one)."""
    out: dict[str, float] = {}
    for g in ents["groups"]:
        if g.get("states") and jurisdiction != "CTH" and jurisdiction not in g["states"]:
            continue
        cs = sorted(g["classes"])
        w = {c: flows.all_by_class.get(c, 0.0) for c in cs}
        tot = sum(w.values())
        for c in cs:
            out[c] = out.get(c, 0.0) + g["count"] * (w[c] / tot if tot else 1 / len(cs))
    return out


def load_licences(path: Path | None = None, inputs: Path | None = None) -> dict[str, dict]:
    """The costed licences' hours and fees, from ``licence_costs.csv`` and the ranges in ``licence-costs.json``."""
    import csv

    path = path or ROOT / "data" / "processed" / "legislation" / "licence_costs.csv"
    inputs = inputs or ROOT / "regulation-register" / "licence-costs.json"
    if not path.exists():
        return {}
    data = json.loads(inputs.read_text("utf-8")) if inputs.exists() else {"items": {}, "assumed_hours": None}
    out = {}

    def num(v):
        return float(v) if v not in ("", None) else None

    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            item = data["items"].get(r["requirement"], {})
            hrs = item.get("hours") or data["assumed_hours"]
            out[r["requirement"]] = {
                "licence": r["licence"],
                "renewal_years": int(r["renewal_years"]),
                "entry_fees": num(r["entry_fees"]),
                "renewal_fees": num(r["renewal_fees"]),
                "start_hours": {s: float(hrs["entry"][s]) for s in SCENARIOS},
                "renewal_hours": {s: float(hrs["renewal"][s]) for s in SCENARIOS},
            }
    return out


def cost_all(
    reqs: list[Requirement],
    flows: Flows | None = None,
    assumptions: dict | None = None,
    licences: dict[str, dict] | None = None,
    rate: float | None = None,
) -> dict:
    """Every requirement's cost, the cost in each class (Commonwealth and state rules apart), and the totals."""
    flows = load_flows() if flows is None else flows
    assumptions = load_assumptions() if assumptions is None else assumptions
    licences = load_licences() if licences is None else licences
    rate = work_rate() if rate is None else rate
    rows, classes = [], {}
    for q in sorted(reqs, key=lambda q: q.id):
        row, by_class = cost_requirement(q, flows, assumptions, licences, rate)
        rows.append(row)
        if not row["costed"]:
            continue
        tier = ("cth" if q.jurisdiction == "CTH" else "state") + ("Upper" if row["upper"] else "")
        for c, v in by_class.items():
            acc = classes.setdefault(c, {**{t: dict.fromkeys(SCENARIOS, 0.0) for t in CLASS_TIERS}, "requirements": 0})
            acc["requirements"] += 1
            for k in SCENARIOS:
                acc[tier][k] += v[k]
    for c, acc in classes.items():
        acc["businesses"] = round(flows.all_by_class.get(c, 0.0)) if flows else None
    costed = [r for r in rows if r["costed"]]
    exact = [r for r in costed if not r["upper"]]

    def total(sel) -> dict[str, float]:
        return {k: sum(r["cost"][k] for r in sel) for k in SCENARIOS}

    return {
        "rows": rows,
        "classes": classes,
        "rate": rate,
        "year": flows.year if flows else None,
        "totals": {
            "cth": total([r for r in costed if r["jurisdiction"] == "CTH"]),
            "state": total([r for r in costed if r["jurisdiction"] != "CTH"]),
            "exact": total(exact),
            "exactCth": total([r for r in exact if r["jurisdiction"] == "CTH"]),
            "exactState": total([r for r in exact if r["jurisdiction"] != "CTH"]),
            "upper": total([r for r in costed if r["upper"]]),
            "byEvidence": {e: total([r for r in exact if r["evidence"] == e]) for e in EVIDENCE},
        },
        "counts": {
            "requirements": len(rows),
            "costed": len(costed),
            "upper": sum(1 for r in costed if r["upper"]),
            "withheld": sum(1 for r in rows if r.get("withheld")),
            "licence": sum(1 for r in costed if r["hoursFrom"] == "licence"),
            "byEvidence": {e: sum(1 for r in exact if r["evidence"] == e) for e in EVIDENCE},
        },
    }


def record_costs(rows: list[dict]) -> dict[str, dict]:
    """A register item's cost: the sum of the costed requirements inside it (those that name it)."""
    out: dict[str, dict] = {}
    for r in rows:
        if not r["costed"]:
            continue
        for rec in r["records"]:
            acc = out.setdefault(rec, {"cost": dict.fromkeys(SCENARIOS, 0.0), "requirements": [], "upper": False})
            for k in SCENARIOS:
                acc["cost"][k] += r["cost"][k]
            acc["requirements"].append(r["id"])
            acc["upper"] = acc["upper"] or r["upper"]
    return out


def sig(x: float, n: int = 2) -> float:
    """``x`` rounded to ``n`` significant figures (the page shows no more: the hours are assumed)."""
    if not x:
        return 0.0
    from math import floor, log10

    return round(x, -int(floor(log10(abs(x)))) + (n - 1))


def money(x: float | None, n: int = 2) -> str:
    """$ to 2 significant figures, in words for millions and billions: '$4.5 million', '$1,200', '$37'."""
    if x is None:
        return "not published"
    v = sig(x, n)
    if abs(v) >= 1e9:
        return f"${v / 1e9:,.{max(0, n - len(str(int(abs(v) // 1e9))))}f} billion".replace(".0 b", " b")
    if abs(v) >= 1e6:
        return f"${v / 1e6:,.{max(0, n - len(str(int(abs(v) // 1e6))))}f} million".replace(".0 m", " m")
    return f"${v:,.0f}"
