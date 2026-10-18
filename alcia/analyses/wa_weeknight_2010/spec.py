"""Perth 9pm weeknight trading (1 Nov 2010): re-evaluation with the expanded data pipeline.

Shared by the blinded design review (design_review.py) and the registered estimation (estimate.py),
so both read exactly the same panels and estimators. The plan is docs/pap_wa_weeknight_2010.md.

Three designs, each a difference-in-differences with one treated unit:
  A  retail turnover, monthly (ABS Retail Trade, seasonally adjusted): turnover of the general
     retail subgroups (supermarkets and grocery, clothing, department stores), WA vs comparison
     states, state and month fixed effects;
  B  hours actually worked, quarterly (ABS Labour Force EQ06): the same groups, WA vs NSW, Victoria
     and Queensland;
  C  retail businesses by place (CABEE businesses by division x SA2, 30 June 2009-2012): metropolitan
     Perth vs the rest of WA, retail relative to other industries, against the same capital-city vs
     rest-of-state contrast in comparison states.

Inference: one treated state, so a "no-effect" distribution comes from the same estimator applied
where there was no reform. A and B: every unit at fake event dates (from 1995) whose windows end
before the reform, plus each comparison state at the true date. C: every other industry division
in every state, plus retail in each comparison state, where the cell has at least 1,000 businesses
in both the capital and the rest of the state.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from alcia import anzsic
from alcia.evaluate.did import event_study, twfe
from alcia.pipeline.store import PROCESSED

TREATED = "WA"
CONTROLS = ["NSW", "VIC", "QLD", "TAS", "ACT", "NT"]  # SA excluded: Adelaide CBD trading change in Apr 2012
LARGE_STATES = ["NSW", "VIC", "QLD"]  # B: comparison states whose LFS group estimates are reliable
GEO_UNITS = ["WA", "NSW", "VIC", "QLD", "TAS", "NT"]  # C: ACT has no rest-of-territory area
REFORM = pd.Timestamp("2010-11-01")
SUNDAY_TRADING = pd.Timestamp("2012-08-26")  # next step of the reform: post-periods stop before it
FAKE_FROM = pd.Timestamp("1995-01-01")  # fake event dates from here (A, B)

# Design A: Retail Trade industries (panel codes; see alcia.pipeline.concord)
A_TREATED = ["RT01", "4251", "4260"]  # supermarkets and grocery stores, clothing, department stores
A_FOOD = ["RT14", "4512"]  # cafes, restaurants and catering; takeaway food
A_OTHER = ["RT03", "RT04", "RT05", "RT06", "RT08", "RT11", "RT13", "4123", "4244", "4271"]  # rest of retail
A_SHARE = ("RT01", "RT03")  # supermarkets vs other specialised food retailing (butchers, bakers, ...)
# Design B: Labour Force ANZSIC groups (industry of main job)
B_TREATED = ["411", "425", "426"]  # supermarket and grocery; clothing, footwear, accessories; department stores
B_FOOD = ["451"]  # cafes, restaurants and takeaway food services
# Design C: CABEE divisions and areas
C_RETAIL = "G"
C_EXCLUDED = {"G", "H"}  # retail, and accommodation and food services (evening trade may move with it)
PERTH_SA4 = ["503", "504", "505", "506", "507"]  # Perth - Inner, North East, North West, South East, South West
MANDURAH_SA4 = "502"  # in Greater Perth but outside the trading-hours metropolitan area: excluded (main)
WA_OUTBACK_SA4 = ["508", "510", "511"]  # 2011 code 508 (WA - Outback) split into 510 and 511 in 2016
C_FLOOR = 1000  # placebo cells need this many businesses in both the capital and the rest (June 2010)
SMALL = ["non-employing", "1-4 employees", "5-19 employees"]
LARGER = ["20-199 employees", "200+ employees"]


@dataclass(frozen=True)
class Design:
    """A window around an event: `pre` periods, then `gap` excluded periods, then `post` periods."""

    key: str
    event: pd.Timestamp  # first post period
    pre: int
    gap: int
    post: int
    block: int = 1  # periods per event-study bin (A: 3 months)

    def window(self, times: list, event=None) -> tuple[list, list]:
        """(estimation times, post times) for an event (default: the real one)."""
        event = self.event if event is None else event
        i = times.index(event)
        lo, hi = i - self.gap - self.pre, i + self.post
        if lo < 0 or hi > len(times):
            raise ValueError("window outside the data")
        return times[lo : i - self.gap] + times[i:hi], times[i:hi]

    def fake_events(self, times: list, since=FAKE_FROM) -> list:
        """Events from `since` whose whole window lies before the real window's excluded periods."""
        last_pre = times.index(self.event) - self.gap - 1
        return [
            times[i]
            for i in range(self.gap + self.pre, len(times))
            if i + self.post - 1 <= last_pre and times[i] >= since
        ]

    def hidden_from(self, times: list):
        """First period hidden from the design review: the first excluded (or post) period."""
        return times[times.index(self.event) - self.gap]


