"""NOT PRE-REGISTERED checks, run after unblinding to help read the registered results.

1. Food prices: Perth's food prices relative to the CPI were already falling against other
   capitals before the reform. Remove each city's own pre-reform linear trend (fitted on
   2000-Q1 to 2010-Q3), then re-run the registered estimator and its comparison-city placebos.
2. Entry and exit means on a balanced panel (without NT, which has no data for 2007-08 and
   2008-09), so the simple before-and-after table matches the estimator.
3. For display only: the comparison-state placebo estimates behind the descriptive productivity
   and pay results (the registered run saved only their spread). The WA estimates are recomputed
   by the same code and must equal estimate.json.

Run: uv run python analyses/wa_trading_hours/posthoc.py
Writes: analyses/wa_trading_hours/posthoc.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from design_review import CONTROLS, FIRST_POST_FY, T_CLASSES, TREATED, WINDOW, cabee, group_rate, restrict
from estimate import FIRST_POST_Q, UNITS, cpi_quarterly, num, relative_price, series

from regimpact.evaluate.did import placebo_in_space, twfe
from regimpact.outcomes import productivity

HERE = Path(__file__).resolve().parent


def detrend_pre(df: pd.DataFrame, first_post) -> pd.DataFrame:
    """Subtract each unit's linear trend fitted on its pre-period only."""
    out = []
    for _, g in df.groupby("unit"):
        pre = g[g["time"] < first_post]
        slope, intercept = np.polyfit(pre["time"].to_numpy(float), pre["y"].to_numpy(float), 1)
        out.append(g.assign(y=g["y"] - (intercept + slope * g["time"]), pre_slope=slope))
    return pd.concat(out, ignore_index=True)


def food_trend_check() -> dict:
    rel = relative_price(cpi_quarterly(), "20001")
    plain = twfe(rel, TREATED, FIRST_POST_Q)
    d = detrend_pre(rel, FIRST_POST_Q)
    est = twfe(d, TREATED, FIRST_POST_Q)
    states = placebo_in_space(d, TREATED, FIRST_POST_Q)
    slopes = d.groupby("unit")["pre_slope"].first() * 4  # log points per year
    post = rel[(rel["unit"] == TREATED) & (rel["time"] >= FIRST_POST_Q)]
    gap = (post.set_index("time")["y"] - rel[rel["unit"].isin(CONTROLS)].groupby("time")["y"].mean()).dropna()
    post_slope = float(np.polyfit(gap.index.to_numpy(float), gap.to_numpy(float), 1)[0]) * 4
    pre_rel = rel[rel["time"] < FIRST_POST_Q]
    pre_gap = (
        pre_rel[pre_rel["unit"] == TREATED].set_index("time")["y"]
        - pre_rel[pre_rel["unit"].isin(CONTROLS)].groupby("time")["y"].mean()
    )
    pre_slope = float(np.polyfit(pre_gap.index.to_numpy(float), pre_gap.to_numpy(float), 1)[0]) * 4
    return {
        "label": "NOT PRE-REGISTERED",
        "registered_estimate_log_points": num(plain),
        "after_removing_each_citys_pre_reform_trend": num(est),
        "p_state_placebo_detrended": num(states.p_value(est)),
        "state_placebos_detrended": series(states.estimates),
        "pre_reform_trend_by_city_log_points_per_year": series(slopes),
        "perth_gap_slope_before_log_points_per_year": num(pre_slope),
        "perth_gap_slope_after_log_points_per_year": num(post_slope),
    }


def balanced_means() -> dict:
    out = {}
    w = cabee()
    for m in ("entries", "exits"):
        t = restrict(group_rate(w, T_CLASSES, m), [u for u in UNITS if u != "NT"], WINDOW)
        post = t["time"] >= FIRST_POST_FY
        wa = t["unit"] == TREATED
        cells = {
            "wa_pre": t[wa & ~post]["y"].mean(),
            "wa_post": t[wa & post]["y"].mean(),
            "comparison_states_pre": t[~wa & ~post]["y"].mean(),
            "comparison_states_post": t[~wa & post]["y"].mean(),
        }
        cells["difference_in_differences"] = (cells["wa_post"] - cells["wa_pre"]) - (
            cells["comparison_states_post"] - cells["comparison_states_pre"]
        )
        out[m] = {k: num(v, 2) for k, v in cells.items()}
    out["note"] = "Comparison states NSW, VIC, QLD, TAS, ACT (NT has no data for 2007-08 and 2008-09)"
    return out


def descriptive_placebos(raw: pd.DataFrame) -> dict:
    """Same steps as estimate.descriptive_productivity, keeping the comparison-state estimates."""
    allg = raw[raw["index_code"] == "10001"].copy()
    allg["fy"] = allg["q"] // 4 + (allg["q"] % 4 >= 2)
    cpi = allg.groupby(["fy", "state"])["value"].agg(["mean", "count"]).reset_index()
    cpi = cpi[cpi["count"] == 4].rename(columns={"mean": "cpi"})[["fy", "state", "cpi"]]
    p = productivity.panel(cpi)
    registered = json.loads((HERE / "estimate.json").read_text(encoding="utf-8"))["descriptive_productivity_and_pay"]
    out = {}
    for var, years in (("gva_per_worker", (1990, 2018)), ("real_coe_per_worker", (2001, 2018))):
        g = p[(p["division"] == "G") & p["state"].isin(UNITS) & p["fy"].between(*years)].copy()
        g = g.rename(columns={"state": "unit", "fy": "time"})
        g["y"] = 100 * np.log(g[var])
        df = g[["unit", "time", "y"]].dropna()
        est = twfe(df, TREATED, FIRST_POST_FY)
        assert num(est) == registered[var]["estimate_log_points"], f"{var} does not reproduce estimate.json"
        out[var] = {
            "estimate_log_points": num(est),
            "state_placebos": series(placebo_in_space(df, TREATED, FIRST_POST_FY).estimates),
        }
    return out


def main() -> None:
    report = {
        "label": "NOT PRE-REGISTERED: run after unblinding to read the registered results",
        "food_price_trend_check": food_trend_check(),
        "balanced_panel_means": balanced_means(),
        "descriptive_placebos_for_display": descriptive_placebos(cpi_quarterly()),
    }
    (HERE / "posthoc.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
