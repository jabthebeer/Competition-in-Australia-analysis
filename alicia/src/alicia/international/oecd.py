"""OECD datasets for the international benchmarks (forward plan, phase P1), from the OECD's SDMX service.

Each dataset is one SDMX query: a dataflow, its version and a key that selects only what the benchmarks need
(the 38 OECD members, the ISIC activities the common industry groups are built from, and the measures in
decision D-4). Raw responses (SDMX-CSV, codes only) go to ``data/raw/<source>/`` with a manifest; each tidy
table goes to ``data/processed/international/<table>.parquet``, one row per observation, with the dimensions
that vary kept as lower-case columns and the value as published (``unit_mult`` gives its power of ten).

In business demography, births are ``business_stage`` B (with ``age`` Y_LT1), deaths D and active enterprises
ACTIVE (both with ``age`` _T), and high-growth enterprises (HGE: by employment, HGT: by turnover; 10 or
20% a year over three years) are counted among enterprises with at least 10 employees, so the active enterprises
of that size are kept as their denominator. It covers employer enterprises only, and Australia,
Chile, Mexico and the US are not in it: their figures come from national sources, harmonised in phase P2.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass

import pandas as pd

from ..pipeline import store
from . import OECD, OUT
from .stan import LICENCE

SDMX = "https://sdmx.oecd.org/public/rest"

# ISIC Rev. 4 sections, plus rental and leasing (N77), which the common groups move to real estate, and the total.
SECTIONS = [*"ABCDEFGHIJKLMNOPQRS", "N77", "_T"]
ALL = "+".join(OECD)


@dataclass(frozen=True)
class Dataset:
    table: str  # processed file name (data/processed/international/<table>.parquet)
    source: str  # raw folder and manifest name
    title: str
    agency: str
    flow: str
    version: str
    key: str
    start: str  # first period
    dims: tuple[str, ...]  # SDMX dimensions kept as columns, in this order

    @property
    def url(self) -> str:
        return (
            f"{SDMX}/data/{self.agency},{self.flow},{self.version}/{self.key}?startPeriod={self.start}&format=csvfile"
        )


ACTS = "+".join(SECTIONS)
BD = ("REF_AREA", "MEASURE", "ACTIVITY", "SIZE_CLASS", "AGE", "BUSINESS_STAGE", "UNIT_MEASURE")
DATASETS = {
    d.table: d
    for d in (
        Dataset(
            "sdbs_births_deaths",
            "oecd_sdbs",
            "SDBS employer business demography: active enterprises, births and deaths, and their employment",
            "OECD.SDD.TPS",
            "DSD_SDBSBD_ISIC4@DF_BD_EMP_B_D",
            "1.0",
            f"A.{ALL}.ENT+EMP.{ACTS}._T+S_GE10._T+Y_LT1.ENT_EMP.ACTIVE+B+D.ENT_EM+PS",
            "2005",
            BD,
        ),
        Dataset(
            "sdbs_survival",
            "oecd_sdbs",
            "SDBS employer business demography: enterprises surviving one, three and five years after birth",
            "OECD.SDD.TPS",
            "DSD_SDBSBD_ISIC4@DF_BD_EMP_S",
            "1.0",
            f"A.{ALL}.ENT.{ACTS}._T.Y1+Y3+Y5.ENT_EMP.ACTIVE.ENT_EM+PT_ENT_B",
            "2005",
            BD,
        ),
        Dataset(
            "sdbs_high_growth",
            "oecd_sdbs",
            "SDBS employer business demography: high-growth enterprises (peers only, decision D-4)",
            "OECD.SDD.TPS",
            "DSD_SDBSBD_ISIC4@DF_BD_EMP_HG",
            "1.0",
            f"A.{ALL}.ENT.{ACTS}.S_GE10._T+Y4T5.ENT_EMP.HGE10+HGE20+HGT10+HGT20.ENT_EM+PT_ENT10",
            "2005",
            BD,
        ),
        Dataset(
            "sdbs_size",
            "oecd_sdbs",
            "SDBS structural business statistics: enterprises, persons employed and value added by size class",
            "OECD.SDD.TPS",
            "DSD_SDBSBSC_ISIC4@DF_SDBS_ISIC4",
            "1.0",
            f"A.{ALL}.ENTR+EMPN+VALU.{ACTS}._T+S1T9+S10T49+S_GE20+S50T249+S_GE250.",
            "2010",
            ("REF_AREA", "MEASURE", "ACTIVITY", "SIZE_CLASS", "UNIT_MEASURE"),
        ),
        Dataset(
            "stan_volumes_hours",
            "oecd_stan",
            "STAN 2025: value added at previous year's prices, and persons employed and hours worked",
            "OECD.STI.PIE",
            "DSD_STAN@DF_STAN_2025",
            "1.0",
            f"A.{ALL}.A+B+C+D_E+F+G+H+I+J+K+L+L68A+M_N+N77+O+P+Q+R+S+T+_T.B1G+EMP.Y+_Z.XDC+H+PS",
            "2005",
            ("REF_AREA", "ACTIVITY", "MEASURE", "PRICE_BASE", "UNIT_MEASURE"),
        ),
        Dataset(
            "tie_quarterly",
            "oecd_tie",
            "Timely indicators of entrepreneurship: enterprise entries, exits and bankruptcies, quarterly",
            "OECD.SDD.TPS",
            "DSD_TIE@DF_TIE",
            "1.1",
            f"Q.{ALL}.ENTRIES+EXITS+BANKRUPTCIES._T._T...",
            "2005-Q1",
            ("REF_AREA", "MEASURE", "LEGAL_FORM", "ADJUSTMENT", "UNIT_MEASURE"),
        ),
        Dataset(
            "pmr",
            "oecd_pmr_peers",
            "Product Market Regulation indicators, economy-wide and by sector (0 to 6, higher is more restrictive)",
            "OECD.ECO.GCRD",
            "DSD_PMR@DF_PMR",
            "1.4",
            f"{ALL}..",
            "2018",
            ("REF_AREA", "MEASURE"),
        ),
        Dataset(
            "stri",
            "oecd_stri_peers",
            "Services Trade Restrictiveness Index, 19 sectors (0 to 1, higher is more restrictive)",
            "OECD.TAD.TPD",
            "DSD_STRI@DF_STRI_MAIN",
            "1.0",
            f"A.{ALL}.STRI.....",
            "2014",
            ("REF_AREA", "ACTIVITY"),
        ),
        Dataset(
            "fdi_rri",
            "oecd_fdi_rri_peers",
            "FDI Regulatory Restrictiveness Index by sector (0 to 1, higher is more restrictive)",
            "OECD.DAF.INV",
            "DSD_FDIRRI_SCORES@DF_FDIRRI_SCORES",
            "2.0",
            f"{ALL}....",
            "2010",
            ("REF_AREA", "ACTIVITY", "POL_CAT", "MEASURE"),
        ),
    )
}


def parse(text: str, ds: Dataset) -> pd.DataFrame:
    """Tidy rows from an SDMX-CSV (codes only) response: the kept dimensions, period, value and unit_mult."""
    if not text.startswith("STRUCTURE") and not text.startswith("DATAFLOW"):
        raise ValueError(f"{ds.table}: the response is not SDMX-CSV ({text[:60]!r})")
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        raise ValueError(f"{ds.table}: no observations")
    missing = [d for d in ds.dims if d not in rows[0]]
    if missing:
        raise ValueError(f"{ds.table}: dimensions {missing} not in the response")
    out = pd.DataFrame(
        {
            **{d.lower(): [r[d] for r in rows] for d in ds.dims},
            "period": [r["TIME_PERIOD"] for r in rows],
            "value": pd.to_numeric([r["OBS_VALUE"] for r in rows], errors="coerce"),
            "unit_mult": pd.Series(pd.to_numeric([r.get("UNIT_MULT") or 0 for r in rows], errors="coerce"))
            .fillna(0)
            .astype(int),
            "status": [r.get("OBS_STATUS", "") for r in rows],
        }
    )
    out = out.dropna(subset=["value"]).rename(columns={"ref_area": "country"})
    return out.sort_values(list(out.columns[: len(ds.dims)]) + ["period"]).reset_index(drop=True)


def recorded_url(source: str, filename: str) -> str | None:
    """The URL the manifest records for a raw file, if any."""
    path = store.MANIFESTS / f"{source}.json"
    if not path.exists():
        return None
    want = str((store.RAW / source / filename).relative_to(store.ROOT))
    return next((f["url"] for f in json.loads(path.read_text("utf-8"))["files"] if f["file"] == want), None)


def build_one(table: str, refresh: bool = False) -> pd.DataFrame:
    ds = DATASETS[table]
    name = f"{table}.csv"
    stale = recorded_url(ds.source, name) != ds.url  # the query changed since the file was downloaded
    path = store.download(ds.source, ds.url, name, LICENCE, refresh=refresh or stale)
    df = parse(path.read_text("utf-8-sig"), ds)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT / f"{table}.parquet", index=False)
    return df


def build(refresh: bool = False) -> dict[str, int]:
    """Download every OECD dataset and write its tidy table. Returns the rows written per table."""
    return {t: len(build_one(t, refresh)) for t in DATASETS}


def read(table: str) -> pd.DataFrame:
    return pd.read_parquet(OUT / f"{table}.parquet")


# What each table is for, and the filter that picks its headline series for the coverage summary
HEADLINE = {
    "sdbs_births_deaths": ("Employer business births", {"measure": "ENT", "business_stage": "B", "size_class": "_T"}),
    "sdbs_survival": ("Survival to three years", {"measure": "ENT", "age": "Y3", "unit_measure": "ENT_EM"}),
    "sdbs_high_growth": ("High-growth enterprises (employment, 10%+)", {"business_stage": "HGE10", "age": "_T"}),
    "sdbs_size": ("Enterprises by size class", {"measure": "ENTR", "size_class": "S1T9"}),
    "stan_volumes_hours": ("Value added at previous year's prices", {"measure": "B1G", "price_base": "Y"}),
    "tie_quarterly": (
        "Quarterly company registrations (limited liability)",
        {"measure": "ENTRIES", "legal_form": "LL"},
    ),
    "pmr": ("Product market regulation (economy-wide)", {"measure": "PMR"}),
    "stri": ("Services trade restrictiveness (any sector)", {}),
    "fdi_rri": ("FDI restrictiveness (total)", {"pol_cat": "_T", "activity": "_T"}),
}


def coverage(countries: list[str]) -> dict[str, dict[str, str]]:
    """For each table, the first and last period of its headline series in each country ('' if none)."""
    out = {}
    for table, (_, where) in HEADLINE.items():
        path = OUT / f"{table}.parquet"
        if not path.exists():
            continue
        df = read(table)
        for col, val in where.items():
            df = df[df[col] == val]
        span = df.groupby("country")["period"].agg(["min", "max"])
        out[table] = {
            c: (f"{span.loc[c, 'min']} to {span.loc[c, 'max']}" if c in span.index else "") for c in countries
        }
    return out