A = Design("A", REFORM, pre=24, gap=4, post=21, block=3)  # Jul 2008-Jun 2010 | Jul-Oct 2010 | Nov 2010-Jul 2012
B = Design("B", pd.Timestamp("2010-10-01"), pre=24, gap=1, post=7)  # Aug 2004-May 2010 | Aug 2010 | Nov 2010-May 2012
C = Design("C", pd.Timestamp("2011-06-30"), pre=2, gap=0, post=2)  # Jun 2009, Jun 2010 | Jun 2011, Jun 2012


def _log(x: pd.Series) -> pd.Series:
    return 100 * np.log(x.where(x > 0))


def _frame(y: pd.Series) -> pd.DataFrame:
    return y.dropna().rename("y").reset_index().rename(columns={"geo_code": "unit", "period": "time"})


# --- panels: columns unit, time, y --------------------------------------------------------------


def retail_wide() -> pd.DataFrame:
    r = pd.read_parquet(PROCESSED / "abs_retail" / "turnover_state.parquet")
    r = r[(r["measure"] == "turnover") & (r["adjustment"] == "seasonally adjusted") & (r["geo_level"] == "STE")]
    return r.pivot_table(index=["geo_code", "period"], columns="industry_code", values="value")


def panel_a(num: list[str] = A_TREATED, den: list[str] | None = None) -> pd.DataFrame:
    """100 x log turnover of `num` (minus 100 x log turnover of `den`)."""
    w = retail_wide()
    w = w[w.index.get_level_values(0).isin([TREATED, *CONTROLS])]
    y = _log(w[num].sum(axis=1, min_count=len(num)))
    if den:
        y = y - _log(w[den].sum(axis=1, min_count=len(den)))
    return _frame(y)


def units_a(df: pd.DataFrame) -> list[str]:
    """Treated state plus comparison states with a complete series from 1992 to the end of the window."""
    times = sorted(df["time"].unique())
    need = [t for t in times if pd.Timestamp("1992-01-01") <= t <= A.window(times)[0][-1]]
    have = df[df["time"].isin(need)].groupby("unit")["y"].count()
    return [u for u in [TREATED, *CONTROLS] if have.get(u, 0) == len(need)]


def panel_b(measure: str = "hours_actual", num: list[str] = B_TREATED, den: list[str] | None = None):
    lf = pd.read_parquet(PROCESSED / "abs_lfs" / "industry_state_quarter.parquet")
    lf = lf[
        (lf["measure"] == measure)
        & (lf["geo_level"] == "STE")
        & (lf["industry_level"] == "group")
        & lf["geo_code"].isin([TREATED, *LARGE_STATES])
    ]
    w = lf.pivot_table(index=["geo_code", "period"], columns="industry_code", values="value", fill_value=0)
    y = _log(w[num].sum(axis=1))
    if den:
        y = y - _log(w[den].sum(axis=1))
    return _frame(y)


