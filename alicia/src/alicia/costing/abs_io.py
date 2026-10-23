"""ABS Australian National Accounts: Input-Output Tables (5209.0.55.001): primary inputs by IOIG.

- ``industries``: for each of the input-output industry groups (IOIGs), Australian production (output), total
  intermediate use, the primary inputs (compensation of employees, gross operating surplus and mixed income,
  taxes less subsidies on products, other taxes less subsidies on production, complementary and competing
  imports) and value added at basic prices (Table 5, industry by industry flow table, direct allocation of
  imports), with employment (Table 20); plus the all-industries total (``TOT``).
- ``ioig_anzsic``: the IOIG to ANZSIC 2006 class concordance as published with the release's methodology
  ("Industry and Product Concordance Tables").

These give the wage-bill and GVA weights for Layer B. The ABS has not published input-output multipliers since
1998-99; the flow matrix itself is not exported here. Data: ABS, CC BY 4.0.
"""

from __future__ import annotations

import re

from .base import (
    ABS_LICENCE,
    Release,
    Source,
    Table,
    abs_page,
    anzsic_codes,
    clean_text,
    fetch_files,
    local_path,
    release_slug,
    remote,
    sheet_names,
    sheet_rows,
    value,
)

PAGE = "https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-input-output-tables/latest-release"
SOURCE = Source(
    id="abs_io",
    title="Australian National Accounts: Input-Output Tables (5209.0.55.001)",
    publisher="Australian Bureau of Statistics",
    licence=ABS_LICENCE,
    url=PAGE,
)
TABLE5 = r"/520905500105\.xlsx$"
TABLE20 = r"/520905500120\.xlsx$"
METHODOLOGY = r"/methodologies/australian-national-accounts-input-output-tables-methodology/\d{4}-\d{2}$"
CONCORDANCE = r"/[^/]*Concordance[^/]*\.xlsx$"
PRIMARY = {
    "T1": "intermediate_use",
    "P1": "coe",
    "P2": "gos_mi",
    "P3": "taxes_on_products",
    "P4": "other_taxes_on_production",
    "P5": "complementary_imports",
    "P6": "competing_imports",
}
AUDM = "AUD million, basic prices"


def discover() -> Release:
    page = abs_page(PAGE)
    t5, t20 = page.files(TABLE5), page.files(TABLE20)
    meth = [u for u in page.links if re.search(METHODOLOGY, u)]
    if len(t5) != 1 or len(t20) != 1 or not meth:
        raise ValueError(f"{PAGE}: Table 5, Table 20 or the methodology link not found")
    mpage = abs_page(meth[0])
    conc = mpage.files(CONCORDANCE)
    if len(conc) != 1:
        raise ValueError(f"{meth[0]}: expected one concordance workbook, found {len(conc)}")
    slug = release_slug(t5[0])
    return Release(
        id=slug,
        date=page.released,
        files=(remote(t5[0]), remote(t20[0]), remote(conc[0], folder=slug)),
        page=PAGE,
        next_release=page.next_release,
        extra=(("reference_period", page.reference_period), ("methodology", meth[0])),
    )


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def _ioig(v) -> str | None:
    s = clean_text(v)
    if re.fullmatch(r"\d{3,4}(\.0)?", s):
        return s.split(".")[0].zfill(4)
    return None


def _sheet(path, prefix: str) -> list[list]:
    name = next((s for s in sheet_names(path) if s.strip().startswith(prefix)), None)
    if name is None:
        raise ValueError(f"{path.name}: no sheet named {prefix!r}")
    return sheet_rows(path, name)


def primary_inputs(rows: list[list]) -> tuple[dict[str, dict], dict[str, str]]:
    """{column code: {measure: value}} and {IOIG: name} from Table 5 (industry columns plus T4, the total)."""
    head = next(i for i, r in enumerate(rows) if sum(_ioig(v) is not None for v in r[2:]) >= 50)
    codes = {c: _ioig(v) for c, v in enumerate(rows[head]) if c >= 2 and _ioig(v)}
    names = {codes[c]: clean_text(rows[head + 1][c]) for c in codes}
    total_col = next(
        (c for c in range(len(rows[head + 2])) if clean_text(rows[head + 2][c]) == "T4"),
        None,
    )
    if total_col is None:
        raise ValueError("Table 5: no T4 (total industry uses) column")
    cols = dict(codes) | {total_col: "TOT"}
    out = {code: {} for code in cols.values()}
    for r in rows[head + 3 :]:
        key, label = clean_text(r[0]), clean_text(r[1]) if len(r) > 1 else ""
        measure = PRIMARY.get(key) or {"Australian Production": "output", "Value Added": "gva"}.get(label)
        if measure is None:
            continue
        for c, code in cols.items():
            out[code][measure] = value(r[c]) if c < len(r) else None
    missing = [m for m in [*PRIMARY.values(), "output", "gva"] if m not in out["TOT"]]
    if missing:
        raise ValueError(f"Table 5: rows not found: {missing}")
    return out, names


