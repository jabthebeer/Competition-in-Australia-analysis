"""The register of regulatory changes: one record per change per jurisdiction.

A record says what changed, when, for whom, and why it might matter for competition and productivity.
The direction ("enhancing" or "weakening") is a hypothesis, not a finding. Each record carries an assessment
against the productivity impact framework (``register/framework.py``). Besides reforms, the register holds
existing settings and non-legislative barriers (``kind``). Records compiled by desk research stay ``draft`` until a
person has checked them.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, HttpUrl, model_validator

from .framework import Confidence, Driver, Kind, Reach, rating

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


class DriverMark(_Strict):
    """One driver's mark: -2 (major harm) to +2 (major gain). Drivers left out are marked 0."""

    driver: Driver
    mark: int = Field(ge=-2, le=2)
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def _not_zero(self) -> DriverMark:
        if self.mark == 0:
            raise ValueError("leave a driver out rather than marking it 0")
        return self


class Assessment(_Strict):
    """The item marked against the productivity impact framework (``register/framework.py``)."""

    summary: str = Field(min_length=1, description="Plain English: what it does to productivity and competition")
    marks: tuple[DriverMark, ...] = Field(min_length=1)
    main_driver: Driver
    reach: Reach
    confidence: Confidence
    confidence_note: str | None = None
    evidence: tuple[HttpUrl, ...] = Field(default=(), description="Sources for the marks beyond the record's own")
    framework: str = Field(default="1.0", description="Framework version the marks follow")
    assessed_on: dt.date

    @model_validator(mode="after")
    def _consistent(self) -> Assessment:
        drivers = [m.driver for m in self.marks]
        if len(set(drivers)) != len(drivers):
            raise ValueError("each driver can be marked once")
        top = max(abs(m.mark) for m in self.marks)
        if self.main_driver not in {m.driver for m in self.marks if abs(m.mark) == top}:
            raise ValueError("main_driver must be a driver with the largest mark (either way)")
        return self

    @property
    def total(self) -> int:
        return sum(m.mark for m in self.marks)

    @property
    def rating(self) -> str:
        return rating(self.total)

    @property
    def mixed(self) -> bool:
        return any(m.mark > 0 for m in self.marks) and any(m.mark < 0 for m in self.marks)

    def mark(self, driver: str) -> int:
        return next((m.mark for m in self.marks if m.driver == driver), 0)


class ChangeRecord(_Strict):
    id: RecordId
    kind: Kind = Field(default="reform", description="reform, existing setting or non-legislative barrier")
    family: RecordId | None = Field(default=None, description="Shared by one reform across jurisdictions")
    title: str = Field(min_length=1)
    jurisdiction: Jurisdiction
    summary: str = Field(min_length=1)
    instruments: tuple[Instrument, ...] = Field(default=(), description="Required for reforms and settings")
    dates: Dates
    direction: Direction = Field(description="Hypothesised competition effect, to be tested")
    direction_rationale: str = Field(min_length=1)
    direction_sources: tuple[HttpUrl, ...] = ()
    channels: tuple[Channel, ...] = Field(min_length=1)
    industries: tuple[Industry, ...] = Field(default=(), description="Required unless the item is economy-wide")
    comparison: str | None = Field(default=None, description="Comparison group for an econometric evaluation")
    confounders: tuple[str, ...] = ()
    price_series: str | None = None
    notes: str | None = None
    verified: Verification
    review: Review = Review()
    assessment: Assessment | None = None

    @model_validator(mode="after")
    def _no_duplicates(self) -> ChangeRecord:
        if len(set(self.channels)) != len(self.channels):
            raise ValueError("channels must not repeat")
        codes = [i.anzsic for i in self.industries]
        if len(set(codes)) != len(codes):
            raise ValueError("industries must not repeat")
        return self

    @model_validator(mode="after")
    def _kind_needs(self) -> ChangeRecord:
        if self.kind != "barrier" and not self.instruments:
            raise ValueError(f"a {self.kind} needs at least one instrument (law, regulation, code or policy)")
        if not self.industries and not (self.assessment and self.assessment.reach == "economy-wide"):
            raise ValueError("industries can be left empty only for an item assessed as economy-wide")
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
