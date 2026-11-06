"""``alicia costing-register``: the register of changes as the Policy costing tab's reference class.

One entry per reform (sorted by id; existing settings and non-legislative barriers are not past changes, so they are
left out): its hypothesis (direction, rationale and sources), the OIA competition
channels, the industries it affects, its primary commencement date, its review status, and, where it has been
evaluated, the evaluation shown for it (the latest one that is not archived; otherwise the latest archived one,
flagged). Written to ``data/processed/costing/register.json``; deterministic (no timestamps).
"""

from __future__ import annotations

from pathlib import Path

from ..register.evaluation import Evaluation, archived, current_evaluation, recency
from ..register.schema import CHANNEL_LABELS, ChangeRecord
from . import base

SCHEMA = "alicia-costing-register"


def default_path() -> Path:
    return base.costing_dir() / "register.json"


def _evaluation_for(records: list[ChangeRecord], evaluations: list[Evaluation]) -> dict[str, tuple[Evaluation, bool]]:
    by_id = {e.id: e for e in evaluations}
    gone = archived(evaluations)
    out = {rid: (by_id[eid], False) for rid, eid in current_evaluation(evaluations).items()}
    for ev in sorted(evaluations, key=recency):  # records evaluated only by archived evaluations
        if ev.id in gone:
            for rid in ev.records:
                if rid not in out or out[rid][1]:
                    out[rid] = (ev, True)
    return out


def entry(rec: ChangeRecord, ev: tuple[Evaluation, bool] | None) -> dict:
    eff = rec.effective_commencement
    evaluation = None
    if ev is not None:
        e, is_archived = ev
        evaluation = {
            "id": e.id,
            "verdict": e.verdict,
            "grade": e.grade,
            "finding": e.finding_label,
            "evaluated_on": e.evaluated_on.isoformat(),
            "archived": is_archived,
            "page": f"evaluation-{e.id}.html",
        }
    return {
        "id": rec.id,
        "title": rec.title,
        "jurisdiction": rec.jurisdiction,
        "family": rec.family,
        "direction": rec.direction,
        "direction_rationale": rec.direction_rationale,
        "direction_sources": [str(u) for u in rec.direction_sources],
        "channels": list(rec.channels),
        "industries": [{"anzsic": i.anzsic, "name": i.name, "exposure": i.exposure} for i in rec.industries],
        "commencement": eff.date.isoformat() if eff else None,
        "commencement_is_primary": bool(eff and eff.primary),
        "review_status": rec.review.status,
        "evaluation": evaluation,
    }


def export(records: list[ChangeRecord], evaluations: list[Evaluation]) -> dict:
    records = [r for r in records if r.kind == "reform"]
    evs = _evaluation_for(records, evaluations)
    return {
        "schema": SCHEMA,
        "version": base.VERSION,
        "channels": dict(CHANNEL_LABELS),
        "notes": (
            "Directions are hypotheses, not findings. Records are drafts until reviewed (review_status). "
            "commencement is the primary commencement, or the earliest when none is marked primary "
            "(commencement_is_primary). Evaluation verdicts are provisional; 'page' is the evaluation's page on "
            "the ALICIA site."
        ),
        "records": [entry(r, evs.get(r.id)) for r in sorted(records, key=lambda r: r.id)],
    }


def write(records: list[ChangeRecord], evaluations: list[Evaluation], path: Path | None = None) -> Path:
    return base.write_json(path or default_path(), export(records, evaluations))
