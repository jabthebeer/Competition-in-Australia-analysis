"""OECD Product Market Regulation indicators (PMR), Australia: economy-wide and sector indicators.

SDMX dataflow ``OECD.ECO.GCRD,DSD_PMR@DF_PMR``, every indicator for Australia, for each vintage the OECD
publishes (2018 and 2023 at present). Scale 0 to 6, higher is more restrictive. Indicators the OECD does not
compute for Australia are left out.
"""

from __future__ import annotations

from . import oecd_sdmx
from .base import Release, Table, fetch_files

AGENCY, FLOW, KEY = "OECD.ECO.GCRD", "DSD_PMR@DF_PMR", "AUS.."
SOURCE = oecd_sdmx.source("oecd_pmr", "OECD Product Market Regulation indicators (PMR): Australia", AGENCY, FLOW)


def discover() -> Release:
    return oecd_sdmx.discover(SOURCE, AGENCY, FLOW, KEY)


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def build(release: Release) -> dict[str, Table]:
    rows = oecd_sdmx.read(SOURCE, release)
    oecd_sdmx.check(rows, "REF_AREA", {"AUS"})
    oecd_sdmx.check(rows, "UNIT_MEASURE", {"0_TO_6"})
    out = [
        {"measure": r["MEASURE"], "label": r["Measure"], "year": int(r["TIME_PERIOD"]), "value": oecd_sdmx.obs(r)}
        for r in rows
        if oecd_sdmx.obs(r) is not None
    ]
    t = Table(
        description=(
            "OECD Product Market Regulation indicators for Australia (economy-wide PMR, its components and the "
            "sector indicators), by PMR vintage. Scale 0-6, higher = more restrictive. E.g. measure PMR is the "
            "economy-wide indicator; SERVBARRIER barriers in service sectors; ADREG_BURDEN administrative and "
            "regulatory burden."
        ),
        columns={
            "measure": "code: OECD PMR measure",
            "label": "text",
            "year": "PMR vintage (year)",
            "value": "index, 0-6 scale (higher = more restrictive)",
        },
        keys=("measure", "year"),
        rows=out,
    )
    t.description += f" Vintages {oecd_sdmx.years(t)}."
    return {"indicators": t}
