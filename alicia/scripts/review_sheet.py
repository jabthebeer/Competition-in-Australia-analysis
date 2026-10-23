"""Write the review sheet for every register record that a current (not archived) evaluation uses.

One row per record: what the record says (dates, sources, instruments, industries, known confounders), how the
evaluations used it (first exposed period, industries or CPI class, comparison states), the automated register check,
and blank review columns for a person (or Claude Cowork) to fill in. docs/cowork_review_guide.md explains the columns
and gives the prompts.

    uv run python scripts/review_sheet.py                    # writes ../docs/review/evaluated_records_review.csv
    uv run python scripts/review_sheet.py --check <file>     # validate a completed sheet before applying it
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

from alicia import anzsic, cpi
from alicia.register.catalogue import load_records
from alicia.register.evaluation import archived, load_evaluations
from alicia.runner.spec import load_all

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "review" / "evaluated_records_review.csv"
REPORT = ROOT / "regulation-register" / "reports" / "effective_dates_2026-10-18.json"

REVIEW_COLUMNS = (
    "check_commencement_date",
    "check_what_commenced",
    "check_source_url",
    "check_quote",
    "date_verdict",
    "industries_verdict",
    "industries_suggested",
    "other_changes_in_window",
    "confidence",
    "reviewer_notes",
)


ALLOWED = {
    "date_verdict": {"agrees", "differs", "unsure"},
    "industries_verdict": {"agrees", "partly", "differs", "unsure"},
    "confidence": {"high", "medium", "low"},
}
OFFICIAL = (
    "legislation.",
    ".gov.au",
    "gazette",
    "abs.gov.au",
)


def check(path: Path) -> list[str]:
    """Problems in a completed sheet: changed left-hand columns, bad values, missing sources or quotes."""
    with OUT.open(encoding="utf-8-sig") as f:
        original = {r["record_id"]: r for r in csv.DictReader(f)}
    with path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header, rows = reader.fieldnames or [], list(reader)
    problems = []
    if header != list(next(iter(original.values()))):
        problems.append("columns differ from the original sheet (renamed, reordered, added or removed)")
    if {r.get("record_id") for r in rows} != set(original):
        problems.append("rows differ from the original sheet (records added or removed)")
    for r in rows:
        rid, orig = r.get("record_id", "?"), original.get(r.get("record_id"))
        if orig:
            changed = [k for k in orig if k not in REVIEW_COLUMNS and r.get(k) != orig[k]]
            if changed:
                problems.append(f"{rid}: non-review columns changed: {', '.join(changed)}")
        for col, ok in ALLOWED.items():
            if r.get(col, "").strip().lower() not in ok:
                problems.append(f"{rid}: {col} must be one of {sorted(ok)} (got {r.get(col)!r})")
        if r.get("date_verdict") in ("agrees", "differs"):
            try:
                dt.date.fromisoformat(r.get("check_commencement_date", ""))
            except ValueError:
                problems.append(f"{rid}: check_commencement_date must be YYYY-MM-DD")
            url = r.get("check_source_url", "").lower()
            if not any(k in url for k in OFFICIAL):
                problems.append(f"{rid}: check_source_url does not look official ({url or 'blank'})")
            if not r.get("check_quote", "").strip():
                problems.append(f"{rid}: check_quote is blank")
        if r.get("date_verdict") == "differs" and not r.get("reviewer_notes", "").strip():
            problems.append(f"{rid}: a differing date needs reviewer_notes")
        if r.get("industries_verdict") in ("partly", "differs") and not r.get("industries_suggested", "").strip():
            problems.append(f"{rid}: industries_verdict {r['industries_verdict']} needs industries_suggested")
    return problems


def fy(year: int) -> str:
    return f"{year - 1}-{str(year)[2:]}"


def period(value) -> str:
    return value if isinstance(value, str) else fy(int(value))


def code_name(code: str) -> str:
    cls = next((c for c in cpi.classes() if c["code"] == code), None)
    if cls:
        return f"CPI {code} {cls['name']}"
    try:
        name = anzsic.name(code)
    except (KeyError, ValueError):
        name = None
    if name:
        return f"{code} {name}"
    return f"{code} (ABS Retail Trade series)" if code.startswith("RT") else code


def usage(records: dict) -> dict[str, list[dict]]:
    """Record id -> how each specification case used it: first exposed period, industries, comparison."""
    out: dict[str, list[dict]] = {}
    specs, _ = load_all()
    for spec in specs:
        cases = spec.cases or [{"id": spec.evaluations[0] if spec.evaluations else spec.id, "records": spec.records}]
        for case in cases:
            outcomes = case.get("outcomes") or []
            for rid in case["records"]:
                if rid not in records:
                    continue
                state = records[rid].jurisdiction
                first, codes, controls = [], [], set()
                for o in outcomes:
                    kind = "prices" if o["kind"] == "price" else o["key"]
                    for c in o["cohorts"]:
                        if state in c["treated"] or state == "CTH":
                            first.append(f"{period(c['first_post'])} to {period(c['last_post'])} ({kind})")
                            controls |= set(c["controls"])
                        elif state in c["controls"]:
                            first.append(
                                f"comparison state for {period(c['first_post'])} to {period(c['last_post'])} ({kind})"
                            )
                    codes += [o["code"]] if o["kind"] == "price" else list(o["classes"])
                if not outcomes:  # the older single-design specifications
                    for o in spec.outcomes:
                        codes += list(o.industries or ())
                        if o.window:
                            w = o.window
                            first.append(
                                f"from {w.event}, {w.pre} periods before and {w.post} after ({o.key}, {o.frequency})"
                            )
                out.setdefault(rid, []).append(
                    {
                        "case": case["id"],
                        "first": "; ".join(dict.fromkeys(first)),
                        "codes": "; ".join(code_name(c) for c in dict.fromkeys(codes)),
                        "controls": ", ".join(sorted(controls)),
                    }
                )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", type=Path, help="validate a completed review sheet instead of writing one")
    args = ap.parse_args()
    if args.check:
        problems = check(args.check)
        print("\n".join(problems) if problems else f"{args.check}: no problems")
        sys.exit(1 if problems else 0)
    records = {r.id: r for r in load_records().records}
    evals = load_evaluations().evaluations
    gone = archived(evals)
    current = [e for e in evals if e.id not in gone]
    by_record: dict[str, list[str]] = {}
    for e in current:
        for rid in e.records:
            by_record.setdefault(rid, []).append(e.id)
    report = {r["record_id"]: r for r in json.loads(REPORT.read_text("utf-8"))}
    used = usage(records)
    current_ids = {e.id for e in current}
    rows = []
    for rid in sorted(by_record, key=lambda r: (records[r].family or "", records[r].jurisdiction, r)):
        r = records[rid]
        d = r.dates
        primary = next((c for c in d.commenced if c.primary), d.commenced[0] if d.commenced else None)
        others = [f"assent or made {d.assent_or_made.date}"] if d.assent_or_made and d.assent_or_made.date else []
        others += [f"{c.date}: {c.what}" for c in d.commenced if c is not primary]
        rep = report.get(rid, {})
        uses = [u for u in used.get(rid, []) if u["case"] in current_ids]
        rows.append(
            {
                "record_id": rid,
                "jurisdiction": r.jurisdiction,
                "title": r.title,
                "family": r.family or "",
                "evaluations": "; ".join(by_record[rid]),
                "recorded_commencement": primary.date.isoformat() if primary and primary.date else "",
                "recorded_what": primary.what if primary else "",
                "recorded_source": primary.source if primary else "",
                "other_dates": "; ".join(others),
                "instruments": " | ".join(
                    f"{i.title} ({i.register_id or 'no id'}) {i.register_url or ''}".strip() for i in r.instruments
                ),
                "record_industries": "; ".join(f"{i.anzsic} {i.name}" for i in r.industries),
                "auto_check": f"{rep.get('status', 'not checked')}: {'; '.join(rep.get('issues', []))}".rstrip(": "),
                "evaluation_window": " || ".join(f"{u['case']}: {u['first']}" for u in uses if u["first"]),
                "evaluation_industries": " || ".join(f"{u['case']}: {u['codes']}" for u in uses if u["codes"]),
                "evaluation_comparison": " || ".join(f"{u['case']}: {u['controls']}" for u in uses if u["controls"]),
                "record_confounders": "; ".join(r.confounders),
                **dict.fromkeys(REVIEW_COLUMNS, ""),
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} records)")


if __name__ == "__main__":
    main()
