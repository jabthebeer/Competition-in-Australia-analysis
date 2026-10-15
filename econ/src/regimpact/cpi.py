"""The CPI's 87 expenditure classes (17th series), from the bundled ABS codelist."""

from __future__ import annotations

import json
from functools import cache
from importlib import resources


@cache
def classes() -> tuple[dict[str, str], ...]:
    raw = json.loads(resources.files("regimpact.data").joinpath("cpi17_classes.json").read_text("utf-8"))
    return tuple(raw["classes"])


@cache
def _aggregates() -> tuple[str, ...]:
    """Group and subgroup names (a subgroup can share its class's name, e.g. 'Rents')."""
    return tuple(sorted({c["group"] for c in classes()} | {c["subgroup"] for c in classes()}))


def matched_classes(text: str | None) -> list[str]:
    """Official class names that appear in free text such as a record's ``price_series``."""
    if not text:
        return []
    low = text.lower()
    return [c["name"] for c in classes() if c["name"].lower() in low]


def matched_aggregates(text: str | None) -> list[str]:
    """CPI group or subgroup names that appear in free text."""
    if not text:
        return []
    low = text.lower()
    return [n for n in _aggregates() if n.lower() in low]
