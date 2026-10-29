"""Recommendations: what a government could do about a register item, drawn from Australian and international reviews
and research (``regulation-register/recommendations/``, one JSON file per recommendation).

A recommendation names the items it applies to, the action in plain English, why it would lift productivity or
competition, and the evidence for it: each source with the exact words that support it. The bodies that would act
default to those that administer the items (their ``responsible`` tags). Recommendations compiled by desk research
stay ``draft`` until a person has checked them, like the records. Owner request, 29 October 2026 (DECISIONS E-95).
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl, model_validator

from .catalogue import default_register_dir
from .framework import Confidence, Driver
from .schema import ChangeRecord, RecordId, Review, _Strict

RecommendationKind = Literal["remove", "reform", "replace", "extend", "harmonise", "review", "keep"]
KIND_LABELS: dict[str, str] = {
    "remove": "Remove a restriction",
    "reform": "Redesign",
    "replace": "Replace with a better tool",
    "extend": "Extend or adopt",
    "harmonise": "Make nationally consistent",
    "review": "Review or evaluate",
    "keep": "Keep, and guard against reversal",
}
Origin = Literal["australian", "international"]
# How a quote was checked: against the document's full text (downloaded), or against the published web page as read
# through a fetching tool (for sites that refuse downloads); the second is weaker and is shown as such.
Checked = Literal["full-text", "web-page"]


class Evidence(_Strict):
    """A source for the recommendation, with the exact words that support it."""

    source: str = Field(min_length=1, description="Title of the report or study")
    publisher: str = Field(min_length=1)
    year: int = Field(ge=1950, le=2100)
    url: HttpUrl
    locator: str | None = Field(default=None, description="Recommendation number, chapter or page")
    quote: str = Field(min_length=20, description="Exact words from the source")
    origin: Origin
    checked: Checked = "full-text"


class Precedent(_Strict):
    """Where the action has been taken, in Australia or abroad."""

    where: str = Field(min_length=1)
    what: str = Field(min_length=1)
    source: HttpUrl | None = None
    record: RecordId | None = Field(default=None, description="The register record that covers it, if any")

    @model_validator(mode="after")
    def _sourced(self) -> Precedent:
        if self.source is None and self.record is None:
            raise ValueError("a precedent needs a source or a register record")
        return self


class Progress(_Strict):
    """What governments have already done towards the action, with its source."""

    what: str = Field(min_length=1)
    source: HttpUrl | None = None
    records: tuple[RecordId, ...] = Field(default=(), description="Register records that show it")

    @model_validator(mode="after")
    def _sourced(self) -> Progress:
        if self.source is None and not self.records:
            raise ValueError("progress needs a source or register records")
        return self


class Recommendation(_Strict):
    id: RecordId
    title: str = Field(min_length=1, max_length=100, description="The action, in a few plain words")
    action: str = Field(min_length=1, description="What government should do, in plain English")
    why: str = Field(min_length=1, description="Why it would lift productivity or competition")
    kind: RecommendationKind
    applies_to: tuple[RecordId, ...] = Field(min_length=1, description="Register records it concerns")
    actors: tuple[RecordId, ...] = Field(
        default=(), description="Bodies that would act; empty means those that administer the records"
    )
    drivers: tuple[Driver, ...] = Field(min_length=1, description="Framework drivers it works through")
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    precedents: tuple[Precedent, ...] = ()
    progress: Progress | None = Field(default=None, description="What governments have already done towards it")
    tradeoffs: str | None = Field(default=None, description="What to weigh: safety, health, revenue, transition")
    confidence: Confidence = Field(description="How strong and consistent the evidence for the action is")
    drafted_on: dt.date
    review: Review = Review()

    @model_validator(mode="after")
    def _no_duplicates(self) -> Recommendation:
        for name in ("applies_to", "actors", "drivers"):
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} has duplicates")
        return self


def default_recommendations_dir() -> Path:
    return default_register_dir() / "recommendations"


@dataclass
class RecommendationsResult:
    recommendations: list[Recommendation] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def load_recommendations(path: Path | None = None) -> RecommendationsResult:
    """Read every recommendation; collect problems rather than stopping at the first."""
    path = path or default_recommendations_dir()
    result = RecommendationsResult()
    seen: set[str] = set()
    for file in sorted(path.glob("*.json")) if path.exists() else []:
        try:
            rec = Recommendation.model_validate(json.loads(file.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, ValueError) as exc:
            result.problems.append(f"recommendations/{file.name}: {exc}")
            continue
        if rec.id != file.stem:
            result.problems.append(f"recommendations/{file.name}: id '{rec.id}' does not match the file name")
        if rec.id in seen:
            result.problems.append(f"recommendations/{file.name}: duplicate id")
        seen.add(rec.id)
        result.recommendations.append(rec)
    return result


def write_recommendation(rec: Recommendation, path: Path | None = None) -> Path:
    path = path or default_recommendations_dir()
    path.mkdir(parents=True, exist_ok=True)
    out = path / f"{rec.id}.json"
    out.write_text(json.dumps(rec.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def check_recommendations(recs: list[Recommendation], records: list[ChangeRecord], bodies: dict) -> list[str]:
    """Every recommendation names known records, bodies and precedent records."""
    ids = {r.id for r in records}
    problems = []
    for rec in recs:
        problems += [f"recommendations/{rec.id}.json: unknown record '{x}'" for x in rec.applies_to if x not in ids]
        problems += [f"recommendations/{rec.id}.json: unknown body '{b}'" for b in rec.actors if b not in bodies]
        problems += [
            f"recommendations/{rec.id}.json: precedent names unknown record '{p.record}'"
            for p in rec.precedents
            if p.record and p.record not in ids
        ]
        problems += [
            f"recommendations/{rec.id}.json: progress names unknown record '{x}'"
            for x in (rec.progress.records if rec.progress else ())
            if x not in ids
        ]
    return problems


def default_gaps_path() -> Path:
    return default_register_dir() / "recommendation-gaps.json"


def load_gaps(path: Path | None = None) -> dict[str, str]:
    """Why some items have no recommendation, keyed by family or record id (``recommendation-gaps.json``)."""
    path = path or default_gaps_path()
    return json.loads(path.read_text(encoding="utf-8"))["gaps"] if path.exists() else {}


def gap_for(record: ChangeRecord, gaps: dict[str, str]) -> str | None:
    return gaps.get(record.id) or (gaps.get(record.family) if record.family else None)


def check_coverage(recs: list[Recommendation], records: list[ChangeRecord], gaps: dict[str, str]) -> list[str]:
    """Every record has a recommendation or a stated reason for having none; every gap key names a family or record."""
    covered = set(by_record(recs))
    keys = {r.id for r in records} | {r.family for r in records if r.family}
    problems = [f"recommendation-gaps.json: unknown family or record '{k}'" for k in gaps if k not in keys]
    problems += [
        f"{r.id}.json: no recommendation and no reason in recommendation-gaps.json"
        for r in records
        if r.id not in covered and not gap_for(r, gaps)
    ]
    return problems


def by_record(recs: list[Recommendation]) -> dict[str, list[Recommendation]]:
    out: dict[str, list[Recommendation]] = {}
    for rec in recs:
        for rid in rec.applies_to:
            out.setdefault(rid, []).append(rec)
    return out


def actors_of(rec: Recommendation, records: dict[str, ChangeRecord]) -> list[str]:
    """The bodies that would act: the named actors, else those that administer the records or lead policy on them."""
    if rec.actors:
        return list(rec.actors)
    out: list[str] = []
    for rid in rec.applies_to:
        r = records.get(rid)
        for x in r.responsible if r else ():
            if x.role in ("administers", "policy") and x.body not in out:
                out.append(x.body)
    return out


def json_schema() -> dict:
    schema = Recommendation.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Recommendation"
    return schema


__all__ = [
    "KIND_LABELS",
    "Evidence",
    "Precedent",
    "Progress",
    "Recommendation",
    "actors_of",
    "by_record",
    "check_coverage",
    "check_recommendations",
    "gap_for",
    "load_gaps",
    "load_recommendations",
    "write_recommendation",
]
