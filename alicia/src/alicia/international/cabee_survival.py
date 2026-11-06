"""Survival of new Australian businesses (ABS CABEE, data cube 5: survival of entries by main state, ANZSIC
subdivision and employment size at entry), for comparison with the OECD's employer enterprise survival.

Each release follows one year's entries: businesses that entered in the release's first financial year, and how
many were still trading at each of the next three Junes. The five xlsx releases (Jul 2017-Jun 2021 to Jul 2021-
Jun 2025) give the entry cohorts 2017-18 to 2021-22. The table here keeps, by cohort, state, subdivision and size
at entry: the entries and the survivors at the first, second and third June after the entry year. Sizes 1-4 and
5-19 (published separately from the Jul 2018-Jun 2022 release) are summed to 1-19, as in the CABEE panel.
Data: ABS, CC BY 4.0.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from ..pipeline import store
from . import OUT

SOURCE = "abs_cabee_survival"
LICENCE = "CC BY 4.0, Australian Bureau of Statistics"
BASE = "https://www.abs.gov.au/statistics/economy/business-indicators/counts-australian-businesses-including-entries-and-exits"
SIZES = {
    "Non Employing": "non-employing",
    "1-4 Employees": "1-19 employees",
    "5-19 Employees": "1-19 employees",
    "1-19 Employees": "1-19 employees",
    "20-199 Employees": "20-199 employees",
    "200+ Employees": "200+ employees",
}


@dataclass(frozen=True)
class Release:
    slug: str
    file: str
    cohort: int  # financial year of entry, by its ending year (2021-22 is 2022)

    @property
    def url(self) -> str:
        return f"{BASE}/{self.slug}/{self.file}"


RELEASES = (
    Release("jul2017-jun2021", "816505.xlsx", 2018),
    Release("jul2018-jun2022", "816505.xlsx", 2019),
    Release("jul2019-jun2023", "8165DC05.xlsx", 2020),
    Release("jul2020-jun2024", "8165DC05.xlsx", 2021),
    Release("jul2021-jun2025", "8165DC05.xlsx", 2022),
)


def parse(path, cohort: int) -> pd.DataFrame:
    """Long rows (cohort, state, subdivision, size, june, count) from a survival-of-entries cube. ``june`` is 0 for
    the entries and 1 to 3 for the survivors at the first to third June after the entry year."""
    raw = pd.read_excel(path, sheet_name=None, header=None)
    # The data sheet is "Table 1" in later releases and named by its years in earlier ones
    sheet = next((df for df in raw.values() if (df.iloc[:, 0].astype(str).str.strip() == "State").any()), None)
    if sheet is None:
        raise ValueError(f"{path}: no sheet with a 'State' heading")
    head = next(i for i in range(len(sheet)) if str(sheet.iat[i, 0]).strip() == "State")
    groups = sheet.iloc[head - 1].ffill()
    labels = sheet.iloc[head]
    cols = []
    for j in range(3, sheet.shape[1]):
        size, period = str(labels.iat[j]).strip(), str(groups.iat[j])
        if size not in SIZES:
            continue  # survival rates and totals are recomputed from the counts
        if period.startswith("Entries"):
            june = 0
        else:
            m = re.search(r"June (\d{4})", period)
            if not m:
                continue
            june = int(m.group(1)) - cohort
        cols.append((j, SIZES[size], june))
    if not cols or {c[2] for c in cols} != {0, 1, 2, 3}:
        raise ValueError(f"{path}: unexpected column layout {sorted({c[2] for c in cols})}")
    rows = []
    for i in range(head + 2, len(sheet)):
        state, code = sheet.iat[i, 0], sheet.iat[i, 1]
        if pd.isna(state) or pd.isna(code) or not str(code).strip().isdigit():
            continue
        sub = f"{int(code):02d}"
        for j, size, june in cols:
            v = pd.to_numeric(sheet.iat[i, j], errors="coerce")
            if pd.notna(v):
                rows.append((cohort, str(state).strip(), sub, size, june, float(v)))
    df = pd.DataFrame(rows, columns=["cohort", "state", "subdivision", "size", "june", "count"])
    return df.groupby(["cohort", "state", "subdivision", "size", "june"], as_index=False)["count"].sum()


def build(refresh: bool = False) -> pd.DataFrame:
    frames = []
    for rel in RELEASES:
        path = store.download(SOURCE, rel.url, f"{rel.slug}_{rel.file}", LICENCE, refresh=refresh)
        frames.append(parse(path, rel.cohort))
    df = pd.concat(frames, ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT / "au_cabee_survival.parquet", index=False)
    return df


def read() -> pd.DataFrame:
    return pd.read_parquet(OUT / "au_cabee_survival.parquet")
