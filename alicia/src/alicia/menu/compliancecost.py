"""Compliance cost on the site: what each requirement costs the businesses it binds in staff time, a year, and a
register item's total from the requirements inside it (DECISIONS E-700).

The figures are built by ``alicia/scripts/compliance_costs.py`` into ``data/processed/legislation/compliance_costs.csv``
and ``compliance_costs_by_class.csv`` (method: ``alicia/src/alicia/costing/compliance.py``; note:
``docs/compliance_costs.md``). This module only reads them. The cost sits beside a rule's severity and impact class and
does not change either."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CSV = ROOT / "data" / "processed" / "legislation" / "compliance_costs.csv"
CLASS_CSV = ROOT / "data" / "processed" / "legislation" / "compliance_costs_by_class.csv"
NOTE_PATH = "docs/compliance_costs.md"
SCEN = ("low", "central", "high")

NOTE = (
    "Draft: the hours are assumed, not measured, and nothing has yet been checked by a person. Compliance cost is the "
    "staff time a requirement takes the businesses it binds, a year, valued at $91.54 an hour, the Office of Impact "
    "Analysis's rate for work time (Regulatory Burden Measurement Framework, July 2026). It is the hours when a "
    "business starts times the new businesses a year, plus the hours each year times the businesses operating, from "
    "the ABS Counts of Australian Businesses. The hours are set for each kind of requirement, with a low and a high "
    "value. It leaves out the cost of meeting a standard (equipment, building work, training), waiting time, fees and "
    "taxes paid to government, and effects on competition. Where a rule binds only some of the businesses counted, "
    "the figure is an upper bound, shown as 'up to'. The cost sits beside the rule's severity and impact class and "
    "does not change them."
)


def _num(v: str) -> float | None:
    return float(v) if v not in ("", None) else None


def _trio(r: dict, stem: str) -> dict[str, float | None]:
    return {"low": _num(r[f"{stem}_low"]), "central": _num(r[stem]), "high": _num(r[f"{stem}_high"])}


def load(path: Path = CSV) -> dict[str, dict]:
    """Each requirement's compliance cost, by requirement id, as the page shows it."""
    if not path.exists():
        return {}
    out = {}
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["costed"] != "yes":
                out[r["requirement"]] = {"costed": False, "why": r["why_not"]}
                continue
            out[r["requirement"]] = {
                "costed": True,
                "task": r["task"],
                "hoursFrom": r["hours_from"],
                "basis": r["size_basis"],
                "upper": r["upper_bound"] == "yes",
                "upperWhy": [x for x in r["upper_why"].split("; ") if x],
                "businesses": int(r["businesses"]),
                "newPerYear": int(r["new_per_year"]),
                "startHours": _trio(r, "start_hours"),
                "yearlyHours": _trio(r, "yearly_hours"),
                "rate": float(r["rate"]),
                "perStart": _num(r["per_business_start"]),
                "perYear": _num(r["per_business_year"]),
                "cost": _trio(r, "cost"),
                "fees": _num(r["fees_total"]),
                "year": int(r["counts_year"]),
            }
    return out


def record_totals(costs: dict[str, dict], nested: dict[str, list[str]]) -> dict[str, dict]:
    """A register item's compliance cost: the sum over the costed requirements inside it (``nested``: item id to the
    ids of its requirements). Items with no costed requirement have none."""
    out = {}
    for rec, ids in nested.items():
        inner = [costs[i] for i in ids if costs.get(i, {}).get("costed")]
        if not inner:
            continue
        out[rec] = {
            "costed": True,
            "sum": True,
            "requirements": len(inner),
            "of": len(ids),
            "upper": any(c["upper"] for c in inner),
            "cost": {s: sum(c["cost"][s] for c in inner) for s in SCEN},
            "businesses": max(c["businesses"] for c in inner),
        }
    return out


def load_classes(path: Path = CLASS_CSV) -> dict[str, dict]:
    """The cost in each ANZSIC class: Commonwealth and state rules apart, exact figures and upper bounds apart."""
    if not path.exists():
        return {}
    out = {}
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[r["anzsic"]] = {
                "cth": _num(r["cth"]),
                "state": _num(r["state"]),
                "cthUpper": _num(r["cth_upper"]),
                "stateUpper": _num(r["state_upper"]),
                "businesses": int(r["businesses"]),
                "requirements": int(r["requirements"]),
            }
    return out
