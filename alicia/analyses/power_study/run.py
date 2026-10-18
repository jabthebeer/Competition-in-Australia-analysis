"""Forward plan Phase 3: blinded power study. How much does each layer of the regression framework shrink
the no-effect spread for each evaluable reform?

Outcome: business entry and exit rates (per 100 businesses operating at the start of the financial year),
ANZSIC class x state x financial year, from CABEE. Unit of analysis: a cell (class x state).

Blinding: before anything is computed, every row for a reform's treated classes in its treated states from
the first exposed year on is deleted (``hide``; checked by ``assert_blind``). No estimate of any reform's
effect is made here.

No-effect distributions (placebo families). Every layer is run on the same placebo assignments, so
differences in spread are differences between estimators. Smallest detectable effect (80% power, 5%
two-sided) = 2.8 x the standard deviation of placebo estimates.
- ``industries`` (main): the same size-matched placebo class groups as the high-evaluability batch
  (``analyses/high_evaluability/run.py: placebo_groups``; up to 40), each assigned the reform's treated
  states and dates;
- ``states``: the reform's own classes, assigned to states that never adopted it (every way of choosing
  as many states as each cohort has; up to 20), at the reform's dates;
- ``dates``: the reform's own classes and states at earlier, fake dates (each cohort moved back 1, 2, ...
  years, keeping at least two earlier years; window cut before the real first exposure; the panel ends with
  the fake window);
- ``states_dates``: both at once (up to 20 draws).
The last three use the treated industries themselves, so they show whether placebo industries understate
or overstate the noise in the treated classes. They have few draws: MDEs from fewer than 10 are rough.

Layers (estimates in percentage points of the entry or exit rate):
- ``twoway``: cell and year fixed effects (no macro controls), weighted by businesses;
- ``state_year``: cell and state x year effects (state macro conditions absorbed);
- ``saturated``: cell, class x year and state x year effects (plus national industry cycles);
- ``controls``: cell and year effects plus measured state controls (final demand growth, unemployment,
  population growth, mining share x commodity prices), the fallback where effects cannot be saturated;
- ``imputation``: saturated effects fitted on untreated cells (Borusyak, Jaravel and Spiess), weighted;
- ``sdid``: synthetic DiD on the treated group's rate against all untreated cells, per cohort;
- ``gsynth``: generalised synthetic control on the same matrix, factors chosen by cross-validation.

The registered batch design's spread (stacked DiD net of placebo industries, design stage) is reported
alongside from ``analyses/high_evaluability/design.json``.

    uv run python analyses/power_study/run.py            # all reforms (about 20 minutes)
    uv run python analyses/power_study/run.py --only amr-2021-2022 --max-placebos 10
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
import warnings
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BATCH = HERE.parent / "high_evaluability"
sys.path.insert(0, str(BATCH))

import cases as batch_cases  # noqa: E402
import run as batch  # noqa: E402

from alicia.evaluate import covariates, panel, synth  # noqa: E402
from alicia.evaluate.stacked import Cohort  # noqa: E402

MDE_FACTOR = 2.801585
MAX_PLACEBOS = 40
MAX_OWN_DRAWS = 20  # placebo-state and state-and-date draws
MIN_PRE_FAKE = 2  # financial years before a fake first exposure
FAMILIES = ("industries", "states", "dates", "states_dates")
SEED = 20261018
MIN_CELL = 20  # businesses at the start of the base year, for control cells in the synthetic methods
MIN_CLASS_NATIONAL = 100  # businesses in the base year, Australia, for a class to enter the panel
COVARIATES = ("sfd_growth", "unemployment_rate", "population_growth", "commodity_exposure")
LAYERS = ("twoway", "state_year", "saturated", "controls", "imputation", "sdid", "gsynth")
ALL_BUT = batch_cases.ALL_BUT


@dataclass(frozen=True)
class Reform:
    case: batch_cases.Case
    registered: bool  # in the batch: use its registered CABEE vintage and report its design-stage spread
    notes: tuple[str, ...] = ()


def _case(**kw) -> batch_cases.Case:
    base = dict(records=(), family=None, hypothesis="enhancing", division="", design="", price=None)
    return batch_cases.Case(**(base | kw))


REFORMS: tuple[Reform, ...] = tuple(Reform(c, True) for c in batch_cases.CASES) + (
    Reform(
        _case(
            id="wa-trading-hours-weeknight-2010",
            title="Perth weeknight trading (November 2010)",
            records=("wa-trading-hours-weeknight-2010",),
            family="retail-trading-hours",
            classes=("4110", "4251", "4260"),
            cohorts=(Cohort(("WA",), 2011, 2012, ("NSW", "VIC", "QLD", "ACT")),),
            division="G",
            design="WA general retail against the same classes in NSW, Victoria, Queensland and the ACT, "
            "2010-11 and 2011-12 (Sunday trading followed in August 2012).",
            start=2008,
        ),
        False,
        ("Business counts by state are a different outcome from the registered re-evaluation (Perth vs regional WA).",),
    ),
    Reform(
        _case(
            id="amr-2021-2022",
            title="Automatic mutual recognition of occupational registrations (2021-22)",
            records=tuple(f"{s}-amr-2021" for s in ("act", "nsw", "nt", "sa", "tas", "vic")) + ("wa-amr-2022",),
            family="amr-occupational-licensing",
            classes=("3231", "3232", "3233", "6720", "3011"),
            cohorts=(
                Cohort(("ACT", "NSW", "NT", "VIC", "TAS", "SA"), 2022, 2025, ("QLD",)),
                Cohort(("WA",), 2023, 2025, ("QLD",)),
            ),
            division="E",
            design="Staggered: six jurisdictions from 2021-22, WA from 2022-23; Queensland never adopted.",
            start=2017,
        ),
        False,
        (
            "Uses CABEE releases after the registered vintage (to June 2025); 2019-20 to 2021-22 are COVID years.",
            "One never-treated state (Queensland), so comparisons within the treated classes rest on it.",
        ),
    ),
)


def _new(id, title, records, family, hypothesis, classes, cohorts, start, design, notes=()) -> Reform:
    """A family added from the 2026 gap scan (CABEE to June 2025; first exposed year = the one containing the date)."""
    case = _case(
        id=id,
        title=title,
        records=records,
        family=family,
        hypothesis=hypothesis,
        classes=classes,
        cohorts=cohorts,
        start=start,
        design=design,
    )
    return Reform(case, False, ("New family (gap scan, 18 October 2026).", *notes))


C = Cohort
NEW_REFORMS: tuple[Reform, ...] = (
    _new(
        "fuel-price-reporting-2016-2021",
        "Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021)",
        (
            "nsw-fuel-price-reporting-2016",
            "nt-fuel-price-reporting-2017",
            "qld-fuel-price-reporting-2018",
            "tas-fuel-price-reporting-2020",
            "sa-fuel-price-reporting-2021",
        ),
        "fuel-price-transparency",
        "mixed",
        ("4000",),
        (
            C(("NSW",), 2017, 2020, ("VIC", "ACT", "TAS", "SA")),
            C(("NT",), 2018, 2020, ("VIC", "ACT", "TAS", "SA")),
            C(("QLD",), 2019, 2020, ("VIC", "ACT", "TAS", "SA")),
            C(("TAS", "SA"), 2021, 2025, ("VIC", "ACT")),
        ),
        2010,
        "Staggered; Victoria (until August 2025) and the ACT never report; WA (always reporting) is left out.",
        ("NSW reporting start not confirmed; first exposed year 2016-17, from the July 2016 registration deadline.",),
    ),
    _new(
        "pharmacist-uti-2020-2024",
        "Pharmacists treat uncomplicated UTIs (QLD 2020, NSW 2023, five more 2023-24)",
        tuple(
            f"{s}-pharmacist-uti-{y}"
            for s, y in (
                ("qld", 2020),
                ("nsw", 2023),
                ("act", 2023),
                ("wa", 2023),
                ("vic", 2023),
                ("sa", 2024),
                ("tas", 2024),
            )
        ),
        "pharmacist-uti-prescribing",
        "enhancing",
        ("4271",),
        (
            C(("QLD",), 2020, 2022, ("NSW", "VIC", "SA", "WA", "TAS", "ACT", "NT")),
            C(("NSW",), 2023, 2023, ("VIC", "SA", "WA", "TAS", "ACT", "NT")),
            C(("ACT", "WA", "VIC", "SA", "TAS"), 2024, 2024, ("NT",)),
        ),
        2014,
        "Staggered, not-yet-adopting states as controls; the NT adopted last (October 2024).",
    ),
    _new(
        "necf-2012-2015",
        "National Energy Customer Framework adoption (ACT, TAS 2012; SA 2013; NSW 2013; QLD 2015)",
        ("act-necf-2012", "tas-necf-2012", "sa-necf-2013", "nsw-necf-2013", "qld-necf-2015"),
        "national-energy-customer-framework",
        "enhancing",
        ("2640",),
        (
            C(("ACT", "TAS", "SA"), 2013, 2018, ("VIC", "WA", "NT")),
            C(("NSW",), 2014, 2018, ("VIC", "WA", "NT")),
            C(("QLD",), 2016, 2018, ("VIC", "WA", "NT")),
        ),
        2008,
        "Staggered; Victoria, WA and the NT never adopted.",
    ),
    _new(
        "small-bars-nsw-2013",
        "Small bar licence (NSW, July 2013)",
        ("nsw-small-bar-licence-2013",),
        "small-bar-licences",
        "enhancing",
        ("4520",),
        (C(("NSW",), 2014, 2017, ("VIC", "QLD", "TAS", "ACT", "NT")),),
        2008,
        "NSW against states without a small-bar class (WA, from 2007, and SA, date unconfirmed, are left out).",
        ("Sydney lockout laws began in February 2014, in the first exposed year.",),
    ),
    _new(
        "e-conveyancing-2018-2023",
        "Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023)",
        (
            "nsw-e-conveyancing-mandate-2018",
            "wa-e-conveyancing-mandate-2018",
            "vic-e-conveyancing-mandate-2019",
            "sa-e-conveyancing-mandate-2020",
            "qld-e-conveyancing-mandate-2023",
        ),
        "e-conveyancing-mandate",
        "mixed",
        ("6931",),
        (
            C(("NSW",), 2018, 2022, ("ACT", "TAS", "NT", "QLD")),
            C(("WA",), 2019, 2022, ("ACT", "TAS", "NT", "QLD")),
            C(("VIC",), 2020, 2022, ("ACT", "TAS", "NT", "QLD")),
            C(("SA",), 2021, 2022, ("ACT", "TAS", "NT", "QLD")),
            C(("QLD",), 2023, 2025, ("ACT", "TAS", "NT")),
        ),
        2010,
        "Staggered; the ACT, Tasmania and the NT never mandated.",
    ),
    _new(
        "ncc-2022-2023-2025",
        "2022 building code adoption (NSW, VIC, QLD, ACT, NT 2023-24; SA, TAS, WA 2024-25)",
        ("nsw-ncc-2022-2023", "vic-ncc-2022-2024", "qld-ncc-2022-2024", "act-ncc-2022-2024", "nt-ncc-2022-2023"),
        "ncc-2022-adoption",
        "weakening",
        ("3011", "3019"),
        (C(("NSW", "VIC", "QLD", "ACT", "NT"), 2024, 2024, ("SA", "TAS", "WA")),),
        2016,
        "First-year effect only: 2023-24 adopters against 2024-25 adopters.",
    ),
    _new(
        "vet-entitlements-2009-2015",
        "Contestable VET entitlements (VIC 2009, SA 2012, QLD 2013)",
        ("vic-training-guarantee-2009", "sa-skills-for-all-2012", "qld-certificate-3-guarantee-2013"),
        "vet-contestable-funding",
        "enhancing",
        ("8101",),
        (
            C(("VIC",), 2010, 2012, ("SA", "QLD", "NSW")),
            C(("SA",), 2013, 2013, ("QLD", "NSW")),
            C(("QLD",), 2014, 2014, ("NSW",)),
        ),
        2008,
        "Staggered with not-yet-adopting states only: WA, Tasmania, the ACT and the NT have unchecked dates.",
    ),
    _new(
        "ndis-commission-2018-2020",
        "NDIS Quality and Safeguards Commission (NSW, SA 2018; five more 2019; WA 2020)",
        tuple(
            f"{s}-ndis-commission-{y}"
            for s, y in (
                ("nsw", 2018),
                ("sa", 2018),
                ("vic", 2019),
                ("qld", 2019),
                ("tas", 2019),
                ("act", 2019),
                ("nt", 2019),
            )
        ),
        "ndis-quality-safeguards",
        "mixed",
        ("8790",),
        (
            C(("NSW", "SA"), 2019, 2019, ("VIC", "QLD", "TAS", "ACT", "NT", "WA")),
            C(("VIC", "QLD", "TAS", "ACT", "NT"), 2020, 2020, ("WA",)),
        ),
        2013,
        "Staggered, not-yet-adopting states as controls; WA last (December 2020).",
        ("The NDIS full-scheme rollout by region (from July 2016) overlaps.",),
    ),
    _new(
        "ctp-2017-2020",
        "CTP insurance reforms (NSW 2017; SA price competition 2019; ACT 2020)",
        ("nsw-ctp-scheme-2017", "sa-ctp-price-competition-2019", "act-ctp-scheme-2020"),
        "ctp-insurance-competition",
        "enhancing",
        ("6322",),
        (
            C(("NSW",), 2018, 2019, ("VIC", "TAS", "QLD", "WA", "NT")),
            C(("SA", "ACT"), 2020, 2022, ("VIC", "TAS", "QLD", "WA", "NT")),
        ),
        2010,
        "Against states whose CTP markets did not change (public monopolies in Victoria, Tasmania, WA and the NT).",
    ),
    _new(
        "commercial-stamp-duty-2015-2018",
        "Commercial property stamp duty cut or abolished (SA from December 2015; ACT June 2018)",
        ("sa-commercial-stamp-duty-2015", "act-commercial-conveyance-duty-2018"),
        "commercial-property-transfer-tax",
        "enhancing",
        ("6712",),
        (
            C(("SA",), 2016, 2017, ("NSW", "VIC", "QLD", "WA", "TAS", "NT")),
            C(("ACT",), 2018, 2019, ("NSW", "VIC", "QLD", "WA", "TAS", "NT")),
        ),
        2010,
        "Each against states that kept commercial stamp duty (Victoria's 2024 change is after the window).",
    ),
    _new(
        "vic-gaming-venue-operator-2012",
        "Victorian gaming venue-operator model (August 2012)",
        ("vic-gaming-venue-operator-2012",),
        "gaming-market-structure",
        "mixed",
        ("4520", "4530"),
        (C(("VIC",), 2013, 2016, ALL_BUT("VIC")),),
        2008,
        "Victoria against all other states.",
    ),
    _new(
        "vic-late-night-freeze-lifted-2023",
        "Victorian freeze on late-night liquor licences lifted (July 2023)",
        ("vic-late-night-liquor-freeze-lifted-2023",),
        "liquor-licence-entry-restrictions",
        "enhancing",
        ("4520",),
        (C(("VIC",), 2024, 2025, ALL_BUT("VIC")),),
        2016,
        "Victoria against all other states; the freeze applied to four inner-Melbourne councils only.",
    ),
    _new(
        "nt-takeaway-moratorium-2017",
        "NT moratorium on new takeaway liquor licences (October 2017)",
        ("nt-takeaway-liquor-moratorium-2017",),
        "liquor-licence-entry-restrictions",
        "weakening",
        ("4123",),
        (C(("NT",), 2018, 2019, ("NSW", "VIC", "QLD", "SA", "WA", "TAS", "ACT")),),
        2010,
        "NT against all other states.",
    ),
)
REFORMS = REFORMS + NEW_REFORMS


# ---- data --------------------------------------------------------------------------------------------


@cache
def cabee(registered: bool) -> pd.DataFrame:
    if registered:
        return batch.cabee()
    p = pd.read_csv(batch.PANEL / "cabee_class_state_fy.csv.gz", dtype={"anzsic": str})
    p = p[p["measure"].isin(["start", "entries", "exits"]) & (p["band"] == "total")]
    return p.pivot_table(index=["fy", "state", "anzsic"], columns="measure", values="value").reset_index()


@cache
def fy_covariates(base_first_year: int) -> pd.DataFrame:
    """State x financial-year means of the quarterly controls (fy named by the year it ends)."""
    q = covariates.state_covariates(base_fy=base_first_year)
    q = q.assign(fy=q["period"].dt.year + (q["period"].dt.month >= 7))
    return q.groupby(["state", "fy"])[list(COVARIATES)].mean().reset_index()


def states_of(cohorts) -> list[str]:
    return sorted({s for c in cohorts for s in c.units})


def hide(df: pd.DataFrame, case) -> pd.DataFrame:
    """Delete the reform's treated cells from first exposure on (and treated states after their window)."""
    drop = pd.Series(False, index=df.index)
    for c in case.cohorts:
        in_tr = df["state"].isin(c.treated)
        drop |= in_tr & df["cls"].isin(case.classes) & (df["fy"] >= c.first_post)
        drop |= in_tr & (df["fy"] > c.last_post)
    return df[~drop]


