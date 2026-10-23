"""ABS Australian Industry (8155.0): key data by division and subdivision, and by employment size × division.

From the release's data cube 1 (``81550DO001_<yyyymm>.xlsx``):

- ``industry`` (Table 1): employment at end of June, wages and salaries, sales and service income, total
  income and expenses, operating profit before tax, EBITDA and industry value added, for each subdivision,
  each division total and all selected industries, for the three years in the release;
- ``size_division`` (Table 5): the same items by employment range (0-4, 5-19, 20-199, 200+ employees) and
  division.

Coverage (ABS): selected industries only. Finance and insurance is subdivision 64 only (and is not in the
size table); public administration, education and health are private sector only. The number of businesses
is not in Australian Industry (use CABEE). Data: ABS, CC BY 4.0.
"""

from __future__ import annotations

import re

from .base import (
    ABS_LICENCE,
    Release,
    Source,
    Table,
    abs_page,
    anzsic_codes,
    clean_text,
    division_by_name,
    fetch_files,
    fy_end,
    fy_label,
    local_path,
    release_slug,
    remote,
    sheet_rows,
    value,
)

PAGE = "https://www.abs.gov.au/statistics/industry/industry-overview/australian-industry/latest-release"
SOURCE = Source(
    id="abs_australian_industry",
    title="Australian Industry (8155.0)",
    publisher="Australian Bureau of Statistics",
    licence=ABS_LICENCE,
    url=PAGE,
)
CUBE = r"/81550DO001_\d{6}\.xlsx$"
ITEMS = {
    "Employment at end of June": "employment",
    "Wages and salaries": "wages",
    "Sales and service income": "sales",
    "Total income": "total_income",
    "Total expenses": "total_expenses",
    "Operating profit before tax": "opbt",
    "Earnings before interest tax depreciation and amortisation": "ebitda",
    "Industry value added": "iva",
}
UNITS = {"'000": "thousand persons", "$m": "AUD million, current prices"}
BANDS = {
    "0–4 EMPLOYEES": "0-4",
    "5–19 EMPLOYEES": "5-19",
    "20–199 EMPLOYEES": "20-199",
    "200 OR MORE EMPLOYEES": "200+",
    "TOTAL": "total",
}
FY = re.compile(r"^\d{4}-\d{2}$")


def discover() -> Release:
    page = abs_page(PAGE)
    found = page.files(CUBE)
    if len(found) != 1:
        raise ValueError(f"expected one link matching {CUBE} on {PAGE}, found {len(found)}")
    return Release(
        id=release_slug(found[0]),
        date=page.released,
        files=(remote(found[0]),),
        page=PAGE,
        next_release=page.next_release,
        extra=(("reference_period", page.reference_period),),
    )


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def _header(rows: list[list], start: int = 0) -> tuple[int, dict[int, str], dict[int, str]]:
    """(row index of item names, {column: item}, {column: unit}) for Table 1's layout."""
    for i, r in enumerate(rows[start:], start=start):
        cells = {c: clean_text(v) for c, v in enumerate(r) if c > 0 and clean_text(v) in ITEMS}
        if len(cells) >= 4:
            units = {c: clean_text(rows[i + 1][c]) for c in cells}
            return i, {c: ITEMS[v] for c, v in cells.items()}, units
    raise ValueError("no header row of Australian Industry items found")


def _unit(u: str) -> str:
    if u not in UNITS:
        raise ValueError(f"unexpected unit {u!r}")
    return UNITS[u]


