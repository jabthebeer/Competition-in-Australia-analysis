"""The Home page: every figure it shows is recomputed here from the source files by a separate route."""

from __future__ import annotations

import datetime as dt
import json
import re

import pandas as pd
import pytest

from alicia.menu import growth, home
from alicia.menu.explorer import build_payload
from alicia.pipeline import store
from alicia.register.catalogue import load_records
from alicia.register.requirements import load_requirements

CABEE = store.PROCESSED / "abs_cabee" / "class_state_fy.parquet"
PARAMS = store.PROCESSED / "costing" / "parameters.json"
needs_data = pytest.mark.skipif(
    not CABEE.exists()
    or not PARAMS.exists()
    or not (store.PROCESSED / "abs_state_accounts" / "industry_state_fy.parquet").exists(),
    reason="processed panels not built",
)


@pytest.fixture(scope="module")
def data():
    records = load_records().records
    page = growth.growth_payload() | {"conditions": growth.conditions_payload(records)}
    return page, build_payload(records)


def _by_label(figs):
    return {f["label"]: f for f in figs}


@needs_data
def test_the_entry_rate_matches_the_business_counts(data):
    """New businesses with employees, as a share of those operating at the start of the year: straight from the
    CABEE panel, every state and class added up."""
    df = pd.read_parquet(CABEE)
    emp = df[df["breakdown"].isin(["1-19 employees", "20-199 employees", "200+ employees"])]
    t = emp.pivot_table(index="period", columns="measure", values="value", aggfunc="sum")
    rate = (100 * t["entries"] / t["businesses_start"]).sort_index()
    first, last = rate.index[0].year, rate.index[-1].year
    fig = _by_label(home.figures(*data))["New businesses"]
    assert fig["value"] == f"{rate.iloc[-1]:.1f}%"
    assert f"in {home.fy(last)}," in fig["what"] and f"was {rate.iloc[0]:.1f}% in {home.fy(first)}." in fig["what"]
    assert (home.fy(2024), home.fy(1999), home.fy(2009)) == ("2024–25", "1999–00", "2009–10")  # an en dash


@needs_data
def test_concentration_and_mark_ups_match_the_rba_tables(data):
    """All industries, first and last years, straight from the ingested RBA RDP 2025-05 tables."""
    tables = json.loads(PARAMS.read_text("utf-8"))["tables"]
    figs = _by_label(home.figures(*data))

    def ends(table, column):
        rows = [r for r in tables[table]["rows"] if r["division"] == "TOT" and r[column] is not None]
        rows.sort(key=lambda r: r["fyear"])
        return rows[0], rows[-1]

    a, b = ends("rba_hf2025.concentration", "top4_weighted")
    conc = figs["Concentration"]
    assert conc["value"] == f"{100 * b['top4_weighted']:.1f}%" and f"in {b['fyear']}." in conc["what"]
    assert f"was {100 * a['top4_weighted']:.1f}% in {a['fyear']}." in conc["what"]
    a, b = ends("rba_hf2025.markups", "markup")
    mark = figs["Mark-ups"]
    assert mark["value"] == f"{b['markup']:.2f}" and f"in {b['fyear']}." in mark["what"]
    assert f"was {a['markup']:.2f} in {a['fyear']}." in mark["what"]


@needs_data
def test_the_barriers_count_matches_the_register(data):
    """Items with a negative overall mark, of the rows the levers page lists: every register record, and every
    requirement that is not shown inside a record."""

    def total(item):
        return sum(m.mark for m in item.assessment.marks) if item.assessment else 0

    records = load_records().records
    rows = [q for q in load_requirements().requirements if not q.records]
    negative = sum(total(x) < 0 for x in (*records, *rows))
    fig = _by_label(home.figures(*data))["Barriers on record"]
    assert fig["value"] == f"{negative:,}" and f"of the {len(records) + len(rows):,} laws" in fig["what"]
    assert fig["href"] == "menu.html"


@needs_data
def test_the_page_shows_each_figure_once_with_its_source_and_a_link(data):
    built = {href for href, _ in growth.PAGES}
    html = home.page(*data, built, generated=dt.date(2026, 11, 14))
    assert not re.search(r"__[A-Z_]+__", html)
    tiles = re.findall(r'<a class="tile" href="([^"]+)">.*?<span class="tile-src">([^<]+)</span></a>', html, re.S)
    assert [t[0] for t in tiles] == ["growth.html", "growth.html", "growth.html", "menu.html"]
    assert all(src for _, src in tiles)
    assert "Updated 14 November 2026." in html and "not an Australian Government product" in html
    # The picker lists the 19 industry divisions and the 8 states and territories, the lens's default chosen.
    assert len(re.findall(r'<option value="[A-S]"', html)) == 19 and '<option value="H" selected>' in html
    states = re.findall(r'<option value="([A-Z]+)"[^>]*>([^<]+)</option>', html[html.index('id="pickState"') :])
    assert states == [("NSW", "NSW"), ("VIC", "Vic"), ("QLD", "Qld"), ("SA", "SA"), ("WA", "WA")] + [
        ("TAS", "Tas"),
        ("NT", "NT"),
        ("ACT", "ACT"),
    ]


def test_a_figure_without_data_is_left_out():
    empty = {"barriers": {"bizGroup": {}, "bizYears": [], "concentration": None}}
    assert home.figures(empty, {}) == []
    one = home.figures(empty, {"records": [{"assessment": {"total": -1}}, {"assessment": {"total": 2}}]})
    assert [f["label"] for f in one] == ["Barriers on record"] and one[0]["value"] == "1"
