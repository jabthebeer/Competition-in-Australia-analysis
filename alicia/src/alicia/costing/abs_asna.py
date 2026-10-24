"""ABS Australian System of National Accounts (5204.0): GVA, factor income and capital stock by industry.

Tables 5 (gross value added by industry), 46 (factor income by industry), 48 (compensation of employees by
industry) and 58 (capital stock by industry), annual, ANZSIC division level, and Table 1 (key national
aggregates: GDP per capita and gross national income), for the last ``YEARS`` financial years of the release.
Ownership of dwellings (not an ANZSIC division) is kept as code ``OWN``; the all-industries total as ``TOT``.
Chain volume series do not add across industries; use current prices for shares and sums.

Data: ABS time series workbooks, CC BY 4.0. The release, its date, the next release date and the chain volume
reference year are read from the ABS latest-release page.
"""

from __future__ import annotations

import re

import pandas as pd

from ..pipeline import abs_tsw
from .base import (
    ABS_LICENCE,
    Release,
    Source,
    Table,
    abs_page,
    division_by_name,
    fetch_files,
    fy_label,
    local_path,
    release_slug,
    remote,
)

PAGE = "https://www.abs.gov.au/statistics/economy/national-accounts/australian-system-national-accounts/latest-release"
SOURCE = Source(
    id="abs_asna",
    title="Australian System of National Accounts (5204.0)",
    publisher="Australian Bureau of Statistics",
    licence=ABS_LICENCE,
    url=PAGE,
)
TABLES = {
    "5": r"/5204005_GVA_by_Industry\.xlsx$",
    "46": r"/5204046_Factor_Income_By_Industry\.xlsx$",
    "48": r"/5204048_Comp_Employees_By_Industry\.xlsx$",
    "58": r"/5204058_Capital_Stock_By_Industry\.xlsx$",
    "1": r"/5204001_Key_National_Aggregates\.xlsx$",
}
YEARS = 15  # financial years kept, ending with the release's latest year
AUDM = "AUD million, current prices"


def discover() -> Release:
    page = abs_page(PAGE)
    files = []
    for table, pattern in TABLES.items():
        found = page.files(pattern)
        if len(found) != 1:
            raise ValueError(f"ASNA Table {table}: expected one link matching {pattern}, found {len(found)}")
        files.append(remote(found[0]))
    slugs = {release_slug(f.url) for f in files}
    if len(slugs) != 1:
        raise ValueError(f"ASNA tables come from different releases: {sorted(slugs)}")
    extra = [("reference_period", page.reference_period)]
    m = re.search(r"Reference year for chain volume measures[^.]*? is (\d{4}-\d{2})", page.text)
    if m:
        extra.append(("cvm_reference_year", m.group(1)))
    return Release(
        id=slugs.pop(),
        date=page.released,
        files=tuple(files),
        page=PAGE,
        next_release=page.next_release,
        extra=tuple(extra),
    )


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def _code(head: str) -> str | None:
    head = head.strip()
    if m := re.search(r"\(([A-S])\)$", head):
        return m.group(1)
    low = head.lower()
    if low == "ownership of dwellings":
        return "OWN"
    if low in ("all industries", "total all industries"):
        return "TOT"
    return division_by_name(head)


def _split(description: str) -> tuple[str | None, str]:
    """'Mining (B) ;  Current prices ;' -> ('B', 'Current prices'); also 'Wages and salaries ;  Mining ;'."""
    parts = [p.strip() for p in description.split(";") if p.strip()]
    if len(parts) == 1:
        return None, parts[0]
    a, b = parts[0], parts[1]
    if (code := _code(a)) is not None:
        return code, b
    if (code := _code(b)) is not None:
        return code, a
    return None, " ; ".join(parts)


def tidy(raw: pd.DataFrame) -> pd.DataFrame:
    """Long frame: code, item, fy (ending year), value, unit."""
    split = raw["description"].map(_split)
    out = raw.assign(code=[s[0] for s in split], item=[s[1] for s in split], fy=raw["date"].dt.year)
    return out[["code", "item", "fy", "value", "unit"]]


def _names() -> dict[str, str]:
    from .base import anzsic_codes

    names = {c: v["name"] for c, v in anzsic_codes().items() if len(c) == 1}
    return names | {"OWN": "Ownership of dwellings", "TOT": "All industries"}


def _window(df: pd.DataFrame) -> tuple[int, int]:
    last = int(df["fy"].max())
    return last - YEARS + 1, last


def _wide(df: pd.DataFrame, items: dict[str, str], first: int) -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    unknown = df[df["code"].isna() & df["item"].map(lambda s: any(p.strip() in items for p in s.split(" ; ")))]
    if not unknown.empty:
        raise ValueError(f"series with an unrecognised industry: {sorted(set(unknown['item']))}")
    d = df[df["code"].notna() & df["item"].isin(items) & (df["fy"] >= first)]
    for r in d.itertuples():
        out.setdefault((r.code, int(r.fy)), {})[items[r.item]] = r.value
    return out


