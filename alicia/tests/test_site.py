"""Website summary pages (growth, conditions) built from the committed processed panels."""

from __future__ import annotations

import json
import re

import pytest

from alicia.menu import growth
from alicia.pipeline import store
from alicia.register.catalogue import load_records
from alicia.register.evaluation import load_evaluations

needs_panels = pytest.mark.skipif(
    not (store.PROCESSED / "controls" / "state_quarter.parquet").exists()
    or not (store.PROCESSED / "abs_state_accounts" / "industry_state_fy.parquet").exists(),
    reason="processed panels not built",
)


@needs_panels
def test_growth_payload_is_aligned_and_consistent():
    p = growth.growth_payload()
    n = len(p["years"])
    for s in p["states"]:
        assert len(p["gsp"]["volume"][s]) == n
        for series in p["gva"]["current"][s].values():
            assert len(series) == n
    # Divisions in current prices sum to less than the total (ownership of dwellings is left out).
    i = p["years"].index(2024)
    wa = p["gva"]["current"]["WA"]
    divisions = sum(wa[c][i] for c in growth.DIVISIONS)
    assert 0.8 * wa["TOT"][i] < divisions < wa["TOT"][i]
    # CABEE: Australia is the sum of the states; stocks link up (end of one year = start of the next, roughly).
    j = p["bizYears"].index(2020)
    aus = p["biz"]["AUS"]["TOT"]["entries"][j]
    assert aus == sum(p["biz"][s]["TOT"]["entries"][j] for s in p["states"] if s != "AUS")
    assert len(p["empYears"]) == len(p["emp"]["NSW"]["G"])


@needs_panels
def test_conditions_payload_series_match_periods_and_mark_evaluated_reforms():
    records = load_records().records
    evals = load_evaluations(records).evaluations
    p = growth.conditions_payload(records, evals)
    for block in (*p["quarterly"].values(), *p["monthly"].values()):
        for values in block["values"].values():
            assert len(values) == len(block["periods"])
    assert set(p["monthly"]["unemp"]["original"]) == {"NT", "ACT"}
    assert "AUS" not in p["quarterly"]["sfd"]["values"]  # state final demand is published for states only
    dates = {(r["jurisdiction"], r["date"]) for r in p["reforms"]}
    assert ("WA", "2010-11-01") in dates
    assert all(v for v in p["vintages"].values())


def test_render_fills_every_placeholder_and_marks_the_current_page():
    html = growth.render("growth.html", {"x": "</script>"}, "growth.html", standalone=True)
    assert not re.search(r"__[A-Z_]+__", html)
    assert '<a href="growth.html" aria-current="page">' in html
    assert "<\\/script>" in html  # embedded data cannot close the script element
    assert html.startswith("<!doctype html>")


@needs_panels
def test_build_site_writes_three_linked_pages(tmp_path):
    records = load_records().records
    evals = load_evaluations(records).evaluations
    paths = growth.build_site(tmp_path, records, evals)
    assert sorted(p.name for p in paths) == ["conditions.html", "growth.html", "index.html"]
    index = (tmp_path / "index.html").read_text("utf-8")
    assert '<a href="index.html" aria-current="page">' in index and 'href="conditions.html"' in index
    data = re.search(r'id="page-data">(.*?)</script>', (tmp_path / "growth.html").read_text("utf-8"), re.S)
    assert json.loads(data.group(1))["repo"].startswith("https://github.com/")


@needs_panels
def test_state_covariates_cover_every_state_and_are_plausible():
    from alicia.evaluate import covariates

    d = covariates.state_covariates(base_fy=2009)
    assert set(d["state"]) >= {"NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"}
    wa = d[(d["state"] == "WA") & (d["period"] == "2010-10-01")].iloc[0]
    assert 2 < wa["unemployment_rate"] < 8 and 0 < wa["population_growth"] < 5
    share = covariates.mining_share(2009)
    assert share.idxmax() == "WA" and share["ACT"] < 0.01
    # The exposure control moves one for one with the mining share.
    q = d[d["period"] == "2010-10-01"].set_index("state")["commodity_exposure"]
    assert q["WA"] / q["NSW"] == pytest.approx(share["WA"] / share["NSW"])
