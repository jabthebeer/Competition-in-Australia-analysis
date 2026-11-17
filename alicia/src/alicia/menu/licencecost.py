"""What a licence costs the business that holds it: fees and staff time, to get it and to renew it (phase 8 of the
levers re-evaluation, DECISIONS E-173 and E-175).

The figures are built by ``alicia/scripts/licence_costs.py`` into ``data/processed/legislation/licence_costs.csv``
from the sourced inputs in ``regulation-register/licence-costs.json``. This module only reads them for the site. The
costs sit beside a rule's severity and impact class and do not change either (owner, 16 November 2026)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from ..register.catalogue import default_register_dir

ROOT = Path(__file__).resolve().parents[4]
CSV = ROOT / "data" / "processed" / "legislation" / "licence_costs.csv"
NOTE_PATH = "docs/licence_costs.md"

NOTE = (
    "Draft: compiled by AI-assisted desk research and not yet checked by a person. Fees are quoted from the fee "
    "regulations or the regulator's fee page, for the class of licence named. Staff time is assumed (no regulator "
    "publishes it) and valued at $91.54 an hour, the Office of Impact Analysis's rate for work time. Regulatory "
    "burden is that office's own measure: the staff time averaged over 10 years. It leaves out fees, which are "
    "transfers to government, so they are shown beside it. Training, insurance, waiting time and any effect on the "
    "wider economy are not counted. The cost sits beside the rule's severity and impact class and does not change "
    "them."
)


def _num(v: str) -> float | None:
    return float(v) if v not in ("", None) else None


def load_inputs(path: Path | None = None) -> dict[str, dict]:
    """Each costed licence's fee sources (once each: title, locator and link) and the range of hours assumed to
    apply for it, from the input file."""
    path = path or default_register_dir() / "licence-costs.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text("utf-8"))
    out: dict[str, dict] = {}
    for rid, item in data.get("items", {}).items():
        seen: dict[tuple, dict] = {}
        for f in item.get("fees", []):
            s = f["source"]
            seen.setdefault(
                (s["url"], s.get("locator")), {"title": s["title"], "locator": s.get("locator"), "url": s["url"]}
            )
        h = (item.get("hours") or data["assumed_hours"])["entry"]
        out[rid] = {"sources": list(seen.values()), "entryHoursLow": h["low"], "entryHoursHigh": h["high"]}
    return out


def load(path: Path = CSV, inputs: dict[str, dict] | None = None) -> dict[str, dict]:
    """The cost of each costed licence, by requirement id. A renewal fee the regulator does not publish is None."""
    if not path.exists():
        return {}
    inputs = load_inputs() if inputs is None else inputs
    out = {}
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rid = r["requirement"]
            extra = inputs.get(rid, {})
            out[rid] = {
                "licence": r["licence"],
                "entryFees": _num(r["entry_fees"]),
                "entryHours": _num(r["entry_hours"]),
                "entryTime": _num(r["entry_time_cost"]),
                "entryTotal": _num(r["entry_total"]),
                "entryLow": _num(r["entry_total_low"]),
                "entryHigh": _num(r["entry_total_high"]),
                "entryHoursLow": extra.get("entryHoursLow"),
                "entryHoursHigh": extra.get("entryHoursHigh"),
                "renewalYears": int(r["renewal_years"]),
                "renewalFees": _num(r["renewal_fees"]),
                "renewalHours": _num(r["renewal_hours"]),
                "renewalTime": _num(r["renewal_time_cost"]),
                "renewalTotal": _num(r["renewal_total"]),
                "renewalPerYear": _num(r["renewal_total_per_year"]),
                "burden": _num(r["rbm_burden_per_year"]),
                "hoursAssumed": r["hours_basis"] == "assumed",
                "sources": extra.get("sources", []),
            }
    return out
