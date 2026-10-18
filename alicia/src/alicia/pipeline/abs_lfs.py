"""Labour Force Survey: employment and hours actually worked by ANZSIC group and state, quarterly.

Table EQ06 of Labour Force, Australia, Detailed (ABS cat. 6291.0.55.001, CC BY 4.0) gives, for each
mid-quarter month since November 1984, employed persons (full-time and part-time, '000) and hours
actually worked in all jobs ('000 hours in the reference week) by industry group of main job, sex
and state. Only the middle month of each quarter carries industry detail, so the panel is quarterly:
the period is the first day of the calendar quarter whose middle month was surveyed.

The estimates are survey-based. At group x state level many cells rest on a handful of respondents
and have large sampling errors (the ABS publishes relative standard errors separately), so small
cells move a lot from quarter to quarter. Groups are coded by industry of main job, and hours are
for all jobs of people whose main job is in the industry.

Rows coded "nfd" (not further defined) belong to a subdivision or division but no group. They are
left out of the group rows and included in the subdivision, division and total rows built here.
"""

from __future__ import annotations

import openpyxl
import pandas as pd

from .. import anzsic
from . import schema, store

SOURCE = "abs_lfs"
LICENCE = "CC BY 4.0, Australian Bureau of Statistics"
RELEASE = "mar-2026"  # latest Labour Force, Australia, Detailed release on 18 Oct 2026 (data to Feb 2026)
URL = (
    "https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia-detailed/"
    f"{RELEASE}/EQ06.xlsx"
)
COLUMNS = ("month", "sex", "state", "industry", "ft", "pt", "hours_ft", "hours_pt")


def read(path) -> pd.DataFrame:
    """The 'Data 1' sheet as a frame with COLUMNS (one row per month, sex, state and industry)."""
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb["Data 1"]
    rows = ws.iter_rows(min_row=4, values_only=True)
    header = next(rows)
    if not (str(header[3]).startswith("Industry group") and "hours actually worked" in str(header[6])):
        raise ValueError(f"unexpected EQ06 layout: {header[:8]}")
    data = [r[:8] for r in rows if r[0] is not None]
    wb.close()
    return pd.DataFrame(data, columns=list(COLUMNS))


def tidy(raw: pd.DataFrame, vintage: str) -> pd.DataFrame:
    d = raw.assign(
        state=raw["state"].map(schema.STATE_NAMES),
        code=raw["industry"].str.extract(r"^(\w+)\s", expand=False),
        nfd=raw["industry"].str.contains(r"\bnfd\b", regex=True),
    )
    if d["state"].isna().any():
        raise ValueError(f"unknown states: {sorted(raw.loc[d['state'].isna(), 'state'].unique())}")
    # "C00 Manufacturing nfd" -> division C; "150 ... nfd" -> subdivision 15; "151 ..." -> group 151.
    d["division"] = d["code"].map(lambda c: c[0] if c[0].isalpha() else anzsic.division(c[:2]))
    d["subdivision"] = d["code"].where(~d["code"].str[0].str.isalpha()).str[:2]
    d["group"] = d["code"].where(~d["nfd"] & d["code"].str[0].str.isdigit())
    groups = d["group"].dropna()
    if (bad := groups[groups.map(anzsic.name).isna()]).any():
        raise ValueError(f"codes not in ANZSIC 2006: {sorted(bad.unique())[:5]}")
    d["employed"] = d["ft"] + d["pt"]
    d["hours"] = d["hours_ft"] + d["hours_pt"]
    month = pd.to_datetime(d["month"])
    d["period"] = pd.to_datetime(dict(year=month.dt.year, month=(month.dt.month - 1) // 3 * 3 + 1, day=1))

    parts = []
    for level, col in (("group", "group"), ("subdivision", "subdivision"), ("division", "division"), ("total", None)):
        g = d if col is None else d[d[col].notna()]
        keys = ["period", "state"] + ([col] if col else [])
        sums = g.groupby(keys, observed=True)[["employed", "ft", "hours"]].sum().reset_index()
        for geo_level in ("STE", "AUS"):
            k = keys if geo_level == "STE" else [k for k in keys if k != "state"]
            s = sums.groupby(k, observed=True)[["employed", "ft", "hours"]].sum().reset_index()
            for measure, value, unit in (
                ("employed", "employed", "'000 persons"),
                ("employed_full_time", "ft", "'000 persons"),
                ("hours_actual", "hours", "'000 hours (reference week)"),
            ):
                parts.append(
                    pd.DataFrame(
                        {
                            "measure": measure,
                            "unit": unit,
                            "industry_scheme": "ANZSIC06" if col else "none",
                            "industry_level": level,
                            "industry_code": s[col] if col else "",
                            "industry_label": s[col].map(anzsic.name) if col else "",
                            "geo_level": geo_level,
                            "geo_code": s["state"] if geo_level == "STE" else "AUS",
                            "period": s["period"],
                            "value": s[value].round(3),  # '000s, so to the person or hour
                        }
                    )
                )
    return schema.make(
        pd.concat(parts, ignore_index=True),
        source=SOURCE,
        adjustment="original",
        period_type="quarter",
        breakdown="",
        vintage=vintage,
    )


def build() -> pd.DataFrame:
    path = store.download(SOURCE, URL, f"EQ06_{RELEASE}.xlsx", LICENCE)
    panel = tidy(read(path), f"Labour Force, Australia, Detailed, {RELEASE}")
    store.write_panel(panel, SOURCE, "industry_state_quarter")
    return panel
