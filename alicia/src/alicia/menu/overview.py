"""Regulatory overview by industry (``regulatory-overview.html``): compare industries by the regulation they face.

Owner decisions, 14 November 2026 (DECISIONS E-159: build it as a real page; E-161: own evidence first, exposure and
impact classes, no ranking of states). The page's end goal is to compare industries by the regulation they face. It
opens with the 19 industry divisions; a division opens to its detailed industries, and every row opens the
Industry lens.

Every figure is worked out here when the site is built:

- **businesses** and **new businesses for every 100** from the ABS Counts of Australian Businesses (Australia, latest
  year; the entry rate is for businesses with employees, as on Structural competitive conditions);
- **regimes**, **government bodies** and **regimes that differ between states** from the 61 regulatory regimes
  (``regulation-register/regimes/``; ``docs/industry_regulation.md``);
- **Commonwealth rules particular to the industry**, by impact class, from the register and the requirements
  (``exposure``). State and council rules are left out of the comparison, because far less of their law has been
  recorded and the amount differs between states; they show on the Industry lens, one state at a time.

For a division, the regime measures are the median of its detailed industries, and its rules are those that reach any
of them.
"""

from __future__ import annotations

from statistics import median

from .. import anzsic
from ..pipeline import schema, store
from ..register.regimes import Regime, industry_profiles, load_regimes
from ..register.requirements import Requirement, load_requirements
from ..register.schema import ChangeRecord
from . import exposure as X

NOTE = (
    "Regimes, government bodies and differences between states describe a typical business in the industry: a given "
    "business may deal with more or fewer. They are drafts from AI-assisted desk research and have not yet been "
    "checked. Rules are those the Commonwealth sets that apply today, are marked as weighing on productivity and are "
    "particular to some industries; rules for every business are left out, since they do not tell industries "
    "apart. State and council rules are left out of this comparison because much less of their law has been "
    "recorded; the Industry lens shows them, one state at a time."
)


def entry_rates(df) -> tuple[dict[str, tuple[float, float]], int | None]:
    """Businesses with employees starting in the latest year, and those operating at its start, by class (Australia):
    ``{class: (entries, start)}``, with the year the financial year starts in."""
    df = df[df["geo_code"].isin(schema.STATES) & df["industry_code"].str.fullmatch(r"\d{4}")]
    df = df[~df["breakdown"].isin(["", "non-employing"])]
    if df.empty:
        return {}, None
    last = df["period"].max()
    df = df[df["period"] == last]
    t = df.pivot_table(index="industry_code", columns="measure", values="value", aggfunc="sum")
    return {c: (float(r["entries"]), float(r["businesses_start"])) for c, r in t.iterrows()}, int(last.year)


def _load_entry():
    import pandas as pd

    path = store.PROCESSED / "abs_cabee" / "class_state_fy.parquet"
    if not path.exists():
        return {}, None
    cols = ["measure", "industry_code", "geo_code", "breakdown", "period", "value"]
    return entry_rates(pd.read_parquet(path, columns=cols))


def commonwealth_rules(menu: dict, records: list[ChangeRecord], requirements: list[Requirement]) -> dict[str, dict]:
    """For each class, the Commonwealth rules particular to some industries that reach it, by impact class:
    ``{class: {"major-narrow": {ids}, "minor": {ids}}}``. The classes come from the levers page's own rows."""
    rows = {r["id"]: r for r in menu["records"]}
    rows.update({q["id"]: q for r in menu["records"] for q in r.get("requirements", [])})
    reach = {q.id: X.requirement_pairs(q) for q in requirements if q.jurisdiction == "CTH"}
    reach.update({r.id: X.record_pairs(r) for r in records if r.jurisdiction == "CTH"})
    out: dict[str, dict] = {}
    for rid, pairs in reach.items():
        cls = (rows.get(rid) or {}).get("impactClass")
        if cls not in ("major-narrow", "minor"):
            continue
        for c in {c for c, _ in pairs}:
            out.setdefault(c, {"major-narrow": set(), "minor": set()})[cls].add(rid)
    return out


def payload(
    menu: dict,
    records: list[ChangeRecord],
    regimes: list[Regime] | None = None,
    requirements: list[Requirement] | None = None,
    counts: X.Counts | None = None,
    entry: tuple | None = None,
) -> dict:
    """The page's data: one row for each division and each detailed industry."""
    regimes = load_regimes().regimes if regimes is None else regimes
    requirements = load_requirements().requirements if requirements is None else requirements
    counts = X.load_counts() if counts is None else counts
    rates, entry_year = _load_entry() if entry is None else entry
    rules = commonwealth_rules(menu, records, requirements)

    def businesses(classes) -> int | None:
        if not counts:
            return None
        return round(sum(v for (c, _), v in counts.all.items() if c in classes))

    def rate(classes) -> float | None:
        entries = sum(rates[c][0] for c in classes if c in rates)
        start = sum(rates[c][1] for c in classes if c in rates)
        return round(100 * entries / start, 1) if start else None

    classes = []
    for p in industry_profiles(regimes):
        c = p["anzsic"]
        mine = rules.get(c, {"major-narrow": set(), "minor": set()})
        classes.append(
            {
                "code": c,
                "name": p["name"],
                "division": p["division"],
                "businesses": businesses({c}),
                "entry": rate({c}),
                "regimes": p["sector_regimes"],
                "bodies": p["sector_touchpoints"],
                "varying": p["sector_varying"],
                "major": len(mine["major-narrow"]),
                "minor": len(mine["minor"]),
            }
        )
    divisions = []
    for d in sorted({c["division"] for c in classes}):
        inside = [c for c in classes if c["division"] == d]
        codes = {c["code"] for c in inside}
        major = set().union(*(rules.get(c, {}).get("major-narrow", set()) for c in codes))
        minor = set().union(*(rules.get(c, {}).get("minor", set()) for c in codes))
        divisions.append(
            {
                "code": d,
                "name": anzsic.name(d),
                "classes": len(inside),
                "businesses": businesses(codes),
                "entry": rate(codes),
                "regimes": median(c["regimes"] for c in inside),
                "bodies": median(c["bodies"] for c in inside),
                "varying": median(c["varying"] for c in inside),
                "major": len(major),
                "minor": len(minor),
            }
        )
    return {
        "divisions": divisions,
        "classes": classes,
        "year": counts.year if counts else None,
        "entryYear": entry_year,
        "note": NOTE,
        "generated": menu.get("generated"),
        "lens": "industry-lens.html",
        "levers": "menu.html",
    }