def sa4_areas(include_mandurah: bool = False) -> pd.Series:
    """SA4 code -> "<state>|cap" or "<state>|rest", from the ASGS 2021 concordance: each SA4 lies
    inside one GCCSA, found as the GCCSA sharing most postcode population. 2011 code 508 (WA - Outback)
    is added as rest of WA; ACT and unknown areas are left out."""
    from alcia.pipeline import geo

    c = geo.concordance()
    s4 = c[c["level"] == "SA4"][["postcode", "code", "ratio"]].rename(columns={"code": "sa4", "ratio": "r4"})
    gc = c[c["level"] == "GCCSA"][["postcode", "code", "ratio"]].rename(columns={"code": "gccsa", "ratio": "rg"})
    m = s4.merge(gc, on="postcode")
    m["w"] = m["r4"] * m["rg"]
    best = m.groupby(["sa4", "gccsa"])["w"].sum().reset_index().sort_values("w").drop_duplicates("sa4", keep="last")
    best = best[best["gccsa"].str.match(r"^[1-7][GR]")]
    states = {"1": "NSW", "2": "VIC", "3": "QLD", "4": "SA", "5": "WA", "6": "TAS", "7": "NT"}
    area = best.set_index("sa4")["gccsa"].map(lambda g: f"{states[g[0]]}|{'cap' if g[1] == 'G' else 'rest'}")
    area["508"] = "WA|rest"
    return area if include_mandurah else area.drop(MANDURAH_SA4)


def cabee_areas(bands: list[str] | None = None, include_mandurah: bool = False, drop_outback: bool = False):
    """Businesses by area x division x 30 June, chained across the two releases at June 2011:
    June 2009-2011 from the Jun 2007-Jun 2011 release, later years moved by their change within the
    Jun 2009-Jun 2013 release. Returns log counts (x100), index (state, part, division), columns dates."""
    area = sa4_areas(include_mandurah)
    if drop_outback:
        area = area.drop([c for c in WA_OUTBACK_SA4 if c in area.index])
    out = {}
    for rel in ("2007_2011", "2009_2013"):
        p = pd.read_parquet(PROCESSED / "abs_cabee_local" / f"division_sa2_2011_release_{rel}.parquet")
        p = p[p["breakdown"].isin(bands)] if bands else p[p["breakdown"] == ""]
        p = p.assign(area=p["geo_code"].str[:3].map(area)).dropna(subset=["area"])
        out[rel] = p.groupby(["area", "industry_code", "period"])["value"].sum().unstack("period")
    la, lb = np.log(out["2007_2011"]), np.log(out["2009_2013"])
    j = pd.Timestamp("2011-06-30")
    chained = la.copy()
    for t in [t for t in lb.columns if t > j]:
        chained[t] = la[j] + (lb[t] - lb[j])
    chained = 100 * chained
    idx = chained.index.get_level_values("area").str.split("|", expand=True)
    chained.index = pd.MultiIndex.from_arrays(
        [idx.get_level_values(0), idx.get_level_values(1), chained.index.get_level_values("industry_code")],
        names=["state", "part", "division"],
    )
    return chained


def panel_c(division: str = C_RETAIL, logs: pd.DataFrame | None = None) -> pd.DataFrame:
    """y = (capital minus rest-of-state gap in log businesses of `division`) minus the same gap for
    all other divisions together (leaving out retail, accommodation and food, and `division`)."""
    logs = cabee_areas() if logs is None else logs
    counts = np.exp(logs / 100)
    others = [d for d in counts.index.get_level_values("division").unique() if d not in C_EXCLUDED | {division}]
    rows = []
    for st in GEO_UNITS:
        try:
            cap, rest = counts.loc[(st, "cap")], counts.loc[(st, "rest")]
        except KeyError:
            continue
        gap_x = 100 * (np.log(cap.loc[division]) - np.log(rest.loc[division]))
        gap_o = 100 * (np.log(cap.loc[others].sum()) - np.log(rest.loc[others].sum()))
        for t, v in (gap_x - gap_o).items():
            rows.append({"unit": st, "time": t, "y": float(v)})
    d = pd.DataFrame(rows)
    return d[d["time"] <= pd.Timestamp("2012-06-30")]


