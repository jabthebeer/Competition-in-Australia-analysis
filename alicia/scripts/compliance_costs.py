"""Cost each requirement on the register: the staff time it takes the businesses it binds, a year (DECISIONS E-700).

Reads the requirements, regulation-register/compliance-cost-assumptions.json, the licence costs and the ABS business
counts, and writes:
    data/processed/legislation/compliance_costs.csv           one row per requirement (costed or not, and why)
    data/processed/legislation/compliance_costs_by_class.csv  the cost in each ANZSIC class (Commonwealth, state)
    docs/compliance_costs.md                                   methods note, assumptions, a sample and the totals

The method is in alicia/src/alicia/costing/compliance.py. Builds are deterministic (no timestamps), so a test can
check the committed files are current.

    uv run python scripts/compliance_costs.py
    uv run python scripts/compliance_costs.py --check   # exit 1 if the committed files are out of date
"""

from __future__ import annotations

import csv
import io
import random
import sys
from pathlib import Path

from alicia import anzsic
from alicia.costing import compliance as C
from alicia.register.requirements import KIND_LABELS, load_requirements

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed" / "legislation" / "compliance_costs.csv"
OUT_CLASS = ROOT / "data" / "processed" / "legislation" / "compliance_costs_by_class.csv"
NOTE = ROOT / "docs" / "compliance_costs.md"
SAMPLE_SEED = 20261127
SAMPLE_SIZE = 20

FIELDS = (
    "requirement",
    "jurisdiction",
    "tier",
    "kind",
    "title",
    "costed",
    "why_not",
    "task",
    "hours_from",
    "size_basis",
    "upper_bound",
    "upper_why",
    "classes",
    "businesses",
    "share_pct",
    "new_per_year",
    "start_hours_low",
    "start_hours",
    "start_hours_high",
    "yearly_hours_low",
    "yearly_hours",
    "yearly_hours_high",
    "rate",
    "per_business_start",
    "per_business_year",
    "cost_low",
    "cost",
    "cost_high",
    "fees_start",
    "fees_yearly",
    "fees_total",
    "records",
    "counts_year",
)
CLASS_FIELDS = (
    "anzsic",
    "name",
    "division",
    "businesses",
    "requirements",
    "cth_low",
    "cth",
    "cth_high",
    "state_low",
    "state",
    "state_high",
    "cth_upper",
    "state_upper",
    "per_business_cth",
    "per_business_all",
)


def r2(x):
    return "" if x is None else f"{x:.2f}"


def row_out(r: dict) -> dict:
    base = {k: "" for k in FIELDS}
    base.update(
        requirement=r["id"],
        jurisdiction=r["jurisdiction"],
        tier=r["tier"],
        kind=r["kind"],
        title=r["title"],
        costed="yes" if r["costed"] else "no",
        why_not=r["why"] or "",
        records=";".join(r["records"]),
    )
    if not r["costed"]:
        return base
    base.update(
        task=r["task"],
        hours_from=r["hoursFrom"],
        size_basis=r["sizeBasis"],
        upper_bound="yes" if r["upper"] else "no",
        upper_why="; ".join(r["upperWhy"]),
        classes=r["classes"],
        businesses=r["businesses"],
        share_pct=r["share"],
        new_per_year=r["newPerYear"],
        rate=r2(r["rate"]),
        per_business_start=r2(r["perBusinessStart"]["central"]),
        per_business_year=r2(r["perBusinessYear"]["central"]),
        fees_start=r2(r["feesStart"]),
        fees_yearly=r2(r["feesYearly"]),
        fees_total=r2(r["feesTotal"]),
        counts_year=r["year"],
        **{
            f"start_hours{s}": f"{r['startHours'][k]:g}"
            for k, s in (("low", "_low"), ("central", ""), ("high", "_high"))
        },
        **{
            f"yearly_hours{s}": f"{r['yearlyHours'][k]:g}"
            for k, s in (("low", "_low"), ("central", ""), ("high", "_high"))
        },
        **{f"cost{s}": r2(r["cost"][k]) for k, s in (("low", "_low"), ("central", ""), ("high", "_high"))},
    )
    return base


