"""CABEE in the common panel format: businesses, entries and exits by ANZSIC class, state and year.

Built from the stitched class x state x employment-size panel (``alicia.outcomes.cabee``: releases
from Jun 2007-Jun 2009 to Jul 2021-Jun 2025, years 2007-08 to 2024-25, each year from the release in
which it is final). Data: ABS, CC BY 4.0.

Levels jump where the releases join: the Jul 2017-Jun 2021 release put 2.31 million businesses at
the end of 2019-20, against 2.42 million in the Jul 2016-Jun 2020 release. Compare rates (entries or
exits per business at the start of the year) across that join, not counts; the overlaps file holds
the second vintage of each year for checks. From 2021-22 the 1-19 employee band is the sum of the
published 1-4 and 5-19 bands.
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
    path = store.PROCESSED / SOURCE / "cabee_class_state_fy.csv.gz"
    if not path.exists():
        from ..outcomes import cabee

        cabee.build()
    p = pd.read_csv(path, dtype={"anzsic": str})
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