def assert_blind(df: pd.DataFrame, case) -> None:
    for c in case.cohorts:
        bad = df["state"].isin(c.treated) & df["cls"].isin(case.classes) & (df["fy"] >= c.first_post)
        if bad.any():
            raise AssertionError(f"{case.id}: treated outcomes visible after first exposure")


def cell_panel(w: pd.DataFrame, case, measure: str) -> pd.DataFrame:
    base_fy = min(c.first_post for c in case.cohorts) - 1
    last = max(c.last_post for c in case.cohorts)
    d = w[(w["fy"] >= case.start) & (w["fy"] <= last) & w["state"].isin(states_of(case.cohorts))]
    d = d[(d["anzsic"].str.len() == 4) & (d["anzsic"] != "9999") & (d["start"] > 0)]
    national = d[d["fy"] == base_fy].groupby("anzsic")["start"].sum()
    keep = set(national[national >= MIN_CLASS_NATIONAL].index) | set(case.classes)
    d = d[d["anzsic"].isin(keep)]
    out = pd.DataFrame(
        {
            "cls": d["anzsic"].to_numpy(),
            "state": d["state"].to_numpy(),
            "fy": d["fy"].astype(int).to_numpy(),
            "y": 100 * d[measure].fillna(0).to_numpy(float) / d["start"].to_numpy(float),
            "w": d["start"].to_numpy(float),
        }
    )
    out["cell"] = out["cls"] + ":" + out["state"]
    base = out[out["fy"] == base_fy].set_index("cell")["w"]
    out["base"] = out["cell"].map(base).fillna(0.0)
    cov = fy_covariates(base_fy - 1)
    out = out.merge(cov, on=["state", "fy"], how="left")
    return hide(out, case).reset_index(drop=True)


