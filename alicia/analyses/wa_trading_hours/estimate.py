"""Pre-registered estimation: Perth trading-hours deregulation and retail entry and exit.

Implements docs/pap_wa_trading_hours.md (registered 15 October 2026): §5 estimators, §6 inference,
§7 interpretation rule, §8 robustness list, §9 decision rule and grade. Points the plan left open
were settled before unblinding and are listed in the plan's §10 ("clarifications"). Anything
the plan does not ask for is labelled "not pre-registered" in the output.

Dry run first: the treated outcomes are hidden exactly as in the design review. This checks the
pipeline and that the placebo draws reproduce design_review.json:
    uv run python analyses/wa_trading_hours/estimate.py --blind
The registered analysis (unblinded):
    uv run python analyses/wa_trading_hours/estimate.py
Writes estimate_blind.json or estimate.json next to this file.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from design_review import (
    C_CLASSES,
    CONTROLS,
    EXCLUDE_FROM_PLACEBO_DIVS,
    FIRST_POST_FY,
    PANEL,
    T_CLASSES,
    TREATED,
    WINDOW,
    cabee,
    group_rate,
    restrict,
)

from alicia import anzsic
from alicia.evaluate.did import Placebo, blind, event_study, placebo_in_space, twfe
from alicia.outcomes import productivity
from alicia.outcomes.abs_series import CITY_STATE, fetch_cpi
from alicia.outcomes.cabee import as_registered

HERE = Path(__file__).resolve().parent
SEED = 20261015
DRAWS = 1000
UNITS = [TREATED, *CONTROLS]
WINDOW_2019 = range(2008, 2020)  # §8.2: adds 2018-19, the year with the identity break
FIRST_POST_Q = 2010 * 4 + 3  # 2010-Q4, as quarters counted year * 4 + (quarter - 1)
EFFECT_OF_INTEREST = 5.0  # per 100 businesses: the §7 interpretation rule
BLIND = False


# --- helpers -------------------------------------------------------------------------------------


def hide(df: pd.DataFrame, first_post) -> pd.DataFrame:
    """In the dry run, hide WA's treated outcomes from the first exposed period, as in the review."""
    return blind(df, TREATED, first_post) if BLIND else df


def num(x, nd: int = 3):
    """JSON-safe rounding (NaN becomes null)."""
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) else round(x, nd)


def p_value(placebo: Placebo, estimate: float) -> float:
    return float("nan") if math.isnan(estimate) else placebo.p_value(estimate)


def series(s: pd.Series, nd: int = 3) -> dict:
    return {str(k): num(v, nd) for k, v in s.items()}


# --- placebo industry groups (§3) ----------------------------------------------------------------


def eligible_classes(w: pd.DataFrame, divisions: set[str] | None = None) -> tuple[list[str], pd.Series, float]:
    """Classes outside division G with at least 50 WA businesses in 2009-10, in the review's order."""
    base = w[(w["fy"] == 2010) & (w["state"] == TREATED)]
    sizes = base.set_index("anzsic")["start"]
    t_size = float(base[base["anzsic"].isin(T_CLASSES)]["start"].sum())
    eligible = [
        c
        for c in base["anzsic"].unique()
        if anzsic.division(c) not in EXCLUDE_FROM_PLACEBO_DIVS and c not in C_CLASSES and c != "9999"
    ]
    eligible = [c for c in eligible if sizes.get(c, 0) >= 50]
    if divisions:
        eligible = [c for c in eligible if anzsic.division(c) in divisions]
    return eligible, sizes, t_size


def draw_groups(w: pd.DataFrame, rng: np.random.Generator, divisions: set[str] | None = None) -> list[list[str]]:
    """1,000 random groups of 3 classes; keep those between half and twice the treated group's size."""
    eligible, sizes, t_size = eligible_classes(w, divisions)
    picks = []
    for _ in range(DRAWS):
        pick = list(rng.choice(eligible, size=3, replace=False))
        if 0.5 * t_size <= float(sizes[pick].sum()) <= 2.0 * t_size:
            picks.append(pick)
    return picks


def placebo_panels(w, picks, measure, units, window) -> list[pd.DataFrame]:
    """WA-versus-states panels for each placebo group; groups where WA lacks a year are dropped."""
    out = []
    for pick in picks:
        g = restrict(group_rate(w, pick, measure), units, window)
        if (g["unit"] == TREATED).sum() >= len(window):
            out.append(g)
    return out


# --- §5-§6: the primary estimator and its inference ----------------------------------------------


