"""The Industry lens (beta): pick an ANZSIC class and a state, and see the laws that apply to it, marked against the
productivity impact framework and placed by the market position each effect acts through: entrants, small and medium
competitors, and the largest players.

The page is built from the register as it stands, so every requirement or register item added later appears on it
without code changes: requirements (``regulation-register/requirements/``) by their reach, and register items
(``regulation-register/records/``) by their industries. How each is coded is in ``register/competition.py``; the
methods note is ``docs/industry_lens.md``.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

from ..register import competition as C
from ..register.catalogue import default_register_dir
from ..register.framework import DRIVERS, MARK_LABELS
from ..register.requirements import KIND_LABELS, TRIGGER_LABELS, Requirement, load_requirements, reach_classes
from ..register.schema import ChangeRecord

PAGE = ("industry-lens.html", "Industry lens (beta)")
ROOT = Path(__file__).resolve().parents[4]
CLASSES = ROOT / "data" / "processed" / "anzsic" / "anzsic2006_classes.json"
MARKS = ROOT / "data" / "processed" / "anzsic" / "class_marks.csv"
MAP = ROOT / "data" / "processed" / "geo" / "ste_2021_map.json"
STATES = (
    ("NSW", "New South Wales"),
    ("VIC", "Victoria"),
    ("QLD", "Queensland"),
    ("SA", "South Australia"),
    ("WA", "Western Australia"),
    ("TAS", "Tasmania"),
    ("NT", "Northern Territory"),
    ("ACT", "Australian Capital Territory"),
)
CLASS_MARKS = {
    "government": "Mainly government",
    "npish": "Mainly non-profit institutions serving households",
    "households": "Households, not businesses",
}
DEFAULT = ("4511", "NSW")  # cafes and restaurants: a calibration class with laws at every tier
REPO_MAIN = "https://github.com/jabthebeer/Competition-in-Australia-analysis/blob/main/"


def classes() -> list[dict]:
    rows = json.loads(CLASSES.read_text("utf-8"))["rows"]
    marks = {}
    if MARKS.exists():
        with MARKS.open(encoding="utf-8", newline="") as fh:
            marks = {r["class"]: r["mark"] for r in csv.DictReader(fh)}
    return [
        {
            "code": r["class"],
            "name": r["class_name"],
            "division": r["division"],
            "group": f"{r['group']} {r['group_name']}",
            "subdivision": f"{r['subdivision']} {r['subdivision_name']}",
            "definition": r["definition"],
            "mark": CLASS_MARKS.get(marks.get(r["class"], ""), ""),
        }
        for r in rows
    ]


def _compact(value):
    """Drop empty fields (None, empty lists and strings, False) to keep the embedded data small."""
    if isinstance(value, dict):
        # Identity and length tests, not ==, so that 0 (a mark total) is kept while False is dropped.
        return {k: _compact(v) for k, v in value.items() if not (v is None or v is False or v in ([], ""))}
    if isinstance(value, list):
        return [_compact(v) for v in value]
    return value


def divisions() -> dict[str, str]:
    return {r["division"]: r["division_name"] for r in json.loads(CLASSES.read_text("utf-8"))["rows"]}


def _law(law) -> dict:
    return {"title": law.title, "id": law.register_id, "url": str(law.register_url) if law.register_url else None}


def _source(s) -> dict:
    return {"title": s.title, "publisher": s.publisher, "url": str(s.url), "locator": s.locator}


def requirement_row(q: Requirement, settings: dict[str, ChangeRecord]) -> dict:
    # A requirement that names a setting record (the same law in force) stands for it on the page.
    setting = next((r for r in q.records if r in settings), None)
    reach = []
    for r in q.reach:
        cls = reach_classes(r)
        reach.append(
            {
                "classes": "all" if r.scope == "all" and not r.exclude else cls,
                "activities": list(r.activities),
                "condition": r.condition,
                "legalForms": list(r.legal_forms),
                "inStates": list(r.in_states),
            }
        )
    folder = "cth" if q.tier == "cth" else (f"local/{q.lga}" if q.tier == "local" else q.jurisdiction.lower())
    return {
        "id": q.id,
        "type": "requirement",
        "tier": q.tier,
        "jurisdiction": q.jurisdiction,
        "council": q.lga_name,
        "title": q.title,
        "what": q.what,
        "kind": KIND_LABELS[q.kind],
        "triggers": [TRIGGER_LABELS[t.type] for t in q.triggers],
        "laws": [_law(law) for law in q.laws],
        "source": _source(q.sources[0]),
        "reach": reach,
        "marks": C.placed_marks(q.assessment),
        "framework": C.summary(q.assessment),
        "setting": setting,
        "related": [r for r in q.records if r != setting],
        "reachConfidence": q.confidence,
        "councilsAdminister": q.administered_by_councils,
        "file": f"regulation-register/requirements/{folder}/{q.id}.json",
    }


def record_row(r: ChangeRecord) -> dict:
    first = r.dates.commenced[0].date if r.dates.commenced else None
    return {
        "id": r.id,
        "type": "record",
        "kind": r.kind,
        "tier": "cth" if r.jurisdiction == "CTH" else "state",
        "jurisdiction": r.jurisdiction,
        "title": r.title,
        "what": r.summary,
        "since": first.isoformat() if first else None,
        # An economy-wide item may list no industries: it reaches every class.
        "industries": [{"code": i.anzsic, "exposure": i.exposure} for i in r.industries] or "all",
        "laws": [
            {"title": i.title, "id": i.register_id, "url": str(i.register_url) if i.register_url else None}
            for i in r.instruments
        ],
        "sources": [str(u) for u in r.direction_sources],
        "marks": C.placed_marks(r.assessment) if r.assessment else [],
        "framework": C.summary(r.assessment) if r.assessment else None,
        "file": f"regulation-register/records/{r.id}.json",
    }


def payload(
    records: list[ChangeRecord], requirements: list[Requirement] | None = None, repo_base: str | None = None
) -> dict:
    repo = repo_base or REPO_MAIN
    reqs = requirements if requirements is not None else load_requirements().requirements
    settings = {r.id: r for r in records if r.kind == "setting"}
    live = [r for r in records if r.ended is None]
    rows = [_compact(row) for row in [requirement_row(q, settings) for q in reqs] + [record_row(r) for r in live]]
    geo = json.loads(MAP.read_text("utf-8"))
    return {
        "page": PAGE[1],
        "positions": [
            {
                "id": p,
                "label": C.POSITION_LABELS[p],
                "question": C.POSITION_QUESTIONS[p],
                "drivers": [DRIVERS[d]["short"] for d, ps in C.DRIVER_POSITIONS.items() if p in ps],
            }
            for p in C.POSITIONS
        ],
        "markLabels": {str(k): v for k, v in MARK_LABELS.items()},
        "classes": classes(),
        "divisions": divisions(),
        "states": [{"code": c, "name": n} for c, n in STATES],
        "map": {"viewBox": geo["viewBox"], "areas": geo["areas"], "source": geo["source"], "licence": geo["licence"]},
        "rows": rows,
        "default": {"class": DEFAULT[0], "state": DEFAULT[1]},
        "counts": {
            "requirements": len(reqs),
            "records": len(live),
            "ended": len(records) - len(live),
            "industrySpecific": sum(1 for q in reqs if not any(r.scope == "all" for r in q.reach)),
        },
        "repo": repo,
        "built": dt.date.today().isoformat(),
        "sources": {
            "anzsic": json.loads(CLASSES.read_text("utf-8"))["source"],
            "map": geo["url"],
        },
    }


def default_requirements_dir() -> Path:
    return default_register_dir() / "requirements"


__all__ = ["PAGE", "payload"]
