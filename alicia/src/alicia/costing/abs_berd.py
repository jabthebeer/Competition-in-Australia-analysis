"""ABS Research and Experimental Development, Businesses, Australia (8104.0): BERD by subdivision × size.

From data cube 2 (``81040DO002_<yyyymm>.xlsx``, Table 1): business expenditure on R&D by ANZSIC subdivision
(with division totals and the all-industries total) and employment size (0-4, 5-19, 20-199, 200 or more
persons). Blank cells are not published by the ABS (confidentiality) and are null here, so size columns do not
always add to the total. Data: ABS, CC BY 4.0.
"""

from __future__ import annotations

from .base import (
    ABS_LICENCE,
    Release,
    Source,
    Table,
    abs_page,
    anzsic_codes,
    child_by_name,
    clean_text,
    division_by_name,
    fetch_files,
    local_path,
    release_slug,
    remote,
    sheet_rows,
    value,
)

PAGE = "https://www.abs.gov.au/statistics/industry/technology-and-innovation/research-and-experimental-development-businesses-australia/latest-release"
SOURCE = Source(
    id="abs_berd",
    title="Research and Experimental Development, Businesses, Australia (8104.0)",
    publisher="Australian Bureau of Statistics",
    licence=ABS_LICENCE,
    url=PAGE,
)
CUBE = r"/81040DO002_\d{6}\.xlsx$"
SIZES = {
    "0-4 persons": "rd_0_4",
    "5-19 persons": "rd_5_19",
    "20-199 persons": "rd_20_199",
    "200 or more persons": "rd_200_plus",
    "Total expenditure on R&D": "rd_total",
}
UNITS = {"$'000": "AUD thousand, current prices"}


def discover() -> Release:
    page = abs_page(PAGE)
    found = page.files(CUBE)
    if len(found) != 1:
        raise ValueError(f"expected one link matching {CUBE} on {PAGE}, found {len(found)}")
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


def table(rows: list[list], period: str) -> Table:
    hi = next(i for i, r in enumerate(rows) if sum(clean_text(v) in SIZES for v in r) >= 4)
    cols = {c: SIZES[clean_text(v)] for c, v in enumerate(rows[hi]) if clean_text(v) in SIZES}
    units = {clean_text(rows[hi + 1][c]) for c in cols}
    if units - set(UNITS):
        raise ValueError(f"unexpected units {units}")
    out, division = [], None
    for r in rows[hi + 2 :]:
        label = clean_text(r[0])
        if not label or label.startswith("©") or label[:4].isdigit():
            continue
        vals = {name: value(r[c]) if c < len(r) else None for c, name in cols.items()}
        published = any(clean_text(r[c]) for c in cols if c < len(r))
        if not published and (heading := division_by_name(label)) is not None:  # a division heading
            division = heading
            continue
        if label == "Total":
            code, level = "TOT", "total"
        elif label.lower().startswith("total "):
            code, level = division_by_name(label[6:]), "division"
        else:
            code, level = child_by_name(division, label) if division else None, "subdivision"
        if code is None:
            raise ValueError(f"unknown industry {label!r} (division {division})")
        out.append({"anzsic": code, "level": level} | vals)
    return Table(
        description=(
            f"Business expenditure on R&D by ANZSIC subdivision and employment size, {period} (8104.0 data cube 2, "
            "Table 1). level: subdivision, division (ABS total) or total. Size columns are persons employed; null "
            "= not published, so sizes need not add to rd_total."
        ),
        columns={"anzsic": "code: ANZSIC 2006 subdivision, division or TOT", "level": "text"}
        | {name: UNITS["$'000"] for name in SIZES.values()},
        keys=("anzsic",),
        rows=out,
    )


def build(release: Release) -> dict[str, Table]:
    path = local_path(SOURCE.id, release.files[0])
    t = table(sheet_rows(path, "Table_1"), release.get("reference_period", release.id))
    known = set(anzsic_codes()) | {"TOT"}
    if any(r["anzsic"] not in known for r in t.rows):
        raise ValueError("BERD: codes outside ANZSIC 2006")
    return {"subdivision_size": t}
