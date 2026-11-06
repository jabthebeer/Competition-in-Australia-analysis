"""Write docs/legislation_inventory.md: phase A of the legislation-links plan, a review of what the repository already
holds on Commonwealth, state and territory, and council legislation, and what can be reused.

Usage: uv run python scripts/legislation_inventory.py

Counts come from the files (regulation-register/, data/processed/anzsic/, data/processed/geo/); the descriptions of
the register adapters and the reachability checks are as recorded on the date in REACHABILITY.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "regulation-register"
OUT = ROOT / "docs" / "legislation_inventory.md"
JURIS = ("CTH", "NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT")
STATES = JURIS[1:]
TIER = {"cth": "Commonwealth", "state": "State or territory", "local": "Council"}
FUNCTIONS = ("sets-rules", "licenses", "approves", "inspects", "collects", "funds")
LEVEL = {1: "division", 2: "subdivision", 3: "group", 4: "class"}

# What each register adapter in alicia/src/alicia/legislation/ reads (from the modules' docstrings), and whether the
# register, or a source that could list all its laws, answered this environment on the date below.
REACHABILITY = "6 November 2026"
REGISTERS = [
    (
        "CTH",
        "Federal Register of Legislation: public REST API (no key)",
        "Assent or making date, registration, repeal, commencement table, compilations",
        "API answers lookups by name and ID; the in-force filter on all titles returned an error",
    ),
    (
        "NSW",
        "NSW Legislation",
        "Nothing: blocks automated requests",
        "Refused (403); NSW Parliament's site also refused",
    ),
    ("VIC", "Victorian Legislation", "In-force version dates only", "Home page loaded"),
    ("QLD", "Queensland Legislation", "As-made XML; legislative history XML", "Home page loaded"),
    ("WA", "WA Legislation", "Act page (assent); history table", "Home page loaded"),
    (
        "SA",
        "SA Legislation",
        "Nothing: blocked in October 2026",
        "Home page loaded without a challenge; lists not yet tested. "
        "Official XML update packages on data.sa.gov.au (fortnightly)",
    ),
    ("TAS", "Tasmanian Legislation", "Amendment commencement table (JSON); as-made XML", "Home page loaded"),
    ("ACT", "ACT Legislation Register", "Notified date; commencement table", "Home page loaded"),
    ("NT", "NT Legislation", "As-assented page", "Home page loaded"),
]
OTHER_SOURCES = [
    ("AustLII", "Free legal information institute (not official)", "Refused (Cloudflare block)"),
    (
        "Open Australian Legal Corpus (Isaacus, v7.1.0)",
        "CC BY 4.0; in-force statutes and regulations of CTH, NSW, Qld, WA, SA, Tas as at 10 March 2025, with each "
        "law's official register URL",
        "Dataset card read; corpus not downloaded",
    ),
    (
        "ABLIS (business.gov.au)",
        "Licences and obligations by ANZSIC activity, jurisdiction, tier and council area; API needs a key",
        "Site and public API documents read; key applied for by the owner",
    ),
]
DOCS = [
    (
        "industry_regulation.md",
        "Regulatory complexity by class: regimes, tiers, touchpoints, overlaps, issues",
        "All three; councils as one party per regime",
    ),
    (
        "responsibility_and_history.md",
        "Who administers and regulates each register item; later changes",
        "Commonwealth and states",
    ),
    (
        "legislation_gap_scan.md",
        "Reforms missing from the register, chosen for evaluability (October 2026)",
        "Commonwealth and states",
    ),
    ("register_review_framework.md", "The register against the productivity framework; gaps to add", "All"),
    ("recommendations.md", "65 recommendations and the bodies that would act", "Commonwealth and states"),
    ("productivity_framework.md", "The framework the register's marks use", "n/a"),
    ("fact_check_2026-11.md", "Dates and quotes checked against sources; which sites block checks", "All"),
    ("anzsic_classes.md", "The 506 classes, primary activities and marks", "n/a"),
]


def load(folder: str) -> list[dict]:
    return [json.loads(p.read_text("utf-8")) for p in sorted((REG / folder).glob("*.json"))]


def pct(a: int, b: int) -> str:
    return f"{a / b:.0%}" if b else "n/a"


def table(head: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


def main() -> None:
    records = load("records")
    regimes = load("regimes")
    bodies = json.loads((REG / "bodies.json").read_text("utf-8"))
    recs_by_id = {r["id"]: r for r in records}
    marks = list(csv.DictReader((ROOT / "data/processed/anzsic/class_marks.csv").open(encoding="utf-8")))
    classes = json.loads((ROOT / "data/processed/anzsic/anzsic2006_classes.json").read_text("utf-8"))["rows"]

    # --- Register records by jurisdiction
    rec_rows, tot = [], Counter()
    for j in JURIS:
        rs = [r for r in records if r["jurisdiction"] == j]
        inst = [i for r in rs for i in r["instruments"]]
        with_id = [i for i in inst if i.get("register_url") or i.get("register_id")]
        codes = [c for r in rs for c in r["industries"]]
        cls = [c for c in codes if len(c["anzsic"]) == 4]
        kinds = Counter(r["kind"] for r in rs)
        row = [
            j,
            len(rs),
            kinds["reform"],
            kinds["setting"],
            kinds["barrier"],
            len(inst),
            f"{len(with_id)} ({pct(len(with_id), len(inst))})",
            sum(r["verified"]["dates"] for r in rs),
            f"{len(cls)} of {len(codes)}",
            sum(1 for r in rs if not r["industries"]),
        ]
        rec_rows.append(row)
        for k, v in zip(
            ("n", "reform", "setting", "barrier", "inst", "id", "ver", "cls", "codes", "none"),
            (
                len(rs),
                kinds["reform"],
                kinds["setting"],
                kinds["barrier"],
                len(inst),
                len(with_id),
                sum(r["verified"]["dates"] for r in rs),
                len(cls),
                len(codes),
                sum(1 for r in rs if not r["industries"]),
            ),
            strict=True,
        ):
            tot[k] += v
    rec_rows.append(
        [
            "**All**",
            tot["n"],
            tot["reform"],
            tot["setting"],
            tot["barrier"],
            tot["inst"],
            f"{tot['id']} ({pct(tot['id'], tot['inst'])})",
            tot["ver"],
            f"{tot['cls']} of {tot['codes']}",
            tot["none"],
        ]
    )
    local_records = sum(1 for r in records if r["jurisdiction"] not in JURIS)

    # --- Regime layers by tier and function
    layer_ct: dict[str, Counter] = defaultdict(Counter)
    no_body = Counter()
    for g in regimes:
        for layer in g["layers"]:
            layer_ct[layer["tier"]][layer["function"]] += 1
            if not layer["bodies"]:
                no_body[layer["tier"]] += 1
    layer_rows = [
        [TIER[t]]
        + [layer_ct[t][f] or "" for f in FUNCTIONS]
        + [sum(layer_ct[t].values()), f"{no_body[t]} of {sum(layer_ct[t].values())}"]
        for t in ("cth", "state", "local")
    ]
    local_regimes = sorted(g["name"] for g in regimes if any(lyr["tier"] == "local" for lyr in g["layers"]))

    # --- State versions of regimes that differ by state
    varying = [g for g in regimes if g["consistency"] in ("varies", "harmonised", "recognised")]
    cover = []
    for g in varying:
        states = {recs_by_id[x]["jurisdiction"] for x in g["records"] if x in recs_by_id} & set(STATES)
        cover.append((g, states))
    all8 = sorted(g["name"] for g, s in cover if len(s) == 8)
    some = sorted((g["name"], len(s)) for g, s in cover if 0 < len(s) < 8)
    none = sorted(g["name"] for g, s in cover if not s)

    # --- Industry coding
    rec_levels = Counter(
        (LEVEL[len(c["anzsic"]) if not c["anzsic"].isalpha() else 1], c["exposure"])
        for r in records
        for c in r["industries"]
    )
    reg_levels: dict[str, Counter] = defaultdict(Counter)
    for g in regimes:
        for c in g["coverage"]["anzsic"]:
            reg_levels[g["scope"]][LEVEL[1 if c.isalpha() else len(c)]] += 1
    sector_div = sorted(
        g["name"] for g in regimes if g["scope"] == "sector" and any(c.isalpha() for c in g["coverage"]["anzsic"])
    )

    # --- Bodies
    body_ct: dict[str, Counter] = defaultdict(Counter)
    for b in bodies:
        body_ct[b["jurisdiction"]][b["type"]] += 1
    body_rows = [
        [
            j,
            body_ct[j]["department"] or "",
            body_ct[j]["agency"] or "",
            body_ct[j]["regulator"] or "",
            sum(body_ct[j].values()),
        ]
        for j in (*JURIS, "national")
        if body_ct[j]
    ]

    # --- Sources behind the regimes
    basis_pub = Counter(b["publisher"] for g in regimes for b in g["basis"])
    issue_pub = Counter(e["publisher"] for g in regimes for i in g["issues"] for e in i["evidence"])
    n_issues = sum(len(g["issues"]) for g in regimes)
    council_issues = sum(1 for g in regimes for i in g["issues"] if i["tag"] == "local-variation")

    n_act = sum(len(c["primary_activities"]) for c in classes)
    geo = ROOT / "data" / "processed" / "geo" / "postcode_2021_to_asgs.parquet"

    o = [
        "# Legislation inventory: what the repository holds at each tier",
        "",
        f"*Generated by `alicia/scripts/legislation_inventory.py` on {dt.date.today():%-d %B %Y}. Phase A of the "
        "[legislation-links plan](plan_legislation_links.md) (DECISIONS E-116). Counts are from the files; the "
        f"register checks are as on {REACHABILITY}. Everything in the register is an AI-assisted draft, not yet "
        "checked by a person.*",
        "",
        "## Summary",
        "",
        f"- **Commonwealth and states are partly covered; councils not at all.** The register holds {tot['n']} items "
        f"with {tot['inst']} instruments, all Commonwealth, state or territory ({local_records} council items). "
        f"The {len(regimes)} regimes name councils as a tier in {len(local_regimes)} regimes, as one party each, with "
        f"no council laws, bodies or planning terms behind them.",
        "- **The register was built to evaluate reforms, not to list every law.** Items were chosen as reforms and "
        "settings that matter for competition, so they are a sample of the statute book, not an inventory of it. "
        "No list of all laws in force exists yet at any tier.",
        f"- **Few instruments can be traced to a register entry.** {tot['id']} of {tot['inst']} instruments "
        f"({pct(tot['id'], tot['inst'])}) carry a register ID or link. The rest are titles only.",
        f"- **The industry coding is at the right level.** {tot['cls']} of {tot['codes']} industry codes on register "
        "items are classes. Regimes use class codes for most industry-specific coverage, but some map a whole class "
        "where a law covers part of it (pharmacy rules on all of 4271).",
        f"- **State versions are uneven.** Of {len(varying)} regimes whose rules differ by state, {len(all8)} have a "
        f"register item in all eight states and territories, {len(some)} in some, and {len(none)} in none.",
        f"- **The regimes' evidence is mostly guidance.** {basis_pub.get('business.gov.au', 0)} of "
        f"{sum(basis_pub.values())} sources for the regime descriptions are business.gov.au pages, with the "
        "Productivity Commission next. Both are good for what a business deals with, but neither is the law itself.",
        "- **Reusable machinery exists.** The register adapters read dates for a named law from the Federal Register "
        "and six state and territory registers. They need extending to list every law in force, and NSW (and "
        "possibly SA) needs another source.",
        "",
        "## 1. Register items by jurisdiction",
        "",
        "`regulation-register/records/`: reforms, settings and barriers, one per jurisdiction.",
        "",
        *table(
            [
                "Jurisdiction",
                "Items",
                "Reforms",
                "Settings",
                "Barriers",
                "Instruments",
                "With register ID or link",
                "Dates verified",
                "Industry codes at class level",
                "Economy-wide (no industry)",
            ],
            rec_rows,
        ),
        "",
        "Reuse: each instrument is a seed for the catalogue of laws (phases C and D). Items keep their framework "
        "marks for the page. Instruments without a register ID need one before they can be linked.",
        "",
        "## 2. Regimes: who does what, by tier",
        "",
        f"`regulation-register/regimes/`: {len(regimes)} regimes "
        f"({sum(1 for g in regimes if g['scope'] == 'cross-cutting')} cross-cutting, "
        f"{sum(1 for g in regimes if g['scope'] == 'sector')} industry-specific). Each layer is one function "
        "performed by one tier of government.",
        "",
        *table(["Tier", *FUNCTIONS, "Layers", "Layers naming no body"], layer_rows),
        "",
        f"Regimes with a council layer ({len(local_regimes)}): " + "; ".join(local_regimes) + ".",
        "",
        f"Issues: {n_issues} evidenced issues, {council_issues} of them tagged as varying council by council.",
        "",
        "Reuse: regimes stay as the grouping a business sees, and each requirement in the new tables belongs to one. "
        "Their class maps become hypotheses to test against the laws (phase B). Their council layers say where "
        "council laws must be looked for in phase E.",
        "",
        "## 3. State versions of regimes that differ by state",
        "",
        f"Of {len(varying)} regimes whose rules differ between states (state laws, model laws adopted with "
        "variations, or licences recognised across states), the number of the eight states and territories with "
        "a register item:",
        "",
        f"- **All eight ({len(all8)}):** " + "; ".join(all8) + ".",
        f"- **Some ({len(some)}):** " + "; ".join(f"{n} ({k})" for n, k in some) + ".",
        f"- **None ({len(none)}):** " + "; ".join(none) + ".",
        "",
        "Reuse: the 'all eight' regimes are the pattern for phase D; the others show where state laws have not been "
        "collected yet.",
        "",
        "## 4. Industry coding",
        "",
        *table(
            [
                "Level",
                "Register codes, direct",
                "Register codes, indirect",
                "Regime codes, cross-cutting",
                "Regime codes, industry-specific",
            ],
            [
                [
                    lv,
                    rec_levels[(lv, "direct")],
                    rec_levels[(lv, "indirect")],
                    reg_levels["cross-cutting"][lv],
                    reg_levels["sector"][lv],
                ]
                for lv in ("division", "subdivision", "group", "class")
            ],
        ),
        "",
        f"Industry-specific regimes that include a whole division ({len(sector_div)}): " + "; ".join(sector_div) + ". "
        "These need checking against the laws, since a division spans many activities.",
        "",
        f"The join key is ready: 506 classes and {n_act:,} ABS primary activities (`data/processed/anzsic/`), with "
        f"{len(marks)} classes marked as mainly government, households or non-profit institutions serving "
        "households (`class_marks.csv`).",
        "",
        "## 5. Government bodies",
        "",
        f"`regulation-register/bodies.json`: {len(bodies)} bodies, each with its department, source and whether it "
        "still exists. No councils.",
        "",
        *table(["Jurisdiction", "Departments", "Agencies", "Regulators", "Total"], body_rows),
        "",
        "Reuse: administering bodies for the laws in phases C and D. Councils would be added in phase E, keyed by "
        f"ABS local government area ({'548 codes in ASGS 2021' if geo.exists() else 'ASGS'}, "
        "`data/processed/geo/`).",
        "",
        "## 6. Sources behind the regimes",
        "",
        *table(
            ["Publisher", "Regime descriptions", "Issue evidence"],
            [
                [p, basis_pub.get(p, ""), issue_pub.get(p, "")]
                for p in sorted(set(basis_pub) | set(issue_pub), key=lambda p: -(basis_pub[p] + issue_pub[p]))
            ],
        ),
        "",
        "Every quote was checked against its source's full text. They describe what a business does, not the "
        "provisions of the law, so phases C to E add the law itself.",
        "",
        "## 7. Reading the registers",
        "",
        f"The adapters in `alicia/src/alicia/legislation/` read dates for a law the register is asked about by name "
        f"or ID. Listing every law in force is new work. Checks on {REACHABILITY}:",
        "",
        *table(["Jurisdiction", "Register", "What the adapter reads", "Reachable from here"], REGISTERS),
        "",
        *table(["Other source", "What it is", "Status"], OTHER_SOURCES),
        "",
        "## 8. Notes in `docs/` that bear on the tiers",
        "",
        *table(["Note", "What it holds", "Tiers"], [[f"[`{d}`]({d})", w, t] for d, w, t in DOCS]),
        "",
        "## 9. What carries into phase B",
        "",
        "- **Reuse as they are:** the class list and marks, the bodies, the regime groupings and issues, and the "
        "Federal Register adapter.",
        "- **Reuse as starting points:** register instruments (seeds for the catalogue), regime class maps "
        "(hypotheses to test), and the state adapters (to extend from one law to all laws).",
        "- **To fix in the new tables:** every instrument needs a register ID; links that cover part of a class are "
        "qualified with ABS primary activities; and industry-specific regimes coded to a whole division are "
        "checked.",
        "- **New:**",
        "  - a catalogue of every law in force at each tier;",
        "  - councils as bodies, with their local laws;",
        "  - a crosswalk from classes to each state's planning land-use terms;",
        "  - a source for NSW (D2), and ABLIS for the completeness check (D3).",
    ]
    OUT.write_text("\n".join(o) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
