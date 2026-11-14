"""Register data and the draft severity score (DECISIONS E-161, E-184)."""

from __future__ import annotations

import datetime as dt
import json
import re

import pytest

from alicia.menu import growth, registerdata
from alicia.menu.explorer import build_payload
from alicia.register import severity as S
from alicia.register.catalogue import load_records
from alicia.register.requirements import load_requirements


@pytest.fixture(scope="module")
def data():
    records = load_records().records
    menu = build_payload(records, generated=dt.date(2026, 11, 14))
    return records, menu, registerdata.payload(menu)


def test_severity_follows_the_coded_attributes():
    reqs = {q.id: q for q in load_requirements().requirements}
    for q in reqs.values():
        s = S.severity(q)
        types = {t.type for t in q.triggers}
        when = "entry" if "entry" in types else "growth" if types & set(S.GROWTH) else "operating"
        bound = "all" if any(not (r.condition or r.activities) for r in q.reach) else "some"
        assert (s["when"], s["bound"]) == (when, bound), q.id
        assert s["score"] == S.KIND_POINTS[q.kind] + S.WHEN_POINTS[when] + S.BOUND_POINTS[bound], q.id
        assert 1 <= s["score"] <= S.MAX_SCORE == 7 and s["notCoded"] == list(S.NOT_CODED), q.id
        assert s["band"] == ("high" if s["score"] >= 5 else "medium" if s["score"] >= 3 else "low"), q.id
    # A licence needed before trading, binding every builder, is the top score; GST registration bites at a
    # turnover threshold.
    assert S.severity(reqs["nsw-builder-licence"])["score"] == 7
    gst = S.severity(reqs["cth-gst-registration"])
    assert (gst["when"], gst["score"], gst["band"], gst["thresholds"]) == ("growth", 4, "medium", 1)
    # The score tells requirements apart where the marks do not: it takes every value from 1 to 7.
    assert {S.severity(q)["score"] for q in reqs.values()} == set(range(1, 8))


def test_every_item_has_one_row_with_its_coding(data):
    records, menu, page = data
    reqs = load_requirements().requirements
    ids = [r["id"] for r in page["rows"]]
    assert len(ids) == len(set(ids)) == len(records) + len(reqs)
    assert set(ids) == {r.id for r in records} | {q.id for q in reqs}
    by_id = {r["id"]: r for r in page["rows"]}
    levers = {r["id"]: r for r in menu["records"]} | {
        q["id"]: q for r in menu["records"] for q in r.get("requirements", [])
    }
    drivers = list(menu["framework"]["drivers"])
    for rid in ("cth-gst-registration", "nsw-builder-licence", "nsw-planning-zoning", "act-amr-2021"):
        row, src = by_id[rid], levers[rid]
        marks = {m["driver"]: m["mark"] for m in src["assessment"]["marks"]}
        assert row["marks"] == [marks.get(d, 0) for d in drivers] and row["total"] == sum(marks.values()), rid
        assert row["impactClass"] == (src["impactClass"] or "") and row["businesses"] == src["exposure"]["businesses"]
        assert row["review"] == "draft" and row["file"].endswith(f"{rid}.json"), rid
    gst = by_id["cth-gst-registration"]
    assert gst["type"] == "Requirement" and gst["severity"] == 4 and gst["setBy"] == "Cth" and gst["classes"] == "All"
    assert "C2004A00446" in gst["laws"] and gst["checked"] == "official register text" and gst["sources"] == 1
    assert "Australian Taxation Office" in gst["bodies"]
    amr = by_id["act-amr-2021"]
    assert amr["type"] == "Reform" and not amr["standing"] and amr["severity"] is None and amr["setBy"] == "ACT"
    # A requirement shown inside a register item on the levers page has its own row here, naming the item.
    inside = [r for r in page["rows"] if r["inside"]]
    assert inside and all(r["type"] == "Requirement" and r["inside"] in by_id for r in inside)


def test_the_page_is_built_and_linked_from_the_nav(data):
    _, _, page = data
    html = growth.render("register-data.html", page, "register-data.html", standalone=True)
    assert "<h1>Register data" in html and 'aria-current="page"' in html and "Download as CSV" in html
    nav = html[html.index('<nav class="site-nav"') : html.index("</nav>")]
    assert re.findall(r'href="(register-data\.html)"', nav) == ["register-data.html"]
    embedded = json.loads(re.search(r'id="page-data">(.*?)</script>', html, re.S).group(1))
    assert len(embedded["rows"]) == len(page["rows"]) and len(embedded["drivers"]) == 8
    assert "have not been settled" in embedded["note"]  # the severity weights are a draft
