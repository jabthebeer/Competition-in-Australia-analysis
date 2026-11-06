"""How each law affects competition, by market position: the coding behind the Industry lens.

Three positions, one question each:

- **Entrants into the market** (``entrants``): does it make starting up in the market easier or harder?
- **Small and medium competitors** (``smaller``): does it change existing smaller businesses' ability or incentive to
  compete and grow, or customers' ability to switch to them?
- **Monopoly and oligopoly players** (``dominant``): does it constrain or shelter the market power of the largest
  players (prices, market shares, exclusive rights)?

An effect is ``positive`` (more competition), ``negative`` (less), ``mixed`` or ``unclear``. It describes the
effect on competition only, not whether the law is worth having: a licence can protect consumers and still be a
barrier to entry.

Three sources of coding, in order of precedence:

1. **Assessed on the requirement**: a ``competition`` block written by hand on a requirement, with its reasons.
2. **Assessed in the register**: a register record's direction (enhancing, weakening, mixed, unclear) and its
   competition channels (the OIA checklist's five categories), mapped to positions by ``CHANNEL_POSITIONS``. A
   requirement that names a *setting* record (the same law in force, e.g. payroll tax) takes that record's coding.
3. **Coded by rule**: a requirement without either is coded from its kind and triggers (``rule_effects``): a licence,
   approval, registration, notification or insurance needed before trading is a cost of entry; a size threshold
   exempts businesses below it and adds a step in cost when a business grows past it. Everything else (duties every
   business or employer meets alike) is left uncoded.

Methods note: ``docs/industry_lens.md``.
"""

from __future__ import annotations

from typing import Literal

Position = Literal["entrants", "smaller", "dominant"]
Effect = Literal["positive", "negative", "mixed", "unclear"]
POSITIONS: tuple[str, ...] = ("entrants", "smaller", "dominant")
POSITION_LABELS = {
    "entrants": "Entrants into the market",
    "smaller": "Small and medium competitors",
    "dominant": "Monopoly and oligopoly players",
}
POSITION_QUESTIONS = {
    "entrants": "Does it make starting up in this market easier or harder?",
    "smaller": "Does it change smaller businesses' ability or incentive to compete and grow, or customers' ability to "
    "switch to them?",
    "dominant": "Does it constrain or shelter the market power of the largest players?",
}
# The register's channels (OIA competition checklist) and the positions they act through.
CHANNEL_POSITIONS: dict[str, tuple[str, ...]] = {
    "barriers": ("entrants",),
    "number-or-type": ("entrants", "dominant"),  # limits on who may operate shelter those already in
    "ability-incentive": ("smaller",),
    "consumer-choice": ("smaller",),
    "prices-market-share": ("dominant",),
}
DIRECTION_EFFECT = {"enhancing": "positive", "weakening": "negative", "mixed": "mixed", "unclear": "unclear"}

# Rules for requirements.
GATE_KINDS = {
    "licence": "strong",
    "approval": "strong",
    "registration": "weak",
    "notification": "weak",
    "insurance": "weak",
}
GATE_TRIGGERS = {"entry", "activity", "quantity"}
SIZE_TRIGGERS = {"turnover", "payroll", "revenue", "employees", "assets"}
# A money threshold below this applies to practically every business that trades or employs; at or above LARGE (or
# LARGE_STAFF employees) it reaches only the largest businesses, so it is no step for small and medium ones.
TINY, LARGE, LARGE_STAFF = 50_000, 50_000_000, 200
GATE_WORDS = {
    "licence": "hold a licence, permit or accreditation",
    "approval": "get an approval",
    "registration": "register",
    "notification": "notify the regulator",
    "insurance": "take out insurance",
}


def money(value: float) -> str:
    if value >= 1_000_000:
        return f"${value / 1_000_000:,.2f}".rstrip("0").rstrip(".") + " million"
    return f"${value:,.0f}"


def threshold_text(trigger) -> str:
    unit = trigger.unit or ""
    if trigger.type == "employees":
        return f"{trigger.value:,.0f} employees"
    return f"{money(trigger.value)} {unit.replace('AUD', '').strip()}".strip()


def rule_effects(req) -> dict[str, dict]:
    """Effects of a requirement by position, from its kind and triggers (coding source 3)."""
    out: dict[str, dict] = {}
    types = {t.type for t in req.triggers}
    size = [t for t in req.triggers if t.type in SIZE_TRIGGERS and t.value is not None]
    # A requirement on any business that takes a particular action (every class, triggered by the activity, such as an
    # environmental approval) falls alike on firms in every market, so it doesn't mark entry into this one.
    anywhere = all(r.scope == "all" for r in req.reach) and "entry" not in types
    if req.kind in GATE_KINDS and types & GATE_TRIGGERS and not size and not anywhere:
        strength = GATE_KINDS[req.kind]
        when = "before it can trade" if "entry" in types else "before it can carry out the activity"
        out["entrants"] = {
            "effect": "negative",
            "strength": strength,
            "reason": f"A new business must {GATE_WORDS[req.kind]} {when}: "
            + (
                "a cost and a wait before entering, and a test some can't pass."
                if strength == "strong"
                else "a small cost of entry."
            ),
        }
    for t in size:
        big = t.value >= (LARGE_STAFF if t.type == "employees" else LARGE)
        tiny = t.type != "employees" and t.value < TINY
        if tiny:
            continue
        text = threshold_text(t)
        out["entrants"] = {
            "effect": "positive",
            "strength": "weak",
            "reason": f"Businesses below {text} don't have to, so it doesn't fall on most new businesses.",
        }
        if not big:
            out["smaller"] = {
                "effect": "negative",
                "strength": "weak",
                "reason": f"It starts once a business passes {text}: "
                "a step in cost that can discourage growing past it.",
            }
        break
    return out


def record_effects(record) -> dict[str, dict]:
    """Effects of a register record by position, from its direction and channels (coding source 2)."""
    effect = DIRECTION_EFFECT[record.direction]
    out: dict[str, dict] = {}
    for ch in record.channels:
        for pos in CHANNEL_POSITIONS.get(ch, ()):
            # The reason is the record's direction rationale, the same for every position it codes.
            out.setdefault(pos, {"effect": effect, "strength": "strong", "reason": None, "channels": []})
            out[pos]["channels"].append(ch)
    return out


def assessed_effects(req) -> dict[str, dict]:
    """A requirement's own hand-coded effects (coding source 1)."""
    if req.competition is None:
        return {}
    return {
        e.position: {"effect": e.effect, "strength": e.strength, "reason": e.reason} for e in req.competition.effects
    }


def requirement_effects(req, settings: dict) -> tuple[dict[str, dict], str, str | None]:
    """(effects, basis, setting id): the requirement's effects and where they come from.

    ``settings`` maps record ids to *setting* records; a requirement naming one takes its coding."""
    own = assessed_effects(req)
    if own:
        return own, "assessed", None
    linked = [settings[r] for r in req.records if r in settings]
    if linked:
        return record_effects(linked[0]), "register", linked[0].id
    return rule_effects(req), "rule", None


__all__ = [
    "CHANNEL_POSITIONS",
    "POSITIONS",
    "POSITION_LABELS",
    "POSITION_QUESTIONS",
    "record_effects",
    "requirement_effects",
    "rule_effects",
]
