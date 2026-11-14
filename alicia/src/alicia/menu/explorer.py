"""Legislative levers influencing competition (the legislation menu): every register item, and every requirement a law
places on businesses, marked against the productivity impact framework, with summary statistics for the industries
an item affects.

One self-contained page (``menu.html`` on the website, ``alicia explorer`` on its own). Since 11 November 2026
(DECISIONS E-137) it lists the requirements the Industry lens shows (``regulation-register/requirements/``) beside the
register items, in one vocabulary with the lens: reforms, existing settings and requirements are all "legislative
influences", a non-legislative barrier keeps its own tag, and each entry is tagged with the market position it most
affects (entrants, existing competitors, or monopolies and oligopolies; ``register/competition.py``). A requirement
that belongs to a register item (the same law in force) is shown inside that item, not as a row of its own.

Filters include the framework's drivers ("main driver" tags), the overall mark, the type (laws and policies,
requirements, non-legislative barriers), the market position most affected, jurisdiction, reach, status (including
repealed or replaced) and the department or agency responsible, and the complexity tags of the regulatory regimes an
item belongs to (duplicative, inconsistent across states, unclear guidance and others; DECISIONS E-96). Views: a
list, a scorecard of every item's marks by driver, a
timeline of reforms, recommendations, and industries (every ANZSIC class with the regimes it faces). Items that share a
family (one policy in several jurisdictions) appear as one row under a group name that says what the issue is across
them, and expand to each jurisdiction's item (DECISIONS E-99). Each item opens
with its assessment (only the drivers it affects; each opens to its reason), then collapsible sections: its regimes
(with a diagram of which tiers of government do what, and where they overlap), recommendations, who is responsible, a
timeline of its changes, its industries' statistics, and its sources. Secondary filters, explanations and the page's
method notes sit behind a "More filters" dropdown, "i" buttons and folds, and no text is set below 13px (owner request,
29 October 2026, DECISIONS E-98).

The econometric evaluations that the menu used to show are archived (DECISIONS E-75, E-87) and, since
11 November 2026, off the website altogether (E-136): the menu neither shows nor links them.
"""

from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from pathlib import Path

from .. import anzsic
from ..register import competition as C
from ..register import framework
from ..register.bodies import BODY_TYPE_LABELS, Body, load_bodies
from ..register.evaluation import Evaluation
from ..register.families import Family, load_families
from ..register.recommendations import KIND_LABELS as REC_KIND_LABELS
from ..register.recommendations import Recommendation, actors_of, by_record, gap_for, load_gaps, load_recommendations
from ..register.regimes import (
    CONSISTENCY_LABELS,
    FUNCTION_LABELS,
    ISSUE_HELP,
    ISSUE_LABELS,
    TIER_LABELS,
    VARYING,
    Regime,
    classes_for,
    industry_profiles,
    load_regimes,
    regimes_by_record,
)
from ..register.requirements import KIND_LABELS as OBLIGATION_LABELS
from ..register.requirements import TRIGGER_LABELS, Requirement, load_requirements, reach_classes
from ..register.schema import CHANNEL_LABELS, ROLE_LABELS, ChangeRecord
from ..register.severity import severity
from ..register.timeline import changed_by_index, changes_list, ended_dict, timeline
from ..timing import timing
from . import exposure as X
from .archive import CHECK_NOTE, FAMILY_LABELS, _humanise, _short
from .industry import NOTE as STATS_NOTE
from .industry import STATE_NAMES, TILES, IndustryStats, measures_dict

MENU_NOTE = (
    "Every item is marked from −2 to +2 on each of the framework's eight drivers of productivity; the overall mark "
    "is their sum. Marks are judgements from desk research and the sources cited, not estimates. They cover "
    "productivity and competition only: many rules have benefits for health, safety, the environment or fairness "
    "that are not weighed here."
)


def _division_names() -> dict[str, str]:
    return {code: anzsic.name(code) or "" for code in "ABCDEFGHIJKLMNOPQRS"}


def assessment_dict(record: ChangeRecord | Requirement) -> dict | None:
    a = record.assessment
    if a is None:
        return None
    return a.model_dump(mode="json") | {"total": a.total, "rating": a.rating, "mixed": a.mixed}


