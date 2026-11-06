"""ATO Taxation Statistics, Company Table 4 (selected items by industry) in the common panel format.

Company tax returns summed by industry: income, expenses, accounting profit, tax, and the balance-sheet
totals (total assets, total liabilities) that give shareholders' equity. They are the public stand-in for
the IBISWorld and Morningstar data behind Grattan Institute's profitability charts (Minifie, Chisholm and
Percival 2017, *Competition in Australia: too little of a good thing?*): return on equity, super-normal
profit and mark-ups by sector (``alicia.menu.growth``; methods in docs/methods_competition_charts.md).

Tables
- ``class_fy``: Table 4B, by the ATO's five-digit industry code, summed to ANZSIC class (the code's first
  four digits), income years 2018-19 to 2022-23. Earlier releases publish only a few items by industry
  code, without the balance sheet.
- ``group_fy``: Table 4A, by ANZSIC group ("fine industry"), income years 2014-15 to 2022-23. The ATO
  publishes rail freight and rail passenger transport together (kept as subdivision 47). Releases before
  2014-15 publish division D as a single row, so they are not used.
Both tables carry an all-industries row (industry_level "total"), which includes companies whose
industry is not known ("Other").

Coverage: companies only. Sole traders, partnerships and trusts are left out, and so are businesses that
pay tax equivalents to a state instead of company tax (state-owned electricity networks, water utilities,
some ports); stapled structures are partly in (their trusts are not). Industry is the company's own
description of its main business. Book equity (total assets less total liabilities) includes goodwill.

Data: Australian Taxation Office, Taxation Statistics (via data.gov.au), CC BY 2.5 AU (2014-15 onwards).
"""

from __future__ import annotations

import re

import openpyxl
import pandas as pd

from .. import anzsic
from . import schema, store

SOURCE = "ato_company"
LICENCE = "CC BY 2.5 AU, Australian Taxation Office (Taxation Statistics, via data.gov.au)"
DATA = "https://data.gov.au/data/dataset/"
# Income year (first year) -> the Company Table 4 workbook on data.gov.au: (dataset/resource ids, file name).
# Table 4B has the balance sheet from 2018-19 on.
FILES = {
    2014: (
        "5c99cfed-254d-40a6-af1c-47412b7de6fe/resource/cbdd520b-0f61-4191-aabc-ede0a2f6ce14",
        "taxstats2015company04selecteditemsbyindustry.xlsx",
    ),
    2015: (
        "d170213c-4391-4d10-ac24-b0c11768da3f/resource/ca69a419-ce86-4db5-bb12-8990927a9aa0",
        "taxstats2016company04industry.xlsx",
    ),
    2016: (
        "540e3eac-f2df-48d1-9bc0-fbe8dfec641f/resource/be333247-4447-4dfc-b7ab-b9ee1059bd5b",
        "ts17company04industry.xlsx",
    ),
    2017: (
        "23b8c299-a85b-4fc0-a07d-5ed14e23a103/resource/ddc401e8-5875-4763-9932-33cb63df94ec",
        "ts18company04industry.xlsx",
    ),
    2018: (
        "2805b28d-2c3b-47e2-87c3-50aacc6ea212/resource/fb954ec6-7716-4a09-abf2-cff826d29da4",
        "ts19company04industry.xlsx",
    ),
    2019: (
        "f1a2c3d5-98d0-46b7-8b8c-742e65c6afa7/resource/dca79801-03b9-4339-932b-e0881391113d",
        "ts20company04industry.xlsx",
    ),
    2020: (
        "07b51b39-254a-4177-8b4c-497f17eddb80/resource/bf9cbddb-cecf-49eb-92ba-40cbca58c76c",
        "ts21company04industry.xlsx",
    ),
    2021: (
        "4be150cc-8f84-46b8-8c61-55ff1d48a700/resource/d7f1f6a2-9376-4b90-bf6f-146948aceae4",
        "ts22company04industry.xlsx",
    ),
    2022: (
        "03326c3f-c0d3-4af4-afc7-c6ccc0a02223/resource/9c343469-7fa4-450c-8e96-b7fcee2eaad8",
        "ts23company04industry.xlsx",
    ),
}
CLASS_FROM = 2018
# Normalised column heading -> (measure, unit). Dollar items are converted to AUD million.
ITEMS = {
    "companies no.": ("companies", "count"),
    "number of companies no.": ("companies", "count"),
    "total income $": ("total_income", "AUD m"),
    "total expenses $": ("total_expenses", "AUD m"),
    "total profit or loss $": ("profit_before_tax", "AUD m"),
    "taxable income or loss $": ("taxable_income", "AUD m"),
    "tax payable $": ("tax_payable", "AUD m"),
    "total assets $": ("total_assets", "AUD m"),
    "total liabilities $": ("total_liabilities", "AUD m"),
    "depreciation expenses $": ("depreciation", "AUD m"),
    "interest expenses within australia $": ("interest_expenses", "AUD m"),
    "total salary and wage expenses $": ("wages", "AUD m"),
}
MEASURES = tuple(dict.fromkeys(m for m, _ in ITEMS.values()))
RAIL = re.compile(r"rail freight( and |/)passenger transport", re.I)  # ANZSIC groups 471 and 472, published together


