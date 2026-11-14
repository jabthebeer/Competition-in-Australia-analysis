"""The Home page (``index.html``): what ALICIA is, the state of play in a few figures, and three questions to
start from.

Owner decision, 14 November 2026 (DECISIONS E-159; plan in ``docs/plan_site_overhaul.md``). The page's end goal is
to tell a new reader what the site is and get them to the right page in one click. Every figure is worked out here
from the data the other pages show, when the site is built, so it can't drift from them; ``tests/test_home.py``
recomputes each one by a separate route.
"""

from __future__ import annotations

import datetime as dt
from html import escape

from ..pipeline import schema
from .figures import business_rates, concentration, fy, markups
from .growth import (
    COMPETITION_PAGE,
    FRAMEWORK_PAGE,
    HOME_PAGE,
    LENS_PAGE,
    MENU_PAGE,
    METHODOLOGY_PAGE,
    OVERVIEW_PAGE,
    PAGES,
    STATE_SHORT,
    _division_list,
    render,
    site_foot,
)

# The lens opens on this industry and state unless the reader picks others (the lens's own default).
PICK_DIVISION, PICK_STATE = "H", "NSW"


def _figure(label: str, value: str, what: str, source: str, href: str) -> dict:
    return {"label": label, "value": value, "what": what, "source": source, "href": href}


def figures(growth: dict, menu: dict) -> list[dict]:
    """The Home page's key figures: a label, the value, what it is, its source and the page that shows it. A figure
    whose data is missing is left out."""
    out = []
    rba = "RBA, Research Discussion Paper 2025-05"
    entry = business_rates(growth, "entries")
    if entry:
        (y0, v0), (y1, v1) = entry
        what = (
            f"New businesses with employees in {fy(y1)}, as a share of those operating at the start of the year. "
            f"The rate was {v0:.1f}% in {fy(y0)}."
        )
        out.append(
            _figure("New businesses", f"{v1:.1f}%", what, "ABS, Counts of Australian Businesses", COMPETITION_PAGE[0])
        )
    top4 = concentration(growth)
    if top4:
        (y0, v0), (y1, v1) = top4
        what = f"The 4 largest firms' share of sales in the average industry in {y1}. The share was {v0:.1f}% in {y0}."
        out.append(_figure("Concentration", f"{v1:.1f}%", what, rba, COMPETITION_PAGE[0]))
    ups = markups(growth)
    if ups:
        (y0, v0), (y1, v1) = ups
        what = f"The average ratio of price to marginal cost in {y1}. It was {v0:.2f} in {y0}."
        out.append(_figure("Mark-ups", f"{v1:.2f}", what, rba, COMPETITION_PAGE[0]))
    items = menu.get("records", [])
    if items:
        negative = sum(1 for r in items if ((r.get("assessment") or {}).get("total") or 0) < 0)
        what = (
            f"of the {len(items):,} laws, requirements and market barriers in the register are marked as weighing "
            "on productivity."
        )
        out.append(_figure("Barriers on record", f"{negative:,}", what, "ALICIA register (draft)", MENU_PAGE[0]))
    return out


def figures_html(figs: list[dict]) -> str:
    return "\n      ".join(
        f'<a class="tile" href="{escape(f["href"])}"><span class="t-label">{escape(f["label"])}</span>'
        f'<span class="t-value">{escape(f["value"])}</span><span class="t-sub">{escape(f["what"])}</span>'
        f'<span class="t-src">{escape(f["source"])}</span></a>'
        for f in figs
    )


def _options(pairs, selected: str) -> str:
    return "".join(
        f'<option value="{escape(code)}"{" selected" if code == selected else ""}>{escape(name)}</option>'
        for code, name in pairs
    )


def routes_html(built: set[str]) -> str:
    """The three questions a reader can start from, each with the page that answers it. The third picks an industry
    and a state for the Industry lens. A page this build does not write is left out."""
    cards = []
    if COMPETITION_PAGE[0] in built:
        cards.append(
            '<div class="panel route"><p class="route-view">Top down</p>'
            "<h3>How competitive is Australia's economy?</h3>"
            "<p>Business entry, concentration, mark-ups and profits by state and industry, compared with similar "
            "economies.</p>"
            f'<a class="btn primary" href="{COMPETITION_PAGE[0]}">Open {escape(COMPETITION_PAGE[1])}</a></div>'
        )
    if MENU_PAGE[0] in built:
        cards.append(
            '<div class="panel route"><p class="route-view">Top down</p>'
            "<h3>What holds competition back?</h3>"
            "<p>Laws, business requirements and other barriers that affect competition, each marked against the "
            "productivity framework.</p>"
            f'<a class="btn primary" href="{MENU_PAGE[0]}">Open Legislative levers</a></div>'
        )
    if LENS_PAGE[0] in built:
        divisions = [(d["code"], d["name"]) for d in _division_list() if len(d["code"]) == 1]
        states = [(s, STATE_SHORT[s]) for s in schema.STATES]
        cards.append(
            '<div class="panel route"><p class="route-view">Bottom up</p>'
            "<h3>What does a business in my industry face?</h3>"
            '<div class="route-pick">'
            f'<div class="field"><label for="pickInd">Industry</label><select id="pickInd">'
            f"{_options(divisions, PICK_DIVISION)}</select></div>"
            f'<div class="field"><label for="pickState">State or territory</label><select id="pickState">'
            f"{_options(states, PICK_STATE)}</select></div></div>"
            f'<a class="btn primary" id="pickGo" href="{LENS_PAGE[0]}#division={PICK_DIVISION}&amp;state={PICK_STATE}">'
            "See this industry</a></div>"
        )
    return "\n      ".join(cards)


def more_html(built: set[str]) -> str:
    """The other pages. One this build does not write shows as coming soon, without a link."""
    items = (
        (OVERVIEW_PAGE, "Compare industries by the regulation they face."),
        ((FRAMEWORK_PAGE[0], "Productivity framework"), "How every law and barrier is marked."),
        (METHODOLOGY_PAGE, "Where the figures come from, and their limits."),
    )
    out = []
    for (href, name), text in items:
        if href in built:
            out.append(
                f'<a class="more-link" href="{href}"><span class="name">{escape(name)}</span>'
                f'<span class="desc">{escape(text)}</span></a>'
            )
        else:
            out.append(
                f'<div class="more-link soon"><span class="name">{escape(name)}<span class="badge">Coming soon</span>'
                f'</span><span class="desc">{escape(text)}</span></div>'
            )
    return "\n      ".join(out)


def page(
    growth: dict,
    menu: dict,
    built: set[str],
    standalone: bool = True,
    pages: tuple = PAGES,
    generated: dt.date | None = None,
) -> str:
    """The Home page. ``growth`` is the competition page's data (with the economic conditions under
    ``conditions``), ``menu`` the levers page's, and ``built`` the pages this build writes."""
    html = render("home.html", {}, HOME_PAGE[0], standalone, pages)
    return (
        html.replace("<!--__FIGURES__-->", figures_html(figures(growth, menu)))
        .replace("<!--__ROUTES__-->", routes_html(built))
        .replace("<!--__MORE__-->", more_html(built))
        .replace("<!--__FOOT__-->", site_foot(generated))
    )
