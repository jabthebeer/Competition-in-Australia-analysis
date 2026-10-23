"""RBA Research Discussion Paper 2025-05 (Hambur and Freestone): division mark-ups and concentration.

From the paper's supplementary information zip, two input workbooks only (read from the zip; nothing in it is
extracted or run - the zip also holds model code):

- ``markups``: harmonic-mean mark-ups (De Loecker-Warzynski method, the authors' variable
  ``wding_m_DLW_tl_m_w_y``), aggregate and by ANZSIC division, 2004 to 2017 (``Inputs/markups - harmonic.xls``);
- ``concentration``: top-4, top-10 and top-20 firm shares, top 5 per cent of firms' share and the HHI, national
  and by division, 2002 to 2019 (``Inputs/Industry cocnentrations.xlsx``, file name as published): the
  weighted average across the industries in each division (``w...``), the unweighted average and the median,
  with the number of industries for each metric.

Both are BLADE-derived aggregates computed by the authors; firm-level data are not public. Years are the
authors' ``fyear``. Some divisions are not published (e.g. K, and J for concentration). Licence: CC BY 4.0
(the RBA's notice in the zip, excluding any Excluded Material).
"""

from __future__ import annotations

import io
import re
import zipfile

import pandas as pd

from .base import Release, Source, Table, fetch_files, get, links, local_path, remote

PAGE = "https://www.rba.gov.au/publications/rdp/2025/2025-05.html"
SOURCE = Source(
    id="rba_hf2025",
    title="Hambur and Freestone (2025), RBA RDP 2025-05: supplementary information (mark-ups and concentration)",
    publisher="Reserve Bank of Australia",
    licence="CC BY 4.0 (RBA notice in the supplementary zip; Excluded Material excepted)",
    url=PAGE,
)
MARKUPS = "Inputs/markups - harmonic.xls"
CONCENTRATION = "Inputs/Industry cocnentrations.xlsx"
METRICS = {"top4share": "top4", "top10share": "top10", "top20share": "top20", "top5pcshare": "top5pc", "hhi": "hhi"}


def discover() -> Release:
    supp = [u for u in links(get(PAGE).text, PAGE) if u.endswith("/supplementary-information.html")]
    if len(supp) != 1:
        raise ValueError(f"{PAGE}: no supplementary information page link")
    zips = [u for u in links(get(supp[0]).text, supp[0]) if u.endswith(".zip")]
    if len(zips) != 1:
        raise ValueError(f"{supp[0]}: expected one zip, found {len(zips)}")
    head = get_head(zips[0])
    modified = head.get("last-modified", "")
    stamp = re.sub(r"[^0-9A-Za-z]+", "-", modified).strip("-") or "unknown"
    return Release(
        id=f"RDP 2025-05 supplementary zip (Last-Modified {modified or 'not sent'})",
        date=None,
        files=(remote(zips[0], folder=stamp),),
        page=PAGE,
        extra=(("published", "August 2025"), ("supplementary_page", supp[0])),
    )


def get_head(url: str) -> dict:
    from .base import client

    resp = client().head(url)
    resp.raise_for_status()
    return {k.lower(): v for k, v in resp.headers.items()}


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def _sheet(z: zipfile.ZipFile, member: str, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(z.read(member)), sheet_name=sheet)
    return df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]


def markups(z: zipfile.ZipFile) -> Table:
    agg, div = _sheet(z, MARKUPS, "aggr"), _sheet(z, MARKUPS, "div")
    col_a = next(c for c in agg.columns if "DLW" in str(c))
    col_d = next(c for c in div.columns if "DLW" in str(c))
    rows = [
        {"division": "TOT", "fyear": int(r["fyear"]), "markup": float(r[col_a])} for _, r in agg.dropna().iterrows()
    ]
    rows += [
        {"division": str(r["division"]), "fyear": int(r["fyear"]), "markup": float(r[col_d])}
        for _, r in div.dropna(subset=["fyear", "division", col_d]).iterrows()
    ]
    return Table(
        description=(
            "Harmonic-mean firm mark-ups (price over marginal cost, De Loecker-Warzynski method) by ANZSIC division "
            "and for the aggregate (TOT), from BLADE, as used in Hambur and Freestone (2025), RBA RDP 2025-05 "
            "(supplementary 'Inputs/markups - harmonic.xls'). fyear as labelled by the authors."
        ),
        columns={"division": "code: ANZSIC 2006 division or TOT", "fyear": "year (authors' fyear)", "markup": "ratio"},
        keys=("division", "fyear"),
        rows=rows,
    )


def concentration(z: zipfile.ZipFile) -> Table:
    book = pd.ExcelFile(io.BytesIO(z.read(CONCENTRATION)))
    acc: dict[tuple[str, int], dict] = {}
    for sheet in book.sheet_names:
        m = re.fullmatch(r"(all|div|dv)_(\w+)", sheet)
        if not m or m.group(2) not in METRICS:
            continue
        metric = METRICS[m.group(2)]
        df = pd.read_excel(book, sheet_name=sheet)
        weighted = next(c for c in df.columns if str(c).startswith("w") and str(c).endswith("_go"))
        unweighted = next(c for c in df.columns if str(c).endswith("_go_industry") and not str(c).startswith("med"))
        median = next((c for c in df.columns if str(c).startswith("med_")), None)
        for _, r in df.dropna(subset=["fyear", weighted]).iterrows():
            div = "TOT" if m.group(1) == "all" else str(r["division"])
            if div == "nan":
                continue
            a = acc.setdefault((div, int(r["fyear"])), {})
            a[f"{metric}_weighted"] = float(r[weighted])
            a[f"{metric}_mean"] = float(r[unweighted])
            a[f"{metric}_median"] = float(r[median]) if median is not None and pd.notna(r[median]) else None
            a[f"{metric}_industries"] = int(r["industries"]) if pd.notna(r.get("industries")) else None
    cols = [f"{m}_{k}" for m in METRICS.values() for k in ("weighted", "mean", "median", "industries")]
    rows = [{"division": d, "fyear": y} | {c: v.get(c) for c in cols} for (d, y), v in acc.items()]
    return Table(
        description=(
            "Industry concentration from BLADE, as used in Hambur and Freestone (2025), RBA RDP 2025-05 "
            "(supplementary 'Inputs/Industry cocnentrations.xlsx'): top-4, top-10 and top-20 firm shares, the top "
            "5 per cent of firms' share and the Herfindahl index, computed within each industry and summarised for "
            "each ANZSIC division (and nationally, TOT) as the weighted average across industries (_weighted), the "
            "unweighted average (_mean) and the median (_median, null where not given); _industries: the number "
            "of industries summarised for that metric. Division HHIs are not published. fyear as labelled by the "
            "authors."
        ),
        columns={"division": "code: ANZSIC 2006 division or TOT", "fyear": "year (authors' fyear)"}
        | {
            c: "count of industries"
            if c.endswith("_industries")
            else "index (0-1)"
            if c.startswith("hhi")
            else "share (0-1)"
            for c in cols
        },
        keys=("division", "fyear"),
        rows=rows,
    )


def build(release: Release) -> dict[str, Table]:
    with zipfile.ZipFile(local_path(SOURCE.id, release.files[0])) as z:
        names = set(z.namelist())
        for member in (MARKUPS, CONCENTRATION):
            if member not in names:
                raise ValueError(f"supplementary zip has no {member!r}")
        return {"markups": markups(z), "concentration": concentration(z)}
