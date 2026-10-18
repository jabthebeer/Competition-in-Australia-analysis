"""A rule that starts late in one jurisdiction: the "on-off" difference-in-differences.

When a rule starts in most jurisdictions at T1 and in one late jurisdiction at T2 > T1 (the
National Quality Framework began in January 2012 everywhere but WA, which followed in August
2012), the late jurisdiction is a clean, not-yet-treated comparison between T1 and T2. Write the
gap D_t = y(late) - mean of y(early). If the rule's effect is immediate and lasting, the gap
moves by minus the effect at T1 ("on") and back at T2 ("off"), when the late jurisdiction catches
up. Three estimates come from the same gap:

- ``early``: effect on the early jurisdictions in [T1, T2), against the late one (a clean
  comparison: no already-treated unit is used as a control);
- ``late``: change in the late jurisdiction against the early ones at T2. This assumes the early
  jurisdictions' effect stayed the same after T2 (no build-up), since they are its comparison;
- ``pooled``: one effect for both, from the gap opening and closing (efficient if effects are
  immediate, lasting and equal; the gap after T2 is then back at its pre-T1 level).

Seasonal differences between the late and early jurisdictions are removed with the gap's
pre-period mean for each season. Inference is by placebos (other industries over the same
windows, the same industry at fake dates); see ``Null``.

Panels are long DataFrames with columns unit, time, y (time sortable; seasons supplied as a
function of time).
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Windows:
    """Periods used: pre [pre_start, t1), on [t1, t2), off [t2, end]; anything else is ignored."""

    pre_start: object
    t1: object
    t2: object
    end: object

    def part(self, t) -> str | None:
        if self.pre_start <= t < self.t1:
            return "pre"
        if self.t1 <= t < self.t2:
            return "on"
        if self.t2 <= t <= self.end:
            return "off"
        return None

    def shifted(self, shift: Callable[[object], object]) -> Windows:
        return Windows(shift(self.pre_start), shift(self.t1), shift(self.t2), shift(self.end))


def gap(df: pd.DataFrame, late: Hashable, early: Iterable[Hashable]) -> pd.Series:
    """D_t = y(late) - mean over early units of y, for periods where every unit is observed."""
    early = list(early)
    w = df[df["unit"].isin([late, *early])].pivot_table(index="time", columns="unit", values="y")
    w = w.dropna(subset=[late, *early])
    return (w[late] - w[early].mean(axis=1)).rename("gap")


def deseason(
    d: pd.Series, windows: Windows, season: Callable[[object], Hashable] | None, trend: bool = False
) -> pd.Series:
    """Subtract the pre-period mean of the gap for each season (or the overall pre mean); with
    `trend`, also remove a linear trend in the gap fitted on the pre-period (robustness check)."""
    pre = d[[windows.part(t) == "pre" for t in d.index]]
    if season is None:
        out = d - pre.mean()
    else:
        means = pre.groupby([season(t) for t in pre.index]).mean()
        out = d - np.array([means.get(season(t), np.nan) for t in d.index])
    if trend:
        pos = pd.Series(np.arange(len(out), dtype=float), index=out.index)
        pre_mask = np.array([windows.part(t) == "pre" for t in out.index]) & out.notna().to_numpy()
        slope, icept = np.polyfit(pos[pre_mask], out[pre_mask], 1)
        out = out - (icept + slope * pos)
    return out


def estimates(
    df: pd.DataFrame,
    late: Hashable,
    early: Iterable[Hashable],
    windows: Windows,
    season: Callable[[object], Hashable] | None = None,
    trend: bool = False,
) -> dict[str, float]:
    """early, late and pooled effects (in units of y); NaN if a window has no data."""
    d = gap(df, late, early)
    d = d[[windows.part(t) is not None for t in d.index]]
    d = deseason(d, windows, season, trend).dropna()
    part = pd.Series([windows.part(t) for t in d.index], index=d.index)
    means = d.groupby(part).mean()
    pre, on, off = (means.get(k, np.nan) for k in ("pre", "on", "off"))
    # pooled: D_t = c - effect * 1[on], fitted on pre, on and off together
    base = d[part.isin(["pre", "off"])]
    pooled = base.mean() - on if len(base) and not np.isnan(on) else np.nan
    return {"early": float(pre - on), "late": float(off - on), "pooled": float(pooled), "off_vs_pre": float(off - pre)}


def event_path(
    df: pd.DataFrame,
    late: Hashable,
    early: Iterable[Hashable],
    windows: Windows,
    season: Callable[[object], Hashable] | None = None,
    trend: bool = False,
) -> pd.Series:
    """The deseasonalised gap by period, relative to its pre-period mean (0 before T1 on average)."""
    d = gap(df, late, early)
    d = d[[windows.part(t) is not None for t in d.index]]
    return deseason(d, windows, season, trend)


@dataclass(frozen=True)
class Null:
    """Estimates where there was no reform, and what they imply for one real estimate."""

    estimates: pd.Series

    @property
    def sd(self) -> float:
        return float(self.estimates.std(ddof=1))

    @property
    def mde(self) -> float:
        """Smallest effect detectable with 80% power at 5% (two-sided), from the placebo spread."""
        return 2.801585 * self.sd

    def p_value(self, est: float) -> float:
        e = self.estimates.dropna()
        return float((1 + (e.abs() >= abs(est)).sum()) / (len(e) + 1))

    def interval(self, est: float, level: float = 0.9) -> tuple[float, float]:
        lo, hi = np.quantile(self.estimates.dropna(), [(1 - level) / 2, 1 - (1 - level) / 2])
        return float(est - hi), float(est - lo)

    def summary(self) -> dict:
        e = self.estimates.dropna()
        q = e.quantile([0.05, 0.5, 0.95])
        return {
            "n": int(len(e)),
            "sd": round(self.sd, 3),
            "mde_80": round(self.mde, 3),
            "q05": round(float(q[0.05]), 3),
            "median": round(float(q[0.5]), 3),
            "q95": round(float(q[0.95]), 3),
        }
