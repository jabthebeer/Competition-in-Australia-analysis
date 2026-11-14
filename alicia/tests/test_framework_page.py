"""The Framework page: the framework as pictures, tables and a rubric, with more detail on hover (offline)."""

from __future__ import annotations

import re

from alicia.menu import framework as page
from alicia.register import framework as fw
from alicia.register.catalogue import load_records


def _body():
    records = load_records().records
    return records, page.body(records)


def test_every_component_with_detail_points_at_a_hidden_detail():
    _, html = _body()
    tips = re.findall(r'data-tip="(tip-\d+)" aria-describedby="\1"', html)
    details = set(re.findall(r'<div id="(tip-\d+)">', html.split('<div class="tip-srcs" hidden>')[1]))
    assert tips and set(tips) == details and len(tips) == len(set(tips))


def test_the_rubric_has_a_row_per_driver_and_counts_every_mark():
    records, html = _body()
    for key in fw.DRIVERS:
        row = re.search(rf'<tr id="r-{key}">(.*?)</tr>', html, re.S).group(1)
        assert len(re.findall(r'<td class="c ', row)) == 5, key
        marked = sum(1 for r in records for m in r.assessment.marks if m.driver == key)
        counted = sum(int(n) for n in re.findall(r'<span class="n">(\d+) items?</span>', row))
        assert counted == marked, key
        assert fw.DRIVERS[key]["plain"] in row


def test_the_page_draws_the_ideas_with_icons_and_plain_words():
    _, html = _body()
    for c in fw.CONCEPTS:
        assert c["plain"] in html and page.CONCEPT_ICONS[c["key"]] in page.ICONS
    for k in [*fw.DRIVERS, *fw.KINDS, *page.STEP_ICONS, *page.LIMIT_ICONS, *page.SIGN_ICONS.values()]:
        assert k in page.ICONS, k
    assert all(s["figure"] in html for s in fw.SIGNS)
    assert all(t in html for t, _ in fw.STEP_TITLES) and all(t in html for t in fw.CAVEAT_TITLES)
    assert 'id="h-example"' in html and 'class="strip"' in html  # the worked example on the rubric
    assert all(f'id="d-{k}"' in html for k in fw.DRIVERS)  # each driver's evidence, folded away


def test_render_includes_the_tooltip_code_and_fills_every_placeholder():
    records = load_records().records
    html = page.render(records, "<nav></nav>")
    assert "function showTipAt" in html and "data-tip" in html
    assert not re.search(r"__[A-Z_]+__", html)


def test_the_page_leads_with_how_much_a_rule_matters_then_the_worked_example():
    """Owner, 14 November 2026 (DECISIONS E-182, E-185): the Framework page opens with version 2's three questions
    and four impact classes, then how to read a mark on one worked example, then the eight drivers."""
    from alicia.register import severity as S

    html = page.body(load_records().records, classes={"severe": 2, "major-wide": 55, "major-narrow": 168, "minor": 372})
    order = ["h-v2", "h-classes", "h-judgement", "h-example", "h-fit", "h-rubric", "h-how", "h-overlap", "h-limits"]
    at = [html.index(f'id="{i}"') for i in order]
    assert at == sorted(at)
    assert [re.sub(r"<[^>]+>", "", q) for q in re.findall(r"<h3>(.*?)</h3>", html[: at[1]])] == [
        q["question"] for q in fw.QUESTIONS
    ]
    # The 2 x 2 grid: large effect over smaller, small set of industries before wide, each with its count.
    grid = html[at[1] : at[2]]
    tiles = re.findall(r'<span class="t-label">([^<]+)</span><span class="t-value">(\d+)</span>', grid)
    assert tiles == [("Major, narrow", "168"), ("Severe", "2"), ("Minor", "372"), ("Major, wide", "55")]
    assert f"<td>Kind: {S.KIND_LABELS['cap'][0].lower()}" in html and "is being revised" not in html
    assert "How to read a mark: a worked example" in html and fw.VERSION == "2.0"
    # Without counts (a page built on its own), the grid still shows the classes.
    assert '<span class="t-value">' not in page.version_two().split('id="h-classes"')[1].split("</section>")[0]


def test_the_methodology_page_leads_with_how_far_to_rely_on_each_part():
    from alicia.menu import growth, methodology

    html = methodology.page(load_records().records, True, growth.PAGES)
    heads = re.findall(r'<h2 id="h-(\w+)">', html)
    assert heads[0] == "rely" and heads == [a for a, _ in methodology.SECTIONS]
    rows = re.findall(r"(?s)<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>", html)
    assert len(rows) == len(methodology.RELIANCE) and all(all(cell for cell in r) for r in rows)
    # Official statistics come first; the draft judgements and what others recommend come last.
    assert rows[0][0].startswith("Business counts") and rows[-1][0] == "What others recommend"
    assert "regulatory-overview.html" in html
