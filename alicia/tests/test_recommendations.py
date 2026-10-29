"""Recommendations: what government could do about register items, each with quoted sources.

Recommendations and records built here are ILLUSTRATIVE test fixtures, except where a test loads the committed register.
"""

from __future__ import annotations

import json
import re

import pytest
from pydantic import ValidationError

from alicia.menu import growth
from alicia.menu.explorer import build_payload
from alicia.register.bodies import load_bodies
from alicia.register.catalogue import default_register_dir, load_records
from alicia.register.recommendations import (
    Recommendation,
    actors_of,
    by_record,
    check_coverage,
    check_recommendations,
    gap_for,
    json_schema,
    load_gaps,
    load_recommendations,
    write_recommendation,
)
from alicia.register.schema import ChangeRecord

SRC = "https://example.org/illustrative-source"


def record(rid="nsw-illustrative-2016", family=None) -> ChangeRecord:
    return ChangeRecord.model_validate(
        {
            "id": rid,
            "family": family,
            "title": "ILLUSTRATIVE change (test fixture)",
            "jurisdiction": "NSW",
            "summary": "Illustrative record used only in tests.",
            "instruments": [{"title": "Illustrative Act 2016", "role": "principal"}],
            "dates": {"commenced": [{"date": "2016-11-01", "what": "Whole Act", "source": SRC}]},
            "direction": "enhancing",
            "direction_rationale": "Illustrative.",
            "channels": ["barriers"],
            "industries": [{"anzsic": "4623", "name": "Taxi and Other Road Transport", "exposure": "direct"}],
            "verified": {"dates": True},
            "responsible": [{"body": "nsw-dept", "role": "administers", "source": SRC}],
        }
    )


def recommendation(**over) -> dict:
    rec = {
        "id": "illustrative-recommendation",
        "title": "Do the illustrative thing",
        "action": "An illustrative action.",
        "why": "An illustrative reason.",
        "kind": "reform",
        "applies_to": ["nsw-illustrative-2016"],
        "drivers": ["entry-exit"],
        "evidence": [
            {
                "source": "Illustrative report",
                "publisher": "Illustrative publisher",
                "year": 2025,
                "url": SRC,
                "locator": "Recommendation 1",
                "quote": "Governments should do the illustrative thing.",
                "origin": "australian",
            }
        ],
        "confidence": "medium",
        "drafted_on": "2026-10-29",
    }
    rec.update(over)
    return rec


def test_a_recommendation_needs_evidence_and_sourced_precedents_and_progress():
    assert Recommendation.model_validate(recommendation()).evidence[0].checked == "full-text"
    with pytest.raises(ValidationError):
        Recommendation.model_validate(recommendation(evidence=[]))
    with pytest.raises(ValidationError, match="precedent needs a source"):
        Recommendation.model_validate(recommendation(precedents=[{"where": "Somewhere", "what": "Did it"}]))
    with pytest.raises(ValidationError, match="progress needs a source"):
        Recommendation.model_validate(recommendation(progress={"what": "Under way"}))
    with pytest.raises(ValidationError, match="applies_to has duplicates"):
        Recommendation.model_validate(recommendation(applies_to=["nsw-illustrative-2016"] * 2))
    with pytest.raises(ValidationError):
        short = recommendation()
        short["evidence"][0]["quote"] = "Too short"
        Recommendation.model_validate(short)


def test_the_loader_reports_problems_rather_than_stopping(tmp_path):
    write_recommendation(Recommendation.model_validate(recommendation()), tmp_path)
    (tmp_path / "wrong-name.json").write_text(json.dumps(recommendation()), encoding="utf-8")
    (tmp_path / "broken.json").write_text("{", encoding="utf-8")
    result = load_recommendations(tmp_path)
    assert len(result.recommendations) == 2
    assert any("does not match the file name" in p for p in result.problems)
    assert any("broken.json" in p for p in result.problems)


def test_checks_name_unknown_records_bodies_and_uncovered_items():
    rec = Recommendation.model_validate(recommendation())
    bodies = {"nsw-dept": object()}
    assert check_recommendations([rec], [record()], bodies) == []
    bad = Recommendation.model_validate(recommendation(applies_to=["nsw-missing-2016"], actors=["nsw-nobody"]))
    problems = check_recommendations([bad], [record()], bodies)
    assert any("unknown record 'nsw-missing-2016'" in p for p in problems)
    assert any("unknown body 'nsw-nobody'" in p for p in problems)
    other = record("nsw-other-2017", family="illustrative-family")
    assert check_coverage([rec], [record(), other], {}) == [
        "nsw-other-2017.json: no recommendation and no reason in recommendation-gaps.json"
    ]
    assert check_coverage([rec], [record(), other], {"illustrative-family": "No source found."}) == []
    assert gap_for(other, {"illustrative-family": "No source found."}) == "No source found."
    assert "unknown family or record 'nope'" in check_coverage([rec], [record()], {"nope": "x"})[0]


def test_actors_default_to_the_bodies_that_administer_the_items():
    rec = Recommendation.model_validate(recommendation())
    assert actors_of(rec, {"nsw-illustrative-2016": record()}) == ["nsw-dept"]
    named = Recommendation.model_validate(recommendation(actors=["cth-treasury"]))
    assert actors_of(named, {"nsw-illustrative-2016": record()}) == ["cth-treasury"]


def test_the_committed_recommendations_validate_and_cover_the_register():
    records = load_records().records
    result = load_recommendations()
    assert result.problems == [] and len(result.recommendations) >= 50
    bodies = load_bodies()[0]
    assert check_recommendations(result.recommendations, records, bodies) == []
    assert check_coverage(result.recommendations, records, load_gaps()) == []
    # Every recommendation quotes at least one source, and the owner's examples are covered.
    assert all(e.quote for r in result.recommendations for e in r.evidence)
    covered = by_record(result.recommendations)
    assert "nsw-residential-transfer-duty" in covered and "cth-pharmacy-location-rules" in covered
    assert any(e.origin == "international" for r in result.recommendations for e in r.evidence)


def test_the_exported_recommendation_schema_is_up_to_date():
    path = default_register_dir() / "schema" / "recommendation.schema.json"
    assert json.loads(path.read_text("utf-8")) == json.loads(json.dumps(json_schema())), (
        "regenerate with: uv run python scripts/export_schema.py"
    )


def test_the_menu_shows_recommendations_and_gaps():
    rec = Recommendation.model_validate(recommendation())
    other = record("nsw-other-2017", family="illustrative-family")
    bodies = load_bodies()[0]
    data = build_payload(
        [record(), other], bodies=bodies, recommendations=[rec], gaps={"illustrative-family": "No source found."}
    )
    by_id = {r["id"]: r for r in data["records"]}
    assert by_id["nsw-illustrative-2016"]["recs"] == ["illustrative-recommendation"]
    assert by_id["nsw-other-2017"]["recs"] == [] and by_id["nsw-other-2017"]["recGap"] == "No source found."
    assert data["recommendations"][0]["kindLabel"] and data["recKinds"]["reform"]
    html = growth.render("explorer.html", data, "index.html", standalone=True)
    page = json.loads(re.search(r'<script type="application/json" id="page-data">(.*?)</script>', html, re.S).group(1))
    assert page["recommendations"][0]["id"] == "illustrative-recommendation"
    for hook in ('id="tab-recs"', 'id="reclist"', "What government could do", "rec="):
        assert hook in html
