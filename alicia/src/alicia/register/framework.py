"""The ALICIA productivity impact framework: how a law, regulatory setting or other barrier is marked for its
likely effect on productivity and competition in Australia.

One definition, used by the register's validation (``register/schema.py``), the website's legislation menu and
framework page (``menu/explorer.py``, ``menu/framework.py``) and the methods note (``alicia framework``,
``docs/productivity_framework.md``). Owner request, 28 October 2026 (DECISIONS E-87).

Each item in the register gets a mark from -2 to +2 on each of eight drivers of productivity. Marks are judgements
from desk research and the evidence cited, not estimates: the Policy costing tab quantifies. The drivers follow
the productivity channels the Productivity Commission and the Treasury use, and each maps to the costing tab's
channels (C1 to C11), so a qualitative mark and a costing describe the same mechanism.
"""

from __future__ import annotations

from typing import Literal

VERSION = "1.0"
ADOPTED = "2026-10-28"

Driver = Literal[
    "entry-exit",
    "competition",
    "market-integration",
    "capital",
    "labour",
    "burden",
    "innovation",
    "prices-taxes",
]
Reach = Literal["narrow", "sector", "multi-sector", "economy-wide"]
Confidence = Literal["high", "medium", "low"]
# What kind of item a register record is. A reform is a change in law, regulation or policy (in force, passed or
# proposed); a setting is a law, regulation or government policy already in place, marked against its absence; a
# barrier is something that is not a law or policy (market structure, conduct, practice) that limits competition.
Kind = Literal["reform", "setting", "barrier"]

PILLARS: dict[str, dict] = {
    "dynamism": {
        "label": "Competition and dynamism",
        "question": "Who gets to compete, and how hard?",
    },
    "inputs": {
        "label": "Investment and people",
        "question": "How much capital and skill do firms work with, and can they move to where they earn most?",
    },
    "efficiency": {
        "label": "Efficiency",
        "question": "How well are labour and capital used once in place?",
    },
}

