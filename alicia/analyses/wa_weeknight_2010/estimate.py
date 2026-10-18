"""Registered estimation for the Perth weeknight trading re-evaluation (docs/pap_wa_weeknight_2010.md).

--blind: dry run with WA's post-reform outcomes hidden; it must reproduce the design stage's
no-effect distributions (design.json) and estimate nothing for WA. Without --blind: the one
registered run, written to estimate.json.

Run: uv run python analyses/wa_weeknight_2010/estimate.py [--blind]
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import spec
from spec import TREATED, A, B, C, Design

from alicia.evaluate.did import blind

HERE = Path(__file__).resolve().parent


def num(x: float | None, nd: int = 3) -> float | None:
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), nd)


def summarise(est: float, null: pd.Series) -> dict:
    ok = not math.isnan(est)
    lo90, hi90 = spec.interval(null, est, 0.9) if ok else (None, None)
    lo95, hi95 = spec.interval(null, est, 0.95) if ok else (None, None)
    return {
        "estimate": num(est),
        "p": num(spec.p_value(null, est), 4) if ok else None,
        "interval_90": [num(lo90), num(hi90)],
        "interval_95": [num(lo95), num(hi95)],
        "null": spec.summarise_null(null),
    }


def finding(res: dict) -> str:
    if res["p"] is None:
        return "not-identified"
    if res["p"] < 0.10:
        return "increase" if res["estimate"] > 0 else "decrease"
    return "no-detectable-effect"


def dated(df: pd.DataFrame, design: Design, units: list[str], hide: bool, trend: bool = False) -> dict:
    """A or B: the estimate against fake-date and comparison-state placebos."""
    times = sorted(df["time"].unique())
    data = blind(df, TREATED, design.hidden_from(times)) if hide else df
    null = spec.null_dates(data, design, units, trend=trend)["estimate"]
    est = spec.estimate(data, design, units, trend=trend)
    return summarise(est, null)


def event_points(df: pd.DataFrame, design: Design, units: list[str], hide: bool, band: pd.DataFrame) -> list[dict]:
    times = sorted(df["time"].unique())
    data = blind(df, TREATED, design.hidden_from(times)) if hide else df
    coef = spec.event_coefficients(data, design, units)
    win, post = design.window(times)
    pre = [t for t in win if t < design.event]
    first = {}
    for t in pre:
        first.setdefault(-1 - ((len(pre) - 1 - pre.index(t)) // design.block), t)
    for t in post:
        first.setdefault(post.index(t) // design.block, t)
    ks = sorted({*coef.index, -1})
    out = []
    for k in ks:
        start = first[k]
        label = start.strftime("%b %Y") if design.block == 1 or k == -1 else start.strftime("%b %Y") + " +"
        out.append(
            {
                "k": int(k),
                "period": label,
                "estimate": 0.0 if k == -1 else num(coef.get(k)),
                "low": num(band.loc[k, "low"]) if k in band.index else None,
                "high": num(band.loc[k, "high"]) if k in band.index else None,
            }
        )
    return out


def places(hide: bool, floor: int = spec.C_FLOOR, **kw) -> dict:
    logs = spec.cabee_areas(**kw)
    null = spec.null_industries(logs, floor=floor)["estimate"]
    df = spec.panel_c(spec.C_RETAIL, logs)
    if hide:
        df = blind(df, TREATED, C.event)
    est = spec.estimate(df, C, sorted(df["unit"].unique()))
    out = summarise(est, null)
    counts = np.exp(logs / 100)
    out["wa_retail_businesses"] = {
        part: {
            str(t.date()): int(round(v)) for t, v in counts.loc[(TREATED, part, "G")].items() if not hide or t < C.event
        }
        for part in ("cap", "rest")
    }
    return out


def places_event(hide: bool) -> list[dict]:
    logs = spec.cabee_areas()
    df = spec.panel_c(spec.C_RETAIL, logs)
    if hide:
        df = blind(df, TREATED, C.event)
    units = sorted(df["unit"].unique())
    coef = spec.event_coefficients(df, C, units)
    band = spec.event_band_industries(logs)
    out = []
    for k, t in zip([-2, -1, 0, 1], ["Jun 2009", "Jun 2010", "Jun 2011", "Jun 2012"], strict=True):
        out.append(
            {
                "k": k,
                "period": t,
                "estimate": 0.0 if k == -1 else num(coef.get(k)),
                "low": num(band.loc[k, "low"]) if k in band.index else None,
                "high": num(band.loc[k, "high"]) if k in band.index else None,
            }
        )
    return out


def bh(ps: dict[str, float]) -> dict[str, float]:
    """Benjamini-Hochberg q-values."""
    items = sorted(ps.items(), key=lambda kv: kv[1])
    m = len(items)
    q, out = 1.0, {}
    for i in range(m - 1, -1, -1):
        k, p = items[i]
        q = min(q, p * m / (i + 1))
        out[k] = round(q, 4)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blind", action="store_true", help="dry run with WA's post-reform outcomes hidden")
    args = ap.parse_args()
    hide = args.blind

    a = spec.panel_a()
    ua = spec.units_a(a)
    ub = [TREATED, *spec.LARGE_STATES]
    a_band = spec.event_band(blind(a, TREATED, A.hidden_from(sorted(a["time"].unique()))), A, ua)
    b = spec.panel_b()
    b_band = spec.event_band(blind(b, TREATED, B.hidden_from(sorted(b["time"].unique()))), B, ub)

    out: dict = {"blind": hide, "units": {"A": ua, "B": ub, "C": spec.GEO_UNITS}}
    out["A"] = dated(a, A, ua, hide)
    out["A"]["event_study"] = event_points(a, A, ua, hide, a_band)
    out["A_secondary"] = {
        "detrended": dated(a, A, ua, hide, trend=True),
        "all_fake_dates": summarise(
            out["A"]["estimate"] if out["A"]["estimate"] is not None else float("nan"),
            spec.null_dates(
                blind(a, TREATED, A.hidden_from(sorted(a["time"].unique()))) if hide else a,
                A,
                ua,
                since=pd.Timestamp("1900-01-01"),
            )["estimate"],
        ),
        "minus_rest_of_retail_and_food": dated(spec.panel_a(den=spec.A_OTHER + spec.A_FOOD), A, ua, hide),
        "triple_diff_food": dated(spec.panel_a(den=spec.A_FOOD), A, ua, hide),
        "supermarket_share": dated(spec.panel_a([spec.A_SHARE[0]], [spec.A_SHARE[1]]), A, ua, hide),
        **{f"only_{c}": dated(spec.panel_a([c]), A, ua, hide) for c in spec.A_TREATED},
    }
    out["B_descriptive"] = {
        "hours": dated(b, B, ub, hide),
        "employment": dated(spec.panel_b("employed"), B, ub, hide),
        "hours_minus_food": dated(spec.panel_b(den=spec.B_FOOD), B, ub, hide),
        "hours_detrended": dated(b, B, ub, hide, trend=True),
    }
    out["B_descriptive"]["hours"]["event_study"] = event_points(b, B, ub, hide, b_band)
    out["C"] = places(hide)
    out["C"]["event_study"] = places_event(hide)
    out["C_secondary"] = {
        "small_businesses": places(hide, bands=spec.SMALL),
        "with_mandurah": places(hide, include_mandurah=True),
        "without_outback": places(hide, drop_outback=True),
        "no_size_floor": places(hide, floor=0),
    }
    for key in ("A", "C"):
        out[key]["finding"] = finding(out[key])
    ps = {k: out[k]["p"] for k in ("A", "C") if out[k]["p"] is not None}
    out["q_values"] = bh(ps) if ps else {}

    design = json.loads((HERE / "design.json").read_text("utf-8"))
    checks = {
        "A": (out["A"]["null"], design["A_turnover"]["null"]),
        "B": (out["B_descriptive"]["hours"]["null"], design["B_hours"]["null"]),
        "C": (out["C"]["null"], design["C_places"]["null"]),
    }
    for k, (got, want) in checks.items():
        assert got["n"] == want["n"] and abs(got["sd"] - want["sd"]) < 1e-6, f"{k}: null differs from the design stage"
    out["null_matches_design_stage"] = True

    name = "estimate_blind.json" if hide else "estimate.json"
    (HERE / name).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for k in ("A", "C"):
        r = out[k]
        print(f"{k}: estimate={r['estimate']} p={r['p']} 90%={r['interval_90']} mde={r['null']['mde_80']}", end=" ")
        print(f"-> {r.get('finding')}")
    print(f"q-values: {out['q_values']}")
    h = out["B_descriptive"]["hours"]
    print(f"B hours (descriptive): estimate={h['estimate']} p={h['p']}")
    print(f"wrote {name}")


if __name__ == "__main__":
    main()
