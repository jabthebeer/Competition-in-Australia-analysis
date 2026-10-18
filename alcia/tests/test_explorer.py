"""Explorer page builder and the real register (offline)."""

from __future__ import annotations

import json
import re

from alcia.menu.explorer import build_payload, render
from alcia.register.catalogue import load_records
from alcia.register.schema import ChangeRecord

SRC = "https://example.org/illustrative-source"


def illustrative(title: str) -> ChangeRecord:
    return ChangeRecord.model_validate(
        {
            "id": "nsw-illustrative-2016",
            "family": "rideshare-legalisation",
            "title": title,
            "jurisdiction": "NSW",
            "summary": "ILLUSTRATIVE test record.",
            "instruments": [
                {
                    "title": "Illustrative Act",
                    "register_url": None,
                    "register_id": None,
                    "role": "principal",
                    "provisions": None,
                }
            ],
            "dates": {"commenced": [{"date": "2016-07-01", "what": "x", "source": SRC}]},
            "direction": "enhancing",
            "direction_rationale": "x",
            "direction_sources": [],
            "channels": ["barriers"],
            "industries": [{"anzsic": "4623", "name": "Taxi and Other Road Transport", "exposure": "direct"}],
            "comparison": "x",
            "confounders": [],
            "price_series": None,
            "notes": None,
            "verified": {"dates": True, "notes": None},
        }
    )


def test_payload_carries_screen_timing_division_and_check():
    rec = illustrative("Illustrative change")
    report = [{"record_id": rec.id, "status": "confirmed", "issues": []}]
    data = build_payload([rec], report)
    r = data["records"][0]
    assert r["effective"] == "2016-07-01"
    assert r["timing"]["first_full_fy"] == "2016-17"
    assert r["industries"][0]["division"] == "I"
    assert r["check"] == {"status": "confirmed", "issues": []}
    assert data["familyLabels"]["rideshare-legalisation"] == "Ride-share legalisation"
    assert data["coverage"]["firstStart"] == "2007-07-01" and data["coverage"]["lastEnd"] == "2025-06-30"


def test_embedded_data_cannot_close_the_script_tag():
    page = render(build_payload([illustrative("Bad </script><script>alert(1)</script> title")]))
    blob = re.search(r'<script type="application/json" id="menu-data">(.*?)</script>', page, re.S).group(1)
    assert "</script" not in blob
    assert json.loads(blob)["records"][0]["title"].startswith("Bad </script>")


def test_standalone_wraps_a_full_document():
    page = render(build_payload([illustrative("x")]), standalone=True)
    assert page.startswith("<!doctype html>") and page.rstrip().endswith("</html>")
    assert "__MENU_DATA__" not in page


def test_the_register_loads_and_validates():
    result = load_records()
    assert result.ok, result.problems
    assert len(result.records) >= 60
    assert all(r.review.status in ("draft", "reviewed") for r in result.records)


def test_payload_marks_evaluated_records_and_embeds_their_results():
    from alcia.register.evaluation import load_evaluations

    records = load_records().records
    evals = load_evaluations(records).evaluations
    data = build_payload(records, evaluations=evals, repo_base="https://example.org/repo/")
    by_id = {r["id"]: r for r in data["records"]}
    ev = data["evaluations"]["wa-trading-hours-2010-2012"]
    # The weeknight record shows its follow-up evaluation; the earlier one still covers the Sunday step.
    assert by_id["wa-trading-hours-weeknight-2010"]["evaluation"] == "wa-trading-hours-weeknight-2010-new-data"
    assert by_id["wa-trading-hours-sunday-2012"]["evaluation"] == ev["id"]
    covered = len({rid for e in data["evaluations"].values() for rid in e["records"]})
    assert sum(r["evaluation"] is not None for r in data["records"]) == covered
    assert {o["category"] for o in ev["outcomes"]} == {"competition", "prices", "productivity"}
    assert data["repoBase"] == "https://example.org/repo/" and data["categoryLabels"]["competition"] == "Competition"


def test_payload_without_evaluations_still_renders():
    page = render(build_payload([illustrative("x")]))
    blob = re.search(r'<script type="application/json" id="menu-data">(.*?)</script>', page, re.S).group(1)
    data = json.loads(blob)
    assert data["evaluations"] == {} and data["records"][0]["evaluation"] is None