# ---- estimators on one placebo assignment ----------------------------------------------------------------


def assign(df: pd.DataFrame, cohorts, classes) -> pd.DataFrame:
    d = np.zeros(len(df))
    for c in cohorts:
        on = df["state"].isin(c.treated) & df["cls"].isin(classes) & df["fy"].between(c.first_post, c.last_post)
        d[on.to_numpy()] = 1.0
    return df.assign(D=d)


def _matrix(
    df: pd.DataFrame, cohorts, start: int, cohort: Cohort, classes
) -> tuple[np.ndarray, np.ndarray, int, np.ndarray] | None:
    """Cells complete over the cohort's window: controls (untreated) then the treated group's average row."""
    years = list(range(start, cohort.last_post + 1))
    sub = df[df["state"].isin(cohort.units) & df["fy"].between(years[0], years[-1])]
    other_treated = {s for c in cohorts if c is not cohort for s in c.treated}
    sub = sub[~(sub["cls"].isin(classes) & sub["state"].isin(other_treated))]
    wide = sub.pivot(index="cell", columns="fy", values="y").reindex(columns=years)
    wide = wide.dropna()
    meta = sub.drop_duplicates("cell").set_index("cell").loc[wide.index]
    is_tr = meta["cls"].isin(classes) & meta["state"].isin(cohort.treated)
    ctrl = wide[~is_tr & (meta["base"] >= MIN_CELL)]
    tr = wide[is_tr]
    if tr.empty or len(ctrl) < 5:
        return None
    wts = meta.loc[is_tr, "base"].to_numpy(float)
    wts = wts if wts.sum() > 0 else np.ones(len(wts))
    row = np.average(tr.to_numpy(), axis=0, weights=wts)
    y = np.vstack([ctrl.to_numpy(), row])
    t0 = years.index(cohort.first_post)
    mask = np.zeros_like(y, bool)
    mask[-1, t0:] = True
    return y, mask, t0, wts


