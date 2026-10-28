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
    names = sorted(p.name for p in paths)
    assert [n for n in names if not n.startswith("evaluation-")] == ["conditions.html", "growth.html", "index.html"]
    assert sorted(n for n in names if n.startswith("evaluation-")) == sorted(f"evaluation-{e.id}.html" for e in evals)
    one = (tmp_path / "evaluation-childcare-nqf-wa-delay-2012.html").read_text("utf-8")
    payload = json.loads(re.search(r'id="menu-data">(.*?)</script>', one, re.S).group(1))
    assert payload["single"] == "childcare-nqf-wa-delay-2012" and payload["evalPages"]
    assert {r["id"] for r in payload["records"]} == {"cth-nqf-childcare-2012", "wa-nqf-childcare-2012"}
    assert set(payload["evaluations"]) == {"childcare-nqf-wa-delay-2012", "childcare-nqf-2012"}  # follows link
    assert "<title>National Quality Framework" in one
    index = (tmp_path / "index.html").read_text("utf-8")
    assert '<a href="index.html" aria-current="page">' in index and 'href="conditions.html"' in index
    data = re.search(r'id="page-data">(.*?)</script>', (tmp_path / "growth.html").read_text("utf-8"), re.S)
    assert json.loads(data.group(1))["repo"].startswith("https://github.com/")


def _costing_dist(tmp_path, html=None):
    """A stand-in for regulatory-burden-tool/dist-site (the real one comes from `npm run build:site`)."""
    dist = tmp_path / "dist-site"
    (dist / growth.COSTING_ASSETS).mkdir(parents=True)
    (dist / growth.COSTING_ASSETS / "index-abc.js").write_text("console.log(1)", "utf-8")
    csp = "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'self'; connect-src 'none'\" />"
    body = '<body><!--__NAV__--><div id="root"></div></body>'
    default = f'<html lang="en-AU" data-site="alicia"><head>{csp}</head>{body}</html>'
    (dist / "costing.html").write_text(html if html is not None else default, "utf-8")
    return dist


def test_costing_tab_is_copied_with_the_site_nav(tmp_path):
    out = tmp_path / "site"
    out.mkdir()
    (out / growth.COSTING_ASSETS).mkdir()
    (out / growth.COSTING_ASSETS / "stale.js").write_text("old", "utf-8")
    pages = (*growth.PAGES, growth.COSTING_PAGE)
    written = growth.build_costing(out, _costing_dist(tmp_path), pages)
    html = (out / "costing.html").read_text("utf-8")
    assert '<div class="alicia-site-top"><nav class="site-nav"' in html and "<!--__NAV__-->" not in html
    assert '<a href="costing.html" aria-current="page">Policy costing</a>' in html and 'href="index.html"' in html
    assert sorted(p.name for p in written) == ["costing.html", "index-abc.js"]  # stale assets are removed
    assert "connect-src 'none'" in html


def test_costing_tab_refuses_a_build_without_its_privacy_policy_or_nav(tmp_path):
    with pytest.raises(ValueError, match="Content-Security-Policy"):
        growth.build_costing(tmp_path, _costing_dist(tmp_path / "a", "<body><!--__NAV__--></body>"), growth.PAGES)
    with pytest.raises(ValueError, match="placeholder"):
        no_nav = "<meta content=\"connect-src 'none'\">"
        growth.build_costing(tmp_path, _costing_dist(tmp_path / "b", no_nav), growth.PAGES)


@needs_panels
def test_build_site_links_the_costing_tab_from_every_page_only_when_built(tmp_path):
    records = load_records().records
    evals = load_evaluations(records).evaluations
    names = {p.name for p in growth.build_site(tmp_path / "with", records, evals, costing_dist=_costing_dist(tmp_path))}
    assert {"costing.html", "index-abc.js"} <= names
    for page in ("index.html", "growth.html", "conditions.html"):
        assert 'href="costing.html"' in (tmp_path / "with" / page).read_text("utf-8"), page
    growth.build_site(tmp_path / "without", records, evals)
    assert not (tmp_path / "without" / "costing.html").exists()
    assert 'href="costing.html"' not in (tmp_path / "without" / "growth.html").read_text("utf-8")


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


