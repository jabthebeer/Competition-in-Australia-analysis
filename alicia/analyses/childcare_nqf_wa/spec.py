"""National Quality Framework for childcare in WA: the seven-month delay, with monthly and quarterly data.

Shared by design_review.py (blinded) and estimate.py (registered run); plan in docs/pap_childcare_nqf_wa.md.

The framework started on 1 January 2012 in every jurisdiction except WA, which started on 1 August
2012. Method: the on-off difference-in-differences in ``alicia.evaluate.stagger``. The WA-minus-others
gap should move when the others adopt and move back when WA adopts.

Outcomes (each WA against the other seven jurisdictions pooled):
  hours        100 x log hours actually worked, ANZSIC group 871 Child care services (LFS EQ06, quarterly)
  employment   100 x log employed persons, same group
  exits        childcare-named businesses' share of named-business ABN cancellations (%, monthly)
  entries      the same share of ABNs still active, by the month they became active (survivors)
  prices       100 x log(Child care CPI / All groups CPI), capital cities (quarterly)
No-effect distributions: other industries (or CPI classes) over the same windows, and childcare
itself at fake dates two or more years earlier.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from alicia import anzsic
from alicia.evaluate import stagger
from alicia.pipeline.store import PROCESSED
from alicia.runner.spec import load

# Design constants, from the specification file (alicia/specs/childcare-nqf-wa-delay-2012.json).
SPEC = load("childcare-nqf-wa-delay-2012")
_P = SPEC.parameters
LATE = _P["late"]
EARLY = _P["early"]
OTHERS = "others"  # the early jurisdictions pooled
NQF = pd.Timestamp(_P["nqf"])  # all jurisdictions except WA
NQF_WA = pd.Timestamp(_P["nqf_wa"])
CHILDCARE_GROUP = _P["childcare_group"]
CHILDCARE_CLASS = _P["childcare_class"]
EXCLUDED_DIVISIONS = set(_P["excluded_divisions"])  # education and training; health care and social assistance
LFS_SIZE = tuple(_P["lfs_size"])  # placebo groups: WA employment ('000) in this range, 2009-2011 (childcare 9.4)
ABN_SIZE = tuple(_P["abn_size"])  # placebo named industries: WA cancellations a year, 2009-2011
CPI_CHILD_CARE = _P["cpi_child_care"]
CPI_EXCLUDED_SUBGROUP = _P["cpi_excluded_subgroup"]

# Windows: pre [pre_start, t1), on [t1, t2), off [t2, end]
QUARTERLY = stagger.Windows(*map(pd.Timestamp, _P["quarterly_windows"]))  # quarter starts: Feb 2009 .. May 2013 surveys
MONTHLY = stagger.Windows(*map(pd.Timestamp, _P["monthly_windows"]))
FAKE_YEARS = range(*_P["fake_years"])  # shifts back in whole years; windows must end before January 2012


def quarter(t: pd.Timestamp) -> int:
    return (t.month - 1) // 3


def back(years: int):
    return lambda t: t - pd.DateOffset(years=years)


# --- panels (unit, time, y) ------------------------------------------------------------------------


def lfs(measure: str = "hours_actual") -> pd.DataFrame:
    """Group x state values ('000), quarterly, wide: index (group, period), columns states."""
    lf = pd.read_parquet(PROCESSED / "abs_lfs" / "industry_state_quarter.parquet")
    lf = lf[(lf["measure"] == measure) & (lf["geo_level"] == "STE") & (lf["industry_level"] == "group")]
    return lf.pivot_table(index=["industry_code", "period"], columns="geo_code", values="value", fill_value=0)


def lfs_panel(w: pd.DataFrame, group: str) -> pd.DataFrame:
    g = w.loc[group]
    y = pd.DataFrame({LATE: g[LATE], OTHERS: g[EARLY].sum(axis=1)})
    y = 100 * np.log(y.where(y > 0))
    return y.stack().rename("y").reset_index().rename(columns={"period": "time", "level_1": "unit", "geo_code": "unit"})


def lfs_placebos(w: pd.DataFrame) -> list[str]:
    emp = lfs("employed")
    wa = emp.xs(LATE, axis=1).unstack("industry_code").loc["2009-01-01":"2011-10-01"].mean()
    keep = []
    for g, v in wa.items():
        div = anzsic.division(g)
        if g != CHILDCARE_GROUP and div not in EXCLUDED_DIVISIONS and LFS_SIZE[0] <= v <= LFS_SIZE[1]:
            keep.append(g)
    return sorted(keep)


def abn_counts(measure: str = "abn_cancellations") -> pd.DataFrame:
    """Named-business ABN counts (cancellations, or survivors by start month) by inferred industry,
    state and month."""
    f = pd.read_parquet(PROCESSED / "abr_abn" / "flows_month.parquet")
    f = f[(f["measure"] == measure) & (f["geo_level"] == "STE") & (f["industry_scheme"] == "ANZSIC06-inferred")]
    return f.pivot_table(index=["industry_code", "period"], columns="geo_code", values="value", fill_value=0)


def _division(code: str) -> str | None:
    return code if code.isalpha() else anzsic.division(code)


def abn_panel(c: pd.DataFrame, code: str) -> pd.DataFrame:
    """Share (%) of `code` in named cancellations of `code` plus all industries outside P and Q."""
    codes = c.index.get_level_values("industry_code").unique()
    comp = [k for k in codes if k != code and _division(k) not in EXCLUDED_DIVISIONS]
    num = c.loc[code]
    den = num + c.loc[comp].groupby("period").sum()
    num = num.reindex(den.index, fill_value=0)
    share = pd.DataFrame(
        {
            LATE: 100 * num[LATE] / den[LATE],
            OTHERS: 100 * num[EARLY].sum(axis=1) / den[EARLY].sum(axis=1),
        }
    )
    return share.stack().rename("y").reset_index().rename(columns={"period": "time", "level_1": "unit"})


def abn_placebos(c: pd.DataFrame) -> list[str]:
    wa = c[LATE].unstack("industry_code").loc["2009-01-01":"2011-12-01"].sum() / 3
    return sorted(
        k
        for k, v in wa.items()
        if k != CHILDCARE_CLASS and _division(k) not in EXCLUDED_DIVISIONS and ABN_SIZE[0] <= v <= ABN_SIZE[1]
    )


def cpi() -> pd.DataFrame:
    """100 x log(class / All groups) by state capital and quarter: index (class, period), columns states."""
    from alicia import cpi as cpi_codes
    from alicia.outcomes.abs_series import CITY_STATE, fetch_cpi

    codes = ["10001", *[c["code"] for c in cpi_codes.classes()]]
    raw = fetch_cpi(codes, start="1995-Q1", end="2015-Q4")
    raw["state"] = raw["city"].map(CITY_STATE)
    raw["period"] = pd.PeriodIndex(raw["period"].str.replace("-", ""), freq="Q").to_timestamp()
    w = raw.pivot_table(index=["index_code", "period"], columns="state", values="value")
    allg = w.loc["10001"]
    rel = 100 * np.log(w.div(allg, level="period"))
    return rel.drop(index="10001", level="index_code")


def cpi_panel(rel: pd.DataFrame, code: str) -> pd.DataFrame:
    r = rel.loc[code]
    y = pd.DataFrame({LATE: r[LATE], OTHERS: r[EARLY].mean(axis=1)}).dropna()
    return y.stack().rename("y").reset_index().rename(columns={"period": "time", "level_1": "unit"})


def cpi_placebos() -> list[str]:
    from alicia import cpi as cpi_codes

    return [
        c["code"] for c in cpi_codes.classes() if c["code"] != CPI_CHILD_CARE and c["subgroup"] != CPI_EXCLUDED_SUBGROUP
    ]


# --- estimation --------------------------------------------------------------------------------------


def hide(df: pd.DataFrame, t1) -> pd.DataFrame:
    """Blinding: WA's values from the first treated period on are set to missing."""
    out = df.copy()
    out.loc[(out["unit"] == LATE) & (out["time"] >= t1), "y"] = np.nan
    return out


def estimate(df: pd.DataFrame, windows: stagger.Windows, season=quarter, trend: bool = False) -> dict[str, float]:
    return stagger.estimates(df, LATE, [OTHERS], windows, season, trend)


def null(panels: dict[str, pd.DataFrame], childcare: pd.DataFrame, windows, first_data, season=quarter, trend=False):
    """No-effect estimates by estimand: placebo industries at the real dates, and childcare at fake
    dates whose whole window ends before January 2012 and starts after the data begin."""
    rows = []
    for name, df in panels.items():
        rows.append({"source": f"placebo {name}", **estimate(df, windows, season, trend)})
    for k in FAKE_YEARS:
        w = windows.shifted(back(k))
        if w.end >= NQF or w.pre_start < first_data:
            continue
        rows.append({"source": f"childcare -{k}y", **estimate(childcare, w, season, trend)})
    return pd.DataFrame(rows)


def path(df: pd.DataFrame, windows, season=quarter, trend: bool = False) -> pd.Series:
    return stagger.event_path(df, LATE, [OTHERS], windows, season, trend)
