"""Where each productivity framework mark lands among market players, for the Industry lens's columns and the
"Most affects" tags on Legislative levers influencing competition (one vocabulary for both pages, DECISIONS E-137).

Every law on either page (a requirement, or a register item) is marked against the ALICIA productivity impact
framework (``register/framework.py``): each of eight drivers from -2 to +2, with a reason. Each mark is placed by the
market position it acts through:

- **Entrants** (``entrants``): starting up, and rivals entering from other states and countries;
- **Existing competitors** (``smaller``): existing firms' costs and their ability and incentive to compete, invest
  and grow (fixed costs weigh most on smaller firms);
- **Monopolies and oligopolies** (``dominant``): the pressure on the largest players, or their shelter from it.

``DRIVER_POSITIONS`` gives each driver's usual place. An entry-exit mark of +2 or -2 (a ban, cap or exclusive right,
or its removal, in the framework's marking guide) also lands with monopolies and oligopolies, whom it shelters or
exposes. A mark can name its own place (``DriverMark.positions``), as the entry-exit marks about growing past a tax
threshold do. A position's cell is the sum of its marks: positive, negative, or mixed when marks of both signs meet.
The position an item **most affects** is the one whose marks weigh most (the largest sum of absolute marks); a tie
names each.

Methods note: ``docs/industry_lens.md``.
"""

from __future__ import annotations

from .framework import DRIVERS, MARK_LABELS, RATING_LABELS

POSITIONS: tuple[str, ...] = ("entrants", "smaller", "dominant")
POSITION_LABELS = {
    "entrants": "Entrants",
    "smaller": "Existing competitors",
    "dominant": "Monopolies and oligopolies",
}
POSITION_QUESTIONS = {
    "entrants": "Does it change how easily new businesses can start up, or enter from other states and countries?",
    "smaller": "Does it change existing businesses' costs, or their ability and incentive to compete, invest and grow?",
    "dominant": "Does it shelter monopolies and oligopolies from rivals, or expose them to more competition?",
}
# What a position's effect means, in plain words. The sign is the effect on productivity and competition, not on the
# firms themselves: a law that shelters monopolies and oligopolies is negative.
EFFECT_PHRASES: dict[str, dict[str, str]] = {
    "entrants": {
        "positive": "Easier to start up or enter",
        "negative": "Harder to start up or enter",
        "mixed": "Easier in some ways, harder in others",
    },
    "smaller": {
        "positive": "Lower costs or more pressure to compete",
        "negative": "Higher costs or less pressure to compete",
        "mixed": "Effects in both directions",
    },
    "dominant": {
        "positive": "Exposes monopolies and oligopolies to rivals",
        "negative": "Shelters monopolies and oligopolies from rivals",
        "mixed": "Effects in both directions",
    },
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
            "phrase": EFFECT_PHRASES[pos][effect],
            "strength": "strong" if any(abs(m.mark) == 2 for m in marks) else "weak",
            "marks": [
                {"driver": DRIVERS[m.driver]["short"], "mark": m.mark, "label": MARK_LABELS[m.mark], "reason": m.reason}
                for m in marks
            ],
        }
    return out


def most_affected(assessment) -> list[str]:
    """The positions whose marks weigh most (the largest sum of absolute marks), in ``POSITIONS`` order; a tie names
    each, and an assessment with no marks names none."""
    weight = dict.fromkeys(POSITIONS, 0)
    for m in assessment.marks:
        for pos in positions(m):
            weight[pos] += abs(m.mark)
    top = max(weight.values())
    return [p for p in POSITIONS if top and weight[p] == top]


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
    "EFFECT_PHRASES",
    "POSITIONS",
    "POSITION_LABELS",
    "POSITION_QUESTIONS",
    "effects",
    "most_affected",
    "placed_marks",
    "positions",
    "summary",
]
