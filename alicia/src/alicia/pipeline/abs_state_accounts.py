"""ABS Australian National Accounts: State Accounts (cat. 5220.0) in the common panel format.

Annual (financial year) gross value added by ANZSIC division for each state and territory and
Australia, in chain volume terms and current prices, with total factor income by division and gross
state product (total, per capita and real gross state income). The release used here covers 1989-90
to 2024-25. Chain volume series are in the reference year's prices and are not additive across
industries; shares and sums should use current prices.

Data: ABS time series workbooks (tables 1 to 10), CC BY 4.0. "Ownership of dwellings" is not an
ANZSIC division and is left out of the division rows (it is included in the totals).
"""

from __future__ import annotations

import pandas as pd

from . import abs_tsw, schema, store

SOURCE = "abs_state_accounts"
LICENCE = "CC BY 4.0, Australian Bureau of Statistics"
RELEASE = "2024-25-financial-year"
BASE = (
    "https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-state-accounts/"
    f"{RELEASE}/"
)
STATE_TABLES = {
    "NSW": "5220002_Annual_NSW.xlsx",
    "VIC": "5220003_Annual_VIC.xlsx",
    "QLD": "5220004_Annual_QLD.xlsx",
    "SA": "5220005_Annual_SA.xlsx",
    "WA": "5220006_Annual_WA.xlsx",
    "TAS": "5220007_Annual_TAS.xlsx",
    "NT": "5220008_Annual_NT.xlsx",
    "ACT": "5220009_Annual_ACT.xlsx",
    "AUS": "5220010_Annual_AUS.xlsx",
}
SUMMARY_TABLE = "5220001_Annual_Gross_State_Product_All_States.xlsx"
# (item, price basis) in a series description -> (measure, unit, adjustment)
CVM = "Chain volume measures"
INDUSTRY_ITEMS = {
    ("Industry gross value added", "Chain volume measures"): ("gva_volume", "AUD m, chain volume", "chain volume"),
    ("Industry gross value added", "Current prices"): ("gva_current", "AUD m", "original"),
    ("Total factor income", "Current prices"): ("factor_income", "AUD m", "original"),
}
SUMMARY_ITEMS = {
    ("Gross state product", "Chain volume measures"): ("gsp_volume", "AUD m, chain volume", "chain volume"),
    ("Gross domestic product", "Chain volume measures"): ("gsp_volume", "AUD m, chain volume", "chain volume"),
    ("Gross state product", "Current prices"): ("gsp_current", "AUD m", "original"),
    ("Gross domestic product", "Current prices"): ("gsp_current", "AUD m", "original"),
    ("Gross state product per capita", CVM): ("gsp_per_capita", "AUD, chain volume", "chain volume"),
    ("GDP per capita", "Chain volume measures"): ("gsp_per_capita", "AUD, chain volume", "chain volume"),
    ("Real gross state income", "Chain volume measures"): ("real_income", "AUD m, chain volume", "chain volume"),
    ("Real gross domestic income", "Chain volume measures"): ("real_income", "AUD m, chain volume", "chain volume"),
}
GEO = schema.STATE_NAMES | {"Australia": "AUS"}


def _split(description: str) -> tuple[str, str, str]:
    """'Mining (B) ;  Industry gross value added: Chain volume measures ;' -> ('Mining (B)', item, basis)."""
    parts = [p.strip() for p in description.split(";")]
    item, _, basis = parts[1].rpartition(":")
    return parts[0], item.strip(), basis.strip()


def _fy(date: pd.Series) -> pd.Series:
    """Year ending June -> first day of the financial year."""
    return pd.to_datetime(dict(year=date.dt.year - 1, month=7, day=1))


def tidy_industry(raw: pd.DataFrame, geo: str, vintage: str) -> pd.DataFrame:
    parts = raw["description"].map(_split)
    d = raw.assign(
        head=[p[0] for p in parts], key=[(p[1], p[2]) for p in parts], series_type=raw["series_type"].fillna("")
    )
    d = d[d["key"].isin(INDUSTRY_ITEMS.keys())]
    code = d["head"].str.extract(r"\(([A-S])\)$", expand=False)
    total = d["head"].eq("Total all industries")
    d = d[code.notna() | total].assign(code=code.fillna(""))
    meta = d["key"].map(INDUSTRY_ITEMS)
    return pd.DataFrame(
        {
            "measure": [m[0] for m in meta],
            "unit": [m[1] for m in meta],
            "adjustment": [m[2] for m in meta],
            "industry_level": d["code"].map(lambda c: "division" if c else "total"),
            "industry_code": d["code"],
            "industry_label": d["head"].str.replace(r"\s*\([A-S]\)$", "", regex=True),
            "geo_level": "AUS" if geo == "AUS" else "STE",
            "geo_code": geo,
            "period_type": "fy",
            "period": _fy(d["date"]),
            "value": d["value"],
            "vintage": vintage,
        }
    )


def tidy_summary(raw: pd.DataFrame, vintage: str) -> pd.DataFrame:
    parts = raw["description"].map(_split)
    d = raw.assign(head=[p[0] for p in parts], key=[(p[1], p[2]) for p in parts])
    d = d[d["key"].isin(SUMMARY_ITEMS.keys()) & d["head"].isin(GEO.keys())]
    meta = d["key"].map(SUMMARY_ITEMS)
    geo = d["head"].map(GEO)
    return pd.DataFrame(
        {
            "measure": [m[0] for m in meta],
            "unit": [m[1] for m in meta],
            "adjustment": [m[2] for m in meta],
            "industry_level": "total",
            "industry_code": "",
            "industry_label": "All industries",
            "geo_level": geo.map(lambda g: "AUS" if g == "AUS" else "STE"),
            "geo_code": geo,
            "period_type": "fy",
            "period": _fy(d["date"]),
            "value": d["value"],
            "vintage": vintage,
        }
    )


def build() -> pd.DataFrame:
    vintage = f"ABS 5220.0 {RELEASE}"
    frames = []
    for geo, name in STATE_TABLES.items():
        path = store.download(SOURCE, BASE + name, name, LICENCE)
        frames.append(tidy_industry(abs_tsw.read(path), geo, vintage))
    summary = abs_tsw.read(store.download(SOURCE, BASE + SUMMARY_TABLE, SUMMARY_TABLE, LICENCE))
    frames.append(tidy_summary(summary, vintage))
    panel = schema.make(pd.concat(frames, ignore_index=True), source=SOURCE, industry_scheme="ANZSIC06")
    store.write_panel(panel, SOURCE, "industry_state_fy")
    return panel
