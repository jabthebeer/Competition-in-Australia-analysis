"""Phase 3 power study: blinding and placebo assignment (ILLUSTRATIVE rows)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parents[1] / "analyses" / "power_study" / "run.py"


@pytest.fixture(scope="module")
def study():
    spec = importlib.util.spec_from_file_location("power_study_run", HERE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["power_study_run"] = mod
    spec.loader.exec_module(mod)
    return mod


def _rows():
    return pd.DataFrame(
        [
            {"cls": c, "state": s, "fy": y, "y": 1.0, "w": 10.0}
            for c in ("4110", "9000")
            for s in ("WA", "NSW")
            for y in range(2008, 2014)
        ]
    )


def test_hide_removes_treated_cells_from_first_exposure(study):
    case = next(r.case for r in study.REFORMS if r.case.id == "wa-trading-hours-weeknight-2010")
    out = study.hide(_rows(), case)
    wa_treated = out[(out["state"] == "WA") & (out["cls"] == "4110")]
    assert wa_treated["fy"].max() == 2010  # 2010-11 on hidden
    assert out.loc[out["state"] == "WA", "fy"].max() == 2012  # nothing after the window in WA
    assert (out[(out["state"] == "NSW") & (out["cls"] == "4110")]["fy"].max()) == 2013
    study.assert_blind(out, case)
    with pytest.raises(AssertionError):
        study.assert_blind(_rows(), case)


def test_placebo_assignment_marks_only_placebo_cells_in_treated_states_and_window(study):
    case = next(r.case for r in study.REFORMS if r.case.id == "wa-trading-hours-weeknight-2010")
    d = study.assign(study.hide(_rows(), case), case.cohorts, ["9000"])
    on = d[d["D"] == 1]
    assert set(on["cls"]) == {"9000"} and set(on["state"]) == {"WA"} and set(on["fy"]) == {2011, 2012}


def test_fake_dates_end_before_real_exposure_and_keep_two_earlier_years(study):
    for r in study.REFORMS:
        case = r.case
        for cohorts in study.date_draws(case.cohorts, case.start):
            for fake, real in zip(cohorts, case.cohorts, strict=True):
                assert fake.treated == real.treated
                assert fake.first_post <= fake.last_post < real.first_post
                assert fake.first_post - case.start >= study.MIN_PRE_FAKE


def test_placebo_states_never_include_a_state_that_adopted(study):
    for r in study.REFORMS:
        real = {s for c in r.case.cohorts for s in c.treated}
        for cohorts in study.state_draws(r.case):
            fake = [s for c in cohorts for s in c.treated]
            assert not set(fake) & real
            assert len(fake) == len(set(fake))  # disjoint across cohorts
            for c in cohorts:
                assert not set(c.controls) & set(fake)
