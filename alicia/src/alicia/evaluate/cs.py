"""Callaway and Sant'Anna (2021) group-time effects, with the doubly robust estimator of Sant'Anna and
Zhao (2020) (forward plan §2.4).

For each adoption cohort g (units first treated in period g) and period t, ATT(g, t) compares the change
in outcome from the base period to t for cohort g with the change for a comparison group: units never
treated, or units not yet treated by t. Post-treatment cells use the period before adoption as the base
("universal" base); pre-treatment cells use the previous period ("varying" base), so they test for
pre-trends period by period.

With covariates (time-invariant, e.g. pre-period levels), each comparison combines an outcome
regression for the comparison group's change and inverse probability weights from a logit of cohort
membership; it is consistent if either model is right. Without covariates it is the plain
difference in mean changes.

Aggregations: ``simple`` (cohort-size weighted mean over post cells), ``dynamic`` (by time since
adoption) and ``group`` (by cohort). Inference: a cluster bootstrap that resamples clusters (valid with
many clusters; with few states use ``panel.placebo_null``).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def _logit(x: np.ndarray, d: np.ndarray, w: np.ndarray, iters: int = 50) -> np.ndarray:
    """Fitted probabilities from a weighted logit by Newton-Raphson."""
    b = np.zeros(x.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(x @ b, -30, 30)))
        g = x.T @ (w * (d - p))
        h = (x * (w * p * (1 - p))[:, None]).T @ x
        step = np.linalg.solve(h + 1e-10 * np.eye(len(b)), g)
        b += step
        if np.abs(step).max() < 1e-10:
            break
    return 1 / (1 + np.exp(-np.clip(x @ b, -30, 30)))


def drdid(
    dy: np.ndarray, d: np.ndarray, x: np.ndarray | None = None, w: np.ndarray | None = None, trim: float = 0.995
) -> float:
    """Doubly robust ATT for panel data (Sant'Anna and Zhao 2020; R: DRDID::drdid_panel): an OLS outcome
    regression for the comparison group's change and a logit propensity score, with normalised weights.
    Comparison units with propensity at or above ``trim`` are dropped."""
    w = np.ones(len(dy)) if w is None else w
    if x is None or x.shape[1] == 0:
        return float(np.average(dy[d == 1], weights=w[d == 1]) - np.average(dy[d == 0], weights=w[d == 0]))
    xx = np.column_stack([np.ones(len(dy)), x])
    c = d == 0
    beta = np.linalg.lstsq(xx[c] * np.sqrt(w[c])[:, None], dy[c] * np.sqrt(w[c]), rcond=None)[0]
    m = xx @ beta
    p = _logit(xx, d.astype(float), w)
    keep = (d == 1) | (p < trim)
    w1 = w * d * keep
    w0 = w * p * (1 - d) / (1 - p) * keep
    return float((w1 * (dy - m)).sum() / w1.sum() - (w0 * (dy - m)).sum() / w0.sum())


@dataclass
class GroupTime:
    table: pd.DataFrame  # g, t, e (= t - g), att, n_treated, n_control, post
    simple: float
    dynamic: pd.Series
    group: pd.Series


def att_gt(
    df: pd.DataFrame,
    y: str,
    unit: str,
    time: str,
    group: str,
    covariates: tuple[str, ...] = (),
    control: str = "never",
    weights: str | None = None,
) -> GroupTime:
    """Group-time effects on a balanced panel. ``group``: first treated period (0 or NaN for never
    treated). ``control``: "never" or "notyet". ``covariates`` must be constant within units."""
    wide = df.pivot(index=unit, columns=time, values=y)
    if wide.isna().any().any():
        raise ValueError("att_gt needs a balanced panel")
    units = df.drop_duplicates(unit).set_index(unit).loc[wide.index]
    g = units[group].fillna(0).to_numpy(float)
    x = units[list(covariates)].to_numpy(float) if covariates else None
    w = units[weights].to_numpy(float) if weights else np.ones(len(units))
    times = list(wide.columns)
    yv = wide.to_numpy(float)
    rows = []
    for gg in sorted(set(g[g > 0])):
        if gg not in times or times.index(gg) == 0:
            continue
        gi = times.index(gg)
        for ti, tt in enumerate(times):
            if ti == 0:
                continue
            base = gi - 1 if tt >= gg else ti - 1
            if control == "never":
                comp = g == 0
            else:
                later = max(tt, times[base])
                comp = (g == 0) | ((g > later) & (g != gg))
            sel = (g == gg) | comp
            if not comp.any():
                continue
            d = (g[sel] == gg).astype(int)
            dy = yv[sel, ti] - yv[sel, base]
            att = drdid(dy, d, x[sel] if x is not None else None, w[sel])
            rows.append(
                {
                    "g": gg,
                    "t": tt,
                    "e": ti - gi,
                    "att": att,
                    "n_treated": int(d.sum()),
                    "n_control": int((1 - d).sum()),
                    "post": tt >= gg,
                }
            )
    table = pd.DataFrame(rows)
    size = pd.Series({gg: w[g == gg].sum() for gg in table["g"].unique()})
    post = table[table["post"]].assign(wg=lambda t: t["g"].map(size))
    simple = float(np.average(post["att"], weights=post["wg"])) if len(post) else float("nan")
    allc = table.assign(wg=table["g"].map(size))
    dynamic = allc.groupby("e").apply(lambda t: np.average(t["att"], weights=t["wg"]), include_groups=False)
    grp = post.groupby("g")["att"].mean()
    return GroupTime(table, simple, dynamic, grp)


def cluster_bootstrap(
    df: pd.DataFrame,
    cluster: str,
    statistic,
    reps: int = 199,
    seed: int = 0,
    unit: str | None = None,
) -> np.ndarray:
    """Re-run ``statistic(frame) -> float`` on cluster resamples (clusters drawn with replacement; the
    cluster and ``unit`` columns are relabelled so a repeated cluster counts as distinct units)."""
    rng = np.random.default_rng(seed)
    ids = df[cluster].unique()
    out = []
    for _ in range(reps):
        pick = rng.choice(ids, size=len(ids), replace=True)
        parts = []
        for k, c in enumerate(pick):
            part = df[df[cluster] == c].assign(**{cluster: f"{c}#{k}"})
            if unit:
                part[unit] = part[unit].astype(str) + f"#{k}"
            parts.append(part)
        try:
            out.append(statistic(pd.concat(parts, ignore_index=True)))
        except (ValueError, np.linalg.LinAlgError):
            continue
    return np.array(out)