def synthetic(df: pd.DataFrame, cohorts, start: int, classes, method: str) -> float:
    ests, weights = [], []
    for c in cohorts:
        m = _matrix(df, cohorts, start, c, classes)
        if m is None:
            continue
        y, mask, t0, wts = m
        if t0 < 2:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            est = synth.sdid(y, mask).estimate if method == "sdid" else synth.gsynth(y, mask, rmax=3).att
        ests.append(est)
        weights.append(wts.sum() * (c.last_post - c.first_post + 1))
    return float(np.average(ests, weights=weights)) if ests else float("nan")


def estimate_all(df: pd.DataFrame, cohorts, start: int, classes, layers=LAYERS) -> dict[str, float]:
    d = assign(df, cohorts, classes)
    out: dict[str, float] = {}
    sat = ["cell", ("cls", "fy"), ("state", "fy")]
    for layer in layers:
        try:
            if layer == "twoway":
                out[layer] = panel.feols(d, "y", ["D"], fe=["cell", "fy"], weights="w").coef["D"]
            elif layer == "state_year":
                out[layer] = panel.feols(d, "y", ["D"], fe=["cell", ("state", "fy")], weights="w").coef["D"]
            elif layer == "saturated":
                out[layer] = panel.feols(d, "y", ["D"], fe=sat, weights="w").coef["D"]
            elif layer == "controls":
                dc = d.dropna(subset=list(COVARIATES))
                out[layer] = panel.feols(dc, "y", ["D", *COVARIATES], fe=["cell", "fy"], weights="w").coef["D"]
            elif layer == "imputation":
                imp = panel.imputation(d, "y", "D", fe=sat, weights="w", first_stage_weights=True, tol=1e-9)
                out[layer] = imp.att
            else:
                out[layer] = synthetic(d, cohorts, start, classes, layer)
        except (np.linalg.LinAlgError, ValueError, RuntimeError) as e:
            print(f"    {layer}: {type(e).__name__}: {e}", flush=True)
            out[layer] = float("nan")
    return {k: float(v) for k, v in out.items()}


