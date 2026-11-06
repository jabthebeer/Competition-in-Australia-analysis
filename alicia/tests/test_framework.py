"""The productivity impact framework, the assessments in the register, and the industry statistics beside them."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from alicia.register import framework as fw
from alicia.register.catalogue import default_register_dir, load_records
from alicia.register.schema import ChangeRecord, json_schema

ROOT = Path(__file__).resolve().parents[2]
SRC = "https://example.org/illustrative-source"


def illustrative(**changes) -> dict:
    rec = {
        "id": "nsw-illustrative-2016",
        "title": "ILLUSTRATIVE change",
        "jurisdiction": "NSW",
        "summary": "ILLUSTRATIVE test record.",
        "instruments": [{"title": "Illustrative Act", "role": "principal"}],
        "dates": {"commenced": [{"date": "2016-07-01", "what": "x", "source": SRC}]},
        "direction": "enhancing",
        "direction_rationale": "x",
        "channels": ["barriers"],
        "industries": [{"anzsic": "4623", "name": "Taxi and Other Road Transport", "exposure": "direct"}],
        "verified": {"dates": True},
        "assessment": {
            "summary": "ILLUSTRATIVE.",
            "marks": [
                {"driver": "entry-exit", "mark": 2, "reason": "x"},
                {"driver": "burden", "mark": -1, "reason": "y"},
            ],
            "main_driver": "entry-exit",
            "reach": "narrow",
            "confidence": "low",
            "assessed_on": "2026-10-28",
        },
    }
    for k, v in changes.items():
        rec[k] = v
    return rec


def test_every_driver_has_a_question_evidence_a_full_marking_guide_and_costing_channels():
    assert set(fw.DRIVERS) == set(fw.Driver.__args__)
    for key, d in fw.DRIVERS.items():
        assert d["pillar"] in fw.PILLARS, key
        assert d["question"].endswith("?") and d["why"] and d["look_for"], key
        assert set(d["marks"]) == {2, 1, -1, -2}, key
        assert d["channels"] and all(c.startswith("C") for c in d["channels"]), key
        assert all(s in fw.SOURCES for s in d["why_sources"]), key
    assert all(s["url"].startswith("https://") for s in fw.SOURCES.values())
    assert {p for p in fw.PILLARS} == {d["pillar"] for d in fw.DRIVERS.values()}


def test_the_plain_language_content_is_complete():
    for key, d in fw.DRIVERS.items():
        assert d["plain"].endswith("."), key
        assert set(d["marks_short"]) == set(d["marks"]), key
    assert len({c["key"] for c in fw.CONCEPTS}) == len(fw.CONCEPTS)
    assert all(c["plain"] and c["detail"] for c in fw.CONCEPTS)
    assert all(s in fw.SOURCES for x in fw.SIGNS for s in x["sources"])
    assert len(fw.STEP_TITLES) == len(fw.STEPS) and len(fw.CAVEAT_TITLES) == len(fw.CAVEATS)
    assert all(set(o["under"]) <= set(fw.DRIVERS) for o in fw.OVERLAP_TABLE)


@pytest.mark.parametrize(
    ("total", "band"),
    [
        (5, "strongly-positive"),
        (3, "strongly-positive"),
        (2, "positive"),
        (1, "positive"),
        (0, "neutral"),
        (-1, "negative"),
        (-2, "negative"),
        (-3, "strongly-negative"),
        (-8, "strongly-negative"),
    ],
)
def test_rating_bands(total, band):
    assert fw.rating(total) == band


def test_an_assessment_sums_its_marks_and_flags_mixed_effects():
    a = ChangeRecord.model_validate(illustrative()).assessment
    assert a.total == 1 and a.rating == "positive" and a.mixed
    assert a.mark("entry-exit") == 2 and a.mark("capital") == 0


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (lambda a: a["marks"].append({"driver": "capital", "mark": 0, "reason": "z"}), "leave a driver out"),
        (lambda a: a["marks"].append({"driver": "burden", "mark": 1, "reason": "z"}), "marked once"),
        (lambda a: a.update(main_driver="burden"), "largest mark"),
        (lambda a: a["marks"].append({"driver": "capital", "mark": 3, "reason": "z"}), "less than or equal to 2"),
        (lambda a: a.update(main_driver="growth"), "main_driver"),
        (lambda a: a.update(marks=[]), "at least 1"),
    ],
)
def test_inconsistent_assessments_are_rejected(edit, message):
    rec = illustrative()
    edit(rec["assessment"])
    with pytest.raises(ValidationError, match=message):
        ChangeRecord.model_validate(rec)


def test_kinds_of_item_need_what_they_should():
    # A non-legislative barrier needs no instrument; a reform or setting does.
    assert ChangeRecord.model_validate(illustrative(kind="barrier", instruments=[])).kind == "barrier"
    with pytest.raises(ValidationError, match="setting needs at least one instrument"):
        ChangeRecord.model_validate(illustrative(kind="setting", instruments=[]))
    # Industries may be left out only for an economy-wide item.
    with pytest.raises(ValidationError, match="economy-wide"):
        ChangeRecord.model_validate(illustrative(industries=[]))
    rec = illustrative(industries=[])
    rec["assessment"]["reach"] = "economy-wide"
    assert ChangeRecord.model_validate(rec).industries == ()


def test_every_register_item_is_assessed_against_the_current_framework():
    records = load_records().records
    assert records and all(r.assessment for r in records)
    assert {r.assessment.framework for r in records} == {fw.VERSION}
    # The marks use the whole scale and every driver is someone's main driver or at least marked.
    marked = {m.driver for r in records for m in r.assessment.marks}
    assert marked == set(fw.DRIVERS)
    assert {m.mark for r in records for m in r.assessment.marks} == {-2, -1, 1, 2}


def test_records_of_one_reform_family_share_a_main_driver_unless_they_differ():
    """Members of a family are the same reform in different places, so their main drivers should agree; the known
    exceptions are where a member genuinely differs (Tasmania's ride-share law also let new taxi licences be
    suspended; the industry codes family holds different codes)."""
    exceptions = {
        "industry-codes",
        "pharmacy-regulation",
        "liquor-lockouts-last-drinks",
        "fair-work-2022-2024",
        "rideshare-legalisation",
        "liquor-licence-entry-restrictions",
        "planning-zoning",
        "card-payments",
        "ctp-insurance-competition",
        "building-practitioner-registration",
        "insolvency-reform",
        "short-term-rental-regulation",
        "harper-cca-2017",
        "point-to-point-licensing",
        "gaming-market-structure",
    }
    by_family: dict[str, set] = {}
    for r in load_records().records:
        if r.family and r.family not in exceptions:
            by_family.setdefault(r.family, set()).add(r.assessment.main_driver)
    assert {f: d for f, d in by_family.items() if len(d) > 1} == {}


def test_the_methods_note_matches_the_framework():
    doc = ROOT / "docs" / "productivity_framework.md"
    assert doc.read_text("utf-8") == fw.markdown(), (
        "regenerate with: uv run alicia framework -o ../docs/productivity_framework.md"
    )


def test_the_exported_record_schema_is_up_to_date():
    path = default_register_dir() / "schema" / "change-record.schema.json"
    assert json.loads(path.read_text("utf-8")) == json.loads(json.dumps(json_schema())), (
        "regenerate with: uv run python scripts/export_schema.py"
    )


# --- Industry statistics -----------------------------------------------------------------------------------------
def _params():
    from alicia.costing.params import params_path

    path = params_path()
    if not path.exists():
        pytest.skip("costing parameters not built")
    return json.loads(path.read_text("utf-8"))


def test_industry_statistics_come_from_the_published_rows():
    from alicia.menu.industry import MEASURES, IndustryStats

    params = _params()
    stats = IndustryStats(params)
    rec = ChangeRecord.model_validate(illustrative())
    snap = stats.snapshot(rec)
    rows = {r[0]: r for r in snap["rows"]}
    assert set(rows) <= set(MEASURES)
    cab = next(
        r
        for r in params["tables"]["abs_cabee_latest.class_size"]["rows"]
        if r["anzsic"] == "4623" and r["size_band"] == "total"
    )
    assert rows["biz"][1] == pytest.approx(cab["end"], rel=1e-3)
    assert rows["entry"][1] == pytest.approx(cab["entries"] / cab["start"] * 100, rel=1e-3)
    # Australian Industry: subdivision 46 (road transport) for a class in it.
    ai = next(
        r
        for r in params["tables"]["abs_australian_industry.industry"]["rows"]
        if r["anzsic"] == "46" and r["fy"] == "2024-25"
    )
    assert rows["va_worker"][1] == pytest.approx(ai["iva"] / ai["employment"] * 1000, rel=1e-3)
    assert "subdivision 46" in snap["levels"][rows["va_worker"][3]]
    # The division of the first industry (I, transport) for productivity growth and concentration.
    assert "division I" in snap["levels"][rows["top4"][3]]
    assert snap["where"] == "NSW" and not snap["economyWide"]


def test_an_economy_wide_item_gets_all_industry_figures_and_overlapping_codes_count_once():
    from alicia.menu.industry import IndustryStats, _dedupe

    assert _dedupe(["41", "4110", "G", "6221"]) == ["G", "6221"]
    stats = IndustryStats(_params())
    rec = illustrative(industries=[])
    rec["assessment"]["reach"] = "economy-wide"
    snap = stats.snapshot(ChangeRecord.model_validate(rec))
    rows = {r[0]: r for r in snap["rows"]}
    assert snap["economyWide"] and rows["biz"][1] == rows["biz"][2]


def test_the_assessment_review_sheet_is_up_to_date():
    import subprocess
    import sys

    script = ROOT / "alicia" / "scripts" / "assessment_sheet.py"
    out = subprocess.run([sys.executable, str(script), "--check"], capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


def test_assessed_records_round_trip_through_json():
    rec = ChangeRecord.model_validate(illustrative())
    again = ChangeRecord.model_validate(json.loads(rec.model_dump_json()))
    assert again == rec and copy.deepcopy(again.assessment).total == 1
