"""The government bodies the register's items are tagged with (``regulation-register/bodies.json``).

Each record's ``responsible`` list names bodies from this registry by id, with a role (administers, regulates,
leads policy) and the source for that responsibility. Departments come from each jurisdiction's administrative
arrangements; agencies and regulators name the department or portfolio they sit in (``parent``), so the
legislation menu can filter by department and include its agencies. Owner request, 28 October 2026 (DECISIONS E-94).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, TypeAdapter

from .catalogue import default_register_dir
from .schema import JURISDICTIONS, RecordId

BodyType = Literal["department", "agency", "regulator"]
BODY_TYPE_LABELS: dict[str, str] = {"department": "Department", "agency": "Agency", "regulator": "Regulator"}
BodyJurisdiction = Literal["CTH", "NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT", "national"]


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: RecordId
    name: str = Field(min_length=1)
    short: str = Field(min_length=1, description="Short name or acronym for tags")
    jurisdiction: BodyJurisdiction = Field(description="'national' for bodies of national schemes, such as Ahpra")
    type: BodyType
    parent: RecordId | None = Field(default=None, description="The department (or portfolio) it sits in")
    url: HttpUrl
    source: HttpUrl = Field(description="Where the body's name and place in government are stated")
    current: bool = Field(default=True, description="False for a body since abolished or renamed")
    note: str | None = None


def default_bodies_path() -> Path:
    return default_register_dir() / "bodies.json"


def load_bodies(path: Path | None = None) -> tuple[dict[str, Body], list[str]]:
    """The registry by id, and any problems (duplicate ids, unknown or non-department parents)."""
    raw = json.loads((path or default_bodies_path()).read_text(encoding="utf-8"))
    bodies = TypeAdapter(list[Body]).validate_python(raw)
    out: dict[str, Body] = {}
    problems: list[str] = []
    for b in bodies:
        if b.id in out:
            problems.append(f"bodies.json: duplicate id '{b.id}'")
        out[b.id] = b
    for b in bodies:
        if b.parent and b.parent not in out:
            problems.append(f"bodies.json: {b.id}: unknown parent '{b.parent}'")
        elif b.parent and out[b.parent].type != "department":
            problems.append(f"bodies.json: {b.id}: parent '{b.parent}' is not a department")
        if b.type == "department" and b.parent:
            problems.append(f"bodies.json: {b.id}: a department has no parent")
    return out, problems


def department_of(body: Body, bodies: dict[str, Body]) -> Body | None:
    """The department a body is, or sits in."""
    if body.type == "department":
        return body
    return bodies.get(body.parent) if body.parent else None


def check_records(records, bodies: dict[str, Body]) -> list[str]:
    """Every responsibility names a known body; every item has a responsible department or policy lead."""
    problems = []
    for r in records:
        for x in r.responsible:
            if x.body not in bodies:
                problems.append(f"{r.id}.json: responsible: unknown body '{x.body}'")
        if not any(x.role in ("administers", "policy") for x in r.responsible):
            problems.append(f"{r.id}.json: responsible: needs a body that administers it or leads policy")
    return problems


__all__ = ["BODY_TYPE_LABELS", "JURISDICTIONS", "Body", "check_records", "department_of", "load_bodies"]
