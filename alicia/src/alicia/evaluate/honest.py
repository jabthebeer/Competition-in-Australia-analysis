"""Sensitivity of event-study effects to violations of parallel trends (Rambachan and Roth 2023).

Event-study coefficients beta_k (k = -K..-2 before adoption, the reference period -1 normalised to 0,
and k = 0..H after) are effects plus a bias delta_k from differential trends. Pre-period coefficients
identify delta before adoption; the restrictions below bound how far delta can move afterwards:

- relative magnitudes, Delta^RM(Mbar): each post-period change in delta is at most Mbar times the
  largest change between consecutive pre-periods;
- smoothness, Delta^SD(M): the slope of delta changes by at most M a period (M = 0 allows only a
  linear continuation of the pre-trend).

For a target theta = l'tau (``lvec``; default the average post-period effect) the identified set is an interval,
computed here in closed form for any l. ``breakdown`` gives the smallest Mbar (or M) at which the set
includes zero.

Inference here is approximate: the interval is widened by z x se(l'beta_post), treating pre-period
coefficients as fixed. The conditional and hybrid confidence sets of the paper (R: HonestDiD) are the
reference; use them for anything reported as a finding.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Bounds:
    restriction: str  # "RM" or "SD"
    m: float
    lower: float  # identified set
    upper: float
    ci_lower: float  # approximate confidence interval
    ci_upper: float
    feasible: bool = True  # SD only: False if the pre-period already breaks the smoothness bound


def _split(beta: np.ndarray, k_pre: int):
    beta = np.asarray(beta, float)
    pre = np.r_[beta[:k_pre], 0.0]  # pre-period coefficients plus the reference period (0)
    return pre, beta[k_pre:]


def _l(lvec: np.ndarray | None, h: int) -> np.ndarray:
    return np.full(h, 1.0 / h) if lvec is None else np.asarray(lvec, float)


def _rm_scale(lvec: np.ndarray) -> float:
    """max of l'delta over post paths whose steps are each at most 1 in absolute value."""
    tails = np.cumsum(lvec[::-1])[::-1]  # sum_{t >= k} l_t
    return float(np.abs(tails).sum())


def relative_magnitudes(
    beta: np.ndarray, k_pre: int, mbar: float, lvec: np.ndarray | None = None, se_post: float = 0.0, z: float = 1.645
) -> Bounds:
    """Identified set for theta = l'tau under Delta^RM(mbar). ``beta``: pre coefficients (k = -K..-2,
    oldest first, ``k_pre`` of them) then post coefficients (k = 0..H). ``se_post``: se of l'beta_post."""
    pre, post = _split(beta, k_pre)
    lvec = _l(lvec, len(post))
    step = np.abs(np.diff(pre)).max() if len(pre) > 1 else 0.0
    point = float(lvec @ post)
    half = mbar * step * _rm_scale(lvec)
    return Bounds("RM", mbar, point - half, point + half, point - half - z * se_post, point + half + z * se_post)


def smoothness(
    beta: np.ndarray, k_pre: int, m: float, lvec: np.ndarray | None = None, se_post: float = 0.0, z: float = 1.645
) -> Bounds:
    """Identified set for theta = l'tau under Delta^SD(m): delta continues the last pre-period slope,
    which may change by at most m each period."""
    pre, post = _split(beta, k_pre)
    lvec = _l(lvec, len(post))
    h = len(post)
    slope = pre[-1] - pre[-2] if len(pre) > 1 else 0.0
    second = np.abs(np.diff(pre, 2)) if len(pre) > 2 else np.array([0.0])
    feasible = bool(second.max() <= m + 1e-12)
    # delta_t (t = 0..h-1) = (t + 1) slope + sum_{j <= t} (t - j + 1) c_j with |c_j| <= m.
    t = np.arange(h)
    centre = float(lvec @ ((t + 1) * slope))
    coef = np.array([sum(lvec[tt] * (tt - j + 1) for tt in range(j, h)) for j in range(h)])
    half = m * float(np.abs(coef).sum())
    point = float(lvec @ post)
    lo, hi = point - centre - half, point - centre + half
    return Bounds("SD", m, lo, hi, lo - z * se_post, hi + z * se_post, feasible)


def breakdown(beta: np.ndarray, k_pre: int, restriction: str = "RM", lvec: np.ndarray | None = None) -> float:
    """Smallest Mbar (RM) or M (SD) at which the identified set includes zero (0 if it already does
    with no allowance; inf if no allowance can reach zero)."""
    pre, post = _split(beta, k_pre)
    lvec = _l(lvec, len(post))
    point = float(lvec @ post)
    if restriction == "RM":
        step = np.abs(np.diff(pre)).max() if len(pre) > 1 else 0.0
        scale = step * _rm_scale(lvec)
        return 0.0 if point == 0 else (abs(point) / scale if scale > 0 else float("inf"))
    b0 = smoothness(beta, k_pre, 0.0, lvec)
    centre = b0.lower  # with m = 0 the set is a point
    second = np.abs(np.diff(pre, 2)).max() if len(pre) > 2 else 0.0  # below this the set is empty
    per_m = smoothness(beta, k_pre, 1.0, lvec).upper - centre
    needed = abs(centre) / per_m if per_m > 0 else (0.0 if centre == 0 else float("inf"))
    return float(max(needed, second))
