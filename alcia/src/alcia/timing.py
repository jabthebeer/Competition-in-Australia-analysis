"""Map a commencement date onto the periods outcome data use.

ABS business counts (CABEE) and most industry data are by Australian financial year
(1 July to 30 June); the CPI is quarterly (and monthly from October 2025). A change that
commences part-way through a period only partly treats it, so we report both the first
period with any exposure and the first fully exposed period.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


def financial_year(d: dt.date) -> int:
    """Financial year containing ``d``, named by the year it ends (2021-07-01 -> 2022)."""
    return d.year + 1 if d.month >= 7 else d.year


def fy_label(fy: int) -> str:
    """2022 -> '2021-22'."""
    return f"{fy - 1}-{fy % 100:02d}"


def fy_bounds(fy: int) -> tuple[dt.date, dt.date]:
    return dt.date(fy - 1, 7, 1), dt.date(fy, 6, 30)


def quarter_of(d: dt.date) -> tuple[int, int]:
    return d.year, (d.month - 1) // 3 + 1


def quarter_label(q: tuple[int, int]) -> str:
    return f"{q[0]}-Q{q[1]}"


def _next_quarter(q: tuple[int, int]) -> tuple[int, int]:
    year, n = q
    return (year + 1, 1) if n == 4 else (year, n + 1)


@dataclass(frozen=True)
class Timing:
    """Where a commencement date falls in financial years and calendar quarters."""

    effective: dt.date
    first_exposed_fy: int
    first_full_fy: int
    exposure_share_first_fy: float  # share of days in the first exposed FY on or after commencement
    first_exposed_quarter: tuple[int, int]
    first_full_quarter: tuple[int, int]

    def as_dict(self) -> dict[str, object]:
        return {
            "effective_date": self.effective.isoformat(),
            "first_exposed_fy": fy_label(self.first_exposed_fy),
            "first_full_fy": fy_label(self.first_full_fy),
            "exposure_share_first_fy": round(self.exposure_share_first_fy, 4),
            "first_exposed_quarter": quarter_label(self.first_exposed_quarter),
            "first_full_quarter": quarter_label(self.first_full_quarter),
        }


def timing(effective: dt.date) -> Timing:
    fy = financial_year(effective)
    start, end = fy_bounds(fy)
    share = ((end - effective).days + 1) / ((end - start).days + 1)
    q = quarter_of(effective)
    q_start = dt.date(q[0], 3 * (q[1] - 1) + 1, 1)
    return Timing(
        effective=effective,
        first_exposed_fy=fy,
        first_full_fy=fy if effective == start else fy + 1,
        exposure_share_first_fy=share,
        first_exposed_quarter=q,
        first_full_quarter=q if effective == q_start else _next_quarter(q),
    )