# Source keys used below; full references in SOURCES.
DRIVERS: dict[str, dict] = {
    "entry-exit": {
        "label": "Entry, exit and scale-up",
        "short": "Entry and exit",
        "pillar": "dynamism",
        "question": "Does it change how easily new firms can start, small firms can grow and failing firms can close?",
        "why": (
            "New firms bring new products and methods, and push incumbents to keep up. Australia's business entry "
            "rate fell from 14.5% to 11.5% between 2004 and 2016, and that fall explains about three quarters of the "
            "slowdown in how fast firms catch up to the most productive ones."
        ),
        "why_sources": ("andrews2022", "pc2025"),
        "look_for": (
            "licences, permits and accreditation needed to start",
            "caps on numbers, moratoriums, location or ownership rules, exclusive rights",
            "approval times and fees for new businesses",
            "size thresholds that switch on costs as firms grow",
            "insolvency, restructuring and other exit costs",
        ),
        "marks": {
            2: "Removes a cap, exclusive right, moratorium or ban on entry",
            1: "Lowers the cost, time or conditions of entry, growth or exit",
            -1: "Adds a cost, condition or delay for new or growing firms",
            -2: "Creates or entrenches a cap, exclusive right, moratorium or ban on entry",
        },
        "channels": ("C4", "C5"),
    },
    "competition": {
        "label": "Competitive pressure",
        "short": "Competition",
        "pillar": "dynamism",
        "question": "Does it change how hard existing firms must compete on price, quality and service?",
        "why": (
            "Rivalry pushes firms to cut costs, improve and pass gains on. Mark-ups in Australia rose from about 1.18 "
            "to 1.25 between the mid-2000s and mid-2010s, and the RBA estimates productivity would be 1 to 3% "
            "higher with the competition of the mid-2000s."
        ),
        "why_sources": ("hf2025", "oecd_cat"),
        "look_for": (
            "rules on prices, advertising, trading hours or business models",
            "exemptions from competition law, or collective price setting",
            "merger rules and rules on misuse of market power",
            "switching costs, and the information customers have to compare offers",
            "state-owned or licensed monopolies after entry",
        ),
        "marks": {
            2: "Opens a concentrated market to strong rivalry, or removes a major restriction on how firms compete",
            1: "Strengthens rivalry modestly: easier switching, better information, stronger enforcement",
            -1: "Dampens rivalry: limits on conduct, coordination made easier, shelter from competition law",
            -2: "Shields incumbents from competition: a statutory monopoly, cartel-like price setting",
        },
        "channels": ("C6", "C7"),
    },
    "market-integration": {
        "label": "Trade and market integration",
        "short": "Market integration",
        "pillar": "dynamism",
        "question": (
            "Does it change how large a market firms can serve, and how open it is to rivals from other states and "
            "countries?"
        ),
        "why": (
            "Bigger, more open markets let the best firms grow and expose the rest to competition. Across OECD "
            "countries, greater trade openness raises multifactor productivity; the Productivity Commission "
            "estimates that removing Australia's remaining tariffs would add 0.13 to 0.25% to GDP."
        ),
        "why_sources": ("egert_gal", "pc2024ncp", "pc2023v3"),
        "look_for": (
            "tariffs, anti-dumping duties, cabotage and local-content rules",
            "foreign investment screening and ownership limits",
            "standards that differ from international ones",
            "state-by-state licences and rules; mutual recognition and national laws",
        ),
        "marks": {
            2: "Removes a major barrier between states, or to international trade or investment",
            1: "Harmonises rules across jurisdictions, or recognises other jurisdictions' approvals",
            -1: "Adds a jurisdiction-specific rule, or a restriction on imports or foreign investment",
            -2: "Closes a market to interstate or foreign competitors",
        },
        "channels": ("C10",),
    },
    "capital": {
        "label": "Capital deepening",
        "short": "Capital",
        "pillar": "inputs",
        "question": (
            "Does it change firms' incentive or ability to invest in equipment, buildings, software and other capital?"
        ),
        "why": (
            "Workers produce more with more and better capital. Non-mining business investment has fallen by about "
            "3 percentage points of GDP since the global financial crisis; the Productivity Commission estimates "
            "its company tax package would lift investment by 2.2% and labour productivity by 0.5%."
        ),
        "why_sources": ("pc2025", "hambur_andrews2023"),
        "look_for": (
            "company tax rate and base, depreciation and expensing",
            "approval times for investment projects",
            "regulatory uncertainty and sovereign risk",
            "access to finance; rules on how assets may be used",
        ),
        "marks": {
            2: "Raises the after-tax return on, or certainty of, investment across many industries",
            1: "Lowers the cost, risk or approval time of investing in an industry",
            -1: "Raises the cost, risk or delay of investing",
            -2: "A major deterrent to investment: a large new tax on capital, expropriation risk, open-ended delays",
        },
        "channels": ("C3", "C2"),
    },
    "labour": {
        "label": "Labour mobility and skills",
        "short": "Labour and skills",
        "pillar": "inputs",
        "question": (
            "Does it change workers' ability to move to more productive jobs, firms and places, or to gain skills?"
        ),
        "why": (
            "Moving workers to where they are most productive raises output without extra inputs. Weaker job "
            "reallocation took about 0.15 percentage points a year off labour productivity growth by 2016, and about "
            "24% of workers are in occupations that need a licence."
        ),
        "why_sources": ("andrews_hansell", "pc2023v7", "pc2024ncp"),
        "look_for": (
            "occupational licensing, and whether a licence is valid in other states",
            "non-compete, no-poach and similar clauses",
            "migration and visa settings",
            "funding and quality of training",
            "workplace rules that limit how jobs can be organised",
        ),
        "marks": {
            2: "Removes a major barrier to moving between jobs, occupations or states for many workers",
            1: "Eases mobility or lifts skills in an industry",
            -1: "Adds a restriction or cost to moving jobs, or narrows the pool of workers firms can hire",
            -2: "Locks large numbers of workers out of occupations or jobs",
        },
        "channels": ("C8",),
    },
    "burden": {
        "label": "Regulatory burden",
        "short": "Regulatory burden",
        "pillar": "efficiency",
        "question": (
            "Does it change the time and money firms spend complying with rules, including waiting for decisions?"
        ),
        "why": (
            "Staff time and spending on compliance produce no measured output. The Productivity Commission puts the "
            "compliance and delay costs of Australian Government regulation at about $115 to $160 billion a year, "
            "and recommends cutting them by $10 billion by 2030."
        ),
        "why_sources": ("pc2025", "oia_rbm"),
        "look_for": (
            "new reporting, record-keeping, audits and approvals",
            "the same thing regulated by several governments",
            "complexity, and frequent changes to the rules",
            "removal of redundant rules; digital lodgement",
        ),
        "marks": {
            2: "Removes or streamlines a large burden on many firms",
            1: "Cuts compliance time or cost",
            -1: "Adds compliance or delay costs",
            -2: "Large new compliance or delay costs: a material share of revenue, or delays of years",
        },
        "channels": ("C1", "C2"),
    },
    "innovation": {
        "label": "Innovation and technology diffusion",
        "short": "Innovation",
        "pillar": "efficiency",
        "question": (
            "Does it change incentives and freedom to develop new products, adopt better technology or try new "
            "business models?"
        ),
        "why": (
            "Most Australian firms sit well below the productivity frontier, and the spread of better methods from "
            "leading firms to the rest has slowed. Rules written around one technology or business model can lock "
            "out better ones."
        ),
        "why_sources": ("pc2023v5", "andrews2022"),
        "look_for": (
            "R&D incentives",
            "rules written around one technology or business model",
            "bans on, or approvals for, new products and services",
            "access to data, interoperability and the right to repair",
        ),
        "marks": {
            2: "Legalises or enables a new technology or business model across an industry",
            1: "Eases adoption of better technology, or raises incentives to innovate",
            -1: "Locks in incumbent technology, or adds approval hurdles for new products",
            -2: "Bans a new technology or business model",
        },
        "channels": ("C9",),
    },
    "prices-taxes": {
        "label": "Price and tax signals",
        "short": "Prices and taxes",
        "pillar": "efficiency",
        "question": "Does it change whether prices reflect costs, so that resources go where they are most valued?",
        "why": (
            "Taxes, subsidies and price controls that bend prices away from costs send labour and capital to the "
            "wrong uses. Treasury estimates that each extra dollar raised by stamp duty on property transfers costs "
            "the economy 72 cents in lost efficiency, while a broad land tax costs close to nothing."
        ),
        "why_sources": ("cao2015", "oia_comp"),
        "look_for": (
            "price caps, price floors and regulated tariffs",
            "subsidies and levies that favour some firms or products",
            "taxes on transactions, such as stamp duty",
            "cross-subsidies, and the cost of funding public spending",
        ),
        "marks": {
            2: "Replaces a highly distorting tax, subsidy or price control with an efficient one",
            1: "Moves prices closer to costs",
            -1: "Adds a modest distortion: a levy, a targeted subsidy, a cap or floor that binds",
            -2: "A large distortion in a major market: transaction taxes on property, binding price controls",
        },
        "channels": ("C11",),
    },
}

