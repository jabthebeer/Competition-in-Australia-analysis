"""Difference-in-differences for one treated unit, with blinding, placebo inference and power.

Designed for the case where a single jurisdiction changes a rule at one date (design D3 in
docs/impact_evaluation_design.md), so two-way fixed effects carry no negative-weighting
problem. With one treated unit, conventional standard errors are not credible; inference uses
the distribution of the same estimator applied to untreated units (placebo-in-space, as in
Abadie et al. and Conley & Taber 2011) or to untreated industry groups.

Panels are long DataFrames with columns: unit, time, y (and optionally weight).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

Z_80_POWER_5PC = 1.959964 + 0.841621  # two-sided 5% test, 80% power (normal approximation)


def blind(
    df: pd.DataFrame, treated: str, first_post, unit: str = "unit", time: str = "time", y: str = "y"
) -> pd.DataFrame:
    """Hide the treated unit's outcomes from the first exposed period on (set to NaN)."""
    out = df.copy()
    out.loc[(out[unit] == treated) & (out[time] >= first_post), y] = np.nan
    return out


def _design(df: pd.DataFrame, regressors: list[str]) -> tuple[np.ndarray, np.ndarray]:
    units = pd.get_dummies(df["unit"], prefix="u", drop_first=True, dtype=float)
    times = pd.get_dummies(df["time"], prefix="t", drop_first=True, dtype=float)
    X = np.column_stack([np.ones(len(df)), df[regressors].to_numpy(float), units.to_numpy(), times.to_numpy()])
    return X, df["y"].to_numpy(float)


def twfe(df: pd.DataFrame, treated: str, first_post) -> float:
    """y = a_unit + b_time + delta * 1[treated & time >= first_post]; returns delta. NaN rows are dropped."""
    d = df.dropna(subset=["y"]).copy()
    d["D"] = ((d["unit"] == treated) & (d["time"] >= first_post)).astype(float)
    if d["D"].sum() == 0:
        return float("nan")
    X, y = _design(d, ["D"])
    w = np.sqrt(d["weight"].to_numpy(float)) if "weight" in d else np.ones(len(d))
    beta, *_ = np.linalg.lstsq(X * w[:, None], y * w, rcond=None)
    return float(beta[1])


def event_study(df: pd.DataFrame, treated: str, event_time0, reference=-1) -> pd.Series:
    """Coefficients on 1[treated & time - event_time0 == k] for each k != reference."""
    d = df.dropna(subset=["y"]).copy()
    times = sorted(d["time"].unique())
    rel = {t: times.index(t) - times.index(event_time0) if event_time0 in times else None for t in times}
    ks = sorted({rel[t] for t in d.loc[d["unit"] == treated, "time"]} - {reference})
    cols = []
    for k in ks:
        name = f"k{k}"
        d[name] = ((d["unit"] == treated) & (d["time"].map(rel) == k)).astype(float)
        cols.append(name)
    X, y = _design(d, cols)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return pd.Series(beta[1 : 1 + len(cols)], index=ks, name="coef")


@dataclass(frozen=True)
class Placebo:
    estimates: pd.Series  # by placebo unit (or group)

    @property
    def sd(self) -> float:
        return float(self.estimates.std(ddof=1))

    @property
    def mde(self) -> float:
        """Minimum detectable effect at 80% power, 5% two-sided, from the placebo spread."""
        return Z_80_POWER_5PC * self.sd

    @property
    def min_p(self) -> float:
        """Smallest achievable two-sided randomisation p-value: 1 / (placebos + 1)."""
        return 1 / (len(self.estimates) + 1)

    def p_value(self, estimate: float) -> float:
        """Share of placebo estimates at least as large in absolute value (treated unit included)."""
        return float((1 + (self.estimates.abs() >= abs(estimate)).sum()) / (len(self.estimates) + 1))

    def interval(self, estimate: float, level: float = 0.9) -> tuple[float, float]:
        """Conley-Taber style interval: estimate minus the placebo quantiles (needs many placebos)."""
        lo, hi = np.quantile(self.estimates, [(1 - level) / 2, 1 - (1 - level) / 2])
        return float(estimate - hi), float(estimate - lo)


def placebo_in_space(df: pd.DataFrame, treated: str, first_post, exclude_treated: bool = True) -> Placebo:
    """Apply the estimator to each untreated unit as if it were treated, using the other untreated units."""
    pool = df[df["unit"] != treated] if exclude_treated else df
    est = {}
    for u in sorted(pool["unit"].unique()):
        est[u] = twfe(pool, u, first_post)
    return Placebo(pd.Series(est, name="placebo"))


def plant(df: pd.DataFrame, host: str, first_post, effect: float, relative: bool = False) -> pd.DataFrame:
    """Add a known effect to a host unit's post-period outcomes (simulation check; data are not real)."""
    out = df.copy()
    m = (out["unit"] == host) & (out["time"] >= first_post)
    out.loc[m, "y"] = out.loc[m, "y"] * (1 + effect) if relative else out.loc[m, "y"] + effect
    return out


def recovery(df: pd.DataFrame, treated: str, first_post, effects: list[float]) -> pd.DataFrame:
    """For each untreated host unit and planted effect: the estimate and its placebo p-value."""
    pool = df[df["unit"] != treated]
    rows = []
    for host in sorted(pool["unit"].unique()):
        others = pool[pool["unit"] != host]
        placebo = placebo_in_space(others, "__none__", first_post, exclude_treated=False)
        for eff in effects:
            est = twfe(plant(pool, host, first_post, eff), host, first_post)
            rows.append({"host": host, "planted": eff, "estimate": est, "p": placebo.p_value(est)})
    return pd.DataFrame(rows)
