"""US Business Dynamics Statistics (Census Bureau): employer firms, births and deaths by NAICS sector.

The US is not in the OECD's employer business demography, so its entry and exit rates come from here (the plan's
fixed comparison list includes it; it is not in the approved core group). Two published CSV tables of the latest
release are used: by sector (firms, establishments, employment, firm deaths) and by sector and firm age (firm
births are firms aged 0). Like the OECD data, BDS covers employer businesses only; it uses NAICS 2017 sectors,
which are mapped to the common industry groups in phase P2. Suppressed cells ("X", "D", "S") are left out.
"""

from __future__ import annotations

import io
import re

import pandas as pd

from ..pipeline import store
from . import OUT

SOURCE = "us_bds"
BASE = "https://www2.census.gov/programs-surveys/bds/tables/time-series"
LICENCE = "Public domain as a US federal government work (17 U.S.C. 105); Census Bureau terms not re-checked"
TABLES = {"sec": "by NAICS sector", "sec_fa": "by NAICS sector and firm age"}
MEASURES = (
    "firms",
    "estabs",
    "emp",
    "denom",
    "estabs_entry",
    "estabs_exit",
    "job_creation_births",
    "job_destruction_deaths",
    "firmdeath_firms",
    "firmdeath_emp",
)


def latest_release(listing: str) -> str:
    """The newest release folder (a year) in the time-series directory listing."""
    years = sorted(set(re.findall(r'href="(\d{4})/"', listing)))
    if not years:
        raise ValueError("BDS: no release folders in the directory listing")
    return years[-1]


def parse(text: str) -> pd.DataFrame:
    """Long rows (year, sector, fage, measure, value) from a BDS CSV table; suppressed cells dropped."""
    df = pd.read_csv(io.StringIO(text), dtype=str)
    if not {"year", "sector"} <= set(df.columns):
        raise ValueError(f"BDS: unexpected columns {list(df.columns)[:6]}")
    if "fage" not in df.columns:
        df["fage"] = ""
    keep = [m for m in MEASURES if m in df.columns]
    long = df.melt(id_vars=["year", "sector", "fage"], value_vars=keep, var_name="measure", value_name="value")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    long["year"] = long["year"].astype(int)
    return long.sort_values(["sector", "fage", "measure", "year"]).reset_index(drop=True)


def build(refresh: bool = False) -> pd.DataFrame:
    """Download the latest release's sector tables and write data/processed/international/us_bds.parquet."""
    import httpx

    listing = httpx.get(BASE + "/", headers={"User-Agent": store.USER_AGENT}, timeout=60, follow_redirects=True)
    listing.raise_for_status()
    rel = latest_release(listing.text)
    frames = []
    for t in TABLES:
        name = f"bds{rel}_{t}.csv"
        path = store.download(SOURCE, f"{BASE}/{rel}/{name}", name, LICENCE, refresh=refresh)
        frames.append(parse(path.read_text("utf-8")).assign(table=t, release=rel))
    df = pd.concat(frames, ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT / "us_bds.parquet", index=False)
    return df


def read() -> pd.DataFrame:
    return pd.read_parquet(OUT / "us_bds.parquet")