MARK_LABELS: dict[int, str] = {2: "Major gain", 1: "Gain", 0: "No material effect", -1: "Harm", -2: "Major harm"}

# Bands for the overall mark (the sum of the driver marks).
RATINGS: tuple[tuple[int, str, str], ...] = (
    (3, "strongly-positive", "Strongly positive"),
    (1, "positive", "Positive"),
    (0, "neutral", "Neutral or offsetting"),
    (-2, "negative", "Negative"),
    (-99, "strongly-negative", "Strongly negative"),
)
RATING_LABELS: dict[str, str] = {k: label for _, k, label in RATINGS}

REACH: dict[str, dict] = {
    "narrow": {"label": "Narrow", "help": "One detailed industry or activity, such as small bars or taxis"},
    "sector": {"label": "Sector", "help": "One broad industry, or a few related detailed industries"},
    "multi-sector": {"label": "Several sectors", "help": "Several broad industries, or many occupations"},
    "economy-wide": {"label": "Economy-wide", "help": "All or most industries"},
}
CONFIDENCE: dict[str, dict] = {
    "high": {"label": "High", "help": "Ex post evaluations or consistent official findings about this setting"},
    "medium": {
        "label": "Medium",
        "help": "Official ex ante analysis, or strong evidence from similar reforms elsewhere",
    },
    "low": {"label": "Low", "help": "Economic reasoning and desk research only"},
}
KINDS: dict[str, dict] = {
    "reform": {"label": "Reform", "help": "A change in law, regulation or policy: in force, passed or proposed"},
    "setting": {"label": "Existing setting", "help": "A law, regulation or government policy already in place"},
    "barrier": {
        "label": "Non-legislative barrier",
        "help": "Not a law or policy: market structure, business conduct or practice that limits competition",
    },
}

