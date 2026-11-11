"""The Industry lens (beta): pick an ANZSIC class and a state, and see the laws that apply to it, marked against the
productivity impact framework and placed by the market position each effect acts through: entrants, existing
competitors, and monopolies and oligopolies. The wording is shared with Legislative levers influencing competition
(``register/competition.py``; DECISIONS E-137).

The page is built from the register as it stands, so every requirement or register item added later appears on it
without code changes: requirements (``regulation-register/requirements/``) by their reach, and register items
(``regulation-register/records/``) by their industries. How each is coded is in ``register/competition.py``; the
methods note is ``docs/industry_lens.md``.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

from ..register import competition as C
from ..register.catalogue import default_register_dir
from ..register.framework import DRIVERS, MARK_LABELS
from ..register.requirements import KIND_LABELS, TRIGGER_LABELS, Requirement, load_requirements, reach_classes
from ..register.schema import ChangeRecord

PAGE = ("industry-lens.html", "Industry lens (beta)")
ROOT = Path(__file__).resolve().parents[4]
CLASSES = ROOT / "data" / "processed" / "anzsic" / "anzsic2006_classes.json"
MARKS = ROOT / "data" / "processed" / "anzsic" / "class_marks.csv"
MAP = ROOT / "data" / "processed" / "geo" / "ste_2021_map.json"
STATES = (
    ("NSW", "New South Wales"),
    ("VIC", "Victoria"),
    ("QLD", "Queensland"),
    ("SA", "South Australia"),
    ("WA", "Western Australia"),
    ("TAS", "Tasmania"),
    ("NT", "Northern Territory"),
    ("ACT", "Australian Capital Territory"),
)
CLASS_MARKS = {
    "government": "Mainly government",
    "npish": "Mainly non-profit institutions serving households",
    "households": "Households, not businesses",
}
DEFAULT = ("H", "", "NSW")  # Accommodation and Food Services, all classes: calibration classes with laws at every tier
REPO_MAIN = "https://github.com/jabthebeer/Competition-in-Australia-analysis/blob/main/"


def classes() -> list[dict]:
    rows = json.loads(CLASSES.read_text("utf-8"))["rows"]
    marks = {}
    if MARKS.exists():
        with MARKS.open(encoding="utf-8", newline="") as fh:
            marks = {r["class"]: r["mark"] for r in csv.DictReader(fh)}
    return [
        {
            "code": r["class"],
            "name": r["class_name"],
            "division": r["division"],
            "group": f"{r['group']} {r['group_name']}",
            "subdivision": f"{r['subdivision']} {r['subdivision_name']}",
            "definition": r["definition"],
            "mark": CLASS_MARKS.get(marks.get(r["class"], ""), ""),
        }
        for r in rows
    ]


def _compact(value):
    """Drop empty fields (None, empty lists and strings, False) to keep the embedded data small."""
    if isinstance(value, dict):
        # Identity and length tests, not ==, so that 0 (a mark total) is kept while False is dropped.
        return {k: _compact(v) for k, v in value.items() if not (v is None or v is False or v in ([], ""))}
    if isinstance(value, list):
        return [_compact(v) for v in value]
    return value


def divisions() -> dict[str, str]:
    return {r["division"]: r["division_name"] for r in json.loads(CLASSES.read_text("utf-8"))["rows"]}


def _law(law) -> dict:
    return {"title": law.title, "id": law.register_id, "url": str(law.register_url) if law.register_url else None}


def _source(s) -> dict:
    return {"title": s.title, "publisher": s.publisher, "url": str(s.url), "locator": s.locator}


def requirement_row(q: Requirement, settings: dict[str, ChangeRecord]) -> dict:
    # A requirement that names a setting record (the same law in force) stands for it on the page.
    setting = next((r for r in q.records if r in settings), None)
    reach = []
    for r in q.reach:
        cls = reach_classes(r)
        reach.append(
            {
                "classes": "all" if r.scope == "all" and not r.exclude else cls,
                "activities": list(r.activities),
                "condition": r.condition,
                "legalForms": list(r.legal_forms),
                "inStates": list(r.in_states),
            }
        )
    folder = "cth" if q.tier == "cth" else (f"local/{q.lga}" if q.tier == "local" else q.jurisdiction.lower())
    return {
        "id": q.id,
        "type": "requirement",
        "tier": q.tier,
        "jurisdiction": q.jurisdiction,
        "council": q.lga_name,
        "title": q.title,
        "what": q.what,
        "kind": KIND_LABELS[q.kind],
        "triggers": [TRIGGER_LABELS[t.type] for t in q.triggers],
        "laws": [_law(law) for law in q.laws],
        "source": _source(q.sources[0]),
        "reach": reach,
        "marks": C.placed_marks(q.assessment),
        "framework": C.summary(q.assessment),
        "setting": setting,
        "related": [r for r in q.records if r != setting],
        "reachConfidence": q.confidence,
        "councilsAdminister": q.administered_by_councils,
        "file": f"regulation-register/requirements/{folder}/{q.id}.json",
    }


def record_row(r: ChangeRecord) -> dict:
    first = r.dates.commenced[0].date if r.dates.commenced else None
    return {
        "id": r.id,
        "type": "record",
        "kind": r.kind,
        "tier": "cth" if r.jurisdiction == "CTH" else "state",
        "jurisdiction": r.jurisdiction,
        "title": r.title,
        "what": r.summary,
        "since": first.isoformat() if first else None,
        # An economy-wide item may list no industries: it reaches every class.
        "industries": [{"code": i.anzsic, "exposure": i.exposure} for i in r.industries] or "all",
        "laws": [
            {"title": i.title, "id": i.register_id, "url": str(i.register_url) if i.register_url else None}
            for i in r.instruments
        ],
        "sources": [str(u) for u in r.direction_sources],
        "marks": C.placed_marks(r.assessment) if r.assessment else [],
        "framework": C.summary(r.assessment) if r.assessment else None,
        # Assessed as economy-wide: it reaches every industry, directly where listed and indirectly elsewhere.
        "economyWide": bool(r.assessment and r.assessment.reach == "economy-wide"),
        "file": f"regulation-register/records/{r.id}.json",
    }


def payload(
    records: list[ChangeRecord], requirements: list[Requirement] | None = None, repo_base: str | None = None
) -> dict:
    repo = repo_base or REPO_MAIN
    reqs = requirements if requirements is not None else load_requirements().requirements
    settings = {r.id: r for r in records if r.kind == "setting"}
    live = [r for r in records if r.ended is None]
    rows = [_compact(row) for row in [requirement_row(q, settings) for q in reqs] + [record_row(r) for r in live]]
    geo = json.loads(MAP.read_text("utf-8"))
    return {
        "page": PAGE[1],
        "positions": [
            {
                "id": p,
                "label": C.POSITION_LABELS[p],
                "question": C.POSITION_QUESTIONS[p],
                "drivers": [DRIVERS[d]["short"] for d, ps in C.DRIVER_POSITIONS.items() if p in ps],
            }
            for p in C.POSITIONS
        ],
        "effectPhrases": C.EFFECT_PHRASES,
        "markLabels": {str(k): v for k, v in MARK_LABELS.items()},
        "classes": classes(),
        "divisions": divisions(),
        "states": [{"code": c, "name": n} for c, n in STATES],
        "map": {"viewBox": geo["viewBox"], "areas": geo["areas"], "source": geo["source"], "licence": geo["licence"]},
        "rows": rows,
        "market": market(),
        "default": {"division": DEFAULT[0], "class": DEFAULT[1], "state": DEFAULT[2]},
        "counts": {
            "requirements": len(reqs),
            "records": len(live),
            "laws": sum(1 for r in live if r.kind != "barrier"),
            "barriers": sum(1 for r in live if r.kind == "barrier"),
            "ended": len(records) - len(live),
            "industrySpecific": sum(1 for q in reqs if not any(r.scope == "all" for r in q.reach)),
        },
        "repo": repo,
        "built": dt.date.today().isoformat(),
        "sources": {
            "anzsic": json.loads(CLASSES.read_text("utf-8"))["source"],
            "map": geo["url"],
        },
    }


CABEE = ROOT / "data" / "processed" / "abs_cabee" / "class_state_fy.parquet"
AUS_INDUSTRY = ROOT / "data" / "processed" / "costing" / "sources" / "abs_australian_industry.json"
RBA = ROOT / "data" / "processed" / "costing" / "sources" / "rba_hf2025.json"
SIZE_BANDS = ("non-employing", "1-19 employees", "20-199 employees", "200+ employees")


def _int(v):
    return None if v is None or v != v else int(v)


def _pct(num, den, digits: int = 1):
    if den is None or den != den or not den or num != num:
        return None
    v = round(100 * num / den, digits)
    return int(v) if v == int(v) else v


def market() -> dict:
    """Market structure for the lens, from three authoritative public sources, each at the finest level published:

    - ``cabee``: for every class and state, entry and exit rates each financial year (entries and exits as a share of
      businesses operating at the start of the year), the latest year's counts, and businesses by employment size at
      the end of the latest year (ABS CABEE);
    - ``sizeSales``: for each division, Australia, sales and service income by employment size in the latest year
      (ABS Australian Industry, 8155.0, Table 5; finance and insurance is not in the table);
    - ``top4``: for each division, the four largest firms' share of sales in its industries (sales-weighted mean and
      median), 2002 to 2019 (RBA RDP 2025-05, from BLADE).

    Counts of businesses are not market shares; the page labels each figure with its level and year."""
    import pandas as pd

    from .growth import SOURCES

    d = pd.read_parquet(
        CABEE, columns=["measure", "industry_level", "industry_code", "geo_code", "breakdown", "period", "value"]
    )
    d = d[d.industry_level == "class"]
    periods = sorted(d.period.unique())
    years = [p.year for p in periods]
    latest = periods[-1]
    tot = d[d.breakdown == ""].pivot_table(
        index=["geo_code", "industry_code", "period"], columns="measure", values="value"
    )
    sizes = d[(d.breakdown != "") & (d.measure == "businesses_end") & (d.period == latest)].pivot_table(
        index=["geo_code", "industry_code"], columns="breakdown", values="value"
    )
    states: dict[str, dict] = {}
    for (geo, cls), g in tot.groupby(level=[0, 1]):
        g = g.droplevel([0, 1]).reindex(periods)
        entry = [_pct(e, s) for e, s in zip(g.get("entries", []), g.get("businesses_start", []), strict=True)]
        exit_ = [_pct(e, s) for e, s in zip(g.get("exits", []), g.get("businesses_start", []), strict=True)]
        last = g.loc[latest]
        band = sizes.loc[(geo, cls)] if (geo, cls) in sizes.index else None
        states.setdefault(geo, {})[cls] = [
            entry,
            exit_,
            [_int(band.get(b)) for b in SIZE_BANDS] if band is not None else None,
            [_int(last.get(m)) for m in ("businesses_start", "entries", "exits", "businesses_end")],
        ]
    # The same measures for each division in each state, from the sum of its classes (CABEE publishes classes; the
    # ABS's own division totals can differ slightly, because small counts are perturbed).
    div_of = {r["class"]: r["division"] for r in json.loads(CLASSES.read_text("utf-8"))["rows"]}
    d = d.assign(division=d.industry_code.map(div_of))
    dtot = d[d.breakdown == ""].pivot_table(
        index=["geo_code", "division", "period"], columns="measure", values="value", aggfunc="sum"
    )
    dsizes = d[(d.breakdown != "") & (d.measure == "businesses_end") & (d.period == latest)].pivot_table(
        index=["geo_code", "division"], columns="breakdown", values="value", aggfunc="sum"
    )
    divisions: dict[str, dict] = {}
    for (geo, div), g in dtot.groupby(level=[0, 1]):
        g = g.droplevel([0, 1]).reindex(periods)
        band = dsizes.loc[(geo, div)] if (geo, div) in dsizes.index else None
        last = g.loc[latest]
        divisions.setdefault(geo, {})[div] = [
            [_pct(e, s) for e, s in zip(g["entries"], g["businesses_start"], strict=True)],
            [_pct(e, s) for e, s in zip(g["exits"], g["businesses_start"], strict=True)],
            [_int(band.get(b)) for b in SIZE_BANDS] if band is not None else None,
            [_int(last.get(m)) for m in ("businesses_start", "entries", "exits", "businesses_end")],
        ]
    ai = json.loads(AUS_INDUSTRY.read_text("utf-8"))
    rows = ai["tables"]["size_division"]["rows"]
    fy = max(r["fy"] for r in rows)
    size_sales: dict[str, dict] = {}
    for r in rows:
        if r["fy"] == fy and r["anzsic"] != "TOT" and r.get("sales") is not None:
            size_sales.setdefault(r["anzsic"], {})[r["size_band"]] = r["sales"]
    for div, v in size_sales.items():
        size_sales[div] = {
            "under20": (v.get("0-4") or 0) + (v.get("5-19") or 0),
            "20-199": v.get("20-199"),
            "200+": v.get("200+"),
            "total": v.get("total"),
        }
    rba = json.loads(RBA.read_text("utf-8"))
    conc = [r for r in rba["tables"]["concentration"]["rows"] if r.get("top4_weighted") is not None]
    top4: dict[str, dict] = {}
    for r in sorted(conc, key=lambda r: r["fyear"]):
        t = top4.setdefault(r["division"], {"years": [], "weighted": [], "median": [], "industries": None})
        t["years"].append(r["fyear"])
        t["weighted"].append(round(100 * r["top4_weighted"], 1))
        t["median"].append(round(100 * r["top4_median"], 1) if r.get("top4_median") is not None else None)
        t["industries"] = r.get("top4_industries")
    return {
        "years": years,
        "cabee": states,
        "cabeeDivision": divisions,
        "sizeBands": list(SIZE_BANDS),
        "sizeSales": size_sales,
        "sizeSalesYear": fy,
        "top4": top4,
        "sources": {
            "cabee": list(SOURCES["cabee"]),
            "australianIndustry": [ai["source"]["title"], ai["source"]["url"]],
            "rba": list(SOURCES["rba_rdp"]),
        },
    }


def default_requirements_dir() -> Path:
    return default_register_dir() / "requirements"


__all__ = ["PAGE", "payload"]
