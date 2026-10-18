"""Estimators for one or a few treated units with long histories (forward plan §2.3 and §2.5).

They let each treated unit respond differently to common shocks (a factor structure), which fixed
effects cannot. Inputs are wide matrices: ``Y`` is units x periods, ``treated`` a boolean matrix of the
same shape marking treated unit-periods (treatment is absorbing).

- ``sdid``: synthetic difference-in-differences (Arkhangelsky, Athey, Hirshberg, Imbens and Wager 2021),
  following the reference implementation (R package synthdid): Frank-Wolfe unit and time weights with
  an intercept, ridge penalty zeta = (N1 x T1)^(1/4) x sd(first differences of control outcomes), then
  one sparsifying pass. ``method="sc"`` gives the synthetic control (no intercept, no time weights) and
  ``"did"`` difference-in-differences (uniform weights), on the same footing.
- ``gsynth``: generalised synthetic control / interactive fixed effects (Xu 2017; Bai 2009). Factors and
  time effects come from never-treated units; each treated unit's intercept and loadings from its own
  pre-period; the number of factors by leave-one-period-out cross-validation on treated pre-periods.
- ``mc_nnm``: matrix completion with unit and time effects and a nuclear-norm penalty (Athey, Bayati,
  Doudchenko, Imbens and Khosravi 2021), penalty chosen by cross-validation on control cells. A check.
- ``conformal_pvalue`` / ``conformal_interval``: permutation inference for a hypothesised post-period
  effect (Chernozhukov, Wuthrich and Zhu 2021), with moving-block permutations over time; valid with a
  single treated unit when the fitted model's residuals are stationary and weakly dependent.

Placebo inference across units, as elsewhere in ALICIA, uses ``panel.placebo_null``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

# ---- Frank-Wolfe simplex weights (synthdid's sc.weight.fw) --------------------------------------------


def _fw_step(a: np.ndarray, x: np.ndarray, b: np.ndarray, eta: float) -> np.ndarray:
    ax = a @ x
    half_grad = (ax - b) @ a + eta * x
    i = int(np.argmin(half_grad))
    dx = -x.copy()
    dx[i] = 1 - x[i]
    if not dx.any():
        return x
    derr = a[:, i] - ax
    step = -(half_grad @ dx) / (derr @ derr + eta * (dx @ dx))
    return x + min(1.0, max(0.0, step)) * dx


def simplex_weights(
    y: np.ndarray,
    zeta: float,
    intercept: bool = True,
    start: np.ndarray | None = None,
    min_decrease: float = 1e-3,
    max_iter: int = 1000,
) -> np.ndarray:
    """Weights on the simplex for the columns of ``y[:, :-1]`` that best reproduce ``y[:, -1]``:
    minimise zeta^2 ||w||^2 + ||A w - b||^2 / rows, with a free intercept if ``intercept``."""
    y = np.asarray(y, float)
    if intercept:
        y = y - y.mean(axis=0)
    rows, k = y.shape[0], y.shape[1] - 1
    a, b = y[:, :k], y[:, k]
    w = np.full(k, 1.0 / k) if start is None else start.copy()
    eta = rows * zeta**2
    vals = []
    for t in range(max_iter):
        w = _fw_step(a, w, b, eta)
        err = a @ w - b
        vals.append(zeta**2 * (w @ w) + (err @ err) / rows)
        if t >= 1 and vals[-2] - vals[-1] <= min_decrease**2:
            break
    return w


def _sparsify(w: np.ndarray) -> np.ndarray:
    w = np.where(w <= w.max() / 4, 0.0, w)
    return w / w.sum()


@dataclass
class SDID:
    estimate: float
    omega: np.ndarray  # weights on control units
    lam: np.ndarray  # weights on pre-periods
    method: str


def _split(y: np.ndarray, treated: np.ndarray):
    tr_units = treated.any(axis=1)
    post = treated.any(axis=0)
    if not tr_units.any() or not post.any():
        raise ValueError("no treated unit-periods")
    t0 = int(np.argmax(post))
    if not (treated[tr_units] == post).all() or not post[t0:].all():
        raise ValueError("sdid needs one adoption date for all treated units: use it per cohort and average")
    return y[~tr_units], y[tr_units], t0


def sdid(y: np.ndarray, treated: np.ndarray, method: str = "sdid", unit_weights: np.ndarray | None = None) -> SDID:
    """Synthetic DiD (``method="sdid"``), synthetic control (``"sc"``) or DiD (``"did"``).

    All treated units must adopt in the same period; treated rows are averaged (``unit_weights`` to weight
    them, e.g. by business counts)."""
    y = np.asarray(y, float)
    treated = np.asarray(treated, bool)
    yc, yt, t0 = _split(y, treated)
    n0, t = yc.shape
    n1, t1 = yt.shape[0], t - t0
    wt = np.full(n1, 1 / n1) if unit_weights is None else np.asarray(unit_weights, float) / np.sum(unit_weights)
    ytr = wt @ yt
    noise = float(np.std(np.diff(yc[:, :t0], axis=1), ddof=1)) if t0 > 1 else 1.0
    # Collapsed form: controls and the treated average; pre-periods and the post average.
    yc_post = yc[:, t0:].mean(axis=1)
    ytr_post = ytr[t0:].mean()
    if method == "did":
        omega, lam = np.full(n0, 1 / n0), np.full(t0, 1 / t0)
    elif method == "sc":
        zeta = 1e-6 * noise
        mat = np.column_stack([yc[:, :t0].T, ytr[:t0]])
        omega = simplex_weights(mat, zeta, intercept=False, min_decrease=1e-5 * noise, max_iter=100)
        omega = simplex_weights(mat, zeta, False, _sparsify(omega), 1e-5 * noise, 10_000)
        lam = np.zeros(t0)
    elif method == "sdid":
        zeta_omega = (n1 * t1) ** 0.25 * noise
        zeta_lambda = 1e-6 * noise
        md = 1e-5 * noise
        lam = simplex_weights(np.column_stack([yc[:, :t0], yc_post]), zeta_lambda, True, None, md, 100)
        lam = simplex_weights(np.column_stack([yc[:, :t0], yc_post]), zeta_lambda, True, _sparsify(lam), md, 10_000)
        mat = np.column_stack([yc[:, :t0].T, ytr[:t0]])
        omega = simplex_weights(mat, zeta_omega, True, None, md, 100)
        omega = simplex_weights(mat, zeta_omega, True, _sparsify(omega), md, 10_000)
    else:
        raise ValueError(f"unknown method '{method}'")
    est = (ytr_post - lam @ ytr[:t0]) - omega @ (yc_post - yc[:, :t0] @ lam)
    return SDID(float(est), omega, lam, method)


# ---- interactive fixed effects / generalised synthetic control -------------------------------------------


def _twoway(z: np.ndarray, mask: np.ndarray | None = None, iters: int = 200) -> np.ndarray:
    """Fitted unit + time effects of ``z`` (on ``mask`` cells only, if given)."""
    if mask is None:
        mu = z.mean()
        return mu + (z.mean(axis=1, keepdims=True) - mu) + (z.mean(axis=0, keepdims=True) - mu)
    a = np.zeros((z.shape[0], 1))
    b = np.zeros((1, z.shape[1]))
    m = mask.astype(float)
    for _ in range(iters):
        a = ((z - b) * m).sum(axis=1, keepdims=True) / np.maximum(m.sum(axis=1, keepdims=True), 1)
        b_new = ((z - a) * m).sum(axis=0, keepdims=True) / np.maximum(m.sum(axis=0, keepdims=True), 1)
        if np.abs(b_new - b).max() < 1e-12:
            b = b_new
            break
        b = b_new
    return a + b


def factor_model(yc: np.ndarray, r: int, tol: float = 1e-9, maxiter: int = 5000) -> tuple[np.ndarray, np.ndarray]:
    """Time effects xi (T,) and factors F (T x r, F'F/T = I) from control units: y = a_i + xi_t + l_i'F_t + e."""
    n, t = yc.shape
    low = np.zeros_like(yc)
    for _ in range(maxiter):
        fe = _twoway(yc - low)
        e = yc - fe
        if r == 0:
            low_new = np.zeros_like(yc)
        else:
            u, s, vt = np.linalg.svd(e, full_matrices=False)
            low_new = (u[:, :r] * s[:r]) @ vt[:r]
        if np.abs(low_new - low).max() < tol * (1 + np.abs(yc).max()):
            low = low_new
            break
        low = low_new
    fe = _twoway(yc - low)
    xi = fe.mean(axis=0)  # grand mean plus time effects; unit levels are re-estimated for treated units
    if r == 0:
        return xi, np.zeros((t, 0))
    _, _, vt = np.linalg.svd(yc - fe, full_matrices=False)
    return xi, np.sqrt(t) * vt[:r].T


@dataclass
class GSynth:
    att: float
    att_by_period: np.ndarray  # mean effect in each period among treated units (nan where none treated)
    effects: np.ndarray  # unit x period effects (nan where untreated)
    y0: np.ndarray  # imputed untreated outcomes for treated units
    r: int
    cv_mse: dict[int, float]


def _loadings(target: np.ndarray, f: np.ndarray, pre: np.ndarray) -> np.ndarray:
    x = np.column_stack([np.ones(pre.sum()), f[pre]])
    coef, *_ = np.linalg.lstsq(x, target[pre], rcond=None)
    return coef


def gsynth(y: np.ndarray, treated: np.ndarray, r: int | None = None, rmax: int = 5) -> GSynth:
    """Generalised synthetic control. Treated units may adopt at different dates (each uses its own
    pre-period); controls are units never treated. ``r=None`` chooses the number of factors by
    leave-one-period-out cross-validation over treated units' pre-periods."""
    y = np.asarray(y, float)
    treated = np.asarray(treated, bool)
    tr = treated.any(axis=1)
    yc, yt, dt = y[~tr], y[tr], treated[tr]
    pre_len = (~dt).sum(axis=1)
    cv: dict[int, float] = {}
    if r is None:
        best = None
        for k in range(0, rmax + 1):
            if (pre_len <= k + 1).any() or k >= min(yc.shape):
                break
            xi, f = factor_model(yc, k)
            errs = []
            for i in range(len(yt)):
                pre = ~dt[i]
                for s in np.flatnonzero(pre):
                    keep = pre.copy()
                    keep[s] = False
                    coef = _loadings(yt[i] - xi, f, keep)
                    pred = coef[0] + f[s] @ coef[1:] + xi[s]
                    errs.append((yt[i, s] - pred) ** 2)
            cv[k] = float(np.mean(errs))
            if best is None or cv[k] < cv[best] - 1e-12:
                best = k
        r = 0 if best is None else best
    xi, f = factor_model(yc, r)
    y0 = np.empty_like(yt)
    for i in range(len(yt)):
        coef = _loadings(yt[i] - xi, f, ~dt[i])
        y0[i] = xi + coef[0] + f @ coef[1:]
    eff = np.where(dt, yt - y0, np.nan)
    count = dt.sum(axis=0)
    by_t = np.where(count > 0, np.where(dt, eff, 0.0).sum(axis=0) / np.maximum(count, 1), np.nan)
    return GSynth(float(np.nanmean(eff)), by_t, eff, y0, int(r), cv)


# ---- matrix completion -------------------------------------------------------------------------------------


def _svt(m: np.ndarray, thr: float) -> np.ndarray:
    u, s, vt = np.linalg.svd(m, full_matrices=False)
    s = np.maximum(s - thr, 0)
    return (u * s) @ vt


def _complete(y: np.ndarray, observed: np.ndarray, thr: float, tol: float = 1e-7, maxiter: int = 2000) -> np.ndarray:
    fit = np.where(observed, y, np.nanmean(np.where(observed, y, np.nan)))
    low = np.zeros_like(y)
    for _ in range(maxiter):
        z = np.where(observed, y, fit)
        fe = _twoway(z - low)
        low_new = _svt(z - fe, thr)
        fit_new = fe + low_new
        if np.abs(fit_new - fit).max() < tol * (1 + np.abs(y[observed]).max()):
            return fit_new
        fit, low = fit_new, low_new
    return fit


@dataclass
class MatrixCompletion:
    att: float
    effects: np.ndarray
    threshold: float


def mc_nnm(y: np.ndarray, treated: np.ndarray, grid: int = 8, folds: int = 4, seed: int = 0) -> MatrixCompletion:
    """Matrix completion with unit and time effects; treated cells are treated as missing."""
    y = np.asarray(y, float)
    treated = np.asarray(treated, bool)
    observed = ~treated
    smax = np.linalg.svd(np.where(observed, y, 0) - _twoway(y, observed), compute_uv=False)[0]
    thresholds = smax * np.geomspace(1, 1e-3, grid)
    rng = np.random.default_rng(seed)
    ctrl = np.argwhere(observed & ~treated.any(axis=1, keepdims=True))
    fold = rng.integers(0, folds, len(ctrl))
    mse = []
    for thr in thresholds:
        err = []
        for k in range(folds):
            hold = ctrl[fold == k]
            obs = observed.copy()
            obs[hold[:, 0], hold[:, 1]] = False
            fit = _complete(y, obs, thr)
            err.append(np.mean((fit[hold[:, 0], hold[:, 1]] - y[hold[:, 0], hold[:, 1]]) ** 2))
        mse.append(np.mean(err))
    thr = float(thresholds[int(np.argmin(mse))])
    fit = _complete(y, observed, thr)
    eff = np.where(treated, y - fit, np.nan)
    return MatrixCompletion(float(np.nanmean(eff)), eff, thr)


# ---- conformal inference ------------------------------------------------------------------------------------

Fit = Callable[[np.ndarray, np.ndarray], np.ndarray]


def fit_did(ytr: np.ndarray, yc: np.ndarray) -> np.ndarray:
    """Counterfactual for the treated series: its mean level plus the control average's movements."""
    avg = yc.mean(axis=0)
    return avg + (ytr - avg).mean()


def fit_sc(ytr: np.ndarray, yc: np.ndarray) -> np.ndarray:
    """Synthetic control fitted on every period supplied (no intercept, simplex weights)."""
    w = simplex_weights(np.column_stack([yc.T, ytr]), zeta=1e-8, intercept=False, max_iter=5000, min_decrease=1e-8)
    return yc.T @ w


def conformal_pvalue(
    ytr: np.ndarray, yc: np.ndarray, t0: int, theta: float | np.ndarray = 0.0, fit: Fit = fit_did, q: float = 1.0
) -> float:
    """p-value for H0: the treated unit's effect in periods t0.. equals ``theta``.

    The model is fitted on all periods with the null imposed; the statistic is the mean absolute
    post-period residual (q = 1), compared with its values under the T moving-block (cyclic) shifts."""
    ytr = np.asarray(ytr, float).copy()
    ytr[t0:] = ytr[t0:] - theta
    u = ytr - fit(ytr, np.asarray(yc, float))
    t = len(u)
    t1 = t - t0

    def stat(v):
        return (np.abs(v[t0:]) ** q).sum() / np.sqrt(t1)

    s0 = stat(u)
    perms = [stat(np.roll(u, j)) for j in range(t)]
    return float(np.mean(np.array(perms) >= s0 - 1e-12))


def conformal_interval(
    ytr: np.ndarray, yc: np.ndarray, t0: int, grid: np.ndarray, fit: Fit = fit_did, alpha: float = 0.1
) -> tuple[float, float] | None:
    """Set of constant effects not rejected at level ``alpha`` (by test inversion over ``grid``)."""
    keep = [g for g in grid if conformal_pvalue(ytr, yc, t0, g, fit) > alpha]
    return (float(min(keep)), float(max(keep))) if keep else None
