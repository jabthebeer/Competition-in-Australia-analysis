"""OECD FDI Regulatory Restrictiveness Index (FDI RRI), Australia: by sector and by type of restriction.

SDMX dataflow ``OECD.DAF.INV,DSD_FDIRRI_SCORES@DF_FDIRRI_SCORES``. Two tables:

- ``sectors``: the total index (all types of restriction) for each sector and year;
- ``restriction_types``: the all-activities index by type of restriction (foreign equity limits, screening and
  approval, restrictions on key foreign personnel, other restrictions) and the total, by year.

Index 0 (open) to 1 (closed).
"""

from __future__ import annotations

from . import oecd_sdmx
from .base import Release, Table, fetch_files

AGENCY, FLOW, KEY = "OECD.DAF.INV", "DSD_FDIRRI_SCORES@DF_FDIRRI_SCORES", "AUS...."
SOURCE = oecd_sdmx.source(
    "oecd_fdi_rri", "OECD FDI Regulatory Restrictiveness Index (FDI RRI): Australia", AGENCY, FLOW
)
UNIT = "index, 0-1 (higher = more restrictive)"


def discover() -> Release:
    return oecd_sdmx.discover(SOURCE, AGENCY, FLOW, KEY)


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def build(release: Release) -> dict[str, Table]:
    rows = oecd_sdmx.read(SOURCE, release)
    oecd_sdmx.check(rows, "REF_AREA", {"AUS"})
    oecd_sdmx.check(rows, "MEASURE", {"RR"})
    oecd_sdmx.check(rows, "UNIT_MEASURE", {"IX"})
    sectors = [
        {
            "sector": r["ACTIVITY"],
            "label": r["Economic activity"],
            "year": int(r["TIME_PERIOD"]),
            "value": oecd_sdmx.obs(r),
        }
        for r in rows
        if r["POL_CAT"] == "_T" and oecd_sdmx.obs(r) is not None
    ]
    types = [
        {
            "restriction": r["POL_CAT"],
            "label": r["Policy category"],
            "year": int(r["TIME_PERIOD"]),
            "value": oecd_sdmx.obs(r),
        }
        for r in rows
        if r["ACTIVITY"] == "_T" and oecd_sdmx.obs(r) is not None
    ]
    s = Table(
        description=(
            "OECD FDI Regulatory Restrictiveness Index for Australia by sector (all types of restriction). Index 0 "
            "(open) to 1 (closed). Sector _T = all activities (the headline index)."
        ),
        columns={"sector": "code: OECD FDI RRI activity", "label": "text", "year": "year", "value": UNIT},
        keys=("sector", "year"),
        rows=sectors,
    )
    t = Table(
        description=(
            "OECD FDI Regulatory Restrictiveness Index for Australia, all activities, by type of restriction: "
            "CLAS1_1 foreign equity limits, CLAS1_2 screening and approval, CLAS1_3 restrictions on key foreign "
            "personnel, _O other restrictions, _T total. Index 0 (open) to 1 (closed)."
        ),
        columns={"restriction": "code: OECD policy category", "label": "text", "year": "year", "value": UNIT},
        keys=("restriction", "year"),
        rows=types,
    )
    s.description += f" Years {oecd_sdmx.years(s)}."
    return {"sectors": s, "restriction_types": t}