def estimate(w, measure, picks, units=UNITS, window=WINDOW, classes=T_CLASSES) -> dict:
    """delta = delta_T - mean(delta_placebo); rank p-value and intervals from the centred placebos."""
    t = hide(restrict(group_rate(w, classes, measure), units, window), FIRST_POST_FY)
    d_t = twfe(t, TREATED, FIRST_POST_FY)
    plac = pd.Series([twfe(g, TREATED, FIRST_POST_FY) for g in placebo_panels(w, picks, measure, units, window)])
    shock = float(plac.mean())
    centred = Placebo(plac - shock)
    delta = d_t - shock
    states = placebo_in_space(t, TREATED, FIRST_POST_FY)
    lo90, hi90 = centred.interval(delta, 0.90) if not math.isnan(delta) else (float("nan"),) * 2
    lo95, hi95 = centred.interval(delta, 0.95) if not math.isnan(delta) else (float("nan"),) * 2
    return {
        "delta": num(delta),
        "delta_T_plain_did": num(d_t),
        "wa_wide_shock_placebo_mean": num(shock),
        "placebo_groups": int(len(plac)),
        "placebo_sd": num(centred.sd),
        "mde_80pc": num(centred.mde),
        "p_industry_placebo": num(p_value(centred, delta), 4),
        "interval_90": [num(lo90), num(hi90)],
        "interval_95_not_preregistered": [num(lo95), num(hi95)],
        "p_state_placebo_for_delta_T": num(p_value(states, d_t)),
        "p_state_placebo_for_delta_not_preregistered": num(p_value(states, delta)),
        "state_placebos": series(states.estimates),
    }


def event_paths(w, measure, picks) -> dict:
    """§5.3 plain event study, and the same net of the placebo mean for each year (clarification C7)."""
    t = hide(restrict(group_rate(w, T_CLASSES, measure), UNITS, WINDOW), FIRST_POST_FY)
    raw = event_study(t, TREATED, FIRST_POST_FY)
    plac = pd.DataFrame(
        [event_study(g, TREATED, FIRST_POST_FY) for g in placebo_panels(w, picks, measure, UNITS, WINDOW)]
    )
    shock = plac.mean()
    centred = plac - shock
    net = raw.reindex(shock.index) - shock
    out = {
        "reference": "2009-10 (k = -1); k = 0 is 2010-11",
        "plain": series(raw.reindex(shock.index)),
        "placebo_mean": series(shock),
        "net": series(net),
        "net_band_90": {
            str(k): [num(net[k] - centred[k].quantile(0.95)), num(net[k] - centred[k].quantile(0.05))]
            for k in net.index
        },
        "net_band_95": {
            str(k): [num(net[k] - centred[k].quantile(0.975)), num(net[k] - centred[k].quantile(0.025))]
            for k in net.index
        },
    }
    pre = [k for k in net.index if k < -1]
    out["pre_period_inside_95_band"] = (
        None
        if net[pre].isna().any()
        else bool(all(centred[k].quantile(0.025) <= net[k] <= centred[k].quantile(0.975) for k in pre))
    )
    out["sensitivity_net"] = trend_sensitivity(net)
    out["sensitivity_plain"] = trend_sensitivity(raw.reindex(shock.index))
    return out


def trend_sensitivity(path: pd.Series) -> dict:
    """§8.6: how large a violation of parallel trends would overturn the sign of the average post effect.

    Relative magnitudes (Rambachan and Roth 2023, point-identified version, sampling noise ignored):
    if each post-period step in the trend violation can be up to M times the largest pre-period step,
    the average post effect is identified only up to +/- M * max_step * mean(k + 1); the breakdown M
    is where that band first reaches zero. Linear trend: the slope through the pre-period
    coefficients (reference year = 0) extrapolated forward, and the slope that would cancel the effect."""
    pre = pd.concat([path[path.index < -1], pd.Series({-1: 0.0})]).sort_index()
    post = path[path.index >= 0]
    if post.isna().any() or pre.isna().any():
        return {"note": "post-period hidden (dry run)"}
    step = float(pre.diff().abs().max())
    theta = float(post.mean())
    lever = float(np.mean(np.asarray(post.index) + 1))
    slope = float(np.polyfit(np.asarray(pre.index, float), pre.to_numpy(float), 1)[0])
    return {
        "average_post_effect": num(theta),
        "largest_pre_period_step": num(step),
        "relative_magnitude_breakdown": num(abs(theta) / (step * lever)),
        "pre_trend_slope_per_year": num(slope),
        "breakeven_slope_per_year": num(theta / lever),
        "linear_trend_adjusted_average_post_effect": num(theta - slope * lever),
    }


