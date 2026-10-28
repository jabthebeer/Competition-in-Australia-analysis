"""Print Markdown tables summarising the register's framework assessments, for docs/register_review_framework.md.

Counts are given for items (one per jurisdiction) and for policy units (a family of items of one kind counted once),
because a national scheme adopted by eight jurisdictions is eight items but one policy choice.

    uv run python scripts/register_summary.py
"""

from __future__ import annotations

from collections import Counter

from alicia.menu.archive import FAMILY_LABELS
from alicia.register import framework as fw
from alicia.register.catalogue import load_records


def table(header: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


def main() -> None:
    records = load_records().records
    units: dict[tuple, list] = {}
    for r in records:
        units.setdefault((r.family or r.id, r.kind), []).append(r)
    # One unit per family: its members' most common main driver and median overall mark.
    fam_rows = []
    for key, members in units.items():
        drivers = Counter(m.assessment.main_driver for m in members)
        totals = sorted(m.assessment.total for m in members)
        fam_rows.append((key, members, drivers.most_common(1)[0][0], totals[len(totals) // 2]))

    kinds = Counter(r.kind for r in records)
    by_kind = ", ".join(f"{n} {fw.KINDS[k]['label'].lower()}" for k, n in kinds.items())
    print(
        f"**Items:** {len(records)} ({by_kind}); **policy units** (a family of one kind counted once): {len(units)}.\n"
    )

    print("**Main driver by overall band (items; policy units in brackets)**\n")
    bands = [k for _, k, _ in fw.RATINGS]
    rows = []
    for d, spec in fw.DRIVERS.items():
        row = [spec["label"]]
        for b in bands:
            n = sum(1 for r in records if r.assessment.main_driver == d and r.assessment.rating == b)
            u = sum(1 for _, _, md, t in fam_rows if md == d and fw.rating(t) == b)
            row.append(f"{n} ({u})" if n or u else "")
        n_all = sum(1 for r in records if r.assessment.main_driver == d)
        row.append(f"{n_all} ({sum(1 for _, _, md, _ in fam_rows if md == d)})")
        rows.append(row)
    print(table(["Main driver", *[fw.RATING_LABELS[b] for b in bands], "All"], rows) + "\n")

    print("**Every non-zero mark, by driver (items)**\n")
    rows = []
    for d, spec in fw.DRIVERS.items():
        marks = Counter(m.mark for r in records for m in r.assessment.marks if m.driver == d)
        rows.append([spec["label"], *[marks.get(v, "") for v in (-2, -1, 1, 2)], sum(marks.values())])
    print(table(["Driver", "−2", "−1", "+1", "+2", "Marked"], rows) + "\n")

    print("**Kind of item by overall band (items)**\n")
    rows = [
        [
            fw.KINDS[k]["label"],
            *[sum(1 for r in records if r.kind == k and r.assessment.rating == b) or "" for b in bands],
        ]
        for k in fw.KINDS
    ]
    print(table(["Kind", *[fw.RATING_LABELS[b] for b in bands]], rows) + "\n")

    print("**Reach and confidence (items)**\n")
    rows = [
        [
            fw.REACH[k]["label"],
            *[
                sum(1 for r in records if r.assessment.reach == k and r.assessment.confidence == c) or ""
                for c in fw.CONFIDENCE
            ],
        ]
        for k in fw.REACH
    ]
    print(table(["Reach", *[fw.CONFIDENCE[c]["label"] + " confidence" for c in fw.CONFIDENCE]], rows) + "\n")

    print("**The most negative policy units (overall mark −2 or less, reaching a sector or more)**\n")
    order = {"economy-wide": 0, "multi-sector": 1, "sector": 2, "narrow": 3}
    neg = [f for f in fam_rows if f[3] <= -2 and f[1][0].assessment.reach != "narrow"]
    neg.sort(key=lambda f: (f[3], order[f[1][0].assessment.reach], f[0]))

    def name(f) -> str:
        return f[1][0].title if len(f[1]) == 1 else f"{FAMILY_LABELS.get(f[0][0], f[0][0])} ({len(f[1])} items)"

    rows = [
        [
            name(f),
            fw.KINDS[f[1][0].kind]["label"],
            f"{f[3]:+d}",
            fw.DRIVERS[f[2]]["short"],
            fw.REACH[f[1][0].assessment.reach]["label"],
        ]
        for f in neg
    ]
    print(table(["Policy unit", "Kind", "Median mark", "Main driver", "Reach"], rows) + "\n")


if __name__ == "__main__":
    main()
