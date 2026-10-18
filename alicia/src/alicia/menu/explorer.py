"""Build the interactive menu explorer: one self-contained HTML page with the register embedded.

The page is a fragment (title, styles, markup, data, script) so it can be published as a
hosted page; ``standalone=True`` wraps it in a full HTML document for opening locally.
"""

from __future__ import annotations

import datetime as dt
import json
from importlib import resources
from pathlib import Path

from .. import anzsic
from ..register.evaluation import CATEGORY_LABELS, Evaluation, current_evaluation
from ..register.schema import CHANNEL_LABELS, ChangeRecord
from ..timing import fy_bounds, timing
from .screen import COVID_FYS, DEFAULT_COVERAGE, screen_all

FAMILY_LABELS = {
    "amr-occupational-licensing": "Automatic mutual recognition of occupational licences",
    "building-practitioner-registration": "Building practitioner registration",
    "childcare-nqf": "Childcare National Quality Framework",
    "container-deposit-scheme": "Container deposit schemes",
    "default-offer-reregulation": "Default electricity offers",
    "harper-cca-2017": "Harper competition law reforms (2017)",
    "heavy-vehicle-national-law": "Heavy Vehicle National Law",
    "industry-codes": "Mandatory industry codes",
    "legal-profession-uniform-law": "Legal Profession Uniform Law",
    "liquor-lockouts-last-drinks": "Liquor lockouts and last drinks",
    "merger-control": "Merger control",
    "pharmacy-regulation": "Pharmacy regulation",
    "retail-energy-price-deregulation": "Retail energy price deregulation",
    "retail-trading-hours": "Retail trading hours",
    "rideshare-legalisation": "Ride-share legalisation",
    "short-term-rental-regulation": "Short-term rental regulation",
    "unfair-contract-terms": "Unfair contract terms",
}

SCREEN_RULES = (
    "A triage aid, not a judgement on the reform. Weaknesses counted: no geographic comparison group "
    "(national change); fewer than 3 financial years of entry and exit data before the first full year, or "
    "fewer than 2 from it; affected industries only at division or subdivision level; an event window "
    "overlapping 2019-20 to 2021-22 (COVID); another recorded change in the same industry and place within "
    "two years; dates not fully verified. None: high. One: medium. Two or more: low."
)
# Evaluation documents are linked on GitHub; override with --repo-base once the work is merged.
REPO_BASE = "https://github.com/jabthebeer/Competition-in-Australia-analysis/blob/claude/sharp-bell-4dsvcz/"
EVALUATION_NOTE = (
    "Evaluated changes have a pre-registered analysis in this repository: a plan committed before the "
    "results were estimated, a graded result and its caveats. A record's direction stays a hypothesis; the "
    "evaluation says what the data showed. Grades follow the evaluation design: Strong, Moderate, Weak or "
    "Not identified."
)
CHECK_NOTE = (
    "Effective dates are checked against the official legislation registers by 'alicia dates'. "
    "Commonwealth, Queensland, Tasmania, ACT, WA and NT registers can be read automatically; Victoria gives "
    "version dates only; NSW and SA block automated requests, so their records rely on sourced dates."
)


def _humanise(family: str) -> str:
    return family.replace("-", " ").capitalize()


def _short(title: str, limit: int = 30) -> str:
    base = title.split(" (")[0]
    return base if len(base) <= limit else base[: limit - 1].rstrip() + "…"


def _division_names() -> dict[str, str]:
    return {code: anzsic.name(code) or "" for code in "ABCDEFGHIJKLMNOPQRS"}


LEVEL_ORDER = ("class", "group", "retail-group", "subdivision", "division", "inferred", "occupation", "total")
DATA_NOTE = (
    "Data that can measure a change: every processed panel in data/processed matched to the change's ANZSIC "
    "codes and jurisdiction, at the finest industry level the panel offers. 'Local' means areas finer than the "
    "state (postcode, SA2, LGA and so on) are available in the change's state. 'Inferred' industries come from "
    "business names in the ABN and ASIC registers (81% precise on held-out names, and only some names say what a "
    "business does), so read them as changes over time, not levels."
)