# --- estimation helpers ----------------------------------------------------------------------------


def restrict(df: pd.DataFrame, units: list[str], times: list) -> pd.DataFrame:
    return df[df["unit"].isin(units) & df["time"].isin(times)].copy()


def detrend(df: pd.DataFrame, first_post) -> pd.DataFrame:
    """Remove each unit's linear trend fitted on its pre-period (robustness check)."""
    out = []
    times = sorted(df["time"].unique())
    pos = {t: i for i, t in enumerate(times)}
    for _, g in df.groupby("unit"):
        g = g.copy()
        x = g["time"].map(pos).astype(float)
        pre = (g["time"] < first_post) & g["y"].notna()
        if pre.sum() >= 3:
            b, a = np.polyfit(x[pre], g.loc[pre, "y"], 1)
            g["y"] = g["y"] - (a + b * x)
        out.append(g)
    return pd.concat(out, ignore_index=True)


def estimate(df: pd.DataFrame, design: Design, units: list[str], treated: str = TREATED, trend: bool = False):
    times = sorted(df["time"].unique())
    win, post = design.window(times)
    d = restrict(df, units, win)
    if trend:
        d = detrend(d, post[0])
    return twfe(d, treated, post[0])


def null_dates(df: pd.DataFrame, design: Design, units: list[str], trend: bool = False, since=FAKE_FROM):
    """No-effect estimates for A and B: every unit at every fake event date, and every comparison
    state at the real date (the treated state left out)."""
    times = sorted(df["time"].unique())
    rows = []
    for e in design.fake_events(times, since):
        win, post = design.window(times, e)
        d = restrict(df, units, win)
        if trend:
            d = detrend(d, post[0])
        for u in units:
            if d.loc[d["unit"] == u, "y"].notna().sum() == len(win):
                rows.append({"unit": u, "event": e, "estimate": twfe(d, u, post[0]), "kind": "fake date"})
    win, post = design.window(times)
    d = restrict(df[df["unit"] != TREATED], units, win)
    if trend:
        d = detrend(d, post[0])
    for u in units:
        if u != TREATED:
            rows.append({"unit": u, "event": design.event, "estimate": twfe(d, u, post[0]), "kind": "comparison state"})
    return pd.DataFrame(rows)


def big_enough(logs: pd.DataFrame, floor: int = C_FLOOR) -> set[tuple[str, str]]:
    """(state, division) cells with at least `floor` businesses in both parts at 30 June 2010."""
    c = np.exp(logs[pd.Timestamp("2010-06-30")] / 100).unstack("part")
    return {(s, d) for (s, d), r in c.iterrows() if min(r["cap"], r["rest"]) >= floor}


def null_industries(logs: pd.DataFrame, trend: bool = False, floor: int = C_FLOOR) -> pd.DataFrame:
    """No-effect estimates for C: every other division in every state, and retail in each comparison
    state (WA left out of that pool), keeping cells of a size like WA retail (`floor`)."""
    rows = []
    keep = big_enough(logs, floor)
    divisions = [d for d in logs.index.get_level_values("division").unique() if d not in C_EXCLUDED]
    for div in [*divisions, C_RETAIL]:
        df = panel_c(div, logs)
        if div == C_RETAIL:
            df = df[df["unit"] != TREATED]
        units = sorted(df["unit"].unique())
        for u in units:
            if (u, div) in keep:
                rows.append({"unit": u, "division": div, "estimate": estimate(df, C, units, u, trend)})
    return pd.DataFrame(rows)


