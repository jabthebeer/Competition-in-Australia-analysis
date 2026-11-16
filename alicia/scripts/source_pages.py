"""Page numbers for quotes from PDF laws, so the Industry lens can open a PDF at the page (``#page=N``).

For every requirement source whose address is a PDF, find the saved text of that PDF (``data/raw/law_text/``, written
by ``law_text.fetch_doc``), whose pages are separated by form feeds, and the page where the quote starts. Writes
``data/processed/legislation/source_pages.csv`` (url, quote_key, page, requirement). A quote not found, or a PDF not
saved, is left out and its link opens the PDF at the start.

    uv run python scripts/source_pages.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import law_sources as S  # noqa: E402
import law_text as L  # noqa: E402

from alicia.register.source_links import PAGES, is_pdf, quote_key  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REQ = ROOT / "regulation-register" / "requirements"


def page_of(raw: str, quote: str) -> int | None:
    """The page (from 1) on which ``quote`` starts, in text whose pages are split by form feeds."""
    starts, pos, flats = [], 0, []
    for i, page in enumerate(raw.split("\f")):
        f = " ".join(page.split())
        if f:
            starts.append((pos, i + 1))
            flats.append(f)
            pos += len(f) + 1
    at = " ".join(flats).find(" ".join(quote.split()))
    if at < 0:
        return None
    return max(p for s, p in starts if s <= at)


def main() -> None:
    rows, missing = {}, 0
    for path in sorted(REQ.rglob("*.json")):
        d = json.loads(path.read_text("utf-8"))
        for s in d["sources"] + [x for r in d.get("reach", []) for x in r["sources"]]:
            url, quote = s["url"], s.get("quote")
            if not quote or not is_pdf(url) or (url, quote_key(quote)) in rows:
                continue
            cache = L.CACHE / f"{S._key(url)}.txt"
            page = page_of(cache.read_text("utf-8"), quote) if cache.exists() else None
            if page:
                rows[(url, quote_key(quote))] = {"url": url, "quote_key": quote_key(quote), "page": page,
                                                 "requirement": d["id"]}
            else:
                missing += 1
    PAGES.parent.mkdir(parents=True, exist_ok=True)
    with PAGES.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["url", "quote_key", "page", "requirement"])
        w.writeheader()
        w.writerows(sorted(rows.values(), key=lambda r: (r["requirement"], r["url"], r["page"])))
    print(f"{len(rows)} PDF quotes placed on a page; {missing} not found or not saved -> {PAGES.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
