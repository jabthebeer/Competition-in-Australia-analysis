"""Council families across the sample councils (docs/plan_councils.md, batch E-7, DECISIONS E-366).

For each council family and each of the 18 sample councils outside Victoria, the table says whether the register
holds the requirement or, if not, what was searched and why it is missing. It also checks that each family is drafted
consistently across councils (kind, regime, confidence and quoted law).

Inputs:
- regulation-register/requirements/local/<LGA code>/ (the council requirements);
- data/processed/legislation/council_sample.csv (scripts/council_sample.py);
- CELLS below: the search result for each council and family the register does not hold, recorded by hand in E-7.

Outputs:
- data/processed/legislation/council_variation.csv: one row per family and council;
- data/processed/legislation/council_variation_summary.csv: one row per family.

Run from alicia/: uv run python scripts/council_variation.py
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "regulation-register" / "requirements" / "local"
SAMPLE = ROOT / "data" / "processed" / "legislation" / "council_sample.csv"
OUT = ROOT / "data" / "processed" / "legislation" / "council_variation.csv"
SUMMARY = ROOT / "data" / "processed" / "legislation" / "council_variation_summary.csv"

FAMILIES = {
    "council-busking-permit": "Busking",
    "council-filming-permit": "Filming",
    "council-outdoor-dining-permit": "Outdoor dining",
    "council-street-trading-permit": "Street trading and stalls",
    "council-market-licence": "Markets",
    "council-advertising-sign-approval": "Advertising signs",
    "council-temporary-event-approval": "Temporary events",
    "council-caravan-park-approval": "Caravan parks",
}
ALL = tuple(FAMILIES)

# Why a council and family has no requirement. Status:
# - state-act: approved under a state Act, so counted once as a state requirement (methods rule 7);
# - covered: the activity falls under another council requirement already recorded;
# - not-found: the council's laws named in the note were read and have no such provision;
# - to-check: a law that likely holds it was identified but not read, or the clause was not located;
# - blocked: the council's laws could not be read (site refuses automated requests, scanned image, or down);
# - none-published: the council publishes no local laws or by-laws.
NSW_S68 = "Local Government Act 1993 (NSW) s 68"
CELLS: dict[str, dict[str, tuple[str, str]]] = {
    "17200": {  # Sydney
        "council-street-trading-permit": ("state-act", f"{NSW_S68}, table, Part F item 7 and Part E item 2"),
        "council-caravan-park-approval": ("state-act", f"{NSW_S68}, table, Part F item 2"),
        "council-market-licence": ("to-check", "City of Sydney approvals policies not read"),
        "council-advertising-sign-approval": ("to-check", "NSW signage is set by planning instruments; not read"),
        "council-temporary-event-approval": ("to-check", "City of Sydney approvals policies not read"),
    },
    "16950": {  # Shoalhaven
        "council-busking-permit": ("state-act", f"{NSW_S68}, table, Part D item 4"),
        "council-filming-permit": ("state-act", "Local Government Act 1993 (NSW) ch 7 pt 1 div 4 (ss 114 to 121)"),
        "council-outdoor-dining-permit": ("state-act", "Roads Act 1993 (NSW) s 125"),
        "council-street-trading-permit": ("state-act", f"{NSW_S68}, table, Part F item 7 and Part E item 2"),
        "council-caravan-park-approval": ("state-act", f"{NSW_S68}, table, Part F item 2"),
        "council-market-licence": ("to-check", "Council approvals policies not read"),
        "council-advertising-sign-approval": ("to-check", "NSW signage is set by planning instruments; not read"),
        "council-temporary-event-approval": ("to-check", "Council approvals policies not read"),
    },
    "31000": {  # Brisbane
        "council-market-licence": ("to-check", "Not found in the 4 local laws read; the other 30 not read"),
        "council-caravan-park-approval": (
            "to-check",
            "Local Law (Caravan Parks and Relocatable Home Parks) 2000 identified on the council's local laws page, "
            "not read; only its subordinate local law was read",
        ),
    },
    "36910": {  # Toowoomba
        "council-outdoor-dining-permit": (
            "covered",
            "Commercial use of local government controlled areas and roads (SLL 1.2) covers tables and chairs on roads",
        ),
        "council-busking-permit": ("to-check", "Subordinate local laws other than 1.2, 1.8 and 1.12 not read"),
        "council-filming-permit": ("to-check", "Subordinate local laws other than 1.2, 1.8 and 1.12 not read"),
        "council-market-licence": ("to-check", "Subordinate local laws other than 1.2, 1.8 and 1.12 not read"),
        "council-advertising-sign-approval": (
            "to-check",
            "Subordinate local law on advertising devices not found online",
        ),
    },
    "37400": {  # Winton
        "council-outdoor-dining-permit": (
            "covered",
            "Commercial use of local government controlled areas and "
            "roads covers serving food or drink on a road (SLL 1 sch 8 s 3(c))",
        ),
        "council-busking-permit": ("not-found", "Not a prescribed activity in Local Law No. 1 sch 2"),
        "council-filming-permit": ("not-found", "Not a prescribed activity in Local Law No. 1 sch 2"),
        "council-market-licence": (
            "covered",
            "A single-day market stall is a prescribed public place activity "
            "(SLL 1 sch 6 item 2); no separate market licence",
        ),
    },
    "57080": {  # Perth
        "council-market-licence": ("to-check", "Other City of Perth local laws not reachable"),
        "council-advertising-sign-approval": ("to-check", "Other City of Perth local laws not reachable"),
        "council-temporary-event-approval": (
            "to-check",
            "Local Government Property Local Law 2005 cl 29(1)(h) (conduct a function) not yet drafted",
        ),
        "council-caravan-park-approval": (
            "state-act",
            "Caravan Parks and Camping Grounds Act 1995 (WA); not checked against the WA state requirements",
        ),
    },
    "51260": {  # Busselton
        "council-filming-permit": (
            "not-found",
            "Not in the Activities in Thoroughfares and Public Places and Trading Local Law 2026",
        ),
        "council-market-licence": ("to-check", "Property Local Law 2010 not read"),
        "council-temporary-event-approval": ("to-check", "Property Local Law 2010 not read"),
        "council-caravan-park-approval": (
            "state-act",
            "Caravan Parks and Camping Grounds Act 1995 (WA); not checked against the WA state requirements",
        ),
    },
    "58540": {  # Victoria Plains
        "council-busking-permit": (
            "to-check",
            "Entertainment licence named in cl 1.8(c); the clause requiring it not located",
        ),
        "council-outdoor-dining-permit": (
            "to-check",
            "Food sales licence named in cl 1.8(d); the clause requiring it not located",
        ),
        "council-market-licence": (
            "to-check",
            "Market licence named in cl 1.8(b); the clause requiring it not located",
        ),
        "council-filming-permit": (
            "not-found",
            "Not in the Public Places and Local Government Property Local Law 2018",
        ),
        "council-caravan-park-approval": (
            "state-act",
            "Caravan Parks and Camping Grounds Act 1995 (WA); not checked against the WA state requirements",
        ),
    },
    "71000": {  # Darwin
        "council-caravan-park-approval": ("not-found", "Not in the City of Darwin By-laws 2023"),
        "council-temporary-event-approval": (
            "to-check",
            "By-law 22 mentions event permits; the provision requiring them not located",
        ),
    },
    "70200": {  # Alice Springs
        "council-filming-permit": ("not-found", "Not in the Management of Public Places By-laws 2010"),
        "council-caravan-park-approval": ("not-found", "Not in the Management of Public Places By-laws 2010"),
        "council-temporary-event-approval": ("not-found", "Not in the Management of Public Places By-laws 2010"),
    },
}
CELLS["17350"] = dict(CELLS["16950"])  # Temora: as Shoalhaven (NSW councils approve under the state Acts)
for code, why in {
    "40070": "City of Adelaide website and the SA Government Gazette refuse automated requests",
    "40220": "Alexandrina Council website refuses automated requests",
    "44830": "Mount Remarkable website refuses automated requests",
    "62810": "Hobart's by-laws are scanned images with no text layer",
    "64010": "Launceston's by-laws are scanned images with no text layer",
    "60210": "Break O'Day website returned 502 on 27 November 2026",
}.items():
    CELLS.setdefault(code, {})
    for fam in ALL:
        CELLS[code].setdefault(fam, ("blocked", why))
CELLS["74550"] = {f: ("none-published", "Victoria Daly Regional Council publishes no by-laws") for f in ALL}


def requirements() -> dict[tuple[str, str], dict]:
    out = {}
    for f in sorted(LOCAL.glob("*/*.json")):
        d = json.loads(f.read_text("utf-8"))
        out[(d["family"], d["lga"])] = d
    return out


def law_quoted(d: dict) -> bool:
    """True if a source quotes the law itself (a council document, a register or the corpus), not only ABLIS."""
    return any(s["checked"] in ("document", "register-text", "corpus-copy") for s in d["sources"])


def main() -> None:
    sample = [r for r in csv.DictReader(SAMPLE.open(encoding="utf-8")) if r["state"] != "VIC"]
    reqs = requirements()
    rows, problems = [], []
    for fam in ALL:
        for c in sample:
            d = reqs.get((fam, c["lga_code"]))
            if d:
                status, note = "recorded", d["confidence_note"] or ""
            elif fam in CELLS.get(c["lga_code"], {}):
                status, note = CELLS[c["lga_code"]][fam]
            else:
                status, note = "", ""
                problems.append(f"{fam} in {c['lga_name']}: no requirement and no search result recorded")
            if d and CELLS.get(c["lga_code"], {}).get(fam, ("blocked",))[0] != "blocked":
                problems.append(f"{fam} in {c['lga_name']}: recorded, but CELLS also gives a search result")
            rows.append(
                {
                    "family": fam,
                    "family_name": FAMILIES[fam],
                    "state": c["state"],
                    "role": c["role"],
                    "lga_code": c["lga_code"],
                    "lga_name": c["lga_name"],
                    "status": status,
                    "requirement": d["id"] if d else "",
                    "kind": d["kind"] if d else "",
                    "confidence": d["confidence"] if d else "",
                    "law_quoted": ("yes" if law_quoted(d) else "no") if d else "",
                    "what": d["what"] if d else "",
                    "note": note,
                }
            )
    for (fam, _lga), d in reqs.items():
        if fam not in FAMILIES:
            problems.append(f"{d['id']}: family {fam} is not in FAMILIES")
        if not d["administration"]:
            problems.append(f"{d['id']}: no administering body")
        if d["confidence"] == "high" and not law_quoted(d):
            problems.append(f"{d['id']}: high confidence without a quote from the law")
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    by = defaultdict(list)
    for r in rows:
        by[r["family"]].append(r)
    summary = []
    for fam in ALL:
        rs = by[fam]
        st = Counter(r["status"] for r in rs)
        rec = [r for r in rs if r["status"] == "recorded"]
        regimes = {reqs[(fam, r["lga_code"])]["regime"] for r in rec}
        summary.append(
            {
                "family": fam,
                "family_name": FAMILIES[fam],
                "councils": len(rs),
                "recorded": st["recorded"],
                "covered": st["covered"],
                "state_act": st["state-act"],
                "not_found": st["not-found"],
                "to_check": st["to-check"],
                "blocked": st["blocked"] + st["none-published"],
                "law_quoted": sum(r["law_quoted"] == "yes" for r in rec),
                "high_confidence": sum(r["confidence"] == "high" for r in rec),
                "kinds": "; ".join(sorted({r["kind"] for r in rec})),
                "regimes": "; ".join(sorted(x or "none" for x in regimes)),
                "councils_recorded": "; ".join(r["lga_name"] for r in rec),
            }
        )
    with SUMMARY.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    for s in summary:
        print(
            f"{s['family_name']:<26} recorded {s['recorded']:>2}  covered {s['covered']}  state {s['state_act']}  "
            f"not found {s['not_found']}  to check {s['to_check']:>2}  blocked {s['blocked']:>2}  "
            f"kinds {s['kinds']}  regimes {s['regimes']}"
        )
    print(f"{len(reqs)} council requirements; {len(rows)} cells")
    for p in problems:
        print("PROBLEM:", p)
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
