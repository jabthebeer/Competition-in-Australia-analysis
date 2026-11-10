"""Requirements: what a law asks of a business, and which ANZSIC classes it reaches.

Phase B of the legislation-links plan (``docs/plan_legislation_links.md``; DECISIONS E-116, E-119). One JSON file per
requirement per jurisdiction, in ``regulation-register/requirements/<jurisdiction>/`` (``cth``, ``nsw``, ... and, for
council-made instruments, ``local/<LGA code>/``). The coding rules are in ``docs/methods_legislation_links.md``.

A requirement records:

- the **laws** behind it, each with an official register ID or link and the provision;
- what the business must do (**kind**, **what**) and what **triggers** it (starting up, a first employee, a size
  threshold, an activity, closing), with any threshold value sourced;
- its **reach**: every class, listed classes, listed classes limited to ABS primary activities (quoted exactly as the
  ABS lists them), or listed classes when the business also does something else (a ``condition``, for laws that follow
  an activity across classes), optionally limited to some legal forms;
- the sources for each of those, quoted word for word, and a confidence rating.

``links`` expands requirements into one row per class and requirement: the table that joins each legislative level
to the ANZSIC classes. A requirement that reaches every business is stored once and expanded only in that table.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl, model_validator

from .. import anzsic
from .catalogue import default_register_dir
from .framework import Driver
from .regimes import Tier
from .schema import JURISDICTIONS, AnzsicCode, Assessment, DriverMark, Jurisdiction, RecordId, Review, _Strict

LawKind = Literal["act", "regulation", "legislative-instrument", "code", "planning-instrument", "local-law", "other"]
RequirementKind = Literal[
    "registration",
    "licence",
    "approval",
    "notification",
    "tax-or-levy",
    "insurance",
    "reporting",
    "record-keeping",
    "standard",
    "other",
]
KIND_LABELS: dict[str, str] = {
    "registration": "Register",
    "licence": "Hold a licence, permit or accreditation",
    "approval": "Get an approval for premises, a project or a product",
    "notification": "Notify a regulator",
    "tax-or-levy": "Pay a tax, levy or fee",
    "insurance": "Hold insurance",
    "reporting": "Report or lodge",
    "record-keeping": "Keep records",
    "standard": "Meet a standard or code",
    "other": "Other",
}
TriggerType = Literal[
    "entry",
    "first-employee",
    "employees",
    "payroll",
    "turnover",
    "revenue",
    "assets",
    "quantity",
    "activity",
    "ongoing",
    "exit",
]
TRIGGER_LABELS: dict[str, str] = {
    "entry": "Before starting to trade",
    "first-employee": "On taking on a first employee",
    "employees": "Above a number of employees",
    "payroll": "Above a payroll threshold",
    "turnover": "Above a turnover threshold",
    "revenue": "Above a revenue threshold",
    "assets": "Above an asset threshold",
    "quantity": "Above another measured threshold (floor area, emissions, livestock and so on)",
    "activity": "When carrying out a particular activity",
    "ongoing": "While operating",
    "exit": "On closing or selling the business",
}
# Thresholds need a value, a test and a unit; the other triggers have none.
VALUED: tuple[str, ...] = ("employees", "payroll", "turnover", "revenue", "assets", "quantity")
# Legal forms, after the ABS's Type of Legal Organisation (SESCA 2008) and ABLIS's business structures.
LegalForm = Literal["sole-proprietor", "partnership", "trust", "company", "co-operative", "incorporated-association"]
Confidence = Literal["high", "medium", "low"]
CONFIDENCE_HELP: dict[str, str] = {
    "high": "The law's own words name the activity, or its scope clearly covers every business in the class",
    "medium": "Official guidance (a regulator, business.gov.au or ABLIS) names the industry",
    "low": "Inferred from the ABS class definition; no source names the industry",
}
# How a quote was checked: against the official register's text; against a downloaded official document; against a
# web page as read through a fetching tool; or against the Open Australian Legal Corpus's copy of the official text
# (for NSW and SA, whose registers refuse automated requests; DECISIONS E-118).
Checked = Literal["register-text", "document", "web-page", "corpus-copy"]


class Source(_Strict):
    """A source with the exact words that support a claim."""

    title: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    url: HttpUrl
    locator: str | None = Field(default=None, description="Section, clause, page or heading")
    quote: str = Field(min_length=20, description="Exact words from the source")
    accessed: dt.date
    checked: Checked
    corpus_version_id: str | None = Field(default=None, description="The corpus document read, for 'corpus-copy'")

    @model_validator(mode="after")
    def _corpus_id(self) -> Source:
        if (self.checked == "corpus-copy") != (self.corpus_version_id is not None):
            raise ValueError("a 'corpus-copy' source needs its corpus_version_id, and only such a source has one")
        return self


class Law(_Strict):
    """An Act, regulation, instrument, code, planning scheme or local law, as on its official register."""

    title: str = Field(min_length=1)
    jurisdiction: Jurisdiction
    kind: LawKind
    register_id: str | None = Field(default=None, description="e.g. C2004A00109, or the register's own identifier")
    register_url: HttpUrl | None = None
    provisions: str | None = Field(default=None, description="e.g. 's 9-5', 'Part 3, Division 2'")
    applied: bool = Field(
        default=False,
        description="A national law hosted by another jurisdiction (e.g. the Health Practitioner Regulation "
        "National Law in Queensland's Act) that this jurisdiction applies as its own law",
    )

    @model_validator(mode="after")
    def _traceable(self) -> Law:
        if self.register_id is None and self.register_url is None:
            raise ValueError("a law needs a register ID or an official register link")
        return self


class Trigger(_Strict):
    """What sets the requirement off."""

    type: TriggerType
    test: Literal[">=", ">", "<=", "<"] | None = None
    value: float | None = None
    unit: str | None = Field(default=None, description="e.g. 'AUD a financial year', 'employees'")
    as_at: dt.date | None = Field(default=None, description="When the value applied, as checked")
    note: str | None = None
    sources: tuple[Source, ...] = ()

    @model_validator(mode="after")
    def _value(self) -> Trigger:
        if self.type in VALUED:
            if self.value is None or self.test is None or self.unit is None or self.as_at is None:
                raise ValueError(f"a '{self.type}' trigger needs a test, value, unit and as_at date")
            if not self.sources:
                raise ValueError(f"a '{self.type}' threshold needs an official source")
        elif self.value is not None or self.test is not None:
            raise ValueError(f"a '{self.type}' trigger has no threshold value")
        return self


class Reach(_Strict):
    """Which businesses the requirement reaches.

    ``scope`` "all" reaches every class (less ``exclude``). Otherwise ``classes`` lists ANZSIC codes at any level;
    ``activities`` (only with 4-digit classes) limits the reach to those ABS primary activities, quoted exactly; and
    ``condition`` limits it to businesses in the classes that also do something else (an activity that crosses
    classes, such as selling alcohol)."""

    scope: Literal["all", "listed"]
    classes: tuple[AnzsicCode, ...] = ()
    exclude: tuple[AnzsicCode, ...] = ()
    activities: tuple[str, ...] = ()
    condition: str | None = Field(default=None, description="Plain English: 'if the business sells alcohol'")
    legal_forms: tuple[LegalForm, ...] = Field(default=(), description="Empty means every legal form")
    in_states: tuple[Jurisdiction, ...] = Field(
        default=(), description="For a Commonwealth requirement: the states and territories it reaches; empty means all"
    )
    note: str | None = None
    sources: tuple[Source, ...] = Field(min_length=1, description="Where the reach comes from, quoted")

    @model_validator(mode="after")
    def _shape(self) -> Reach:
        if self.scope == "all" and (self.classes or self.activities):
            raise ValueError("an 'all' reach lists no classes or activities (use 'exclude' for exceptions)")
        if self.scope == "listed" and not self.classes:
            raise ValueError("a 'listed' reach needs classes")
        if self.activities and not all(len(c) == 4 and c.isdigit() for c in self.classes):
            raise ValueError("activities can only qualify 4-digit classes")
        if self.activities and self.condition:
            raise ValueError("use activities or a condition, not both, in one reach")
        if "CTH" in self.in_states:
            raise ValueError("in_states lists states and territories, not CTH")
        return self


class RequirementAssessment(Assessment):
    """A requirement marked against the productivity impact framework, like a register item. Unlike an item, a small
    obligation may have no material effect on any driver (the framework's mark 0): it then has no marks and no main
    driver, and the summary says why."""

    marks: tuple[DriverMark, ...] = Field(default=(), description="Empty when it has no material effect")
    main_driver: Driver | None = None

    @model_validator(mode="after")
    def _consistent(self) -> RequirementAssessment:
        if not self.marks:
            if self.main_driver is not None:
                raise ValueError("an assessment with no marks has no main driver")
            return self
        drivers = [m.driver for m in self.marks]
        if len(set(drivers)) != len(drivers):
            raise ValueError("each driver can be marked once")
        top = max(abs(m.mark) for m in self.marks)
        if self.main_driver not in {m.driver for m in self.marks if abs(m.mark) == top}:
            raise ValueError("main_driver must be a driver with the largest mark (either way)")
        return self


class Requirement(_Strict):
    id: RecordId
    family: RecordId = Field(description="The same requirement across jurisdictions, e.g. 'food-business-registration'")
    jurisdiction: Jurisdiction
    tier: Tier
    lga: str | None = Field(default=None, pattern=r"^\d{5}$", description="ABS LGA code (ASGS 2021), for a council")
    lga_name: str | None = None
    regime: RecordId | None = Field(default=None, description="The regime it belongs to (regulation-register/regimes)")
    title: str = Field(min_length=1, max_length=100)
    kind: RequirementKind
    what: str = Field(min_length=1, description="Plain English: what the business must do")
    laws: tuple[Law, ...] = Field(min_length=1)
    sources: tuple[Source, ...] = Field(min_length=1, description="The obligation in the law's own words")
    administered_by: tuple[RecordId, ...] = Field(default=(), description="Bodies in bodies.json")
    administered_by_councils: bool = False
    triggers: tuple[Trigger, ...] = Field(min_length=1)
    reach: tuple[Reach, ...] = Field(min_length=1)
    confidence: Confidence
    confidence_note: str | None = None
    records: tuple[RecordId, ...] = Field(default=(), description="Register items about it")
    ablis: tuple[str, ...] = Field(default=(), description="ABLIS service IDs, once checked against ABLIS")
    assessment: RequirementAssessment = Field(
        description="The requirement marked against the productivity impact framework (register/framework.py), "
        "against the same market without it"
    )
    drafted_on: dt.date
    review: Review = Review()

    @model_validator(mode="after")
    def _tier(self) -> Requirement:
        expected = "cth" if self.jurisdiction == "CTH" else ("local" if self.lga else "state")
        if self.tier != expected:
            raise ValueError(f"tier should be '{expected}' for jurisdiction {self.jurisdiction} (lga: {self.lga})")
        if self.lga and not self.lga_name:
            raise ValueError("a council requirement needs lga_name")
        if self.jurisdiction != "CTH" and any(r.in_states for r in self.reach):
            raise ValueError("only a Commonwealth requirement can limit its reach to some states (in_states)")
        return self


def default_requirements_dir() -> Path:
    return default_register_dir() / "requirements"


def expected_folder(req: Requirement) -> str:
    return f"local/{req.lga}" if req.lga else req.jurisdiction.lower()


@dataclass
class RequirementsResult:
    requirements: list[Requirement] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def load_requirements(path: Path | None = None) -> RequirementsResult:
    path = path or default_requirements_dir()
    result = RequirementsResult()
    for file in sorted(path.rglob("*.json")) if path.exists() else []:
        rel = file.relative_to(path).as_posix()
        try:
            req = Requirement.model_validate(json.loads(file.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, ValueError) as exc:
            result.problems.append(f"requirements/{rel}: {exc}")
            continue
        if req.id != file.stem:
            result.problems.append(f"requirements/{rel}: id '{req.id}' does not match the file name")
        if file.parent.relative_to(path).as_posix() != expected_folder(req):
            result.problems.append(f"requirements/{rel}: belongs in requirements/{expected_folder(req)}/")
        result.requirements.append(req)
    return result


def write_requirement(req: Requirement, path: Path | None = None) -> Path:
    folder = (path or default_requirements_dir()) / expected_folder(req)
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / f"{req.id}.json"
    data = req.model_dump(mode="json", exclude_defaults=False)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


@cache
def primary_activities() -> dict[str, frozenset[str]]:
    """Each class's ABS primary activities, from data/processed/anzsic/ (scripts/fetch_anzsic_activities.py)."""
    p = default_register_dir().parent / "data" / "processed" / "anzsic" / "anzsic2006_classes.json"
    if not p.exists():
        return {}
    rows = json.loads(p.read_text("utf-8"))["rows"]
    return {r["class"]: frozenset(r["primary_activities"]) for r in rows}


LGA_STATE = {"1": "NSW", "2": "VIC", "3": "QLD", "4": "SA", "5": "WA", "6": "TAS", "7": "NT", "8": "ACT"}


@cache
def lga_names() -> dict[str, str]:
    """ABS LGA codes (ASGS 2021) and names, from data/processed/geo/ (the postcode correspondence)."""
    p = default_register_dir().parent / "data" / "processed" / "geo" / "postcode_2021_to_asgs.parquet"
    if not p.exists():
        return {}
    import pandas as pd

    d = pd.read_parquet(p, columns=["level", "code", "name"])
    d = d[d["level"] == "LGA"].drop_duplicates("code")
    return dict(zip(d["code"], d["name"], strict=True))


@cache
def _classes() -> tuple[str, ...]:
    return tuple(sorted(c for c in anzsic._codes() if len(c) == 4))


def _under(cls: str, code: str) -> bool:
    return anzsic.division(cls) == code if len(code) == 1 else cls.startswith(code)


def reach_classes(r: Reach) -> list[str]:
    """The classes a reach covers."""
    inc = _classes() if r.scope == "all" else [c for c in _classes() if any(_under(c, a) for a in r.classes)]
    return [c for c in inc if not any(_under(c, x) for x in r.exclude)]


def check_requirements(reqs: list[Requirement], bodies: dict, regimes: set[str], records: set[str]) -> list[str]:
    """Codes, ABS activities, regimes, bodies and records exist; ids are unique; families keep one per place."""
    problems: list[str] = []
    acts = primary_activities()
    seen: dict[str, str] = {}
    places: dict[tuple[str, str, str | None], str] = {}
    for q in reqs:
        where = f"requirements/{expected_folder(q)}/{q.id}.json"
        if q.id in seen:
            problems.append(f"{where}: id also used in {seen[q.id]}")
        seen[q.id] = where
        key = (q.family, q.jurisdiction, q.lga)
        if key in places:
            problems.append(f"{where}: family '{q.family}' already has {places[key]} for this place")
        places[key] = q.id
        if q.lga:
            lgas = lga_names()
            if lgas and q.lga not in lgas:
                problems.append(f"{where}: '{q.lga}' is not an ABS LGA code (ASGS 2021)")
            if LGA_STATE.get(q.lga[0]) != q.jurisdiction:
                problems.append(f"{where}: LGA {q.lga} is not in {q.jurisdiction}")
        if q.regime and q.regime not in regimes:
            problems.append(f"{where}: unknown regime '{q.regime}'")
        problems += [f"{where}: unknown body '{b}'" for b in q.administered_by if b not in bodies]
        problems += [f"{where}: unknown register record '{r}'" for r in q.records if r not in records]
        for law in q.laws:
            if q.tier != "cth" and law.jurisdiction not in (q.jurisdiction, "CTH") and not law.applied:
                problems.append(f"{where}: law '{law.title}' is from {law.jurisdiction}, not {q.jurisdiction}")
        for i, r in enumerate(q.reach):
            for c in (*r.classes, *r.exclude):
                problems += [f"{where}: reach {i}: {p}" for p in anzsic.check(c)]
            if r.activities:
                listed = set().union(*(acts.get(c, frozenset()) for c in r.classes))
                if not acts:
                    problems.append(f"{where}: reach {i}: ABS primary activities not built (fetch_anzsic_activities)")
                problems += [
                    f"{where}: reach {i}: '{a}' is not an ABS primary activity of {', '.join(r.classes)}"
                    for a in r.activities
                    if acts and a not in listed
                ]
            if r.scope == "listed" and not reach_classes(r):
                problems.append(f"{where}: reach {i} covers no class")
    return problems


LINK_FIELDS = (
    "class",
    "jurisdiction",
    "tier",
    "lga",
    "requirement",
    "family",
    "regime",
    "kind",
    "title",
    "triggers",
    "activities",
    "condition",
    "legal_forms",
    "applies_in",
    "laws",
    "confidence",
    "review",
)


def links(reqs: list[Requirement]) -> list[dict]:
    """One row per class and requirement (a requirement reaching a class twice keeps each reach)."""
    rows = []
    for q in reqs:
        for r in q.reach:
            for c in reach_classes(r):
                rows.append(
                    {
                        "class": c,
                        "jurisdiction": q.jurisdiction,
                        "tier": q.tier,
                        "lga": q.lga or "",
                        "requirement": q.id,
                        "family": q.family,
                        "regime": q.regime or "",
                        "kind": q.kind,
                        "title": q.title,
                        "triggers": " | ".join(t.type for t in q.triggers),
                        "activities": " | ".join(r.activities),
                        "condition": r.condition or "",
                        "legal_forms": " | ".join(r.legal_forms),
                        "applies_in": " | ".join(r.in_states)
                        if r.in_states
                        else ("all" if q.jurisdiction == "CTH" else q.jurisdiction),
                        "laws": " | ".join(f"{law.title} ({law.register_id or law.register_url})" for law in q.laws),
                        "confidence": q.confidence,
                        "review": q.review.status,
                    }
                )
    return rows


def json_schema() -> dict:
    schema = Requirement.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Requirement: what a law asks of a business, and the ANZSIC classes it reaches"
    return schema


__all__ = [
    "JURISDICTIONS",
    "Law",
    "Reach",
    "Requirement",
    "Source",
    "Trigger",
    "check_requirements",
    "links",
    "load_requirements",
    "reach_classes",
    "write_requirement",
]


# --- Gaps (methods rule 12) -------------------------------------------------------------------------------------

GapStatus = Literal["not-found", "to-draft", "not-applicable", "blocked", "not-searched"]


class RequirementGap(_Strict):
    """A family with no requirement recorded in a state or territory, and what was searched (methods rule 12).

    ``not-found``: the sources searched show no such requirement there. ``to-draft``: the law is identified but the
    requirement is not yet drafted. ``not-applicable``: a source shows the family cannot apply there. ``blocked``: the
    sources could not be read (e.g. a register or regulator refusing automated requests). ``not-searched``: not yet
    looked for, with the reason. A gap says what was searched, not that no law exists, unless its sources say so."""

    family: str = Field(min_length=1)
    jurisdiction: Literal["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"]
    status: GapStatus
    searched: str = Field(min_length=10, description="What was searched, and where")
    law: str | None = Field(default=None, description="For 'to-draft': the law identified")
    note: str | None = None
    checked_on: dt.date
    sources: tuple[Source, ...] = ()

    @model_validator(mode="after")
    def _status(self) -> RequirementGap:
        if self.status == "to-draft" and not self.law:
            raise ValueError("a 'to-draft' gap names the law identified (law)")
        if self.status == "not-applicable" and not self.sources:
            raise ValueError("a 'not-applicable' gap needs a source saying why")
        return self


def default_gaps_path() -> Path:
    return default_register_dir() / "requirement-gaps.json"


def load_requirement_gaps(path: Path | None = None) -> tuple[list[RequirementGap], list[str]]:
    path = path or default_gaps_path()
    if not path.exists():
        return [], []
    gaps, problems = [], []
    for i, g in enumerate(json.loads(path.read_text("utf-8"))["gaps"]):
        try:
            gaps.append(RequirementGap.model_validate(g))
        except ValueError as exc:
            problems.append(f"requirement-gaps.json: gap {i + 1}: {exc}")
    return gaps, problems


def check_requirement_gaps(reqs: list[Requirement], gaps: list[RequirementGap]) -> list[str]:
    """Every state family is recorded, or logged as a gap, in each of the eight states and territories."""
    problems: list[str] = []
    have: dict[str, set[str]] = {}
    for q in reqs:
        if q.tier in ("state", "local"):
            have.setdefault(q.family, set()).add(q.jurisdiction)
    state_families = {q.family for q in reqs if q.tier == "state"}
    logged: set[tuple[str, str]] = set()
    for g in gaps:
        key = (g.family, g.jurisdiction)
        if g.family not in have:
            problems.append(f"requirement-gaps.json: unknown state or council family '{g.family}'")
        elif g.jurisdiction in have[g.family]:
            problems.append(f"requirement-gaps.json: {g.family} is recorded in {g.jurisdiction}; remove the gap")
        if key in logged:
            problems.append(f"requirement-gaps.json: {g.family} in {g.jurisdiction} is logged twice")
        logged.add(key)
    for fam in sorted(state_families):
        for st in JURISDICTIONS[1:]:
            if st not in have[fam] and (fam, st) not in logged:
                problems.append(f"requirement-gaps.json: {fam} has no requirement and no gap logged in {st}")
    return problems
