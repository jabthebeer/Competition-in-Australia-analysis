"""ABS Data by Region: businesses and employee jobs by ANZSIC division for SA2s and LGAs.

Two dataflows of the ABS Data API (CC BY 4.0) on ASGS Edition 3 (2021) boundaries:
- ABS_REGIONAL_ASGS2021 for SA2s, states and Australia, and ABS_REGIONAL_LGA2021 for LGAs (2021
  boundaries);
- "Number of businesses by industry - 30 June" (CABEE_*: businesses actively trading in GST, by
  division, counted at the main business address), 2021 to 2025;
- "Jobs in Australia" (LEED_*: employee jobs by division of the employer, from tax records linked
  in the ABS Linked Employer Employee Dataset), years ended 30 June 2018 to 2023.

There are no entries or exits at this level here, only stocks; local entry and exit rates need the
CABEE SA2 and LGA cubes or the register flows (ABN, ASIC) apportioned from postcodes.
"""

from __future__ import annotations

import pandas as pd

from .. import anzsic
from . import abs_api, schema, store

SOURCE = "abs_regional"
DIVISIONS = "ABCDEFGHIJKLMNOPQRS"
# Measure codes from the flows' MEASURE codelist (checked against their labels, 18 Oct 2026).
CABEE = {"CABEE_5": ""} | dict(
    zip(
        [f"CABEE_{i}" for i in (19, 28, 27, 23, 21, 37, 34, 17, 36, 26, 24, 33, 31, 18, 32, 22, 25, 20, 30)],
        DIVISIONS,
        strict=True,
    )
)
LEED = {"LEED_24": ""} | {f"LEED_{i}": d for i, d in zip(range(5, 24), DIVISIONS, strict=True)}
# (dataflow, region types queried, region column); state and Australia rows come from the ASGS flow.
FLOWS = (("ABS_REGIONAL_ASGS2021", "SA2+STE+AUS", "ASGS_2021"), ("ABS_REGIONAL_LGA2021", "LGA2021", "LGA_2021"))
GEO_LEVELS = {"SA2": "SA2", "STE": "STE", "AUS": "AUS", "LGA2021": "LGA"}


def tidy(raw: pd.DataFrame, region_col: str, vintage: str) -> pd.DataFrame:
    d = raw.assign(value=pd.to_numeric(raw["OBS_VALUE"], errors="coerce")).dropna(subset=["value"])
    d = d[~((d["REGIONTYPE"] == "STE") & ~d[region_col].astype(str).isin(schema.STATE_CODES))]  # Other Territories
    geo_level = d["REGIONTYPE"].map(GEO_LEVELS)
    geo_code = d[region_col].astype(str)
    geo_code = geo_code.where(geo_level != "STE", geo_code.map(schema.STATE_CODES))
    year = d["TIME_PERIOD"].astype(int)
    is_cabee = d["MEASURE"].isin(CABEE)
    division = d["MEASURE"].map(CABEE | LEED)
    return pd.DataFrame(
        {
            "measure": is_cabee.map({True: "businesses", False: "employee_jobs"}),
            "unit": "count",
            "industry_scheme": division.map(lambda c: "ANZSIC06" if c else "none"),
            "industry_level": division.map(lambda c: "division" if c else "total"),
            "industry_code": division,
            "industry_label": division.map(lambda c: anzsic.name(c) if c else ""),
            "geo_level": geo_level,
            "geo_code": geo_code,
            # Business counts are at 30 June; jobs are for the financial year ending 30 June.
            "period_type": is_cabee.map({True: "day", False: "fy"}),
            "period": pd.to_datetime(
                [f"{y}-06-30" if c else f"{y - 1}-07-01" for y, c in zip(year, is_cabee, strict=True)]
            ),
            "value": d["value"],
            "vintage": vintage,
        }
    )


def build() -> pd.DataFrame:
    key = "+".join([*CABEE, *LEED])
    parts = []
    for flow, region_types, region_col in FLOWS:
        raw = abs_api.data(flow, f"{key}.{region_types}..A")
        version = raw["DATAFLOW"].iloc[0].split("(")[-1].rstrip(")")
        parts.append(tidy(raw, region_col, f"{flow} {version}"))
    panel = schema.make(pd.concat(parts, ignore_index=True), source=SOURCE, adjustment="original", breakdown="")
    store.write_panel(panel, SOURCE, "division_local_year")
    return panel
