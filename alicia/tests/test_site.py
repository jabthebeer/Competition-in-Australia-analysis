"""Website summary pages (growth, conditions) built from the committed processed panels."""

from __future__ import annotations

import json
import re
from importlib import resources

import pytest

from alicia.menu import growth, home
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
    # Industries classified differently in other countries carry a hover note (international/concordance.py)
    notes = p["intl"]["notes"]
    assert {"J", "S"} <= set(notes) and "A" not in notes and set(notes) <= set(growth.DIVISIONS)
    assert "computer system design" in notes["J"] and "abs_isic" in p["sources"]
    # Comparisons with similar economies (E-107): series for Australia and the six core peers, by group
    intl = p["intl"]
    assert len(intl["peers"]) == 6 and "AUS" not in intl["peers"]
    assert set(intl["heat"]) <= set(growth.GROWTH_NOTES) | {"gva", "emp", "prod", "entry", "exit", "net"}
    s = intl["series"]["net_entry_rate"]["TRD"]
    assert set(s) >= {"AUS", "OECD"} and all(len(v) == len(intl["years"]) for v in s.values())
    assert all(len(r) == len(intl["years"]) for g in intl["ratings"].values() for r in g.values())
    assert intl["divGroup"]["F"] == intl["divGroup"]["G"] == "TRD" and intl["divGroup"]["TOT"] == "ALL"
    assert {"oecd_sdbs", "oecd_stan", "oecd_pmr", "oecd_stri", "oecd_fdi"} <= set(p["sources"])
    # Levels on the selected industry's charts say whose prices they are in: the chain volume reference year,
    # when volumes equal current prices
    k = p["years"].index(p["cvmRef"])
    for c in ("C", "E", "G"):
        assert abs(p["gva"]["volume"]["AUS"][c][k] - p["gva"]["current"]["AUS"][c][k]) < 1


def test_growth_page_compares_industries_with_similar_economies():
    html = resources.files("alicia.menu").joinpath("templates/growth.html").read_text("utf-8")
    js = resources.files("alicia.menu").joinpath("templates/charts.js").read_text("utf-8")
    # the heatmap column, the by-industry chart, the selected industry's card and the bands on its charts
    assert 'class="peer-th"' in html and "button[data-peer]" in html
    for el in (
        'id="peerChart"',
        'id="peerMeasure"',
        'id="cmpChart"',
        'id="peerToggleBar"',
        'id="gvaKey"',
        'id="empKey"',
    ):
        assert el in html
    assert "peerBand(" in html and "areas" in html and "rangeChart(" in html
    # a Compare with menu beside both comparison charts sets what they draw: the middle half and median, the OECD
    # median, Australia beside a state, and single economies, labelled (not told apart by colour)
    assert html.count("<span data-cmp></span>") == 2
    for el in ('data-k="band"', 'data-k="oecd"', 'data-k="australia"', "data-peer=", "data-reset"):
        assert el in html
    assert "rg-cty-lab" in js and "endLabel" in js and "function rangeDomain" in js
    # the selected industry's productivity, output and jobs charts show an index, a level or growth each year
    for k in ("prod", "gva", "emp"):
        assert f'<select id="{k}Show"></select>' in html
    assert "function modeChart" in html and "function peerGrowth" in html
    # each range row speaks its figures and position, and shows them in words, not colour alone
    assert "aria-label" in js and "RANGE_POS" in js and "function rangeChart" in js and "function quantile7" in js


def test_page_quantile_matches_the_benchmark_engine():
    import shutil
    import subprocess

    if shutil.which("node") is None:
        pytest.skip("Node.js not installed")
    src = resources.files("alicia.menu").joinpath("templates/charts.js").read_text("utf-8")
    fn = re.search(r"function quantile7\(.*?\n}\n", src, re.S).group(0)
    code = "const isNum = (v) => typeof v === 'number' && Number.isFinite(v);" + fn
    code += "console.log(JSON.stringify([0.25, 0.5, 0.75].map((x) => quantile7([3, 1, 4, 1.5, 9, 2.6], x))));"
    out = subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True).stdout
    from alicia.international import benchmark

    assert json.loads(out) == pytest.approx([benchmark.quantile([3, 1, 4, 1.5, 9, 2.6], x) for x in (0.25, 0.5, 0.75)])


