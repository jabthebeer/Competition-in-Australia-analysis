"""The legislation menu: every register item marked against the productivity impact framework, with summary
statistics for the industries it affects.

One self-contained page (``index.html`` on the website, ``alicia explorer`` on its own). Filters include the
framework's drivers ("main driver" tags), the overall mark, the kind of item (reform, existing setting,
non-legislative barrier), jurisdiction, reach, status (including repealed or replaced) and the department or agency
responsible, and the complexity tags of the regulatory regimes an item belongs to (duplicative, inconsistent across
states, unclear guidance and others; DECISIONS E-96). Views: a list, a scorecard of every item's marks by driver, a
timeline of reforms, recommendations, and industries (every ANZSIC class with the regimes it faces). Items that share a
family (one policy in several jurisdictions) appear as one row under a group name that says what the issue is across
them, and expand to each jurisdiction's item (DECISIONS E-99). Each item opens
with its assessment (only the drivers it affects; each opens to its reason), then collapsible sections: its regimes
(with a diagram of which tiers of government do what, and where they overlap), recommendations, who is responsible, a
timeline of its changes, its industries' statistics, and its sources. Secondary filters, explanations and the page's
method notes sit behind a "More filters" dropdown, "i" buttons and folds, and no text is set below 13px (owner request,
29 October 2026, DECISIONS E-98).

The econometric evaluations that the menu used to show are kept, unchanged, in the econometric archive
(``menu/archive.py``; DECISIONS E-75, E-87).
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .. import anzsic
from ..register import framework
from ..register.bodies import BODY_TYPE_LABELS, Body, load_bodies
from ..register.evaluation import Evaluation, current_evaluation
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
from ..register.schema import CHANNEL_LABELS, ROLE_LABELS, ChangeRecord
from ..register.timeline import changed_by_index, changes_list, ended_dict, timeline
from ..timing import timing
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


def assessment_dict(record: ChangeRecord) -> dict | None:
    a = record.assessment
    if a is None:
        return None
    return a.model_dump(mode="json") | {"total": a.total, "rating": a.rating, "mixed": a.mixed}


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


def groups_dict(records: list[ChangeRecord], families: dict[str, Family]) -> dict:
    """Families of two or more items, each shown in the menu as one expandable row under its group name."""
    members: dict[str, list[str]] = {}
    for r in records:
        if r.family:
            members.setdefault(r.family, []).append(r.id)
    return {
        f: {
            "title": families[f].title if f in families else FAMILY_LABELS.get(f, _humanise(f)),
            "summary": families[f].summary if f in families else None,
            "members": ids,
        }
        for f, ids in members.items()
        if len(ids) > 1
    }


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
) -> dict:
    """``stats`` defaults to the committed panels (``IndustryStats.load``), ``bodies`` to the committed registry
    (``load_bodies``) and ``recommendations``, ``gaps`` and ``regimes`` to the committed ones; pass fixtures in
    tests."""
    stats = IndustryStats.load() if stats is None else stats
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
    evals = {e.id: e for e in evaluations or []}
    archived = current_evaluation(evaluations or [])
    regimes = load_regimes().regimes if regimes is None else regimes
    families = load_families()[0] if families is None else families
    reg_index = regimes_by_record(regimes)
    out = []
    for r in records:
        eff = r.effective_commencement
        check = checks.get(r.id)
        ev = evals.get(archived.get(r.id, ""))
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
                "archivedEvaluation": {"id": ev.id, "title": ev.title, "finding": ev.finding_label} if ev else None,
                "ended": ended_dict(r),
                "timeline": timeline(r, titles, generated),
                "changes": changes_list(changed.get(r.id, [])),
                "recs": [x.id for x in rec_index.get(r.id, [])],
                "recGap": None if r.id in rec_index else gap_for(r, gaps),
                "regimes": [x.id for x in reg_index.get(r.id, [])],
                "complexity": live_tags(reg_index.get(r.id, [])),
            }
        )
        data["industries"] = [{**i, "division": anzsic.division(i["anzsic"])} for i in data["industries"]]
        out.append(data)
    return {
        "generated": (generated or dt.date.today()).isoformat(),
        "records": out,
        "framework": framework.as_dict(),
        "channels": [{"id": k, "label": v} for k, v in CHANNEL_LABELS.items()],
        "familyLabels": {f: FAMILY_LABELS.get(f, _humanise(f)) for f in {r.family for r in records if r.family}},
        "groups": groups_dict(records, families),
        "bodies": bodies_dict(records, bodies, {b for x in rec_dicts for b in x["actors"]}),
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
        "archivedEvaluations": len(evaluations or []),
    }


def build_explorer(
    records: list[ChangeRecord],
    out: Path,
    dates_report: Path | None = None,
    standalone: bool = False,
    evaluations: list[Evaluation] | None = None,
    pages: tuple | None = None,
) -> Path:
    """Write the menu to ``out``. ``pages`` is the site navigation (``growth.PAGES`` and the costing tab, when
    built); left out, the page is written with the navigation of a full site build."""
    from .growth import PAGES, render

    report = json.loads(dates_report.read_text("utf-8")) if dates_report and dates_report.exists() else None
    payload = build_payload(records, report, evaluations=evaluations)
    out.write_text(render("explorer.html", payload, "index.html", standalone, pages or PAGES), encoding="utf-8")
    return out
