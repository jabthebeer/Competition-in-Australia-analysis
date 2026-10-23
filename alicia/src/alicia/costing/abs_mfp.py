"""ABS Estimates of Industry Multifactor Productivity (5260.0.55.002): productivity, inputs and factor shares.

From the release's main workbook (``52600550021_<year>.xlsx``, Tables 1-19), for the 16 market-sector
divisions (A-N, R, S) and the two aggregates (``MKT16``: divisions A-N, R and S; ``SEL12``: A-K and R):

- ``industry``: MFP, labour productivity, capital productivity, GVA, labour input, capital services and combined
  inputs indexes (Tables 1, 6-11), with the value-added income shares (Table 14) and gross-output cost shares
  (Table 19);
- ``market_sector``: the market-sector aggregate measures, growth accounting and income shares (Table 2);
- ``productive_capital_stock``: Table 12 summed over asset types for each division (an approximation: chain
  volume components are not strictly additive; cells the ABS does not publish are counted).

No ABS Data API dataflow exists for these estimates: XLSX only. Index reference year is read from the
tables' footnotes.
"""

from __future__ import annotations

import re

from . import abs_cube
from .base import (
    ABS_LICENCE,
    Release,
    Source,
    Table,
    abs_page,
    anzsic_codes,
    fetch_files,
    fy_end,
    fy_label,
    local_path,
    release_slug,
    remote,
    sheet_rows,
)

PAGE = "https://www.abs.gov.au/statistics/industry/industry-overview/estimates-industry-multifactor-productivity/latest-release"
SOURCE = Source(
    id="abs_mfp",
    title="Estimates of Industry Multifactor Productivity (5260.0.55.002)",
    publisher="Australian Bureau of Statistics",
    licence=ABS_LICENCE,
    url=PAGE,
)
WORKBOOK = r"/52600550021_\d{4}\.xlsx$"
YEARS = 20  # financial years kept in the industry table
QA, HOURS = "Quality adjusted hours worked basis", "Hours worked basis"
# sheet -> {section heading (or None for none): column}
INDEX_TABLES = {
    "Table 1": {QA: "mfp_qa", HOURS: "mfp_hours"},
    "Table 6": {QA: "lp_qa", HOURS: "lp_hours"},
    "Table 7": {None: "capital_productivity"},
    "Table 8": {None: "gva"},
    "Table 9": {QA: "labour_input_qa", HOURS: "labour_input_hours"},
    "Table 10": {None: "capital_services"},
    "Table 11": {QA: "combined_inputs_qa", HOURS: "combined_inputs_hours"},
}
SHARE_TABLES = {
    "Table 14": {"Labour income shares": "labour_income_share", "Capital income shares": "capital_income_share"},
    "Table 19": {
        "Labour cost shares": "labour_cost_share",
        "Capital cost shares": "capital_cost_share",
        "Intermediate inputs cost shares": "intermediate_cost_share",
    },
}
AGGREGATES = {
    "MKT16": "Market sector industries (divisions A-N, R and S)",
    "SEL12": "Selected industries (divisions A-K and R)",
}


def discover() -> Release:
    page = abs_page(PAGE)
    found = page.files(WORKBOOK)
    if len(found) != 1:
        raise ValueError(f"expected one link matching {WORKBOOK} on {PAGE}, found {len(found)}")
    return Release(
        id=release_slug(found[0]),
        date=page.released,
        files=(remote(found[0]),),
        page=PAGE,
        next_release=page.next_release,
        extra=(("reference_period", page.reference_period),),
    )


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def _name(code: str) -> str:
    return AGGREGATES.get(code) or anzsic_codes()[code]["name"]


def _section(row: abs_cube.CubeRow) -> str | None:
    return re.sub(r"\s+", " ", row.path[-1]).strip() if row.path else None


