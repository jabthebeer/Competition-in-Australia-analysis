"""Forward plan Phase 3, price outcomes: how much each layer shrinks the no-effect spread when the outcome is a
consumer price rather than business entry or exit.

Outcome: CPI expenditure class relative to the city's All groups CPI, 100 x log(class / All groups), by capital
city (one city per state) and quarter, 2001-Q1 to 2025-Q3 (ABS CPI, 17th series). Unit of analysis: a cell
(CPI class x city). Every eligible class is in the panel, so class x quarter and city x quarter effects can be
absorbed (the price analogue of the saturated business-count model).

Blinding: before anything is computed, the reform's CPI class in its treated cities is deleted from the first
exposed quarter on, and treated cities after their window (``run.hide``; checked by ``run.assert_blind``). No
estimate of any reform's effect is made here.

Placebo families (each layer runs on the same assignments):
- ``industries`` (here: CPI classes): up to 40 classes outside the reform's related subgroups, assigned the
  reform's treated cities and quarters (the registered batch used every eligible class);
- ``states``: the reform's own class in cities that never adopted it;
- ``dates``: the reform's own class and cities at earlier dates, moved back whole years (at least eight earlier
  quarters kept);
- ``states_dates``: both at once.

Layers and the MDE are as in ``run.py``; units are log points x 100 (about percent) of the relative price.

    uv run python analyses/power_study/prices.py
    uv run python analyses/power_study/prices.py --only fuel-price-reporting --max-placebos 5
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
# Load this folder's run.py under its own name: it imports the batch's run.py as "run".
_spec = importlib.util.spec_from_file_location("power_run", HERE / "run.py")
power = importlib.util.module_from_spec(_spec)
sys.modules["power_run"] = power
_spec.loader.exec_module(power)

from alicia.evaluate import covariates  # noqa: E402
from alicia.evaluate.stacked import Cohort  # noqa: E402
from alicia.outcomes.abs_series import CITY_STATE, fetch_cpi  # noqa: E402

batch_cases = power.batch_cases
CPI_CLASSES = power.batch.CPI_CLASSES
q = batch_cases.q
MIN_PRE_Q = 8
LAST_Q = q(2025, 3)
STEP = 4  # fake dates move back whole years, so seasonal patterns line up


@dataclass(frozen=True)
class PriceReform:
    id: str
    title: str
    records: tuple[str, ...]
    codes: tuple[str, ...]  # CPI classes analysed, one at a time
    cohorts: tuple[Cohort, ...]
    exclude_subgroups: tuple[str, ...]
    start: int = q(2005, 1)
    registered: str | None = None  # batch case whose design-stage price spread is reported alongside
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class _Case:
    """What the shared blinding and estimation helpers need: one class, its cohorts and its start."""

    id: str
    classes: tuple[str, ...]
    cohorts: tuple[Cohort, ...]
    start: int


def _from_batch(case: batch_cases.Case, start: int = q(2005, 1)) -> PriceReform:
    spec = case.price
    return PriceReform(
        id=f"{case.id}-prices",
        title=case.title,
        records=case.records,
        codes=spec.codes,
        cohorts=spec.cohorts,
        exclude_subgroups=spec.exclude_subgroups,
        start=start,
        registered=case.id,
    )


ALL_BUT = batch_cases.ALL_BUT
C = Cohort
NEW = "New family (gap scan, 18 October 2026)."
REFORMS: tuple[PriceReform, ...] = (
    *(_from_batch(c) for c in batch_cases.CASES if c.price is not None),
    PriceReform(
        id="fuel-price-reporting",
        title="Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021)",
        records=(
            "nsw-fuel-price-reporting-2016",
            "nt-fuel-price-reporting-2017",
            "qld-fuel-price-reporting-2018",
            "tas-fuel-price-reporting-2020",
            "sa-fuel-price-reporting-2021",
        ),
        codes=("40081",),
        cohorts=(
            C(("NSW",), q(2016, 3), q(2020, 2), ("VIC", "ACT", "TAS", "SA")),
            C(("NT",), q(2017, 4), q(2020, 2), ("VIC", "ACT", "TAS", "SA")),
            C(("QLD",), q(2018, 4), q(2020, 2), ("VIC", "ACT", "TAS", "SA")),
            C(("TAS",), q(2020, 3), q(2025, 2), ("VIC", "ACT")),
            C(("SA",), q(2021, 1), q(2025, 2), ("VIC", "ACT")),
        ),
        exclude_subgroups=("Private motoring",),
        notes=(NEW, "WA (reporting since 2001) is left out; Victoria reports from August 2025, after the window."),
    ),
    PriceReform(
        id="necf",
        title="National Energy Customer Framework adoption (ACT, TAS 2012; SA 2013; NSW 2013; QLD 2015)",
        records=("act-necf-2012", "tas-necf-2012", "sa-necf-2013", "nsw-necf-2013", "qld-necf-2015"),
        codes=("40055",),
        cohorts=(
            C(("ACT", "TAS"), q(2012, 3), q(2017, 2), ("VIC", "WA", "NT")),
            C(("SA",), q(2013, 1), q(2017, 2), ("VIC", "WA", "NT")),
            C(("NSW",), q(2013, 3), q(2017, 2), ("VIC", "WA", "NT")),
            C(("QLD",), q(2015, 3), q(2017, 2), ("VIC", "WA", "NT")),
        ),
        exclude_subgroups=("Utilities",),
        notes=(NEW, "SA adopted on the day it deregulated retail prices; NSW and QLD deregulated about a year after."),
    ),
    PriceReform(
        id="ctp",
        title="CTP insurance reforms (NSW 2017; SA price competition 2019; ACT 2020)",
        records=("nsw-ctp-scheme-2017", "sa-ctp-price-competition-2019", "act-ctp-scheme-2020"),
        codes=("115529",),
        cohorts=(
            C(("NSW",), q(2017, 4), q(2019, 2), ("VIC", "TAS", "QLD", "WA", "NT")),
            C(("SA",), q(2019, 3), q(2022, 2), ("VIC", "TAS", "QLD", "WA", "NT")),
            C(("ACT",), q(2020, 1), q(2022, 2), ("VIC", "TAS", "QLD", "WA", "NT")),
        ),
        exclude_subgroups=("Insurance", "Financial services"),
        notes=(NEW, "Whether CTP premiums sit in the CPI Insurance class (not motoring charges) is to be checked."),
    ),
    PriceReform(
        id="pharmacist-uti",
        title="Pharmacists treat uncomplicated UTIs (QLD 2020, NSW 2023, five more 2023-24)",
        records=(
            "qld-pharmacist-uti-2020",
            "nsw-pharmacist-uti-2023",
            "act-pharmacist-uti-2023",
            "wa-pharmacist-uti-2023",
            "vic-pharmacist-uti-2023",
            "sa-pharmacist-uti-2024",
            "tas-pharmacist-uti-2024",
        ),
        codes=("40091", "40094"),
        cohorts=(
            C(("QLD",), q(2020, 2), q(2023, 1), ("NSW", "VIC", "SA", "WA", "TAS", "ACT", "NT")),
            C(("NSW",), q(2023, 2), q(2023, 2), ("VIC", "SA", "WA", "TAS", "ACT", "NT")),
            C(("WA", "ACT"), q(2023, 3), q(2023, 3), ("VIC", "SA", "TAS", "NT")),
            C(("VIC",), q(2023, 4), q(2023, 4), ("SA", "TAS", "NT")),
            C(("SA", "TAS"), q(2024, 1), q(2024, 3), ("NT",)),
        ),
        exclude_subgroups=("Medical products, appliances and equipment", "Medical, dental and hospital services"),
        notes=(NEW, "GP fees (Medical and hospital services) and pharmaceuticals; pharmacist fees are in neither."),
    ),
    PriceReform(
        id="ncc-2022",
        title="2022 building code adoption (staggered 2023-2025)",
        records=(
            "nsw-ncc-2022-2023",
            "nt-ncc-2022-2023",
            "act-ncc-2022-2024",
            "vic-ncc-2022-2024",
            "qld-ncc-2022-2024",
            "sa-ncc-2022-2024",
            "tas-ncc-2022-2024",
        ),
        codes=("97559",),
        cohorts=(
            C(("NSW", "NT"), q(2023, 4), q(2024, 1), ("VIC", "QLD", "SA", "TAS", "WA")),
            C(("ACT",), q(2024, 1), q(2024, 1), ("VIC", "QLD", "SA", "TAS", "WA")),
            C(("VIC", "QLD"), q(2024, 2), q(2024, 3), ("SA", "TAS", "WA")),
            C(("SA", "TAS"), q(2024, 4), q(2025, 1), ("WA",)),
        ),
        exclude_subgroups=("New dwelling purchase by owner-occupiers", "Other housing"),
        start=q(2010, 1),
        notes=(NEW, "Adoption differs: some states took only the energy or only the livable housing provisions."),
    ),
    PriceReform(
        id="east-coast-gas",
        title="East-coast gas price cap (December 2022) and Gas Market Code (July 2023)",
        records=("cth-gas-market-code-2023",),
        codes=("115524",),
        cohorts=(C(("NSW", "VIC", "QLD", "SA", "TAS", "ACT"), q(2022, 4), q(2025, 2), ("WA", "NT")),),
        exclude_subgroups=("Utilities",),
        start=q(2010, 1),
        notes=(NEW, "WA and the NT are outside the east-coast gas market."),
    ),
)


# ---- data ------------------------------------------------------------------------------------------------------


@cache
def relative_prices() -> pd.DataFrame:
    """cls, state, t (year x 4 + quarter - 1), y = 100 x log(class / All groups) for every CPI class and city."""
    raw = fetch_cpi(["10001", *[c["code"] for c in CPI_CLASSES]], start="2001-Q1", end="2025-Q3")
    raw = raw.assign(
        state=raw["city"].map(CITY_STATE),
        t=raw["period"].str[:4].astype(int) * 4 + raw["period"].str[-1].astype(int) - 1,
    )
    allg = raw[raw["index_code"] == "10001"].set_index(["state", "t"])["value"]
    cl = raw[raw["index_code"] != "10001"]
    base = allg.reindex(pd.MultiIndex.from_frame(cl[["state", "t"]])).to_numpy(float)
    out = pd.DataFrame(
        {
            "cls": cl["index_code"].to_numpy(),
            "state": cl["state"].to_numpy(),
            "t": cl["t"].to_numpy(int),
            "y": 100 * np.log(cl["value"].to_numpy(float) / base),
        }
    )
    return out.dropna().reset_index(drop=True)


@cache
def quarter_covariates() -> pd.DataFrame:
    c = covariates.state_covariates(base_fy=2005)
    t = c["period"].dt.year * 4 + (c["period"].dt.month - 1) // 3
    return c.assign(t=t)[["state", "t", *power.COVARIATES]]


def eligible(r: PriceReform) -> list[str]:
    return [c["code"] for c in CPI_CLASSES if c["subgroup"] not in r.exclude_subgroups and c["code"] not in r.codes]


def price_panel(r: PriceReform, case: _Case) -> pd.DataFrame:
    """Every eligible class plus the reform's class, the reform's cities, from start to the last window quarter.
    Columns follow the business-count panel so the same estimators run: ``fy`` holds the quarter index."""
    last = max(c.last_post for c in case.cohorts)
    keep = {*eligible(r), *case.classes}
    d = relative_prices()
    d = d[d["cls"].isin(keep) & d["state"].isin(power.states_of(case.cohorts)) & d["t"].between(case.start, last)]
    d = d.merge(quarter_covariates(), on=["state", "t"], how="left")
    d = d.rename(columns={"t": "fy"}).assign(w=1.0, base=float(power.MIN_CELL))
    d["cell"] = d["cls"] + ":" + d["state"]
    return power.hide(d.reset_index(drop=True), case).reset_index(drop=True)


def placebo_classes(r: PriceReform, max_placebos: int) -> list[str]:
    codes = eligible(r)
    if len(codes) > max_placebos:
        codes = sorted(np.random.default_rng(power.SEED).choice(codes, size=max_placebos, replace=False))
    return list(codes)


def registered_spread(case_id: str | None, code: str) -> dict | None:
    if case_id is None:
        return None
    design = json.loads((power.BATCH / "design.json").read_text("utf-8"))
    row = next((c for c in design["cases"] if c["id"] == case_id), None)
    cl = ((row or {}).get("prices") or {}).get("classes", {}).get(code)
    return {"sd": cl["placebo_sd"], "mde": cl["mde_80"], "n": cl["placebos"]} if cl and cl.get("placebo_sd") else None


# ---- study -----------------------------------------------------------------------------------------------------


def run_reform(r: PriceReform, max_placebos: int, own: bool = True) -> dict:
    names = {c["code"]: c["name"] for c in CPI_CLASSES}
    out = {
        "id": r.id,
        "title": r.title,
        "records": list(r.records),
        "cohorts": power.describe(r.cohorts),
        "start": r.start,
        "registered_case": r.registered,
        "notes": list(r.notes),
        "outcomes": {},
    }
    placebos = placebo_classes(r, max_placebos)
    for code in r.codes:
        case = _Case(r.id, (code,), r.cohorts, r.start)
        df = price_panel(r, case)
        power.assert_blind(df, case)
        t0 = time.time()
        rows = [power.estimate_all(df, case.cohorts, case.start, [g]) for g in placebos]
        fams = {}
        if own:
            draws = power.own_class_draws(case, step=STEP, min_pre=MIN_PRE_Q, first_year={})
            for name, ds in draws.items():
                est = []
                for cohorts in ds:
                    last = max(c.last_post for c in cohorts)
                    est.append(power.estimate_all(df[df["fy"] <= last], cohorts, case.start, [code]))
                fams[name] = {
                    "draws": len(ds),
                    "layers": power.layer_table(est),
                    "placebo_estimates": [
                        {k: round(v, 4) for k, v in row.items()} | {"cohorts": power.describe(c)}
                        for row, c in zip(est, ds, strict=True)
                    ],
                }
        res = power.layer_table(rows)
        sd = df[df["cls"] == code].groupby("cell")["y"].diff().std()
        out["outcomes"][code] = {
            "name": names[code],
            "cells": int(df["cell"].nunique()),
            "rows": int(len(df)),
            "quarterly_change_sd": round(float(sd), 3),
            "registered_design": registered_spread(r.registered, code),
            "layers": res,
            "placebo_estimates": [
                {k: round(v, 4) for k, v in row.items()} | {"classes": [g]}
                for row, g in zip(rows, placebos, strict=True)
            ],
            "families": fams,
        }
        print(
            f"  {names[code]}: {len(placebos)} placebo classes, "
            + ", ".join(f"{k} {v['draws']}" for k, v in fams.items())
            + f" own-class draws in {time.time() - t0:.0f}s; "
            + ", ".join(f"{k} {res[k]['mde']}" for k in power.LAYERS),
            flush=True,
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="one reform id")
    ap.add_argument("--max-placebos", type=int, default=power.MAX_PLACEBOS)
    ap.add_argument("--industries-only", action="store_true", help="skip the own-class placebo families")
    args = ap.parse_args()
    results = []
    for r in REFORMS:
        if args.only and r.id != args.only:
            continue
        print(r.id, flush=True)
        results.append(run_reform(r, args.max_placebos, own=not args.industries_only))
    report = {
        "plan": "docs/forward_plan_macro_controls.md (Phase 3)",
        "mode": "BLIND: treated class hidden in treated cities from first exposure; no reform effect estimated",
        "outcome": "100 x log(CPI class / All groups CPI), capital city, quarterly",
        "mde": "2.8 x standard deviation of placebo estimates (80% power, 5% two-sided)",
        "layers": list(power.LAYERS),
        "families": list(power.FAMILIES),
        "reforms": results,
    }
    name = "power_prices.json" if not args.only else f"check_prices_{args.only}.json"
    (HERE / name).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {HERE / name}")


if __name__ == "__main__":
    main()
