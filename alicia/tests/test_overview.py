"""Regulatory overview by industry: its figures are recomputed here from the source files by a separate route."""

from __future__ import annotations

import datetime as dt
import json
import re
from statistics import median

import pandas as pd
import pytest

from alicia.menu import growth, overview
from alicia.menu.explorer import build_payload
from alicia.pipeline import schema, store
from alicia.register.catalogue import load_records
from alicia.register.regimes import load_regimes, regimes_by_class
from alicia.register.requirements import load_requirements, reach_classes

CABEE = store.PROCESSED / "abs_cabee" / "class_state_fy.parquet"
needs_data = pytest.mark.skipif(not CABEE.exists(), reason="business counts not built")


@pytest.fixture(scope="module")
def data():
    records = load_records().records
    menu = build_payload(records, generated=dt.date(2026, 11, 14))
    return menu, records, overview.payload(menu, records)


@needs_data
def test_businesses_and_entry_rates_match_the_abs_counts(data):
    _, _, page = data
    df = pd.read_parquet(CABEE)
    df = df[df["geo_code"].isin(schema.STATES) & (df["period"] == df["period"].max()) & (df["breakdown"] != "")]
    assert page["year"] == df["period"].max().year + 1 and page["entryYear"] == df["period"].max().year
    by_class = {c["code"]: c for c in page["classes"]}
    for code in ("4511", "6221", "3011"):
        rows = df[df["industry_code"] == code]
        assert by_class[code]["businesses"] == round(rows[rows["measure"] == "businesses_end"]["value"].sum()), code
        emp = rows[rows["breakdown"] != "non-employing"]
        start = emp[emp["measure"] == "businesses_start"]["value"].sum()
        entries = emp[emp["measure"] == "entries"]["value"].sum()
        assert by_class[code]["entry"] == (round(100 * entries / start, 1) if start else None), code
    # A division is its classes added up.
    h = next(d for d in page["divisions"] if d["code"] == "H")
    inside = [c for c in page["classes"] if c["division"] == "H"]
    assert h["businesses"] == sum(c["businesses"] for c in inside) and h["classes"] == len(inside)
    assert len(page["divisions"]) == 19 and len(page["classes"]) == 506


def test_regime_figures_match_the_regimes(data):
    _, _, page = data
    by_class = regimes_by_class(load_regimes().regimes)
    for c in page["classes"][::40]:
        sector = [r for r in by_class[c["code"]] if r.scope == "sector"]
        assert c["regimes"] == len(sector) and c["bodies"] == sum(r.touchpoints for r in sector), c["code"]
    a = next(d for d in page["divisions"] if d["code"] == "A")
    inside = [c for c in page["classes"] if c["division"] == "A"]
    assert a["regimes"] == median(c["regimes"] for c in inside) and a["bodies"] == median(c["bodies"] for c in inside)


@needs_data
def test_rules_are_commonwealth_rules_particular_to_the_industry(data):
    """Cafes and restaurants (4511): each Commonwealth requirement that reaches the class, applies today, has a
    negative mark and does not reach a quarter of all businesses."""
    menu, _, page = data
    rows = {r["id"]: r for r in menu["records"]} | {
        q["id"]: q for r in menu["records"] for q in r.get("requirements", [])
    }
    want = {"major-narrow": set(), "minor": set()}
    for q in load_requirements().requirements:
        if q.jurisdiction != "CTH":
            continue
        firm = [r for r in q.reach if not (r.condition or r.activities)] or list(q.reach)
        if "4511" in {c for r in firm for c in reach_classes(r)} and rows[q.id]["impactClass"] in want:
            want[rows[q.id]["impactClass"]].add(q.id)
    got = overview.commonwealth_rules(menu, [], load_requirements().requirements)["4511"]
    assert got == want and all(want.values())
    cafe = next(c for c in page["classes"] if c["code"] == "4511")
    assert cafe["major"] >= len(want["major-narrow"]) and cafe["minor"] >= len(want["minor"])  # plus register items
    assert all(rows[i]["jurisdiction"] == "CTH" for ids in got.values() for i in ids)


@needs_data
def test_the_page_is_built_with_a_link_to_the_lens_on_every_row(data, tmp_path):
    _, _, page = data
    html = growth.render("regulatory-overview.html", page, "regulatory-overview.html", standalone=True)
    assert "<h1>Regulatory overview by industry" in html and 'aria-current="page"' in html
    assert not re.search(r"__(?!FOOT)[A-Z_]+__", html)
    embedded = json.loads(re.search(r'id="page-data">(.*?)</script>', html, re.S).group(1))
    assert embedded["lens"] == "industry-lens.html" and "not yet been" in embedded["note"]
    assert "division=${encodeURIComponent(d)}" in html  # each row's link to the lens