def summarise_null(null: pd.Series) -> dict:
    q = null.quantile([0.05, 0.5, 0.95])
    return {
        "n": int(len(null)),
        "sd": round(float(null.std(ddof=1)), 3),
        "mde_80": round(float(2.801585 * null.std(ddof=1)), 3),
        "q05": round(float(q[0.05]), 3),
        "median": round(float(q[0.5]), 3),
        "q95": round(float(q[0.95]), 3),
    }


def p_value(null: pd.Series, est: float) -> float:
    return float((1 + (null.abs() >= abs(est)).sum()) / (len(null) + 1))


def interval(null: pd.Series, est: float, level: float = 0.9) -> tuple[float, float]:
    lo, hi = np.quantile(null, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(est - hi), float(est - lo)


def binned(df: pd.DataFrame, design: Design, event=None) -> pd.DataFrame:
    """Window data with time replaced by event-time bins of `design.block` periods (k = 0 is the
    first post bin, k = -1 the last pre bin); y averaged within bins."""
    times = sorted(df["time"].unique())
    event = design.event if event is None else event
    win, post = design.window(times, event)
    pre = [t for t in win if t < event]
    k = {t: (post.index(t) // design.block) for t in post}
    k.update({t: -1 - ((len(pre) - 1 - pre.index(t)) // design.block) for t in pre})
    d = df[df["time"].isin(win)].copy()
    d["time"] = d["time"].map(k)
    return d.groupby(["unit", "time"], as_index=False)["y"].mean()


def event_coefficients(df: pd.DataFrame, design: Design, units: list[str], treated: str = TREATED, event=None):
    d = binned(df[df["unit"].isin(units)], design, event)
    return event_study(d, treated, 0, reference=-1)


def event_band(df: pd.DataFrame, design: Design, units: list[str]) -> pd.DataFrame:
    """5th and 95th percentiles of event-study coefficients by k across fake dates and units."""
    times = sorted(df["time"].unique())
    rows = []
    for e in design.fake_events(times):
        win, _ = design.window(times, e)
        d = restrict(df, units, win)
        for u in units:
            if d.loc[d["unit"] == u, "y"].notna().sum() == len(win):
                c = event_coefficients(df, design, units, u, e)
                rows += [{"k": k, "coef": v} for k, v in c.items()]
    b = pd.DataFrame(rows).groupby("k")["coef"].quantile([0.05, 0.95]).unstack()
    return b.rename(columns={0.05: "low", 0.95: "high"})


def event_band_industries(logs: pd.DataFrame, floor: int = C_FLOOR) -> pd.DataFrame:
    """C: percentiles of event-study coefficients across other divisions and states (size floor)."""
    rows = []
    keep = big_enough(logs, floor)
    for div in [d for d in logs.index.get_level_values("division").unique() if d not in C_EXCLUDED]:
        df = panel_c(div, logs)
        units = sorted(df["unit"].unique())
        for u in [u for u in units if (u, div) in keep]:
            c = event_coefficients(df, C, units, u)
            rows += [{"k": k, "coef": v} for k, v in c.items()]
    b = pd.DataFrame(rows).groupby("k")["coef"].quantile([0.05, 0.95]).unstack()
    return b.rename(columns={0.05: "low", 0.95: "high"})


def abn_named_exit_counts() -> pd.DataFrame:
    """Why the ABN design was dropped: retail-named exits a year by area, 2005-2009 average."""
    s = pd.read_parquet(PROCESSED / "abr_abn" / "cancellations_sa4_month.parquet")
    s = s[s["industry_scheme"] == "ANZSIC06-inferred"]
    area = sa4_areas()
    s = s[s["geo_code"].isin(area.index) & s["period"].dt.year.between(2005, 2009)]
    div = s["industry_code"].map(lambda c: c if c.isalpha() else anzsic.division(c))
    s = s.assign(area=s["geo_code"].map(area), retail=(div == "G"))
    return (s.groupby(["area", "retail"])["value"].sum() / 5).unstack("retail").round(1)