def triple_difference(w, measure) -> dict:
    """§5.4: (treated group - cafes, takeaway and fuel) for WA versus comparison states."""
    t = restrict(group_rate(w, T_CLASSES, measure), UNITS, WINDOW)
    c = restrict(group_rate(w, C_CLASSES, measure), UNITS, WINDOW)
    trip = t.merge(c, on=["unit", "time"], suffixes=("", "_c"))
    trip["y"] = trip["y"] - trip["y_c"]
    trip = hide(trip[["unit", "time", "y"]], FIRST_POST_FY)
    d = twfe(trip, TREATED, FIRST_POST_FY)
    states = placebo_in_space(trip, TREATED, FIRST_POST_FY)
    return {
        "estimate": num(d),
        "p_state_placebo": num(p_value(states, d)),
        "state_placebo_sd": num(states.sd),
        "event_study": series(event_study(trip, TREATED, FIRST_POST_FY)),
    }


def raw_means(w, measure, picks) -> dict:
    """Descriptive 2x2 means behind the estimate (per 100 businesses at the start of the year)."""
    t = hide(restrict(group_rate(w, T_CLASSES, measure), UNITS, WINDOW), FIRST_POST_FY)
    post = t["time"] >= FIRST_POST_FY
    wa = t["unit"] == TREATED
    return {
        "wa_pre": num(t[wa & ~post]["y"].mean(), 2),
        "wa_post": num(t[wa & post]["y"].mean(), 2),
        "comparison_states_pre": num(t[~wa & ~post]["y"].mean(), 2),
        "comparison_states_post": num(t[~wa & post]["y"].mean(), 2),
        "wa_by_year": series(t[wa].set_index("time")["y"], 2),
        "comparison_states_by_year": series(t[~wa].groupby("time")["y"].mean(), 2),
    }


# --- §8 robustness -------------------------------------------------------------------------------


def overlap_vintage(w: pd.DataFrame) -> tuple[pd.DataFrame, list[int]]:
    """§8.1: replace each year that has a second vintage with that vintage (clarification C2)."""
    ov = as_registered(pd.read_csv(PANEL / "cabee_class_state_fy_overlaps.csv.gz", dtype={"anzsic": str}))
    ov = ov[(ov["band"] == "total") & ov["measure"].isin(["start", "entries", "exits"])]
    assert ov.groupby("fy")["release"].nunique().max() == 1, "expected one alternative vintage per year"
    ov = ov.pivot_table(index=["fy", "state", "anzsic"], columns="measure", values="value").reset_index()
    years = sorted(int(y) for y in ov["fy"].unique())
    return pd.concat([w[~w["fy"].isin(years)], ov], ignore_index=True), years


def robustness(w, w_ov, measure, picks, picks_hs, broad) -> dict:
    variants = {
        "1_vintage_overlap": {"w": w_ov},
        "2_window_to_2018_19": {"window": WINDOW_2019},
        **{f"3_leave_out_{s}": {"units": [u for u in UNITS if u != s]} for s in CONTROLS},
        "3_drop_NT_and_ACT": {"units": [u for u in UNITS if u not in ("NT", "ACT")]},
        "4_treated_subdivisions_41_42_less_liquor": {"classes": broad},
        "5_placebo_pool_divisions_H_and_S": {"picks": picks_hs},
    }
    out = {}
    for name, v in variants.items():
        r = estimate(
            v.get("w", w),
            measure,
            v.get("picks", picks),
            units=v.get("units", UNITS),
            window=v.get("window", WINDOW),
            classes=v.get("classes", T_CLASSES),
        )
        out[name] = {k: r[k] for k in ("delta", "delta_T_plain_did", "p_industry_placebo", "interval_90")} | {
            "placebo_groups": r["placebo_groups"],
            "wa_wide_shock_placebo_mean": r["wa_wide_shock_placebo_mean"],
        }
    return out


# --- prices and descriptive outcomes -------------------------------------------------------------


def cpi_quarterly() -> pd.DataFrame:
    raw = fetch_cpi(["10001", "20001", "20002"], start="2000-Q1", end="2019-Q4")
    raw["state"] = raw["city"].map(CITY_STATE)
    raw["q"] = raw["period"].str[:4].astype(int) * 4 + raw["period"].str[-1].astype(int) - 1
    return raw


def relative_price(raw: pd.DataFrame, code: str) -> pd.DataFrame:
    a = raw[raw["index_code"] == code].set_index(["state", "q"])["value"]
    b = raw[raw["index_code"] == "10001"].set_index(["state", "q"])["value"]
    rel = (100 * np.log(a / b)).dropna().reset_index()
    rel.columns = ["unit", "time", "y"]
    return rel[rel["unit"].isin(UNITS)]


