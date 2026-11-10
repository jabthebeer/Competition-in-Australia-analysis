"""Requirements (legislation-links plan, phase B): the model's rules, loading, checks and the class link table."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from alicia.register.requirements import (
    Requirement,
    check_requirements,
    links,
    load_requirements,
    primary_activities,
    reach_classes,
    write_requirement,
)

SOURCE = {
    "title": "Example Act 2000",
    "publisher": "Federal Register of Legislation",
    "url": "https://www.legislation.gov.au/C2004A00001/latest/text",
    "locator": "s 10",
    "quote": "A person must not carry on a business without registering.",
    "accessed": "2026-11-06",
    "checked": "register-text",
}


def req(**over) -> dict:
    base = {
        "id": "cth-example-registration",
        "family": "example-registration",
        "jurisdiction": "CTH",
        "tier": "cth",
        "title": "Register the business",
        "kind": "registration",
        "what": "Register before trading.",
        "laws": [{"title": "Example Act 2000", "jurisdiction": "CTH", "kind": "act", "register_id": "C2004A00001"}],
        "sources": [SOURCE],
        "triggers": [{"type": "entry"}],
        "reach": [{"scope": "all", "sources": [SOURCE]}],
        "confidence": "high",
        "assessment": {
            "summary": "No material effect.",
            "reach": "economy-wide",
            "confidence": "low",
            "assessed_on": "2026-11-07",
        },
        "drafted_on": "2026-11-06",
    }
    return base | over


def test_a_valid_requirement_loads_and_reaches_every_class():
    q = Requirement.model_validate(req())
    assert len(reach_classes(q.reach[0])) == 506
    rows = links([q])
    assert len(rows) == 506 and {r["tier"] for r in rows} == {"cth"}


def test_exclusions_and_coarser_codes_expand_to_classes():
    q = Requirement.model_validate(
        req(reach=[{"scope": "listed", "classes": ["45"], "exclude": ["4513"], "sources": [SOURCE]}])
    )
    assert reach_classes(q.reach[0]) == ["4511", "4512", "4520", "4530"]


def test_thresholds_need_a_value_unit_date_and_source():
    with pytest.raises(ValidationError, match="needs a test, value, unit and as_at"):
        Requirement.model_validate(req(triggers=[{"type": "turnover"}]))
    with pytest.raises(ValidationError, match="needs an official source"):
        Requirement.model_validate(
            req(triggers=[{"type": "turnover", "test": ">=", "value": 75000, "unit": "AUD", "as_at": "2026-11-06"}])
        )
    with pytest.raises(ValidationError, match="has no threshold value"):
        Requirement.model_validate(req(triggers=[{"type": "entry", "value": 1}]))


def test_laws_must_be_traceable_and_corpus_quotes_name_their_copy():
    law = {"title": "Example Act 2000", "jurisdiction": "CTH", "kind": "act"}
    with pytest.raises(ValidationError, match="register ID or an official register link"):
        Requirement.model_validate(req(laws=[law]))
    with pytest.raises(ValidationError, match="corpus_version_id"):
        Requirement.model_validate(req(sources=[SOURCE | {"checked": "corpus-copy"}]))


def test_tier_follows_the_jurisdiction_and_council():
    with pytest.raises(ValidationError, match="tier should be 'state'"):
        Requirement.model_validate(req(jurisdiction="NSW"))
    q = Requirement.model_validate(
        req(id="lga-example", jurisdiction="VIC", tier="local", lga="24600", lga_name="Melbourne (C)")
    )
    assert q.tier == "local"


def test_activities_must_be_the_abs_wording_for_their_class(tmp_path):
    if not primary_activities():
        pytest.skip("ABS primary activities not built")
    good = req(
        reach=[
            {"scope": "listed", "classes": ["4271"], "activities": ["Pharmacy, retail, operation"], "sources": [SOURCE]}
        ]
    )
    bad = req(id="cth-other", family="other", reach=[good["reach"][0] | {"activities": ["Running a pharmacy"]}])
    reqs = [Requirement.model_validate(good), Requirement.model_validate(bad)]
    problems = check_requirements(reqs, bodies={}, regimes=set(), records=set())
    assert len(problems) == 1 and "'Running a pharmacy' is not an ABS primary activity of 4271" in problems[0]


def test_files_live_in_their_jurisdictions_folder(tmp_path):
    q = Requirement.model_validate(req())
    out = write_requirement(q, tmp_path)
    assert out == tmp_path / "cth" / "cth-example-registration.json"
    moved = tmp_path / "nsw" / out.name
    moved.parent.mkdir()
    out.rename(moved)
    result = load_requirements(tmp_path)
    assert result.problems == ["requirements/nsw/cth-example-registration.json: belongs in requirements/cth/"]
    assert json.loads(moved.read_text())["id"] == q.id


def test_a_family_has_one_requirement_per_place():
    a = Requirement.model_validate(req())
    b = Requirement.model_validate(req(id="cth-example-registration-2"))
    problems = check_requirements([a, b], bodies={}, regimes=set(), records=set())
    assert any("family 'example-registration' already has" in p for p in problems)


def test_council_codes_are_abs_lgas_in_the_right_state():
    ok = Requirement.model_validate(
        req(id="lga-example", jurisdiction="VIC", tier="local", lga="24600", lga_name="Melbourne")
    )
    wrong_state = Requirement.model_validate(
        req(id="lga-example-2", family="other", jurisdiction="NSW", tier="local", lga="24600", lga_name="Melbourne")
    )
    problems = check_requirements([ok, wrong_state], bodies={}, regimes=set(), records=set())
    assert problems == ["requirements/local/24600/lga-example-2.json: LGA 24600 is not in NSW"]


def test_a_commonwealth_reach_can_skip_a_state():
    q = Requirement.model_validate(
        req(
            reach=[
                {"scope": "all", "legal_forms": ["sole-proprietor"], "in_states": ["NSW", "VIC"], "sources": [SOURCE]}
            ]
        )
    )
    row = links([q])[0]
    assert row["applies_in"] == "NSW | VIC" and row["legal_forms"] == "sole-proprietor"
    with pytest.raises(ValidationError, match="only a Commonwealth requirement"):
        Requirement.model_validate(req(jurisdiction="NSW", tier="state", reach=q.model_dump()["reach"]))


def test_a_quantity_threshold_needs_its_unit_and_source():
    trig = {
        "type": "quantity",
        "test": ">=",
        "value": 1000,
        "unit": "square metres of office space",
        "as_at": "2026-11-06",
    }
    with pytest.raises(ValidationError, match="needs an official source"):
        Requirement.model_validate(req(triggers=[trig]))
    assert (
        Requirement.model_validate(req(triggers=[trig | {"sources": [SOURCE]}])).triggers[0].unit.startswith("square")
    )


def test_a_state_can_cite_a_national_law_hosted_by_another_state_only_when_applied():
    qld = {
        "title": "Health Practitioner Regulation National Law",
        "jurisdiction": "QLD",
        "kind": "act",
        "register_id": "act-2009-045",
    }
    base = req(id="sa-example", jurisdiction="SA", tier="state")
    wrong = Requirement.model_validate(base | {"laws": [qld]})
    right = Requirement.model_validate(
        base | {"id": "sa-example-2", "family": "other", "laws": [qld | {"applied": True}]}
    )
    problems = check_requirements([wrong, right], bodies={}, regimes=set(), records=set())
    assert len(problems) == 1 and "is from QLD, not SA" in problems[0]


def test_every_requirement_is_marked_against_the_productivity_framework():
    marked = req(
        assessment={
            "summary": "A licence before trading.",
            "marks": [{"driver": "entry-exit", "mark": -1, "reason": "A licence is needed before trading."}],
            "main_driver": "entry-exit",
            "reach": "narrow",
            "confidence": "low",
            "assessed_on": "2026-11-07",
        }
    )
    assert Requirement.model_validate(marked).assessment.total == -1
    with pytest.raises(ValidationError, match="assessment"):
        Requirement.model_validate({k: v for k, v in req().items() if k != "assessment"})
    with pytest.raises(ValidationError, match="no marks has no main driver"):
        Requirement.model_validate(req(assessment=req()["assessment"] | {"main_driver": "burden"}))
    with pytest.raises(ValidationError, match="largest mark"):
        Requirement.model_validate(marked | {"assessment": marked["assessment"] | {"main_driver": "burden"}})


def test_every_state_family_is_recorded_or_its_gap_logged_with_what_was_searched():
    from alicia.register.requirements import (
        RequirementGap,
        check_requirement_gaps,
        load_requirement_gaps,
        load_requirements,
    )

    reqs = load_requirements().requirements
    gaps, problems = load_requirement_gaps()
    assert not problems and gaps and not check_requirement_gaps(reqs, gaps)
    assert all(g.searched for g in gaps)
    assert all(g.law for g in gaps if g.status == "to-draft")
    dropped = [g for g in gaps if not (g.family == "home-warranty-insurance" and g.jurisdiction == "TAS")]
    assert check_requirement_gaps(reqs, dropped) == [
        "requirement-gaps.json: home-warranty-insurance has no requirement and no gap logged in TAS"
    ]
    nsw = RequirementGap.model_validate(
        {
            "family": "food-business-registration",
            "jurisdiction": "NSW",
            "status": "not-found",
            "searched": "a search that should not be needed",
            "checked_on": "2026-11-10",
        }
    )
    assert "remove the gap" in check_requirement_gaps(reqs, gaps + [nsw])[0]
    with pytest.raises(ValueError, match="names the law"):
        RequirementGap.model_validate(
            {
                "family": "x",
                "jurisdiction": "NSW",
                "status": "to-draft",
                "searched": "searched somewhere",
                "checked_on": "2026-11-10",
            }
        )