def data_summary(record: ChangeRecord, catalogue: list[dict]) -> list[dict]:
    """Coverage matches grouped by source panel: its measures, and the finest industry level found."""
    from ..pipeline.coverage import coverage
    from ..pipeline.sources import measure_label

    if not catalogue:
        return []
    groups: dict[tuple[str, str], dict] = {}
    for m in coverage(record, catalogue):
        g = groups.setdefault(
            (m.source, m.table),
            {
                "source": m.source,
                "table": m.table,
                "measures": [],
                "level": m.matched_level,
                "codes": [],
                "state": m.state,
                "local": list(m.local_levels),
                "first": m.first,
                "last": m.last,
                "periodType": m.period_type,
            },
        )
        label = f"{measure_label(m.measure)} ({m.unit})"
        if label not in g["measures"]:
            g["measures"].append(label)
        if LEVEL_ORDER.index(m.matched_level) < LEVEL_ORDER.index(g["level"]):
            g["level"] = m.matched_level
        if m.matched_code and m.matched_code not in g["codes"]:
            g["codes"].append(m.matched_code)
        g["first"], g["last"] = min(g["first"], m.first), max(g["last"], m.last)
        g["state"] = g["state"] or m.state
        g["local"] = sorted(set(g["local"]) | set(m.local_levels))
        if m.period_type not in g["periodType"].split("/"):
            g["periodType"] += f"/{m.period_type}"
    return sorted(groups.values(), key=lambda g: (LEVEL_ORDER.index(g["level"]), g["source"]))


def build_payload(
    records: list[ChangeRecord],
    dates_report: list[dict] | None = None,
    generated: dt.date | None = None,
    evaluations: list[Evaluation] | None = None,
    repo_base: str | None = None,
    catalogue: list[dict] | None = None,
) -> dict:
    from ..pipeline.coverage import load_catalogue
    from ..pipeline.sources import SOURCES

    catalogue = load_catalogue() if catalogue is None else catalogue
    screens = screen_all(records)
    checks = {d["record_id"]: d for d in dates_report or []}
    evaluations = evaluations or []
    evaluated = current_evaluation(evaluations)
    out = []
    for r in records:
        eff = r.effective_commencement
        t = screens[r.id]
        check = checks.get(r.id)
        data = r.model_dump(mode="json")
        data.update(
            {
                "effective": eff.date.isoformat() if eff else None,
                "effectiveWhat": eff.what if eff else None,
                "timing": None,
                "screen": t.as_dict(),
                "channelLabels": [CHANNEL_LABELS[c] for c in r.channels],
                "short": _short(r.title),
                "check": {"status": check["status"], "issues": check["issues"]} if check else None,
                "evaluation": evaluated.get(r.id),
                "data": data_summary(r, catalogue),
            }
        )
        if eff:
            data["timing"] = timing(eff.date).as_dict()
        data["industries"] = [{**i, "division": anzsic.division(i["anzsic"])} for i in data["industries"]]
        out.append(data)
    first_start, _ = fy_bounds(DEFAULT_COVERAGE.first_fy)
    _, last_end = fy_bounds(DEFAULT_COVERAGE.last_fy)
    return {
        "generated": (generated or dt.date.today()).isoformat(),
        "records": out,
        "channels": [{"id": k, "label": v} for k, v in CHANNEL_LABELS.items()],
        "familyLabels": {f: FAMILY_LABELS.get(f, _humanise(f)) for f in {r.family for r in records if r.family}},
        "divisions": _division_names(),
        "coverage": {
            "firstStart": first_start.isoformat(),
            "lastEnd": last_end.isoformat(),
            "label": f"ABS CABEE, {first_start.year}-{str(first_start.year + 1)[2:]} to "
            f"{last_end.year - 1}-{str(last_end.year)[2:]}",
        },
        "covidFys": [min(COVID_FYS), max(COVID_FYS)],
        "evaluations": {ev.id: ev.model_dump(mode="json") for ev in evaluations},
        "categoryLabels": CATEGORY_LABELS,
        "repoBase": repo_base or REPO_BASE,
        "evaluationNote": EVALUATION_NOTE,
        "dataSources": {k: v.as_dict() for k, v in SOURCES.items()},
        "dataNote": DATA_NOTE,
        "screenRules": SCREEN_RULES,
        "checkNote": CHECK_NOTE,
    }


def render(payload: dict, standalone: bool = False, nav: str = "") -> str:
    """``nav`` is the site navigation (``growth.nav``), set when the page is built with the other pages."""
    template = resources.files("alicia.menu").joinpath("templates/explorer.html").read_text("utf-8")
    # Embed the data safely inside <script type="application/json">.
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = template.replace("<!--__NAV__-->", nav).replace("__MENU_DATA__", blob)
    if standalone:
        page = (
            '<!doctype html>\n<html lang="en-AU">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            "</head>\n<body>\n" + page + "\n</body>\n</html>\n"
        )
    return page


def build_explorer(
    records: list[ChangeRecord],
    out: Path,
    dates_report: Path | None = None,
    standalone: bool = False,
    evaluations: list[Evaluation] | None = None,
    repo_base: str | None = None,
    nav: str = "",
) -> Path:
    report = json.loads(dates_report.read_text("utf-8")) if dates_report and dates_report.exists() else None
    payload = build_payload(records, report, evaluations=evaluations, repo_base=repo_base)
    out.write_text(render(payload, standalone, nav), encoding="utf-8")
    return out
