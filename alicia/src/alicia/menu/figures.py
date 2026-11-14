"""Headline figures, worked out from the page data when the site is built.

Home's "Competition at a glance" and the scorecard on Structural competitive conditions show the same few numbers.
Each is computed here from the data the competition page embeds (``growth.growth_payload`` with the economic
conditions under ``conditions``), so the figures can't drift from the charts they summarise. The definitions are
the page's own ([methods note](../../../../docs/methods_competition_charts.md)); ``tests/test_home.py`` and
``tests/test_scorecard.py`` recompute each one from the source files by a separate route.
"""

from __future__ import annotations

# The barriers-to-entry groups whose companies sit behind barriers (Grattan Institute, 2017), and the comparison.
BARRIER_GROUPS = ("natural_monopoly", "scale_economies", "heavy_regulation")
LOW_BARRIERS = "low_barriers"


def fy(year: int) -> str:
    """A financial year by the year it starts in, with an en dash (Style Manual): 2024 is 2024–25."""
    return f"{year}–{(year + 1) % 100:02d}"


def first_last(years: list, values: list) -> tuple | None:
    """The first and last years with a figure, each with its value: ``((year, value), (year, value))``."""
    pairs = [(y, v) for y, v in zip(years, values, strict=True) if v is not None]
    return (pairs[0], pairs[-1]) if len(pairs) >= 2 else None


def business_rates(
    growth: dict, measure: str = "entries", scope: str = "employing", place: str = "AUS"
) -> tuple | None:
    """Businesses starting (``entries``) or closing (``exits``) in a year for every 100 operating at its start, for
    the first and last years of the business counts. ``scope`` is ``employing`` (businesses with employees, the
    page's default) or ``all``."""
    groups = growth["barriers"]["bizGroup"].get(scope, {}).get(place)
    if not groups:
        return None
    years = growth["barriers"]["bizYears"]
    rates = []
    for i in range(len(years)):
        start = sum(g["start"][i] or 0 for g in groups.values())
        rates.append(100 * sum(g[measure][i] or 0 for g in groups.values()) / start if start else None)
    return first_last(years, rates)


def concentration(growth: dict, measure: str = "top4_weighted") -> tuple | None:
    """The largest firms' share of sales in the average industry (sales-weighted), all industries, %: first and last
    years (RBA RDP 2025-05)."""
    conc = growth["barriers"].get("concentration") or {}
    return first_last(conc.get("years", []), conc.get("values", {}).get("TOT", {}).get(measure, []))


def markups(growth: dict) -> tuple | None:
    """The average ratio of price to marginal cost, all industries: first and last years (RBA RDP 2025-05)."""
    mark = (growth.get("conditions") or {}).get("profit", {}).get("markups") or {}
    return first_last(mark.get("years", []), mark.get("values", {}).get("TOT", []))


def returns(growth: dict) -> dict | None:
    """Company return on equity after tax, %, behind barriers to entry and where barriers are low, over every income
    year the ATO publishes: ``{"barriers", "low", "years": (first, last)}``.

    As on the page: a sector's profit and equity are averages over the years it is published with positive equity,
    and a group's return is its sectors' profit divided by their equity."""
    profit = (growth.get("conditions") or {}).get("profit") or {}
    years, sectors = profit.get("years") or [], profit.get("sectors") or []
    if not years or not sectors:
        return None

    def group_return(groups) -> float | None:
        equity = after_tax = 0.0
        for s in sectors:
            if s["group"] not in groups:
                continue
            ok = [
                i
                for i in range(len(years))
                if None not in (s["income"][i], s["npat"][i], s["equity"][i]) and s["equity"][i] > 0
            ]
            if ok:
                equity += sum(s["equity"][i] for i in ok) / len(ok)
                after_tax += sum(s["npat"][i] for i in ok) / len(ok)
        return 100 * after_tax / equity if equity > 0 else None

    behind, low = group_return(BARRIER_GROUPS), group_return((LOW_BARRIERS,))
    if behind is None or low is None:
        return None
    return {"barriers": behind, "low": low, "years": (years[0], years[-1])}


def scorecard(growth: dict) -> list[dict]:
    """Australia at a glance, for Structural competitive conditions: each figure's label, value, what it is, the
    earlier or comparison figure, and the tab that shows it. A figure whose data is missing is left out."""
    out = []

    def add(label: str, value: str, what: str, was: str, tab: str) -> None:
        out.append({"label": label, "value": value, "what": what, "was": was, "tab": tab})

    entry = business_rates(growth, "entries")
    if entry:
        (y0, v0), (y1, v1) = entry
        add(
            "Business entry",
            f"{v1:.1f}",
            f"new businesses for every 100 with employees, {fy(y1)}",
            f"{v0:.1f} in {fy(y0)}",
            "entry",
        )
    exits = business_rates(growth, "exits")
    if exits:
        (y0, v0), (y1, v1) = exits
        add(
            "Business exit",
            f"{v1:.1f}",
            f"closures for every 100 businesses with employees, {fy(y1)}",
            f"{v0:.1f} in {fy(y0)}",
            "entry",
        )
    top4 = concentration(growth)
    if top4:
        (y0, v0), (y1, v1) = top4
        add(
            "Concentration",
            f"{v1:.1f}%",
            f"of sales go to the 4 largest firms in the average industry, {y1}",
            f"{v0:.1f}% in {y0}",
            "concentration",
        )
    ups = markups(growth)
    if ups:
        (y0, v0), (y1, v1) = ups
        add("Mark-ups", f"{v1:.2f}", f"average ratio of price to marginal cost, {y1}", f"{v0:.2f} in {y0}", "profits")
    roe = returns(growth)
    if roe:
        y0, y1 = roe["years"]
        add(
            "Returns behind barriers",
            f"{roe['barriers']:.1f}%",
            f"company return on equity where barriers to entry are high, {fy(y0)} to {fy(y1)}",
            f"{roe['low']:.1f}% where barriers are low",
            "profits",
        )
    return out