def class_rows(classes: dict) -> list[dict]:
    out = []
    for c in sorted(classes):
        a = classes[c]
        n = a["businesses"] or 0
        out.append(
            {
                "anzsic": c,
                "name": anzsic.name(c),
                "division": anzsic.division(c),
                "businesses": n,
                "requirements": a["requirements"],
                "cth_low": r2(a["cth"]["low"]),
                "cth": r2(a["cth"]["central"]),
                "cth_high": r2(a["cth"]["high"]),
                "state_low": r2(a["state"]["low"]),
                "state": r2(a["state"]["central"]),
                "state_high": r2(a["state"]["high"]),
                "cth_upper": r2(a["cthUpper"]["central"]),
                "state_upper": r2(a["stateUpper"]["central"]),
                "per_business_cth": r2(a["cth"]["central"] / n) if n else "",
                "per_business_all": r2((a["cth"]["central"] + a["state"]["central"]) / n) if n else "",
            }
        )
    return out


def csv_text(rows: list[dict], fields) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def hrs(h: dict) -> str:
    return f"{h['central']:g} ({h['low']:g} to {h['high']:g})"


def hours_word(h: float) -> str:
    return f"{h:g} hour" + ("" if h == 1 else "s")


def working(r: dict) -> str:
    """The sum in words, as the page shows it."""
    parts = []
    if r["startHours"]["central"]:
        parts.append(
            f"{hours_word(r['startHours']['central'])} × ${r['rate']:.2f} × {r['newPerYear']:,} new businesses a year"
        )
    if r["yearlyHours"]["central"]:
        parts.append(f"{hours_word(r['yearlyHours']['central'])} × ${r['rate']:.2f} × {r['businesses']:,} businesses")
    return " + ".join(parts) + f" = {C.money(r['cost']['central'])}"


