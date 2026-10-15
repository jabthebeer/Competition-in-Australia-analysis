"""NOT PRE-REGISTERED checks, run after unblinding to help read the registered results.

1. Food prices: Perth's food prices relative to the CPI were already falling against other
   capitals before the reform. Remove each city's own pre-reform linear trend (fitted on
   2000-Q1 to 2010-Q3), then re-run the registered estimator and its comparison-city placebos.
2. Entry and exit means on a balanced panel (without NT, which has no data for 2007-08 and
   2008-09), so the simple before-and-after table matches the estimator.

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


def main() -> None:
    report = {
        "label": "NOT PRE-REGISTERED: run after unblinding to read the registered results",
        "food_price_trend_check": food_trend_check(),
        "balanced_panel_means": balanced_means(),
    }
    (HERE / "posthoc.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
