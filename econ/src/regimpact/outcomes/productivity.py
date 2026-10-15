"""Real output and wages per worker by state x ANZSIC division x financial year (public data).

- Industry gross value added, chain volume measures, and compensation of employees (current
  prices): ABS Australian National Accounts: State Accounts (5220.0), annual, from 1989-90.
- Employed persons by state x industry division: ABS Labour Force, Australia, Detailed
  (6291.0.55.001) Table 05, quarterly (Nov, Feb, May, Aug), averaged over each financial year.

Labour productivity here is real value added per employed person (hours by state and industry
are not published before 2011-12). Wages are compensation of employees per employed person,
deflated by the capital-city CPI. Data: Australian Bureau of Statistics, CC BY 4.0.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .. import anzsic
from .abs_series import cached_download, read_timeseries_workbook

STATE_ACCOUNTS = (
    "https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-state-"
    "accounts/2024-25-financial-year/{file}"
)
STATE_FILES = {
    "NSW": "5220002_Annual_NSW.xlsx",
    "VIC": "5220003_Annual_VIC.xlsx",
    "QLD": "5220004_Annual_QLD.xlsx",
    "SA": "5220005_Annual_SA.xlsx",
    "WA": "5220006_Annual_WA.xlsx",
    "TAS": "5220007_Annual_TAS.xlsx",
    "NT": "5220008_Annual_NT.xlsx",
    "ACT": "5220009_Annual_ACT.xlsx",
}
LFS05 = (
    "https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia-detailed/"
    "mar-2026/6291005.xlsx"
)
LFS_STATES = {
    "New South Wales": "NSW",
    "Victoria": "VIC",
    "Queensland": "QLD",
    "South Australia": "SA",
    "Western Australia": "WA",
    "Tasmania": "TAS",
    "Northern Territory": "NT",
    "Australian Capital Territory": "ACT",
}


def _cache() -> Path:
    return Path(__file__).resolve().parents[3] / ".cache" / "abs" / "productivity"


def _fy(dates: pd.Series) -> pd.Series:
    return dates.dt.year + (dates.dt.month >= 7).astype(int)


def state_accounts() -> pd.DataFrame:
    """fy, state, division, gva_cvm ($m), coe ($m, current prices) for every industry division."""
    rows = []
    for state, file in STATE_FILES.items():
        df = read_timeseries_workbook(cached_download(STATE_ACCOUNTS.format(file=file), _cache() / file))
        for measure, pattern in (
            ("gva_cvm", r"Industry gross value added: Chain volume measures ;$"),
            ("coe", r"Total compensation of employees: Current prices ;$"),
        ):
            sel = df[df["description"].str.contains(pattern, regex=True)]
            for desc, g in sel.groupby("description"):
                m = re.search(r"\(([A-S])\)", desc)
                if not m:
                    continue
                rows.append(
                    pd.DataFrame(
                        {
                            "fy": g["date"].dt.year,
                            "state": state,
                            "division": m.group(1),
                            "measure": measure,
                            "value": g["value"].to_numpy(),
                        }
                    )
                )
    out = pd.concat(rows, ignore_index=True)
    return out.pivot_table(index=["fy", "state", "division"], columns="measure", values="value").reset_index()


def employment() -> pd.DataFrame:
    """fy, state, division, employed ('000, average of the four quarters in the financial year)."""
    df = read_timeseries_workbook(cached_download(LFS05, _cache() / "6291005.xlsx"))
    names = {anzsic.name(d).lower(): d for d in "ABCDEFGHIJKLMNOPQRS"}
    rows = []
    for desc, g in df[df["description"].str.endswith("Employed total ;")].groupby("description"):
        parts = [p.strip(" >") for p in desc.split(";")]
        state, industry = LFS_STATES.get(parts[0]), names.get(parts[1].lower())
        if state and industry:
            rows.append(
                pd.DataFrame(
                    {
                        "fy": _fy(g["date"]).to_numpy(),
                        "state": state,
                        "division": industry,
                        "employed": g["value"].to_numpy(),
                    }
                )
            )
    out = pd.concat(rows, ignore_index=True)
    counts = out.groupby(["fy", "state", "division"])["employed"].agg(["mean", "count"]).reset_index()
    full = counts[counts["count"] == 4]  # complete financial years only
    return full.rename(columns={"mean": "employed"}).drop(columns="count")


def panel(cpi_annual: pd.DataFrame | None = None) -> pd.DataFrame:
    """Merged panel with gva_per_worker ($ per person, chain volume) and coe_per_worker (nominal, and real
    when ``cpi_annual`` [fy, state, cpi] is given)."""
    p = state_accounts().merge(employment(), on=["fy", "state", "division"], how="inner")
    p["gva_per_worker"] = p["gva_cvm"] * 1e6 / (p["employed"] * 1e3)
    p["coe_per_worker"] = p["coe"] * 1e6 / (p["employed"] * 1e3)
    if cpi_annual is not None:
        p = p.merge(cpi_annual, on=["fy", "state"], how="left")
        p["real_coe_per_worker"] = p["coe_per_worker"] / p["cpi"] * 100
    return p
