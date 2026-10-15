"""Readers for ABS time-series spreadsheets and the ABS Data API (CPI).

ABS time-series workbooks ("Data1", "Data2", ... sheets) put each series in a column: row 0
holds the description, rows 1-9 metadata (unit, series type, frequency, series ID), and data
start at row 10 with the period date in column 0. Data: Australian Bureau of Statistics, CC BY 4.0.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pandas as pd

from ..legislation.base import make_client
from ..legislation.http import Fetcher

DATA_API = "https://data.api.abs.gov.au/rest/data"
CPI_REGIONS = {
    "1": "Sydney",
    "2": "Melbourne",
    "3": "Brisbane",
    "4": "Adelaide",
    "5": "Perth",
    "6": "Hobart",
    "7": "Darwin",
    "8": "Canberra",
    "50": "Eight capitals",
}
CITY_STATE = {
    "Sydney": "NSW",
    "Melbourne": "VIC",
    "Brisbane": "QLD",
    "Adelaide": "SA",
    "Perth": "WA",
    "Hobart": "TAS",
    "Darwin": "NT",
    "Canberra": "ACT",
}


def cached_download(url: str, path: Path) -> Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with make_client() as client:
            path.write_bytes(Fetcher(client).content(url))
    return path


def read_timeseries_workbook(path: Path) -> pd.DataFrame:
    """Long table: series_id, description, unit, series_type, frequency, date, value."""
    frames = []
    for sheet in pd.ExcelFile(path).sheet_names:
        if not sheet.startswith("Data"):
            continue
        raw = pd.read_excel(path, sheet_name=sheet, header=None)
        meta = raw.iloc[:10]
        data = raw.iloc[10:]
        for col in range(1, raw.shape[1]):
            desc = meta.iat[0, col]
            if not isinstance(desc, str):
                continue
            values = pd.to_numeric(data.iloc[:, col], errors="coerce")
            frames.append(
                pd.DataFrame(
                    {
                        "series_id": meta.iat[9, col],
                        "description": " ".join(desc.split()),
                        "unit": meta.iat[1, col],
                        "series_type": meta.iat[2, col],
                        "frequency": meta.iat[4, col],
                        "date": pd.to_datetime(data.iloc[:, 0]),
                        "value": values,
                    }
                )
            )
    out = pd.concat(frames, ignore_index=True)
    return out.dropna(subset=["date", "value"])


def fetch_cpi(
    index_codes: list[str],
    regions: list[str] | None = None,
    start: str = "2000-Q1",
    end: str = "2025-Q3",
    cache_dir: Path | None = None,
) -> pd.DataFrame:
    """CPI index numbers (original, quarterly) for expenditure classes or groups by capital city.

    Dataflow ABS:CPI 1.1.0 (17th series, quarterly, to 2025-Q3). Columns: index_code, region, city,
    period, value."""
    regions = regions or [r for r in CPI_REGIONS if r != "50"]
    key = f"1.{'+'.join(index_codes)}.10.{'+'.join(regions)}.Q"
    url = f"{DATA_API}/ABS,CPI,1.1.0/{key}?startPeriod={start}&endPeriod={end}"
    cache_dir = cache_dir or Path(__file__).resolve().parents[3] / ".cache" / "abs" / "cpi"
    name = f"cpi_{hashlib.sha256(url.encode()).hexdigest()[:16]}.csv"
    path = cache_dir / name
    if not path.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        with make_client() as client:
            resp = client.get(url, headers={"Accept": "application/vnd.sdmx.data+csv"})
            resp.raise_for_status()
            path.write_text(resp.text, encoding="utf-8")
    df = pd.read_csv(io.StringIO(path.read_text(encoding="utf-8")), dtype={"INDEX": str, "REGION": str})
    out = df.rename(columns={"INDEX": "index_code", "REGION": "region", "TIME_PERIOD": "period", "OBS_VALUE": "value"})
    out["city"] = out["region"].map(CPI_REGIONS)
    return out[["index_code", "region", "city", "period", "value"]].assign(source_url=url)
