"""Group names for register families (``regulation-register/families.json``).

A family is one policy that several items share, usually the same law or setting in several jurisdictions. Its group
name says what the issue is across them ("Inconsistent adoption of the 2022 building code standards"), so the menu can
show the family as one expandable row with each jurisdiction's item, and its own assessment, beneath. Owner request,
29 October 2026 (DECISIONS E-99).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from pydantic import Field

from .catalogue import default_register_dir
from .schema import ChangeRecord, RecordId, _Strict


class Family(_Strict):
    id: RecordId
    title: str = Field(min_length=1, max_length=100, description="Plain English: the issue across the jurisdictions")
    summary: str = Field(min_length=1, description="One or two sentences on how the jurisdictions compare")


def default_families_path() -> Path:
    return default_register_dir() / "families.json"


def load_families(path: Path | None = None) -> tuple[dict[str, Family], list[str]]:
    """The group names by family id, and any problems (duplicate ids)."""
    path = path or default_families_path()
    if not path.exists():
        return {}, []
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, Family] = {}
    problems: list[str] = []
    for item in raw.get("families", []):
        fam = Family.model_validate(item)
        if fam.id in out:
            problems.append(f"families.json: duplicate id '{fam.id}'")
        out[fam.id] = fam
    return out, problems


def check_families(families: dict[str, Family], records: list[ChangeRecord]) -> list[str]:
    """Every family shared by two or more items has a group name, and every group name belongs to a family."""
    sizes = Counter(r.family for r in records if r.family)
    problems = [f"families.json: no family '{f}' in the register" for f in families if f not in sizes]
    problems += [
        f"families.json: family '{f}' has {n} items but no group name"
        for f, n in sorted(sizes.items())
        if n > 1 and f not in families
    ]
    return problems


__all__ = ["Family", "check_families", "default_families_path", "load_families"]
