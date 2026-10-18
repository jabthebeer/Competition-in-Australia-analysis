"""Parsing helpers for register pages: dates written in the registers' formats, and Word tables."""

from __future__ import annotations

import datetime as dt
import io
import re
import xml.etree.ElementTree as ET
import zipfile

MONTHS = {
    m: i
    for i, m in enumerate(
        [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ],
        start=1,
    )
}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
MONTHS["sept"] = 9

_DMY_WORDS = re.compile(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b")
_DMY_NUM = re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b")
_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})")


def _safe(y: int, m: int, d: int) -> dt.date | None:
    try:
        return dt.date(y, m, d)
    except ValueError:
        return None


def parse_date(text: str | None) -> dt.date | None:
    """The first date in ``text``: '9 November 2022', '30 Oct 2018', '31/03/2026', '1.7.2016' or ISO."""
    dates = find_dates(text)
    return dates[0] if dates else None


def find_dates(text: str | None) -> list[dt.date]:
    """Every date in ``text``, in order of appearance."""
    if not text:
        return []
    found: list[tuple[int, dt.date]] = []
    for m in _DMY_WORDS.finditer(text):
        month = MONTHS.get(m.group(2).lower())
        if month and (d := _safe(int(m.group(3)), month, int(m.group(1)))):
            found.append((m.start(), d))
    for m in _DMY_NUM.finditer(text):
        if d := _safe(int(m.group(3)), int(m.group(2)), int(m.group(1))):
            found.append((m.start(), d))
    for m in _ISO.finditer(text):
        if d := _safe(int(m.group(1)), int(m.group(2)), int(m.group(3))):
            found.append((m.start(), d))
    return [d for _, d in sorted(found, key=lambda x: x[0])]


_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_tables(data: bytes) -> list[list[list[str]]]:
    """Every table in a .docx as rows of cell text (paragraphs joined with spaces)."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    tables = []
    for tbl in root.iter(f"{_W}tbl"):
        rows = []
        for tr in tbl.iter(f"{_W}tr"):
            cells = []
            for tc in tr.findall(f"{_W}tc"):
                paras = ["".join(t.text or "" for t in p.iter(f"{_W}t")) for p in tc.iter(f"{_W}p")]
                cells.append(" ".join(x for x in paras if x).strip())
            rows.append(cells)
        tables.append(rows)
    return tables


def docx_text(data: bytes, max_chars: int = 20000) -> str:
    """Body text of a .docx (first ``max_chars`` characters), paragraphs separated by newlines."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    out, size = [], 0
    for p in root.iter(f"{_W}p"):
        line = "".join(t.text or "" for t in p.iter(f"{_W}t"))
        out.append(line)
        size += len(line) + 1
        if size > max_chars:
            break
    return "\n".join(out)


def commencement_table(tables: list[list[list[str]]]) -> list[tuple[str, str, str]]:
    """Rows (provisions, rule, date/details) of a Commonwealth s 2 'Commencement information' table."""
    for rows in tables:
        flat = " ".join(" ".join(r) for r in rows)
        if "Commencement information" not in flat:
            continue
        out = []
        for r in rows:
            if len(r) < 3 or r[0] in ("Column 1", "Provisions") or r[0].startswith("Commencement information"):
                continue
            out.append((re.sub(r"^\d+\.\s*", "", r[0]).strip(), r[1].strip(), r[2].strip()))
        return out
    return []


_COMMENCES = re.compile(r"commence[sd]?\s+on\s+(?:the\s+)?(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})", re.I)


def commencement_in_prose(text: str) -> list[dt.date]:
    """Dates in sentences like 'This instrument commences on 1 April 2017.'"""
    return [d for m in _COMMENCES.finditer(text) if (d := parse_date(m.group(1)))]