def prices(raw: pd.DataFrame) -> dict:
    """§5.5: 100 x log(group / All groups), Perth versus the comparison capitals, city and quarter effects."""
    out = {}
    for code, label, role in (
        ("20001", "Food and non-alcoholic beverages", "secondary (pre-registered)"),
        ("20002", "Clothing and footwear", "descriptive only"),
    ):
        rel = hide(relative_price(raw, code), FIRST_POST_Q)
        d = twfe(rel, TREATED, FIRST_POST_Q)
        states = placebo_in_space(rel, TREATED, FIRST_POST_Q)
        rel["fy"] = rel["time"] // 4 + (rel["time"] % 4 >= 2)  # Sep quarter (q index 2) starts the financial year
        by_fy = rel.groupby(["unit", "fy"])["y"].mean().unstack("unit")
        gap = by_fy[TREATED] - by_fy[CONTROLS].mean(axis=1)
        gap = gap - gap.get(2010, np.nan)
        out[label] = {
            "role": role,
            "estimate_log_points": num(d),
            "p_state_placebo": num(p_value(states, d)),
            "state_placebo_sd": num(states.sd),
            "mde_80pc": num(states.mde),
            "state_placebos": series(states.estimates),
            "perth_gap_vs_other_capitals_by_fy_relative_to_2009_10": series(gap, 2),
        }
    return out


def descriptive_productivity(raw: pd.DataFrame) -> dict:
    """Descriptive only (plan §4): retail output and real pay per worker, WA versus comparison states.
    Output per worker is not blind (robustness review §5)."""
    allg = raw[raw["index_code"] == "10001"].copy()
    allg["fy"] = allg["q"] // 4 + (allg["q"] % 4 >= 2)
    cpi = allg.groupby(["fy", "state"])["value"].agg(["mean", "count"]).reset_index()
    cpi = cpi[cpi["count"] == 4].rename(columns={"mean": "cpi"})[["fy", "state", "cpi"]]
    p = productivity.panel(cpi)
    out = {}
    for var, years, label in (
        ("gva_per_worker", (1990, 2018), "real value added per employed person (not blind)"),
        ("real_coe_per_worker", (2001, 2018), "real compensation of employees per employed person"),
    ):
        g = p[(p["division"] == "G") & p["state"].isin(UNITS) & p["fy"].between(*years)].copy()
        g = g.rename(columns={"state": "unit", "fy": "time"})
        g["y"] = 100 * np.log(g[var])
        df = hide(g[["unit", "time", "y"]].dropna(), FIRST_POST_FY)
        d = twfe(df, TREATED, FIRST_POST_FY)
        states = placebo_in_space(df, TREATED, FIRST_POST_FY)
        out[var] = {
            "label": label,
            "years": f"{years[0] - 1}-{str(years[0])[2:]} to {years[1] - 1}-{str(years[1])[2:]}",
            "estimate_log_points": num(d),
            "p_state_placebo": num(p_value(states, d)),
            "state_placebo_sd": num(states.sd),
        }
    return out


# --- §9 decision rule and grade ------------------------------------------------------------------


def sign(x) -> int | None:
    return None if x is None else int(np.sign(x))


def decide(primary: dict, trip: dict, vintage: dict) -> dict:
    d, p = primary["delta"], primary["p_industry_placebo"]
    if d is None:
        return {"verdict": "hidden (dry run)"}
    signs = [sign(primary["delta_T_plain_did"]), sign(trip["estimate"]), sign(vintage["delta"])]
    if d > 0 and p < 0.05 and all(s == 1 for s in signs):
        verdict = "supports 'enhancing'"
    elif d < 0 and p < 0.05 and all(s == -1 for s in signs):
        verdict = "supports 'weakening'"
    else:
        verdict = "inconclusive"
    lo, hi = primary["interval_90"]
    wide = lo <= 0 <= hi and (lo <= -EFFECT_OF_INTEREST or hi >= EFFECT_OF_INTEREST)
    return {
        "verdict": verdict,
        "conditions": {
            "delta_sign": sign(d),
            "p_below_0_05": p < 0.05,
            "plain_did_same_sign": signs[0] == sign(d),
            "triple_difference_same_sign": signs[1] == sign(d),
            "vintage_no_reversal": signs[2] == sign(d),
        },
        "interval_90_includes_0_and_5_per_100": wide,
    }


