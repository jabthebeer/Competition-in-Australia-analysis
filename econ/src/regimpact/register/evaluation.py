"""Evaluation results: what an evaluation found for one or more register records.

A record's ``direction`` stays a hypothesis. Results live in separate files,
``regulation-register/evaluations/<id>.json``, one per evaluation. A single evaluation can cover
several records, such as two steps of the same reform. Each file is written by its analysis's
builder script from the analysis outputs, never typed by hand. The tests check the numbers
against those outputs.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from .schema import ChangeRecord, Direction, RecordId, _Strict

Category = Literal["competition", "prices", "productivity"]
CATEGORY_LABELS: dict[str, str] = {
    "competition": "Competition",
    "prices": "Prices",
    "productivity": "Productivity and pay",
}
Role = Literal["primary", "secondary", "descriptive"]
Verdict = Literal[
    "supports-enhancing",
    "supports-weakening",
    "contradicts-enhancing",
    "contradicts-weakening",
    "detects-increase",
    "detects-decrease",
    "inconclusive",
    "not-identified",
]
Grade = Literal["Strong", "Moderate", "Weak", "Not identified"]
Finding = Literal["increase", "decrease", "no-detectable-effect", "not-identified", "descriptive-only"]


class Interval(_Strict):
    low: float
    high: float
    level: float = Field(0.9, gt=0, lt=1)

    @model_validator(mode="after")
    def _ordered(self) -> Interval:
        if self.low > self.high:
            raise ValueError("low must not exceed high")
        return self


class NoEffectRange(_Strict):
    """What the estimator gives where there was no reform (placebos), drawn around zero."""

    low: float
    high: float
    basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def _ordered(self) -> NoEffectRange:
        if self.low > self.high:
            raise ValueError("low must not exceed high")
        return self


class OutcomeResult(_Strict):
    id: RecordId
    label: str = Field(min_length=1)
    category: Category
    role: Role
    unit: str = Field(min_length=1)
    baseline: float | None = None
    baseline_label: str | None = None
    estimate: float
    interval: Interval | None = None
    no_effect_range: NoEffectRange
    p_value: float | None = Field(None, ge=0, le=1)
    inference: str = Field(min_length=1)
    mde_80: float | None = Field(None, gt=0, description="Smallest effect detectable with 80% power")
    finding: Finding
    grade: Grade | None = None
    preregistered: bool
    note: str = ""


class EventPoint(_Strict):
    period: str
    k: int
    estimate: float
    low: float | None = None
    high: float | None = None


class Marker(_Strict):
    k: float
    label: str


class EventStudy(_Strict):
    outcome: RecordId
    title: str
    unit: str
    reference: str
    band: str | None = None
    points: tuple[EventPoint, ...] = Field(min_length=2)
    markers: tuple[Marker, ...] = ()
    caption: str = ""


class Document(_Strict):
    label: str
    path: str = Field(pattern=r"^[A-Za-z0-9_./-]+$", description="Path relative to the repository root")


class Evaluation(_Strict):
    id: RecordId
    title: str = Field(min_length=1)
    records: tuple[RecordId, ...] = Field(min_length=1)
    family: RecordId | None = None
    evaluated_on: dt.date
    hypothesis: Direction
    design: str = Field(min_length=1)
    comparison: str = Field(min_length=1)
    window: str = Field(min_length=1)
    verdict: Verdict
    finding_label: str = Field(min_length=1, max_length=40)
    grade: Grade
    grade_reason: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    category_summaries: dict[Category, str]
    preregistered: bool
    outcomes: tuple[OutcomeResult, ...] = Field(min_length=1)
    event_studies: tuple[EventStudy, ...] = ()
    caveats: tuple[str, ...] = ()
    documents: tuple[Document, ...] = ()
    built_by: str = Field(min_length=1, description="Script that wrote this file from the analysis outputs")

    @model_validator(mode="after")
    def _consistent(self) -> Evaluation:
        ids = [o.id for o in self.outcomes]
        if len(set(ids)) != len(ids):
            raise ValueError("outcome ids must not repeat")
        if len(set(self.records)) != len(self.records):
            raise ValueError("records must not repeat")
        missing = [e.outcome for e in self.event_studies if e.outcome not in ids]
        if missing:
            raise ValueError(f"event studies refer to unknown outcomes: {missing}")
        return self


@dataclass
class EvaluationLoad:
    evaluations: list[Evaluation] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def default_evaluations_dir() -> Path:
    return Path(__file__).resolve().parents[4] / "regulation-register" / "evaluations"


def load_evaluations(records: list[ChangeRecord] | None = None, evaluations_dir: Path | None = None) -> EvaluationLoad:
    """Read every evaluation file; check ids, file names, and (when given) that records exist."""
    from .catalogue import _describe

    folder = evaluations_dir or default_evaluations_dir()
    out = EvaluationLoad()
    by_id = {r.id: r for r in records or []}
    covered: dict[str, str] = {}
    for path in sorted(folder.glob("*.json")) if folder.exists() else []:
        try:
            ev = Evaluation.model_validate(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            out.problems.append(f"evaluations/{path.name}: not valid JSON ({exc})")
            continue
        except ValidationError as exc:
            out.problems.extend(f"evaluations/{path.name}: {m}" for m in _describe(exc))
            continue
        if path.stem != ev.id:
            out.problems.append(f"evaluations/{path.name}: file name must match id '{ev.id}'")
        if records is not None:
            for rid in ev.records:
                rec = by_id.get(rid)
                if rec is None:
                    out.problems.append(f"evaluations/{path.name}: unknown record '{rid}'")
                elif ev.family and rec.family != ev.family:
                    out.problems.append(f"evaluations/{path.name}: record '{rid}' is not in family '{ev.family}'")
                if rid in covered:
                    out.problems.append(f"evaluations/{path.name}: record '{rid}' is also in '{covered[rid]}'")
                covered[rid] = ev.id
        out.evaluations.append(ev)
    return out


def write_evaluation(ev: Evaluation, evaluations_dir: Path | None = None) -> Path:
    folder = evaluations_dir or default_evaluations_dir()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{ev.id}.json"
    path.write_text(json.dumps(ev.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def json_schema() -> dict:
    schema = Evaluation.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Evaluation result"
    return schema
