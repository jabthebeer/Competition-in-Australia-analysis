"""GDP per head, population and trade openness for the OECD economies, from the World Bank's World Development
Indicators (API v2).

Each indicator's licence is read from the API's own metadata (``License_Type``), not assumed, and is recorded
in the manifest with the download.
"""

from __future__ import annotations

import csv
import json

from ..pipeline import store
from . import OECD, OUT

SOURCE = "wb_wdi"
API = "https://api.worldbank.org/v2"
INDICATORS = {
    "NY.GDP.PCAP.PP.KD": "gdp_per_head_ppp",  # GDP per capita, PPP (constant 2021 international $)
    "SP.POP.TOTL": "population",
    "NE.TRD.GNFS.ZS": "trade_share_gdp",  # exports plus imports of goods and services, % of GDP
}
YEARS = (2010, 2025)


def data_url(indicator: str, countries: list[str] | None = None) -> str:
    return (
        f"{API}/country/{';'.join(countries or OECD)}/indicator/{indicator}"
        f"?format=json&date={YEARS[0]}:{YEARS[1]}&per_page=2000"
    )


def meta_url(indicator: str) -> str:
    return f"{API}/sources/2/series/{indicator}/metadata?format=json"


def licence(meta: list | dict) -> tuple[str, str]:
    """(indicator name, licence with its URL) from the series metadata response."""
    fields = {m["id"]: m["value"] for m in meta["source"][0]["concept"][0]["variable"][0]["metatype"]}
    if "License_Type" not in fields:
        raise ValueError("WDI metadata gives no licence")
    url = fields.get("License_URL", "")
    return fields.get("IndicatorName", ""), f"{fields['License_Type']}, World Bank" + (f" ({url})" if url else "")


def parse(response: list, indicator: str) -> list[dict]:
    """(country, year, value) from a WDI data response; missing values are dropped."""
    if not isinstance(response, list) or len(response) < 2:
        raise ValueError(f"{indicator}: unexpected WDI response {str(response)[:120]}")
    page = response[0]
    if int(page.get("pages", 1)) > 1:
        raise ValueError(f"{indicator}: the response has more than one page; raise per_page")
    return [
        {
            "country": r["countryiso3code"],
            "country_name": r["country"]["value"],
            "indicator": INDICATORS[indicator],
            "year": int(r["date"]),
            "value": float(r["value"]),
        }
        for r in response[1] or []
        if r["value"] is not None
    ]


def build(refresh: bool = False) -> list[dict]:
    """Download the three indicators (with their metadata) and write data/processed/international/wdi.csv."""
    rows = []
    for ind in INDICATORS:
        name = ind.replace(".", "_")
        meta_path = store.download(SOURCE, meta_url(ind), f"{name}_metadata.json", "World Bank", refresh=refresh)
        _, lic = licence(json.loads(meta_path.read_text("utf-8")))
        store.record_download(SOURCE, meta_path, meta_url(ind), lic)
        path = store.download(SOURCE, data_url(ind), f"{name}.json", lic, refresh=refresh)
        rows += parse(json.loads(path.read_text("utf-8")), ind)
    rows.sort(key=lambda r: (r["country"], r["indicator"], r["year"]))
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "wdi.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


def read() -> list[dict]:
    with (OUT / "wdi.csv").open(encoding="utf-8") as f:
        return [{**r, "year": int(r["year"]), "value": float(r["value"])} for r in csv.DictReader(f)]