def market_dict(record: ChangeRecord | Requirement) -> dict:
    """Where an item's marks act among market players (``register/competition.py``): the positions it most affects,
    and each position's effect and strength, with the indexes of the assessment's marks behind it (the page words the
    effect from ``effectPhrases``)."""
    a = record.assessment
    if a is None:
        return {"most": [], "effects": {}}
    effects = {}
    for pos, e in C.effects(a).items():
        idx = [n for n, m in enumerate(a.marks) if pos in C.positions(m)]
        effects[pos] = {"effect": e["effect"], "strength": e["strength"], "marks": idx}
    return {"most": C.most_affected(a), "effects": effects}


def _req_source(s) -> dict:
    return {
        "title": s.title,
        "publisher": s.publisher,
        "url": str(s.url),
        "locator": s.locator,
        "quote": s.quote,
        "accessed": s.accessed.isoformat(),
        "checked": s.checked,
    }


def requirement_dict(q: Requirement, regimes: dict[str, Regime], record_marks: dict[str, list] | None = None) -> dict:
    """A requirement as the page shows it: as a row of its own, or inside the register item it belongs to. Its
    industries are ANZSIC class codes (``industryCodes``; the page looks up their names), or every industry."""
    every = any(r.scope == "all" and not r.exclude for r in q.reach)
    codes = sorted({c for r in q.reach for c in reach_classes(r)}) if not every else []
    marks = [m.model_dump(mode="json") for m in q.assessment.marks]
    regs = [regimes[q.regime]] if q.regime in regimes else []
    data = {
        "id": q.id,
        "type": "requirement",
        "group": "requirement",
        "kind": "requirement",
        "family": f"req-{q.family}",
        "title": q.title,
        "short": _short(q.title),
        "jurisdiction": q.jurisdiction,
        "tier": q.tier,
        "council": q.lga_name,
        "summary": q.what,
        "obligation": OBLIGATION_LABELS[q.kind],
        "triggers": [
            {
                "label": TRIGGER_LABELS[t.type],
                "type": t.type,
                "test": t.test,
                "value": t.value,
                "unit": t.unit,
                "asAt": t.as_at.isoformat() if t.as_at else None,
                "note": t.note,
                "sources": [_req_source(s) for s in t.sources],
            }
            for t in q.triggers
        ],
        "laws": [
            {
                "title": law.title,
                "url": str(law.register_url) if law.register_url else None,
                "registerId": law.register_id,
                "provisions": law.provisions,
                "applied": law.applied,
            }
            for law in q.laws
        ],
        "sources": [_req_source(s) for s in q.sources],
        "reachGroups": [
            {
                "all": r.scope == "all",
                "classes": list(r.classes),
                "exclude": list(r.exclude),
                "activities": list(r.activities),
                "condition": r.condition,
                "legalForms": list(r.legal_forms),
                "inStates": list(r.in_states),
                "note": r.note,
                "n": len(reach_classes(r)),
            }
            for r in q.reach
        ],
        "allIndustries": every,
        "industryCodes": codes,
        "industries": [],
        "reachConfidence": q.confidence,
        "reachNote": q.confidence_note,
        "councilsAdminister": q.administered_by_councils,
        "responsible": [{"body": b, "role": "regulates", "source": None, "note": None} for b in q.administered_by],
        "regimes": [g.id for g in regs],
        "complexity": live_tags(regs),
        "assessment": assessment_dict(q),
        **market_dict(q),
        "records": list(q.records),
        "sameMarks": any(marks == m for m in (record_marks or {}).values()),
        "recs": [],
        "recGap": None,
        "timeline": [],
        "changes": [],
        "ended": None,
        "effective": None,
        "check": None,
        "stats": None,
        "drafted": q.drafted_on.isoformat(),
        "review": q.review.model_dump(mode="json"),
        "file": f"regulation-register/requirements/{'local/' + q.lga if q.lga else q.jurisdiction.lower()}/{q.id}.json",
    }
    return data


def bodies_dict(records: list[ChangeRecord], bodies: dict[str, Body], extra: set[str] = frozenset()) -> dict:
    """The bodies the records (and ``extra``, such as recommendations' actors) name, and their departments, by id."""
    used = {x.body for r in records for x in r.responsible if x.body in bodies} | {b for b in extra if b in bodies}
    used |= {bodies[b].parent for b in used if bodies[b].parent}
    keep = ("name", "short", "jurisdiction", "type", "parent", "url", "current", "note")
    return {b: bodies[b].model_dump(mode="json", include=set(keep)) for b in sorted(used)}