STEPS: tuple[str, ...] = (
    "Describe the item and what it changes, with its sources.",
    "Mark each of the eight drivers from −2 to +2, with a one-line reason for every mark that is not zero. Leave a "
    "driver at zero when the effect is small or speculative.",
    "Add the marks to get the overall mark, and read its band: strongly positive (+3 or more), positive (+1 or +2), "
    "neutral or offsetting (0), negative (−1 or −2), strongly negative (−3 or less). An item with both positive and "
    "negative marks is flagged as mixed.",
    "Name the main driver: the driver with the largest mark, either way. Where two tie, the assessor picks the one "
    "the evidence says matters more.",
    "Rate the reach (narrow, sector, several sectors, economy-wide) and the confidence (high, medium, low).",
)
COUNTERFACTUAL = (
    "A reform is marked against the settings it replaced or would replace. An existing setting or barrier is marked "
    "against the same market without it."
)
OVERLAP_RULES: tuple[str, ...] = (
    "A licence a new firm needs before it can start is marked under entry and exit; the ongoing paperwork it brings "
    "is regulatory burden.",
    "An occupational licence is marked under labour mobility (as the Productivity Commission costs it), and under "
    "entry and exit only if it caps the number of businesses.",
    "A tax change is marked under capital deepening when it changes the return on investment, and under price and "
    "tax signals when it distorts a transaction or a choice between products. Mark both only when both effects "
    "are material.",
    "A rule that restrains market power is marked under competitive pressure; whether the resulting prices still "
    "cover costs is marked under price and tax signals.",
)
CAVEATS: tuple[str, ...] = (
    "Marks cover productivity and competition only. Many rules protect health, safety, the environment or fairness, "
    "and those benefits are not weighed here. A negative mark is not a finding that a rule should go: it is a "
    "productivity cost to weigh against its benefits, as the Office of Impact Analysis's competition tests ask.",
    "Marks are ordinal judgements, not estimates. Adding them is a summary device: a +2 is not exactly twice a +1. "
    "Use the Policy costing tab for dollar figures.",
    "Assessments were drafted by AI-assisted desk research from each record's sources and have not yet been "
    "checked by a person.",
    "Reach describes how much of the economy an item touches, not the size of its effect there; a state law reaches "
    "only that state.",
)

