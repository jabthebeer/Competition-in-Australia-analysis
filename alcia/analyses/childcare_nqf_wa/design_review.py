"""Design-stage review for the NQF-in-WA evaluation (blinded).

BLINDING: WA's childcare outcomes are set to missing from January 2012 on (when the other
jurisdictions adopted), before anything is computed. Every number below comes from the other
jurisdictions, from WA before 2012, or from WA industries the framework did not touch. Reported:
coverage, the no-effect distribution and smallest detectable effect of each estimand, and WA's
own fake-date diagnostics.

Run: uv run python analyses/childcare_nqf_wa/design_review.py
Writes: analyses/childcare_nqf_wa/design.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import spec

from alcia.evaluate.stagger import Null

HERE = Path(__file__).resolve().parent
ESTIMANDS = ("pooled", "early", "late")


def review(name: str, childcare: pd.DataFrame, placebos: dict, windows, first_data, season=spec.quarter) -> dict:
    blinded = spec.hide(childcare, windows.t1)
    nul = spec.null(placebos, blinded, windows, first_data, season)
    nul_trend = spec.null(placebos, blinded, windows, first_data, season, trend=True)
    wa = blinded[(blinded["unit"] == spec.LATE) & (blinded["time"] >= windows.pre_start)]
    fake = nul[nul["source"].str.startswith("childcare")]
    out = {
        "outcome": name,
        "windows": {k: str(getattr(windows, k).date()) for k in ("pre_start", "t1", "t2", "end")},
        "placebo_industries": int(len(placebos)),
        "fake_dates": int(len(fake)),
        "null": {e: Null(nul[e]).summary() for e in ESTIMANDS},
        "null_detrended": {e: Null(nul_trend[e]).summary() for e in ESTIMANDS},
        "wa_pre_level": round(float(wa.loc[wa["time"] < windows.t1, "y"].mean()), 3),
    }
    # WA's own fake-date diagnostic: childcare at the latest fake date, against the rest of the null
    latest = fake.iloc[0] if len(fake) else None  # FAKE_YEARS starts at the most recent shift
    if latest is not None:
        rest = nul.drop(index=latest.name)
        out["wa_fake_date_test"] = {
            "source": latest["source"],
            **{
                e: {"estimate": round(float(latest[e]), 3), "p": round(Null(rest[e]).p_value(latest[e]), 3)}
                for e in ESTIMANDS
            },
        }
    pre = spec.path(blinded, windows, season)
    pre = pre[pre.index < windows.t1]
    out["wa_pre_gap_sd"] = round(float(pre.std(ddof=1)), 3)
    return out


def main() -> None:
    hours, emp = spec.lfs("hours_actual"), spec.lfs("employed")
    groups = spec.lfs_placebos(hours)
    abn = spec.abn_counts()
    codes = spec.abn_placebos(abn)
    ent = spec.abn_counts("abn_active_since")
    ent_codes = spec.abn_placebos(ent)
    rel = spec.cpi()
    classes = [c for c in spec.cpi_placebos() if c in rel.index.get_level_values(0)]
    lfs_start = pd.Timestamp("1985-01-01")
    out = {
        "blinding": "WA childcare outcomes hidden from January 2012 on",
        "hours": review(
            "hours",
            spec.lfs_panel(hours, spec.CHILDCARE_GROUP),
            {g: spec.lfs_panel(hours, g) for g in groups},
            spec.QUARTERLY,
            lfs_start,
        ),
        "employment": review(
            "employment",
            spec.lfs_panel(emp, spec.CHILDCARE_GROUP),
            {g: spec.lfs_panel(emp, g) for g in groups},
            spec.QUARTERLY,
            lfs_start,
        ),
        "exits": review(
            "exits",
            spec.abn_panel(abn, spec.CHILDCARE_CLASS),
            {c: spec.abn_panel(abn, c) for c in codes},
            spec.MONTHLY,
            pd.Timestamp("1999-07-01"),
        ),
        "entries": review(
            "entries",
            spec.abn_panel(ent, spec.CHILDCARE_CLASS),
            {c: spec.abn_panel(ent, c) for c in ent_codes},
            spec.MONTHLY,
            pd.Timestamp("1999-07-01"),
        ),
        "prices": review(
            "prices",
            spec.cpi_panel(rel, spec.CPI_CHILD_CARE),
            {c: spec.cpi_panel(rel, c) for c in classes},
            spec.QUARTERLY,
            rel.index.get_level_values("period").min(),
        ),
        "placebo_lists": {
            "lfs_groups": groups,
            "abn_codes": codes,
            "abn_entry_codes": ent_codes,
            "cpi_classes": len(classes),
        },
    }
    (HERE / "design.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for k in ("hours", "employment", "exits", "entries", "prices"):
        v = out[k]
        n = v["null"]
        line = f"{k:10s} placebos={v['placebo_industries']:3d} fakes={v['fake_dates']:2d} "
        line += " | ".join(f"{e}: sd={n[e]['sd']:.2f} mde={n[e]['mde_80']:.1f}" for e in ESTIMANDS)
        f = v.get("wa_fake_date_test", {})
        if f:
            line += f" | WA fake {f['source']}: pooled {f['pooled']['estimate']:+.2f} p={f['pooled']['p']:.2f}"
        print(line)


if __name__ == "__main__":
    main()