@needs_panels
def test_summary_pages_use_period_sliders_and_carry_the_competition_data(tmp_path):
    records = load_records().records
    evals = load_evaluations(records).evaluations
    growth.build_site(tmp_path, records, evals)
    g = (tmp_path / "growth.html").read_text("utf-8")
    c = (tmp_path / "conditions.html").read_text("utf-8")
    # Each section has its own slider, spanning the years its data cover; there is no page-wide period any more.
    for i in ("conRange", "entRange", "whereRange", "retRange", "indRange", "gspRange"):
        assert f'<div id="{i}"></div>' in g and f'periodSlider("{i}"' in g, i
    assert '<div id="period"></div>' not in g and '<select id="win">' not in g
    for i in ("range", "comRange", "pRange"):
        assert f'<div id="{i}"></div>' in c, i
    gd = json.loads(re.search(r'id="page-data">(.*?)</script>', g, re.S).group(1))
    cd = json.loads(re.search(r'id="page-data">(.*?)</script>', c, re.S).group(1))
    assert {"groups", "sectors", "bizGroup", "concentration"} <= set(gd["barriers"])
    assert {"groups", "sectors", "series", "yields", "markups"} <= set(cd["profit"])
    assert all(w["label"] for w in gd["windows"])


@needs_panels
def test_every_page_source_has_a_link_and_the_concentration_chart_compares_all_industries(tmp_path):
    records = load_records().records
    evals = load_evaluations(records).evaluations
    growth.build_site(tmp_path, records, evals)
    for page in ("growth.html", "conditions.html"):
        html = (tmp_path / page).read_text("utf-8")
        data = json.loads(re.search(r'id="page-data">(.*?)</script>', html, re.S).group(1))
        assert data["sources"] and all(s["url"].startswith("https://") and s["label"] for s in data["sources"].values())
        for key in set(re.findall(r"SRC\(\[([^\]]*)\]\)", html)):
            for k in re.findall(r'"([a-z_]+)"', key):
                assert k in data["sources"], (page, k)
    assert 'class="dumbbell" id="conRows"' in (tmp_path / "growth.html").read_text("utf-8")


@needs_panels
def test_every_chart_that_follows_a_control_can_be_exported_to_excel(tmp_path):
    records = load_records().records
    evals = load_evaluations(records).evaluations
    growth.build_site(tmp_path, records, evals)
    exported = {
        "growth.html": ["gspChart", "heat", "dRank", "shares", "grpChart", "dynChart", "scChart", "conRows"],
        "conditions.html": ["comChart", "roeChart", "sumTable", "mkChart", "muChart", "tsChart", "rbaChart"],
    }
    for page, ids in exported.items():
        html = (tmp_path / page).read_text("utf-8")
        assert "function xlsxWorkbook(" in html and "excelSetup(" in html
        for i in ids:
            assert f'excelButton(cardOf("{i}")' in html, (page, i)
        data = json.loads(re.search(r'id="page-data">(.*?)</script>', html, re.S).group(1))
        assert all("licence" in s for s in data["sources"].values())
        assert data["sources"]["ato"]["licence"] == "CC BY 2.5 AU"
    g = (tmp_path / "growth.html").read_text("utf-8")
    c = (tmp_path / "conditions.html").read_text("utf-8")
    assert '[["dGva", "Output"], ["dEmp", "Jobs"], ["dBiz", "Businesses starting and closing"]].forEach' in g
    assert "for (const c of CHARTS) {\n    excelButton(cardOf(`ch-${c.id}`)" in c


@needs_panels
def test_competition_page_tells_its_story_in_order(tmp_path):
    records = load_records().records
    evals = load_evaluations(records).evaluations
    growth.build_site(tmp_path, records, evals)
    g = (tmp_path / "growth.html").read_text("utf-8")
    assert "<h1>The state of competition in Australia</h1>" in g
    c = (tmp_path / "conditions.html").read_text("utf-8")
    assert '<a href="growth.html">The state of competition in Australia</a>' in c
    # Concentration, business entry, where the barriers are, returns, then industries by state, state economies last.
    ids = ["conRows", "grpChart", "dynChart", "shares", "scChart", "heat", "detailTitle", "gspTable"]
    at = [g.index(f'id="{i}"') for i in ids]
    assert at == sorted(at)
    # Each section's heading is filled in from the data shown.
    for h in ("h-con", "h-entry", "h-where", "h-ret"):
        assert f'setHead("{h}"' in g
    # A card's column never grows past the card, so an opened table scrolls inside it.
    assert re.search(r"\.chart-card \{[^}]*grid-template-columns: minmax\(0, 1fr\)", g)
    data = json.loads(re.search(r'id="page-data">(.*?)</script>', g, re.S).group(1))
    assert all(grp["definition"] and grp["examples"] for grp in data["barriers"]["groups"])