def industry_table(rows: list[list]) -> Table:
    hi, items, units = _header(rows)
    out, division, current = [], None, None
    for r in rows[hi + 2 :]:
        label = clean_text(r[0])
        if not label or label.startswith("©"):
            continue
        if FY.match(label):
            if current is None:
                raise ValueError(f"year row {label} before any industry label")
            code, level, name = current
            out.append(
                {"anzsic": code, "level": level, "name": name, "fy": label}
                | {col: value(r[c]) for c, col in items.items()}
            )
            continue
        if m := re.match(r"^(\d{2})\s+(.+)$", label):
            code = m.group(1)
            if code not in anzsic_codes():
                raise ValueError(f"unknown subdivision {label!r}")
            current = (code, "subdivision", anzsic_codes()[code]["name"])
        elif label.lower() == "total selected industries":
            current = ("TOT", "total", "Total selected industries")
        elif label.lower().startswith("total "):
            code = division_by_name(label[6:])
            if code is None:
                raise ValueError(f"unknown division total {label!r}")
            current = (code, "division", anzsic_codes()[code]["name"])
        else:
            division = division_by_name(label)
            if division is None and not re.match(r"^Auxiliary Finance", label, re.I):
                raise ValueError(f"unknown division heading {label!r}")
            current = None
    first, last = min(fy_end(r["fy"]) for r in out), max(fy_end(r["fy"]) for r in out)
    return Table(
        description=(
            f"Key data by ANZSIC subdivision and division, FY{fy_label(first)} to FY{fy_label(last)} (8155.0 "
            "Table 1). level: subdivision, division (the ABS division total) or total (all selected industries). "
            "Finance and insurance covers subdivision 64 only; divisions O, P and Q are private sector only. "
            "Employment is at end of June."
        ),
        columns={"anzsic": "code: ANZSIC 2006 subdivision, division or TOT", "level": "text", "name": "text"}
        | {"fy": "financial year (YYYY-YY)"}
        | {col: _unit(units[c]) for c, col in items.items()},
        keys=("anzsic", "fy"),
        rows=out,
    )


def size_table(rows: list[list]) -> Table:
    # Row with item names (each spanning three year columns), then years, then units.
    hi = next(i for i, r in enumerate(rows) if sum(clean_text(v) in ITEMS for v in r) >= 4)
    names, years, units = rows[hi], rows[hi + 1], rows[hi + 2]
    cols, item = {}, None
    for c in range(1, len(names)):
        if clean_text(names[c]) in ITEMS:
            item = ITEMS[clean_text(names[c])]
        y = clean_text(years[c]) if c < len(years) else ""
        if item and FY.match(y):
            cols[c] = (item, y, clean_text(units[c]))
    out: dict[tuple[str, str, str], dict] = {}
    band = None
    for r in rows[hi + 3 :]:
        label = clean_text(r[0])
        if not label or label.startswith("©"):
            continue
        if label in BANDS:
            band = BANDS[label]
            continue
        code = "TOT" if label.lower() == "total selected industries" else division_by_name(label)
        if code is None or band is None:
            raise ValueError(f"Table 5: unexpected row {label!r}")
        for c, (it, fy, _) in cols.items():
            out.setdefault((code, band, fy), {})[it] = value(r[c]) if c < len(r) else None
    item_units = {it: _unit(u) for it, _, u in cols.values()}
    years_kept = sorted({fy for _, fy, _ in cols.values()})
    names_ = {c: v["name"] for c, v in anzsic_codes().items()} | {"TOT": "Total selected industries"}
    return Table(
        description=(
            f"Key data by employment range and ANZSIC division, FY{years_kept[0]} to FY{years_kept[-1]} (8155.0 "
            "Table 5). size_band: employees (0-4, 5-19, 20-199, 200+) or total. Excludes finance and insurance "
            "(division K); divisions O, P and Q are private sector only."
        ),
        columns={
            "anzsic": "code: ANZSIC 2006 division or TOT",
            "name": "text",
            "size_band": "text: employment range (employees)",
            "fy": "financial year (YYYY-YY)",
        }
        | {it: item_units[it] for it in ITEMS.values() if it in item_units},
        keys=("anzsic", "size_band", "fy"),
        rows=[
            {"anzsic": code, "name": names_[code], "size_band": band, "fy": fy}
            | {it: v.get(it) for it in ITEMS.values() if it in item_units}
            for (code, band, fy), v in out.items()
        ],
    )


def build(release: Release) -> dict[str, Table]:
    path = local_path(SOURCE.id, release.files[0])
    return {
        "industry": industry_table(sheet_rows(path, "Table_1")),
        "size_division": size_table(sheet_rows(path, "Table_5")),
    }
