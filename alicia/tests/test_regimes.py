"""Regulatory regimes: who in government does what for each industry, and where tiers and states diverge.

Regimes built here are ILLUSTRATIVE test fixtures, except where a test loads the committed register.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from alicia.register.bodies import load_bodies
from alicia.register.catalogue import default_register_dir, load_records
from alicia.register.regimes import (
    ISSUE_LABELS,
    Regime,
    check_regimes,
    class_profile,
    classes_for,
    industry_profiles,
    json_schema,
    load_regimes,
    regimes_by_record,
    write_regime,
)

SRC = "https://example.org/illustrative-source"
EVIDENCE = {
    "source": "Illustrative report",
    "publisher": "Illustrative publisher",
    "year": 2025,
    "url": SRC,
    "locator": "Chapter 1",
    "quote": "Businesses deal with several illustrative agencies.",
    "origin": "australian",
}


def regime(**over) -> dict:
    reg = {
        "id": "illustrative-regime",
        "name": "Illustrative regime",
        "what": "Hold an illustrative licence.",
        "scope": "sector",
        "coverage": {"anzsic": ["45"], "exclude": ["4520"]},
        "layers": [
            {"tier": "cth", "function": "sets-rules", "who": "Commonwealth standards body"},
            {"tier": "state", "function": "licenses", "who": "State regulator"},
            {"tier": "state", "function": "inspects", "who": "State regulator"},
            {"tier": "local", "function": "inspects", "who": "Local council"},
        ],
        "consistency": "harmonised",
        "basis": [EVIDENCE],
    }
    reg.update(over)
    return reg


def test_coverage_reaches_classes_at_any_level_less_exclusions():
    reg = Regime.model_validate(regime())
    assert classes_for(reg) == ["4511", "4512", "4513", "4530"]
    division = Regime.model_validate(regime(coverage={"anzsic": ["H"], "exclude": ["44"]}))
    assert "4400" not in classes_for(division) and "4520" in classes_for(division)
    assert classes_for(Regime.model_validate(regime(coverage={"anzsic": ["4520"]}))) == ["4520"]


def test_overlap_tiers_and_touchpoints():
    reg = Regime.model_validate(regime())
    # State and council both inspect: the overlap the Venn diagram shows. Setting rules is not a touchpoint.
    assert reg.overlap() == {"inspects": ["state", "local"]}
    assert reg.tiers == ["cth", "state", "local"]
    assert reg.touchpoints == 2
    with pytest.raises(ValidationError, match="layers repeat"):
        Regime.model_validate(regime(layers=[regime()["layers"][1]] * 2))
    with pytest.raises(ValidationError):
        Regime.model_validate(regime(basis=[]))


def test_a_class_profile_counts_regimes_parties_overlaps_variation_and_live_issues():
    issue = {"tag": "duplicative", "what": "Two inspectors check the same thing.", "evidence": [EVIDENCE]}
    done = {**issue, "tag": "complex", "status": "addressed"}
    reg = Regime.model_validate(regime(issues=[issue, done]))
    cross = Regime.model_validate(
        regime(
            id="illustrative-cross",
            scope="cross-cutting",
            coverage={"anzsic": ["H"]},
            layers=[{"tier": "cth", "function": "collects", "who": "Commonwealth tax office"}],
            consistency="national",
        )
    )
    p = class_profile("4511", [reg, cross])
    assert (p["regimes"], p["sector_regimes"]) == (2, 1)
    assert (p["touchpoints"], p["sector_touchpoints"]) == (3, 2)
    assert (p["overlapping_regimes"], p["varying_regimes"], p["tiers"]) == (1, 1, 3)
    # Addressed issues are not counted.
    assert p["issues"] == 1 and p["issue_duplicative"] == 1 and p["issue_complex"] == 0
    assert {f"issue_{t.replace('-', '_')}" for t in ISSUE_LABELS} <= set(p)
    profiles = {q["anzsic"]: q for q in industry_profiles([reg, cross])}
    assert len(profiles) == 506 and profiles["4520"]["regimes"] == 1 and profiles["0111"]["regimes"] == 0


def test_the_loader_and_checks_report_problems(tmp_path):
    write_regime(Regime.model_validate(regime()), tmp_path)
    (tmp_path / "wrong-name.json").write_text(json.dumps(regime()), encoding="utf-8")
    (tmp_path / "broken.json").write_text("{", encoding="utf-8")
    result = load_regimes(tmp_path)
    assert len(result.regimes) == 2
    assert any("does not match the file name" in p for p in result.problems)
    assert any("broken.json" in p for p in result.problems)

    bad = Regime.model_validate(
        regime(
            coverage={"anzsic": ["9999"]},
            layers=[{"tier": "state", "function": "licenses", "who": "Nobody", "bodies": ["nsw-nobody"]}],
            records=["nsw-missing-2016"],
        )
    )
    problems = check_regimes([bad, bad], [], {})
    assert any("duplicate id" in p for p in problems)
    assert any("9999" in p for p in problems)
    assert any("unknown record 'nsw-missing-2016'" in p for p in problems)
    assert any("unknown body 'nsw-nobody'" in p for p in problems)
    assert any("reaches no ANZSIC class" in p for p in problems)
    assert any("class 0111 is reached by no regime" in p for p in problems)


def test_the_committed_regimes_validate_and_reach_every_class():
    result = load_regimes()
    assert result.problems == [] and len(result.regimes) >= 50
    assert check_regimes(result.regimes, load_records().records, load_bodies()[0]) == []
    assert all(e.quote for r in result.regimes for e in r.basis)
    by_id = {r.id: r for r in result.regimes}
    # Pubs face liquor licensing, food safety and gambling regulation, among others.
    pubs = {q["anzsic"]: q for q in industry_profiles(result.regimes)}["4520"]["regime_ids"].split()
    assert {"liquor-licensing", "food-safety", "gambling"} <= set(pubs)
    assert "liquor-licensing" in {r.id for r in regimes_by_record(result.regimes)["nsw-lockout-2014"]}
    assert by_id["payroll-tax"].scope == "cross-cutting"


def test_the_exported_regime_schema_is_up_to_date():
    path = default_register_dir() / "schema" / "regime.schema.json"
    assert json.loads(path.read_text("utf-8")) == json.loads(json.dumps(json_schema())), (
        "regenerate with: uv run python scripts/export_schema.py"
    )
