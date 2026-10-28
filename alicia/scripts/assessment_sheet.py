"""Write the review sheet of every register item's framework assessment, for a person (or Claude Cowork) to check.

One row per item: what it is, its marks on each driver with the reasons, the overall mark, main driver, reach and
confidence, and blank review columns. The left-hand columns come from the records; a reviewer fills in only the
review columns, and a completed sheet is checked before any change is applied to the records.

    uv run python scripts/assessment_sheet.py                 # writes ../docs/review/framework_assessments_review.csv
    uv run python scripts/assessment_sheet.py --check         # the committed sheet matches the records
    uv run python scripts/assessment_sheet.py --check <file>  # validate a completed sheet before applying it
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

from alicia.register import framework as fw
from alicia.register.catalogue import load_records

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "review" / "framework_assessments_review.csv"
REVIEW_COLUMNS = ("review_verdict", "marks_suggested", "main_driver_suggested", "sources_checked", "reviewer_notes")
ALLOWED = {"review_verdict": {"agrees", "partly", "differs", "unsure"}}


def rows() -> list[dict]:
    out = []
    for r in sorted(load_records().records, key=lambda r: (r.kind, r.family or "~", r.id)):
        a = r.assessment
        row = {
            "record_id": r.id,
            "kind": r.kind,
            "jurisdiction": r.jurisdiction,
            "title": r.title,
            "family": r.family or "",
            "overall_mark": f"{a.total:+d}" if a else "",
            "rating": fw.RATING_LABELS[a.rating] if a else "",
            "main_driver": a.main_driver if a else "",
            "reach": a.reach if a else "",
            "confidence": a.confidence if a else "",
        }
        for d in fw.DRIVERS:
            row[d] = f"{a.mark(d):+d}" if a and a.mark(d) else "0"
        row["reasons"] = " | ".join(f"{m.driver} {m.mark:+d}: {m.reason}" for m in a.marks) if a else ""
        row["summary"] = a.summary if a else ""
        row["sources"] = " ".join(str(u) for u in (*r.direction_sources, *(a.evidence if a else ())))
        row.update({c: "" for c in REVIEW_COLUMNS})
        out.append(row)
    return out


def text() -> str:
    data = rows()
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(data[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(data)
    return buf.getvalue()


def check(path: Path | None) -> list[str]:
    """Problems: the committed sheet out of date (no path), or a completed sheet that changed the record columns."""
    if path is None:
        if not OUT.exists() or OUT.read_text("utf-8") != text():
            return [f"{OUT.relative_to(ROOT)} is out of date: run uv run python scripts/assessment_sheet.py"]
        return []
    current = {r["record_id"]: r for r in rows()}
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header, filled = reader.fieldnames or [], list(reader)
    problems = []
    if header != list(next(iter(current.values()))):
        problems.append("columns differ from the sheet (renamed, reordered, added or removed)")
    for r in filled:
        rid, orig = r.get("record_id", "?"), current.get(r.get("record_id"))
        if orig is None:
            problems.append(f"{rid}: not in the register")
            continue
        changed = [k for k in orig if k not in REVIEW_COLUMNS and r.get(k) != orig[k]]
        if changed:
            problems.append(f"{rid}: non-review columns changed: {', '.join(changed)}")
        verdict = r.get("review_verdict", "").strip().lower()
        if verdict and verdict not in ALLOWED["review_verdict"]:
            problems.append(f"{rid}: review_verdict must be one of {sorted(ALLOWED['review_verdict'])}")
        if verdict in ("partly", "differs") and not r.get("reviewer_notes", "").strip():
            problems.append(f"{rid}: say why in reviewer_notes")
    return problems


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--check", nargs="?", const="", default=None, help="check the committed sheet, or a completed one")
    args = p.parse_args(argv)
    if args.check is not None:
        problems = check(Path(args.check) if args.check else None)
        for x in problems:
            print(x)
        print(f"{len(problems)} problem(s)")
        return 1 if problems else 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text(), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