# ---- placebo families on the reform's own classes -------------------------------------------------------


def state_draws(case, max_draws: int = MAX_OWN_DRAWS) -> list[tuple[Cohort, ...]]:
    """The reform's cohorts with their treated states replaced by states that never adopted it."""
    states = states_of(case.cohorts)
    real = {s for c in case.cohorts for s in c.treated}
    pool = [s for s in states if s not in real]
    sizes = [len(c.treated) for c in case.cohorts]
    choices: list[list[tuple[str, ...]]] = []

    def pick(i: int, left: list[str], acc: list[tuple[str, ...]]) -> None:
        if i == len(sizes):
            choices.append(acc)
            return
        for combo in itertools.combinations(left, sizes[i]):
            pick(i + 1, [s for s in left if s not in combo], [*acc, combo])

    pick(0, pool, [])
    if len(choices) > max_draws:
        keep = np.random.default_rng(SEED).choice(len(choices), size=max_draws, replace=False)
        choices = [choices[i] for i in sorted(keep)]
    out = []
    for choice in choices:
        fake = {s for combo in choice for s in combo}
        out.append(
            tuple(
                Cohort(combo, c.first_post, c.last_post, tuple(s for s in states if s not in fake))
                for combo, c in zip(choice, case.cohorts, strict=True)
            )
        )
    return out


