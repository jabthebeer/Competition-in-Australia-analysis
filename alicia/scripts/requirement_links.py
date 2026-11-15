"""Write the class link table: one row per ANZSIC class and requirement it reaches, across every tier.

Usage: uv run python scripts/requirement_links.py

Reads regulation-register/requirements/ (``alicia.register.requirements``) and writes
``data/processed/legislation/links.csv.gz`` (the table) and ``links_summary.csv`` (requirements per class and
jurisdiction, by tier). Marked classes (data/processed/anzsic/class_marks.csv) carry their mark.
"""

from __future__ import annotations

import csv
import gzip
from collections import Counter
from pathlib import Path

from alicia.register.requirements import LINK_FIELDS, links, load_requirements
from alicia.register.schema import STATES

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed" / "legislation"
MARKS = ROOT / "data" / "processed" / "anzsic" / "class_marks.csv"


def main() -> None:
    result = load_requirements()
    if result.problems:
        raise SystemExit("\n".join(result.problems))
    rows = links(result.requirements)
    marks = {r["class"]: r["mark"] for r in csv.DictReader(MARKS.open(encoding="utf-8"))} if MARKS.exists() else {}
    for r in rows:
        r["class_mark"] = marks.get(r["class"], "")
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / "links.csv.gz", "wt", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[*LINK_FIELDS, "class_mark"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["class"], r["tier"], r["jurisdiction"], r["requirement"])))
    # Requirements reaching each class in each state: Commonwealth ones that reach the state, plus the state's own.
    # A requirement with several reaches (companies everywhere, unincorporated employers in some states) counts once.
    seen = {
        (r["class"], s, r["tier"], r["requirement"])
        for r in rows
        for s in (STATES if r["applies_in"] == "all" else [x.strip() for x in r["applies_in"].split("|")])
    }
    count: Counter = Counter((c, s, t) for c, s, t, _ in seen)
    classes = sorted({r["class"] for r in rows})
    with (OUT / "links_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["class", "state", "commonwealth", "state_or_territory", "council", "total"])
        for c in classes:
            for s in STATES:
                n = [count[(c, s, t)] for t in ("cth", "state", "local")]
                w.writerow([c, s, *n, sum(n)])
    print(f"{len(rows):,} links from {len(result.requirements)} requirements, {len(classes)} classes")


if __name__ == "__main__":
    main()
