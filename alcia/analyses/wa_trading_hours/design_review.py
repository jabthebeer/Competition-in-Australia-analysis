"""Design-stage robustness review for the Perth trading-hours deregulation (blinded).

Case: WA Retail Trading Hours Amendment Act 2010 (9pm weeknight trading from 1 Nov 2010, after
special trading precincts from Jul-Sep 2010) and Amendment Act 2012 (Sunday trading from
26 Aug 2012), metropolitan Perth. First exposed financial year 2010-11 (fy 2011).

BLINDING: nothing here reports WA's outcomes for affected retail after the reform (fy >= 2011,
or CPI quarters from 2010-Q4). Every number is computed from (a) comparison states, (b) WA
before the reform, or (c) WA industries the reform did not touch. The treated post-period is
set to missing before any estimator runs. (Exception, disclosed: WA division-level retail
productivity was displayed once during data validation on 15 Oct 2026.)

Run: uv run python analyses/wa_trading_hours/design_review.py
Writes: analyses/wa_trading_hours/design_review.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from alcia.evaluate.did import Z_80_POWER_5PC, Placebo, blind, event_study, placebo_in_space, recovery, twfe
from alcia.outcomes import productivity
from alcia.outcomes.abs_series import CITY_STATE, fetch_cpi

HERE = Path(__file__).resolve().parent
PANEL = HERE.parents[1] / "data" / "processed"

TREATED = "WA"
CONTROLS = ["NSW", "VIC", "QLD", "TAS", "ACT", "NT"]  # SA excluded: Adelaide CBD trading change in April 2012
FIRST_POST_FY = 2011
WINDOW = range(2008, 2019)  # 2007-08 to 2017-18; 2018-19 is a vintage break (identity fails) -> sensitivity only
T_CLASSES = ["4110", "4251", "4260"]  # supermarkets and grocery, clothing, department stores (general retail shops)
C_CLASSES = ["4511", "4512", "4000"]  # cafes and restaurants, takeaway food, fuel retailing (not general retail)
EXCLUDE_FROM_PLACEBO_DIVS = {"G"}  # retail is (partly) treated
RNG = np.random.default_rng(20261015)


def cabee() -> pd.DataFrame:
    p = pd.read_csv(PANEL / "cabee_class_state_fy.csv.gz", dtype={"anzsic": str})
    p = p[(p["band"] == "total") & p["measure"].isin(["start", "entries", "exits"])]
    return p.pivot_table(index=["fy", "state", "anzsic"], columns="measure", values="value").reset_index()


def group_rate(w: pd.DataFrame, classes: list[str], measure: str = "entries") -> pd.DataFrame:
    g = w[w["anzsic"].isin(classes)].groupby(["state", "fy"])[["start", measure]].sum().reset_index()
    g["y"] = 100 * g[measure] / g["start"]  # per 100 businesses operating at the start of the year
    return g.rename(columns={"state": "unit", "fy": "time"})[["unit", "time", "y", "start"]]


def restrict(df: pd.DataFrame, units: list[str], times) -> pd.DataFrame:
    return df[df["unit"].isin(units) & df["time"].isin(list(times))].copy()


def summarise_placebo(p: Placebo) -> dict:
    return {
        "n": int(len(p.estimates)),
        "sd": round(p.sd, 3),
        "mde_80pc": round(p.mde, 3),
        "min_p": round(p.min_p, 3),
        "estimates": {k: round(float(v), 3) for k, v in p.estimates.items()},
    }


def entry_exit_designs(w: pd.DataFrame) -> dict:
    out = {}
    units = [TREATED, *CONTROLS]
    for measure in ("entries", "exits"):
        t = restrict(group_rate(w, T_CLASSES, measure), units, WINDOW)
        c = restrict(group_rate(w, C_CLASSES, measure), units, WINDOW)
        trip = t.merge(c, on=["unit", "time"], suffixes=("", "_c"))
        trip["y"] = trip["y"] - trip["y_c"]
        res = {}
        for name, df in (("did_treated_group", t), ("triple_diff", trip[["unit", "time", "y"]])):
            bl = blind(df, TREATED, FIRST_POST_FY)
            pre = event_study(bl, TREATED, FIRST_POST_FY)  # only pre-period coefficients exist after blinding
            placebo = placebo_in_space(df, TREATED, FIRST_POST_FY)  # comparison states only
            no_qld = placebo_in_space(df[df["unit"] != "QLD"], TREATED, FIRST_POST_FY)
            pre_mean = float(df[(df["unit"] == TREATED) & (df["time"] < FIRST_POST_FY)]["y"].mean())
            res[name] = {
                "wa_pre_mean": round(pre_mean, 2),
                "controls_pre_mean": round(
                    float(df[(df["unit"] != TREATED) & (df["time"] < FIRST_POST_FY)]["y"].mean()), 2
                ),
                "pre_period_event_coefs": {int(k): round(float(v), 2) for k, v in pre.items()},
                "placebo_in_space": summarise_placebo(placebo),
                "placebo_in_space_without_qld": summarise_placebo(no_qld),
                "mde_relative_to_wa_pre_mean": round(placebo.mde / abs(pre_mean), 3) if pre_mean else None,
            }
        sim = recovery(t, TREATED, FIRST_POST_FY, [0.0, 1.0, 2.0, 3.0, 5.0])
        res["simulation_recovery_did"] = (
            sim.groupby("planted")
            .agg(
                mean_estimate=("estimate", "mean"),
                mean_abs_error=("estimate", lambda s: 0),
                share_p_min=("p", lambda p: float((p <= p.min() + 1e-12).mean())),
            )
            .reset_index()
            .round(3)
            .to_dict("records")
        )
        for r in res["simulation_recovery_did"]:
            planted = r["planted"]
            r["mean_abs_error"] = round(float((sim.loc[sim.planted == planted, "estimate"] - planted).abs().mean()), 3)
        out[measure] = res
    return out


def placebo_industries(w: pd.DataFrame, draws: int = 1000, measure: str = "entries") -> dict:
    """WA versus comparison states for random groups of 3 unaffected industry classes: a finer-grained
    reference distribution (it uses WA's post-period only for industries the reform did not touch)."""
    units = [TREATED, *CONTROLS]
    base = w[(w["fy"] == 2010) & (w["state"] == TREATED)]
    t_size = float(base[base["anzsic"].isin(T_CLASSES)]["start"].sum())
    from alcia import anzsic

    eligible = [
        c
        for c in base["anzsic"].unique()
        if anzsic.division(c) not in EXCLUDE_FROM_PLACEBO_DIVS and c not in C_CLASSES and c != "9999"
    ]
    sizes = base.set_index("anzsic")["start"]
    eligible = [c for c in eligible if sizes.get(c, 0) >= 50]
    est = []
    for _ in range(draws):
        pick = list(RNG.choice(eligible, size=3, replace=False))
        if not 0.5 * t_size <= float(sizes[pick].sum()) <= 2.0 * t_size:
            continue
        g = restrict(group_rate(w, pick, measure), units, WINDOW)
        if (g["unit"] == TREATED).sum() < len(WINDOW):  # WA needs every year; small territories may have gaps
            continue
        est.append(twfe(g, TREATED, FIRST_POST_FY))
    p = Placebo(pd.Series(est))
    centred = p.estimates - p.estimates.mean()
    crit = float(np.quantile(centred.abs(), 0.95))
    # The estimator is linear in the planted effect, so power for an effect d is the share of placebo
    # groups whose centred estimate plus d lands beyond the 5% two-sided critical value.
    power = {f"{d:g}": round(float(((centred + d).abs() > crit).mean()), 3) for d in (1, 2, 3, 4, 5, 6, 8)}
    return {
        "measure": measure,
        "draws_kept": len(est),
        "eligible_classes": len(eligible),
        "treated_group_wa_2010_start": t_size,
        "mean": round(float(p.estimates.mean()), 3),
        "sd": round(p.sd, 3),
        "mde_80pc": round(p.mde, 3),
        "critical_value_5pc": round(crit, 3),
        "power_by_effect_per_100": power,
        "min_p": round(p.min_p, 4),
        "note": "mean != 0 measures WA-wide shocks common to unaffected industries (e.g. the mining cycle)",
    }


def vintage_check(w_overlap: pd.DataFrame, w_own: pd.DataFrame) -> dict:
    """Entry-rate revisions between vintages, for comparison states (all years) and WA before the reform."""
    out = {}
    for label, classes in (("treated_group", T_CLASSES), ("comparison_group", C_CLASSES)):
        own = group_rate(w_own, classes)
        ov = (
            w_overlap[w_overlap["anzsic"].isin(classes)].groupby(["release", "state", "fy"])[["start", "entries"]].sum()
        )
        ov = ov.reset_index()
        ov["y_overlap"] = 100 * ov["entries"] / ov["start"]
        m = ov.merge(own, left_on=["state", "fy"], right_on=["unit", "time"])
        m = m[(m["state"].isin(CONTROLS)) | ((m["state"] == TREATED) & (m["fy"] < FIRST_POST_FY))]
        diff = (m["y_overlap"] - m["y"]).abs()
        out[label] = {
            "pairs": int(len(m)),
            "mean_abs_revision_pp": round(float(diff.mean()), 3),
            "max_abs_revision_pp": round(float(diff.max()), 3),
        }
    return out


def productivity_design() -> dict:
    p = productivity.panel()
    units = [TREATED, *CONTROLS]
    g = p[(p["division"] == "G") & p["state"].isin(units) & p["fy"].between(1990, 2018)].copy()
    g = g.rename(columns={"state": "unit", "fy": "time"})
    g["y"] = 100 * np.log(g["gva_per_worker"])
    df = g[["unit", "time", "y"]]
    placebo = placebo_in_space(df, TREATED, FIRST_POST_FY)
    pre = blind(df, TREATED, FIRST_POST_FY)
    # Placebo in time inside the pre-period: pretend the reform began in 2004-05 or 2006-07.
    in_time = {str(fake): round(twfe(pre[pre["time"] < FIRST_POST_FY], TREATED, fake), 2) for fake in (2005, 2007)}
    # Dilution: share of WA retail businesses in store-based retailing (subdivisions 41 and 42) in 2009-10.
    w = cabee()
    wa = w[(w["state"] == TREATED) & (w["fy"] == 2010) & w["anzsic"].str[:1].isin(["3", "4"])]
    from alcia import anzsic

    wa = wa[wa["anzsic"].map(anzsic.division) == "G"]
    store = wa[wa["anzsic"].str[:2].isin(["41", "42"])]["start"].sum()
    return {
        "outcome": "100 x log real retail value added per employed person, division G",
        "years": "1989-90 to 2017-18",
        "placebo_in_space": summarise_placebo(placebo),
        "pre_period_placebo_in_time": in_time,
        "store_based_share_of_wa_retail_businesses_2010": round(float(store / wa["start"].sum()), 3),
        "blinding_note": "WA's post-2011 division G series was displayed once during data validation; "
        "results for this outcome are not blind and are graded accordingly",
    }


def cpi_design() -> dict:
    codes = {"10001": "All groups", "20001": "Food and non-alcoholic beverages", "20002": "Clothing and footwear"}
    raw = fetch_cpi(list(codes), start="2000-Q1", end="2019-Q4")
    raw["state"] = raw["city"].map(CITY_STATE)
    raw["q"] = raw["period"].str[:4].astype(int) * 4 + raw["period"].str[-1].astype(int) - 1
    first_post_q = 2010 * 4 + 3  # 2010-Q4
    units = [TREATED, *CONTROLS]
    out = {}
    for code in ("20001", "20002"):
        a = raw[raw["index_code"] == code].set_index(["state", "q"])["value"]
        b = raw[raw["index_code"] == "10001"].set_index(["state", "q"])["value"]
        rel = (100 * np.log(a / b)).dropna().reset_index().rename(columns={"state": "unit", "q": "time", 0: "y"})
        rel.columns = ["unit", "time", "y"]
        rel = rel[rel["unit"].isin(units)]
        placebo = placebo_in_space(rel, TREATED, first_post_q)
        pre = blind(rel, TREATED, first_post_q)
        in_time = round(twfe(pre[pre["time"] < first_post_q], TREATED, 2006 * 4), 2)
        out[codes[code]] = {
            "outcome": f"100 x log({codes[code]} / All groups), capital city, quarterly 2000-Q1 to 2019-Q4",
            "placebo_in_space": summarise_placebo(placebo),
            "pre_period_placebo_in_time_2006q1": in_time,
        }
    return out


def main() -> None:
    w = cabee()
    ov = pd.read_csv(PANEL / "cabee_class_state_fy_overlaps.csv.gz", dtype={"anzsic": str})
    ov = ov[(ov["band"] == "total") & ov["measure"].isin(["start", "entries"])]
    ov = ov.pivot_table(index=["release", "fy", "state", "anzsic"], columns="measure", values="value").reset_index()
    pre_cells = (
        w[(w["state"] == TREATED) & (w["fy"] < FIRST_POST_FY) & w["anzsic"].isin(T_CLASSES + C_CLASSES)]
        .groupby("anzsic")[["start", "entries", "exits"]]
        .mean()
        .round(0)
        .to_dict("index")
    )
    report = {
        "case": "Perth retail trading-hours deregulation (2010 weeknights and precincts; 2012 Sundays)",
        "blinding": "WA affected-retail outcomes from 2010-11 and Perth CPI from 2010-Q4 are never reported here",
        "z_80_power_5pc": round(Z_80_POWER_5PC, 3),
        "wa_pre_period_cell_sizes_mean_2008_2010": pre_cells,
        "entry_exit": entry_exit_designs(w),
        "placebo_industries_wa": {m: placebo_industries(w, measure=m) for m in ("entries", "exits")},
        "vintage_revisions": vintage_check(ov, w),
        "productivity": productivity_design(),
        "cpi": cpi_design(),
    }
    (HERE / "design_review.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1)[:200000])


if __name__ == "__main__":
    main()
