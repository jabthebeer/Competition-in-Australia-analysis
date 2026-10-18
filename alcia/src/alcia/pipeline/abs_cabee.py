"""CABEE in the common panel format: businesses, entries and exits by ANZSIC class, state and year.

Built from the stitched class x state x employment-size panel (``alcia.outcomes.cabee``, archived
releases 2007-08 to 2019-20, each year from the release in which it is final). Data: ABS, CC BY 4.0.
"""

from __future__ import annotations

import pandas as pd

from . import schema, store

SOURCE = "abs_cabee"
MEASURES = {"start": "businesses_start", "entries": "entries", "exits": "exits", "end": "businesses_end"}
BANDS = {
    "total": "",
    "nonemp": "non-employing",
    "1-19": "1-19 employees",
    "20-199": "20-199 employees",
    "200+": "200+ employees",
}


def build() -> pd.DataFrame:
    p = pd.read_csv(store.PROCESSED / SOURCE / "cabee_class_state_fy.csv.gz", dtype={"anzsic": str})
    p = p[p["measure"].isin(MEASURES) & p["band"].isin(BANDS)]
    out = pd.DataFrame(
        {
            "measure": p["measure"].map(MEASURES),
            "industry_code": p["anzsic"],
            "geo_code": p["state"],
            "breakdown": p["band"].map(BANDS),
            # Financial years are named by their ending year; the period is the year's first day.
            "period": pd.to_datetime((p["fy"] - 1).astype(str) + "-07-01"),
            "value": p["value"],
            "vintage": p["release"],
        }
    )
    panel = schema.make(
        out,
        source=SOURCE,
        unit="count",
        adjustment="original",
        industry_scheme="ANZSIC06",
        industry_level="class",
        geo_level="STE",
        period_type="fy",
    )
    store.write_panel(panel, SOURCE, "class_state_fy")
    return panel