def date_draws(
    cohorts, start: int, step: int = 1, min_pre: int = MIN_PRE_FAKE, first_year: dict | None = None
) -> list[tuple[Cohort, ...]]:
    """Each cohort moved back k = step, 2 x step, ... periods; its window cut before its real first exposure."""
    first_year = batch.FIRST_YEAR if first_year is None else first_year

    def first(c) -> int:  # first period with data for every treated state (NT business counts start in 2009-10)
        return max([start, *(first_year.get(s, start) for s in c.treated)])

    out, k = [], step
    while all(c.first_post - k - first(c) >= min_pre for c in cohorts):
        out.append(
            tuple(
                Cohort(c.treated, c.first_post - k, min(c.last_post - k, c.first_post - 1), c.controls) for c in cohorts
            )
        )
        k += step
    return out


def own_class_draws(case, **dates) -> dict[str, list[tuple[Cohort, ...]]]:
    real = tuple(case.cohorts)
    states = state_draws(case)
    both = [d for s in states for d in date_draws(s, case.start, **dates)]
    if len(both) > MAX_OWN_DRAWS:
        keep = np.random.default_rng(SEED).choice(len(both), size=MAX_OWN_DRAWS, replace=False)
        both = [both[i] for i in sorted(keep)]
    return {"states": states, "dates": date_draws(real, case.start, **dates), "states_dates": both}


