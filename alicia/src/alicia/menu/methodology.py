"""The Methodology page (``methodology.html``): how the site is made, in short, from the methods notes in ``docs/``.

Owner request, 11 November 2026 (DECISIONS E-135): a concise account of the site's methodology, drawn only from the
existing documentation and written to the Australian Government Style Manual. Every count on the page is read from
the register when the site is built, so it can't drift from the data; the methods behind each statement are in the
notes linked at the end.
"""

from __future__ import annotations

from collections import Counter
from html import escape

from ..register import framework
from ..register.bodies import load_bodies
from ..register.recommendations import load_recommendations
from ..register.regimes import load_regimes
from ..register.requirements import load_requirements
from ..register.schema import ChangeRecord
from .growth import COMPETITION_PAGE, FRAMEWORK_PAGE, LENS_PAGE, MENU_PAGE, METHODOLOGY_PAGE, REPO_MAIN, render

# The page's sections, in order: (anchor, heading). The "On this page" row links to each.
SECTIONS = (
    ("what", "What the site does"),
    ("conditions", COMPETITION_PAGE[1]),
    ("levers", MENU_PAGE[1]),
    ("marking", "How each item is marked"),
    ("lens", LENS_PAGE[1]),
    ("checks", "How the site is checked"),
    ("limits", "Limits"),
    ("detail", "More detail"),
)
# The methods notes behind each section, linked at the end (paths in the repository).
NOTES = (
    ("docs/productivity_framework.md", "The productivity framework"),
    ("docs/methods_competition_charts.md", "Barriers to entry, profitability and the competition charts"),
    ("docs/methods_international_benchmarks.md", "International comparisons: harmonisation and comparability"),
    ("docs/international_peers.md", "The similar economies"),
    ("regulation-register/README.md", "The register and its coding protocol"),
    ("docs/responsibility_and_history.md", "Who is responsible, and later changes"),
    ("docs/recommendations.md", "Recommendations"),
    ("docs/industry_regulation.md", "Regulatory complexity by industry"),
    ("docs/industry_lens.md", "The Industry lens"),
    ("docs/methods_legislation_links.md", "Linking legislation to industries"),
    ("docs/fact_check_2026-11.md", "Fact-check of the website, October to November 2026"),
    ("data/SOURCES.md", "Every data source, with its licence"),
)


def counts(records: list[ChangeRecord]) -> dict:
    """The figures the page quotes, read from the register."""
    kinds = Counter(r.kind for r in records)
    requirements = load_requirements().requirements
    recommendations = load_recommendations().recommendations
    covered = {rid for rec in recommendations for rid in rec.applies_to}
    bodies, _ = load_bodies()
    return {
        "items": len(records),
        "reform": kinds.get("reform", 0),
        "setting": kinds.get("setting", 0),
        "barrier": kinds.get("barrier", 0),
        "requirements": len(requirements),
        "recommendations": len(recommendations),
        "covered": len(covered & {r.id for r in records}),
        "regimes": len(load_regimes().regimes),
        "bodies": len(bodies),
        "reviewed": sum(r.review.status == "reviewed" for r in records)
        + sum(q.review.status == "reviewed" for q in requirements),
        "drivers": len(framework.DRIVERS),
        "version": framework.VERSION,
    }


def _section(anchor: str, heading: str, body: str) -> str:
    return (
        f'  <section class="block" aria-labelledby="h-{anchor}">\n'
        f'    <div class="block-head"><h2 id="h-{anchor}">{escape(heading)}</h2></div>\n'
        f"{body}\n  </section>"
    )


def _list(*items: str) -> str:
    return "    <ul>\n" + "".join(f"      <li>{i}</li>\n" for i in items) + "    </ul>"