def employment(rows: list[list]) -> dict[str, dict]:
    head = next(i for i, r in enumerate(rows) if any(clean_text(v) == "Full-time" for v in r))
    cols = {}
    for c, v in enumerate(rows[head]):
        t = clean_text(v)
        if t == "Full-time":
            cols[c] = "employed_full_time"
        elif t == "Part-time":
            cols[c] = "employed_part_time"
        elif t.startswith("Full-time equivalent"):
            cols[c] = "employed_fte"
    out = {}
    for r in rows[head + 1 :]:
        code = _ioig(r[0])
        if code:
            out[code] = {name: value(r[c]) for c, name in cols.items()}
    if len(cols) != 3 or not out:
        raise ValueError("Table 20: employment columns or rows not found")
    return out


def concordance(rows: list[list]) -> list[dict]:
    head = next(i for i, r in enumerate(rows) if clean_text(r[0]) == "IOIG" and "ANZSIC" in clean_text(r[2]))
    out, current = [], None
    for r in rows[head + 1 :]:
        if (code := _ioig(r[0])) is not None:
            current = code
        a = clean_text(r[2]) if len(r) > 2 else ""
        if current and re.fullmatch(r"\d{3,4}(\.0)?", a):
            out.append({"ioig": current, "anzsic": a.split(".")[0].zfill(4)})
    return out


def derived_pairs(table_ioigs: set[str], pairs: list[dict]) -> list[dict]:
    """Rows for a table IOIG with no concordance entry, where the tables combine concordance IOIGs that they do
    not publish separately: the unpublished concordance IOIGs in the same ANZSIC subdivision (first two
    digits). In 2023-24, 1205 'Wine, spirits and tobacco' = concordance IOIGs 1203 and 1204."""
    in_conc = {p["ioig"] for p in pairs}
    out = []
    for code in sorted(table_ioigs - in_conc):
        parts = sorted(c for c in in_conc - table_ioigs if c[:2] == code[:2])
        note = f"derived: the tables combine concordance IOIGs {' and '.join(parts)}"
        out += [{"ioig": code, "anzsic": p["anzsic"], "basis": note} for p in pairs if p["ioig"] in parts]
    return out


def build(release: Release) -> dict[str, Table]:
    t5, t20, conc = (local_path(SOURCE.id, f) for f in release.files)
    flows, names = primary_inputs(_sheet(t5, "Table 5"))
    jobs = employment(_sheet(t20, "Table 20"))
    sheet = next(s for s in sheet_names(conc) if "ANZSIC" in s and "IOIG" in s)
    pairs = concordance(sheet_rows(conc, sheet))
    classes = {c for c in anzsic_codes() if len(c) == 4}
    bad = sorted({p["anzsic"] for p in pairs} - classes)
    if bad:
        raise ValueError(f"concordance: codes that are not ANZSIC 2006 classes: {bad[:10]}")
    pairs = [p | {"basis": "published"} for p in pairs]
    pairs += derived_pairs(set(names), pairs)
    unmapped = sorted(set(names) - {p["ioig"] for p in pairs})
    measures = ["output", "intermediate_use", *list(PRIMARY.values())[1:], "gva"]
    jcols = ["employed_full_time", "employed_part_time", "employed_fte"]
    rows = []
    for code, v in flows.items():
        e = jobs.get(code, {}) if code != "TOT" else {c: sum(j[c] or 0 for j in jobs.values()) for c in jcols}
        rows.append(
            {"ioig": code, "name": names.get(code, "Total industry uses")}
            | {m: v.get(m) for m in measures}
            | {c: e.get(c) for c in jcols}
        )
    year = release.get("reference_period", release.id)
    industries = Table(
        description=(
            f"Output and primary inputs by input-output industry group (IOIG), {year} (5209.0.55.001 Table 5, "
            "industry by industry flow table, direct allocation of competing imports; employment from Table 20). "
            "gva is value added at basic prices as published (= coe + gos_mi + other_taxes_on_production). "
            "TOT = total industry uses (employment summed over IOIGs). Weights for Layer B: wage bill coe/TOT.coe, "
            "value added gva/TOT.gva."
            + (f" IOIGs without a concordance entry: {', '.join(unmapped)}." if unmapped else "")
        ),
        columns={"ioig": "code: IOIG (4 digits) or TOT", "name": "text"}
        | {m: AUDM for m in measures}
        | {c: "thousand persons" for c in jcols[:2]}
        | {"employed_fte": "thousand full-time equivalent persons"},
        keys=("ioig",),
        rows=rows,
    )
    mapping = Table(
        description=(
            "IOIG to ANZSIC 2006 class concordance as published by the ABS with the input-output methodology "
            "('Industry and Product Concordance Tables', sheet 'IOIG(2022) to ANZSIC06'), one row per IOIG x "
            "class (basis 'published'). Where the tables publish an IOIG that the concordance splits (1205 'Wine, "
            "spirits and tobacco' in 2023-24, the concordance's 1203 and 1204), rows for it are added with a "
            "'derived' basis, so every IOIG in the tables maps to classes. Class 6711 maps to two IOIGs (imputed "
            "and actual rent) in the published concordance."
        ),
        columns={
            "ioig": "code: IOIG (4 digits)",
            "anzsic": "code: ANZSIC 2006 class",
            "basis": "text: published, or derived (with the rule)",
        },
        keys=("ioig", "anzsic"),
        rows=pairs,
    )
    return {"industries": industries, "ioig_anzsic": mapping}