class LayoutError(ValueError):
    pass


def heading(cell) -> str:
    """'Total income3\\n$' -> 'total income $' (footnote digits and line breaks removed)."""
    text = " ".join(str(cell or "").split()).lower()
    return re.sub(r"(?<=[a-z)])\d+(?=\s|$)", "", text)


def _rows(path, sheet_hint: str) -> tuple[list[str], list[tuple]]:
    """The heading row and data rows of the sheet whose title names ``sheet_hint`` ('4A', '4B' or '4')."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheets = [ws for ws in wb.worksheets if ws.title.strip().lower() != "notes"]
        named = [ws for ws in sheets if ws.title.replace(" ", "").upper().endswith(f"TABLE{sheet_hint}".upper())]
        if not named and sheet_hint == "4A":
            named = [ws for ws in sheets if ws.title.replace(" ", "").upper().endswith("TABLE4")]
        if not named:
            raise LayoutError(f"{path}: no sheet for Table {sheet_hint} in {[ws.title for ws in sheets]}")
        rows = list(named[0].iter_rows(values_only=True))
    finally:
        wb.close()
    head = max(range(min(8, len(rows))), key=lambda i: sum(c is not None for c in rows[i]))
    return [heading(c) for c in rows[head]], [r for r in rows[head + 1 :] if any(c is not None for c in r)]


def _number(v) -> float:
    return float(v) if isinstance(v, int | float) and not isinstance(v, bool) else float("nan")


def _long(head: list[str], rows: list[tuple], keys: dict[str, list]) -> pd.DataFrame:
    """Rows -> one record per (key, measure); keys are already parsed per row."""
    cols = {i: ITEMS[h] for i, h in enumerate(head) if h in ITEMS}
    found = {m for m, _ in cols.values()}
    if found != set(MEASURES):
        raise LayoutError(f"items not found: {sorted(set(MEASURES) - found)}")
    out = []
    for n, r in enumerate(rows):
        for i, (measure, unit) in cols.items():
            v = _number(r[i])
            out.append(
                {
                    **{k: v_[n] for k, v_ in keys.items()},
                    "measure": measure,
                    "unit": unit,
                    "value": v / 1e6 if unit == "AUD m" else v,
                }
            )
    return pd.DataFrame(out)


def read_by_code(path) -> pd.DataFrame:
    """Table 4B: one row per ATO industry code -> code (five digits, '' for 'Other'), description, items."""
    head, rows = _rows(path, "4B")
    ci = next((i for i, h in enumerate(head) if h.startswith("industry code")), None)
    di = next((i for i, h in enumerate(head) if h == "business description"), None)
    if ci is None or di is None:
        raise LayoutError(f"{path}: Table 4B has no industry code or business description column")
    rows = [r for r in rows if r[ci] is not None or str(r[di] or "").strip().lower().startswith("other")]
    codes = [str(int(r[ci])).zfill(5) if r[ci] is not None else "" for r in rows]
    return _long(head, rows, {"code": codes, "description": [str(r[di] or "").strip() for r in rows]})


def read_by_group(path) -> pd.DataFrame:
    """Table 4A: one row per fine industry -> ANZSIC group code ('47' for rail, '' for 'Other'), items."""
    head, rows = _rows(path, "4A")
    fi = next((i for i, h in enumerate(head) if h.startswith("fine industry")), None)
    if fi is None:
        raise LayoutError(f"{path}: Table 4A has no fine industry column")
    rows = [r for r in rows if r[fi]]
    codes, labels = [], []
    for r in rows:
        text = " ".join(str(r[fi]).split())
        m = re.match(r"(\d{3})\s+(.*)", text)
        if m:
            codes.append(m.group(1))
            labels.append(m.group(2))
        elif RAIL.fullmatch(text):
            codes.append("47")
            labels.append(text)
        elif re.fullmatch(r"other\d?", text.lower()):
            codes.append("")
            labels.append("Other")
        else:
            raise LayoutError(f"{path}: fine industry without an ANZSIC group code: {text!r}")
    return _long(head, rows, {"code": codes, "description": labels})


def _panel(df: pd.DataFrame, level_of, year: int, vintage: str) -> pd.DataFrame:
    """Sum to the panel's industries, add an all-industries row, and lay out in the common format."""
    df = df.assign(level=df["code"].map(level_of))
    known = df[df["code"] != ""]
    by = known.groupby(["level", "code", "measure", "unit"], as_index=False)["value"].sum(min_count=1)
    total = df.groupby(["measure", "unit"], as_index=False)["value"].sum(min_count=1).assign(level="total", code="")
    out = pd.concat([by, total], ignore_index=True)
    return pd.DataFrame(
        {
            "measure": out["measure"],
            "unit": out["unit"],
            "adjustment": "original",
            "industry_level": out["level"],
            "industry_code": out["code"],
            "industry_label": [
                "All industries" if lv == "total" else (anzsic.name(c) or c)
                for lv, c in zip(out["level"], out["code"], strict=True)
            ],
            "geo_level": "AUS",
            "geo_code": "AUS",
            "period_type": "fy",
            "period": pd.Timestamp(year, 7, 1),
            "value": out["value"],
            "vintage": vintage,
        }
    )


