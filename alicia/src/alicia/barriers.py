"""Barriers to entry by ANZSIC class, after Grattan Institute (2017): the bundled classification.

Six groups: natural monopolies, scale economies and heavy regulation (the sectors with barriers to entry),
low barriers, tradeable, and mostly public. The assignments and the reason for each are in
``data/barriers.json``; the method is in docs/methods_competition_charts.md.
"""

from __future__ import annotations

import json
from functools import cache
from importlib import resources

from . import anzsic

GROUPS = ("natural_monopoly", "scale_economies", "heavy_regulation", "low_barriers", "tradeable", "public")
BARRIER_GROUPS = GROUPS[:3]


@cache
def _data() -> dict:
    return json.loads(resources.files("alicia.data").joinpath("barriers.json").read_text("utf-8"))


@cache
def _listed() -> dict[str, dict]:
    return {e["code"]: e for e in _data()["codes"]}


def groups() -> dict[str, dict]:
    """Group id -> label, short label, whether it is a barrier group, and a description."""
    return _data()["groups"]


def _ancestors(code: str) -> list[str]:
    """A code and the codes above it, finest first: '4610' -> ['4610', '461', '46']."""
    return [code[:n] for n in (4, 3, 2) if n <= len(code)]


def entry(code: str) -> dict:
    """The classification of an ANZSIC code: group, sector label, Grattan's label and note where listed, and
    ``basis``: the listed code it comes from, or 'division' for the division default."""
    for c in _ancestors(code):
        if c in _listed():
            e = _listed()[c]
            return {
                "group": e["group"],
                "sector": e.get("sector") or anzsic.name(code) or code,
                "grattan": e.get("grattan"),
                "note": e.get("note"),
                "basis": c,
            }
    div = anzsic.division(code)
    if div is None:
        raise KeyError(f"{code} is not an ANZSIC 2006 code")
    return {
        "group": _data()["divisions"][div],
        "sector": anzsic.name(code) or code,
        "grattan": None,
        "note": None,
        "basis": "division",
    }


def group(code: str) -> str:
    return entry(code)["group"]


def sector(code: str) -> tuple[str, str]:
    """The sector an ANZSIC class is reported in on the website, as (key, label). Classes listed with the same
    sector label form one sector (keyed by the first such code); other classes are grouped by ANZSIC group,
    labelled ', other' where some of the group's classes are listed as sectors of their own."""
    e = entry(code)
    listed = _listed().get(e["basis"])
    if listed and listed.get("sector"):
        return _sector_keys()[listed["sector"]], listed["sector"]
    grp = code[:3]
    split = any(c.startswith(grp) and _listed()[c].get("sector") for c in _listed() if len(c) == 4)
    return grp, f"{sentence_case(anzsic.name(grp))}{', other' if split else ''}"


def sentence_case(title: str) -> str:
    """ABS titles are in title case ('Pubs, Taverns and Bars'); the website's sector labels are in sentence case."""
    words = title.split(" ")
    return " ".join([words[0], *(w if len(w) > 1 and w.isupper() else w.lower() for w in words[1:])])


@cache
def _sector_keys() -> dict[str, str]:
    keys: dict[str, str] = {}
    for e in _data()["codes"]:
        if e.get("sector"):
            keys.setdefault(e["sector"], e["code"])
    return keys


def aggregate_group(code: str, weights: dict[str, float]) -> str:
    """The group of a code that spans several classes (an ANZSIC group or subdivision), for data published
    only at that level. A code listed itself keeps its listing; otherwise it takes the group holding the
    largest share of ``weights`` (class code -> weight, e.g. company income) among its classes, and the
    group of most of its classes when no weights are given."""
    if code in _listed():
        return _listed()[code]["group"]
    totals: dict[str, float] = {}
    for c, w in weights.items():
        if c.startswith(code) and w and w > 0:
            totals[group(c)] = totals.get(group(c), 0.0) + w
    if totals:
        return max(totals, key=totals.get)
    classes = [c for c in anzsic._codes() if len(c) == 4 and c.startswith(code)]
    counts: dict[str, int] = {}
    for c in classes:
        counts[group(c)] = counts.get(group(c), 0) + 1
    return max(counts, key=counts.get) if counts else group(code)


def check() -> list[str]:
    """Problems with the bundled classification: unknown codes or groups, missing division defaults."""
    data = _data()
    problems = [f"{g}: no group metadata" for g in GROUPS if g not in data["groups"]]
    problems += [f"division {d}: no default group" for d in "ABCDEFGHIJKLMNOPQRS" if d not in data["divisions"]]
    problems += [f"division {d}: unknown group {g}" for d, g in data["divisions"].items() if g not in GROUPS]
    seen = set()
    for e in data["codes"]:
        if e["code"] in seen:
            problems.append(f"{e['code']}: listed twice")
        seen.add(e["code"])
        if anzsic.name(e["code"]) is None:
            problems.append(f"{e['code']}: not an ANZSIC 2006 code")
        if e["group"] not in GROUPS:
            problems.append(f"{e['code']}: unknown group {e['group']}")
    return problems
