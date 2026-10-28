"""The legislation menu: every register item marked against the productivity impact framework, with summary
statistics for the industries it affects.

One self-contained page (``index.html`` on the website, ``alicia explorer`` on its own). Filters include the
framework's drivers ("main driver" tags), the overall mark, the kind of item (reform, existing setting,
non-legislative barrier), jurisdiction and reach. Views: a list, a scorecard of every item's marks by driver, and a
timeline of reforms. Each item opens with its assessment, then its industries' statistics, then its sources.

The econometric evaluations that the menu used to show are kept, unchanged, in the econometric archive
(``menu/archive.py``; DECISIONS E-75, E-85).
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .. import anzsic
from ..register import framework
from ..register.evaluation import Evaluation, current_evaluation
from ..register.schema import CHANNEL_LABELS, ChangeRecord
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


def build_payload(
    records: list[ChangeRecord],
    dates_report: list[dict] | None = None,
    generated: dt.date | None = None,
    evaluations: list[Evaluation] | None = None,
    stats: IndustryStats | None = None,
) -> dict:
    """``stats`` defaults to the committed panels (``IndustryStats.load``); pass one built from fixtures in tests."""
    stats = IndustryStats.load() if stats is None else stats
    checks = {d["record_id"]: d for d in dates_report or []}
    evals = {e.id: e for e in evaluations or []}
    archived = current_evaluation(evaluations or [])
    out = []
    for r in records:
        eff = r.effective_commencement
        check = checks.get(r.id)
        ev = evals.get(archived.get(r.id, ""))
        data = r.model_dump(mode="json", exclude={"comparison", "confounders", "price_series", "assessment"})
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