def body(c: dict, repo: str = REPO_MAIN) -> str:
    """The page's sections as HTML. ``c`` is ``counts()``; ``repo`` is where the methods notes are linked."""
    reviewed = (
        "None has yet been checked by a person."
        if not c["reviewed"]
        else f"{c['reviewed']} of them have been checked by a person so far."
    )
    sections = {
        "what": "\n".join(
            [
                "    <p>ALICIA (Australian Legislation Impact on Competition Industry Analysis) shows where "
                "competition "
                "and business dynamism may be held back in Australia, and which laws and settings may be the cause. "
                "It uses public data and published sources only. It is unofficial research, not an Australian "
                "Government product.</p>",
                _list(
                    f'<strong>Top down.</strong> <a href="{COMPETITION_PAGE[0]}">{COMPETITION_PAGE[1]}</a> describes '
                    f'the economy by state and industry. <a href="{MENU_PAGE[0]}">{MENU_PAGE[1]}</a> lists the laws, '
                    "settings and barriers that shape it.",
                    f'<strong>Bottom up.</strong> The <a href="{LENS_PAGE[0]}">{LENS_PAGE[1]}</a> starts from one '
                    "industry in one state and lists the laws a business in it deals with.",
                    f'<strong>About.</strong> The <a href="{FRAMEWORK_PAGE[0]}">productivity framework</a> sets out '
                    "how "
                    "every law, setting and barrier is marked. This page explains the rest.",
                ),
                f'    <p class="notice"><strong>The register is a draft.</strong> Its {c["items"]} items, '
                f"{c['requirements']} requirements and {c['recommendations']} recommendations were drafted by "
                f"AI-assisted desk research from the sources they cite. {reviewed}</p>",
            ]
        ),
        "conditions": "\n".join(
            [
                "    <p>Descriptive statistics from official sources. They show what happened, not why.</p>",
                _list(
                    "<strong>Output, jobs and productivity</strong> by industry and state come from the ABS State "
                    "Accounts and Labour Force survey. Output per worker is real output divided by the number of "
                    "people "
                    "employed. It counts people, not hours.",
                    "<strong>Business entry and exit</strong> come from ABS Counts of Australian Businesses. A rate is "
                    "the number of businesses that started (or closed) for every 100 operating at the start of the "
                    "year. "
                    "By default, it counts businesses with employees.",
                    "<strong>Concentration and mark-ups</strong> by industry division come from the Reserve Bank of "
                    "Australia's Research Discussion Paper 2025-05, which uses ABS firm-level data that are not "
                    "public.",
                    "<strong>Barriers to entry and profitability.</strong> Every industry class is placed in one of 6 "
                    "groups, following Grattan Institute's <cite>Competition in Australia</cite> (2017). Company "
                    "returns "
                    "come from ATO company tax statistics. Profit above the cost of equity is profit after tax less "
                    "equity times the cost of equity. The cost of equity is the 10-year government bond yield plus "
                    "6 percentage points.",
                    "<strong>Similar economies.</strong> Australia is compared with Canada, France, Italy, New "
                    "Zealand, "
                    "Spain and the United Kingdom: the OECD members most like it in industry structure, income, size "
                    "and trade. The comparison uses 16 industry groups that line up across countries' classifications, "
                    "with OECD and World Bank data and Australia's own figures from the ABS.",
                    "<strong>Economic conditions</strong>, at the end of the page, show the spending, jobs, "
                    "population, "
                    "wages, dwelling approvals and commodity prices each state has faced, from the ABS and the RBA.",
                ),
                '    <p class="note">Profit measures cover companies only. Public data are too aggregated to show '
                "market "
                "shares or mark-ups for single firms or detailed industries.</p>",
            ]
        ),
        "levers": "\n".join(
            [
                f"    <p>A register of {c['items']} items: {c['reform']} reforms, {c['setting']} existing settings and "
                f"{c['barrier']} non-legislative barriers. An item that applies in several jurisdictions has one "
                "record "
                "for each.</p>",
                _list(
                    "A <strong>reform</strong> is a change in law, regulation or policy that is in force, passed or "
                    "proposed. A <strong>setting</strong> is a law, regulation or policy already in place. A "
                    "<strong>barrier</strong> is not a law or policy: it is market structure, conduct or practice that "
                    "limits competition.",
                    "Every date has a source. Dates are checked against the legislation registers that can be read "
                    "automatically: the Commonwealth, Queensland, Tasmania, the ACT, Western Australia and the "
                    "Northern "
                    "Territory. The NSW and SA registers block automated requests, so their dates rest on the sources "
                    "cited.",
                    "Industries are coded to the ABS's ANZSIC 2006 classification, at the most detailed level that "
                    "fits.",
                    f"Each item names the departments, agencies and regulators responsible for it ({c['bodies']} "
                    "bodies), "
                    "from each government's administrative arrangements. Later changes to its law or setting are "
                    "recorded with their sources.",
                    f"{c['recommendations']} recommendations say what government could do about {c['covered']} items. "
                    "Each rests on a review or study that recommends the action, quoted word for word. Items without "
                    "one "
                    "record why.",
                    f"{c['regimes']} regulatory regimes show which tiers of government license, approve, inspect or "
                    "collect in each industry, where tiers overlap and where rules differ between states.",
                ),
            ]
        ),
        "marking": "\n".join(
            [
                "    <p>Every item is marked against the ALICIA productivity framework (version "
                f"{escape(c['version'])}), "
                f"which has {c['drivers']} drivers of productivity.</p>",
                _list(
                    "Each driver is marked from −2 (major harm) to +2 (major gain), with a reason. A driver with a "
                    "small "
                    "or uncertain effect is left at 0.",
                    "A reform is marked against what it replaced. A setting or barrier is marked against the same "
                    "market "
                    "without it.",
                    "The marks add up to an overall mark, read in bands from strongly negative (−3 or less) to "
                    "strongly "
                    "positive (+3 or more). The main driver is the one with the largest mark, either way.",
                    "<strong>Reach</strong> is how much of the economy an item touches: narrow, sector, several "
                    "sectors "
                    "or economy-wide. <strong>Confidence</strong> is high (evaluations or consistent official "
                    "findings), "
                    "medium (official analysis, or evidence from similar reforms) or low (reasoning and desk "
                    "research).",
                    "Marks are judgements about likely effects, not estimates. They weigh productivity and competition "
                    "only, not a rule's benefits for health, safety, the environment or fairness.",
                ),
                f'    <p>The <a href="{FRAMEWORK_PAGE[0]}">Framework</a> page has the drivers and the full marking '
                "guide.</p>",
            ]
        ),
        "lens": "\n".join(
            [
                "    <p>The laws a business in one industry deals with, in one state or territory.</p>",
                _list(
                    f"{c['requirements']} requirements, each one obligation in one jurisdiction: for example, to "
                    "register, hold a licence, get an approval, pay a tax, report or meet a standard.",
                    "Each requirement quotes its law from the official register. For NSW and SA, the quote may come "
                    "from the Open Australian Legal Corpus's copy of the official text. That copy is not official and "
                    "was last updated in March 2025. A few drafts quote the official Australian Business Licence and "
                    "Information Service (ABLIS) until the law itself is quoted.",
                    "Each requirement reaches the industry classes its law covers, read from the law's scope or from "
                    "official guidance that names the industry. Confidence is high where the law names the activity, "
                    "medium where official guidance does, and low where it is inferred from the ABS class definition.",
                    "Each law is marked against the framework. Each mark is shown under the market players it acts "
                    "through: businesses entering the market, small and medium competitors, or the largest players.",
                    "The market figures above each column (business counts, entry and exit rates, sales by business "
                    "size and four-firm concentration) come from the ABS and the RBA. Each states its level and year, "
                    "because no public source gives market shares for one industry in one state.",
                ),
                '    <p class="note">Coverage is uneven, and councils are capital cities only. A short list means '
                "not yet recorded, not no regulation.</p>",
            ]
        ),
        "checks": _list(
            "Automated tests recompute the figures on each page from the source files by a separate route.",
            "Before each build, every register item, requirement and recommendation is checked against its "
            "schema: its industry codes, dates, responsible bodies, framework marks and links.",
            "A fact-check from 29 October to 6 November 2026 compared the register's dates, and other claims on "
            "the site, with their sources and corrected 1 date. Claims whose official sources block automated "
            "access are waiting for a person to check them.",
            "The site is rebuilt after every change, and daily, when the data behind the industry statistics are "
            "checked against the publishers' latest releases.",
        ),
        "limits": _list(
            "<strong>Drafts.</strong> Records, requirements, recommendations and marks are drafts until a person "
            "has checked them.",
            "<strong>Productivity and competition only.</strong> A negative mark is a productivity cost to weigh "
            "against a rule's benefits. It is not a finding that the rule should go.",
            "<strong>Descriptive statistics.</strong> None of the charts identifies cause and effect.",
            "<strong>Public data only.</strong> The site uses no firm-level data, such as the ABS's restricted "
            "Business Longitudinal Analysis Data Environment (BLADE).",
            "<strong>Econometric evaluations.</strong> The evaluations the site used to show were paused on "
            "22 October 2026 and are no longer on the site. Their files stay, unchanged and provisional, in the "
            "project's repository.",
        ),
        "detail": _list(
            *(f'<a href="{escape(repo)}{escape(path)}">{escape(label)}</a>' for path, label in NOTES),
        ),
    }
    return "\n\n".join(_section(a, h, sections[a]) for a, h in SECTIONS)


def toc() -> str:
    links = "".join(f'\n      <a href="#h-{a}">{escape(h)}</a>' for a, h in SECTIONS)
    label = '<span class="toc-label">On this page</span>'
    return f'<nav class="toc" aria-label="On this page">\n      {label}{links}\n    </nav>'


def page(records: list[ChangeRecord], standalone: bool, pages: tuple, repo: str = REPO_MAIN) -> str:
    html = render(METHODOLOGY_PAGE[0], {}, METHODOLOGY_PAGE[0], standalone, pages)
    content = '<main class="method-body">\n' + body(counts(records), repo) + "\n</main>"
    return html.replace("<!--__TOC__-->", toc()).replace("<!--__BODY__-->", content)