SOURCES: dict[str, dict] = {
    "pc2023": {
        "label": "Productivity Commission (2023), Advancing Prosperity: 5-year Productivity Inquiry report",
        "url": "https://www.pc.gov.au/inquiries-and-research/productivity/report",
    },
    "pc2023v3": {
        "label": "Productivity Commission (2023), Advancing Prosperity, Vol. 3: A competitive, dynamic and "
        "sustainable future",
        "url": "https://assets.pc.gov.au/inquiries/completed/productivity/report/productivity-volume3-future.pdf",
    },
    "pc2023v5": {
        "label": "Productivity Commission (2023), Advancing Prosperity, Vol. 5: Innovation for the 98%",
        "url": "https://assets.pc.gov.au/inquiries/completed/productivity/report/productivity-volume5-innovation-diffusion.pdf",
    },
    "pc2023v7": {
        "label": "Productivity Commission (2023), Advancing Prosperity, Vol. 7: A more productive labour market",
        "url": "https://assets.pc.gov.au/inquiries/completed/productivity/report/productivity-volume7-labour-market.pdf",
    },
    "pc2024ncp": {
        "label": "Productivity Commission (2024), National Competition Policy: modelling proposed reforms",
        "url": "https://www.pc.gov.au/inquiries-and-research/competition-analysis/report",
    },
    "pc2025": {
        "label": "Productivity Commission (2025), Creating a more dynamic and resilient economy, inquiry report",
        "url": "https://www.pc.gov.au/inquiries-and-research/resilient-economy/report/",
    },
    "oia_comp": {
        "label": "Office of Impact Analysis (2026), How to consider competition in impact analysis",
        "url": "https://oia.pmc.gov.au/sites/default/files/2026-06/competition-guidance.pdf",
    },
    "oia_rbm": {
        "label": "Office of Impact Analysis, Regulatory Burden Measurement Framework",
        "url": "https://oia.pmc.gov.au/resources/regulatory-burden-measurement-framework",
    },
    "oecd_cat": {
        "label": "OECD (2019), Competition Assessment Toolkit: Principles, version 4.0",
        "url": "https://www.oecd.org/en/publications/competition-assessment-toolkit-principles-version-4-0-volume-i_5f9fa6ca-en.html",
    },
    "andrews2022": {
        "label": "Andrews, Hambur, Hansell and Wheeler (2022), Reaching for the stars: Australian firms and the "
        "global productivity frontier, Treasury Working Paper 2022-01",
        "url": "https://treasury.gov.au/sites/default/files/2022-02/p2022-243535.pdf",
    },
    "andrews_hansell": {
        "label": "Andrews and Hansell (2019), Productivity-enhancing labour reallocation in Australia, Treasury "
        "Working Paper 2019-06",
        "url": "https://treasury.gov.au/sites/default/files/2019-11/p2019-37418-productivity_0.pdf",
    },
    "hambur_andrews2023": {
        "label": "Hambur and Andrews (2023), Doing less, with less: capital misallocation, investment and the "
        "productivity slowdown in Australia, RBA Research Discussion Paper 2023-03",
        "url": "https://www.rba.gov.au/publications/rdp/2023/2023-03.html",
    },
    "hf2025": {
        "label": "Hambur and Freestone (2025), RBA Research Discussion Paper 2025-05 (mark-ups and misallocation)",
        "url": "https://www.rba.gov.au/publications/rdp/2025/2025-05.html",
    },
    "egert_gal": {
        "label": "Égert and Gal (2016), The quantification of structural reforms in OECD countries, OECD Economics "
        "Department Working Paper 1354",
        "url": "https://www.oecd.org/content/dam/oecd/en/publications/reports/2017/02/the-quantification-of-structural-reforms-in-oecd-countries_b5d58c7d/2d887027-en.pdf",
    },
    "cao2015": {
        "label": "Cao et al. (2015), Understanding the economy-wide efficiency and incidence of major Australian "
        "taxes, Treasury Working Paper 2015-01",
        "url": "https://treasury.gov.au/sites/default/files/2019-03/TWP2015-01.pdf",
    },
    "harper2015": {
        "label": "Competition Policy Review (Harper Review), final report (2015)",
        "url": "https://treasury.gov.au/publication/p2015-cpr-final-report",
    },
}

INTRO = (
    "A short, consistent way to judge how a law, a regulatory setting or another barrier is likely to affect "
    "productivity and competition in Australia. Every item in the legislation menu is marked against it."
)
LOGIC: tuple[str, ...] = (
    "Output per hour worked grows in two ways: workers get more and better capital to work with (capital deepening), "
    "and the economy gets more out of the capital and labour it has (multifactor productivity).",
    "Multifactor productivity rises when firms innovate and adopt better methods, when they produce at least cost, "
    "and when workers and capital move to the firms and uses where they are worth most. The Office of Impact "
    "Analysis calls these dynamic, productive and allocative efficiency.",
    "Competition drives all three. New firms entering and weak ones leaving, rivalry among incumbents and open "
    "markets push firms to improve and move resources to the best of them. Australia has seen fewer firms enter, "
    "slower movement of workers to better jobs, rising mark-ups and weaker investment.",
)
LOGIC_SOURCES: tuple[str, ...] = ("pc2023", "pc2025", "oia_comp", "andrews2022", "andrews_hansell", "hf2025")


