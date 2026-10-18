"""City of Melbourne Census of Land Use and Employment (CLUE): business establishments by ANZSIC class.

The dataset "Business establishments location and industry classification" (data.melbourne.vic.gov.au,
CC BY 4.0) lists every business establishment in the municipality in each census year from 2002 to
2024: trading name, address, CLUE small area and ANZSIC 2006 class. Each premises an organisation
occupies counts as a separate establishment. Coverage is one municipality (LGA 24600), so it suits
Victorian or Melbourne-specific changes and fine local comparisons (small area x class x year).

CLUE splits a few ANZSIC classes (men's, women's and children's clothing; convenience stores;
alternative health). Those codes are mapped back to their ANZSIC 2006 class (CLUE_SPLITS), and rows
coded 0000 (vacant space) are dropped.

Because each row has a trading name and an ANZSIC class assigned by City of Melbourne staff, the data
also measure how well the name rules in ``alicia.pipeline.names`` work (``classifier_validation``).
"""

from __future__ import annotations

import hashlib
import json

import pandas as pd

from .. import anzsic
from . import names, schema, store

SOURCE = "clue_melbourne"
LICENCE = "CC BY 4.0, City of Melbourne"
DATASET = "business-establishments-with-address-and-industry-classification"
URL = f"https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/{DATASET}/exports/csv?delimiter=%2C"
LGA_MELBOURNE = "24600"  # ASGS 2021 LGA code for the City of Melbourne
COLUMNS = ["census_year", "clue_small_area", "trading_name", "industry_anzsic4_code"]
CLUE_SPLITS = {
    "4111": "4110",  # convenience stores -> supermarket and grocery stores
    "4254": "4251",  # men's clothing
    "4255": "4251",  # women's clothing
    "4256": "4251",  # children's clothing
    "4257": "4252",  # men's footwear
    "4258": "4252",  # women's footwear
    "8537": "8539",  # alternative health -> other allied health services
}


def read() -> pd.DataFrame:
    path = store.download(SOURCE, URL, "business_establishments.csv", LICENCE)
    d = pd.read_csv(path, dtype=str, usecols=COLUMNS, keep_default_na=False)
    d["year"] = d["census_year"].str[:4].astype(int)
    d["code"] = d["industry_anzsic4_code"].str.strip().str.zfill(4).replace(CLUE_SPLITS)
    return d[d["code"] != "0000"]


def build() -> pd.DataFrame:
    d = read()
    valid = d["code"].map(lambda c: anzsic.name(c) is not None and len(c) == 4)
    d = d[valid]
    parts = []
    for geo_level, col in (("CLUE_AREA", "clue_small_area"), ("LGA", None)):
        keys = ["year", "code"] + ([col] if col else [])
        c = d.groupby(keys).size().rename("value").reset_index()
        parts.append(
            pd.DataFrame(
                {
                    "industry_code": c["code"],
                    "industry_label": c["code"].map(anzsic.name),
                    "geo_level": geo_level,
                    "geo_code": c[col] if col else LGA_MELBOURNE,
                    "period": pd.to_datetime(c["year"].astype(str) + "-01-01"),
                    "value": c["value"],
                }
            )
        )
    panel = schema.make(
        pd.concat(parts, ignore_index=True),
        source=SOURCE,
        measure="establishments",
        unit="count",
        adjustment="original",
        industry_scheme="ANZSIC06",
        industry_level="class",
        period_type="year",
        vintage="CLUE 2002-2024 (dataset processed 16 Mar 2026)",
    )
    store.write_panel(panel, SOURCE, "establishments_area_year")
    classifier_validation(d)
    return panel


def half(name: str) -> str:
    """Fixed split of names: rules were revised on "tuning" names only; "holdout" names test them."""
    return ("tuning", "holdout")[int(hashlib.sha256(name.upper().encode()).hexdigest(), 16) % 2]


def classifier_validation(d: pd.DataFrame | None = None) -> dict:
    """Precision of names.classify against CLUE's ANZSIC classes, one row per trading name x class."""
    d = read() if d is None else d
    u = d[d["trading_name"].str.strip() != ""].drop_duplicates(["trading_name", "code"])
    u = u.assign(half=u["trading_name"].map(half))
    result = {
        "rules_version": names.VERSION,
        "source": "CLUE establishments 2002-2024, distinct trading name x ANZSIC class pairs",
    }
    for h in ("holdout", "tuning"):
        g = u[u["half"] == h]
        result[h] = names.validate(g["trading_name"].tolist(), g["code"].tolist())
    out = store.PROCESSED / SOURCE / "classifier_validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
