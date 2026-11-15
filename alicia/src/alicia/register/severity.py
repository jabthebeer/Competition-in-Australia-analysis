"""Framework version 2: severity from coded attributes, evidence steps and purpose.

Owner decisions, 14 November 2026 (DECISIONS E-161, E-184, E-185; ``docs/plan_policy_tool.md``). A rule's severity is
read from facts anyone can check in its text, not from a judgement: what kind of obligation it is, when it bites and
whom it binds. Requirements carry these facts in their own files (``kind``, ``triggers``, ``reach``). The register's
laws and policies that apply today are coded in ``regulation-register/rule-coding.json``. Fees, waiting times, renewal
periods and penalties are not yet coded (they wait on ABLIS), so they add nothing yet, and every score says so.

The 8-driver marks stay as the judgement: they say whether a rule weighs on productivity. Severity says how hard it
bites on each business it binds, and exposure (``menu/exposure.py``) how many businesses it binds.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .requirements import Requirement

# What kind of obligation it is. A rule that limits who may operate at all (a cap on numbers, an exclusive right, a
# ban, a moratorium or an ownership restriction) scores highest; then one that needs permission or sets prices.
KIND_POINTS = {
    "cap": 5,
    "licence": 4,
    "approval": 4,
    "price-control": 4,
    "registration": 2,
    "insurance": 2,
    "tax-or-levy": 2,
    "standard": 2,
    "reporting": 1,
    "notification": 1,
    "record-keeping": 1,
    "other": 1,
}
KIND_LABELS = {
    "cap": "A cap on numbers, an exclusive right, a ban or an ownership limit",
    "licence": "Hold a licence, permit or accreditation",
    "approval": "Get an approval for premises, a project or a product",
    "price-control": "A control on prices",
    "registration": "Register",
    "insurance": "Hold insurance",
    "tax-or-levy": "Pay a tax, levy or fee",
    "standard": "Meet a standard or code",
    "reporting": "Report or lodge",
    "notification": "Notify a regulator",
    "record-keeping": "Keep records",
    "other": "Other",
}
# When it bites: before trading starts scores highest; then a threshold a business crosses as it grows.
ENTRY, GROWTH = "entry", ("first-employee", "employees", "payroll", "turnover", "revenue", "assets", "quantity")
WHEN_POINTS = {"entry": 2, "growth": 1, "operating": 0}
WHEN_LABELS = {
    "entry": "Before trading starts",
    "growth": "As the business grows (first employee, or a size threshold)",
    "operating": "While operating, or when it does a particular activity",
}
# Whom it binds: every business in the industries it reaches, or only those doing some activity.
BOUND_POINTS = {"all": 1, "some": 0}
BOUND_LABELS = {"all": "Every business in the industries it reaches", "some": "Only businesses doing a named activity"}
NOT_CODED = ("fee", "waiting time", "renewal period", "penalty")
# A rule is wide when it reaches at least this share of the businesses in its jurisdiction (``menu/exposure.py``).
WIDE_SHARE = 25.0
MAX_SCORE = max(KIND_POINTS.values()) + max(WHEN_POINTS.values()) + max(BOUND_POINTS.values())
# Bands, by score. A high score is a large effect on each business bound.
HIGH, MEDIUM = 5, 3
BAND_LABELS = {"high": "High", "medium": "Medium", "low": "Low"}
NOTE = (
    "Severity is scored from attributes coded for each rule: the kind of obligation (a cap on numbers, an "
    f"exclusive right, a ban or an ownership limit scores {KIND_POINTS['cap']}; a licence, approval or price control "
    f"{KIND_POINTS['licence']}; a registration, insurance, tax or standard {KIND_POINTS['registration']}; reporting, "
    f"notification or record-keeping {KIND_POINTS['reporting']}), when it bites (before trading starts adds "
    f"{WHEN_POINTS['entry']}; at the first employee or a size threshold adds {WHEN_POINTS['growth']}) and whom it "
    f"binds (every business in its industries adds {BOUND_POINTS['all']}). The most is {MAX_SCORE}. {HIGH} or more is "
    f"high (a large effect on each business), {MEDIUM} or {MEDIUM + 1} medium, and less is low. Fees, waiting times, "
    "renewal periods and penalties are not yet coded, so they add nothing. Severity measures what a rule asks of the "
    "businesses it binds: a tax whose cost falls mostly on households, such as stamp duty, scores low even where the "
    "marks judge its cost to productivity high."
)

# The steps of evidence an item can reach, in order. Each is a fact about the item, not a judgement.
EVIDENCE_STEPS = {
    "law": "Law named: its Act or instrument, with a link to the official register",
    "quoted": "Law quoted: the obligation quoted word for word from the official text",
    "coded": "Coded: its kind, when it bites and whom it binds",
    "counted": "Counted: the businesses it reaches, from the ABS business counts",
}
QUOTED = ("register-text", "document", "corpus-copy")


def _register_dir() -> Path:
    from .catalogue import default_register_dir

    return default_register_dir()


@lru_cache(maxsize=1)
def load_coding() -> dict[str, dict]:
    """The coded attributes of register items (``regulation-register/rule-coding.json``), by item id."""
    path = _register_dir() / "rule-coding.json"
    return json.loads(path.read_text("utf-8"))["items"] if path.exists() else {}


@lru_cache(maxsize=1)
def load_purposes() -> tuple[dict[str, str], dict[str, str]]:
    """Each regime's purpose, and the purposes' labels (``regulation-register/regime-purposes.json``)."""
    path = _register_dir() / "regime-purposes.json"
    if not path.exists():
        return {}, {}
    data = json.loads(path.read_text("utf-8"))
    return data["regimes"], data["labels"]


def when(q: Requirement) -> str:
    """The earliest point at which the requirement bites: ``entry``, ``growth`` or ``operating``."""
    types = {t.type for t in q.triggers}
    if ENTRY in types:
        return "entry"
    return "growth" if types & set(GROWTH) else "operating"


def bound(q: Requirement) -> str:
    """``all`` when some part of its reach binds every business in its industries; ``some`` when every part
    carries a condition or lists activities, or when it reaches every industry but bites only on an activity (a
    notifiable foreign investment, a product recall)."""
    if not any(not (r.condition or r.activities) for r in q.reach):
        return "some"
    on_activity = bool(q.triggers) and all(t.type == "activity" for t in q.triggers)
    return "some" if on_activity and all(r.scope == "all" for r in q.reach) else "all"


def band(score: int) -> str:
    return "high" if score >= HIGH else "medium" if score >= MEDIUM else "low"


def score(kind: str, w: str, b: str, thresholds: int = 0, note: str | None = None) -> dict:
    parts = {"kind": KIND_POINTS[kind], "when": WHEN_POINTS[w], "bound": BOUND_POINTS[b]}
    s = sum(parts.values())
    return {
        "score": s,
        "max": MAX_SCORE,
        "band": band(s),
        "kind": kind,
        "when": w,
        "bound": b,
        "parts": parts,
        "thresholds": thresholds,
        "note": note,
        "notCoded": list(NOT_CODED),
    }


def severity(q: Requirement) -> dict:
    """A requirement's coded attributes and its severity score."""
    return score(q.kind, when(q), bound(q), sum(t.value is not None for t in q.triggers))


