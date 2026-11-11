"""The legislation menu: every register item with its framework assessment and its industries' statistics."""

from __future__ import annotations

import json
import re
from pathlib import Path

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
    html = growth.render("explorer.html", build_payload([illustrative(assessed=False)]), "menu.html", standalone=True)
    assert _page_data(html)["records"][0]["assessment"] is None
    assert not re.search(r"__[A-Z_]+__", html) and "/*__" not in html


def test_embedded_data_cannot_close_the_script_tag():
    html = growth.render(
        "explorer.html", build_payload([illustrative("Bad </script><script>alert(1)</script>")]), "menu.html"
    )
    blob = re.search(r'id="page-data">(.*?)</script>', html, re.S).group(1)
    assert "</script" not in blob and json.loads(blob)["records"][0]["title"].startswith("Bad </script>")


def test_the_menu_has_driver_tags_and_no_evaluated_tag():
    html = growth.render("explorer.html", build_payload([illustrative()]), "menu.html", standalone=True)
    assert 'id="f-driver"' in html and 'id="f-rating"' in html and 'id="f-type"' in html and 'id="f-pos"' in html
    assert 'id="glanceKey"' in html and 'id="f-kind"' not in html  # types, not kinds of item (DECISIONS E-137)
    assert 'id="f-eval"' not in html and "Evaluated" not in html
    assert '<a href="menu.html" aria-current="page"' in html and 'href="framework.html"' in html
    assert '<h1>Legislative levers influencing competition <span class="beta">' in html


def test_the_menu_shows_no_econometric_evaluations():
    """The econometric archive is off the site (DECISIONS E-136): the menu neither shows nor links evaluations."""
    records = load_records().records
    evals = load_evaluations(records).evaluations
    data = build_payload(records, evaluations=evals)
    assert all(r["assessment"] for r in data["records"])
    assert "archivedEvaluations" not in data and all("archivedEvaluation" not in r for r in data["records"])
    html = growth.render("explorer.html", data, "menu.html", standalone=True)
    assert "archive.html" not in html and "evaluation-" not in html and "econometric archive" not in html.lower()


def test_the_menu_keeps_text_readable_and_folds_secondary_detail():
    """No text below 13px (0.8125rem), apart from the letter inside the round "i" buttons; secondary filters, item
    sections and the page notes sit in collapsible elements (owner request, 29 October 2026)."""
    template = (Path(growth.__file__).parent / "templates" / "explorer.html").read_text("utf-8")
    css = re.search(r"<style>(.*?)</style>", template, re.S).group(1)  # the page's own styles
    small = []
    for rule in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        for size in re.findall(r"font(?:-size)?:[^;]*?([\d.]+)rem", rule.group(2)):
            if float(size) < 0.8125 and ".term.info" not in rule.group(1):
                small.append((rule.group(1).strip(), size))
    assert small == []
    html = growth.render("explorer.html", build_payload([illustrative()]), "menu.html", standalone=True)
    assert 'id="moreFilters"' in html and 'class="about"' in html and 'details class="d-sec fold"' in html


# --- Requirements beside the register's items, in one vocabulary with the Industry lens (DECISIONS E-137) ------------


def _committed():
    from alicia.register.requirements import load_requirements

    records = load_records().records
    reqs = load_requirements().requirements
    return records, reqs, build_payload(records, requirements=reqs)


def test_every_requirement_is_a_row_or_sits_inside_its_item_never_both():
    records, reqs, data = _committed()
    ids = {r.id for r in records}
    rows = {r["id"] for r in data["records"] if r["type"] == "requirement"}
    inside = {q["id"]: r["id"] for r in data["records"] if r["type"] == "record" for q in r["requirements"]}
    assert rows.isdisjoint(inside) and rows | set(inside) == {q.id for q in reqs}
    for q in reqs:
        homes = [x for x in q.records if x in ids]
        assert (q.id in inside) == bool(homes) and (not homes or inside[q.id] in homes)
    pharm = next(r for r in data["records"] if r["id"] == "cth-pharmacy-location-rules")
    assert [q["id"] for q in pharm["requirements"]] == ["cth-pbs-pharmacy-approval"] and pharm["requirements"][0][
        "sameMarks"
    ]


