"""Measured state controls for the panel estimators, from the control panels (``alicia.pipeline.controls``).

Used where the fixed effects cannot be saturated (forward plan §2.2), e.g. a single-industry outcome
such as a price index. All are state x quarter (period = first day of the quarter):

- ``sfd_growth``: state final demand, chain volume, 100 x change in log over four quarters;
- ``unemployment_rate``: quarterly mean of the monthly rate (seasonally adjusted; NT and ACT original);
- ``population_growth``: 100 x change in log ERP over four quarters;
- ``wage_growth``: 100 x change in log Wage Price Index (all sectors, original) over four quarters;
- ``dwelling_approvals``: dwelling units approved in the quarter per 1,000 residents;
- ``commodity_exposure``: shift-share control, each state's mining share of gross value added in a
  base financial year x 100 x log RBA commodity prices (A$), so states more exposed to mining get more
  of the national commodity cycle.

Bad-control rule (plan §3): these are state aggregates that include the treated industry. A plan must
say why the reform cannot move them materially (e.g. the treated industry is a small share of state
demand), or use fixed effects instead.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..pipeline import controls, store
from . import panel


def _quarterly(df: pd.DataFrame, how: str = "mean") -> pd.DataFrame:
    q = df.assign(period=df["period"].dt.to_period("Q").dt.to_timestamp())
    g = q.groupby(["geo_code", "period"])["value"]
    return (g.mean() if how == "mean" else g.sum()).reset_index()


def _log_change(df: pd.DataFrame, lag: int = 4) -> pd.Series:
    df = df.sort_values(["geo_code", "period"])
    return 100 * np.log(df["value"]).groupby(df["geo_code"]).diff(lag)


def mining_share(base_fy: int) -> pd.Series:
    """Mining share of each state's gross value added (current prices) in financial year ``base_fy``
    (named by its first year: 2009 = 2009-10). Indexed by state."""
    sa = store.read_panel("abs_state_accounts", "industry_state_fy")
    d = sa[(sa["measure"] == "gva_current") & (sa["period"].dt.year == base_fy) & (sa["geo_level"] == "STE")]
    wide = d.pivot_table(index="geo_code", columns="industry_code", values="value")
    return (wide["B"] / wide[""]).rename("mining_share")


def commodity_exposure(base_fy: int) -> pd.DataFrame:
    """State x quarter: mining share in ``base_fy`` x 100 x log commodity prices (A$, all items)."""
    nm = controls.load("national_month")
    com = nm[nm["breakdown"] == "All items - A$"].assign(geo_code="AUS")
    shock = _quarterly(com).set_index("period")["value"]
    shocks = pd.DataFrame({"mining": 100 * np.log(shock)})
    share = mining_share(base_fy)
    weights = pd.Series({(s, "mining"): v for s, v in share.items()})
    wide = panel.shift_share(weights, shocks)
    return wide.stack().rename("commodity_exposure").rename_axis(["period", "state"]).reset_index()


def state_covariates(base_fy: int = 2009) -> pd.DataFrame:
    """One row per state and quarter with the measured controls listed in the module docstring."""
    sq = controls.load("state_quarter")
    sm = controls.load("state_month")
    out = []

    sfd = sq[sq["measure"] == "state_final_demand_volume"][["geo_code", "period", "value"]]
    out.append(sfd.assign(value=_log_change(sfd), name="sfd_growth"))

    ur = sm[sm["measure"] == "unemployment_rate"]
    sa = ur[ur["adjustment"] == "seasonally adjusted"]
    orig = ur[(ur["adjustment"] == "original") & ~ur["geo_code"].isin(sa["geo_code"].unique())]
    out.append(_quarterly(pd.concat([sa, orig])).assign(name="unemployment_rate"))

    pop = sq[sq["measure"] == "population"][["geo_code", "period", "value"]]
    out.append(pop.assign(value=_log_change(pop), name="population_growth"))

    wpi = sq[
        (sq["measure"] == "wage_price_index") & (sq["breakdown"] == "all sectors") & (sq["adjustment"] == "original")
    ]
    wpi = wpi[["geo_code", "period", "value"]]
    out.append(wpi.assign(value=_log_change(wpi), name="wage_growth"))

    dw = sm[(sm["measure"] == "dwelling_approvals") & (sm["breakdown"] == "") & sm["geo_level"].isin(["STE", "AUS"])]
    dwq = _quarterly(dw, how="sum").merge(pop.rename(columns={"value": "pop"}), on=["geo_code", "period"])
    out.append(dwq.assign(value=dwq["value"] / dwq["pop"] * 1000, name="dwelling_approvals"))

    long = pd.concat([d[["geo_code", "period", "value", "name"]] for d in out], ignore_index=True)
    wide = long.pivot_table(index=["geo_code", "period"], columns="name", values="value").reset_index()
    wide = wide.rename(columns={"geo_code": "state"}).rename_axis(columns=None)
    exp = commodity_exposure(base_fy)
    return wide.merge(exp, on=["state", "period"], how="left").sort_values(["state", "period"]).reset_index(drop=True)
