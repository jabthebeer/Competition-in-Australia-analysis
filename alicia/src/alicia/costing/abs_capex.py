"""ABS Private New Capital Expenditure and Expected Expenditure (5625.0): actual capital expenditure by industry.

ABS Data API dataflow ``ABS,CAPEX``: actual expenditure (measure M1), original series, Australia, by CAPEX
industry and type of asset (total, buildings and structures, equipment plant and machinery), in current prices
and chain volume measures. Quarters are summed to financial years; only complete years are kept (the last
``YEARS``). CAPEX industries are P-coded aggregates (mostly ANZSIC divisions), the mining and manufacturing
subdivisions (06-25) and divisions H, N, R and S; ``anzsic`` gives the ANZSIC 2006 code where the CAPEX
industry is one division or subdivision. Coverage: private sector; CAPEX excludes agriculture, forestry and
fishing, public administration and some other industries. Data: ABS, CC BY 4.0.

The release (reference quarter, date, next release) is read from the ABS latest-release page and the data's
time range from the Data API's availability endpoint.
"""

from __future__ import annotations

import csv
import io
import re
from collections import defaultdict

from .base import (
    ABS_LICENCE,
    Release,
    RemoteFile,
    Source,
    Table,
    abs_page,
    division_by_name,
    fetch_files,
    fy_label,
    get,
    local_path,
    release_slug,
    value,
)

PAGE = "https://www.abs.gov.au/statistics/economy/business-indicators/private-new-capital-expenditure-and-expected-expenditure-australia/latest-release"
API = "https://data.api.abs.gov.au/rest"
SOURCE = Source(
    id="abs_capex",
    title="Private New Capital Expenditure and Expected Expenditure, Australia (5625.0)",
    publisher="Australian Bureau of Statistics",
    licence=ABS_LICENCE,
    url=PAGE,
)
STRUCTURE = "application/vnd.sdmx.structure+json"
YEARS = 10
ASSETS = {"TOT": "total", "1": "buildings_structures", "2": "equipment_plant_machinery"}
FLAGS = "x = an estimate has a relative standard error of 10% to 25%; z = over 50% (too unreliable for general use)"


def _quarter(period: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d{4})-Q([1-4])", period)
    if not m:
        raise ValueError(f"not a quarter: {period!r}")
    return int(m.group(1)), int(m.group(2))


def _fy(period: str) -> int:
    y, q = _quarter(period)
    return y + 1 if q >= 3 else y


def discover() -> Release:
    page = abs_page(PAGE)
    xlsx = page.files(r"/01_current_prices_original_capex\.xlsx$")
    slug = release_slug(xlsx[0]) if xlsx else re.sub(r"\W+", "-", page.reference_period.lower())
    flows = get(f"{API}/dataflow/ABS/CAPEX/latest", accept=STRUCTURE).json()["data"]["dataflows"]
    version = flows[0]["version"]
    avail = get(
        f"{API}/availableconstraint/ABS,CAPEX,{version}/M1.CUR.TOT..10.AUS.Q/all/all?mode=available", accept=STRUCTURE
    ).json()
    region = avail["data"]["contentConstraints"][0]["cubeRegions"][0]["keyValues"]
    end = next(k for k in region if k["id"] == "TIME_PERIOD")["timeRange"]["endPeriod"]["period"][:10]
    y, m = int(end[:4]), int(end[5:7])
    last_q = f"{y}-Q{(m - 1) // 3 + 1}"
    last_fy = _fy(last_q) if last_q.endswith("Q2") else _fy(last_q) - 1
    start = f"{last_fy - YEARS}-Q3"
    url = f"{API}/data/ABS,CAPEX,{version}/M1.CUR+CVM.TOT+1+2..10.AUS.Q?startPeriod={start}&format=csvfilewithlabels"
    return Release(
        id=f"{slug} (Data API CAPEX {version}, to {last_q})",
        date=page.released,
        files=(RemoteFile(f"{slug}/capex_actual_{start}_{last_q}.csv", url),),
        page=PAGE,
        next_release=page.next_release,
        extra=(("reference_period", page.reference_period), ("api_version", version), ("last_quarter", last_q)),
    )


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def _anzsic(code: str, label: str) -> str | None:
    if re.fullmatch(r"\d{2}", code) or re.fullmatch(r"[A-S]", code):
        return code
    if code.startswith("P"):
        return division_by_name(label)
    return "TOT" if code == "TOT" else None


def build(release: Release) -> dict[str, Table]:
    text = local_path(SOURCE.id, release.files[0]).read_text("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or "OBS_VALUE" not in rows[0]:
        raise ValueError("CAPEX: the data file is not SDMX-CSV")
    for col, allowed in (("MEASURE", {"M1"}), ("TSEST", {"10"}), ("STATE", {"AUS"}), ("UNIT_MULT", {"6"})):
        seen = {r[col] for r in rows}
        if seen - allowed:
            raise ValueError(f"CAPEX: unexpected {col} {sorted(seen)}")
    acc: dict[tuple, dict] = defaultdict(lambda: {"quarters": set(), "flags": set()})
    labels = {}
    for r in rows:
        v = value(r["OBS_VALUE"])
        if v is None:
            continue
        key = (r["INDUSTRY"], ASSETS[r["ASSET"]], _fy(r["TIME_PERIOD"]))
        a = acc[key]
        col = "current" if r["PRICE_ADJUSTMENT"] == "CUR" else "cvm"
        a[col] = a.get(col, 0.0) + v
        a["quarters"].add((col, r["TIME_PERIOD"]))
        if r.get("OBS_STATUS"):
            a["flags"].add(r["OBS_STATUS"])
        labels[r["INDUSTRY"]] = r["Industry"]
    last_fy = _fy(release.get("last_quarter", "")) if release.get("last_quarter", "").endswith("Q2") else None
    out = []
    for (code, asset, fy), a in acc.items():
        full = {c: sum(1 for cc, _ in a["quarters"] if cc == c) == 4 for c in ("current", "cvm")}
        if not full["current"] or (last_fy and fy > last_fy):
            continue
        out.append(
            {
                "industry": code,
                "label": labels[code],
                "anzsic": _anzsic(code, labels[code]),
                "asset": asset,
                "fy": fy_label(fy),
                "capex_current": a.get("current"),
                "capex_cvm": a.get("cvm") if full["cvm"] else None,
                "flags": ",".join(sorted(a["flags"])) or None,
            }
        )
    fys = sorted({r["fy"] for r in out})
    return {
        "actual_fy": Table(
            description=(
                f"Actual private new capital expenditure by CAPEX industry and type of asset, FY{fys[0]} to "
                f"FY{fys[-1]}: the sum of the four quarters of the original series (5625.0, ABS Data API CAPEX). "
                "asset: total, buildings_structures or equipment_plant_machinery. anzsic: the ANZSIC 2006 division "
                f"or subdivision a CAPEX industry corresponds to (null for aggregates such as P95). flags: the "
                f"ABS's quality flags on any of the quarters ({FLAGS})."
            ),
            columns={
                "industry": "code: CAPEX industry (ABS codelist CL_CAP_ANZSIC06_NM)",
                "label": "text",
                "anzsic": "code: ANZSIC 2006 division or subdivision, TOT, or null",
                "asset": "text: type of asset",
                "fy": "financial year (YYYY-YY)",
                "capex_current": "AUD million, current prices",
                "capex_cvm": "AUD million, chain volume measures (sum of quarters)",
                "flags": "text: ABS observation status codes, comma-separated, or null",
            },
            keys=("industry", "asset", "fy"),
            rows=out,
        )
    }
