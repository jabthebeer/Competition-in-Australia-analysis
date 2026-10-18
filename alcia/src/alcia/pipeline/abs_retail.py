"""ABS Retail Trade (8501.0) in the common panel format.

Monthly turnover (current prices, original and seasonally adjusted) for 22 retail industries by state
from April 1982, and quarterly chain-volume turnover (seasonally adjusted) for the six industry groups
by state. The monthly series ends in June 2025. Industries map to ANZSIC through
``alcia.pipeline.concord`` (ABS Retail Trade methodology). Data: ABS Data API, dataflow RT, CC BY 4.0.
"""

from __future__ import annotations

import pandas as pd

from . import abs_api, concord, schema, store

SOURCE = "abs_retail"
ADJUSTMENT = {"10": "original", "20": "seasonally adjusted"}


def _period(p: pd.Series) -> pd.Series:
    q = p.str.contains("Q")
    out = pd.to_datetime(p.where(~q, "2000-01"), format="%Y-%m")
    if q.any():
        year = p[q].str[:4].astype(int)
        month = (p[q].str[-1].astype(int) - 1) * 3 + 1
        out[q] = pd.to_datetime(dict(year=year, month=month, day=1))
    return out


def tidy(raw: pd.DataFrame, measure: str, unit: str, labels: dict[str, str], vintage: str) -> pd.DataFrame:
    raw = raw[raw["REGION"] != "9"]  # Other Territories
    levels = raw["INDUSTRY"].map(concord.retail_industry)
    out = pd.DataFrame(
        {
            "measure": measure,
            "unit": unit,
            "adjustment": raw["TSEST"].map(ADJUSTMENT),
            "industry_level": [lv for lv, _ in levels],
            "industry_code": [code for _, code in levels],
            "industry_label": raw["INDUSTRY"].map(labels),
            "geo_level": raw["REGION"].map(lambda r: "AUS" if r == "AUS" else "STE"),
            "geo_code": raw["REGION"].map(lambda r: "AUS" if r == "AUS" else schema.STATE_CODES[r]),
            "period_type": raw["FREQ"].map({"M": "month", "Q": "quarter"}),
            "period": _period(raw["TIME_PERIOD"]),
            "value": raw["OBS_VALUE"],
            "vintage": vintage,
        }
    )
    return out.dropna(subset=["value"])


def build() -> pd.DataFrame:
    s = abs_api.structure("RT")
    labels = next(d for d in s["dimensions"] if d["id"] == "INDUSTRY")["codes"]
    monthly = abs_api.data("RT", "M1..10+20..M")
    quarterly = abs_api.data("RT", "M3..20..Q")
    vintage = f"ABS RT {s['version']} to {monthly['TIME_PERIOD'].max()}"
    panel = schema.make(
        pd.concat(
            [
                tidy(monthly, "turnover", "AUD m", labels, vintage),
                tidy(quarterly, "turnover_volume", "AUD m, chain volume", labels, vintage),
            ],
            ignore_index=True,
        ),
        source=SOURCE,
        industry_scheme="ANZSIC06",
    )
    store.write_panel(panel, SOURCE, "turnover_state")
    return panel
