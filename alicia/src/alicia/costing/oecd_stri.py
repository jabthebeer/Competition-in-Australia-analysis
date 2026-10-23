"""OECD Services Trade Restrictiveness Index (STRI), Australia: the main index by sector and year.

SDMX dataflow ``OECD.TAD.TPD,DSD_STRI@DF_STRI_MAIN``, the main STRI for Australia in each of the OECD's
services sectors (ISIC Rev. 4 based), annual. Index 0 (open) to 1 (closed).
"""

from __future__ import annotations

from . import oecd_sdmx
from .base import Release, Table, fetch_files

AGENCY, FLOW, KEY = "OECD.TAD.TPD", "DSD_STRI@DF_STRI_MAIN", "A.AUS.STRI....."
SOURCE = oecd_sdmx.source("oecd_stri", "OECD Services Trade Restrictiveness Index (STRI): Australia", AGENCY, FLOW)


def discover() -> Release:
    return oecd_sdmx.discover(SOURCE, AGENCY, FLOW, KEY)


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def build(release: Release) -> dict[str, Table]:
    rows = oecd_sdmx.read(SOURCE, release)
    oecd_sdmx.check(rows, "REF_AREA", {"AUS"})
    oecd_sdmx.check(rows, "STRI_TYPE", {"MAIN_STRI"})
    oecd_sdmx.check(rows, "UNIT_MEASURE", {"IX"})
    out = [
        {
            "sector": r["ACTIVITY"],
            "label": r["Economic activity"],
            "year": int(r["TIME_PERIOD"]),
            "value": oecd_sdmx.obs(r),
        }
        for r in rows
        if oecd_sdmx.obs(r) is not None
    ]
    t = Table(
        description=(
            "OECD Services Trade Restrictiveness Index (main STRI) for Australia by services sector. Index 0 "
            "(completely open to foreign services suppliers) to 1 (completely closed). Sector codes are the "
            "OECD's ISIC Rev. 4 based codes (e.g. H51 air transport, M691 legal, M692 accounting)."
        ),
        columns={
            "sector": "code: OECD STRI sector (ISIC Rev. 4 based)",
            "label": "text",
            "year": "year",
            "value": "index, 0-1 (higher = more restrictive)",
        },
        keys=("sector", "year"),
        rows=out,
    )
    t.description += f" Years {oecd_sdmx.years(t)}."
    return {"sectors": t}