def test_comparison_row_scales_are_rounded_and_never_end_on_a_figure():
    import shutil
    import subprocess

    if shutil.which("node") is None:
        pytest.skip("Node.js not installed")
    src = resources.files("alicia.menu").joinpath("templates/charts.js").read_text("utf-8")
    code = "const isNum = (v) => typeof v === 'number' && Number.isFinite(v);"
    for name in ("niceStep", "rangeDomain"):
        code += re.search(rf"function {name}\(.*?\n}}\n", src, re.S).group(0)
    cases = [[-3.6, 0.9, 1.1, 2.2, 0.2], [9.7, 13.0, 12.1, 12.6], [0.23, 0.12, 0.21, 0.27], [5.0, 5.0]]
    code += f"console.log(JSON.stringify({json.dumps(cases)}.map((vs) => rangeDomain(vs))));"
    out = json.loads(subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True).stdout)
    for vs, (lo, hi) in zip(cases, out, strict=True):
        assert lo < min(vs) and hi > max(vs)  # padded: the ends are the scale's, not an economy's
        assert all(abs(v * 100 - round(v * 100)) < 1e-6 for v in (lo, hi))  # and round numbers


@pytest.mark.parametrize("template", ["growth.html"])
def test_page_scripts_parse(template, tmp_path):
    """A syntax error (such as a name declared twice) stops the whole page drawing, so check every script parses.
    Structural competitive conditions carries three: the shared chart code, its own, and the economic conditions'."""
    import shutil
    import subprocess

    if shutil.which("node") is None:
        pytest.skip("Node.js not installed")
    scripts = re.findall(r"<script>(.*?)</script>", growth.render(template, {}, template), re.S)
    assert len(scripts) >= 3
    for i, code in enumerate(scripts):
        (tmp_path / f"{i}.js").write_text(code, "utf-8")
        r = subprocess.run(["node", "--check", str(tmp_path / f"{i}.js")], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr


def test_growth_page_flags_industries_classified_differently_overseas():
    html = resources.files("alicia.menu").joinpath("templates/growth.html").read_text("utf-8")
    js = resources.files("alicia.menu").joinpath("templates/charts.js").read_text("utf-8")
    assert 'class="flag" data-term="intl-' in html and "${intlFlag(c)}${esc(DIVNAME[c])}" in html
    assert 'id="detailFlag"' in html and ".flag[data-term]" in js
    # Flags work like defined words but stay out of the glossary
    assert 'querySelectorAll(".term, .chip[data-term]")' in js


@needs_panels
def test_conditions_payload_series_match_periods_and_mark_major_reforms():
    records = load_records().records
    p = growth.conditions_payload(records)
    for block in (*p["quarterly"].values(), *p["monthly"].values()):
        for values in block["values"].values():
            assert len(values) == len(block["periods"])
    assert set(p["monthly"]["unemp"]["original"]) == {"NT", "ACT"}
    assert "AUS" not in p["quarterly"]["sfd"]["values"]  # state final demand is published for states only
    # Markers are reforms with an overall framework mark of +3 or more, or -3 or less: NSW ride-share (+3) is one;
    # Perth weeknight trading (+1) is not.
    dates = {(r["jurisdiction"], r["date"]) for r in p["reforms"]}
    assert ("NSW", "2015-12-18") in dates and ("WA", "2010-11-01") not in dates
    assert all(abs(r["mark"]) >= growth.MAJOR_MARK for r in p["reforms"])
    assert all(v for v in p["vintages"].values())


def test_render_fills_every_placeholder_and_marks_the_current_page():
    html = growth.render("growth.html", {"x": "</script>"}, "growth.html", standalone=True)
    assert not re.search(r"__[A-Z_]+__", html)
    assert '<a href="growth.html" aria-current="page"' in html and 'class="beta-tip"' in html
    assert "<\\/script>" in html  # embedded data cannot close the script element
    assert html.startswith("<!doctype html>")


@needs_panels
def test_build_site_writes_the_linked_pages_and_nothing_archived(tmp_path):
    records = load_records().records
    evals = load_evaluations(records).evaluations
    paths = growth.build_site(tmp_path, records, evals)
    names = sorted(p.name for p in paths)
    # The live site: no econometric archive and no Policy costing tab (both archived, DECISIONS E-135, E-136).
    assert names == [
        "conditions.html",
        "framework.html",
        "growth.html",
        "index.html",
        "industry-lens.html",
        "menu.html",
        "methodology.html",
    ]
    pages = [n for n in names if n != "conditions.html"]
    index = (tmp_path / "menu.html").read_text("utf-8")
    assert '<a href="menu.html" aria-current="page"' in index and 'href="methodology.html"' in index
    assert 'href="framework.html"' in index
    # Nothing links to the archived pages, or to the old Economic conditions page, which forwards to its place on the
    # competition page.
    for page in pages:
        html = (tmp_path / page).read_text("utf-8")
        assert 'href="conditions.html' not in html and "costing.html" not in html, page
        assert "archive.html" not in html and not re.search(r'href="evaluation-', html), page
        assert "Econometric archive" not in html and "econometric archive" not in html, page
    menu_data = json.loads(re.search(r'id="page-data">(.*?)</script>', index, re.S).group(1))
    assert "archivedEvaluations" not in menu_data and all("archivedEvaluation" not in r for r in menu_data["records"])
    forward = (tmp_path / "conditions.html").read_text("utf-8")
    assert 'location.replace("growth.html#economic-conditions")' in forward and "<nav" not in forward
    # The nav, on one line: the site's name (the link home) with one Beta badge, then the pages grouped by what
    # they are for, under short labels. The regulatory overview is coming soon, with no link.
    nav = index[index.index('<nav class="site-nav"') : index.index("</nav>")]
    assert re.findall(r'<p class="nav-label" id="[^"]+">([^<]+)</p>', nav) == ["Top down", "Bottom up", "About"]
    built = ["index.html", "growth.html", "menu.html", "industry-lens.html", "framework.html", "methodology.html"]
    assert re.findall(r'<a (?:class="brand" )?href="([^"#]+)"', nav) == built
    short = ["Competitive conditions", "Legislative levers", "Industry lens", "Framework", "Methodology"]
    assert re.findall(r'<a href="[^"]+"[^>]*>([^<]+)</a>', nav) == short
    assert 'title="Structural competitive conditions"' in nav  # a short label carries the page's full name
    assert nav.count(">Beta</span>") == 1 and "(beta)</" not in nav  # one badge, not one on every link
    assert 'Regulatory overview <span class="nav-note">(coming soon)</span>' in nav
    assert '<details class="nav-menu" open><summary>Menu</summary>' in nav  # folds behind a Menu button on a phone
    # Every page is the same width: none sets its own.
    for page in pages:
        assert not re.search(r"\.wrap \{[^}]*max-width: (?!1240px)", (tmp_path / page).read_text("utf-8")), page
    # Home: the figures, three questions to start from, then the other pages.
    index_html = (tmp_path / "index.html").read_text("utf-8")
    assert '<a class="brand" href="index.html" aria-current="page"' in index_html
    assert not re.search(r"__[A-Z_]+__", index_html)
    heads = re.findall(r'<h2 id="h-[a-z-]+">([^<]+)</h2>', index_html)
    assert heads == ["Competition at a glance", "Start with a question", "More"]
    routes = re.findall(r'<a class="btn primary"(?: id="pickGo")? href="([^"#]+)', index_html)
    assert routes == ["growth.html", "menu.html", "industry-lens.html"]
    assert all((tmp_path / h).exists() for h in routes)
    assert index_html.count('<a class="tile" href=') == 4 and 'class="site-foot"' in index_html
    assert index_html.count("Coming soon") == 1  # the regulatory overview is not built yet
    assert 'href="regulatory-overview.html"' not in index_html
    assert 'location.replace("menu.html" + location.hash)' in index_html  # old index.html#<id> links reach the menu
    for page in ("framework.html", "menu.html"):  # links into the menu skip the redirect
        assert not re.search(r'href="index\.html#', (tmp_path / page).read_text("utf-8")), page
    fw = (tmp_path / "framework.html").read_text("utf-8")
    assert '<a href="framework.html" aria-current="page"' in fw and not re.search(r"__[A-Z_]+__", fw)
    # Every page's heading ends with "(beta)", with a tip that says it is a work in progress.
    for page in pages:
        html = (tmp_path / page).read_text("utf-8")
        h1 = re.search(r"<h1>(.*?)</h1>", html, re.S).group(1)
        assert h1.rstrip().endswith("</span>") and ">(beta)</button>" in h1 and growth.BETA_TIP in h1, page
    data = re.search(r'id="page-data">(.*?)</script>', (tmp_path / "growth.html").read_text("utf-8"), re.S)
    assert json.loads(data.group(1))["repo"].startswith("https://github.com/")


@needs_panels
def test_the_archived_econometric_pages_are_built_only_when_asked(tmp_path):
    """Archived, not deleted: ``archive=True`` (``alicia site --archive``) still builds the econometric archive and one
    page per evaluation, unchanged; the live site is built without them."""
    records = load_records().records
    evals = load_evaluations(records).evaluations
    names = sorted(p.name for p in growth.build_site(tmp_path, records, evals, archive=True))
    assert "archive.html" in names
    assert sorted(n for n in names if n.startswith("evaluation-")) == sorted(f"evaluation-{e.id}.html" for e in evals)
    one = (tmp_path / "evaluation-childcare-nqf-wa-delay-2012.html").read_text("utf-8")
    payload = json.loads(re.search(r'id="menu-data">(.*?)</script>', one, re.S).group(1))
    assert payload["single"] == "childcare-nqf-wa-delay-2012" and payload["evalPages"]
    assert {r["id"] for r in payload["records"]} == {"cth-nqf-childcare-2012", "wa-nqf-childcare-2012"}
    assert set(payload["evaluations"]) == {"childcare-nqf-wa-delay-2012", "childcare-nqf-2012"}  # follows link
    assert "<title>National Quality Framework" in one
    assert "archive.html#results" in one  # evaluation pages lead back to the archive, not the menu
    archive = (tmp_path / "archive.html").read_text("utf-8")
    assert "Archived 28 October 2026" in archive and '<a href="framework.html">Framework</a>' in archive
    assert '<span class="beta">' not in archive  # the archive is finished, not a work in progress
    assert not re.search(r'href="index\.html#', archive)
    # Even built, the live pages don't link to it.
    assert "archive.html" not in (tmp_path / "menu.html").read_text("utf-8")


def test_home_links_only_pages_that_are_built():
    built = {"growth.html", "menu.html", "industry-lens.html", "framework.html", "methodology.html"}
    routes, more = home.routes_html(built), home.more_html(built)
    assert routes.index("growth.html") < routes.index("menu.html") < routes.index("industry-lens.html")
    assert more.count("Coming soon") == 1 and 'href="regulatory-overview.html"' not in more
    # A new page becomes a link once it is built, and a page that is not built gets no card.
    assert 'href="regulatory-overview.html"' in home.more_html(built | {"regulatory-overview.html"})
    assert home.routes_html({"menu.html"}).count('class="panel route"') == 1


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
    # Archived: the live site is built without it (the Pages workflow passes no --costing), but the code still works.
    for page in ("index.html", "menu.html", "framework.html", "growth.html", "methodology.html"):
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
    c = g  # the economic conditions are at the end of the same page
    # Each section has its own slider, spanning the years its data cover; there is no page-wide period any more.
    for i in ("conRange", "entRange", "whereRange", "retRange", "indRange", "gspRange"):
        assert f'<div id="{i}"></div>' in g and f'periodSlider("{i}"' in g, i
    assert '<div id="period"></div>' not in g and '<select id="win">' not in g
    for i in ("range", "comRange", "pRange"):
        assert f'<div id="{i}"></div>' in c, i
    gd = json.loads(re.search(r'id="page-data">(.*?)</script>', g, re.S).group(1))
    cd = gd["conditions"]
    assert {"groups", "sectors", "bizGroup", "concentration"} <= set(gd["barriers"])
    assert {"groups", "sectors", "series", "yields", "markups"} <= set(cd["profit"])
    assert all(w["label"] for w in gd["windows"])


@needs_panels
def test_every_page_source_has_a_link_and_the_concentration_chart_compares_all_industries(tmp_path):
    records = load_records().records
    evals = load_evaluations(records).evaluations
    growth.build_site(tmp_path, records, evals)
    html = (tmp_path / "growth.html").read_text("utf-8")
    page = json.loads(re.search(r'id="page-data">(.*?)</script>', html, re.S).group(1))
    # The page's two parts (structural conditions, then economic conditions) each carry their own sources.
    split = html.index('const D = JSON.parse(document.getElementById("page-data").textContent).conditions')
    for data, part in ((page, html[:split]), (page["conditions"], html[split:])):
        assert data["sources"] and all(s["url"].startswith("https://") and s["label"] for s in data["sources"].values())
        for key in set(re.findall(r"SRC\(\[([^\]]*)\]\)", part)):
            for k in re.findall(r'"([a-z_]+)"', key):
                assert k in data["sources"], k
    assert 'class="dumbbell" id="conRows"' in (tmp_path / "growth.html").read_text("utf-8")


@needs_panels
def test_every_chart_that_follows_a_control_can_be_exported_to_excel(tmp_path):
    records = load_records().records
    evals = load_evaluations(records).evaluations
    growth.build_site(tmp_path, records, evals)
    ids = [
        *("gspChart", "heat", "dRank", "shares", "grpChart", "dynChart", "scChart", "conRows"),
        *("comChart", "roeChart", "sumTable", "mkChart", "muChart", "tsChart", "rbaChart"),  # economic conditions
    ]
    html = (tmp_path / "growth.html").read_text("utf-8")
    # Each part sets up its own sources; each Excel button keeps the settings it was made with.
    assert "function xlsxWorkbook(" in html and html.count("excelSetup({") == 2 and "const page = XL_PAGE;" in html
    for i in ids:
        assert f'excelButton(cardOf("{i}")' in html, i
    page = json.loads(re.search(r'id="page-data">(.*?)</script>', html, re.S).group(1))
    for data in (page, page["conditions"]):
        assert all("licence" in s for s in data["sources"].values())
        assert data["sources"]["ato"]["licence"] == "CC BY 2.5 AU"
    g = c = html
    assert (
        '[["dGva", "Output", "gva"], ["dEmp", "Jobs", "emp"], ["dBiz", "Businesses starting and closing"]].forEach' in g
    )
    assert "for (const c of CHARTS) {\n    excelButton(cardOf(`ch-${c.id}`)" in c


@needs_panels
def test_competition_page_puts_each_section_in_its_tab(tmp_path):
    records = load_records().records
    evals = load_evaluations(records).evaluations
    growth.build_site(tmp_path, records, evals)
    whole = (tmp_path / "growth.html").read_text("utf-8")
    assert '<h1>Structural competitive conditions <span class="beta">' in whole
    # Six tabs. Every panel but the Overview starts closed; without scripts they all show.
    tabs = [
        ("overview", "Overview"),
        ("entry", "Business entry"),
        ("concentration", "Concentration"),
        ("profits", "Profits and mark-ups"),
        ("industries", "Industries by state"),
        ("backdrop", "Economic backdrop"),
    ]
    markup = whole[: whole.index('<script type="application/json"')]  # the page itself, not its scripts
    found = re.findall(
        r'<button type="button" role="tab" id="tab-(\w+)" aria-controls="panel-\1"[^>]*>([^<]+)<', markup
    )
    assert found == tabs
    panels = re.findall(
        r'<div class="tab-panel" role="tabpanel" id="panel-(\w+)" aria-labelledby="tab-\1"( hidden)?>', whole
    )
    assert panels == [(k, "" if k == "overview" else " hidden") for k, _ in tabs]
    assert "<noscript><style>.tab-panel[hidden] { display: grid !important; }" in whole
    assert "initTabs(document.querySelector('.tabs[role=\"tablist\"]'));" in whole
    sources = whole.index('<details class="shelf" id="sources">')

    def panel(key: str) -> str:
        start = whole.index(f'id="panel-{key}"')
        end = whole.find('<div class="tab-panel"', start)
        return whole[start : end if end > 0 else sources]

    # Each section sits in its tab, in this order. (An id missing from its panel raises.)
    where = {
        "overview": ["h-glance", "h-find", "ovEntry", "ovCon", "ovRet", "h-more"],
        "entry": ["h-entry", "grpChart", "dynChart", "netChart", "h-where", "shares", "secTable"],
        "concentration": ["h-con", "conRows", "conChart"],
        "profits": [
            "h-profit",
            "roeChart",
            "sumTable",
            "mkChart",
            "muChart",
            "tsChart",
            "rbaChart",
            "h-ret",
            "scChart",
        ],
        "industries": [
            "h-ind",
            "heat",
            "peerChart",
            "detailTitle",
            "prodChart",
            "cmpChart",
            "dGva",
            "h-gsp",
            "gspTable",
        ],
        "backdrop": ["economic-conditions", "h-latest", "h-state", "comChart", "h-nat"],
    }
    for key, ids in where.items():
        at = [panel(key).index(f'id="{i}"') for i in ids]
        assert at == sorted(at), key
    # The old Economic conditions address opens its tab: the forward lands on something inside the panel.
    assert '<a href="growth.html#economic-conditions">Structural competitive conditions</a>' in (
        tmp_path / "conditions.html"
    ).read_text("utf-8")
    # Overview: the scorecard's tiles link to the tabs that show them; each finding repeats its section's heading
    # and first sentence; two cards lead to the other tabs.
    over = panel("overview")
    tiles = re.findall(r'<a class="tile" href="#(\w+)"><span class="t-label">([^<]+)</span>', over)
    assert tiles == [
        ("entry", "Business entry"),
        ("entry", "Business exit"),
        ("concentration", "Concentration"),
        ("profits", "Mark-ups"),
        ("profits", "Returns behind barriers"),
    ]
    mirrors = ["h-entry", "entryLede", "h-con", "conLede", "h-ret", "retLede"]
    assert re.findall(r'data-mirror="([\w-]+)"', over) == mirrors
    assert re.findall(r'<a class="more-link" href="#(\w+)"', over) == ["industries", "backdrop"]
    assert re.findall(r'<a class="go" href="#(\w+)"', over) == ["entry", "concentration", "profits"]
    # The two source lists are folded at the foot of the page.
    assert sources < whole.index('id="foot"') < whole.index('id="foot-econ"')
    # The structural part's own script, not the economic conditions'.
    econ_js = whole.rindex("<script>", 0, whole.index(".textContent).conditions"))
    g = whole[whole.index('<script type="application/json"') : econ_js]
    # Each section's heading is filled in from the data shown.
    assert panel("entry").index('<details class="shelf">') < panel("entry").index('id="h-where"')
    for h in ("h-con", "h-entry", "h-where", "h-ret"):
        assert f'setHead("{h}"' in g
    # A card's column never grows past the card, so an opened table scrolls inside it.
    assert re.search(r"\.chart-card \{[^}]*grid-template-columns: minmax\(0, 1fr\)", whole)
    data = json.loads(re.search(r'id="page-data">(.*?)</script>', g, re.S).group(1))
    assert all(grp["definition"] and grp["examples"] for grp in data["barriers"]["groups"])
    # Each group breaks into its sectors: on the entry chart, the starting-and-closing chart and the sectors card.
    for i in ("grpBreak", "grpBars", "dynInd", "dynSec", "secGroup", "secTable"):
        assert f'id="{i}"' in panel("entry"), i
    # In the structural sections, chart descriptions sit behind an "i" beside the title, and every chart's sources
    # are in a dropdown.
    profits = panel("profits")
    structural = (
        panel("entry")
        + panel("concentration")
        + panel("industries")
        + profits[profits.index('aria-labelledby="h-ret"') :]
    )
    for u in re.findall(r'<p class="unit" id="(\w+)"', structural):
        assert f'<p class="unit" id="{u}" hidden>' in structural and f'data-for="{u}"' in structural, u
    assert '<p class="source"' not in re.sub(r"<details.*?</details>", "", structural, flags=re.S)
    # Productivity: in the heatmap's menu, and the official ABS series by industry for the selected industry's card.
    assert '"Productivity growth (output per worker, % a year)"' in g and 'id="pickDiv"' in panel("industries")
    p = data["productivity"]
    assert p["years"][0] == 2005 and {"G", "B", "MKT16"} <= set(p["lp"]) and "Q" not in p["lp"]
    assert data["sources"]["abs_mfp"]["url"].startswith("https://www.abs.gov.au/")
    assert 'excelButton(cardOf("secTable")' in g
