"""Regulatory regimes and the industries they reach: who in government does what, and how consistent it is.

A regime is a body of regulation a business deals with as one task, such as food safety, liquor licensing or work
health and safety (``regulation-register/regimes/``, one JSON file each). Each names the ANZSIC 2006 industries it
applies to, its layers (which tier of government sets the rules, licenses, approves, inspects or collects, and
through whom), and how consistent it is across states and territories. Mapped onto every ANZSIC class, the regimes
give an industry-level view of how many government parties a business must deal with, where tiers do the same job,
and where the rules differ between states (``industry_profiles``). Phase 2 adds ``issues``: evidenced duplication,
inconsistency, unclear guidance or complexity. Owner request, 29 October 2026 (DECISIONS E-96).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .. import anzsic
from .catalogue import default_register_dir
from .recommendations import Evidence
from .schema import AnzsicCode, ChangeRecord, Jurisdiction, RecordId, Review, _Strict

Tier = Literal["cth", "state", "local"]
TIER_LABELS: dict[str, str] = {"cth": "Commonwealth", "state": "State or territory", "local": "Local council"}
Function = Literal["sets-rules", "licenses", "approves", "inspects", "collects", "funds"]
FUNCTION_LABELS: dict[str, str] = {
    "sets-rules": "Sets the rules or standards",
    "licenses": "Licenses, registers or accredits",
    "approves": "Approves projects, premises or products",
    "inspects": "Inspects and enforces",
    "collects": "Collects tax, levies or fees",
    "funds": "Funds services and sets conditions",
}
# Functions a business deals with directly (a 'touchpoint'); setting the rules is not one.
BUSINESS_FACING: tuple[str, ...] = ("licenses", "approves", "inspects", "collects", "funds")
Consistency = Literal["national", "harmonised", "recognised", "varies", "cth"]
CONSISTENCY_LABELS: dict[str, str] = {
    "national": "One national law or regulator",
    "harmonised": "Model law or national code, adopted state by state with variations",
    "recognised": "State laws differ, but registrations are recognised across states",
    "varies": "Each state and territory has its own law",
    "cth": "Commonwealth only",
}
# Regimes whose rules differ between states, in whole or in part.
VARYING: tuple[str, ...] = ("harmonised", "recognised", "varies")
Scope = Literal["cross-cutting", "sector"]

IssueTag = Literal[
    "duplicative", "inconsistent", "unclear-guidance", "multi-agency", "cth-state-overlap", "local-variation", "complex"
]
ISSUE_LABELS: dict[str, str] = {
    "duplicative": "Duplicative",
    "inconsistent": "Inconsistent across states",
    "unclear-guidance": "Vague or inconsistent guidance",
    "multi-agency": "Many agencies for one activity",
    "cth-state-overlap": "Commonwealth and state overlap",
    "local-variation": "Varies council by council",
    "complex": "Complex or changing rules",
}
ISSUE_HELP: dict[str, str] = {
    "duplicative": "Two or more agencies regulate the same risk, or ask the business for the same information.",
    "inconsistent": "The rules, licences or definitions differ between states and territories, so a business "
    "operating in several must comply with several regimes.",
    "unclear-guidance": "Regulator guidance is vague, or regulators and inspectors interpret the same rule "
    "differently.",
    "multi-agency": "One business activity needs separate approvals from several agencies or tiers, with no "
    "single point of contact.",
    "cth-state-overlap": "Commonwealth and state laws cover the same ground, overlap or conflict.",
    "local-variation": "Councils apply different requirements to the same activity.",
    "complex": "The rules are voluminous, prescriptive or change often, making compliance hard even when each "
    "rule is light.",
}


class Layer(_Strict):
    """One tier of government's role in the regime."""

    tier: Tier
    function: Function
    who: str = Field(min_length=1, description="Plain English: which body, e.g. 'State food authority'")
    bodies: tuple[RecordId, ...] = Field(default=(), description="Examples from bodies.json")
    jurisdictions: tuple[Jurisdiction, ...] = Field(default=(), description="Where it applies; empty means all")


class Coverage(_Strict):
    """The ANZSIC 2006 codes (division, subdivision, group or class) the regime applies to."""

    anzsic: tuple[AnzsicCode, ...] = Field(min_length=1)
    exclude: tuple[AnzsicCode, ...] = ()
    note: str | None = None


class Issue(_Strict):
    """Evidence of duplication, inconsistency, unclear guidance or complexity in the regime (Phase 2)."""

    tag: IssueTag
    what: str = Field(min_length=1, description="Plain English: what the problem is, from the industry's view")
    jurisdictions: tuple[Jurisdiction, ...] = Field(default=(), description="Where it applies; empty means all")
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    status: Literal["current", "partly-addressed", "addressed"] = "current"
    status_note: str | None = None


class Regime(_Strict):
    id: RecordId
    name: str = Field(min_length=1, max_length=80)
    what: str = Field(min_length=1, description="Plain English: what it requires of a business")
    scope: Scope
    coverage: Coverage
    layers: tuple[Layer, ...] = Field(min_length=1)
    consistency: Consistency
    consistency_note: str | None = None
    basis: tuple[Evidence, ...] = Field(min_length=1, description="Sources for the description, quoted")
    records: tuple[RecordId, ...] = Field(default=(), description="Register items about this regime")
    issues: tuple[Issue, ...] = ()
    review: Review = Review()

    @model_validator(mode="after")
    def _distinct(self) -> Regime:
        keys = [(x.tier, x.function, x.who) for x in self.layers]
        if len(set(keys)) != len(keys):
            raise ValueError("layers repeat the same tier, function and body")
        return self

    def overlap(self) -> dict[str, list[str]]:
        """Functions performed by more than one tier: the structural duplication the Venn diagram shows."""
        tiers: dict[str, set[str]] = {}
        for x in self.layers:
            tiers.setdefault(x.function, set()).add(x.tier)
        return {f: sorted(t, key=list(TIER_LABELS).index) for f, t in tiers.items() if len(t) > 1}

    @property
    def tiers(self) -> list[str]:
        return [t for t in TIER_LABELS if any(x.tier == t for x in self.layers)]

    @property
    def touchpoints(self) -> int:
        """Distinct (tier, body) parties the business deals with directly."""
        return len({(x.tier, x.who) for x in self.layers if x.function in BUSINESS_FACING})