def industry_table(sheets: dict[str, list[list]]) -> tuple[Table, str]:
    values: dict[tuple[str, int], dict] = {}
    ref = None
    for sheet, sections in INDEX_TABLES.items():
        rows, notes = abs_cube.read(sheets[sheet])
        ref = ref or abs_cube.index_reference(notes)
        for r in rows:
            code = abs_cube.industry_code(r.label)
            col = sections.get(_section(r)) if None not in sections else sections[None]
            if code is None or col is None:
                raise ValueError(f"{sheet}: unexpected row {r.path} / {r.label!r}")
            for fy, v in r.values.items():
                values.setdefault((code, fy), {})[col] = v
    for sheet, sections in SHARE_TABLES.items():
        rows, _ = abs_cube.read(sheets[sheet])
        for r in rows:
            code, col = abs_cube.industry_code(r.label), sections.get(_section(r) or "")
            if code is None or col is None:
                raise ValueError(f"{sheet}: unexpected row {r.path} / {r.label!r}")
            for fy, v in r.values.items():
                values.setdefault((code, fy), {})[col] = v
    last = max(fy for (_, fy), v in values.items() if v.get("mfp_qa") is not None)
    first = last - YEARS + 1
    idx = f"index ({ref} = 100)" if ref else "index number, as published"
    cols = [c for s in INDEX_TABLES.values() for c in s.values()] + [
        c for s in SHARE_TABLES.values() for c in s.values()
    ]
    rows = [
        {"anzsic": code, "name": _name(code), "fy": fy_label(fy)} | {c: v.get(c) for c in cols}
        for (code, fy), v in values.items()
        if first <= fy <= last
    ]
    share = "proportion (0-1)"
    columns = {"anzsic": "code: ANZSIC 2006 division, MKT16 or SEL12", "name": "text", "fy": "financial year (YYYY-YY)"}
    columns |= {c: idx for s in INDEX_TABLES.values() for c in s.values()}
    columns |= {c: share for s in SHARE_TABLES.values() for c in s.values()}
    table = Table(
        description=(
            f"Productivity, inputs and factor shares by market-sector division, FY{fy_label(first)} to "
            f"FY{fy_label(last)} (5260.0.55.002 Tables 1, 6-11, 14 and 19). Value-added based indexes; '_qa' on the "
            "quality-adjusted hours basis, '_hours' on the hours-worked basis. Income shares (Table 14) are the "
            "labour and capital shares of value added used for value-added MFP; cost shares (Table 19) are shares "
            "of gross output, unsmoothed, used for gross-output MFP (may end a year earlier). null = not available."
        ),
        columns=columns,
        keys=("anzsic", "fy"),
        rows=rows,
    )
    return table, ref


# Table 2: (path tail, label) -> column; paths are matched on their last heading.
MARKET = {
    ("Labour productivity", "Hours worked basis"): ("lp_hours", "index"),
    ("Labour productivity", "Quality adjusted hours worked basis"): ("lp_qa", "index"),
    ("Productivity indexes", "Capital productivity"): ("capital_productivity", "index"),
    ("Multifactor productivity", "Hours worked basis"): ("mfp_hours", "index"),
    ("Multifactor productivity", "Quality adjusted hours worked basis"): ("mfp_qa", "index"),
    ("Output measures", "GVA market sector"): ("gva", "index"),
    ("Labour services", "Hours worked basis"): ("labour_input_hours", "index"),
    ("Labour services", "Quality adjusted hours worked basis"): ("labour_input_qa", "index"),
    ("Input measures", "Capital services"): ("capital_services", "index"),
    ("Total inputs", "Hours worked basis"): ("combined_inputs_hours", "index"),
    ("Total inputs", "Quality adjusted hours worked basis"): ("combined_inputs_qa", "index"),
    ("Capital / labour ratio", "Hours worked basis"): ("capital_labour_hours", "index"),
    ("Capital / labour ratio", "Quality adjusted hours worked basis"): ("capital_labour_qa", "index"),
    ("Growth accounting analysis - Contributions to growth", "Output growth"): ("output_growth", "growth"),
    ("Contribution to output growth - Hours worked basis", "Capital services"): ("contrib_capital_hours", "growth"),
    ("Contribution to output growth - Hours worked basis", "Hours worked"): ("contrib_hours_hours", "growth"),
    ("Contribution to output growth - Hours worked basis", "Multifactor productivity"): ("contrib_mfp_hours", "growth"),
    ("Contribution to output growth - Quality adjusted hours worked basis", "Capital services"): (
        "contrib_capital_qa",
        "growth",
    ),
    ("Contribution to output growth - Quality adjusted hours worked basis", "Hours worked"): (
        "contrib_hours_qa",
        "growth",
    ),
    ("Contribution to output growth - Quality adjusted hours worked basis", "Labour composition"): (
        "contrib_labour_composition_qa",
        "growth",
    ),
    ("Contribution to output growth - Quality adjusted hours worked basis", "Multifactor productivity"): (
        "contrib_mfp_qa",
        "growth",
    ),
    ("Two period average income shares", "Labour"): ("labour_income_share", "share"),
    ("Two period average income shares", "Capital"): ("capital_income_share", "share"),
}


def _norm_heading(h: str) -> str:
    return re.sub(r"\s+", " ", h.replace("–", "-")).strip()


