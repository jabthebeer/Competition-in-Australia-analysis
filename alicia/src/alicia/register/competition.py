"""The Industry lens's columns: where each productivity framework mark lands among market players.

Every law on the lens (a requirement or a register item) is marked against the ALICIA productivity impact
framework (``register/framework.py``): each of eight drivers from -2 to +2, with a reason. The lens reads those
marks and places each one in a column, by the market position it acts through:

- **Entrants into the market** (``entrants``): starting up, and rivals entering from other states and countries;
- **Small and medium competitors** (``smaller``): existing firms' costs and their ability and incentive to compete,
  invest and grow (fixed costs weigh most on smaller firms);
- **Monopoly and oligopoly players** (``dominant``): the pressure on the largest players, or their shelter from it.

``DRIVER_POSITIONS`` gives each driver's usual place. An entry-exit mark of +2 or -2 (a ban, cap or exclusive right,
or its removal, in the framework's marking guide) also lands with the largest players, whom it shelters or exposes.
A mark can name its own place (``DriverMark.positions``), as the entry-exit marks about growing past a tax
threshold do. A column's cell is the sum of its marks: positive, negative, or mixed when marks of both signs meet.

Methods note: ``docs/industry_lens.md``.
"""

from __future__ import annotations

from .framework import DRIVERS, MARK_LABELS, RATING_LABELS

POSITIONS: tuple[str, ...] = ("entrants", "smaller", "dominant")
POSITION_LABELS = {
    "entrants": "Entrants into the market",
    "smaller": "Small and medium competitors",
    "dominant": "Monopoly and oligopoly players",
}
POSITION_QUESTIONS = {
    "entrants": "Does it change how easily new businesses can start up, or enter from other states and countries?",
    "smaller": "Does it change smaller businesses' costs, or their ability and incentive to compete, invest and grow?",
    "dominant": "Does it shelter the largest players from rivals, or expose them to more competition?",
}
DRIVER_POSITIONS: dict[str, tuple[str, ...]] = {
    "entry-exit": ("entrants",),
    "market-integration": ("entrants",),
    "competition": ("smaller", "dominant"),
    "burden": ("smaller",),
    "labour": ("smaller",),
    "capital": ("smaller",),
    "innovation": ("smaller",),
    "prices-taxes": ("smaller",),
}


def positions(mark) -> tuple[str, ...]:
    """The columns a framework mark lands in."""
    if mark.positions:
        return tuple(mark.positions)
    if mark.driver == "entry-exit" and abs(mark.mark) == 2:
        return ("entrants", "dominant")
    return DRIVER_POSITIONS[mark.driver]


def effects(assessment) -> dict[str, dict]:
    """The lens's cells for one assessment: for each column, its effect, strength and the marks behind it."""
    cells: dict[str, list] = {}
    for m in assessment.marks:
        for pos in positions(m):
            cells.setdefault(pos, []).append(m)
    out = {}
    for pos, marks in cells.items():
        signs = {m.mark > 0 for m in marks}
        total = sum(m.mark for m in marks)
        effect = "mixed" if len(signs) == 2 else ("positive" if total > 0 else "negative")
        out[pos] = {
            "effect": effect,
            "strength": "strong" if any(abs(m.mark) == 2 for m in marks) else "weak",
            "marks": [
                {"driver": DRIVERS[m.driver]["short"], "mark": m.mark, "label": MARK_LABELS[m.mark], "reason": m.reason}
                for m in marks
            ],
        }
    return out


def placed_marks(assessment) -> list[dict]:
    """Each mark once, with the columns it lands in: what the page adds up into its cells (as ``effects`` does)."""
    return [
        {"driver": DRIVERS[m.driver]["short"], "mark": m.mark, "reason": m.reason, "positions": list(positions(m))}
        for m in assessment.marks
    ]


def summary(assessment) -> dict:
    """The assessment as a whole, as the legislation menu shows it."""
    return {
        "total": assessment.total,
        "rating": RATING_LABELS[assessment.rating] if assessment.marks else "No material effect",
        "mixed": assessment.mixed,
        "main": DRIVERS[assessment.main_driver]["short"] if assessment.main_driver else None,
        "reach": assessment.reach,
        "confidence": assessment.confidence,
        "note": assessment.confidence_note,
        "text": assessment.summary,
        "evidence": [str(u) for u in assessment.evidence],
    }


__all__ = [
    "DRIVER_POSITIONS",
    "POSITIONS",
    "POSITION_LABELS",
    "POSITION_QUESTIONS",
    "effects",
    "placed_marks",
    "positions",
    "summary",
]
