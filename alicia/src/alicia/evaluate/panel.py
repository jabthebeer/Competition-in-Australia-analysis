"""Panel estimators for the regression framework (docs/forward_plan_macro_controls.md, Phase 2).

The unit is a cell (state or region x industry) observed over periods. The default model saturates
the fixed effects that absorb macroeconomic conditions:

    y_sit = a_si + d_it + g_st + b * D_sit + X_sit' c + e_sit

- a_si: the cell's permanent level; d_it: everything common to an industry in a period (national
  industry growth and demand); g_st: everything common to a state in a period (state demand, the
  mining boom, state budgets). What is left to identify b is how treated industries in treated states
  moved relative to the same industry elsewhere and to other industries in the same state.

Contents
- ``absorb``: partial out any number of fixed effects by alternating projections (the method of
  Guimaraes and Portugal 2010; Gaure 2013), with optional weights.
- ``feols``: least squares after absorption, with cluster-robust (CR1) or heteroskedasticity-robust
  standard errors. Matches ``fixest::feols`` with ``ssc(adj = FALSE, cluster.adj = TRUE)`` when
  ``small="cluster"`` (cross-check in ``analysis/crosscheck_panel_estimators.R``).
- ``wild_cluster_bootstrap``: restricted (null imposed) wild cluster bootstrap-t (Cameron, Gelbach and
  Miller 2008; Roodman et al. 2019), Rademacher or Webb (2023) weights. It is unreliable when only one
  or two clusters are treated (MacKinnon and Webb 2017, 2018): use ``placebo_null`` there.
- ``imputation``: the estimator of Borusyak, Jaravel and Spiess (2024). Fixed effects and controls are
  fitted on untreated observations only, counterfactuals imputed for treated ones, and effects
  averaged (overall and by event time). Robust to staggered timing and effects that change over time,
  where a static two-way regression can mis-weight them.
- ``placebo_null``: randomization inference by re-running any estimator on placebo assignments
  (states, industries, dates); returns the project's ``stagger.Null`` (p-value, Conley-Taber
  interval, smallest detectable effect).
- ``shift_share``: exposure-weighted controls, e.g. pre-period mining share x commodity prices.
- ``simulate_panel``: synthetic panels with planted effects and planted state, industry and
  state-specific-sensitivity shocks, for tests (ILLUSTRATIVE data, not real).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .stagger import Null

FE = str | tuple[str, ...]


# ---- fixed effects -------------------------------------------------------------------------------


def codes(df: pd.DataFrame, spec: FE) -> np.ndarray:
    """Integer group codes 0..G-1 for one fixed effect (a column, or a tuple of columns interacted)."""
    cols = [spec] if isinstance(spec, str) else list(spec)
    return df.groupby(cols, sort=True, observed=True).ngroup().to_numpy()


@dataclass
class _Groups:
    codes: np.ndarray
    weights: np.ndarray
    order: np.ndarray = field(init=False)
    starts: np.ndarray = field(init=False)
    wsum: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.order = np.argsort(self.codes, kind="stable")
        sc = self.codes[self.order]
        self.starts = np.flatnonzero(np.r_[True, sc[1:] != sc[:-1]])
        if len(self.starts) != sc[-1] + 1:
            raise ValueError("group codes must be 0..G-1 with every group present")
        self.wsum = np.add.reduceat(self.weights[self.order], self.starts)

    def means(self, z: np.ndarray) -> np.ndarray:
        wz = self.weights[:, None] * z
        return np.add.reduceat(wz[self.order], self.starts, axis=0) / self.wsum[:, None]


def absorb(
    z: np.ndarray,
    groups: Sequence[np.ndarray],
    weights: np.ndarray | None = None,
    tol: float = 1e-10,
    maxiter: int = 10_000,
) -> np.ndarray:
    """Residuals of ``z`` (n, or n x k) after projecting out every fixed effect in ``groups``."""
    z = np.array(z, dtype=float, copy=True)
    flat = z.ndim == 1
    z = z.reshape(len(z), -1)
    if not groups:
        return z[:, 0] if flat else z
    w = np.ones(len(z)) if weights is None else np.asarray(weights, dtype=float)
    gs = [_Groups(np.asarray(g), w) for g in groups]
    scale = 1.0 + np.abs(z).max()
    for _ in range(maxiter):
        change = 0.0
        for g in gs:
            m = g.means(z)
            z -= m[g.codes]
            change = max(change, float(np.abs(m).max()))
        if change < tol * scale or len(gs) == 1:
            break
    else:
        raise RuntimeError(f"fixed effects did not converge in {maxiter} iterations")
    return z[:, 0] if flat else z


# ---- regression ---------------------------------------------------------------------------------


@dataclass
class Fit:
    names: list[str]
    coef: pd.Series
    se: pd.Series
    vcov: pd.DataFrame
    nobs: int
    nclusters: int | None
    resid: np.ndarray

    def t(self, name: str, null: float = 0.0) -> float:
        return float((self.coef[name] - null) / self.se[name])

    def summary(self) -> dict:
        return {
            "coef": {k: float(v) for k, v in self.coef.items()},
            "se": {k: float(v) for k, v in self.se.items()},
            "nobs": self.nobs,
            "nclusters": self.nclusters,
        }


def _design(df, y, x, fe, weights):
    w = np.ones(len(df)) if weights is None else df[weights].to_numpy(float)
    groups = [codes(df, f) for f in fe]
    z = absorb(np.column_stack([df[y].to_numpy(float), df[list(x)].to_numpy(float)]), groups, w)
    return z[:, 0], z[:, 1:], w, groups


def _vcov(xt, u, w, clusters, small, bread=None):
    n, k = xt.shape
    bread = np.linalg.inv(xt.T @ (w[:, None] * xt)) if bread is None else bread
    s = xt * (w * u)[:, None]
    if clusters is None:
        meat = s.T @ s
        c = n / (n - k)
        return c * bread @ meat @ bread, None
    cl = np.unique(clusters, return_inverse=True)[1]
    g = cl.max() + 1
    sg = np.zeros((g, k))
    np.add.at(sg, cl, s)
    c = g / (g - 1) * ((n - 1) / (n - k) if small == "cr1" else 1.0)
    return c * bread @ (sg.T @ sg) @ bread, int(g)


def feols(
    df: pd.DataFrame,
    y: str,
    x: Sequence[str],
    fe: Sequence[FE] = (),
    cluster: str | None = None,
    weights: str | None = None,
    small: str = "cr1",
) -> Fit:
    """Least squares of ``y`` on ``x`` with fixed effects ``fe`` absorbed.

    ``small``: "cr1" multiplies the cluster variance by G/(G-1) x (N-1)/(N-K) (K = regressors in ``x``);
    "cluster" by G/(G-1) only. Without ``cluster``, heteroskedasticity-robust (HC1 on ``x`` only).
    """
    x = list(x)
    yt, xt, w, _ = _design(df, y, x, fe, weights)
    bread = np.linalg.inv(xt.T @ (w[:, None] * xt))
    beta = bread @ (xt.T @ (w * yt))
    u = yt - xt @ beta
    v, g = _vcov(xt, u, w, df[cluster].to_numpy() if cluster else None, small, bread)
    return Fit(
        names=x,
        coef=pd.Series(beta, index=x),
        se=pd.Series(np.sqrt(np.diag(v)), index=x),
        vcov=pd.DataFrame(v, index=x, columns=x),
        nobs=len(df),
        nclusters=g,
        resid=u,
    )


def wild_cluster_bootstrap(
    df: pd.DataFrame,
    y: str,
    x: Sequence[str],
    param: str,
    cluster: str,
    fe: Sequence[FE] = (),
    null: float = 0.0,
    reps: int = 999,
    dist: str = "webb",
    seed: int = 0,
    weights: str | None = None,
    small: str = "cr1",
    batch: int = 200,
) -> dict:
    """Restricted wild cluster bootstrap-t for H0: coefficient on ``param`` = ``null``.

    Draws multiply the restricted residuals of each cluster by one weight (Rademacher: +-1; Webb: six
    points +-sqrt(1/2), +-1, +-sqrt(3/2)). Fixed effects not nested in the clusters are re-absorbed for
    every draw. Returns the observed t, the symmetric bootstrap p-value and the number of draws.
    """
    x = list(x)
    k = x.index(param)
    yt, xt, w, groups = _design(df, y, x, fe, weights)
    clusters = np.unique(df[cluster].to_numpy(), return_inverse=True)[1]
    g = clusters.max() + 1
    bread = np.linalg.inv(xt.T @ (w[:, None] * xt))
    beta = bread @ (xt.T @ (w * yt))
    u = yt - xt @ beta
    v, _ = _vcov(xt, u, w, clusters, small, bread)
    t_obs = (beta[k] - null) / np.sqrt(v[k, k])

    # Restricted fit: impose the null, regress on the other regressors.
    others = [j for j in range(len(x)) if j != k]
    y_r = yt - null * xt[:, k]
    if others:
        xo = xt[:, others]
        b_r = np.linalg.solve(xo.T @ (w[:, None] * xo), xo.T @ (w * y_r))
        fitted = xo @ b_r + null * xt[:, k]
    else:
        fitted = null * xt[:, k]
    u_r = yt - fitted

    nested = all(_nested(gr, clusters) for gr in groups)
    rng = np.random.default_rng(seed)
    q = (xt @ bread[k]) * w  # beta*_k = sum_i q_i y*_i
    n, kk = xt.shape
    c = g / (g - 1) * ((n - 1) / (n - kk) if small == "cr1" else 1.0)
    t_star = []
    done = 0
    while done < reps:
        b = min(batch, reps - done)
        vg = _weights(rng, dist, (g, b))
        us = u_r[:, None] * vg[clusters]
        if not nested:
            us = absorb(us, groups, w)
        ys = fitted[:, None] + us
        bs = bread @ (xt.T @ (w[:, None] * ys))
        res = ys - xt @ bs
        sc = np.zeros((g, b))
        np.add.at(sc, clusters, q[:, None] * res)
        se = np.sqrt(c * (sc**2).sum(axis=0))
        t_star.append((bs[k] - null) / se)
        done += b
    t_star = np.concatenate(t_star)
    p = float((np.abs(t_star) >= abs(t_obs)).mean())
    return {"param": param, "coef": float(beta[k]), "t": float(t_obs), "p_value": p, "reps": reps, "clusters": int(g)}


def _nested(fe_codes: np.ndarray, clusters: np.ndarray) -> bool:
    """Every fixed-effect group lies within one cluster."""
    pairs = pd.DataFrame({"f": fe_codes, "c": clusters}).drop_duplicates()
    return not pairs["f"].duplicated().any()


def _weights(rng, dist: str, shape) -> np.ndarray:
    if dist == "rademacher":
        return rng.choice([-1.0, 1.0], size=shape)
    if dist == "webb":
        pts = np.sqrt([0.5, 1.0, 1.5])
        return rng.choice(np.r_[-pts, pts], size=shape)
    raise ValueError(f"unknown weight distribution '{dist}'")


# ---- imputation (Borusyak, Jaravel and Spiess 2024) ----------------------------------------------


@dataclass
class Imputation:
    att: float
    tau: pd.Series  # effect for each treated observation (index of the input frame)
    by_event: pd.Series | None
    beta: pd.Series  # control coefficients, from untreated observations
    n_treated: int
    n_unidentified: int  # treated observations whose fixed effects have no untreated observation


def imputation(
    df: pd.DataFrame,
    y: str,
    treat: str,
    fe: Sequence[FE],
    controls: Sequence[str] = (),
    weights: str | None = None,
    event_time: str | None = None,
    tol: float = 1e-12,
    maxiter: int = 100_000,
) -> Imputation:
    """Fit fixed effects (and controls) on untreated observations, impute Y(0) for treated ones,
    and average the differences (``weights`` weight the average, not the first stage)."""
    d = df[treat].to_numpy().astype(bool)
    controls = list(controls)
    un = df.loc[~d]
    beta = pd.Series(dtype=float)
    r = un[y].to_numpy(float)
    if controls:
        beta = feols(un, y, controls, fe).coef
        r = r - un[controls].to_numpy(float) @ beta.to_numpy()
    full = [codes(df, f) for f in fe]
    sub = [c[~d] for c in full]
    counts = [np.bincount(c, minlength=f.max() + 1) for c, f in zip(sub, full, strict=True)]
    alpha = [np.zeros(len(n)) for n in counts]
    fitted = np.zeros(len(r))
    scale = 1.0 + np.abs(r).max()
    # Backfitting (Gauss-Seidel on the normal equations): the fitted values converge even though the
    # individual fixed effects are only identified up to normalisations.
    for _ in range(maxiter):
        delta = 0.0
        for j, (c, n) in enumerate(zip(sub, counts, strict=True)):
            partial = r - fitted + alpha[j][c]
            new = np.bincount(c, weights=partial, minlength=len(n)) / np.where(n > 0, n, 1)
            delta = max(delta, float(np.abs(new - alpha[j]).max()))
            fitted += new[c] - alpha[j][c]
            alpha[j] = new
        if delta < tol * scale:
            break
    else:
        raise RuntimeError(f"imputation first stage did not converge in {maxiter} sweeps")
    tr = df.loc[d]
    y0 = sum(a[c[d]] for a, c in zip(alpha, full, strict=True))
    if controls:
        y0 = y0 + tr[controls].to_numpy(float) @ beta.to_numpy()
    ok = np.all([n[c[d]] > 0 for n, c in zip(counts, full, strict=True)], axis=0)
    tau = pd.Series(np.where(ok, tr[y].to_numpy(float) - y0, np.nan), index=tr.index)
    w = tr[weights].to_numpy(float) if weights else np.ones(len(tr))
    good = ~np.isnan(tau.to_numpy())
    att = float(np.average(tau.to_numpy()[good], weights=w[good])) if good.any() else float("nan")
    by_event = None
    if event_time:
        e = pd.DataFrame({"tau": tau, "w": w, "e": tr[event_time]}).dropna()
        by_event = e.groupby("e").apply(lambda g: np.average(g["tau"], weights=g["w"]), include_groups=False)
    return Imputation(att, tau, by_event, beta, int(d.sum()), int((~ok).sum()))


# ---- randomization inference and controls --------------------------------------------------------


def placebo_null(estimate: Callable[[object], float], placebos: Iterable[object]) -> Null:
    """Run ``estimate`` on each placebo assignment (e.g. a state and industry treated in its place)."""
    items = list(placebos)
    return Null(pd.Series([estimate(p) for p in items], index=[str(p) for p in items], dtype=float))


def shift_share(weights: pd.Series, shocks: pd.DataFrame) -> pd.DataFrame:
    """Exposure-weighted shocks: for each unit, sum over k of weight[unit, k] x shock[period, k].

    ``weights``: indexed by (unit, k), fixed from a pre-period (e.g. each state's mining share of
    output in the year before the reform). ``shocks``: periods x k (e.g. log commodity prices).
    Returns periods x units.
    """
    w = weights.unstack(fill_value=0.0)
    common = [k for k in w.columns if k in shocks.columns]
    if not common:
        raise ValueError("weights and shocks share no components")
    return shocks[common] @ w[common].T


# ---- synthetic panels for tests --------------------------------------------------------------------


def simulate_panel(
    seed: int = 0,
    n_states: int = 8,
    n_industries: int = 12,
    n_periods: int = 40,
    adoption: dict[tuple[int, int], int] | None = None,
    effect: Callable[[np.ndarray], np.ndarray] | float = 2.0,
    state_shock: float = 3.0,
    industry_shock: float = 3.0,
    loading_shock: float = 0.0,
    noise: float = 1.0,
    control: float = 0.0,
) -> pd.DataFrame:
    """ILLUSTRATIVE synthetic state x industry x period panel.

    ``adoption`` maps (state, industry) cells to the first treated period (default: state 0, industry 0
    from period 24). ``effect`` is a number or a function of event time (0 in the first treated period).
    Shocks: ``state_shock`` (state x period, correlated with being the treated state after adoption),
    ``industry_shock`` (industry x period), ``loading_shock`` (a common factor with state-specific
    loadings), ``control`` (a covariate correlated with treatment that enters y with coefficient 1).
    """
    rng = np.random.default_rng(seed)
    adoption = {(0, 0): 24} if adoption is None else adoption
    s, i, t = np.meshgrid(np.arange(n_states), np.arange(n_industries), np.arange(n_periods), indexing="ij")
    s, i, t = s.ravel(), i.ravel(), t.ravel()
    first = np.array([adoption.get((a, b), -1) for a, b in zip(s, i, strict=True)])
    treated_state = np.isin(s, [a for a, _ in adoption])
    d = (first >= 0) & (t >= first)
    e = np.where(first >= 0, t - first, -999)
    cell = rng.normal(0, 2, (n_states, n_industries))[s, i]
    gst = rng.normal(0, state_shock, (n_states, n_periods))
    for a, start in {a: min(v for (aa, _), v in adoption.items() if aa == a) for a, _ in adoption}.items():
        gst[a, start:] += state_shock  # a boom in treated states after adoption
    dit = rng.normal(0, industry_shock, (n_industries, n_periods)) + np.linspace(0, 2, n_periods)
    factor = np.cumsum(rng.normal(0, 1, n_periods))
    loading = rng.normal(1, 1, n_states)
    x = rng.normal(0, 1, len(s)) + control * d
    tau = np.where(d, effect(e) if callable(effect) else effect, 0.0)
    y = (
        cell
        + gst[s, t]
        + dit[i, t]
        + loading_shock * loading[s] * factor[t]
        + (x if control else 0.0)
        + tau
        + rng.normal(0, noise, len(s))
    )
    return pd.DataFrame(
        {
            "state": s,
            "industry": i,
            "period": t,
            "y": y,
            "D": d.astype(float),
            "x": x,
            "first_treated": first,
            "event_time": np.where(d, e, np.nan),
            "treated_state": treated_state,
            "true_tau": tau,
        }
    )
