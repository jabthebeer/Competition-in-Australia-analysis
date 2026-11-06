"""Each register item's timeline: its own dates (announced, assent or made, commenced), then the later changes in
its ``history`` (amendments, easings, repeals), and the earlier items it changed in turn. Owner request,
28 October 2026 (DECISIONS E-94)."""

from __future__ import annotations

import datetime as dt

from .schema import HISTORY_LABELS, ChangeRecord


def changed_by_index(records: list[ChangeRecord]) -> dict[str, list[tuple[ChangeRecord, str]]]:
    """For each record id, the records whose history says this record changed them, with the kind of change."""
    out: dict[str, list[tuple[ChangeRecord, str]]] = {}
    for r in records:
        for h in r.history:
            if h.record:
                out.setdefault(h.record, []).append((r, h.kind))
    return out


def timeline(record: ChangeRecord, titles: dict[str, str], today: dt.date | None = None) -> list[dict]:
    """Dated events, oldest first. ``titles`` maps record ids to titles (for linked records). Events after ``today``
    are marked ``upcoming``."""
    today = today or dt.date.today()
    d = record.dates
    events = []

    def add(date, kind, label, what, source, linked=None, own=True):
        events.append(
            {
                "date": date.isoformat(),
                "kind": kind,
                "label": label,
                "what": what,
                "source": str(source) if source else None,
                "record": linked,
                "recordTitle": titles.get(linked) if linked else None,
                "own": own,
                "upcoming": date > today,
            }
        )

    if d.announced.date:
        add(d.announced.date, "announced", "Announced", "Announced.", d.announced.source)
    if d.assent_or_made.date:
        add(d.assent_or_made.date, "made", "Assent or made", "Law passed or instrument made.", d.assent_or_made.source)
    for c in d.commenced:
        add(c.date, "commenced", "Commenced", c.what, c.source)
    for h in record.history:
        add(h.date, h.kind, HISTORY_LABELS[h.kind], h.what, h.source, h.record, own=False)
    order = {"announced": 0, "made": 1, "commenced": 2}
    events.sort(key=lambda e: (e["date"], order.get(e["kind"], 3)))
    return events


def changes_list(changes: list[tuple[ChangeRecord, str]]) -> list[dict]:
    """The earlier items a record changed (from ``changed_by_index``), for the menu."""
    return [{"record": r.id, "title": r.title, "kind": k, "label": HISTORY_LABELS[k]} for r, k in changes]


def ended_dict(record: ChangeRecord) -> dict | None:
    e = record.ended
    if e is None:
        return None
    return {"date": e.date.isoformat(), "kind": e.kind, "label": HISTORY_LABELS[e.kind], "what": e.what}


__all__ = ["changed_by_index", "changes_list", "ended_dict", "timeline"]
