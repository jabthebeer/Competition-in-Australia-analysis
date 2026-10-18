"""Internet Vacancy Index (Jobs and Skills Australia), from workbooks downloaded by hand.

The IVI (https://www.jobsandskills.gov.au/data/internet-vacancy-index, CC BY 4.0) counts online job
advertisements each month by ANZSCO occupation and state from January 2006, and by broader occupation
groups and IVI region (about 37 regions built from SA4s) from 2010. Vacancies are classified by
occupation, not industry, so they link to a change through the occupations it regulates (licensed
trades, health professions), not through ANZSIC codes; the coverage catalogue lists them but does
not match them to records by industry.

The Jobs and Skills Australia site could not be reached from the environment this was written in
(the connection was refused, 18 Oct 2026), so ``build`` parses whatever workbooks are saved in
``data/raw/jsa_ivi/``. It does not assume a fixed layout: in each sheet it looks for a header row
with an ANZSCO code column and month columns, then reads state, region and title columns by name.
It has been tested only on a synthetic workbook. Check its output against the published totals
before using it, and record each file in data/SOURCES.md.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import schema, store

SOURCE = "jsa_ivi"
LICENCE = "CC BY 4.0, Jobs and Skills Australia"
PAGE = "https://www.jobsandskills.gov.au/data/internet-vacancy-index"
STATE_ALIASES = {**schema.STATE_NAMES, **{s: s for s in schema.STATES}, "AUST": "AUS", "AUSTRALIA": "AUS"}
STATE_ALIASES = {k.upper(): v for k, v in STATE_ALIASES.items()}


def _month(cell) -> pd.Timestamp | None:
    if isinstance(cell, datetime | pd.Timestamp):
        return pd.Timestamp(cell).to_period("M").to_timestamp()
    if isinstance(cell, str) and re.fullmatch(r"[A-Za-z]{3}[- ]\d{2,4}|\d{4}-\d{2}(?:-\d{2})?", cell.strip()):
        t = pd.to_datetime(cell.strip(), errors="coerce", format="mixed")
        return None if pd.isna(t) else t.to_period("M").to_timestamp()
    return None


def _adjustment(sheet: str) -> str:
    s = sheet.lower()
    if "trend" in s:
        return "trend"
    if "seas" in s:
        return "seasonally adjusted"
    if "orig" in s:
        return "original"
    return ""


def parse_sheet(raw: pd.DataFrame, sheet: str, vintage: str) -> pd.DataFrame | None:
    """One sheet (read with header=None) -> panel rows, or None if it holds no IVI table."""
    for i in range(min(30, len(raw))):
        row = raw.iloc[i]
        labels = {j: str(v).strip().lower() for j, v in row.items() if isinstance(v, str)}
        code_col = next((j for j, v in labels.items() if "anzsco" in v and "code" in v), None)
        months = {j: m for j, v in row.items() if (m := _month(v)) is not None}
        if code_col is None or len(months) < 3:
            continue
        state_col = next((j for j, v in labels.items() if v.startswith("state")), None)
        region_col = next((j for j, v in labels.items() if "region" in v), None)
        title_col = next((j for j, v in labels.items() if "title" in v), None)
        body = raw.iloc[i + 1 :]
        out = []
        for _, r in body.iterrows():
            code = str(r[code_col]).strip().split(".")[0]
            if not code.isdigit():
                continue
            state = STATE_ALIASES.get(str(r[state_col]).strip().upper()) if state_col is not None else "AUS"
            if state is None:
                continue
            region = str(r[region_col]).strip() if region_col is not None else ""
            if region and region.upper() not in STATE_ALIASES and state != "AUS":
                geo_level, geo_code = "IVI_REGION", f"{state}:{region}"
            else:
                geo_level, geo_code = ("AUS", "AUS") if state == "AUS" else ("STE", state)
            total = code == "0"
            for j, month in months.items():
                v = pd.to_numeric(r[j], errors="coerce")
                if pd.isna(v):
                    continue
                out.append(
                    {
                        "industry_scheme": "none" if total else "ANZSCO",
                        "industry_level": "total" if total else "occupation",
                        "industry_code": "" if total else code,
                        "industry_label": "" if total or title_col is None else str(r[title_col]).strip(),
                        "geo_level": geo_level,
                        "geo_code": geo_code,
                        "period": month,
                        "value": float(v),
                    }
                )
        if not out:
            return None
        return pd.DataFrame(out).assign(adjustment=_adjustment(sheet), vintage=vintage)
    return None


def parse_file(path: Path) -> pd.DataFrame:
    parts = []
    for sheet, raw in pd.read_excel(path, sheet_name=None, header=None, dtype=object).items():
        part = parse_sheet(raw, sheet, vintage=path.name)
        if part is not None:
            parts.append(part)
    if not parts:
        raise ValueError(f"{path.name}: no IVI table found")
    return pd.concat(parts, ignore_index=True)


def build() -> pd.DataFrame:
    files = sorted(p for p in store.raw_dir(SOURCE).glob("*.xls*") if not p.name.startswith("~"))
    if not files:
        raise FileNotFoundError(f"save IVI workbooks from {PAGE} in {store.raw_dir(SOURCE)} first")
    for p in files:
        store.record_download(SOURCE, p, PAGE, LICENCE, note="downloaded by hand")
    d = pd.concat([parse_file(p) for p in files], ignore_index=True)
    keys = ["adjustment", "industry_code", "geo_level", "geo_code", "period"]
    d = d.drop_duplicates(keys, keep="last")  # later files (by name) win where tables overlap
    panel = schema.make(d, source=SOURCE, measure="online_vacancies", unit="count", period_type="month", breakdown="")
    store.write_panel(panel, SOURCE, "vacancies_month")
    return panel
