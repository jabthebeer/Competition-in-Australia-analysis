"""Difference-in-differences for several treated units, with staggered adoption handled by stacking.

Each *cohort* is a set of units that adopted a change at the same time. A cohort is compared only
with units that were not treated during its window (its "clean controls"), so no already-treated
unit is ever used as a comparison (the problem with two-way fixed effects under staggered
timing). The overall estimate averages the cohort estimates, weighted by the number of treated
units. A single treated unit, or several adopting together, is the one-cohort case.

Panels are long DataFrames with columns unit, time, y (as in ``did.py``).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Cohort:
    treated: tuple[str, ...]
    first_post: int  # first exposed period
    last_post: int  # last period used (before any control is treated, or the window end)
    controls: tuple[str, ...]

    @property
    def units(self) -> tuple[str, ...]:
        return self.treated + self.controls


def _fit(d: pd.DataFrame, cols: list[str]) -> np.ndarray:
    units = pd.get_dummies(d["unit"], prefix="u", drop_first=True, dtype=float)
    times = pd.get_dummies(d["time"], prefix="t", drop_first=True, dtype=float)
    X = np.column_stack([np.ones(len(d)), d[cols].to_numpy(float), units.to_numpy(), times.to_numpy()])
    beta, *_ = np.linalg.lstsq(X, d["y"].to_numpy(float), rcond=None)
    return beta[1 : 1 + len(cols)]


def did(df: pd.DataFrame, treated: Iterable[str], first_post) -> float:
    """y = a_unit + b_time + delta * 1[unit treated & time >= first_post]; NaN rows dropped."""
    treated = set(treated)
    d = df.dropna(subset=["y"]).copy()
    d["D"] = (d["unit"].isin(treated) & (d["time"] >= first_post)).astype(float)
    if d["D"].sum() == 0 or d.loc[~d["unit"].isin(treated)].empty:
        return float("nan")
    return float(_fit(d, ["D"])[0])


def event(df: pd.DataFrame, treated: Iterable[str], first_post: int, reference: int = -1) -> pd.Series:
    """Coefficients on 1[unit treated & time - first_post == k] for each k other than the reference."""
    treated = set(treated)
    d = df.dropna(subset=["y"]).copy()
    d["k"] = d["time"] - first_post
    ks = sorted(set(d.loc[d["unit"].isin(treated), "k"]) - {reference})
    cols = []
    for k in ks:
        name = f"k{k}"
        d[name] = (d["unit"].isin(treated) & (d["k"] == k)).astype(float)
        cols.append(name)
    if not cols:
        return pd.Series(dtype=float)
    return pd.Series(_fit(d, cols), index=ks, name="coef")


def cohort_panel(df: pd.DataFrame, c: Cohort, start) -> pd.DataFrame:
    return df[df["unit"].isin(c.units) & (df["time"] >= start) & (df["time"] <= c.last_post)]


def stacked(df: pd.DataFrame, cohorts: Iterable[Cohort], start) -> float:
    """Average of cohort estimates, weighted by the number of treated units; NaN cohorts skipped."""
    num = den = 0.0
    for c in cohorts:
        est = did(cohort_panel(df, c, start), c.treated, c.first_post)
        if not np.isnan(est):
            num += est * len(c.treated)
            den += len(c.treated)
    return num / den if den else float("nan")


def stacked_event(df: pd.DataFrame, cohorts: Iterable[Cohort], start, reference: int = -1) -> pd.Series:
    """Event-time coefficients averaged across cohorts (weighted by treated units) where each k exists."""
    num: dict[int, float] = {}
    den: dict[int, float] = {}
    for c in cohorts:
        es = event(cohort_panel(df, c, start), c.treated, c.first_post, reference)
        for k, v in es.items():
            if not np.isnan(v):
                num[k] = num.get(k, 0.0) + v * len(c.treated)
                den[k] = den.get(k, 0.0) + len(c.treated)
    return pd.Series({k: num[k] / den[k] for k in sorted(num)}, name="coef", dtype=float)


def blind_cohorts(df: pd.DataFrame, cohorts: Iterable[Cohort]) -> pd.DataFrame:
    """Hide every treated unit's outcomes from its first exposed period on."""
    out = df.copy()
    for c in cohorts:
        out.loc[out["unit"].isin(c.treated) & (out["time"] >= c.first_post), "y"] = np.nan
    return out
