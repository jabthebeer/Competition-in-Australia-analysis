"""Design-stage review for the Perth weeknight trading re-evaluation (blinded).

BLINDING: WA's outcomes are set to missing from the first excluded (transition) period on (July
2010 for turnover, the August 2010 quarter for hours) and, for business counts, WA retail from
June 2011 on, before anything is computed. Every number below comes from comparison states, from
WA before the reform, or from WA industries the reform did not touch. Reported: data coverage, the
no-effect distribution and smallest detectable effect of each design and its variants, comparison
states' placebo estimates, and WA's own fake-date and pre-period event-study diagnostics.

Run: uv run python analyses/wa_weeknight_2010/design_review.py
Writes: analyses/wa_weeknight_2010/design.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import spec
from spec import TREATED, A, B, C, Design

from alcia.evaluate.did import blind

HERE = Path(__file__).resolve().parent


def hide(df: pd.DataFrame, design: Design) -> pd.DataFrame:
    return blind(df, TREATED, design.hidden_from(sorted(df["time"].unique())))


def review_dates(df: pd.DataFrame, design: Design, units: list[str], label: str, full: bool = True) -> dict:
    """A and B: no-effect distribution from fake dates and comparison states; WA diagnostics."""
    blinded = hide(df, design)
    null = spec.null_dates(blinded, design, units)
    out = {
        "label": label,
        "units": units,
        "null": spec.summarise_null(null["estimate"]),
        "comparison_states_at_true_date": null[null["kind"] == "comparison state"]
        .set_index("unit")["estimate"]
        .round(3)
        .to_dict(),
    }
    if not full:
        return out
    times = sorted(df["time"].unique())
    win, post = design.window(times)
    wa_fake = null[(null["unit"] == TREATED) & (null["kind"] == "fake date")].sort_values("event")
    latest = wa_fake.iloc[-1]
    band = spec.event_band(blinded, design, units)
    pre_es = spec.event_coefficients(blinded, design, units)
    pre_es = pre_es[pre_es.index < 0]
    joined = band.join(pre_es.rename("wa"), how="inner")
    outside = ((joined["wa"] < joined["low"]) | (joined["wa"] > joined["high"])).mean()
    out.update(
        {
            "window": {
                "pre": [str(win[0].date()), str(win[len(win) - len(post) - 1].date())],
                "post": [str(post[0].date()), str(post[-1].date())],
                "periods": {"pre": design.pre, "excluded": design.gap, "post": design.post},
            },
            "fake_events": [str(wa_fake["event"].min().date()), str(wa_fake["event"].max().date())],
            "null_all_dates": spec.summarise_null(
                spec.null_dates(blinded, design, units, since=pd.Timestamp("1900-01-01"))["estimate"]
            ),
            "null_detrended": spec.summarise_null(spec.null_dates(blinded, design, units, trend=True)["estimate"]),
            "wa_fake_date_test": {
                "event": str(latest["event"].date()),
                "estimate": round(float(latest["estimate"]), 3),
                "p": round(spec.p_value(null.drop(index=latest.name)["estimate"], latest["estimate"]), 3),
                "mean_of_last_12": round(float(wa_fake["estimate"].tail(12).mean()), 3),
            },
            "wa_pre_event_study": {
                "coefficients": {int(k): round(float(v), 3) for k, v in pre_es.items()},
                "band": {int(k): [round(float(r["low"]), 3), round(float(r["high"]), 3)] for k, r in band.iterrows()},
                "share_outside_90_band": round(float(outside), 3),
            },
        }
    )
    return out


def review_places(label: str, floor: int = spec.C_FLOOR, **kw) -> dict:
    """C: no-effect distribution from other divisions in every state and retail elsewhere."""
    logs = spec.cabee_areas(**kw)
    null = spec.null_industries(logs, floor=floor)
    retail = spec.panel_c(spec.C_RETAIL, logs)
    units = sorted(retail["unit"].unique())
    pre = spec.event_coefficients(blind(retail, TREATED, C.event), C, units)
    band = spec.event_band_industries(logs, floor)
    return {
        "label": label,
        "units": units,
        "null": spec.summarise_null(null["estimate"]),
        "null_detrended": "not computed: two pre-periods",
        "comparison_states_retail": null[null["division"] == spec.C_RETAIL]
        .set_index("unit")["estimate"]
        .round(3)
        .to_dict(),
        "wa_pre_event_study": {
            "coefficients": {int(k): round(float(v), 3) for k, v in pre[pre.index < 0].items()},
            "band": {int(k): [round(float(r["low"]), 3), round(float(r["high"]), 3)] for k, r in band.iterrows()},
        },
    }


def baselines() -> dict:
    """Pre-reform sizes, for reading effects in levels."""
    w = spec.retail_wide().loc[TREATED]
    t = w.loc["2009-07-01":"2010-06-01"].mean()
    lf = pd.read_parquet(spec.PROCESSED / "abs_lfs" / "industry_state_quarter.parquet")
    lf = lf[
        (lf["geo_code"] == TREATED)
        & (lf["industry_level"] == "group")
        & lf["period"].between("2009-07-01", "2010-04-01")
    ]
    lfm = lf.groupby(["measure", "industry_code"])["value"].mean()
    counts = np.exp(spec.cabee_areas() / 100).round()
    return {
        "turnover_aud_m_per_month_2009_10": {k: round(float(t[k]), 1) for k in spec.A_TREATED + spec.A_FOOD},
        "lfs_2009_10_average": {
            m: {g: round(float(lfm[(m, g)]), 2) for g in spec.B_TREATED + spec.B_FOOD if (m, g) in lfm}
            for m in ("employed", "hours_actual")
        },
        "retail_businesses_june_2010": {
            part: int(counts.loc[(TREATED, part, "G"), pd.Timestamp("2010-06-30")]) for part in ("cap", "rest")
        },
        "abn_named_exits_per_year_2005_2009": {
            f"{a}|{'retail' if r else 'other'}": float(v)
            for (a, r), v in spec.abn_named_exit_counts().stack().items()
            if a.startswith("WA|")
        },
    }


def main() -> None:
    a = spec.panel_a()
    ua = spec.units_a(a)
    ub = [TREATED, *spec.LARGE_STATES]
    out = {
        "blinding": "WA outcomes hidden from the first excluded period on; WA retail counts from June 2011 on",
        "A_turnover": review_dates(a, A, ua, "100 x log turnover: supermarkets, clothing, department stores"),
        "A_variants": {
            "triple_diff_food": review_dates(
                spec.panel_a(den=spec.A_FOOD), A, ua, "minus cafes, restaurants and takeaway", full=False
            ),
            "minus_rest_of_retail_and_food": review_dates(
                spec.panel_a(den=spec.A_OTHER + spec.A_FOOD), A, ua, "minus other retail and food services", False
            ),
            "supermarket_share": review_dates(
                spec.panel_a([spec.A_SHARE[0]], [spec.A_SHARE[1]]), A, ua, "supermarkets minus specialised food", False
            ),
            **{
                f"only_{code}": review_dates(spec.panel_a([code]), A, ua, f"turnover of {code} only", False)
                for code in spec.A_TREATED
            },
        },
        "B_hours": review_dates(spec.panel_b(), B, ub, "100 x log hours worked: groups 411, 425, 426"),
        "B_variants": {
            "employment": review_dates(spec.panel_b("employed"), B, ub, "100 x log employed persons", full=False),
            "triple_diff_food": review_dates(
                spec.panel_b(den=spec.B_FOOD), B, ub, "hours minus cafes, restaurants and takeaway", full=False
            ),
        },
        "C_places": review_places("retail businesses, Perth minus rest of WA, relative to other industries"),
        "C_variants": {
            "small_businesses": review_places("businesses with fewer than 20 employees", bands=spec.SMALL),
            "no_size_floor": review_places("all placebo cells, however small", floor=0),
            "with_mandurah": review_places("Mandurah counted in Perth", include_mandurah=True),
            "without_outback": review_places("WA outback left out", drop_outback=True),
        },
        "baselines": baselines(),
    }
    (HERE / "design.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")

    def line(k: str, v: dict) -> str:
        n = v["null"]
        s = f"{k:32s} null n={n['n']:5d} sd={n['sd']:6.2f} mde={n['mde_80']:6.2f}"
        if "wa_fake_date_test" in v:
            f = v["wa_fake_date_test"]
            s += f" | WA fake {f['event']} {f['estimate']:+.2f} p={f['p']:.2f}"
            s += f" | pre-ES outside band {v['wa_pre_event_study']['share_outside_90_band']:.2f}"
        return s

    for k, v in out.items():
        if isinstance(v, dict) and "null" in v:
            print(line(k, v))
        elif k.endswith("variants"):
            for kk, vv in v.items():
                print(line(f"  {k[0]}:{kk}", vv))


if __name__ == "__main__":
    main()