def test_every_entry_has_a_type_and_the_positions_it_most_affects():
    from alicia.register import competition as C

    records, _reqs, data = _committed()
    kinds = {r.id: r.kind for r in records}
    for r in data["records"]:
        expected = (
            "requirement" if r["type"] == "requirement" else ("barrier" if kinds[r["id"]] == "barrier" else "law")
        )
        assert r["group"] == expected
        assert set(r["most"]) <= set(C.POSITIONS) and set(r["effects"]) <= set(C.POSITIONS)
        a = r["assessment"]
        assert bool(r["most"]) == bool(a and a["marks"])  # an item with no material effect affects no position
        for e in r["effects"].values():
            assert e["marks"] and all(0 <= i < len(a["marks"]) for i in e["marks"])
    by_id = {r["id"]: r for r in data["records"]}
    assert by_id["cth-pharmacy-location-rules"]["most"] == ["dominant"]  # the 1.5 km rule shelters incumbents
    assert by_id["qld-liquor-licence"]["most"] == list(C.POSITIONS)  # one mark each way: all three equally
    assert by_id["cth-superannuation-guarantee"]["most"] == ["smaller"]
    assert set(data["effectPhrases"]) == set(C.POSITIONS)


def test_most_affected_names_the_heaviest_position_or_every_tied_one():
    from alicia.register import competition as C
    from alicia.register.requirements import RequirementAssessment

    def a(*marks):
        return RequirementAssessment.model_validate(
            {
                "summary": "x",
                "marks": [{"driver": d, "mark": m, "reason": "r"} for d, m in marks],
                "main_driver": max(marks, key=lambda x: abs(x[1]))[0] if marks else None,
                "reach": "narrow",
                "confidence": "low",
                "assessed_on": "2026-11-11",
            }
        )

    assert C.most_affected(a(("burden", -1))) == ["smaller"]
    assert C.most_affected(a(("entry-exit", -2), ("competition", -1))) == ["dominant"]  # 2 + 1 against 2 and 1
    assert C.most_affected(a(("entry-exit", -1), ("competition", -1))) == ["entrants", "smaller", "dominant"]
    assert C.most_affected(a()) == []


def test_requirements_carry_class_codes_the_page_can_name():
    _records, _reqs, data = _committed()
    for r in data["records"]:
        for q in [r] + r.get("requirements", []):
            if q.get("type") != "requirement":
                continue
            assert not (q["allIndustries"] and q["industryCodes"])
            assert all(c in data["classNames"] and len(c) == 4 for c in q["industryCodes"])
            assert q["laws"] and q["sources"] and all(len(s["quote"]) >= 20 for s in q["sources"])
    liquor = next(r for r in data["records"] if r["id"] == "qld-liquor-licence")
    assert "4520" in liquor["industryCodes"] and data["classNames"]["4520"] == ["Pubs, Taverns and Bars", "H"]


def test_a_requirement_family_is_one_group_apart_from_the_registers_families():
    _records, reqs, data = _committed()
    families = {}
    for q in reqs:
        families.setdefault(q.family, []).append(q)
    rows = {r["id"]: r for r in data["records"]}
    for key, g in data["groups"].items():
        if not key.startswith("req-"):
            assert all(rows[m]["type"] == "record" for m in g["members"])
            continue
        members = [rows[m] for m in g["members"]]
        assert all(m["type"] == "requirement" and m["family"] == key for m in members) and len(members) > 1
    liquor = data["groups"]["req-liquor-licence"]
    assert liquor["title"] == "Hold a liquor licence to sell alcohol" and len(liquor["members"]) == 8
    assert liquor["unit"] == "jurisdiction"
    # One state words it differently ("Register as a domestic builder"); the group takes the title most share.
    assert data["groups"]["req-builder-licence"]["title"] == "Hold a builder's licence"


def test_both_pages_use_one_vocabulary():
    """The levers page and the Industry lens name market positions and types of item the same way (E-137)."""
    from alicia.menu import lens
    from alicia.register import competition as C

    records, reqs, data = _committed()
    lp = lens.payload(records, reqs)
    assert (
        [p["label"] for p in data["positions"]]
        == [p["label"] for p in lp["positions"]]
        == [
            "Entrants",
            "Existing competitors",
            "Monopolies and oligopolies",
        ]
    )
    assert data["effectPhrases"] == lp["effectPhrases"] == C.EFFECT_PHRASES
    assert data["framework"]["influenceTags"]["legislative"]["label"] == "Legislative influence"
    assert data["framework"]["influenceTags"]["barrier"]["label"] == "Non-legislative barrier"
    templates = Path(growth.__file__).parent / "templates"
    for page in ("explorer.html", "industry-lens.html"):
        text = (templates / page).read_text("utf-8")
        for old in (
            "Small and medium competitors",
            "Monopoly and oligopoly players",
            "Entrants into the market",
            "Existing setting",
            "Kind of item",
        ):
            assert old not in text, (page, old)
