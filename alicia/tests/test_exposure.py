"""Exposure and impact classes (DECISIONS E-161): the businesses each rule reaches are recounted here straight from
the ABS business counts, and the classes follow the stated rule."""

from __future__ import annotations

import datetime as dt
import json
import re

import pandas as pd
import pytest

from alicia.menu import exposure as X
from alicia.menu import growth
from alicia.menu.explorer import build_payload
from alicia.pipeline import schema, store
from alicia.register.catalogue import load_records
from alicia.register.requirements import load_requirements, reach_classes

CABEE = store.PROCESSED / "abs_cabee" / "class_state_fy.parquet"
needs_data = pytest.mark.skipif(not CABEE.exists(), reason="business counts not built")


@pytest.fixture(scope="module")
def panel():
    """Businesses at the end of the latest year, by class and state: every size band added up."""
    df = pd.read_parquet(CABEE)
    df = df[(df["measure"] == "businesses_end") & (df["breakdown"] != "") & df["geo_code"].isin(schema.STATES)]
    df = df[df["industry_code"].str.fullmatch(r"\d{4}") & (df["period"] == df["period"].max())]
    return df


@pytest.fixture(scope="module")
def page():
    return build_payload(load_records().records, generated=dt.date(2026, 11, 14))


def _rows(page):
    return page["records"] + [q for r in page["records"] for q in r.get("requirements", [])]


@needs_data
def test_business_counts_match_the_panel(panel):
    counts = X.load_counts()
    assert counts.year == panel["period"].max().year + 1
    assert round(counts.total(schema.STATES)) == round(panel["value"].sum())
    employing = panel[panel["breakdown"] != "non-employing"]
    assert round(counts.total(schema.STATES, employing=True)) == round(employing["value"].sum())
    assert round(counts.total(["WA"])) == round(panel[panel["geo_code"] == "WA"]["value"].sum())


@needs_data
def test_a_requirements_businesses_are_recounted_from_the_panel(panel, page):
    """Three requirements with different shapes: one for every business, one state licence, one Commonwealth
    requirement for a few industries."""
    by_id = {r["id"]: r for r in _rows(page)}
    reqs = {q.id: q for q in load_requirements().requirements}
    total = panel["value"].sum()
    for rid in ("cth-gst-registration", "nsw-builder-licence", "cth-afs-licence"):
        q, row = reqs[rid], by_id[rid]
        states = list(schema.STATES) if q.jurisdiction == "CTH" else [q.jurisdiction]
        # The parts of its reach that bind whole industries (all of them, when every part follows an activity).
        firm = [r for r in q.reach if not (r.condition or r.activities)] or list(q.reach)
        classes = {c for r in firm for c in reach_classes(r)}
        inside = panel[panel["industry_code"].isin(classes) & panel["geo_code"].isin(states)]
        base = panel[panel["geo_code"].isin(states)]["value"].sum()
        e = row["exposure"]
        assert e["businesses"] == round(inside["value"].sum()), rid
        assert e["employing"] == round(inside[inside["breakdown"] != "non-employing"]["value"].sum()), rid
        assert e["share"] == round(100 * inside["value"].sum() / base, 1), rid
        assert e["shareAus"] == round(100 * inside["value"].sum() / total, 1), rid
        assert e["classes"] == len(classes) and e["year"] == 2025, rid
    assert by_id["cth-gst-registration"]["exposure"]["allIndustries"]
    assert by_id["cth-gst-registration"]["impactClass"] == "major-wide"


