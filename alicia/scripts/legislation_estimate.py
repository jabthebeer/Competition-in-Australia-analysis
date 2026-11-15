"""Time and cost estimate for phases C to G of the legislation links (phase B wrap-up, 6 Nov 2026).

Reads only files in the repository:
  docs/calibration_session_usage.csv          time and tokens per calibration batch (from the session transcript)
  data/processed/legislation/oalc_laws.csv.gz the corpus index (laws in force as at March 2025)
  data/processed/legislation/screening_sample.csv  100 laws screened by hand (50 Commonwealth, 50 state)
  data/processed/legislation/ablis_sample.csv      60 random ABLIS service pages
  data/processed/legislation/reach_test.csv        full reach for four families
  regulation-register/requirements/                 the calibration requirements

Writes docs/estimate_legislation_links.csv and docs/estimate_legislation_links_cost.csv, and prints both.
Every input is marked `measured` or `assumed`; assumed values are judgement and are the first thing to revise.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEG = ROOT / "data" / "processed" / "legislation"

# The same title triage the screening samples were drawn after.
DROP_CTH = (
    r"Amendment|Amending|Appropriation|Repeal|Consequential|Transitional|Savings|^AD/|Airworthiness|"
    r"Tariff Concession|Customs Tariff|Notice of Disqualification|Appointment|Instrument CASA|EX\d+"
)
DROP_STATE = (
    r"Amendment|Amending|Appropriation|Repeal|Commencement|Proclamation|Notice|Order No|Gazette|Consequential|"
    r"Transitional|Savings|^AD/|Airworthiness|Tariff Concession|Customs Tariff|Notice of Disqualification|"
    r"Appointment|Instrument CASA|EX\d+"
)
CORPUS_STATES = ("new_south_wales", "queensland", "western_australia", "south_australia", "tasmania")

# ABLIS public sitemap, read 6 Nov 2026 (docs/ablis_brief.md): service pages in all, and at Australian Government level.
ABLIS_PAGES, ABLIS_CTH = 30_663, 775

# Prices per million tokens for the current model in each family (read 6 Nov 2026) from
# https://platform.claude.com/docs/en/about-claude/pricing.
# input, 5-minute cache write, cache read, output; the Batch API halves all four.
PRICES = {
    "Opus": (4.00, 5.00, 0.20, 20.00),
    "Sonnet": (2.00, 2.50, 0.10, 10.00),
    "Haiku": (0.10, 0.125, 0.01, 0.50),  # prompts up to 100,000 tokens
}


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Share and its 95% Wilson interval."""
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), p, min(1.0, c + h)


