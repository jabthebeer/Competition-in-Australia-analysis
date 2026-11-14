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


def test_the_page_leads_with_the_worked_example():
    """Owner, 14 November 2026 (DECISIONS E-159, E-182): the Framework page opens with how to read a mark, on one
    worked example, and says that version 2 is being built."""
    html = page.body(load_records().records)
    order = ["h-example", "h-fit", "h-rubric", "h-how", "h-overlap", "h-ideas", "h-limits"]
    at = [html.index(f'id="{i}"') for i in order]
    assert at == sorted(at)
    assert "How to read a mark: a worked example" in html
    assert html.index("is being revised") < html.index('id="h-example"') and "Biggest barriers" in html


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