def tidy_class(raw: pd.DataFrame, year: int, vintage: str) -> pd.DataFrame:
    raw = raw.assign(code=raw["code"].str[:4])
    unknown = sorted({c for c in raw["code"] if c and anzsic.name(c) is None})
    if unknown:
        raise LayoutError(f"{year}: industry codes outside ANZSIC 2006 classes: {unknown[:5]}")
    return _panel(raw, lambda c: "class" if c else "total", year, vintage)


def tidy_group(raw: pd.DataFrame, year: int, vintage: str) -> pd.DataFrame:
    unknown = sorted({c for c in raw["code"] if c and anzsic.name(c) is None})
    if unknown:
        raise LayoutError(f"{year}: fine industries outside ANZSIC 2006 groups: {unknown[:5]}")
    return _panel(raw, lambda c: schema.ANZSIC_LEVEL_BY_LENGTH.get(len(c), "total"), year, vintage)


def _vintage(year: int, table: str) -> str:
    return f"ATO Taxation statistics {year}-{(year + 1) % 100:02d}, Company Table {table}"


def build() -> dict[str, pd.DataFrame]:
    classes, groups = [], []
    for year, (ids, name) in FILES.items():
        local = store.download(SOURCE, f"{DATA}{ids}/download/{name}", name, LICENCE)
        groups.append(tidy_group(read_by_group(local), year, _vintage(year, "4A")))
        if year >= CLASS_FROM:
            classes.append(tidy_class(read_by_code(local), year, _vintage(year, "4B")))
    out = {
        "class_fy": schema.make(pd.concat(classes, ignore_index=True), source=SOURCE, industry_scheme="ANZSIC06"),
        "group_fy": schema.make(pd.concat(groups, ignore_index=True), source=SOURCE, industry_scheme="ANZSIC06"),
    }
    for table, panel in out.items():
        store.write_panel(panel, SOURCE, table)
    return out
