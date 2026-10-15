"""The CPI's 87 expenditure classes (17th series), from the bundled ABS codelist."""

from __future__ import annotations

import json
from functools import cache
from importlib import resources


@cache
def classes() -> tuple[dict[str, str], ...]:
    raw = json.loads(resources.files("regimpact.data").joinpath("cpi17_classes.json").read_text("utf-8"))
    return tuple(raw["classes"])


def matched_classes(text: str | None) -> list[str]:
    """Official class names that appear in free text such as a record's ``price_series``."""
    if not text:
        return []
    low = text.lower()
    return [c["name"] for c in classes() if c["name"].lower() in low]
