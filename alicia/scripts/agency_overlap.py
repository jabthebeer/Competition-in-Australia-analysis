"""Regulatory complexity from who administers each requirement: agencies per requirement and per ANZSIC class, and
where administration overlaps (DECISIONS E-148; methods rule 13).

Writes to data/processed/legislation/:
- requirement_agencies.csv: one row per requirement and body, with the body's function and tier, and whether that
  function is shared with another body (an overlap);
- agencies_by_class.csv: for each class and state, the requirements reaching it, the distinct bodies a business
  there deals with, how many requirements involve more than one body, and how many have overlapping functions or
  span the Commonwealth and the states.

A requirement with no administration entries falls back on its administered_by bodies (function unknown). Counts
are of bodies named in the register, not of every agency a business may meet.

Usage (in alicia/): uv run python scripts/agency_overlap.py
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from alicia.register.catalogue import default_register_dir
from alicia.register.regimes import BUSINESS_FACING
from alicia.register.requirements import links, load_requirements

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed" / "legislation"
STATES = ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"]


def main() -> None:
    result = load_requirements()
    if result.problems:
        raise SystemExit("\n".join(result.problems))
    bodies = {b["id"]: b for b in json.loads((default_register_dir() / "bodies.json").read_text(encoding="utf-8"))}
    reqs = {q.id: q for q in result.requirements}

    def parties(q) -> list[tuple[str, str, str]]:
        """(who, function, tier) for each body with a part in the requirement."""
        if q.administration:
            return [(a.who, a.function, a.tier) for a in q.administration]
        return [(bodies[b]["name"] if b in bodies else b, "", q.tier) for b in q.administered_by]

    rows = []
    for q in result.requirements:
        counts: dict[str, int] = defaultdict(int)
        for a in q.administration:
            counts[a.function] += 1
        for who, fn, tier in parties(q):
            rows.append(
                {
                    "requirement": q.id,
                    "jurisdiction": q.jurisdiction,
                    "regime": q.regime or "",
                    "who": who,
                    "function": fn,
                    "tier": tier,
                    "function_shared": "yes" if fn and counts[fn] > 1 else "",
                    "business_facing": "yes" if fn in BUSINESS_FACING else ("" if fn else "unknown"),
                    "bodies_in_requirement": len({p[0] for p in parties(q)}),
                }
            )
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "requirement_agencies.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # Per class and state: Commonwealth requirements that reach the state, plus the state's own (councils excluded).
    seen = set()
    for r in links(result.requirements):
        if r["tier"] == "local":
            continue
        for s in STATES if r["applies_in"] == "all" else [x.strip() for x in r["applies_in"].split("|")]:
            seen.add((r["class"], s, r["requirement"]))
    agg: dict[tuple[str, str], dict] = defaultdict(
        lambda: {
            "reqs": set(),
            "who": set(),
            "who_cth": set(),
            "who_state": set(),
            "multi": 0,
            "overlap": 0,
            "rules": 0,
            "tiers": 0,
        }
    )
    for c, s, rid in seen:
        q, a = reqs[rid], agg[(c, s)]
        a["reqs"].add(rid)
        ps = parties(q)
        for who, _fn, tier in ps:
            a["who"].add(who)
            (a["who_cth"] if tier == "cth" else a["who_state"]).add(who)
        a["multi"] += len({p[0] for p in ps}) > 1
        a["overlap"] += bool(q.overlaps())
        a["rules"] += bool(q.overlaps(business_facing=False)) and not q.overlaps()
        a["tiers"] += len({p[2] for p in ps}) > 1
    with (OUT / "agencies_by_class.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "class",
                "state",
                "requirements",
                "bodies",
                "commonwealth_bodies",
                "state_bodies",
                "requirements_with_several_bodies",
                "requirements_with_overlapping_functions",
                "requirements_with_rules_set_by_several_bodies_only",
                "requirements_spanning_tiers",
            ]
        )
        for (c, s), a in sorted(agg.items()):
            w.writerow(
                [
                    c,
                    s,
                    len(a["reqs"]),
                    len(a["who"]),
                    len(a["who_cth"]),
                    len(a["who_state"]),
                    a["multi"],
                    a["overlap"],
                    a["rules"],
                    a["tiers"],
                ]
            )
    n_adm = sum(1 for q in result.requirements if q.administration)
    n_over = sum(1 for q in result.requirements if q.overlaps())
    n_rules = sum(1 for q in result.requirements if q.overlaps(business_facing=False) and not q.overlaps())
    print(
        f"{len(rows)} requirement-body rows; {n_adm} requirements with administration entries, {n_over} with "
        f"overlapping business-facing functions, {n_rules} more with rules set by several bodies; "
        f"{len(agg)} class-state cells"
    )


if __name__ == "__main__":
    main()
