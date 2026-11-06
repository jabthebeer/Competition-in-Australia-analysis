"""Mark the ANZSIC classes that are mainly government, households or non-profit institutions serving households.

Usage: uv run python scripts/anzsic_class_marks.py

Owner decision (DECISIONS E-115): keep all 506 classes, and mark these rather than drop them. A class is marked on
one of two ABS tests, and the mark records which, quoting the ABS:

1. **Definition.** The class's ABS definition describes units of government: government administration, government
   representation, military defence or central banking.
2. **No ABS business counts.** The ABS publishes no counts for the class in Counts of Australian Businesses (CABEE),
   whose scope excludes "Reserve Bank of Australia", "General Government" and "Non-Profit Institutions Serving
   Households" (CABEE release page, Jul 2021 to Jun 2025). These classes are typed from their definitions:
   government, households, or non-profit institutions serving households.

A class that the ABS does count is not marked on test 2, even if many of its units are public (e.g. 7540 Justice,
7714 Correctional and Detention Services). 6330 Superannuation Funds is missing only from the latest release, so it is
not marked. Reads ``data/processed/anzsic/anzsic2006_classes.json`` and
``data/processed/abs_cabee/cabee_class_state_fy.csv.gz``; writes ``data/processed/anzsic/class_marks.csv``.
"""

from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLASSES = ROOT / "data" / "processed" / "anzsic" / "anzsic2006_classes.json"
CABEE = ROOT / "data" / "processed" / "abs_cabee" / "cabee_class_state_fy.csv.gz"
OUT = ROOT / "data" / "processed" / "anzsic" / "class_marks.csv"
CABEE_SCOPE = (
    "ABS, Counts of Australian Businesses, including Entries and Exits, Jul 2021 to Jun 2025, Methodology: scope "
    '"All actively trading businesses in the Australian market sector. Excluding: Reserve Bank of Australia; General '
    'Government; Non-Profit Institutions Serving Households"'
)
# Test 1: phrases in the ABS definition that describe units of government.
GOVERNMENT_PHRASES = (
    "government policy",
    "units of domestic government",
    "units of foreign governments",
    "units of military defence",
    "central banking functions",
)
# Test 2: the type of each class the ABS doesn't count, from its definition.
UNCOUNTED_TYPE = {
    "7711": "government",
    "7713": "government",
    "9540": "non-profit institutions serving households",
    "9551": "non-profit institutions serving households",
    "9552": "non-profit institutions serving households",
    "9559": "non-profit institutions serving households",
    "9601": "households",
    "9602": "households",
    "9603": "households",
}


def counted_classes() -> set[str]:
    with gzip.open(CABEE, "rt", encoding="utf-8") as f:
        rows = csv.DictReader(f)
        latest = {}
        for r in rows:
            latest.setdefault(r["anzsic"].zfill(4), set()).add(int(r["fy"]))
    return set(latest)


def main() -> None:
    rows = json.loads(CLASSES.read_text("utf-8"))["rows"]
    counted = counted_classes()
    out = []
    for r in rows:
        code, definition = r["class"], r["definition"] or ""
        phrase = next((p for p in GOVERNMENT_PHRASES if p in definition), None)
        uncounted = code not in counted
        if not phrase and not uncounted:
            continue
        if uncounted and code not in UNCOUNTED_TYPE:
            raise ValueError(f"{code} has no ABS business counts but no type is set for it")
        mark = "government" if phrase else UNCOUNTED_TYPE[code]
        tests, basis = [], []
        if phrase:
            tests.append("definition")
            basis.append(f'ABS definition: "{definition}"')
        if uncounted:
            tests.append("no ABS business counts")
            basis.append(f"No counts in CABEE 2007-08 to 2024-25. {CABEE_SCOPE}")
        out.append(
            {
                "class": code,
                "class_name": r["class_name"],
                "mark": mark,
                "tests": "; ".join(tests),
                "basis": " | ".join(basis),
            }
        )
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    by = {}
    for r in out:
        by.setdefault(r["mark"], []).append(r["class"])
    print(f"Wrote {OUT}: {len(out)} classes marked: {by}")


if __name__ == "__main__":
    main()