@needs_data
def test_every_class_follows_the_rule(page):
    rows = _rows(page)
    classed = [r for r in rows if r["impactClass"]]
    assert {r["impactClass"] for r in classed} == set(X.CLASSES)
    for r in rows:
        e, total = r["exposure"], (r["assessment"] or {}).get("total")
        if not r["standing"] or total is None or total >= 0:
            assert r["impactClass"] is None, r["id"]
        elif e["share"] >= X.WIDE_SHARE and not e["partial"]:
            assert r["impactClass"] == "major-wide", r["id"]
        else:
            assert r["impactClass"] == ("major-narrow" if total <= X.DEEP_TOTAL else "minor"), r["id"]
    # A reform is a change, not a rule, unless it is in force and added a restriction.
    for r in page["records"]:
        if r.get("kind") == "reform" and (r["ended"] or r["assessment"]["total"] >= 0):
            assert not r["standing"], r["id"]
    # A council's rule, or one that follows an activity, is counted as an upper bound and is never wide.
    assert all(r["impactClass"] != "major-wide" for r in rows if r["exposure"]["partial"])
    assert all(r["exposure"]["partial"] for r in rows if r.get("tier") == "local")


def test_an_award_counts_its_own_industry_not_every_employer_of_the_occupation():
    """The Architects Award covers architectural practices, and anyone else who employs a registered architect.
    Only the first is counted."""
    q = next(x for x in load_requirements().requirements if x.id == "cth-award-ma000079")
    assert any(r.scope == "all" and r.condition for r in q.reach) and X.beyond(q) and not X.conditional(q)
    classes = {c for c, _ in X.requirement_pairs(q)}
    assert classes == {c for r in q.reach if not r.condition and not r.activities for c in reach_classes(r)}
    assert 0 < len(classes) < 20


def test_the_class_rule_on_its_own():
    wide = {"share": 100.0, "partial": False}
    narrow = {"share": 3.0, "partial": False}
    assert X.impact_class(-1, wide) == "major-wide" and X.impact_class(-4, wide) == "major-wide"
    assert X.impact_class(-2, narrow) == "major-narrow" and X.impact_class(-1, narrow) == "minor"
    assert X.impact_class(-3, {"share": 100.0, "partial": True}) == "major-narrow"
    assert X.impact_class(0, wide) is None and X.impact_class(2, wide) is None and X.impact_class(None, wide) is None
    assert X.impact_class(-2, {"share": None}) is None  # no business counts in this build
    assert X.is_standing("requirement", -1, False, True) and X.is_standing("setting", 1, False, True)
    assert X.is_standing("reform", -1, False, True) and not X.is_standing("reform", 2, False, True)
    assert not X.is_standing("reform", -1, False, False) and not X.is_standing("setting", -2, True, True)


@needs_data
def test_the_levers_page_opens_on_an_overview(page):
    html = growth.render("explorer.html", page, "menu.html", standalone=True)
    markup = html[: html.index('<script type="application/json"')]
    assert re.findall(r'role="tab" id="tab-(\w+)" aria-controls="panel-\1"', markup) == ["overview", "browse"]
    panels = dict(
        re.findall(
            r'(?s)<div class="tab-panel" role="tabpanel" id="panel-(\w+)"(.*?)(?=<div class="tab-panel"|<footer)',
            markup,
        )
    )
    for inside in ("h-big", "bigTable", "h-glance", "h-who", "moreLinks"):
        assert f'id="{inside}"' in panels["overview"], inside
    for inside in ("f-impact", "view-list", "view-recs", "view-ind", "detail", "listMore"):
        assert f'id="{inside}"' in panels["browse"], inside
    assert " hidden" in panels["browse"].split(">")[0] and " hidden" not in panels["overview"].split(">")[0]
    assert ".tab-panel[hidden] { display: grid !important; }" in html  # without scripts, both show
    data = json.loads(re.search(r'<script type="application/json" id="page-data">(.*?)</script>', html, re.S).group(1))
    assert [c["id"] for c in data["impactClasses"]] == list(X.CLASSES) and data["exposureYear"] == 2025
    assert "What others recommend" in html and "What government could do" not in html


def test_the_link_cards_do_not_catch_the_chart_notes():
    """The grid of link cards once shared its class with the "About this chart" drop-downs, which split them into
    columns. They are separate classes."""
    from pathlib import Path

    css = (Path(growth.__file__).parent / "templates" / "site.css").read_text("utf-8")
    assert not re.search(r"(?m)^\.more\s*\{", css) and re.search(r"(?m)^\.more-links\s*\{", css)