def default_regimes_dir() -> Path:
    return default_register_dir() / "regimes"


@dataclass
class RegimesResult:
    regimes: list[Regime] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def load_regimes(path: Path | None = None) -> RegimesResult:
    path = path or default_regimes_dir()
    result = RegimesResult()
    for file in sorted(path.glob("*.json")) if path.exists() else []:
        try:
            reg = Regime.model_validate(json.loads(file.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, ValueError) as exc:
            result.problems.append(f"regimes/{file.name}: {exc}")
            continue
        if reg.id != file.stem:
            result.problems.append(f"regimes/{file.name}: id '{reg.id}' does not match the file name")
        result.regimes.append(reg)
    return result


def write_regime(reg: Regime, path: Path | None = None) -> Path:
    path = path or default_regimes_dir()
    path.mkdir(parents=True, exist_ok=True)
    out = path / f"{reg.id}.json"
    out.write_text(json.dumps(reg.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


@cache
def _classes() -> tuple[str, ...]:
    return tuple(sorted(c for c in anzsic._codes() if len(c) == 4))


def _under(cls: str, code: str) -> bool:
    """Whether a class sits under (or is) an ANZSIC code at any level."""
    if len(code) == 1:
        return anzsic.division(cls) == code
    return cls.startswith(code)


def classes_for(reg: Regime) -> list[str]:
    """The ANZSIC classes a regime applies to."""
    return [
        c
        for c in _classes()
        if any(_under(c, a) for a in reg.coverage.anzsic) and not any(_under(c, x) for x in reg.coverage.exclude)
    ]


def regimes_by_class(regimes: list[Regime]) -> dict[str, list[Regime]]:
    out: dict[str, list[Regime]] = {c: [] for c in _classes()}
    for reg in regimes:
        for c in classes_for(reg):
            out[c].append(reg)
    return out


def class_profile(cls: str, regs: list[Regime]) -> dict:
    """Phase 1 indicators for one ANZSIC class (and Phase 2 issue counts, once regimes carry issues)."""
    issues = [i for r in regs for i in r.issues if i.status != "addressed"]
    sector = [r for r in regs if r.scope == "sector"]
    return {
        "anzsic": cls,
        "name": anzsic.name(cls),
        "division": anzsic.division(cls),
        "regimes": len(regs),
        "sector_regimes": len(sector),
        "touchpoints": sum(r.touchpoints for r in regs),
        "sector_touchpoints": sum(r.touchpoints for r in sector),
        "tiers": len({t for r in regs for t in r.tiers}),
        "overlapping_regimes": sum(bool(r.overlap()) for r in regs),
        "sector_overlapping": sum(bool(r.overlap()) for r in sector),
        "varying_regimes": sum(r.consistency in VARYING for r in regs),
        "sector_varying": sum(r.consistency in VARYING for r in sector),
        "issues": len(issues),
        **{f"issue_{t.replace('-', '_')}": sum(i.tag == t for i in issues) for t in ISSUE_LABELS},
        "regime_ids": " ".join(r.id for r in regs),
    }


def industry_profiles(regimes: list[Regime]) -> list[dict]:
    return [class_profile(c, regs) for c, regs in regimes_by_class(regimes).items()]


def check_regimes(regimes: list[Regime], records: list[ChangeRecord], bodies: dict) -> list[str]:
    """Codes, bodies and record links exist; ids are unique; every ANZSIC class is reached by some regime."""
    ids = {r.id for r in records}
    problems = []
    seen: set[str] = set()
    for reg in regimes:
        if reg.id in seen:
            problems.append(f"regimes/{reg.id}.json: duplicate id")
        seen.add(reg.id)
        for code in (*reg.coverage.anzsic, *reg.coverage.exclude):
            problems += [f"regimes/{reg.id}.json: {p}" for p in anzsic.check(code)]
        problems += [f"regimes/{reg.id}.json: unknown record '{x}'" for x in reg.records if x not in ids]
        problems += [
            f"regimes/{reg.id}.json: unknown body '{b}'" for x in reg.layers for b in x.bodies if b not in bodies
        ]
        if not classes_for(reg):
            problems.append(f"regimes/{reg.id}.json: reaches no ANZSIC class")
    if regimes:
        empty = [c for c, regs in regimes_by_class(regimes).items() if not regs]
        problems += [f"regimes: ANZSIC class {c} is reached by no regime" for c in empty]
    return problems


def regimes_by_record(regimes: list[Regime]) -> dict[str, list[Regime]]:
    out: dict[str, list[Regime]] = {}
    for reg in regimes:
        for rid in reg.records:
            out.setdefault(rid, []).append(reg)
    return out


def json_schema() -> dict:
    schema = Regime.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Regulatory regime"
    return schema


__all__ = [
    "CONSISTENCY_LABELS",
    "FUNCTION_LABELS",
    "ISSUE_HELP",
    "ISSUE_LABELS",
    "TIER_LABELS",
    "Issue",
    "Layer",
    "Regime",
    "check_regimes",
    "class_profile",
    "classes_for",
    "industry_profiles",
    "load_regimes",
    "regimes_by_class",
    "regimes_by_record",
    "write_regime",
]