def recommendation_dict(rec: Recommendation, records: dict[str, ChangeRecord]) -> dict:
    data = rec.model_dump(mode="json", exclude={"drafted_on"})
    data["actors"] = actors_of(rec, records)
    data["kindLabel"] = REC_KIND_LABELS[rec.kind]
    data["international"] = any(e.origin == "international" for e in rec.evidence)
    return data


FUNCTION_SHORT = {
    "sets-rules": "Sets rules",
    "licenses": "Licenses",
    "approves": "Approves",
    "inspects": "Inspects",
    "collects": "Collects",
    "funds": "Funds",
}
COMPLEXITY_NOTE = (
    "Regulation can weigh on business through how it is organised as well as how much there is: several agencies or "
    "tiers of government for one activity, rules that differ between states, or rules that are hard to follow. Each "
    "item is linked to the regulatory regimes it belongs to; a regime's tags are problems a source has reported, each "
    "quoted. The diagram shows which tier of government does what; a function in an overlap is done by more than one "
    "tier. No tag means no evidence was found in the sources searched, not that there is no problem."
)


def live_tags(regs: list[Regime]) -> list[str]:
    """The issue tags, not yet addressed, across some regimes, in the order of ISSUE_LABELS."""
    tags = {i.tag for r in regs for i in r.issues if i.status != "addressed"}
    return [t for t in ISSUE_LABELS if t in tags]


def regime_dict(reg: Regime) -> dict:
    data = reg.model_dump(mode="json", exclude={"coverage", "review"})
    data["overlap"] = reg.overlap()
    data["tiers"] = reg.tiers
    data["touchpoints"] = reg.touchpoints
    data["varies"] = reg.consistency in VARYING
    data["classes"] = len(classes_for(reg))
    data["tags"] = live_tags([reg])
    return data


def industries_list(regimes: list[Regime]) -> list[list]:
    """One compact row per ANZSIC class: code, name, division, the indexes of its regimes in ``regimes``, then
    touchpoints, industry-specific touchpoints and issues not yet addressed."""
    index = {r.id: n for n, r in enumerate(regimes)}
    return [
        [
            p["anzsic"],
            p["name"],
            p["division"],
            [index[x] for x in p["regime_ids"].split()],
            p["touchpoints"],
            p["sector_touchpoints"],
            p["issues"],
        ]
        for p in industry_profiles(regimes)
    ]


def groups_dict(records: list[ChangeRecord], families: dict[str, Family], requirements: list[dict] = ()) -> dict:
    """Families of two or more items, each shown in the menu as one expandable row under its group name. A
    requirement's family (the same obligation in several places) is keyed ``req-<family>``, apart from the register's
    families, and named by the title most of its members share."""
    members: dict[str, list[str]] = {}
    for r in records:
        if r.family:
            members.setdefault(r.family, []).append(r.id)
    out = {
        f: {
            "title": families[f].title if f in families else FAMILY_LABELS.get(f, _humanise(f)),
            "summary": families[f].summary if f in families else None,
            "members": ids,
        }
        for f, ids in members.items()
        if len(ids) > 1
    }
    reqs: dict[str, list[dict]] = {}
    for q in requirements:
        reqs.setdefault(q["family"], []).append(q)
    for f, qs in reqs.items():
        if len(qs) < 2:
            continue
        # The title most of its members share (one state may word it differently), else the family's name.
        title, n = Counter(q["title"] for q in qs).most_common(1)[0]
        out[f] = {
            "title": title if n * 2 > len(qs) else _humanise(f.removeprefix("req-")),
            "summary": None,
            "members": [q["id"] for q in qs],
            "unit": "council" if all(q["tier"] == "local" for q in qs) else "jurisdiction",
        }
    return out


