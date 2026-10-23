"""ABS OSCA - Occupation Standard Classification for Australia: occupations and their licensing flag.

From the classification's "OSCA Category Descriptions" workbook (data downloads of the latest version):

- ``occupations`` (Table 1): each six-digit occupation's identifier, principal title, skill level and the
  "Registration or Licensing" statement as a flag (``required``, ``may be required`` or null), with the
  statement's text where it says more than the flag;
- ``groups`` (Table 2): major, sub-major, minor and unit group identifiers and titles.

Employment by occupation is not included. The Labour Force Survey's occupation tables (EQ08: unit group ×
state; EQ09: division × major group) are coded to ANZSCO, not OSCA, and the LFS Detailed release ceased after
March 2026; mapping them to OSCA through the ABS correspondence is left as a limitation. Data: ABS, CC BY 4.0.

Refresh detects a new OSCA version (a new version folder on the ABS site); an in-place revision of the same
workbook within a version is not detected.
"""

from __future__ import annotations

import re

from .base import (
    ABS_LICENCE,
    Release,
    Source,
    Table,
    abs_page,
    clean_text,
    fetch_files,
    local_path,
    remote,
    sheet_names,
    sheet_rows,
)

BASE = "https://www.abs.gov.au/statistics/classifications/osca-occupation-standard-classification-australia"
PAGE = f"{BASE}/latest-release"
SOURCE = Source(
    id="abs_osca",
    title="OSCA - Occupation Standard Classification for Australia: category descriptions",
    publisher="Australian Bureau of Statistics",
    licence=ABS_LICENCE,
    url=PAGE,
)
VERSION = re.compile(r"/osca-occupation-standard-classification-australia/(\d{4}-version-\d+-\d+)(?:/|$)")
WORKBOOK = r"/OSCA(%20| )Category(%20| )Descriptions\.xlsx$"
LEVELS = {1: "major group", 2: "sub-major group", 3: "minor group", 4: "unit group", 6: "occupation"}


def discover() -> Release:
    page = abs_page(PAGE)
    versions = sorted({m.group(1) for u in page.links if (m := VERSION.search(u))})
    if not versions:
        raise ValueError(f"{PAGE}: no OSCA version link found")
    version = versions[-1]
    downloads = abs_page(f"{BASE}/{version}/data-downloads")
    found = downloads.files(WORKBOOK)
    if len(found) != 1:
        raise ValueError(f"{downloads.url}: expected one category descriptions workbook, found {len(found)}")
    return Release(
        id=version,
        date=page.released,
        files=(remote(found[0], folder=version),),
        page=PAGE,
        next_release=page.next_release,
        extra=(("reference_period", page.reference_period), ("data_downloads", downloads.url)),
    )


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def _table(rows: list[list]) -> tuple[dict[str, int], list[list]]:
    hi = next(i for i, r in enumerate(rows) if clean_text(r[0]) == "Identifier")
    cols = {clean_text(v): c for c, v in enumerate(rows[hi]) if clean_text(v)}
    return cols, rows[hi + 1 :]


def licensing(text: str) -> tuple[str | None, str | None]:
    """('required' | 'may be required' | None, the statement when it says more than the flag)."""
    t = clean_text(text)
    if not t:
        return None, None
    if t.lower().startswith("registration or licensing is required"):
        flag = "required"
    elif t.lower().startswith("registration or licensing may be required"):
        flag = "may be required"
    else:
        raise ValueError(f"unrecognised licensing statement {t!r}")
    standard = {"Registration or licensing is required.", "Registration or licensing may be required."}
    return flag, None if t in standard else t


def _released(rows: list[list]) -> str | None:
    for r in rows[:8]:
        for v in r:
            if m := re.search(r"Released at [^)]*\) (\d{1,2} \w+ \d{4})", clean_text(v)):
                return m.group(1)
    return None


def build(release: Release) -> dict[str, Table]:
    path = local_path(SOURCE.id, release.files[0])
    t1 = sheet_rows(path, "Table 1")
    contents = sheet_rows(path, next(s for s in sheet_names(path) if s.strip() == "Contents"))
    released = _released(contents) or "date not stated"
    cols, body = _table(t1)
    for need in ("Identifier", "Principal Title", "Skill Level", "Registration or Licensing"):
        if need not in cols:
            raise ValueError(f"Table 1: no '{need}' column")
    occ = []
    for r in body:
        ident = clean_text(r[cols["Identifier"]])
        if not re.fullmatch(r"\d{6}", ident):
            continue
        flag, note = licensing(r[cols["Registration or Licensing"]])
        skill = clean_text(r[cols["Skill Level"]])
        occ.append(
            {
                "osca": ident,
                "title": clean_text(r[cols["Principal Title"]]),
                "skill_level": int(skill) if skill.isdigit() else (skill or None),
                "licensing": flag,
                "licensing_note": note,
                "unit_group": ident[:4],
                "major_group": ident[:1],
            }
        )
    cols2, body2 = _table(sheet_rows(path, "Table 2"))
    title = next(k for k in cols2 if "Title" in k)
    groups = []
    for r in body2:
        ident = clean_text(r[cols2["Identifier"]])
        if re.fullmatch(r"\d{1,4}", ident):
            groups.append({"code": ident, "level": LEVELS[len(ident)], "title": clean_text(r[cols2[title]])})
    n_req = sum(o["licensing"] == "required" for o in occ)
    n_may = sum(o["licensing"] == "may be required" for o in occ)
    version = release.get("reference_period", release.id)
    return {
        "occupations": Table(
            description=(
                f"OSCA {version} occupations (six-digit identifiers) with their skill level and the 'Registration or "
                f"Licensing' statement of the category descriptions (released {released}): {n_req} occupations "
                f"where registration or licensing is required, {n_may} where it may be required, of {len(occ)}. "
                "No employment counts: the LFS codes occupation to ANZSCO, not OSCA."
            ),
            columns={
                "osca": "code: OSCA occupation (6 digits)",
                "title": "text: principal title",
                "skill_level": "OSCA skill level (1 highest to 5)",
                "licensing": "text: required, may be required, or null (no statement)",
                "licensing_note": "text: the statement where it adds to the flag, else null",
                "unit_group": "code: OSCA unit group (4 digits)",
                "major_group": "code: OSCA major group (1 digit)",
            },
            keys=("osca",),
            rows=occ,
        ),
        "groups": Table(
            description=f"OSCA {version} major, sub-major, minor and unit groups (category descriptions, Table 2).",
            columns={"code": "code: OSCA group (1 to 4 digits)", "level": "text", "title": "text"},
            keys=("code",),
            rows=groups,
        ),
    }
