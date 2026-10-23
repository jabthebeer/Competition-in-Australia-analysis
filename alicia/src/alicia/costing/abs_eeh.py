"""ABS Employee Earnings and Hours, Australia (6306.0), Data Cube 6: earnings by industry and employer size.

Data Cube 6 covers full-time non-managerial employees paid at the adult rate (the population the OIA's
Regulatory Burden Measurement Framework uses for its labour rate). From its Table 3 (industry) and Table 6
(employer size), for all ages: number of employees, average weekly total cash earnings, average weekly total
hours paid for and average hourly total cash earnings, with the ABS's standard errors. Earnings are before tax.
Agriculture, forestry and fishing is out of scope of the survey. Data: ABS, CC BY 4.0.
"""

from __future__ import annotations

import re

from .base import (
    ABS_LICENCE,
    Release,
    Source,
    Table,
    abs_page,
    clean_text,
    division_by_name,
    fetch_files,
    local_path,
    release_slug,
    remote,
    sheet_rows,
    value,
)

PAGE = "https://www.abs.gov.au/statistics/labour/earnings-and-working-conditions/employee-earnings-and-hours-australia/latest-release"
SOURCE = Source(
    id="abs_eeh",
    title="Employee Earnings and Hours, Australia (6306.0), Data Cube 6",
    publisher="Australian Bureau of Statistics",
    licence=ABS_LICENCE,
    url=PAGE,
)
CUBE = r"/63060DO006_\d{6}\.xlsx$"
MEASURES = {
    "NUMBER OF EMPLOYEES": ("employees", "thousand employees"),
    "AVERAGE WEEKLY TOTAL CASH EARNINGS": ("weekly_cash_earnings", "AUD per week, before tax"),
    "AVERAGE WEEKLY TOTAL HOURS PAID FOR": ("weekly_hours_paid", "hours per week"),
    "AVERAGE HOURLY TOTAL CASH EARNINGS": ("hourly_cash_earnings", "AUD per hour, before tax"),
}
SIZES = {
    "Under 20 employees": "<20",
    "20 - 49 employees": "20-49",
    "50 - 99 employees": "50-99",
    "100 - 999 employees": "100-999",
    "1,000 and over employees": "1000+",
    "Total": "total",
}
POPULATION = "full-time non-managerial employees paid at the adult rate, all ages"


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


def read(rows: list[list]) -> dict[str, dict[str, float | None]]:
    """{category label: {column: value}} for the 'All ages' column, estimates and standard errors."""
    head = next(i for i, r in enumerate(rows) if any(clean_text(v) == "All ages" for v in r))
    col = next(c for c, v in enumerate(rows[head]) if clean_text(v) == "All ages")
    out: dict[str, dict] = {}
    kind = measure = None
    for r in rows[head + 1 :]:
        label = clean_text(r[0])
        if not label or label.startswith("©"):
            continue
        up = label.upper()
        if up in ("ESTIMATE", "ESTIMATES"):
            kind = ""
            continue
        if up.startswith("STANDARD ERROR"):
            kind = "_se"
            continue
        key = re.sub(r"\s*\(.*\)$", "", up)
        if key in MEASURES:
            measure = MEASURES[key][0]
            continue
        if kind is None or measure is None:
            raise ValueError(f"row {label!r} before a section or measure heading")
        out.setdefault(label, {})[measure + kind] = value(r[col]) if col < len(r) else None
    return out


def _columns() -> dict[str, str]:
    cols = {}
    for name, unit in MEASURES.values():
        cols[name] = unit
        cols[name + "_se"] = f"{unit}: standard error"
    return cols


def build(release: Release) -> dict[str, Table]:
    path = local_path(SOURCE.id, release.files[0])
    period = release.get("reference_period", release.id)
    industry = []
    for label, vals in read(sheet_rows(path, "Table_3")).items():
        code = "TOT" if label.lower() == "all industries" else division_by_name(label)
        if code is None:
            raise ValueError(f"Table 3: unknown industry {label!r}")
        industry.append({"anzsic": code} | {c: vals.get(c) for c in _columns()})
    size = []
    for label, vals in read(sheet_rows(path, "Table_6")).items():
        band = SIZES.get(label)
        if band is None:
            raise ValueError(f"Table 6: unknown employer size {label!r}")
        size.append({"employer_size": band} | {c: vals.get(c) for c in _columns()})
    return {
        "by_industry": Table(
            description=(
                f"Earnings and hours of {POPULATION}, by ANZSIC division, {period} (6306.0 Data Cube 6, Table 3). "
                "TOT = all industries. Division A is out of scope. _se columns are the ABS's standard errors."
            ),
            columns={"anzsic": "code: ANZSIC 2006 division or TOT"} | _columns(),
            keys=("anzsic",),
            rows=industry,
        ),
        "by_employer_size": Table(
            description=(
                f"Earnings and hours of {POPULATION}, by employer size (number of employees), {period} (6306.0 "
                "Data Cube 6, Table 6). _se columns are the ABS's standard errors."
            ),
            columns={"employer_size": "text: employees (<20, 20-49, 50-99, 100-999, 1000+, total)"} | _columns(),
            keys=("employer_size",),
            rows=size,
        ),
    }
