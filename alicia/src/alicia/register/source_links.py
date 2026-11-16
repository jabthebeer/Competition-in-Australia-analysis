"""Links to the provision a source quotes, for the hover card on the Industry lens (owner, 15 November 2026).

Each source in the register records the law's address, the provision (its locator, such as "s 15(1)") and the words
quoted. From these a link can open the law at the provision. What works was tested in a browser on 15 November 2026:

- **Section anchors** land on the section: Queensland (``#sec.52``) and Tasmania (``#GS6@EN``). NSW's register uses
  the same system (``#sec.15``) but refuses automated requests, so its form is not tested. No text fragment is added
  here: a phrase can match the table of contents first and pull the page away from the section.
- **Text fragments** (``#:~:text=``) scroll to the words quoted on modern awards and ABLIS pages, but only for a plain
  run of words: clause numbers and list markers such as "(a)" are often not in the page's text, so they are left out.
  The Federal Register of Legislation draws its text after the page loads, so a fragment does not land there; its
  links open the law.
- **PDFs:** the ACT and NT registers send their PDFs as downloads, so a page link has no effect; the card names the
  page instead (``scripts/source_pages.py`` reads it from the saved text). Other PDFs open at the page (``#page=N``).
- **The law's own page** for Western Australia, whose sources are Word documents, and Victoria, whose sources cite the
  in-force page. South Australia's sources are RTF documents, which download as they are.
"""

from __future__ import annotations

import csv
import hashlib
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote as _pct
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[4]
PAGES = ROOT / "data" / "processed" / "legislation" / "source_pages.csv"
# A locator that starts with a section, clause or regulation number: "s 15(1)", "ss 62(1), 71C", "cl 3", "reg 9(1)".
SECTION = re.compile(r"^(?:ss?|cll?|regs?|r)\s+(\d+[A-Z]{0,3})\b")
WA_LAW = re.compile(r"law_[as]\d+")
# What each kind of link does, for the card's link text.
HOW = {
    "section": "Open the law at {where}",
    "words": "Open the source at the words quoted",
    "page": "Open the law at page {page}",
    "law": "Open the law",
    "file": "Download the law",
}
DOWNLOAD_PDFS = ("legislation.act.gov.au", "legislation.nt.gov.au")  # sent as attachments, so #page has no effect
NO_FRAGMENT = ("legislation.gov.au",)  # draws its text after loading, so a fragment does not land
ANCHORED = ("legislation.qld.gov.au", "legislation.nsw.gov.au", "legislation.tas.gov.au")  # #sec.N or #GSN@EN


def section(locator: str | None) -> str | None:
    """The section, clause or regulation number a locator starts with, if any."""
    m = SECTION.match((locator or "").strip())
    return m.group(1) if m else None


def _enc(text: str) -> str:
    # Percent-encode for a text fragment: the dash and comma are part of the fragment's own syntax.
    return _pct(text, safe="").replace("-", "%2D")


WORD = re.compile(r"^[A-Za-z][A-Za-z'’-]*[,;:.]?$")
FRAGMENT_WORDS = 10


def fragment(quote: str) -> str:
    """A text fragment for the words quoted: the longest run of plain words (up to 10, with any comma, colon or full
    stop that follows a word), leaving out clause numbers and list markers, which a page often sets apart."""
    best: list[str] = []
    run: list[str] = []
    for t in quote.split() + [""]:
        if WORD.match(t):
            run.append(t)
            continue
        if len(run) > len(best):
            best = run
        run = []
    return "text=" + _enc(" ".join(best[:FRAGMENT_WORDS]))


def quote_key(quote: str) -> str:
    return hashlib.sha256(" ".join(quote.split()).encode("utf-8")).hexdigest()[:16]


@lru_cache(maxsize=1)
def load_pages() -> dict[tuple[str, str], int]:
    """PDF page numbers by (address, quote key), from ``data/processed/legislation/source_pages.csv``."""
    if not PAGES.exists():
        return {}
    with PAGES.open(encoding="utf-8", newline="") as fh:
        return {(r["url"], r["quote_key"]): int(r["page"]) for r in csv.DictReader(fh)}


def is_pdf(url: str) -> bool:
    low = url.lower()
    return low.endswith(".pdf") or "/pdf/" in low or "/pdf?" in low


def deep_link(url: str, locator: str | None, quote: str | None, law_ids: tuple[str, ...] = ()) -> dict:
    """The link to the provision: ``href``, ``how`` (section, words, page, law or file) and the link's text."""
    host = urlparse(url).netloc.lower().removeprefix("www.")
    sec = section(locator)
    where = (locator or "").split(" (")[0]
    if is_pdf(url):
        page = load_pages().get((url, quote_key(quote))) if quote else None
        if page and host in DOWNLOAD_PDFS:
            text = f"Download the law (PDF; {where or 'the provision'} is on page {page})"
            return {"href": url, "how": "file", "text": text}
        if page:
            return {"href": f"{url}#page={page}", "how": "page", "text": HOW["page"].format(page=page)}
        return {"href": url, "how": "file", "text": HOW["file"] + " (PDF)"}
    if host == "legislation.wa.gov.au":
        law = next((m.group(0) for i in law_ids if (m := WA_LAW.search(i or ""))), None)
        if law:
            return {"href": f"https://www.legislation.wa.gov.au/legislation/statutes.nsf/{law}.html", "how": "law",
                    "text": HOW["law"] + "'s page"}
        return {"href": url, "how": "file", "text": HOW["file"] + " (Word)"}
    if url.lower().split("?")[0].endswith(".rtf"):
        return {"href": url, "how": "file", "text": HOW["file"] + " (RTF)"}
    if host == "legislation.vic.gov.au":
        return {"href": url, "how": "law", "text": HOW["law"]}
    base = url.split("#")[0]
    anchored = "/view/" in url and host in ANCHORED
    if sec and anchored:
        anchor = f"GS{sec}@EN" if host == "legislation.tas.gov.au" else f"sec.{sec}"
        return {"href": f"{base}#{anchor}", "how": "section", "text": HOW["section"].format(where=where)}
    words = fragment(quote) if quote else "text="
    if anchored or host in NO_FRAGMENT or words == "text=":
        return {"href": url, "how": "law", "text": HOW["law"]}
    return {"href": f"{base}#:~:{words}", "how": "words", "text": HOW["words"]}