def describe(cohorts) -> list[dict]:
    return [{"treated": list(c.treated), "first_post": c.first_post, "last_post": c.last_post} for c in cohorts]


# ---- study -------------------------------------------------------------------------------------------------


def registered_spread(case_id: str) -> dict[str, dict | None]:
    design = json.loads((BATCH / "design.json").read_text("utf-8"))
    row = next((c for c in design["cases"] if c["id"] == case_id), None)
    out: dict[str, dict | None] = {}
    for m in ("entries", "exits"):
        main = (row or {}).get(m) and row[m]["main"]
        out[m] = {"sd": main["placebo_sd"], "mde": main["mde_80"], "n": main["placebos"]} if main else None
    return out


def summarise(values: list[float]) -> dict:
    v = np.array([x for x in values if np.isfinite(x)])
    if len(v) < 2:
        return {"n": int(len(v)), "sd": None, "mde": None, "mean": None, "rms": None}
    sd = float(v.std(ddof=1))
    return {
        "n": int(len(v)),
        "sd": round(sd, 3),
        "mde": round(MDE_FACTOR * sd, 3),
        "mean": round(float(v.mean()), 3),
        "rms": round(float(np.sqrt((v**2).mean())), 3),
    }


def run_reform(r: Reform, max_placebos: int, families: tuple[str, ...] = ("industries", "own")) -> dict:
    case = r.case
    w = cabee(r.registered)
    if not batch.FIRST_YEAR:
        batch.FIRST_YEAR.update(cabee(True).groupby("state")["fy"].min().astype(int).to_dict())
    pg = batch.placebo_groups(w, case)
    reasons = []
    if pg["treated_size"] < batch.MIN_TREATED:
        reasons.append(
            f"treated group has {pg['treated_size']:.0f} businesses in the base year (rule: {batch.MIN_TREATED})"
        )
    if len(pg["groups"]) < batch.MIN_PLACEBOS:
        reasons.append(f"only {len(pg['groups'])} placebo groups (rule: {batch.MIN_PLACEBOS})")
    out = {
        "id": case.id,
        "title": case.title,
        "classes": list(case.classes),
        "cohorts": [c.__dict__ for c in case.cohorts],
        "start": case.start,
        "registered_vintage": r.registered,
        "notes": list(r.notes),
        "placebo_groups": min(len(pg["groups"]), max_placebos),
        "treated_size": pg["treated_size"],
        "feasible": {"ok": not reasons, "reasons": reasons},
        "registered_design": registered_spread(case.id) if r.registered else None,
        "outcomes": {},
    }
    if reasons:
        return out
    groups = pg["groups"][:max_placebos]
    own = own_class_draws(case) if "own" in families else {}
    for measure in ("entries", "exits"):
        df = cell_panel(w, case, measure)
        assert_blind(df, case)
        t = time.time()
        rows = [estimate_all(df, case.cohorts, case.start, g) for g in groups]
        res = layer_table(rows)
        fams = {}
        for name, draws in own.items():
            est = []
            for cohorts in draws:
                last = max(c.last_post for c in cohorts)
                est.append(estimate_all(df[df["fy"] <= last], cohorts, case.start, list(case.classes)))
            fams[name] = {
                "draws": len(draws),
                "layers": layer_table(est),
                "placebo_estimates": [
                    {k: round(v, 4) for k, v in row.items()} | {"cohorts": describe(c)}
                    for row, c in zip(est, draws, strict=True)
                ],
            }
        out["outcomes"][measure] = {
            "cells": int(df["cell"].nunique()),
            "rows": int(len(df)),
            "mean_rate": round(float(np.average(df["y"], weights=df["w"])), 2),
            "layers": res,
            "placebo_estimates": [
                {k: round(v, 4) for k, v in row.items()} | {"classes": g} for row, g in zip(rows, groups, strict=True)
            ],
            "families": fams,
        }
        print(
            f"  {measure}: {len(groups)} placebos, "
            + ", ".join(f"{k} {v['draws']}" for k, v in fams.items())
            + f" own-class draws in {time.time() - t:.0f}s; "
            + ", ".join(f"{k} {res[k]['mde']}" for k in LAYERS),
            flush=True,
        )
    return out