def rating(total: int) -> str:
    """The band for an overall mark."""
    for floor, key, _ in RATINGS:
        if total >= floor:
            return key
    return "strongly-negative"


def as_dict() -> dict:
    """Everything the framework page and the menu need, as plain JSON."""
    return {
        "version": VERSION,
        "adopted": ADOPTED,
        "intro": INTRO,
        "logic": list(LOGIC),
        "logicSources": list(LOGIC_SOURCES),
        "pillars": PILLARS,
        "drivers": {
            k: {**v, "marks": {str(m): t for m, t in v["marks"].items()}, "look_for": list(v["look_for"])}
            for k, v in DRIVERS.items()
        },
        "markLabels": {str(k): v for k, v in MARK_LABELS.items()},
        "ratings": [{"floor": f, "id": k, "label": label} for f, k, label in RATINGS],
        "reach": REACH,
        "confidence": CONFIDENCE,
        "kinds": KINDS,
        "steps": list(STEPS),
        "counterfactual": COUNTERFACTUAL,
        "overlap": list(OVERLAP_RULES),
        "caveats": list(CAVEATS),
        "sources": SOURCES,
    }


def _cite(keys) -> str:
    return "; ".join(f"[{SOURCES[k]['label']}]({SOURCES[k]['url']})" for k in keys)


def markdown() -> str:
    """The framework as a short methods note (``docs/productivity_framework.md``)."""
    out = [
        f"# ALICIA productivity impact framework (version {VERSION})",
        "",
        f"> Generated by `alicia framework` from `alicia/src/alicia/register/framework.py` (adopted {ADOPTED}). "
        "The same text is on the website's Framework page. Do not edit by hand.",
        "",
        INTRO,
        "",
        "## How productivity grows",
        "",
        *[f"- {p}" for p in LOGIC],
        "",
        f"Sources: {_cite(LOGIC_SOURCES)}.",
        "",
        "## The eight drivers",
        "",
    ]
    for pk, p in PILLARS.items():
        out += [f"### {p['label']}: {p['question']}", ""]
        for k, d in DRIVERS.items():
            if d["pillar"] != pk:
                continue
            out += [
                f"#### {d['label']} (`{k}`)",
                "",
                f"**Question.** {d['question']}",
                "",
                f"**Why it matters.** {d['why']} ({_cite(d['why_sources'])})",
                "",
                "**Look for:** " + "; ".join(d["look_for"]) + ".",
                "",
                "| Mark | Meaning |",
                "|---|---|",
                *[f"| {'+' if m > 0 else '−'}{abs(m)} | {t} |" for m, t in d["marks"].items()],
                "",
                f"Policy costing channels: {', '.join(d['channels'])}.",
                "",
            ]
    out += [
        "## How an item is marked",
        "",
        *[f"{i}. {s}" for i, s in enumerate(STEPS, 1)],
        "",
        f"**What a mark compares against.** {COUNTERFACTUAL}",
        "",
        "| Overall mark | Band |",
        "|---|---|",
        "| +3 or more | Strongly positive |",
        "| +1 to +2 | Positive |",
        "| 0 | Neutral or offsetting |",
        "| −1 to −2 | Negative |",
        "| −3 or less | Strongly negative |",
        "",
        "| Reach | Meaning |",
        "|---|---|",
        *[f"| {v['label']} | {v['help']} |" for v in REACH.values()],
        "",
        "| Confidence | Meaning |",
        "|---|---|",
        *[f"| {v['label']} | {v['help']} |" for v in CONFIDENCE.values()],
        "",
        "| Kind of item | Meaning |",
        "|---|---|",
        *[f"| {v['label']} | {v['help']} |" for v in KINDS.values()],
        "",
        "## Avoiding double counting",
        "",
        *[f"- {r}" for r in OVERLAP_RULES],
        "",
        "## Limits",
        "",
        *[f"- {c}" for c in CAVEATS],
        "",
        "## Sources",
        "",
        *[f"- [{s['label']}]({s['url']})" for s in SOURCES.values()],
        "",
    ]
    return "\n".join(out)