def gva_tables(t5: pd.DataFrame, cvm_ref: str) -> dict[str, Table]:
    first, last = _window(t5)
    cvm = f"AUD million, chain volume measures (reference year {cvm_ref})"
    items = {
        "Current prices": "gva_current",
        "Chain volume measures": "gva_cvm",
        "Percentage of GVA at basic prices, current prices": "gva_share_pct",
    }
    wide = _wide(t5, items, first)
    total_cvm = t5[(t5["item"] == "Gross value added at basic prices: Chain volume measures") & (t5["fy"] >= first)]
    for r in total_cvm.itertuples():
        wide.setdefault(("TOT", int(r.fy)), {})["gva_cvm"] = r.value
    names = _names()
    rows = [
        {
            "anzsic": code,
            "name": names[code],
            "fy": fy_label(fy),
            "gva_current": v.get("gva_current"),
            "gva_cvm": v.get("gva_cvm"),
            "gva_share_pct": v.get("gva_share_pct"),
        }
        for (code, fy), v in wide.items()
    ]
    gdp = {}
    for item, col in (
        ("Gross domestic product: Current prices", "gdp_current"),
        ("Gross domestic product: Chain volume measures", "gdp_cvm"),
    ):
        for r in t5[(t5["item"] == item) & (t5["fy"] >= first)].itertuples():
            gdp.setdefault(int(r.fy), {})[col] = r.value
    return {
        "gva": Table(
            description=(
                f"Gross value added at basic prices by ANZSIC division, FY{fy_label(first)} to FY{fy_label(last)} "
                "(ASNA Table 5). OWN = ownership of dwellings; TOT = all industries (GVA at basic prices). Shares "
                "are as published (the workbook labels the unit 'proportion' but the values are per cent). "
                "Chain volume series are not additive."
            ),
            columns={
                "anzsic": "code: ANZSIC 2006 division, OWN or TOT",
                "name": "text",
                "fy": "financial year (YYYY-YY)",
                "gva_current": AUDM,
                "gva_cvm": cvm,
                "gva_share_pct": "per cent of total GVA at basic prices, current prices",
            },
            keys=("anzsic", "fy"),
            rows=rows,
        ),
        "gdp": Table(
            description=f"Gross domestic product, FY{fy_label(first)} to FY{fy_label(last)} (ASNA Table 5).",
            columns={"fy": "financial year (YYYY-YY)", "gdp_current": AUDM, "gdp_cvm": cvm},
            keys=("fy",),
            rows=[
                {"fy": fy_label(fy), "gdp_current": v.get("gdp_current"), "gdp_cvm": v.get("gdp_cvm")}
                for fy, v in gdp.items()
            ],
        ),
    }


def factor_table(t46: pd.DataFrame, t48: pd.DataFrame) -> Table:
    first, last = _window(t46)
    wide = _wide(
        t46,
        {
            "Compensation of employees": "coe",
            "Gross operating surplus and gross mixed income": "gos_gmi",
            "Gross operating surplus": "gos_gmi",  # ownership of dwellings has no mixed income
            "Total factor income": "tfi",
        },
        first,
    )
    for key, v in _wide(
        t48, {"Wages and salaries": "wages", "Employers' social contributions": "employer_contributions"}, first
    ).items():
        wide.setdefault(key, {}).update(v)
    names = _names()
    rows = []
    for (code, fy), v in wide.items():
        coe, tfi = v.get("coe"), v.get("tfi")
        rows.append(
            {
                "anzsic": code,
                "name": names[code],
                "fy": fy_label(fy),
                "coe": coe,
                "wages": v.get("wages"),
                "employer_contributions": v.get("employer_contributions"),
                "gos_gmi": v.get("gos_gmi"),
                "tfi": tfi,
                "labour_share": coe / tfi if coe is not None and tfi else None,
            }
        )
    return Table(
        description=(
            f"Factor income by ANZSIC division, FY{fy_label(first)} to FY{fy_label(last)} (ASNA Tables 46 and 48): "
            "compensation of employees (wages and salaries plus employers' social contributions), gross operating "
            "surplus and gross mixed income, total factor income. labour_share = coe / tfi (derived here; mixed "
            "income of unincorporated businesses is counted with capital). OWN = ownership of dwellings; "
            "TOT = all industries."
        ),
        columns={
            "anzsic": "code: ANZSIC 2006 division, OWN or TOT",
            "name": "text",
            "fy": "financial year (YYYY-YY)",
            "coe": AUDM,
            "wages": AUDM,
            "employer_contributions": AUDM,
            "gos_gmi": AUDM,
            "tfi": AUDM,
            "labour_share": "proportion (0-1), derived",
        },
        keys=("anzsic", "fy"),
        rows=rows,
    )


