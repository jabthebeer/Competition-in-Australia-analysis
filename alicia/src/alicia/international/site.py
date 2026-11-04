"""The international comparisons for the website (phase P4, E-107): the harmonised series for Australia and the six
core peers, by group, measure and year, with the OECD median, Australia's comparability ratings and the result of
the formal tests (P3), as compact JSON for The state of competition in Australia.

Years are the international years: calendar years for the OECD's data and STAN, and for Australia's business
register and ABS series the calendar year the financial year ends in (2018-19 is 2019). The page maps its
financial-year slider onto them.
"""

from __future__ import annotations

import json
import math

import pandas as pd

from . import OUT, peers

# The measures the page shows, in order: key -> (label, unit, kind, digits). "growth" measures average as compound
# growth over the years chosen; the others as a plain mean.
MEASURES = {
    "va_growth": ("Output growth", "% a year", "growth", 1),
    "emp_growth": ("Jobs growth", "% a year", "growth", 1),
    "lp_growth_person": ("Productivity growth, output per person employed", "% a year", "growth", 1),
    "lp_growth_hour": ("Productivity growth, output per hour worked", "% a year", "growth", 1),
    "net_entry_rate": ("Net change in employer businesses", "% a year", "rate", 1),
    "birth_rate": ("Employer business birth rate", "% a year", "rate", 1),
    "death_rate": ("Employer business death rate", "% a year", "rate", 1),
    "survival_3y": ("New employer businesses surviving three years", "% of new businesses", "rate", 0),
    "pmr_sector": (
        "Sector regulation (OECD product market regulation)",
        "index, 0 to 6 (higher: more restrictive)",
        "level",
        2,
    ),
    "stri_sector": ("Services trade restrictiveness (OECD)", "index, 0 to 1 (higher: more restrictive)", "level", 2),
    "pmr_economy": (
        "Economy-wide regulation (OECD product market regulation)",
        "index, 0 to 6 (higher: more restrictive)",
        "level",
        2,
    ),
    "fdi_rri": ("Foreign investment restrictiveness (OECD)", "index, 0 to 1 (higher: more restrictive)", "level", 3),
}
SHORT_MEASURE = {
    "va_growth": "Output growth",
    "emp_growth": "Jobs growth",
    "lp_growth_person": "Productivity growth, per worker",
    "lp_growth_hour": "Productivity growth, per hour",
    "net_entry_rate": "Net change in employer businesses",
    "birth_rate": "Employer business births",
    "death_rate": "Employer business deaths",
    "survival_3y": "Three-year survival",
    "pmr_sector": "Sector regulation (PMR)",
    "stri_sector": "Services trade restrictiveness",
    "pmr_economy": "Economy-wide regulation (PMR)",
    "fdi_rri": "Foreign investment restrictiveness",
}
SIGNED = ("va_growth", "emp_growth", "lp_growth_person", "lp_growth_hour", "net_entry_rate")
# The heatmap's measures with a comparable international one
HEAT = {
    "gva": "va_growth",
    "emp": "emp_growth",
    "prod": "lp_growth_person",
    "entry": "birth_rate",
    "exit": "death_rate",
}
HEAT["net"] = "net_entry_rate"
SHORT = {
    "ALL": "Business economy",
    "AGR": "Agriculture",
    "MIN": "Mining",
    "MAN": "Manufacturing",
    "UTL": "Utilities",
    "CON": "Construction",
    "TRD": "Wholesale and retail",
    "TRN": "Transport",
    "ACC": "Accommodation and food",
    "ICT": "Information and telecoms",
    "FIN": "Finance and insurance",
    "RES": "Rental and real estate",
    "PRO": "Professional and admin services",
    "PUB": "Public administration",
    "EDU": "Education",
    "HLT": "Health care",
    "OTH": "Arts and other services",
}
ORDER = ["ALL", "AGR", "MIN", "MAN", "UTL", "CON", "TRD", "TRN", "ACC", "ICT", "FIN", "RES", "PRO", "PUB", "EDU", "HLT"]
ORDER.append("OTH")
OECD_MIN = 10  # members needed for an OECD median in a year


def _round(v: float, digits: int) -> float | None:
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), digits)


def payload() -> dict:
    """Everything the page needs for the comparisons; empty if the inputs are not built."""
    if not (OUT / "benchmark_inputs.parquet").exists():
        return {}
    from .concordance import groups
    from .harmonise import ALL_GROUPS

    df = pd.read_parquet(OUT / "benchmark_inputs.parquet")
    df = df[df["measure"].isin(MEASURES)]
    core = list(peers.APPROVED["core"])
    names = {r["country"]: r["name"] for r in json.loads((OUT / "peers.json").read_text("utf-8"))["ranking"]}
    years = list(range(2005, int(df["year"].max()) + 1))
    yi = {y: i for i, y in enumerate(years)}
    series: dict = {}
    for (m, g), cell in df.groupby(["measure", "group"]):
        digits = max(MEASURES[m][3] + 2, 3)  # two past display, at least three, so averages stay exact to show
        by = {}
        for c in ["AUS", *core]:
            sub = cell[cell["country"] == c]
            if sub.empty:
                continue
            vals = [None] * len(years)
            for y, v in zip(sub["year"], sub["value"], strict=True):
                if y in yi:
                    vals[yi[y]] = _round(v, digits)
            by[c] = vals
        others = cell[cell["country"] != "AUS"].groupby("year")["value"]
        med = others.median()[others.count() >= OECD_MIN]
        by["OECD"] = [_round(med.get(y), digits) for y in years]
        if "AUS" in by:
            series.setdefault(m, {})[g] = by
    aus = df[df["country"] == "AUS"]
    ratings, reasons = {}, {}
    for (m, g), sub in aus.groupby(["measure", "group"]):
        r = dict(zip(sub["year"], sub["comparability"], strict=True))
        ratings.setdefault(m, {})[g] = "".join(r[y][0] if y in r else "-" for y in years)
        last = sub[~sub["year"].isin((2020, 2021))].sort_values("year")
        reasons.setdefault(m, {})[g] = (last if len(last) else sub)["reasons"].iloc[-1]
    tests = {}
    if (OUT / "benchmarks.parquet").exists():
        b = pd.read_parquet(OUT / "benchmarks.parquet")
        for r in b.itertuples():
            tests.setdefault(r.measure, {}).setdefault(r.group, []).append(
                {"window": r.window, "status": r.status, "side": r.side if isinstance(r.side, str) else ""}
            )
    G = {g["id"]: g for g in groups()["groups"]}
    group_list = [
        {
            "id": g,
            "label": "Business economy" if g == "ALL" else G[g]["label"],
            "short": SHORT[g],
            "divisions": [] if g == "ALL" else G[g]["anzsic_divisions"],
        }
        for g in ORDER
    ]
    div_group = {d: g["id"] for g in groups()["groups"] for d in g["anzsic_divisions"]} | {"TOT": "ALL"}
    return {
        "peers": core,
        "names": {c: names.get(c, c) for c in core} | {"AUS": "Australia", "OECD": "OECD median"},
        "years": years,
        "measures": {
            k: {
                "label": v[0],
                "short": SHORT_MEASURE[k],
                "unit": v[1],
                "kind": v[2],
                "digits": v[3],
                "signed": k in SIGNED,
            }
            for k, v in MEASURES.items()
        },
        "heat": HEAT,
        "groups": group_list,
        "divGroup": div_group,
        "allGroups": [SHORT[g] for g in ALL_GROUPS],
        "series": series,
        "ratings": ratings,
        "reasons": reasons,
        "tests": tests,
    }
