"""Cost each licence for the business that holds it: fees and staff time, at entry and at renewal (phase 8 of the
Legislative levers re-evaluation, DECISIONS E-173; docs/scoping_licensing_cost.md).

Reads regulation-register/licence-costs.json (sourced fee facts) and writes:
    data/processed/legislation/licence_costs.csv   one row per licence
    docs/licence_costs.md                          methods note and table

Staff time is valued at the Office of Impact Analysis's work rate, read from the burden calculator
(regulatory-burden-tool/src/engine/parameters.ts, Regulatory Burden Measurement Framework, July 2026). The calculator's
own engine also gives each licence's regulatory burden per business: the yearly average of the staff time over the
framework's 10 years. The framework leaves out government fees (transfers to government), so fees are shown beside it.

    uv run python scripts/licence_costs.py                   # runs the calculator (needs Node and npm install)
    uv run python scripts/licence_costs.py --no-calculator   # works the burden out with the same formula instead
    uv run python scripts/licence_costs.py --check           # re-finds every quoted fee in its source
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "regulation-register" / "licence-costs.json"
TOOL = ROOT / "regulatory-burden-tool"
PARAMETERS = TOOL / "src" / "engine" / "parameters.ts"
OUT = ROOT / "data" / "processed" / "legislation" / "licence_costs.csv"
NOTE = ROOT / "docs" / "licence_costs.md"
YEARS = 10  # the framework's default period (RBM p. 6)
SCENARIOS = ("central", "low", "high")
FIELDS = (
    "requirement",
    "jurisdiction",
    "licence",
    "renewal_years",
    "entry_fees",
    "entry_hours",
    "entry_time_cost",
    "entry_total",
    "renewal_fees",
    "renewal_hours",
    "renewal_time_cost",
    "renewal_total",
    "renewal_total_per_year",
    "entry_total_low",
    "entry_total_high",
    "rbm_burden_per_year",
    "rbm_burden_low",
    "rbm_burden_high",
    "hours_basis",
    "fee_sources",
)


def work_rate() -> float:
    """The framework's hourly rate for work time, from the calculator's single source of truth."""
    text = PARAMETERS.read_text("utf-8")
    m = re.search(r'work:\s*\{[^}]*?hourly:\s*"([0-9.]+)"', text, re.S)
    if not m:
        raise SystemExit(f"no work rate found in {PARAMETERS}")
    return float(m.group(1))


def load() -> dict:
    return json.loads(INPUT.read_text("utf-8"))


def dollars(f: dict, juris: str, units: dict) -> float:
    """A fee in dollars: its amount, or its fee units at the jurisdiction's fee unit value. Where the law rounds a
    unit-based fee down to the dollar (the NT's Revenue Units Act 2009 s 3(2)), so does this."""
    if "amount" in f:
        return float(f["amount"])
    u = units[juris]
    value = float(f["fee_units"]) * float(u["value"])
    return float(math.floor(value + 1e-9)) if u.get("round") == "down-to-dollar" else round(value, 2)


def hours(item: dict, data: dict, when: str, scenario: str) -> float:
    h = (item.get("hours") or data["assumed_hours"])[when]
    return float(h[scenario])


def renewals(k: int, years: int = YEARS) -> int:
    """Renewals in the framework's period for a licence granted in year 1 and renewed every k years."""
    return len(range(1 + k, years + 1, k))


def burden_formula(entry_h: float, renew_h: float, k: int, rate: float) -> float:
    """The calculator's regulatory burden per business: yearly average of staff time over the period."""
    return round((entry_h + renew_h * renewals(k)) * rate / YEARS, 2)


def proposal(rows: list[dict], data: dict, items: dict) -> dict:
    """One calculator proposal: an option for each licence and scenario, each for a single business."""
    options = []
    for r in rows:
        k = int(r["renewal_years"])
        for s in SCENARIOS:
            item = items[r["requirement"]]

            def line(when: str, item: dict = item, s: str = s) -> list[dict]:
                return [{"populationId": "biz", "labour": {"hours": hours(item, data, when, s), "timesPerYear": 1}}]

            options.append(
                {
                    "id": f"{r['requirement']}-{s}",
                    "name": f"{r['licence']} ({s})",
                    "obligations": [
                        {
                            "id": "apply",
                            "name": "Apply for the licence",
                            "category": "administrative",
                            "jurisdiction": "commonwealth" if r["jurisdiction"] == "CTH" else "stateTerritory",
                            "reformed": {
                                "costType": "labour",
                                "timing": {"type": "oneOff", "year": 1},
                                "lines": line("entry"),
                            },
                        },
                        {
                            "id": "renew",
                            "name": "Renew the licence",
                            "category": "administrative",
                            "jurisdiction": "commonwealth" if r["jurisdiction"] == "CTH" else "stateTerritory",
                            "reformed": {
                                "costType": "labour",
                                "timing": {"type": "everyKYears", "k": k, "firstYear": k + 1},
                                "lines": line("renewal"),
                            },
                        },
                    ],
                }
            )
    return {
        "schemaVersion": 1,
        "proposal": {
            "id": "licence-costs",
            "title": "Staff time to get and renew each licence, for one business",
            "description": "Generated by alicia/scripts/licence_costs.py from regulation-register/licence-costs.json.",
            "proposalType": "new",
            "durationYears": YEARS,
            "jurisdiction": "interJurisdictional",
            "baseline": "statusQuo",
            "populations": [{"id": "biz", "label": "One licence holder", "group": "business", "count": 1}],
            "options": options,
        },
    }


def run_calculator(prop: dict) -> dict[str, float]:
    """The calculator's regulatory burden (business, per year) for each option, by option id."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(prop, fh)
        path = fh.name
    out = subprocess.run(
        ["npm", "run", "-s", "rbe", "--", path, "--json"], cwd=TOOL, capture_output=True, text=True, check=True
    ).stdout
    res = json.loads(out)
    return {o["optionId"]: round(float(o["rbe"]["business"]), 2) for o in res["options"]}


def build(use_calculator: bool = True) -> list[dict]:
    from alicia.register.requirements import load_requirements

    data = load()
    reqs = {q.id: q for q in load_requirements().requirements}
    rate = work_rate()
    rows = []
    for rid, item in sorted(data["items"].items()):
        q = reqs[rid]
        j = q.jurisdiction
        k = int(item["renewal_years"])
        entry_fees = round(sum(dollars(f, j, data["fee_units"]) for f in item["fees"] if f["when"] == "entry"), 2)
        # A renewal fee some regulators do not publish (it is worked out for each licensee) is left blank.
        published = not item.get("renewal_fee_unpublished")
        renewal_fees = (
            round(sum(dollars(f, j, data["fee_units"]) for f in item["fees"] if f["when"] == "renewal"), 2)
            if published
            else None
        )
        eh, rh = hours(item, data, "entry", "central"), hours(item, data, "renewal", "central")
        row = {
            "requirement": rid,
            "jurisdiction": j,
            "licence": item["licence"],
            "renewal_years": k,
            "entry_fees": entry_fees,
            "entry_hours": eh,
            "entry_time_cost": round(eh * rate, 2),
            "entry_total": round(entry_fees + eh * rate, 2),
            "renewal_fees": "" if renewal_fees is None else renewal_fees,
            "renewal_hours": rh,
            "renewal_time_cost": round(rh * rate, 2),
            "renewal_total": "" if renewal_fees is None else round(renewal_fees + rh * rate, 2),
            "renewal_total_per_year": "" if renewal_fees is None else round((renewal_fees + rh * rate) / k, 2),
            "entry_total_low": round(entry_fees + hours(item, data, "entry", "low") * rate, 2),
            "entry_total_high": round(entry_fees + hours(item, data, "entry", "high") * rate, 2),
            "hours_basis": "sourced" if item.get("hours") else "assumed",
            "fee_sources": "; ".join(
                dict.fromkeys(f"{f['source']['title']} {f['source']['locator']}" for f in item["fees"])
            ),
        }
        for s, col in zip(SCENARIOS, ("rbm_burden_per_year", "rbm_burden_low", "rbm_burden_high"), strict=True):
            row[col] = burden_formula(hours(item, data, "entry", s), hours(item, data, "renewal", s), k, rate)
        rows.append(row)
    if use_calculator:
        rbe = run_calculator(proposal(rows, data, data["items"]))
        for r in rows:
            for s, col in zip(SCENARIOS, ("rbm_burden_per_year", "rbm_burden_low", "rbm_burden_high"), strict=True):
                r[col] = rbe[f"{r['requirement']}-{s}"]
    return rows


def sources(data: dict) -> list[tuple[str, dict]]:
    """Every quoted source in the input file, with where it is used."""
    out = [(f"fee unit {j}", u["source"]) for j, u in data["fee_units"].items()]
    out += [
        (f"fee unit {j} rounding", u["rounding_source"]) for j, u in data["fee_units"].items() if "rounding_source" in u
    ]
    for rid, item in data["items"].items():
        out += [(rid, f["source"]) for f in item["fees"]]
        for key in ("renewal_source", "risk_source"):
            if item.get(key):
                out.append((rid, item[key]))
        if item.get("hours") and item["hours"].get("source"):
            out.append((rid, item["hours"]["source"]))
    return out


def check_quotes() -> int:
    """Re-find each quote in its source, the way scripts/check_requirement_quotes.py checks requirements."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_requirement_quotes as C

    missing = 0
    texts: dict[str, str] = {}
    for where, s in sources(load()):
        url, kind = s["url"], s["checked"]
        if kind == "register-text" and (m := C.FRL.match(url)):
            key = f"frl-{m.group(1)}"
            texts.setdefault(key, C.norm(C.law_text.frl_latest(m.group(1))[0]))
        elif kind in ("register-text", "document"):
            key = "doc-" + C.hashlib.sha256(url.encode()).hexdigest()[:16]
            texts.setdefault(key, C.norm(C.law_text.fetch_doc(url, key)[0]))
        elif kind == "web-page":
            key = "page-" + C.hashlib.sha256(url.encode()).hexdigest()[:16]
            texts.setdefault(key, C.norm(C.law_text.fetch(url, key)))
        elif kind == "corpus-copy":
            key = f"corpus-{s['corpus_version_id']}"
            texts.setdefault(key, C.norm(C.law_text.corpus_text(s["corpus_version_id"])))
        elif kind == "search-result":  # an official page this environment cannot reach; flagged as unverified
            print(f"not checked: {where}: {s['locator']} (search results only; {url} refused the request)")
            continue
        else:
            raise SystemExit(f"{where}: unknown check type {kind}")
        if C.norm(s["quote"]) not in texts[key]:
            missing += 1
            print(f"NOT FOUND: {where}: {s['locator']}: {s['quote'][:90]}")
    unchecked = sum(1 for _, s in sources(load()) if s["checked"] == "search-result")
    print(f"{len(sources(load())) - missing - unchecked} quote(s) found, {missing} not found, {unchecked} not checked")
    return 1 if missing else 0


def money(x: float | str) -> str:
    return "not published" if x == "" else f"${x:,.0f}"


def note(rows: list[dict], data: dict, rate: float, calculator: bool) -> str:
    a = data["assumed_hours"]
    units = data["fee_units"]
    lines = [
        "# The cost of a licence for the business that holds it",
        "",
        f"*Generated by `alicia/scripts/licence_costs.py` on {dt.date.today():%-d %B %Y} from "
        "`regulation-register/licence-costs.json`. Phase 8 of the [re-evaluation plan](plan_levers_reevaluation.md) "
        "(DECISIONS E-173). Draft: compiled by AI-assisted desk research; not yet checked by a person.*",
        "",
        "## What is counted",
        "",
        "- **Fees**, quoted from the fee regulations. Where a fee is set in fee units, it is converted at the unit's "
        "current value: " + "; ".join(f"{j} ${u['value']} from {u['from']}" for j, u in sorted(units.items())) + ".",
        *[
            f"- **Not verified:** the {j} fee unit value (${u['value']}) is from search results; the official page "
            "refused this environment's requests, so its quote could not be checked."
            for j, u in sorted(units.items())
            if u["source"]["checked"] == "search-result"
        ],
        f"- **Staff time** to apply and to renew, at ${rate:.2f} an hour: the Office of Impact Analysis's rate for "
        "work time (*Regulatory Burden Measurement Framework*, July 2026, p. 12).",
        "- **Entry** is the fees and time to get the licence. **Renewal** is the fees and time each time it is "
        "renewed, and per year divides that by the years between renewals.",
        "- **Regulatory burden** is the framework's own measure, worked out by the calculator in "
        "`regulatory-burden-tool/`"
        + ("" if calculator else " (here by the same formula, without running it)")
        + ": the yearly average of the staff time over 10 years. The framework leaves out government fees, which "
        "are transfers to government, so fees are shown beside it.",
        "- **Not counted:** training and qualifications, insurance, waiting time, and any effect on the wider economy "
        "(out of scope, owner, 16 November 2026).",
        "",
        "## Staff time",
        "",
        f"{a['basis']}",
        "",
        "| | Low | Central | High |",
        "|---|---|---|---|",
        f"| Hours to apply (entry) | {a['entry']['low']} | {a['entry']['central']} | {a['entry']['high']} |",
        f"| Hours to renew | {a['renewal']['low']} | {a['renewal']['central']} | {a['renewal']['high']} |",
        "",
        "## Costs per licence (central)",
        "",
        "| Licence | Entry: fees | Entry: time | Entry total (range) | Renewal every | Renewal: fees and time "
        "| Renewal per year | Regulatory burden a year |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['requirement']}`: {r['licence']} | {money(r['entry_fees'])} | {money(r['entry_time_cost'])} | "
            f"{money(r['entry_total'])} ({money(r['entry_total_low'])}–{money(r['entry_total_high'])}) | "
            f"{r['renewal_years']} year{'s' if r['renewal_years'] > 1 else ''} | {money(r['renewal_total'])} | "
            f"{money(r['renewal_total_per_year'])} | {money(r['rbm_burden_per_year'])} |"
        )
    if data.get("not_costed"):
        lines += ["", "## Pilot licences not yet costed", "", "| Licence | Why |", "|---|---|"]
        lines += [f"| `{rid}` | {why} |" for rid, why in sorted(data["not_costed"].items())]
    if any(r["renewal_fees"] == "" for r in rows):
        lines += [
            "",
            'Where a renewal fee is "not published", the regulator works the annual fee out for each licensee '
            "(from capacity, trading hours and risk); only its entry fees are counted.",
        ]
    lines += [
        "",
        "## Sources",
        "",
        *[f"- `{r['requirement']}`: {r['fee_sources']}." for r in rows],
        "",
        "## Limits",
        "",
        "- **Fees change each year.** Most are indexed; each figure is as at the regulation's current version, or the "
        "fee unit value shown.",
        "- **Staff time is assumed**, as no regulator publishes it; the range shows how much it matters.",
        "- **One class of licence each.** The figures are for a small business holding the basic licence; larger "
        "businesses and other classes pay more.",
        "- **Not yet on the website.** Showing these costs on the levers page and the Industry lens is the website "
        "session's step 8.6.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if "--check" in argv:
        return check_quotes()
    calculator = "--no-calculator" not in argv
    rows = build(calculator)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    NOTE.write_text(note(rows, load(), work_rate(), calculator), "utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(rows)} licences) and {NOTE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
