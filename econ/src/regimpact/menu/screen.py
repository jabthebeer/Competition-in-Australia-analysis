"""A transparent screen of how evaluable each change is with public data.

This is a triage aid for choosing what to study, not a quality score for the reform or a
substitute for the robustness review. Every rating comes with the reasons behind it.

Rules (applied to the record's effective commencement):
- not commenced -> "not-yet";
- weaknesses counted: no geographic comparison group (national change); too few years of
  outcome data before (< 3 financial years) or after (< 2); affected industries only at
  division or subdivision level; event window overlaps the COVID period (2019-20 to
  2021-22); another register change hits the same jurisdiction and industry within two
  years; dates not fully verified;
- 0 weaknesses -> "high", 1 -> "medium", 2 or more -> "low".
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from ..register.catalogue import families
from ..register.schema import STATES, ChangeRecord
from ..timing import financial_year, fy_label, timing

Rating = Literal["high", "medium", "low", "not-yet"]
Comparison = Literal["staggered", "other-states", "industry-only"]

COVID_FYS = range(2020, 2023)  # 2019-20, 2020-21, 2021-22
WINDOW = 2  # financial years either side of the first fully exposed year
MIN_PRE, MIN_POST = 3, 2


@dataclass(frozen=True)
class Coverage:
    """The financial years a primary outcome series covers (named by the year they end)."""

    outcome: str
    first_fy: int
    last_fy: int
    note: str


# Primary outcome: entries and exits by state x ANZSIC class (ABS CABEE). See
# docs/impact_evaluation_design.md for how the series is assembled and its breaks.
DEFAULT_COVERAGE = Coverage(
    outcome="business entries and exits by state and ANZSIC class (ABS CABEE)",
    first_fy=2008,  # 2007-08: first entries/exits on ANZSIC 2006 (Jun 2007 - Jun 2009 release)
    last_fy=2025,  # 2024-25: class-level cubes for 2025-26 are due 18 Dec 2026
    note="assembled from successive CABEE releases; series breaks documented by the ABS",
)


@dataclass(frozen=True)
class Screen:
    rating: Rating
    comparison: Comparison | None
    pre_years: int | None
    post_years: int | None
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    overlapping: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "rating": self.rating,
            "comparison": self.comparison,
            "pre_years": self.pre_years,
            "post_years": self.post_years,
            "strengths": list(self.strengths),
            "weaknesses": list(self.weaknesses),
            "overlapping": list(self.overlapping),
        }


def _comparison(rec: ChangeRecord, fam: list[ChangeRecord] | None) -> Comparison:
    if rec.jurisdiction == "CTH":
        return "industry-only"
    if fam:
        dated = {r.effective_commencement.date for r in fam if r.effective_commencement}
        states_covered = {r.jurisdiction for r in fam if r.effective_commencement}
        if len(dated) > 1 or set(STATES) - states_covered:
            return "staggered"
    return "other-states"


def _shares_industry(a: ChangeRecord, b: ChangeRecord) -> bool:
    return any(x.anzsic.startswith(y.anzsic) or y.anzsic.startswith(x.anzsic)
               for x in a.industries for y in b.industries)


def screen_record(rec: ChangeRecord, all_records: list[ChangeRecord], coverage: Coverage = DEFAULT_COVERAGE,
                  fam: list[ChangeRecord] | None = None) -> Screen:
    eff = rec.effective_commencement
    if eff is None:
        return Screen("not-yet", None, None, None, (), ("not yet commenced: ex ante analysis only",), ())

    t = timing(eff.date)
    first_full = t.first_full_fy
    pre = first_full - coverage.first_fy
    post = coverage.last_fy - first_full + 1
    strengths: list[str] = []
    weaknesses: list[str] = []

    comparison = _comparison(rec, fam)
    if comparison == "staggered":
        strengths.append("staggered adoption across jurisdictions gives comparison groups")
    elif comparison == "other-states":
        strengths.append("single-jurisdiction change: other states and territories can serve as comparisons")
    else:
        weaknesses.append("national change: only unaffected industries can serve as comparisons")

    if pre < MIN_PRE:
        weaknesses.append(f"only {max(pre, 0)} financial year(s) of outcome data before {fy_label(first_full)}")
    if post < MIN_POST:
        weaknesses.append(f"only {max(post, 0)} financial year(s) of outcome data from {fy_label(first_full)}")
    if pre >= MIN_PRE and post >= MIN_POST:
        strengths.append(f"{pre} years before and {post} from the first full year ({fy_label(first_full)})")

    direct = [i for i in rec.industries if i.exposure == "direct"]
    if any(len(i.anzsic) >= 3 for i in direct):
        strengths.append("directly affected industries identified at ANZSIC group or class level")
    else:
        weaknesses.append("directly affected industries identified only at division or subdivision level")

    window = range(first_full - WINDOW, first_full + WINDOW + 1)
    if set(window) & set(COVID_FYS):
        weaknesses.append("event window overlaps the COVID period (2019-20 to 2021-22)")

    overlapping = []
    for other in all_records:
        oeff = other.effective_commencement
        if other.id == rec.id or oeff is None or (other.family and other.family == rec.family):
            continue
        same_place = other.jurisdiction in (rec.jurisdiction, "CTH") or rec.jurisdiction == "CTH"
        if same_place and _shares_industry(rec, other) and abs(financial_year(oeff.date) - t.first_exposed_fy) <= 2:
            overlapping.append(other.id)
    if overlapping:
        weaknesses.append("other recorded changes hit the same industry and place within two years: "
                          + ", ".join(sorted(overlapping)))

    if not rec.verified.dates:
        weaknesses.append("dates not fully verified")

    n = len(weaknesses)
    rating: Rating = "high" if n == 0 else "medium" if n == 1 else "low"
    return Screen(rating, comparison, pre, post, tuple(strengths), tuple(weaknesses), tuple(sorted(overlapping)))


def screen_all(records: Iterable[ChangeRecord], coverage: Coverage = DEFAULT_COVERAGE) -> dict[str, Screen]:
    records = list(records)
    fams = families(records)
    return {r.id: screen_record(r, records, coverage, fams.get(r.family) if r.family else None) for r in records}