def build_payload(
    records: list[ChangeRecord],
    dates_report: list[dict] | None = None,
    generated: dt.date | None = None,
    evaluations: list[Evaluation] | None = None,
    stats: IndustryStats | None = None,
    bodies: dict[str, Body] | None = None,
    recommendations: list[Recommendation] | None = None,
    gaps: dict[str, str] | None = None,
    regimes: list[Regime] | None = None,
    families: dict[str, Family] | None = None,
    requirements: list[Requirement] | None = None,
    counts: X.Counts | None = None,
) -> dict:
    """``stats`` defaults to the committed panels (``IndustryStats.load``), ``bodies`` to the committed registry
    (``load_bodies``) and ``recommendations``, ``gaps``, ``regimes`` and ``requirements`` to the committed ones; pass
    fixtures in tests. ``counts`` are the business counts behind each rule's exposure (``exposure.load_counts``)."""
    stats = IndustryStats.load() if stats is None else stats
    counts = X.load_counts() if counts is None else counts
    today = generated or dt.date.today()

    def impact(
        kind: str,
        assessment: dict | None,
        pairs: set,
        jurisdiction: str,
        ended: bool,
        in_force: bool,
        council: bool = False,
        partial: bool = False,
    ) -> dict:
        """A row's exposure, whether it is a rule that applies today, and its impact class."""
        total = assessment["total"] if assessment else None
        exp = X.measure(pairs, jurisdiction, counts, council, partial)
        standing = X.is_standing(kind, total, ended, in_force)
        return {"exposure": exp, "standing": standing, "impactClass": X.impact_class(total, exp) if standing else None}

    bodies = load_bodies()[0] if bodies is None else bodies
    titles = {r.id: r.title for r in records}
    changed = changed_by_index(records)
    recs = load_recommendations().recommendations if recommendations is None else recommendations
    gaps = load_gaps() if gaps is None else gaps
    by_id = {r.id: r for r in records}
    recs = [x for x in recs if any(a in by_id for a in x.applies_to)]
    rec_index = by_record(recs)
    rec_dicts = [recommendation_dict(x, by_id) for x in recs]
    checks = {d["record_id"]: d for d in dates_report or []}
    regimes = load_regimes().regimes if regimes is None else regimes
    families = load_families()[0] if families is None else families
    reg_index = regimes_by_record(regimes)
    reqs = load_requirements().requirements if requirements is None else requirements
    reg_by_id = {g.id: g for g in regimes}
    # A requirement that names a register item (the same law in force) is shown inside it; the rest are rows.
    record_marks = {r.id: [m.model_dump(mode="json") for m in r.assessment.marks] for r in records if r.assessment}
    nested: dict[str, list[dict]] = {}
    rows_req = []
    for q in reqs:
        homes = [x for x in q.records if x in by_id]
        d = requirement_dict(q, reg_by_id, {x: record_marks.get(x) for x in homes})
        d.update(
            impact(
                "requirement",
                d["assessment"],
                X.requirement_pairs(q),
                q.jurisdiction,
                False,
                True,
                q.tier == "local",
                X.conditional(q),
            )
        )
        d["exposure"]["beyond"] = X.beyond(q)
        d["severity"] = severity(q)
        for x in homes:
            nested.setdefault(x, []).append(d)
        if not homes:
            rows_req.append(d)
    out = []
    for r in records:
        eff = r.effective_commencement
        check = checks.get(r.id)
        # The timeline carries the dates and the history.
        data = r.model_dump(
            mode="json", exclude={"comparison", "confounders", "price_series", "assessment", "dates", "history"}
        )
        data.update(
            {
                "effective": eff.date.isoformat() if eff else None,
                "effectiveWhat": eff.what if eff else None,
                "firstFullFy": timing(eff.date).first_full_fy if eff else None,
                "channelLabels": [CHANNEL_LABELS[c] for c in r.channels],
                "short": _short(r.title),
                "check": {"status": check["status"], "issues": check["issues"]} if check else None,
                "assessment": assessment_dict(r),
                "stats": stats.snapshot(r) if stats else None,
                "ended": ended_dict(r),
                "timeline": timeline(r, titles, generated),
                "changes": changes_list(changed.get(r.id, [])),
                "recs": [x.id for x in rec_index.get(r.id, [])],
                "recGap": None if r.id in rec_index else gap_for(r, gaps),
                "regimes": [x.id for x in reg_index.get(r.id, [])],
                "complexity": live_tags(reg_index.get(r.id, [])),
                "type": "record",
                "group": framework.influence_group(r.kind),
                **market_dict(r),
                "requirements": nested.get(r.id, []),
            }
        )
        data["industries"] = [{**i, "division": anzsic.division(i["anzsic"])} for i in data["industries"]]
        data.update(
            impact(
                r.kind,
                data["assessment"],
                X.record_pairs(r),
                r.jurisdiction,
                bool(data["ended"]),
                bool(eff and eff.date <= today),
            )
        )
        out.append(data)
    out += rows_req
    # Every ANZSIC code the requirements name: the classes they reach, and the codes at any level their reach lists.
    every_req = rows_req + [q for qs in nested.values() for q in qs]
    used_classes = sorted(
        {c for q in every_req for c in q["industryCodes"]}
        | {c for q in every_req for g in q["reachGroups"] for c in g["classes"] + g["exclude"]}
    )
    return {
        "generated": (generated or dt.date.today()).isoformat(),
        "records": out,
        "framework": framework.as_dict(),
        "channels": [{"id": k, "label": v} for k, v in CHANNEL_LABELS.items()],
        "familyLabels": {f: FAMILY_LABELS.get(f, _humanise(f)) for f in {r.family for r in records if r.family}},
        "groups": groups_dict(records, families, rows_req),
        "bodies": bodies_dict(
            records,
            bodies,
            {b for x in rec_dicts for b in x["actors"]} | {b for q in reqs for b in q.administered_by},
        ),
        # Names and divisions of the classes the requirements reach, so each requirement carries only codes.
        "classNames": {c: [anzsic.name(c) or "", anzsic.division(c)] for c in used_classes},
        "positions": [
            {"id": p, "label": C.POSITION_LABELS[p], "question": C.POSITION_QUESTIONS[p]} for p in C.POSITIONS
        ],
        "effectPhrases": C.EFFECT_PHRASES,
        "recommendations": rec_dicts,
        "recKinds": REC_KIND_LABELS,
        "regimes": [regime_dict(x) for x in regimes],
        "industries": industries_list(regimes) if regimes else [],
        "issueTags": {k: {"label": v, "help": ISSUE_HELP[k]} for k, v in ISSUE_LABELS.items()},
        "tiers": TIER_LABELS,
        "functions": {k: {"label": v, "short": FUNCTION_SHORT[k]} for k, v in FUNCTION_LABELS.items()},
        "consistency": CONSISTENCY_LABELS,
        "complexityNote": COMPLEXITY_NOTE,
        "bodyTypes": BODY_TYPE_LABELS,
        "roles": ROLE_LABELS,
        "divisions": _division_names(),
        "menuNote": MENU_NOTE,
        "statsNote": STATS_NOTE,
        "statsSources": stats.sources if stats else {},
        "statsMeasures": measures_dict(),
        "statsTiles": list(TILES),
        "places": STATE_NAMES,
        "checkNote": CHECK_NOTE,
        "impactClasses": [{"id": k, "label": v, "help": X.CLASS_HELP[k]} for k, v in X.CLASSES.items()],
        "exposureNote": X.NOTE,
        "exposureYear": counts.year if counts else None,
    }


def menu_payload(
    records: list[ChangeRecord], dates_report: Path | None = None, evaluations: list[Evaluation] | None = None
) -> dict:
    """The page's data, given the path of a dates report (``alicia dates --all --json``), if there is one."""
    report = json.loads(dates_report.read_text("utf-8")) if dates_report and dates_report.exists() else None
    return build_payload(records, report, evaluations=evaluations)


def build_explorer(
    records: list[ChangeRecord],
    out: Path,
    dates_report: Path | None = None,
    standalone: bool = False,
    evaluations: list[Evaluation] | None = None,
    pages: tuple | None = None,
    payload: dict | None = None,
) -> Path:
    """Write the menu to ``out``. ``pages`` is the site navigation (``growth.PAGES`` and the costing tab, when
    built); left out, the page is written with the navigation of a full site build. ``payload`` is the page's data
    when the caller has already built it (``menu_payload``), as the site build does to share it with Home."""
    from .growth import MENU_PAGE, PAGES, render

    if payload is None:
        payload = menu_payload(records, dates_report, evaluations)
    out.write_text(render("explorer.html", payload, MENU_PAGE[0], standalone, pages or PAGES), encoding="utf-8")
    return out