def market_table(rows: list[list], ref: str | None) -> Table:
    data, _ = abs_cube.read(rows)
    out = []
    for r in data:
        tail = _norm_heading(r.path[-1]) if r.path else ""
        if tail.startswith("Percentage changes") or (
            r.path and _norm_heading(r.path[0]).startswith("Percentage changes")
        ):
            continue  # growth of the indexes: derivable from the index rows
        hit = MARKET.get((tail, _norm_heading(r.label)))
        if hit is None:
            continue
        col, kind = hit
        for fy, v in r.values.items():
            out.append({"measure": col, "kind": kind, "fy": fy_label(fy), "value": v})
    last = max(fy_end(r["fy"]) for r in out if r["value"] is not None)
    found = {r["measure"] for r in out}
    missing = sorted({c for c, _ in MARKET.values()} - found)
    if missing:
        raise ValueError(f"Table 2: measures not found: {missing}")
    unit = {
        "index": f"index ({ref} = 100)" if ref else "index",
        "growth": "per cent (natural log growth x 100)",
        "share": "proportion (0-1)",
    }
    return Table(
        description=(
            f"Market-sector (16 industries, divisions A-N, R and S) productivity measures, last {YEARS} years "
            "(5260.0.55.002 Table 2): "
            "value-added indexes ('kind' index), growth accounting contributions to output growth ('kind' growth, "
            "percentage points, natural log growth x 100) and two-period average income shares ('kind' share). "
            "Units by kind: " + "; ".join(f"{k}: {u}" for k, u in unit.items()) + "."
        ),
        columns={
            "measure": "text: measure id",
            "kind": "text: index, growth or share",
            "fy": "financial year (YYYY-YY)",
            "value": "see 'kind': index, per cent (log growth x 100) or proportion (0-1)",
        },
        keys=("measure", "fy"),
        rows=[r for r in out if r["value"] is not None and fy_end(r["fy"]) > last - YEARS],
    )


def capital_stock_table(rows: list[list]) -> Table:
    data, _ = abs_cube.read(rows)
    acc: dict[tuple[str, int], dict] = {}
    for r in data:
        if not r.path:
            continue
        head = r.path[-1]
        code = abs_cube.industry_code(head)
        sector = "unincorporated" if "unincorporated" in head.lower() else "incorporated"
        if code is None:
            raise ValueError(f"Table 12: unexpected heading {head!r}")
        fixed = not re.match(r"^(Land|Inventories)\b", r.label)
        for fy, v in r.values.items():
            a = acc.setdefault((code, fy), {"total": 0.0, "fixed": 0.0, "np": 0, "assets": set()})
            a["assets"].add((sector, r.label))
            if v is None:
                a["np"] += 1
                continue
            a["total"] += v
            if fixed:
                a["fixed"] += v
    last = max(fy for _, fy in acc)
    first = last - YEARS + 1
    out = [
        {
            "anzsic": code,
            "name": _name(code),
            "fy": fy_label(fy),
            "pks_all_assets": a["total"],
            "pks_fixed_assets": a["fixed"],
            "components": len(a["assets"]),
            "components_not_published": a["np"],
        }
        for (code, fy), a in acc.items()
        if first <= fy <= last
    ]
    return Table(
        description=(
            f"Productive capital stock by market-sector division, FY{fy_label(first)} to FY{fy_label(last)} "
            "(5260.0.55.002 Table 12, incorporated plus unincorporated), summed here over asset types: all assets "
            "(including land and inventories) and fixed assets (excluding land and inventories). The sum of chain "
            "volume components is an approximation, and components the ABS does not publish ('np') are left out "
            "of the sum: check components_not_published before using a row."
        ),
        columns={
            "anzsic": "code: ANZSIC 2006 division",
            "name": "text",
            "fy": "financial year (YYYY-YY)",
            "pks_all_assets": "AUD million, chain volume measures (sum of components)",
            "pks_fixed_assets": "AUD million, chain volume measures (sum of components)",
            "components": "count of asset x sector series summed",
            "components_not_published": "count of series not published (np) in that year",
        },
        keys=("anzsic", "fy"),
        rows=out,
    )


def build(release: Release) -> dict[str, Table]:
    path = local_path(SOURCE.id, release.files[0])
    sheets = {s: sheet_rows(path, s) for s in [*INDEX_TABLES, *SHARE_TABLES, "Table 2", "Table 12"]}
    industry, ref = industry_table(sheets)
    return {
        "industry": industry,
        "market_sector": market_table(sheets["Table 2"], ref),
        "productive_capital_stock": capital_stock_table(sheets["Table 12"]),
    }
