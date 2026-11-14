"""Severity from coded attributes: the first step of framework version 2.

Owner decision, 14 November 2026 (DECISIONS E-161; ``docs/plan_policy_tool.md``). A rule's severity is read from
facts anyone can check in its text, not from a judgement: what kind of obligation it is, when it bites and who it
binds. This module scores the attributes the requirements already record. Fees, waiting times, renewal periods and
penalties are not yet coded (they wait on ABLIS), so they add nothing yet, and every score says so.

The weights are a draft for the owner to settle. Until then the score is shown beside the framework marks, on
Register data, and the impact classes still come from the marks.

Only requirements are scored. A register item (a reform, an existing setting or a non-legislative barrier) has no
coded attributes yet.
"""

from __future__ import annotations

from .requirements import Requirement

# What kind of obligation it is: a rule that limits who may operate at all scores highest.
KIND_POINTS = {
    "licence": 4,
    "approval": 4,
    "registration": 2,
    "insurance": 2,
    "tax-or-levy": 2,
    "standard": 2,
    "reporting": 1,
    "notification": 1,
    "record-keeping": 1,
    "other": 1,
}
# When it bites: before trading starts scores highest; then a threshold a business crosses as it grows.
ENTRY, GROWTH = "entry", ("first-employee", "employees", "payroll", "turnover", "revenue", "assets", "quantity")
WHEN_POINTS = {"entry": 2, "growth": 1, "operating": 0}
WHEN_LABELS = {
    "entry": "Before trading starts",
    "growth": "As the business grows (first employee, or a size threshold)",
    "operating": "While operating, or when it does a particular activity",
}
# Who it binds: every business in the industries it reaches, or only those doing some activity.
BOUND_POINTS = {"all": 1, "some": 0}
BOUND_LABELS = {"all": "Every business in the industries it reaches", "some": "Only businesses doing a named activity"}
NOT_CODED = ("fee", "waiting time", "renewal period", "penalty")
MAX_SCORE = max(KIND_POINTS.values()) + max(WHEN_POINTS.values()) + max(BOUND_POINTS.values())
# Bands, by score.
HIGH, MEDIUM = 5, 3
BAND_LABELS = {"high": "High", "medium": "Medium", "low": "Low"}
NOTE = (
    "Severity is a draft score from attributes coded on each requirement: the kind of obligation (a licence or "
    f"approval scores {KIND_POINTS['licence']}; a registration, insurance, tax or standard "
    f"{KIND_POINTS['registration']}; reporting, notification or record-keeping {KIND_POINTS['reporting']}), when it "
    f"bites (before trading starts adds {WHEN_POINTS['entry']}; at the first employee or a size threshold adds "
    f"{WHEN_POINTS['growth']}) and who it binds (every business in its industries adds {BOUND_POINTS['all']}). The "
    f"most is {MAX_SCORE}. {HIGH} or more is high, {MEDIUM} or {MEDIUM + 1} medium, and less is low. Fees, waiting "
    "times, renewal periods and penalties are not yet coded, so they add nothing. Register items are not scored. "
    "The weights are a draft and have not been settled."
)


def when(q: Requirement) -> str:
    """The earliest point at which the requirement bites: ``entry``, ``growth`` or ``operating``."""
    types = {t.type for t in q.triggers}
    if ENTRY in types:
        return "entry"
    return "growth" if types & set(GROWTH) else "operating"


def bound(q: Requirement) -> str:
    """``all`` when some part of its reach binds every business in its industries; ``some`` when every part
    carries a condition or lists activities."""
    return "all" if any(not (r.condition or r.activities) for r in q.reach) else "some"


def band(score: int) -> str:
    return "high" if score >= HIGH else "medium" if score >= MEDIUM else "low"


def severity(q: Requirement) -> dict:
    """The requirement's coded attributes and its draft severity score."""
    w, b = when(q), bound(q)
    parts = {"kind": KIND_POINTS[q.kind], "when": WHEN_POINTS[w], "bound": BOUND_POINTS[b]}
    score = sum(parts.values())
    return {
        "score": score,
        "max": MAX_SCORE,
        "band": band(score),
        "when": w,
        "bound": b,
        "parts": parts,
        "thresholds": sum(t.value is not None for t in q.triggers),
        "notCoded": list(NOT_CODED),
    }