def grade(events: dict, primary: dict, robust: dict) -> dict:
    """Clarification C6: Not identified if a pre-period coefficient is outside the 95% placebo band;
    Weak if a §8.1-8.5 variant moves the estimate outside the primary 90% interval; else Moderate."""
    if primary["delta"] is None:
        return {"grade": "hidden (dry run)"}
    lo, hi = primary["interval_90"]
    outside = [k for k, v in robust.items() if v["delta"] is None or not lo <= v["delta"] <= hi]
    if not events["pre_period_inside_95_band"]:
        g = "Not identified"
    elif outside:
        g = "Weak"
    else:
        g = "Moderate"
    return {
        "grade": g,
        "best_possible": "Moderate (one treated state, three pre-reform years)",
        "pre_period_inside_95_band": events["pre_period_inside_95_band"],
        "variants_outside_primary_90_interval": outside,
    }


# --- main ----------------------------------------------------------------------------------------


def reproduces_review(results: dict) -> dict:
    review = json.loads((HERE / "design_review.json").read_text(encoding="utf-8"))["placebo_industries_wa"]
    out = {}
    for m in ("entries", "exits"):
        r, e = review[m], results[m]["primary"]
        out[m] = {
            "draws_kept": [r["draws_kept"], e["placebo_groups"]],
            "mean": [r["mean"], e["wa_wide_shock_placebo_mean"]],
            "sd": [r["sd"], e["placebo_sd"]],
            "match": r["draws_kept"] == e["placebo_groups"]
            and abs(r["mean"] - e["wa_wide_shock_placebo_mean"]) < 1e-3
            and abs(r["sd"] - e["placebo_sd"]) < 1e-3,
        }
    return out


def main() -> None:
    global BLIND
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--blind", action="store_true", help="dry run with the treated outcomes hidden")
    BLIND = ap.parse_args().blind

    w = cabee()
    w_ov, ov_years = overlap_vintage(w)
    rng = np.random.default_rng(SEED)  # one stream: entries draws first, then exits (as in the review)
    picks = {m: draw_groups(w, rng) for m in ("entries", "exits")}
    picks_hs = draw_groups(w, np.random.default_rng(SEED), divisions={"H", "S"})
    broad = sorted(c for c in w["anzsic"].unique() if c[:2] in ("41", "42") and c != "4123")

    results = {}
    for m in ("entries", "exits"):
        primary = estimate(w, m, picks[m])
        events = event_paths(w, m, picks[m])
        trip = triple_difference(w, m)
        robust = robustness(w, w_ov, m, picks[m], picks_hs, broad)
        results[m] = {
            "role": "primary" if m == "entries" else "secondary",
            "raw_means": raw_means(w, m, picks[m]),
            "primary": primary,
            "event_study": events,
            "triple_difference": trip,
            "robustness": robust,
            "decision": decide(primary, trip, robust["1_vintage_overlap"]),
            "grade": grade(events, primary, robust),
        }

    raw = cpi_quarterly()
    price = prices(raw)
    food = price["Food and non-alcoholic beverages"]["estimate_log_points"]
    entry = results["entries"]["primary"]["delta"]
    chain = None
    if food is not None and entry is not None:
        chain = (
            "consistent with 'enhancing' (entry up, food prices down)"
            if entry > 0 and food < 0
            else "consistent with 'weakening' (entry down, food prices up)"
            if entry < 0 and food > 0
            else "mixed"
        )

    report = {
        "case": "Perth retail trading-hours deregulation (2010 weeknights and precincts; 2012 Sundays)",
        "plan": "docs/pap_wa_trading_hours.md (registered 15 October 2026; clarifications C1-C8 in §10)",
        "mode": "DRY RUN: treated outcomes hidden" if BLIND else "UNBLINDED: registered analysis",
        "units": "entries or exits per 100 businesses operating at the start of the financial year",
        "treated_classes": T_CLASSES,
        "comparison_states": CONTROLS,
        "window": f"{WINDOW.start - 1}-{str(WINDOW.start)[2:]} to {WINDOW.stop - 2}-{str(WINDOW.stop - 1)[2:]}",
        "overlap_vintage_years": ov_years,
        "broadened_treated_classes": broad,
        "placebo_pool_H_S_groups": len(picks_hs),
        "reproduces_design_review": None,
        "entries": results["entries"],
        "exits": results["exits"],
        "prices": price,
        "results_chain": chain,
        "descriptive_productivity_and_pay": descriptive_productivity(raw),
    }
    report["reproduces_design_review"] = reproduces_review(results)
    name = "estimate_blind.json" if BLIND else "estimate.json"
    (HERE / name).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
