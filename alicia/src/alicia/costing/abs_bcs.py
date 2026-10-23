"""ABS Characteristics of Australian Business (BCS), data cube 1: barriers and competition faced.

- ``barriers`` (Table 6): the share of businesses reporting each barrier to general business activities or
  performance, including "Government regulations and/or compliance" (``government_regulation``), for all
  businesses and by innovation status, by employment size, ANZSIC division, state and location.
- ``competition`` (Table 7): the share of businesses by the amount of competition they experienced.

Shares are per cent of in-scope businesses in each group. Cells the ABS does not publish ('np') are null; the
ABS flags some estimates (relative standard error 10-25%) by cell formatting, which is not carried here. The
survey's scope excludes some divisions (public administration and safety, education and training). The survey
is now biennial. Data: ABS, CC BY 4.0.
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
    division_by_name,
    fetch_files,
    local_path,
    release_slug,
    remote,
    sheet_rows,
    value,
)

PAGE = "https://www.abs.gov.au/statistics/industry/technology-and-innovation/characteristics-australian-business/latest-release"
SOURCE = Source(
    id="abs_bcs",
    title="Characteristics of Australian Business, data cube 1",
    publisher="Australian Bureau of Statistics",
    licence=ABS_LICENCE,
    url=PAGE,
)
CUBE = r"/BCSDC01_[^/]*\.xlsx$"
BARRIERS = {
    "Uncertainty about economic conditions": "economic_uncertainty",
    "Supply chain issues": "supply_chain",
    "Lack of access to additional funds": "lack_of_funds",
    "Cost of inputs": "cost_of_inputs",
    "Outstanding accounts receivable limiting cash flow": "accounts_receivable",
    "Internet access issues": "internet_access",
    "Lack of skilled persons: within the business": "skills_within_business",
    "Lack of skilled persons: within the labour market": "skills_labour_market",
    "Lack of skilled persons: any lack of skilled persons": "skills_any",
    "Government regulations and/or compliance": "government_regulation",
    "Lack of customer demand for goods or services": "lack_of_demand",
    "Lower profit margins to remain competitive": "lower_margins",
    "Environmental factors": "environmental",
    "Other factors": "other",
    "No hampering factors": "none",
}
COMPETITION = {
    "None/captive market/no effective competition": "no_effective_competition",
    "One or two competitors": "one_or_two",
    "Three or four competitors": "three_or_four",
    "Five or more competitors": "five_or_more",
}
POPULATIONS = {
    "All businesses": "all",
    "Innovation-active businesses": "innovation_active",
    "Non innovation-active businesses": "non_innovation_active",
}
GROUPS = {
    "Total": "total",
    "Employment size": "size",
    "Industry": "industry",
    "State/Territory": "state",
    "Location": "location",
}
SIZES = {"0-4 persons": "0-4", "5-19 persons": "5-19", "20-199 persons": "20-199", "200 or more persons": "200+"}
STATES = {
    "New South Wales": "NSW",
    "Victoria": "VIC",
    "Queensland": "QLD",
    "South Australia": "SA",
    "Western Australia": "WA",
    "Tasmania": "TAS",
    "Northern Territory": "NT",
    "Australian Capital Territory": "ACT",
}


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


def _dash(s) -> str:
    return clean_text(s).replace("–", "-")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _category(group: str, label: str) -> str:
    if group == "total":
        return "total"
    if group == "size":
        if label not in SIZES:
            raise ValueError(f"unknown employment size {label!r}")
        return SIZES[label]
    if group == "industry":
        code = division_by_name(label)
        if code is None:
            raise ValueError(f"unknown industry {label!r}")
        return code
    if group == "state":
        return STATES[label]
    return _slug(label)


def read(rows: list[list], names: dict[str, str]) -> list[dict]:
    """Rows of a BCS table: population, group, category and one column per item in ``names``."""
    hi = next(
        i for i, r in enumerate(rows) if sum(_dash(v) in names or _dash(v).startswith("Uncertainty") for v in r) >= 3
    )
    prefix, cols = "", {}
    above = rows[hi - 1] if hi > 0 else []
    for c, v in enumerate(rows[hi]):
        if c == 0:
            continue
        p = _dash(above[c]) if c < len(above) else ""
        if p:
            prefix = p
        label = _dash(v)
        full = f"{prefix} {label}" if prefix.endswith(":") and label and not label[0].isupper() else label
        if full in names:
            cols[c] = names[full]
    missing = sorted(set(names.values()) - set(cols.values()))
    if missing:
        raise ValueError(f"columns not found: {missing}")
    out, population, group = [], "all", None
    for r in rows[hi + 2 :]:
        label = _dash(r[0])
        if not label or label.startswith("©") or label == "Footnotes":
            if label == "Footnotes":
                break
            continue
        if label in POPULATIONS:
            population, group = POPULATIONS[label], None
            continue
        vals = {name: value(r[c]) if c < len(r) else None for c, name in cols.items()}
        if label in GROUPS and all(v is None for v in vals.values()) and label != "Total":
            group = GROUPS[label]
            continue
        g = "total" if label == "Total" else group
        if g is None:
            raise ValueError(f"row {label!r} outside any group")
        out.append({"population": population, "group": g, "category": _category(g, label)} | vals)
    return out


KEYS = {
    "population": "text: all, innovation_active or non_innovation_active",
    "group": "text: total, size, industry, state or location",
    "category": "code: employment size (persons), ANZSIC 2006 division, state or location",
}


def build(release: Release) -> dict[str, Table]:
    path = local_path(SOURCE.id, release.files[0])
    period = release.get("reference_period", release.id)
    labels6 = "; ".join(f"{v} = {k}" for k, v in BARRIERS.items())
    labels7 = "; ".join(f"{v} = {k}" for k, v in COMPETITION.items())
    return {
        "barriers": Table(
            description=(
                f"Barriers to general business activities or performance, {period} (BCS data cube 1, Table 6): per "
                f"cent of businesses reporting each barrier, by innovation status, employment size (persons), ANZSIC "
                f"division, state and location. Columns: {labels6}."
            ),
            columns=KEYS | {v: "per cent of businesses" for v in BARRIERS.values()},
            keys=("population", "group", "category"),
            rows=read(sheet_rows(path, "Table 6"), BARRIERS),
        ),
        "competition": Table(
            description=(
                f"Amount of competition experienced, {period} (BCS data cube 1, Table 7): per cent of businesses, "
                f"by employment size (persons), ANZSIC division, state and location. Columns: {labels7}."
            ),
            columns=KEYS | {v: "per cent of businesses" for v in COMPETITION.values()},
            keys=("population", "group", "category"),
            rows=read(sheet_rows(path, "Table 7"), COMPETITION),
        ),
    }
