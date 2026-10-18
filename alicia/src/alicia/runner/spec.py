"""Specification files: one per evaluation design, read by the analysis code and by the runner.

A specification says, before any result is seen, what an evaluation will estimate and how:
the register records and dates, the treated units and industries, the outcomes, the control set,
the estimators, the windows and the placebo pools, and the stages that produce the design review,
the registered estimate and the evaluation file.

Specifications live in ``alicia/specs/<id>.json`` and are validated here. The analysis modules read
their constants from their specification (``load(id).parameters`` and ``.outcomes``), so the file is
the single source of the design; ``alicia spec run <id> --check`` re-runs the stages and confirms
that every output is byte-identical to the committed one.
"""

from __future__ import annotations

import datetime as dt
import json
from functools import cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, model_validator

from ..register.schema import RecordId, _Strict

StageKind = Literal["design", "dry-run", "estimate", "post-hoc", "derived", "evaluation"]
Role = Literal["primary", "secondary", "descriptive", "robustness"]


def specs_dir() -> Path:
    """``alicia/specs/`` (this file is alicia/src/alicia/runner/spec.py)."""
    return Path(__file__).resolve().parents[3] / "specs"


def analyses_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "analyses"


class Cohort(_Strict):
    """Units adopting together: first exposed period, last period used, and clean comparison units."""

    treated: tuple[str, ...] = Field(min_length=1)
    first_post: int
    last_post: int
    controls: tuple[str, ...]

    @model_validator(mode="after")
    def _ordered(self) -> Cohort:
        if self.last_post < self.first_post:
            raise ValueError("last_post must not precede first_post")
        if set(self.treated) & set(self.controls):
            raise ValueError("a unit cannot be both treated and a control")
        return self


class Window(_Strict):
    """Event window in the outcome's own periods: ``pre`` periods, ``gap`` excluded, ``post`` periods."""

    event: str = Field(description="First post period (ISO date) or an index such as a financial year")
    pre: int = Field(ge=0)
    gap: int = Field(ge=0)
    post: int = Field(ge=1)
    block: int = Field(1, ge=1, description="Periods per event-study bin")


class PlaceboPool(_Strict):
    """Where the no-effect distribution comes from."""

    kind: Literal["industries", "cpi-classes", "units", "dates", "areas"]
    rule: str = Field(min_length=1, description="How members are chosen, in words")


class Outcome(_Strict):
    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    role: Role
    source: str = Field(min_length=1, description="Processed panel or connector")
    measure: str = Field(min_length=1)
    frequency: Literal["monthly", "quarterly", "financial-year", "annual", "snapshot"]
    unit: str = Field(min_length=1, description="Unit of analysis, e.g. state, capital city, SA4 area")
    industries: tuple[str, ...] = ()
    cohorts: tuple[Cohort, ...] = ()
    window: Window | None = None
    estimator: str = Field(min_length=1)
    controls: tuple[str, ...] = ()
    placebo_pools: tuple[PlaceboPool, ...] = ()
    pre_registered: bool = True
    notes: tuple[str, ...] = ()


class Stage(_Strict):
    name: str = Field(min_length=1)
    kind: StageKind
    script: str = Field(min_length=1, description="Path under the analysis folder")
    args: tuple[str, ...] = ()
    writes: tuple[str, ...] = Field(min_length=1, description="Paths relative to the alicia/ folder")
    blind: bool = False


class Specification(_Strict):
    id: RecordId
    title: str = Field(min_length=1)
    analysis: str = Field(min_length=1, description="Folder under alicia/analyses")
    plan: str = Field(min_length=1, description="Pre-analysis plan, relative to the repository root")
    registered_on: dt.date | None = None
    follows: RecordId | None = None
    records: tuple[RecordId, ...] = Field(min_length=1)
    evaluations: tuple[RecordId, ...] = ()
    hypothesis: Literal["enhancing", "weakening", "mixed"]
    outcomes: tuple[Outcome, ...] = ()
    stages: tuple[Stage, ...] = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict, description="Analysis-specific constants")
    cases: tuple[dict[str, Any], ...] = Field(default=(), description="Batch specifications: one entry per case")
    notes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _unique(self) -> Specification:
        keys = [o.key for o in self.outcomes]
        if len(set(keys)) != len(keys):
            raise ValueError("outcome keys must be unique")
        names = [s.name for s in self.stages]
        if len(set(names)) != len(names):
            raise ValueError("stage names must be unique")
        return self

    def outcome(self, key: str) -> Outcome:
        return next(o for o in self.outcomes if o.key == key)

    def param(self, name: str) -> Any:
        return self.parameters[name]


@cache
def load(spec_id: str) -> Specification:
    """One specification by id (cached: analysis modules read it at import)."""
    path = specs_dir() / f"{spec_id}.json"
    return Specification.model_validate(json.loads(path.read_text("utf-8")))


def load_all() -> tuple[list[Specification], list[str]]:
    specs, problems = [], []
    for path in sorted(specs_dir().glob("*.json")):
        try:
            spec = Specification.model_validate(json.loads(path.read_text("utf-8")))
        except (ValidationError, json.JSONDecodeError) as exc:
            problems.append(f"{path.name}: {exc}")
            continue
        if spec.id != path.stem:
            problems.append(f"{path.name}: file name must match id '{spec.id}'")
        specs.append(spec)
    return specs, problems


def json_schema() -> dict:
    schema = Specification.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Evaluation specification"
    return schema