def layer_table(rows: list[dict[str, float]]) -> dict[str, dict]:
    res = {layer: summarise([row[layer] for row in rows]) for layer in LAYERS}
    base = res["twoway"]["sd"]
    for layer in LAYERS:
        sd = res[layer]["sd"]
        res[layer]["ratio_to_twoway"] = round(sd / base, 3) if sd is not None and base else None
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="one reform id")
    ap.add_argument("--max-placebos", type=int, default=MAX_PLACEBOS)
    ap.add_argument("--industries-only", action="store_true", help="skip the own-class placebo families")
    args = ap.parse_args()
    families = ("industries",) if args.industries_only else ("industries", "own")
    results = []
    for r in REFORMS:
        if args.only and r.case.id != args.only:
            continue
        print(r.case.id, flush=True)
        results.append(run_reform(r, args.max_placebos, families))
    report = {
        "plan": "docs/forward_plan_macro_controls.md (Phase 3)",
        "mode": "BLIND: treated cells hidden from first exposure; no reform effect estimated",
        "families": list(FAMILIES),
        "units": "percentage points of the entry or exit rate (per 100 businesses at the start of the year)",
        "mde": "2.8 x standard deviation of placebo estimates (80% power, 5% two-sided)",
        "layers": list(LAYERS),
        "reforms": results,
    }
    name = "power.json" if not args.only else f"check_{args.only}.json"
    (HERE / name).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {HERE / name}")


if __name__ == "__main__":
    main()
