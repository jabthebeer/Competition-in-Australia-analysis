"""Fetch each ANZSIC 2006 (Revision 2.0) class's definition, primary activities and exclusions from the ABS.

Usage: uv run python scripts/fetch_anzsic_activities.py [--offline]

The ABS publishes, for every class, a one-paragraph definition, a list of primary activities and a list of
exclusions (activities coded to other classes) on its classification pages. They are not in the Data API
codelist, and the last machine-readable Index of Primary Activities (1292.0.55.004) is for Revision 1.0, so
this script reads the Revision 2.0 class pages:

  https://www.abs.gov.au/statistics/classifications/australian-and-new-zealand-standard-industrial-classification-anzsic/2006-revision-2-0/detailed-classification/<division>/<subdivision>/<group>/<class>

The class list and the hierarchy come from the bundled codelist (``src/alicia/data/anzsic2006.json``, CL_ANZSIC_2006
1.1.0), so the 506 classes are exactly the ABS's. Raw pages go to ``data/raw/abs_anzsic_activities/`` (not
committed); ``--offline`` re-parses them without fetching. Writes:

- ``data/manifests/abs_anzsic_activities.json``: each page's URL, retrieval date, size and SHA-256;
- ``data/processed/anzsic/anzsic2006_classes.json``: one entry per class, with the text exactly as published;
- ``data/processed/anzsic/anzsic2006_classes.csv``: the same, flat (lists joined with " | ").

Content: ABS, CC BY 4.0.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import html
import json
import re
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
CODELIST = ROOT / "alicia" / "src" / "alicia" / "data" / "anzsic2006.json"
RAW = ROOT / "data" / "raw" / "abs_anzsic_activities"
MANIFEST = ROOT / "data" / "manifests" / "abs_anzsic_activities.json"
OUT = ROOT / "data" / "processed" / "anzsic"
BASE = (
    "https://www.abs.gov.au/statistics/classifications/"
    "australian-and-new-zealand-standard-industrial-classification-anzsic/2006-revision-2-0/detailed-classification"
)
LICENCE = "CC BY 4.0, Australian Bureau of Statistics"
PAUSE = 0.5  # seconds between requests


def hierarchy() -> dict[str, dict]:
    codes = {c["code"]: c for c in json.loads(CODELIST.read_text("utf-8"))["codes"]}
    out = {}
    for code, c in codes.items():
        if len(code) != 4:
            continue
        group = codes[c["parent"]]
        sub = codes[group["parent"]]
        div = codes[sub["parent"]]
        out[code] = {
            "division": div["code"],
            "division_name": div["name"],
            "subdivision": sub["code"],
            "subdivision_name": sub["name"],
            "group": group["code"],
            "group_name": group["name"],
            "class": code,
            "class_name": c["name"],
            "url": f"{BASE}/{div['code'].lower()}/{sub['code']}/{group['code']}/{code}",
        }
    return dict(sorted(out.items()))


def _text(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


SECTIONS = {"primaryactivities": "activities", "exclusions/references": "exclusions"}


def _sections(page: str, code: str) -> dict[str, str]:
    """The HTML of each paragraph block, keyed 'activities' or 'exclusions'. Headings vary from page to page
    ("Primary Activities", "Exclusions/ References", a leading zero-width space), so they are compared with case,
    spaces and zero-width spaces removed; any other heading is refused."""
    out = {}
    blocks = re.finditer(
        r'<h3 class="abs-content-title[^"]*">(.*?)</h3>\s*<div class="abs-content[^"]*">(.*?)</div>', page, re.S
    )
    for m in blocks:
        key = re.sub(r"[\s​]+", "", _text(m.group(1))).lower()
        if key not in SECTIONS:
            raise ValueError(f"{code}: unexpected section heading {m.group(1)!r}")
        out[SECTIONS[key]] = m.group(2)
    return out


def parse(page: str, code: str, name: str) -> dict:
    h2 = re.search(r'<h2 class="field-content">\s*(\d{4})\s+(.*?)</h2>', page, re.S)
    if not h2 or h2.group(1) != code:
        raise ValueError(f"{code}: page title not found or for another class")
    title = _text(h2.group(2))
    norm = lambda s: " ".join(s.replace("&", "and").lower().split())  # noqa: E731
    # The page's code is checked above, so a different title is recorded, not refused. The Data API codelist cuts
    # long titles short and words a few differently ("Motor Cycle" for "Motorcycle"); the page's title is used.
    if norm(title) == norm(name):
        status = "same"
    elif norm(title).startswith(norm(name)):
        status = "truncated"
    else:
        status = "differs"
    d = re.search(r'<div class="abs_chapter_description[^"]*">(.*?)</div>', page, re.S)
    definition = _text(d.group(1)) if d else None
    sections = _sections(page, code)
    acts = sections.get("activities")
    activities = [_text(li) for li in re.findall(r"<li>(.*?)</li>", acts, re.S)] if acts else []
    activities = [a.strip("​ ") for a in activities if a.strip("​ ")]
    exc = sections.get("exclusions")
    if exc:
        lead = re.search(r"<p>(.*?)</p>", exc, re.S)
        items = [_text(li) for li in re.findall(r"<li>(.*?)</li>", exc, re.S)]
        exclusions = ([_text(lead.group(1))] if lead else []) + items if items else [_text(exc)]
    else:
        exclusions = []
    return {
        "class_name": title,
        "codelist_title": name,
        "codelist_title_status": status,
        "definition": definition,
        "primary_activities": activities,
        "exclusions": exclusions,
    }


def main(offline: bool = False) -> None:
    classes = hierarchy()
    RAW.mkdir(parents=True, exist_ok=True)
    files, rows = [], []
    with httpx.Client(timeout=60, follow_redirects=True, headers={"User-Agent": "alicia-research/0.1"}) as client:
        for i, (code, c) in enumerate(classes.items(), 1):
            path = RAW / f"{code}.html"
            if not offline and not path.exists():
                for attempt in range(4):
                    try:
                        r = client.get(c["url"])
                        r.raise_for_status()
                        break
                    except httpx.HTTPError:
                        if attempt == 3:
                            raise
                        time.sleep(2 ** (attempt + 1))
                path.write_bytes(r.content)
                time.sleep(PAUSE)
            data = path.read_bytes()
            files.append(
                {
                    "file": str(path.relative_to(ROOT)),
                    "url": c["url"],
                    "retrieved": dt.date.fromtimestamp(path.stat().st_mtime).isoformat(),
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "licence": LICENCE,
                }
            )
            rows.append(c | parse(data.decode("utf-8"), code, c["class_name"]))
            if i % 50 == 0:
                print(f"{i} of {len(classes)}", file=sys.stderr)
    MANIFEST.write_text(json.dumps({"source": "abs_anzsic_activities", "files": files}, indent=1) + "\n", "utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {
        "source": BASE,
        "classification": "ANZSIC 2006 (Revision 2.0), class pages; hierarchy from CL_ANZSIC_2006 1.1.0",
        "licence": LICENCE,
        "retrieved": max(f["retrieved"] for f in files),
        "classes": len(rows),
    }
    (OUT / "anzsic2006_classes.json").write_text(
        json.dumps(meta | {"rows": rows}, indent=1, ensure_ascii=False) + "\n", "utf-8"
    )
    cols = [k for k in rows[0] if k != "url"] + ["url"]
    with (OUT / "anzsic2006_classes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: " | ".join(r[k]) if isinstance(r[k], list) else r[k] for k in cols})
    n_act = sum(len(r["primary_activities"]) for r in rows)
    print(f"Wrote {len(rows)} classes, {n_act} primary activities, to {OUT}")


if __name__ == "__main__":
    main(offline="--offline" in sys.argv)
