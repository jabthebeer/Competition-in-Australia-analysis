"""Phase 5 post-unblinding check (NOT pre-registered): when did Melbourne's urban transport fares fall?

The registered Victorian taxi re-evaluation found Melbourne's urban transport fares (CPI class 40086) about 10%
lower, relative to the CPI and to the other capitals, in the four quarters 2014-Q3 to 2015-Q2. The annual
event-study bins cannot say which quarter the fall came in. Two changes fall in that window:

- the taxi licensing reform the evaluation is about (as-of-right licences from mid-2014, first quarter 2014-Q3);
- public transport fare changes reported for 1 January 2015 (zone 1+2 travel capped at the zone 1 fare; free
  trams in the CBD), first quarter 2015-Q1. Reported in commentary written before the change (e.g.
  danielbowen.com, 11 August 2014); PTV's own fare tables were not checked.

This script only describes the quarterly gap; it was written after the registered results were seen, so it
cannot change the verdict. The gap is Melbourne's 100 x log(class / All groups) minus the mean of the other seven
capitals, less its mean over the four quarters before 2014-Q3. Quarter-on-quarter changes in the gap from
2005-Q2 to 2014-Q2 give a reference spread for the two candidate quarters.

    uv run python analyses/phase5/posthoc.py --spec phase5-reevaluations

Writes analyses/phase5/reevaluations/posthoc.json.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("power_prices", HERE.parent / "power_study" / "prices.py")
prices = importlib.util.module_from_spec(_spec)
sys.modules["power_prices"] = prices
_spec.loader.exec_module(prices)

from alicia.runner.spec import load  # noqa: E402

CASE = "vic-taxi-licensing-2014-phase5"
OUTCOME = "price-urban-transport-fares"
CANDIDATES = {"taxi licensing (2014-Q3)": "2014-Q3", "reported fare cap and free tram zone (2015-Q1)": "2015-Q1"}
SHOW = ("2012-Q1", "2016-Q4")
REFERENCE = ("2005-Q2", "2014-Q2")


def t_of(q: str) -> int:
    return int(q[:4]) * 4 + int(q[-1]) - 1


def q_of(t: int) -> str:
    return f"{t // 4}-Q{t % 4 + 1}"


def vic_fares(spec_id: str) -> dict:
    case = next(c for c in load(spec_id).cases if c["id"] == CASE)
    o = next(x for x in case["outcomes"] if x["key"] == OUTCOME)
    (cohort,) = o["cohorts"]
    d = prices.relative_prices()
    d = d[d["cls"] == o["code"]].pivot(index="t", columns="state", values="y")
    gap = d[cohort["treated"][0]] - d[cohort["controls"]].mean(axis=1)
    first = t_of(cohort["first_post"])
    gap = gap - gap.loc[first - 4 : first - 1].mean()
    step = gap.diff()
    ref = step.loc[t_of(REFERENCE[0]) : t_of(REFERENCE[1])].dropna()
    sd = float(ref.std(ddof=1))
    window = gap.loc[first : t_of(cohort["last_post"])]
    return {
        "case": CASE,
        "outcome": OUTCOME,
        "cpi_class": o["code"],
        "treated": cohort["treated"],
        "controls": cohort["controls"],
        "registered_window": [cohort["first_post"], cohort["last_post"]],
        "baseline_quarters": [q_of(first - 4), q_of(first - 1)],
        "gap": [
            {"quarter": q_of(int(t)), "gap": round(float(v), 3)}
            for t, v in gap.loc[t_of(SHOW[0]) : t_of(SHOW[1])].items()
        ],
        "window_mean": round(float(window.mean()), 3),
        "reference_steps": {"from": REFERENCE[0], "to": REFERENCE[1], "n": int(len(ref)), "sd": round(sd, 3)},
        "candidate_quarters": {
            name: {
                "quarter": q,
                "step": round(float(step.loc[t_of(q)]), 3),
                "step_in_sd": round(float(step.loc[t_of(q)]) / sd, 2),
                "share_of_reference_steps_as_large": round(float(np.mean(np.abs(ref) >= abs(step.loc[t_of(q)]))), 3),
            }
            for name, q in CANDIDATES.items()
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True, choices=["phase5-reevaluations"])
    args = ap.parse_args()
    out = {
        "spec": args.spec,
        "preregistered": False,
        "note": "Written after the registered results were seen; descriptive only; does not change any verdict.",
        "vic_fares": vic_fares(args.spec),
    }
    path = HERE / "reevaluations" / "posthoc.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", "utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