def note(out: dict, assumptions: dict) -> str:
    rows = out["rows"]
    costed = [r for r in rows if r["costed"]]
    t, n = out["totals"], out["counts"]
    rate = out["rate"]
    kinds = assumptions["kinds"]
    by_kind: dict[str, list] = {}
    for r in rows:
        by_kind.setdefault(r["kind"], []).append(r)
    lines = [
        "# Compliance cost of each requirement on the register",
        "",
        "*Generated by `alicia/scripts/compliance_costs.py` from "
        "`regulation-register/compliance-cost-assumptions.json`, "
        f"the requirements and the ABS business counts (June {out['year']}). Do not edit by hand. DECISIONS E-700. "
        "Draft: compiled by AI-assisted desk research; not yet checked by a person.*",
        "",
        "## The figure",
        "",
        "Each requirement's **compliance cost** is the staff time it takes the businesses it binds, a year, valued as "
        "the Office of Impact Analysis (OIA) values it in its *Regulatory Burden Measurement Framework* (July 2026):",
        "",
        f"> cost a year = ${rate:.2f} an hour × (hours to start × new businesses a year + hours each year × businesses "
        "operating)",
        "",
        f"- **${rate:.2f} an hour** is the OIA's default rate for work time: $52.31 × 1.75 for on-costs and overheads "
        "(framework, p. 12). It is read from the burden calculator in `regulatory-burden-tool/`.",
        "- **Hours** are set for each kind of requirement (table below). Every one is **assumed**: no regulator or OIA "
        "publication gives standard hours for these tasks. The 31 costed licences use the licence costs' hours "
        "(`docs/licence_costs.md`, E-175), with renewal hours spread over the years between renewals.",
        "- **Businesses** are from the ABS *Counts of Australian Businesses* by industry class, state and employment "
        "size, for the classes and states each requirement reaches. A state's rule counts that state's businesses; "
        "a Commonwealth rule counts every state's. Its size test picks the size bands, as for the impact classes "
        "(E-178): a rule from the first employee counts employing businesses only. **New businesses** are the ABS "
        "entries over the year in the same bands.",
        "- **Low and high** values use the low and high hours. The rate and the counts are the same in each.",
        "- Figures are shown to 2 significant figures, because the hours are assumed.",
        "",
        "In a steady state every entrant pays the start-up hours once, so this is the framework's yearly average over "
        "10 years for a steady flow of entrants, in constant prices with no discounting (framework, pp. 6–7).",
        "",
        "## Upper bounds, and rules not counted",
        "",
        '- A rule that binds only **some** of the businesses counted is an **upper bound**, shown as "up to" and kept '
        "out of the headline totals. That is a rule above a size threshold the ABS bands can't pin down (a turnover of "
        "$100 million, say), one limited to some legal forms, or one that binds only businesses doing an activity "
        '("if it sells alcohol").',
        "- Where that upper bound covers **a quarter or more** of the businesses in the rule's jurisdiction, it says "
        "nothing useful about the businesses actually bound, so the rule is **not counted**, and says why.",
        "- A **council's** rule is not costed: business counts by council are not in the panel.",
        "- Requirements of kind **other** are not costed: the obligation varies too much to assume hours.",
        "",
        "## What is left out",
        "",
        "- **The cost of meeting a standard**: equipment, building work, training, insurance premiums. The OIA calls "
        "these substantive compliance costs. They vary too much to assume from public data, so for standards the "
        "figure covers only the time to learn the standard and check against it. This is the largest gap.",
        "- **Delay costs**: income lost while waiting for an approval.",
        "- **Fees and taxes** paid to government. The framework leaves them out (p. 4). Where fees are known (the "
        "licences), they are shown beside the figure, never in it.",
        "- **Effects on competition and prices**, which the framework also leaves out.",
        "- **Businesses that would do it anyway.** The framework allows these to be netted off; none are here, so "
        "figures lean high.",
        "- **Businesses not registered for GST**, which the ABS counts leave out, so very small operators are missed.",
        "",
        "## Hours assumed for each kind",
        "",
        "| Kind | Requirements | Costed | Task costed | Hours to start | Hours each year | Basis |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for k in KIND_LABELS:
        rs = by_kind.get(k, [])
        a = kinds.get(k, {})
        if a.get("costed") is False:
            lines.append(f"| {KIND_LABELS[k]} | {len(rs)} | 0 | {a['task']} | – | – | {a['basis']} |")
            continue
        lines.append(
            f"| {KIND_LABELS[k]} | {len(rs)} | {sum(1 for r in rs if r['costed'])} | {a['task']} | "
            f"{hrs(a['start_hours'])} | {hrs(a['yearly_hours'])} | {a['basis']} |"
        )
    withheld = [r for r in rows if r.get("withheld")]
    lines += [
        "",
        "## Totals",
        "",
        f"Of {n['requirements']:,} requirements, {n['costed']:,} are costed: {n['costed'] - n['upper']:,} exactly and "
        f"{n['upper']:,} as upper bounds. {n['withheld']:,} are not counted because their upper bound covers a quarter "
        f"or more of their jurisdiction's businesses, and {n['requirements'] - n['costed'] - n['withheld']:,} are "
        "councils' rules or of kind other.",
        "",
        "| | Low | Central | High |",
        "|---|---|---|---|",
        f"| Commonwealth requirements, counted exactly | {C.money(t['exactCth']['low'])} | "
        f"{C.money(t['exactCth']['central'])} | {C.money(t['exactCth']['high'])} |",
        f"| State and territory requirements, counted exactly | {C.money(t['exactState']['low'])} | "
        f"{C.money(t['exactState']['central'])} | {C.money(t['exactState']['high'])} |",
        f"| **All requirements counted exactly** | {C.money(t['exact']['low'])} | "
        f"**{C.money(t['exact']['central'])}** | "
        f"{C.money(t['exact']['high'])} |",
        f"| Upper bounds, apart (up to) | {C.money(t['upper']['low'])} | {C.money(t['upper']['central'])} | "
        f"{C.money(t['upper']['high'])} |",
        "",
        "The total is a sum of assumed paperwork time, not an estimate of the burden of regulation. It leaves out "
        "substantive compliance costs, the rules not counted, and every law not yet on the register (Victoria has "
        "only 32 requirements so far). State totals are not compared, because each state's law is recorded to a "
        "different extent.",
        "",
        "## Largest costs counted exactly",
        "",
        "| Requirement | Kind | Businesses bound | Working (central) | Range |",
        "|---|---|---|---|---|",
    ]
    exact = sorted([r for r in costed if not r["upper"]], key=lambda r: (-r["cost"]["central"], r["id"]))
    for r in exact[:20]:
        lines.append(
            f"| `{r['id']}`: {r['title']} | {r['kind']} | {r['businesses']:,} ({r['sizeBasisLabel']}) | {working(r)} | "
            f"{C.money(r['cost']['low'])} to {C.money(r['cost']['high'])} |"
        )
    rng = random.Random(SAMPLE_SEED)
    sample = sorted(rng.sample(costed, min(SAMPLE_SIZE, len(costed))), key=lambda r: r["id"])
    lines += [
        "",
        "## A sample to check",
        "",
        f"{len(sample)} costed requirements drawn at random (seed {SAMPLE_SEED}), each with its working, for a person "
        "to check the hours, the businesses counted and the result.",
        "",
        "| Requirement | Hours from | Businesses bound | Working (central) | Upper bound? |",
        "|---|---|---|---|---|",
    ]
    for r in sample:
        lines.append(
            f"| `{r['id']}`: {r['title']} | {r['hoursFrom']} | {r['businesses']:,} ({r['sizeBasisLabel']}) | "
            f"{working(r)} | {'up to: ' + '; '.join(r['upperWhy']) if r['upper'] else 'no'} |"
        )
    lines += [
        "",
        "## Rules not counted because their upper bound is too wide",
        "",
        "| Requirement | Why |",
        "|---|---|",
    ]
    for r in withheld:
        lines.append(f"| `{r['id']}`: {r['title']} | {r['why']} |")
    lines += [
        "",
        "## Known coding gaps that move a figure",
        "",
        '- `cth-payment-times-reporting` binds only large businesses ("reporting entities"), but its triggers carry '
        "no revenue threshold, so it is counted at every business. Adding its threshold, with a quote, would make it "
        "an upper bound.",
        "- A turnover or revenue threshold above GST's $75,000 can't be counted from employment size bands. The ABS "
        "publishes counts by turnover band too; adding them would tighten these upper bounds.",
        "",
        "## Files",
        "",
        "- `data/processed/legislation/compliance_costs.csv`: one row per requirement, with every input and result.",
        "- `data/processed/legislation/compliance_costs_by_class.csv`: the cost in each ANZSIC class, Commonwealth "
        "and state rules apart, and per business in the class.",
        "",
    ]
    return "\n".join(lines)


def build() -> dict[Path, str]:
    assumptions = C.load_assumptions()
    out = C.cost_all(load_requirements().requirements, assumptions=assumptions)
    return {
        OUT: csv_text([row_out(r) for r in out["rows"]], FIELDS),
        OUT_CLASS: csv_text(class_rows(out["classes"]), CLASS_FIELDS),
        NOTE: note(out, assumptions),
    }


def main(argv: list[str]) -> int:
    files = build()
    if "--check" in argv:
        stale = [p for p, text in files.items() if not p.exists() or p.read_text("utf-8") != text]
        for p in stale:
            print(f"out of date: {p.relative_to(ROOT)}")
        return 1 if stale else 0
    for p, text in files.items():
        p.write_text(text, "utf-8")
        print(f"wrote {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
