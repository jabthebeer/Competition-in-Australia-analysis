"""Phase 6 of the levers re-evaluation (DECISIONS E-179): laws in the Open Australian Legal Corpus whose text
signals a cap on numbers, an exclusive right, an ownership limit, a price control or a business ban, and which the
register does not yet cite. A shortlist for reading, not a finding: every candidate is checked against the current
law before anything is drafted.

Reads the corpus downloaded to data/raw/oalc/ (not committed; see data/SOURCES.md). Run from alicia/:
    uv run python scripts/levers_gap_screen.py
"""

import csv
import glob
import gzip
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed" / "legislation" / "levers_gap_screen.csv"

P = {
    "cap": [
        r"\bmoratorium\b",
        r"(?:maximum|total) number of (?:licences|licenses|permits|authorities|authorisations|entitlements|gaming machines|poker machines|taxi[a-z ]{0,20}|plates|venues|pharmacies)",  # noqa: E501
        r"(?:cap|limit|ceiling) on the (?:total )?number of",
        r"must not (?:grant|issue) (?:more than|any further|a further)",
        r"no (?:further|more|new) (?:licences|licenses|permits|authorities|authorisations) (?:may|shall|are to|can) be (?:granted|issued)",  # noqa: E501
    ],
    "exclusive": [
        r"exclusive (?:right|licence|license|period|wagering|lotter(?:y|ies)|casino|operat)",
        r"exclusivity (?:period|arrangement|agreement)",
        r"(?:only|sole) (?:casino|wagering|lotter(?:y|ies)|totalisator) licen[cs]e",
    ],
    "ownership": [
        r"(?:unacceptable|prohibited) (?:shareholding|ownership|control) situation",
        r"(?:more than|exceeds?|exceeding) \d+(?:\.\d+)? ?(?:per ?cent|%) of the (?:total )?(?:voting|issued shares|shares|share capital)",  # noqa: E501
        r"foreign (?:ownership|persons?)[^.]{0,80}\d+ ?(?:per ?cent|%)",
        r"must not (?:hold|have|acquire) (?:an interest|interests|a financial interest|a direct or indirect interest) in more than",  # noqa: E501
    ],
    "price": [
        r"maximum (?:fares?|fees?|prices?|charges?)[^.]{0,80}(?:determined|fixed|prescribed|set by|approved)",
        r"(?:price|fare)s? (?:determination|order|control)",
        r"fix(?:ing)? (?:the )?(?:maximum |minimum )?(?:prices?|fares)",
        r"minimum (?:unit )?price",
    ],
    "ban": [
        r"must not carry on (?:a|the) business of",
        r"(?:is|are) prohibited from carrying on",
    ],
}
RX = {k: [re.compile(p, re.I) for p in ps] for k, ps in P.items()}


def norm(t):
    t = re.sub(r"\((?:cth|nsw|vic|qld|sa|wa|tas|act|nt)\)", "", t or "", flags=re.I)
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


cited = set()
for p in (ROOT / "regulation-register/records").glob("*.json"):
    for i in json.loads(p.read_text("utf-8")).get("instruments", []):
        cited.add(norm(i["title"]))
for p in (ROOT / "regulation-register/requirements").rglob("*.json"):
    for law in json.loads(p.read_text("utf-8")).get("laws", []):
        cited.add(norm(law["title"]))

rows = []
for f in sorted(glob.glob(str(ROOT / "data/raw/oalc/*.jsonl.gz"))):
    if "norfolk" in f:
        continue
    with gzip.open(f, "rt", encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            title = d.get("citation") or ""
            if norm(title) in cited:
                continue
            text = d.get("text") or ""
            hits = defaultdict(list)
            for kind, rxs in RX.items():
                for rx in rxs:
                    for m in rx.finditer(text):
                        if len(hits[kind]) < 3:
                            a, b = max(0, m.start() - 140), min(len(text), m.end() + 160)
                            hits[kind].append(" ".join(text[a:b].split()))
                        else:
                            break
            if hits:
                score = sum(len(v) for k, v in hits.items() if k != "ban") + (1 if hits.get("ban") else 0)
                rows.append(
                    {
                        "jurisdiction": d["jurisdiction"],
                        "type": d["type"],
                        "title": title,
                        "url": d.get("url", ""),
                        "kinds": " ".join(sorted(hits)),
                        "score": score,
                        "snippets": " || ".join(f"[{k}] {s}" for k, v in hits.items() for s in v[:2]),
                    }
                )
rows.sort(key=lambda r: (-r["score"], r["jurisdiction"], r["title"]))
with OUT.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(len(rows), "laws with a signal;", sum(1 for r in rows if r["type"] == "primary_legislation"), "Acts")