def capital_table(t58: pd.DataFrame, cvm_ref: str) -> Table:
    first, last = _window(t58)
    items = {
        "Net capital stock: Current prices": "ncs_current",
        "Net capital stock: Chain volume measures": "ncs_cvm",
        "Gross fixed capital formation: Current prices": "gfcf_current",
        "Gross fixed capital formation: Chain volume measures": "gfcf_cvm",
        "Consumption of fixed capital: Current prices": "cfc_current",
        "Consumption of fixed capital: Chain volume measures": "cfc_cvm",
        "Capital services index": "capital_services",
        "End-year average age of gross stock": "average_age",
    }
    wide = _wide(t58, items, first)
    csi = t58[t58["item"] == "Capital services index"]
    base = csi.groupby("fy")["value"].apply(lambda s: bool((s.round(1) == 100).all()))
    base_years = [int(y) for y, ok in base.items() if ok]
    csi_unit = f"index ({fy_label(base_years[0])} = 100)" if len(base_years) == 1 else "index number, as published"
    cvm = f"AUD million, chain volume measures (reference year {cvm_ref})"
    names = _names()
    rows = [
        {"anzsic": code, "name": names[code], "fy": fy_label(fy)} | {col: v.get(col) for col in items.values()}
        for (code, fy), v in wide.items()
    ]
    return Table(
        description=(
            f"Capital stock by ANZSIC division, FY{fy_label(first)} to FY{fy_label(last)} (ASNA Table 58): net "
            "capital stock (end of year), gross fixed capital formation and consumption of fixed capital, in current "
            "prices and chain volume measures; capital services index; average age of the gross stock. "
            "OWN = ownership of dwellings. Productive capital stock is not in this table (see abs_mfp)."
        ),
        columns={
            "anzsic": "code: ANZSIC 2006 division or OWN",
            "name": "text",
            "fy": "financial year (YYYY-YY)",
            "ncs_current": AUDM,
            "ncs_cvm": cvm,
            "gfcf_current": AUDM,
            "gfcf_cvm": cvm,
            "cfc_current": AUDM,
            "cfc_cvm": cvm,
            "capital_services": csi_unit,
            "average_age": "years",
        },
        keys=("anzsic", "fy"),
        rows=rows,
    )


def aggregates_table(t1: pd.DataFrame, cvm_ref: str) -> Table:
    """GDP per capita and GNI by year (Table 1). Population is GDP over GDP per capita, both current prices."""
    first, last = _window(t1)
    items = {
        "GDP per capita: Current prices": "gdp_per_capita_current",
        "GDP per capita: Chain volume measures": "gdp_per_capita_cvm",
        "Gross national income: Current prices": "gni_current",
    }
    d = t1[t1["code"].isna() & t1["item"].isin(items) & (t1["fy"] >= first)]
    wide: dict[int, dict] = {}
    for r in d.itertuples():
        wide.setdefault(int(r.fy), {})[items[r.item]] = r.value
    missing = sorted(set(items.values()) - {k for v in wide.values() for k in v})
    if missing:
        raise ValueError(f"ASNA Table 1 has no series for {missing}")
    return Table(
        description=(
            f"Key national aggregates, FY{fy_label(first)} to FY{fy_label(last)} (ASNA Table 1): GDP per capita "
            "and gross national income. GDP ÷ GDP per capita (current prices) gives the population the ABS used."
        ),
        columns={
            "fy": "financial year (YYYY-YY)",
            "gdp_per_capita_current": "AUD, current prices",
            "gdp_per_capita_cvm": f"AUD, chain volume measures (reference year {cvm_ref})",
            "gni_current": AUDM,
        },
        keys=("fy",),
        rows=[{"fy": fy_label(fy), **{c: v.get(c) for c in items.values()}} for fy, v in sorted(wide.items())],
    )


def build(release: Release) -> dict[str, Table]:
    paths = {t: local_path(SOURCE.id, f) for t, f in zip(TABLES, release.files, strict=True)}
    raw = {t: tidy(abs_tsw.read(p)) for t, p in paths.items()}
    unknown = sorted((set(raw["46"]["code"]) | set(raw["58"]["code"])) - set(_names()) - {None})
    if unknown:
        raise ValueError(f"unrecognised industries in ASNA tables: {unknown}")
    cvm_ref = release.get("cvm_reference_year") or "not stated on the release page"
    return (
        gva_tables(raw["5"], cvm_ref)
        | {"factor_income": factor_table(raw["46"], raw["48"])}
        | {"capital": capital_table(raw["58"], cvm_ref)}
        | {"key_aggregates": aggregates_table(raw["1"], cvm_ref)}
    )
