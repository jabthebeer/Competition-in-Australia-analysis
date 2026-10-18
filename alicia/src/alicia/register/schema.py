"""The register of regulatory changes: one record per change per jurisdiction.

A record says what changed, when, for whom, and why it might matter for competition.
The direction ("enhancing" or "weakening") is a hypothesis to be tested, not a finding.
Records compiled by desk research stay ``draft`` until a person has checked them.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, HttpUrl, model_validator

Jurisdiction = Literal["CTH", "NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"]
JURISDICTIONS: tuple[str, ...] = ("CTH", "NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT")
STATES: tuple[str, ...] = JURISDICTIONS[1:]

Direction = Literal["enhancing", "weakening", "mixed", "unclear"]

# OIA, "How to consider competition in impact analysis" (July 2026), Step 1 categories,
# which the guidance says are broadly based on the OECD Competition Assessment Toolkit.
Channel = Literal["barriers", "number-or-type", "ability-incentive", "prices-market-share", "consumer-choice"]
CHANNEL_LABELS: dict[str, str] = {
    "barriers": "Barriers to entry, growth or exit",
    "number-or-type": "Number or types of businesses that can operate",
    "ability-incentive": "Ability or incentives to compete",
    "prices-market-share": "Conditions that influence prices or market share",
    "consumer-choice": "Choices, information, goods or services available to consumers",
}

InstrumentRole = Literal["principal", "amending", "regulation", "code", "other"]
Exposure = Literal["direct", "indirect"]

_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ANZSIC = re.compile(r"^(?:[A-S]|\d{2}|\d{3}|\d{4})$")


def _check_id(v: str) -> str:
    if not _ID.match(v):
        raise ValueError("must be kebab-case: lower-case letters and digits separated by hyphens")
    return v


def _check_anzsic(v: str) -> str:
    if not _ANZSIC.match(v):
        raise ValueError("must be an ANZSIC 2006 division letter or a 2-, 3- or 4-digit code")
    return v


RecordId = Annotated[str, AfterValidator(_check_id)]
AnzsicCode = Annotated[str, AfterValidator(_check_anzsic)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Instrument(_Strict):
    title: str = Field(min_length=1)
    register_url: HttpUrl | None = None
    register_id: str | None = Field(default=None, description="Register identifier, e.g. C2021A00123")
    role: InstrumentRole
    provisions: str | None = None


class DatedSource(_Strict):
    date: dt.date | None = None
    source: HttpUrl | None = None

    @model_validator(mode="after")
    def _source_for_date(self) -> DatedSource:
        if self.date is not None and self.source is None:
            raise ValueError("a date needs a source URL")
        return self


class Commencement(_Strict):
    date: dt.date
    what: str = Field(min_length=1, description="Which provisions, or what took effect")
    source: HttpUrl
    primary: bool = Field(
        default=False,
        description="The commencement that changes competition conditions; used as the effective date",
    )


class Dates(_Strict):
    announced: DatedSource = DatedSource()
    assent_or_made: DatedSource = DatedSource()
    commenced: tuple[Commencement, ...] = ()

    @model_validator(mode="after")
    def _one_primary(self) -> Dates:
        if sum(c.primary for c in self.commenced) > 1:
            raise ValueError("at most one commencement can be marked primary")
        return self


class Industry(_Strict):
    anzsic: AnzsicCode
    name: str = Field(min_length=1)
    exposure: Exposure


class Verification(_Strict):
    dates: bool
    notes: str | None = None


class Review(_Strict):
    """Whether a person has checked the record. Desk-research drafts start as ``draft``."""

    status: Literal["draft", "reviewed"] = "draft"
    by: str | None = None
    on: dt.date | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _reviewed_has_reviewer(self) -> Review:
        if self.status == "reviewed" and (not self.by or self.on is None):
            raise ValueError("a reviewed record needs 'by' and 'on'")
        return self


class ChangeRecord(_Strict):
    id: RecordId
    family: RecordId | None = Field(default=None, description="Shared by one reform across jurisdictions")
    title: str = Field(min_length=1)
    jurisdiction: Jurisdiction
    summary: str = Field(min_length=1)
    instruments: tuple[Instrument, ...] = Field(min_length=1)
    dates: Dates
    direction: Direction = Field(description="Hypothesised competition effect, to be tested")
    direction_rationale: str = Field(min_length=1)
    direction_sources: tuple[HttpUrl, ...] = ()
    channels: tuple[Channel, ...] = Field(min_length=1)
    industries: tuple[Industry, ...] = Field(min_length=1)
    comparison: str = Field(min_length=1)
    confounders: tuple[str, ...] = ()
    price_series: str | None = None
    notes: str | None = None
    verified: Verification
    review: Review = Review()

    @model_validator(mode="after")
    def _no_duplicates(self) -> ChangeRecord:
        if len(set(self.channels)) != len(self.channels):
            raise ValueError("channels must not repeat")
        codes = [i.anzsic for i in self.industries]
        if len(set(codes)) != len(codes):
            raise ValueError("industries must not repeat")
        return self

    @property
    def effective_commencement(self) -> Commencement | None:
        """The primary commencement, else the earliest one; None if not yet commenced."""
        if not self.dates.commenced:
            return None
        for c in self.dates.commenced:
            if c.primary:
                return c
        return min(self.dates.commenced, key=lambda c: c.date)


def json_schema() -> dict:
    """JSON Schema for a record, so other tools (e.g. the TypeScript calculator) can validate."""
    schema = ChangeRecord.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Regulatory change record"
    return schema
