"""Australia at a glance, on Structural competitive conditions: each figure is recomputed here by a second route."""

from __future__ import annotations

import json
import re

import pandas as pd
import pytest

from alicia.menu import figures, growth
from alicia.pipeline import store
from alicia.register.catalogue import load_records

CABEE = store.PROCESSED / "abs_cabee" / "class_state_fy.parquet"
PARAMS = store.PROCESSED / "costing" / "parameters.json"
needs_data = pytest.mark.skipif(
    not CABEE.exists()
    or not PARAMS.exists()
    or not (store.PROCESSED / "abs_state_accounts" / "industry_state_fy.parquet").exists(),
    reason="processed panels not built",
)


@pytest.fixture(scope="module")
def page():
    return growth.growth_payload() | {"conditions": growth.conditions_payload(load_records().records)}


def _by_label(card):
    return {f["label"]: f for f in card}


@needs_data
def test_entry_and_exit_match_the_business_counts(page):
    """Businesses with employees starting and closing for every 100 operating at the start of the year: straight
    from the CABEE panel, every state and class added up."""
    df = pd.read_parquet(CABEE)
    emp = df[df["breakdown"].isin(["1-19 employees", "20-199 employees", "200+ employees"])]
    t = emp.pivot_table(index="period", columns="measure", values="value", aggfunc="sum").sort_index()
    first, last = figures.fy(t.index[0].year), figures.fy(t.index[-1].year)
    card = _by_label(figures.scorecard(page))
    for label, measure in (("Business entry", "entries"), ("Business exit", "exits")):
        rate = 100 * t[measure] / t["businesses_start"]
        fig = card[label]
        assert fig["value"] == f"{rate.iloc[-1]:.1f}" and fig["what"].endswith(f", {last}"), label
        assert fig["was"] == f"{rate.iloc[0]:.1f} in {first}" and fig["tab"] == "entry", label
    # A state's rates come from the same counts.
    wa = emp[emp["geo_code"] == "WA"].pivot_table(index="period", columns="measure", values="value", aggfunc="sum")
    (_, v0), (_, v1) = figures.business_rates(page, "entries", place="WA")
    rate = (100 * wa["entries"] / wa["businesses_start"]).sort_index()
    assert (round(v0, 6), round(v1, 6)) == (round(rate.iloc[0], 6), round(rate.iloc[-1], 6))


@needs_data
def test_concentration_and_mark_ups_match_the_rba_tables(page):
    tables = json.loads(PARAMS.read_text("utf-8"))["tables"]
    card = _by_label(figures.scorecard(page))

    def ends(table, column):
        rows = sorted(
            (r for r in tables[table]["rows"] if r["division"] == "TOT" and r[column] is not None),
            key=lambda r: r["fyear"],
        )
        return rows[0], rows[-1]

    a, b = ends("rba_hf2025.concentration", "top4_weighted")
    conc = card["Concentration"]
    assert conc["value"] == f"{100 * b['top4_weighted']:.1f}%" and conc["what"].endswith(f", {b['fyear']}")
    assert conc["was"] == f"{100 * a['top4_weighted']:.1f}% in {a['fyear']}" and conc["tab"] == "concentration"
    a, b = ends("rba_hf2025.markups", "markup")
    mark = card["Mark-ups"]
    assert mark["value"] == f"{b['markup']:.2f}" and mark["what"].endswith(f", {b['fyear']}")
    assert mark["was"] == f"{a['markup']:.2f} in {a['fyear']}" and mark["tab"] == "profits"


@needs_data
def test_returns_match_a_second_calculation(page):
    """Return on equity behind barriers to entry and where barriers are low, worked out again with a table: each
    sector's profit and equity averaged over the years it is published with positive equity, then added up by
    group. (The page's own script makes the same calculation for the Profits and mark-ups tab.)"""
    profit = page["conditions"]["profit"]
    years = profit["years"]
    rows = [
        {
            "sector": s["key"],
            "group": s["group"],
            "year": y,
            "income": s["income"][i],
            "npat": s["npat"][i],
            "equity": s["equity"][i],
        }
        for s in profit["sectors"]
        for i, y in enumerate(years)
    ]
    df = pd.DataFrame(rows).dropna(subset=["income", "npat", "equity"])
    df = df[df["equity"] > 0]
    sector = df.groupby(["group", "sector"])[["npat", "equity"]].mean().reset_index()
    behind = sector[sector["group"].isin(figures.BARRIER_GROUPS)][["npat", "equity"]].sum()
    low = sector[sector["group"] == figures.LOW_BARRIERS][["npat", "equity"]].sum()
    fig = _by_label(figures.scorecard(page))["Returns behind barriers"]
    assert fig["value"] == f"{100 * behind['npat'] / behind['equity']:.1f}%"
    assert fig["was"] == f"{100 * low['npat'] / low['equity']:.1f}% where barriers are low"
    assert fig["what"].endswith(f"{figures.fy(years[0])} to {figures.fy(years[-1])}") and fig["tab"] == "profits"
    # The barrier groups are the ones the page marks as barriers.
    assert set(figures.BARRIER_GROUPS) == {g["id"] for g in page["barriers"]["groups"] if g.get("barrier")}


@needs_data
def test_the_scorecard_is_written_into_the_page_as_links_to_its_tabs(page):
    html = growth.scorecard_html(page)
    tiles = re.findall(r'<a class="tile" href="#(\w+)">.*?<span class="t-was">([^<]+)</span></a>', html, re.S)
    assert [t[0] for t in tiles] == ["entry", "entry", "concentration", "profits", "profits"]
    assert all(was for _, was in tiles)
    assert growth.scorecard_html({}) == ""  # a page without the competition data gets no scorecard


def test_a_figure_without_data_is_left_out():
    empty = {"barriers": {"bizGroup": {}, "bizYears": [], "concentration": None}}
    assert figures.scorecard(empty) == []
    assert figures.first_last([2001, 2002, 2003], [None, 1.0, 2.0]) == ((2002, 1.0), (2003, 2.0))
    assert figures.first_last([2001], [1.0]) is None  # one year is not a comparison