def triaged_counts() -> dict[tuple[str, str], int]:
    out: Counter = Counter()
    with gzip.open(LEG / "oalc_laws.csv.gz", "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            j = r["jurisdiction"]
            if j == "commonwealth" and not re.search(DROP_CTH, r["citation"]):
                out[("commonwealth", r["type"])] += 1
            elif j in CORPUS_STATES and not re.search(DROP_STATE, r["citation"]):
                out[("states", r["type"])] += 1
    return dict(out)


def screening_rates() -> dict[tuple[str, str], dict]:
    rows = read_csv(LEG / "screening_sample.csv")
    out = {}
    for key in {(r["sample"], r["type"]) for r in rows}:
        g = [r for r in rows if (r["sample"], r["type"]) == key]
        y = [r for r in g if r["call"] == "Y"]
        out[key] = {
            "n": len(g),
            "Y": wilson(len(y), len(g)),
            "per_Y": sum(int(r["requirements"]) for r in y) / max(len(y), 1),
            "L": len([r for r in g if r["call"] == "L"]) / len(g),
            "P": len([r for r in g if r["call"] == "P"]) / len(g),
        }
    return out


def calibration() -> dict:
    rows = read_csv(ROOT / "docs" / "calibration_session_usage.csv")
    per = {r["batch"]: float(r["active_minutes"]) / int(r["requirements"]) for r in rows}
    steady = [r for r in rows if r["batch"] in ("3", "4", "5", "4f")]
    n = sum(int(r["requirements"]) for r in steady)
    return {
        "low": min(per[b] for b in ("3", "4", "5", "4f")),
        "central": sum(float(r["active_minutes"]) for r in steady) / n,
        "high": per["2"],  # first-of-kind state work, including building readers
        "out_tokens": sum(int(r["output_tokens"]) for r in steady) / n,
        "cache_read": sum(int(r["cache_read_tokens"]) for r in steady) / n,
        "local": per["5"],
    }


def state_families() -> float:
    reqs = [
        json.loads(p.read_text("utf-8"))
        for p in (ROOT / "regulation-register" / "requirements").glob("*/*.json")
        if p.parent.name not in ("cth", "local")
    ]
    return len(reqs) / len({r["family"] for r in reqs})


def councils() -> int:
    import sys

    sys.path.insert(0, str(ROOT / "alicia" / "src"))
    from alicia.register.requirements import lga_names

    skip = re.compile(r"Unincorp|No usual address|Migratory|Outside Australia", re.I)
    codes = [(c, n) for c, n in lga_names().items() if isinstance(c, str) and isinstance(n, str)]
    return len(
        [c for c, n in codes if c[0] not in "89" and not skip.search(n)]
    )  # no councils in the ACT or other territories


def main() -> None:
    counts, rates, cal = triaged_counts(), screening_rates(), calibration()
    ablis = read_csv(LEG / "ablis_sample.csv")
    council_share = wilson(sum(int(r["council_administered"]) for r in ablis), len(ablis))
    local_law_share = wilson(
        sum(int(r["council_administered"]) and int(r["local_law_named"]) for r in ablis), len(ablis)
    )
    reach = Counter(r["family"] for r in read_csv(LEG / "reach_test.csv"))
    n_councils, fam_states = councils(), state_families()
    scale_states = 8 / 5  # assumed: Victoria, the ACT and the NT have the five corpus states' mean number of laws

    def reqs(sample: str, scale: float = 1.0) -> tuple[float, float, float]:
        tot = [0.0, 0.0, 0.0]
        for t in ("primary_legislation", "secondary_legislation"):
            r, n = rates[(sample, t)], counts[(sample, t)] * scale
            for i in range(3):
                tot[i] += n * r["Y"][i] * r["per_Y"]
        return tuple(tot)

    def attach(sample: str, scale: float = 1.0) -> float:
        return sum(
            counts[(sample, t)] * scale * rates[(sample, t)]["L"]
            for t in ("primary_legislation", "secondary_legislation")
        )

    laws_c = sum(v for (s, _), v in counts.items() if s == "commonwealth")
    laws_d = sum(v for (s, _), v in counts.items() if s == "states") * scale_states
    req_c, req_d = reqs("commonwealth"), reqs("states", scale_states)
    sample_councils = 21  # D4: three councils in each state and the NT (the ACT has none)
    local_per_council = [ABLIS_PAGES * s / n_councils for s in local_law_share]
    req_e = tuple(sample_councils * x for x in local_per_council)
    per_req = (cal["low"], cal["central"], cal["high"])
    per_local = (0.4, cal["local"], cal["high"])

    # component, phase, quantity (low, central, high), minutes per unit (low, central, high), unit, basis
    rows = [
        ("C", "Build the Commonwealth catalogue", (1, 1, 1), (30, 60, 120), "jurisdiction", "assumed"),
        (
            "C",
            "Screen laws (title triage, then a quick read)",
            (laws_c,) * 3,
            (1 / 60, 1 / 60, 5 / 60),
            "law",
            "measured 1.1 s a law; high assumed",
        ),
        (
            "C",
            "Draft requirements (law text, quotes, reach)",
            req_c,
            per_req,
            "requirement",
            "measured rate; count from the sample (95% interval)",
        ),
        (
            "C",
            "Attach supporting instruments to requirements",
            (attach("commonwealth"),) * 3,
            (0.1, 0.2, 0.5),
            "law",
            "count measured; time assumed",
        ),
        (
            "C",
            "Code full reach across 506 classes",
            req_c,
            (0.25, 0.25, 0.5),
            "family",
            "measured 15 s a family; high assumed",
        ),
        ("D", "Build the eight state catalogues", (8, 8, 8), (30, 60, 120), "jurisdiction", "assumed"),
        ("D", "Screen laws", (laws_d,) * 3, (1 / 60, 1 / 60, 5 / 60), "law", "measured 1.0 s a law; high assumed"),
        (
            "D",
            "Draft requirements",
            req_d,
            per_req,
            "requirement",
            "measured rate; count from the sample (95% interval) x 8/5 states",
        ),
        (
            "D",
            "Attach supporting instruments",
            (attach("states", scale_states),) * 3,
            (0.1, 0.2, 0.5),
            "law",
            "count measured; time assumed",
        ),
        (
            "D",
            "Code full reach (once per family)",
            tuple(x / fam_states for x in req_d),
            (0.25, 0.25, 0.5),
            "family",
            f"measured; {fam_states:.1f} states a family in calibration",
        ),
        (
            "E",
            "Classify classes in planning land-use terms",
            (506 * 8,) * 3,
            (0.05, 0.15, 0.3),
            "class x state",
            "assumed",
        ),
        (
            "E",
            f"Local-law requirements, {sample_councils} sample councils (D4)",
            req_e,
            per_local,
            "requirement",
            "count from the ABLIS sample (95% interval); rate measured in batch 5",
        ),
        (
            "F",
            "Compare with ABLIS; review mismatches (waits for the key)",
            (405, 405, 405),
            (1, 2, 3),
            "class x state",
            "assumed: 10% of 4,048 cells reviewed",
        ),
        ("G", "Re-verify a random sample of links", (400, 400, 400), (0.5, 1, 1.5), "link", "assumed"),
    ]
    out = []
    for phase, what, q, m, unit, basis in rows:
        h = tuple(q[i] * m[i] / 60 for i in range(3))
        out.append(
            [phase, what, unit, *(round(x) for x in q), *(round(x, 2) for x in m), *(round(x, 1) for x in h), basis]
        )
    head = [
        "phase",
        "component",
        "unit",
        "qty_low",
        "qty_central",
        "qty_high",
        "min_low",
        "min_central",
        "min_high",
        "hours_low",
        "hours_central",
        "hours_high",
        "basis",
    ]
    tot = [round(sum(r[9 + i] for r in out), 1) for i in range(3)]
    with open(ROOT / "docs" / "estimate_legislation_links.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(out)
        w.writerow(["all", "Total, phases C to G (sample councils)", "", "", "", "", "", "", "", *tot, ""])

    # Councils beyond the sample are not in the total: they need the ABLIS key (the public site is not for bulk use).
    all_councils = tuple(ABLIS_PAGES * s for s in local_law_share)
    n_req = [req_c[i] + req_d[i] + req_e[i] for i in range(3)]

    # API cost: two ways of drafting one requirement, plus screening every law with one call each.
    # Lean: code finds the provisions; one call of 30k input, 4k output (Batch API). Agentic: 8 calls, 60k written to
    # the cache, 420k read from it, 6k output (standard API). Screening: 6k input, 0.3k output a law (Batch API).
    # All assumed.
    cost = []
    for model, (pi, pw, pr, po) in PRICES.items():
        lean = (30_000 * pi + 4_000 * po) / 1e6 / 2
        agent = (60_000 * pw + 420_000 * pr + 6_000 * po) / 1e6
        screen = (6_000 * pi + 300 * po) / 1e6 / 2
        laws = laws_c + laws_d
        for i, label in enumerate(("low", "central", "high")):
            cost.append(
                [
                    model,
                    label,
                    round(n_req[i]),
                    round(laws),
                    round(lean * n_req[i]),
                    round(agent * n_req[i]),
                    round(screen * laws),
                ]
            )
    with open(ROOT / "docs" / "estimate_legislation_links_cost.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "model",
                "case",
                "requirements",
                "laws_screened",
                "usd_drafting_lean_batch",
                "usd_drafting_agentic",
                "usd_screening_batch",
            ]
        )
        w.writerows(cost)

    print(f"Laws after triage: Commonwealth {laws_c:,}; states {laws_d:,.0f} (8/5 x the five corpus states)")
    for k, r in sorted(rates.items()):
        print(
            f"  {k}: n={r['n']} Y={r['Y'][1]:.0%} ({r['Y'][0]:.0%}-{r['Y'][2]:.0%}) "
            f"per Y={r['per_Y']:.2f} L={r['L']:.0%} P={r['P']:.0%}"
        )
    print(
        f"ABLIS: council-administered {council_share[1]:.0%} ({council_share[0]:.0%}-{council_share[2]:.0%}); "
        f"council with a local law {local_law_share[1]:.0%} ({local_law_share[0]:.0%}-{local_law_share[2]:.0%}); "
        f"{n_councils} councils; local-law requirements a council {local_per_council[1]:.0f}; "
        f"all councils {all_councils[1]:,.0f} "
        f"({all_councils[0]:,.0f}-{all_councils[2]:,.0f})"
    )
    print(
        f"Reach test (classes): {dict(reach)}; "
        f"calibration: {cal['low']:.2f}/{cal['central']:.2f}/{cal['high']:.2f} min a requirement, "
        f"{cal['out_tokens']:,.0f} output and {cal['cache_read']:,.0f} cache-read tokens a requirement"
    )
    print(
        f"Requirements: C {req_c[1]:,.0f} ({req_c[0]:,.0f}-{req_c[2]:,.0f}); "
        f"D {req_d[1]:,.0f} ({req_d[0]:,.0f}-{req_d[2]:,.0f}); "
        f"E sample {req_e[1]:,.0f} ({req_e[0]:,.0f}-{req_e[2]:,.0f}); "
        f"total {n_req[1]:,.0f} ({n_req[0]:,.0f}-{n_req[2]:,.0f})"
    )
    for r in out:
        print(f"  {r[0]} {r[1][:52]:52} {r[4]:>8,} {r[2]:13} {r[7]:>5} min  {r[10]:>6} h ({r[9]}-{r[11]})")
    print(f"Total hours (low, central, high): {tot}")
    for r in cost:
        print("  ", r)


if __name__ == "__main__":
    main()
