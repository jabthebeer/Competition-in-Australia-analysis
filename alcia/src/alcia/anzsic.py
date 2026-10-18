"""ANZSIC 2006 (Revision 2.0) codes and titles, from the bundled ABS codelist."""

from __future__ import annotations

import json
from functools import cache
from importlib import resources

LEVELS = {1: "division", 2: "subdivision", 3: "group", 4: "class"}


@cache
def _codes() -> dict[str, dict[str, str | None]]:
    raw = json.loads(resources.files("alcia.data").joinpath("anzsic2006.json").read_text("utf-8"))
    return {c["code"]: c for c in raw["codes"]}


def name(code: str) -> str | None:
    entry = _codes().get(code)
    return entry["name"] if entry else None


def level(code: str) -> str:
    return LEVELS[len(code)]


def division(code: str) -> str | None:
    """The division letter above any code (a division returns itself)."""
    codes = _codes()
    while code in codes:
        parent = codes[code]["parent"]
        if len(code) == 1 or parent is None:
            return code
        code = parent
    return None


def check(code: str, given_name: str | None = None) -> list[str]:
    """Problems with a code (and, optionally, the title given for it)."""
    official = name(code)
    if official is None:
        return [f"{code} is not an ANZSIC 2006 code"]
    if given_name is not None and _norm(given_name) != _norm(official):
        return [f"{code} is '{official}', not '{given_name}'"]
    return []


def _norm(s: str) -> str:
    return " ".join(s.replace("&", "and").lower().split())
