"""The legislation menu: every register item with its framework assessment and its industries' statistics."""

from __future__ import annotations

import json
import re

from alicia.menu import growth
from alicia.menu.explorer import build_payload
from alicia.menu.industry import MEASURES, TILES
from alicia.register import framework as fw
from alicia.register.catalogue import load_records
from alicia.register.evaluation import load_evaluations
from alicia.register.schema import ChangeRecord

SRC = "https://example.org/illustrative-source"


def illustrative(title: str = "Illustrative change", assessed: bool = True) -> ChangeRecord:
    rec = {
        "id": "nsw-illustrative-2016",
        "family": "rideshare-legalisation",
        "title": title,
        "jurisdiction": "NSW",
        "summary": "ILLUSTRATIVE test record.",
        "instruments": [{"title": "Illustrative Act", "role": "principal"}],
        "dates": {"commenced": [{"date": "2016-07-01", "what": "x", "source": SRC}]},
        "direction": "enhancing",
        "direction_rationale": "x",
        "channels": ["barriers"],
        "industries": [{"anzsic": "4623", "name": "Taxi and Other Road Transport", "exposure": "direct"}],
        "verified": {"dates": True},
    }
    if assessed:
        rec["assessment"] = {
            "summary": "ILLUSTRATIVE.",
            "marks": [
                {"driver": "entry-exit", "mark": 2, "reason": "x"},
                {"driver": "innovation", "mark": 1, "reason": "y"},
            ],
            "main_driver": "entry-exit",
            "reach": "narrow",
            "confidence": "low",
            "assessed_on": "2026-10-28",
        }
    return ChangeRecord.model_validate(rec)


def _page_data(html: str) -> dict:
    return json.loads(re.search(r'<script type="application/json" id="page-data">(.*?)</script>', html, re.S).group(1))


def test_payload_carries_the_assessment_with_its_total_band_and_mixed_flag():
    data = build_payload(
        [illustrative()], [{"record_id": "nsw-illustrative-2016", "status": "confirmed", "issues": []}]
    )
    r = data["records"][0]
    assert r["assessment"]["total"] == 3 and r["assessment"]["rating"] == "strongly-positive"
    assert r["assessment"]["mixed"] is False and r["assessment"]["main_driver"] == "entry-exit"
    assert r["effective"] == "2016-07-01" and r["check"]["status"] == "confirmed"
    assert r["industries"][0]["division"] == "I"
    # The econometric fields are left to the archive.
    assert not {"comparison", "confounders", "price_series", "screen", "evaluation"} & set(r)
    assert data["framework"]["version"] == fw.VERSION and set(data["framework"]["drivers"]) == set(fw.DRIVERS)


def test_statistics_rows_name_defined_measures_and_levels():
    data = build_payload([illustrative()])
    s = data["records"][0]["stats"]
    if s is None:  # costing parameters not built
        return
    assert set(data["statsMeasures"]) == set(MEASURES) and data["statsTiles"] == list(TILES)
    for measure, _value, _all, level, period in s["rows"]:
        assert measure in MEASURES and 0 <= level < len(s["levels"]) and period


def test_an_unassessed_item_still_renders():
    html = growth.render("explorer.html", build_payload([illustrative(assessed=False)]), "index.html", standalone=True)
    assert _page_data(html)["records"][0]["assessment"] is None
    assert not re.search(r"__[A-Z_]+__", html) and "/*__" not in html


def test_embedded_data_cannot_close_the_script_tag():
    html = growth.render(
        "explorer.html", build_payload([illustrative("Bad </script><script>alert(1)</script>")]), "index.html"
    )
    blob = re.search(r'id="page-data">(.*?)</script>', html, re.S).group(1)
    assert "</script" not in blob and json.loads(blob)["records"][0]["title"].startswith("Bad </script>")


def test_the_menu_has_driver_tags_and_no_evaluated_tag():
    html = growth.render("explorer.html", build_payload([illustrative()]), "index.html", standalone=True)
    assert 'id="f-driver"' in html and 'id="f-rating"' in html and 'id="f-kind"' in html
    assert 'id="f-eval"' not in html and "Evaluated" not in html
    assert '<a href="index.html" aria-current="page">' in html and 'href="framework.html"' in html


def test_the_real_register_links_archived_evaluations_without_tagging_them():
    records = load_records().records
    evals = load_evaluations(records).evaluations
    data = build_payload(records, evaluations=evals)
    by_id = {r["id"]: r for r in data["records"]}
    assert all(r["assessment"] for r in data["records"])
    assert by_id["wa-trading-hours-weeknight-2010"]["archivedEvaluation"]["id"] == "wa-trading-hours-2010-2012-phase5"
    assert by_id["cth-pharmacy-location-rules-2018"]["archivedEvaluation"] is None
    assert data["archivedEvaluations"] == len(evals)
