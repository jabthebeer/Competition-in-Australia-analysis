"""Reader for ABS data-cube sheets laid out as label rows against financial-year columns.

Used by the Industry MFP tables (5260.0.55.002): a header row of financial years ('1989-90', ...), then
heading rows (a label and no values) and data rows (a label and one value per year), then footnotes. Headings
nest by their indentation (leading spaces or non-breaking spaces), so each data row carries the path of
headings above it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .base import clean_text, fy_end, value

FY = re.compile(r"^\d{4}\s*[-–]\s*\d{2}$")
FOOTNOTE = re.compile(r"^\(\w{1,2}\)\s")


@dataclass(frozen=True)
class CubeRow:
    path: tuple[str, ...]
    label: str
    values: dict[int, float | None]  # financial year (ending year) -> value


def strip_notes(label: str) -> str:
    """'12 Selected industries (b)' -> '12 Selected industries'; 'Output growth (c)' -> 'Output growth'."""
    out = clean_text(label)
    while (m := re.search(r"\s*\([a-z]\)$", out)) is not None:
        out = out[: m.start()]
    return out


def _indent(raw) -> int:
    s = str(raw)
    return len(s) - len(s.lstrip(" \xa0"))


def read(rows: list[list]) -> tuple[list[CubeRow], list[str]]:
    """(data rows, footnote lines) of one sheet."""
    header_i, years = None, {}
    for i, r in enumerate(rows):
        cells = {c: clean_text(v) for c, v in enumerate(r) if c > 0 and v is not None and FY.match(clean_text(v))}
        if len(cells) >= 3:
            header_i, years = i, {c: fy_end(v) for c, v in cells.items()}
            break
    if header_i is None:
        raise ValueError("no row of financial-year column headings found")
    # stack entries: [indent, heading, has data]. A heading replaces earlier headings at its indent that already
    # have data rows; one that directly follows a same-indent heading with no data yet nests under it (a block
    # heading such as "Percentage changes to productivity indexes" above "Productivity indexes").
    out, notes, stack = [], [], []
    for r in rows[header_i + 1 :]:
        raw = r[0] if r else None
        label = clean_text(raw)
        if not label:
            continue
        if FOOTNOTE.match(label) or label.startswith("©") or re.match(r"^n[ap]\s", label):
            notes.append(label)
            continue
        ind = _indent(raw)
        cells = [r[c] if c < len(r) else None for c in years]
        if all(v is None or clean_text(v) == "" for v in cells):
            stack = [e for e in stack if e[0] < ind or (e[0] == ind and not e[2])] + [[ind, strip_notes(label), False]]
            continue
        above = [e for e in stack if e[0] < ind] if ind > 0 else [e for e in stack if e[0] == 0]
        for e in above:
            e[2] = True
        values = {fy: value(v) for fy, v in zip(years.values(), cells, strict=True)}
        out.append(CubeRow(tuple(e[1] for e in above), strip_notes(label), values))
    return out, notes


def index_reference(notes: list[str]) -> str | None:
    """'(a) Reference year for indexes is 2023-24 = 100.0' -> '2023-24'."""
    for n in notes:
        if m := re.search(r"Reference year for indexes is (\d{4}-\d{2})", n):
            return m.group(1)
    return None


def industry_code(label: str) -> str | None:
    """'A Agriculture, forestry and fishing' -> 'A'; '16 Market sector industries' -> 'MKT16';
    '12 Selected industries' -> 'SEL12'."""
    label = strip_notes(label)
    if m := re.match(r"^([A-S])\s+\S", label):
        return m.group(1)
    if re.match(r"^16\s+Market sector", label, re.I):
        return "MKT16"
    if re.match(r"^12\s+Selected industries", label, re.I):
        return "SEL12"
    return None