def record_severity(record_id: str) -> dict | None:
    """A register item's coded attributes and severity, if it has been coded."""
    c = load_coding().get(record_id)
    return score(c["kind"], c["when"], c["bound"], note=c.get("note")) if c else None


def check_coding(coding: dict[str, dict], record_ids: set[str]) -> list[str]:
    """Problems in ``rule-coding.json``: unknown items, kinds, timings or bindings."""
    out = []
    for rid, c in coding.items():
        where = f"rule-coding.json: {rid}"
        if rid not in record_ids:
            out.append(f"{where}: no such register item")
        if c.get("kind") not in KIND_POINTS:
            out.append(f"{where}: kind '{c.get('kind')}' is not one of {', '.join(KIND_POINTS)}")
        if c.get("when") not in WHEN_POINTS:
            out.append(f"{where}: when '{c.get('when')}' is not one of {', '.join(WHEN_POINTS)}")
        if c.get("bound") not in BOUND_POINTS:
            out.append(f"{where}: bound '{c.get('bound')}' is not one of {', '.join(BOUND_POINTS)}")
        if not c.get("note"):
            out.append(f"{where}: needs a note giving the basis")
    return out


def check_purposes(purposes: dict[str, str], labels: dict[str, str], regime_ids: set[str]) -> list[str]:
    """Problems in ``regime-purposes.json``: unknown regimes or purposes."""
    out = [f"regime-purposes.json: {r}: no such regime" for r in purposes if r not in regime_ids]
    out += [f"regime-purposes.json: {r}: purpose '{p}' has no label" for r, p in purposes.items() if p not in labels]
    return out


def evidence(*, law: bool, quoted: bool, coded: bool, counted: bool) -> list[str]:
    """The evidence steps an item reaches, in order."""
    reached = {"law": law, "quoted": quoted, "coded": coded, "counted": counted}
    return [k for k in EVIDENCE_STEPS if reached[k]]


def requirement_evidence(q: Requirement, counted: bool) -> list[str]:
    return evidence(
        law=any(x.register_url or x.register_id for x in q.laws),
        quoted=any(s.checked in QUOTED and s.quote for s in q.sources),
        coded=True,
        counted=counted,
    )
