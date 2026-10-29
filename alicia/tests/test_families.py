"""Group names for register families: one expandable row per policy shared by several items (DECISIONS E-99).

Records built here are ILLUSTRATIVE test fixtures, except where a test loads the committed register.
"""

from __future__ import annotations

from alicia.menu.explorer import build_payload
from alicia.register.catalogue import load_records
from alicia.register.families import Family, check_families, load_families
from alicia.register.schema import ChangeRecord

SRC = "https://example.org/illustrative-source"


def record(rid: str, jurisdiction: str, family: str | None = "illustrative-family") -> ChangeRecord:
    return ChangeRecord.model_validate(
        {
            "id": rid,
            "family": family,
            "title": f"ILLUSTRATIVE change ({jurisdiction})",
            "jurisdiction": jurisdiction,
            "summary": "Illustrative record used only in tests.",
            "instruments": [{"title": "Illustrative Act", "role": "principal"}],
            "dates": {"commenced": [{"date": "2016-07-01", "what": "x", "source": SRC}]},
            "direction": "enhancing",
            "direction_rationale": "x",
            "channels": ["barriers"],
            "industries": [{"anzsic": "4623", "name": "Taxi and Other Road Transport", "exposure": "direct"}],
            "verified": {"dates": True},
            "assessment": {
                "summary": "ILLUSTRATIVE.",
                "marks": [{"driver": "entry-exit", "mark": 1, "reason": "x"}],
                "main_driver": "entry-exit",
                "reach": "narrow",
                "confidence": "low",
                "assessed_on": "2026-10-29",
            },
        }
    )


def test_every_shared_family_needs_a_group_name():
    recs = [record("nsw-x-2016", "NSW"), record("vic-x-2016", "VIC"), record("qld-y-2016", "QLD", "solo-family")]
    named = {"illustrative-family": Family(id="illustrative-family", title="Illustrative issue", summary="S.")}
    assert check_families(named, recs) == []
    assert check_families({}, recs) == ["families.json: family 'illustrative-family' has 2 items but no group name"]
    stray = {**named, "gone": Family(id="gone", title="T", summary="S.")}
    assert check_families(stray, recs) == ["families.json: no family 'gone' in the register"]


def test_the_menu_groups_shared_families_under_their_names():
    recs = [record("nsw-x-2016", "NSW"), record("vic-x-2016", "VIC"), record("qld-y-2016", "QLD", "solo-family")]
    named = {"illustrative-family": Family(id="illustrative-family", title="Illustrative issue", summary="S.")}
    groups = build_payload(recs, families=named)["groups"]
    # A family of one item is not a group; each grouped item keeps its own record and assessment.
    assert groups == {
        "illustrative-family": {"title": "Illustrative issue", "summary": "S.", "members": ["nsw-x-2016", "vic-x-2016"]}
    }


def test_the_committed_group_names_cover_the_register():
    families, problems = load_families()
    assert problems == [] and check_families(families, load_records().records) == []
    # Names say what the issue is across jurisdictions, not just the policy's name.
    assert families["ncc-2022-adoption"].title.startswith("Inconsistent adoption")
    assert "except Victoria" in families["whs-harmonisation"].title
