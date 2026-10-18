"""Case specifications for the high-evaluability batch (docs/pap_high_evaluability.md, section 3).

The case table lives in the batch's specification file, ``alicia/specs/high-evaluability-batch.json``
(forward plan Phase 4); this module turns it into the objects the analysis uses. One entry per reform.

Units are states; times are financial years (named by the year they end) for business counts and
productivity, and quarters (year * 4 + quarter - 1; written YYYY-Qn in the file) for prices. Each
cohort lists the states that adopted together, their first exposed period, the last period used
and the clean controls (states not treated at any time up to that last period).

First exposed financial year: the one containing the effective date, unless that date is the
last day of the year (30 June), in which case the next. Quarters follow the same rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from alicia.evaluate.stacked import Cohort
from alicia.runner.spec import load


def q(year: int, quarter: int) -> int:
    return year * 4 + quarter - 1


@dataclass(frozen=True)
class PriceSpec:
    codes: tuple[str, ...]  # CPI expenditure classes; the first is the main price outcome
    cohorts: tuple[Cohort, ...]
    expected: str  # "up" or "down"
    role: str  # "secondary" or "descriptive"
    exclude_subgroups: tuple[str, ...]  # related CPI subgroups left out of the placebo classes
    start: int = q(2001, 1)


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    records: tuple[str, ...]
    family: str | None
    hypothesis: str  # register direction tested: enhancing, weakening or mixed
    classes: tuple[str, ...]  # ANZSIC classes directly affected (the treated group)
    cohorts: tuple[Cohort, ...]
    division: str  # ANZSIC division for productivity and pay
    design: str
    start: int = 2008
    price: PriceSpec | None = None
    grade_cap: tuple[str, str] | None = None  # (highest grade, reason), set before unblinding
    extend_to_2019: bool = False  # robustness: add 2018-19 (only where no control is treated by then)
    notes: tuple[str, ...] = field(default_factory=tuple)


ALL_BUT = lambda *xs: tuple(s for s in ("NSW", "VIC", "QLD", "SA", "WA", "TAS", "ACT", "NT") if s not in xs)  # noqa: E731

SPEC = load("high-evaluability-batch")


def _quarter(text: str) -> int:
    """'2012-Q1' -> q(2012, 1)."""
    year, quarter = text.split("-Q")
    return q(int(year), int(quarter))


def _cohorts(rows: list[dict], period=int) -> tuple[Cohort, ...]:
    return tuple(
        Cohort(tuple(c["treated"]), period(c["first_post"]), period(c["last_post"]), tuple(c["controls"])) for c in rows
    )


def _case(d: dict) -> Case:
    p = d["price"]
    price = (
        PriceSpec(
            codes=tuple(p["codes"]),
            cohorts=_cohorts(p["cohorts"], _quarter),
            expected=p["expected"],
            role=p["role"],
            exclude_subgroups=tuple(p["exclude_subgroups"]),
            start=_quarter(p["start"]),
        )
        if p
        else None
    )
    return Case(
        id=d["id"],
        title=d["title"],
        records=tuple(d["records"]),
        family=d["family"],
        hypothesis=d["hypothesis"],
        classes=tuple(d["classes"]),
        cohorts=_cohorts(d["cohorts"]),
        division=d["division"],
        design=d["design"],
        start=d["start"],
        price=price,
        grade_cap=tuple(d["grade_cap"]) if d["grade_cap"] else None,
        extend_to_2019=d["extend_to_2019"],
        notes=tuple(d["notes"]),
    )


CASES: tuple[Case, ...] = tuple(_case(d) for d in SPEC.cases)
