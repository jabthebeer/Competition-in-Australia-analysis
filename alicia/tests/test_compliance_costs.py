"""Compliance cost: the staff time each requirement costs the businesses it binds, a year (DECISIONS E-500)."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from alicia.costing import compliance as C
from alicia.menu import compliancecost as CC
from alicia.menu import exposure as X
from alicia.register.requirements import load_requirements

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("compliance_costs", ROOT / "alicia" / "scripts" / "compliance_costs.py")
SCRIPT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCRIPT)


@pytest.fixture(scope="module")
def published():
    with SCRIPT.OUT.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_the_published_costs_are_current():
    """The committed CSVs and methods note match a rebuild from the requirements, assumptions and counts."""
    for path, text in SCRIPT.build().items():
        assert path.read_text("utf-8") == text, f"{path.name} is out of date: run scripts/compliance_costs.py"


def test_every_requirement_has_a_row_and_a_reason_when_not_costed(published):
    ids = sorted(q.id for q in load_requirements().requirements)
    assert [r["requirement"] for r in published] == ids
    for r in published:
        assert (r["costed"] == "yes") != bool(r["why_not"]), r["requirement"]
        if r["tier"] == "local" or r["kind"] == "other":
            assert r["costed"] == "no", r["requirement"]


def test_every_figure_follows_from_its_working(published):
    """Cost = rate × (hours to start × new businesses + hours each year × businesses), in each scenario."""
    for r in [x for x in published if x["costed"] == "yes"]:
        rate = float(r["rate"])
        assert rate == 91.54
        for s in ("_low", "", "_high"):
            want = rate * (
                float(r[f"start_hours{s}"]) * int(r["new_per_year"])
                + float(r[f"yearly_hours{s}"]) * int(r["businesses"])
            )
            # Counts are rounded to whole businesses in the CSV, so allow a dollar a business of slack.
            slack = rate * (float(r[f"start_hours{s}"]) + float(r[f"yearly_hours{s}"])) + 1
            assert abs(float(r[f"cost{s}"]) - want) <= slack, r["requirement"]
        assert float(r["cost_low"]) <= float(r["cost"]) <= float(r["cost_high"]), r["requirement"]


def test_hours_are_ordered_and_every_kind_is_covered():
    a = C.load_assumptions()
    from alicia.register.requirements import KIND_LABELS

    assert set(a["kinds"]) == set(KIND_LABELS)
    for k, v in a["kinds"].items():
        if v.get("costed") is False:
            continue
        for when in ("start_hours", "yearly_hours"):
            assert 0 <= v[when]["low"] <= v[when]["central"] <= v[when]["high"], k
        assert v["basis"].startswith("Assumed"), k


def test_licences_take_their_hours_and_renewal_period_from_the_licence_costs(published):
    rows = {r["requirement"]: r for r in published}
    with (ROOT / "data" / "processed" / "legislation" / "licence_costs.csv").open(encoding="utf-8") as fh:
        for lic in csv.DictReader(fh):
            r = rows[lic["requirement"]]
            if r["costed"] != "yes":
                continue
            assert r["hours_from"] == "licence"
            assert float(r["start_hours"]) == float(lic["entry_hours"])
            assert float(r["yearly_hours"]) == pytest.approx(float(lic["renewal_hours"]) / int(lic["renewal_years"]))


def test_an_employer_rule_counts_only_employers_and_upper_bounds_are_flagged(published):
    reqs = {q.id: q for q in load_requirements().requirements}
    for r in [x for x in published if x["costed"] == "yes"]:
        q = reqs[r["requirement"]]
        basis, size_upper = X.size_basis(q.triggers)
        assert r["size_basis"] == basis, r["requirement"]
        if size_upper or X.conditional(q) or X.form_limited(q):
            assert r["upper_bound"] == "yes", r["requirement"]


def test_a_wide_upper_bound_is_not_counted(published):
    for r in published:
        if r["costed"] == "yes" and r["upper_bound"] == "yes":
            assert float(r["share_pct"]) < 25, r["requirement"]


def test_the_counts_are_recounted_from_the_abs_file():
    """One requirement's businesses, recounted from the CABEE panel by another route."""
    q = next(q for q in load_requirements().requirements if q.id == "qld-builder-licence")
    df = pd.read_parquet(ROOT / "data" / "processed" / "abs_cabee" / "class_state_fy.parquet")
    df = df[(df["geo_code"] == "QLD") & (df["breakdown"] == "") & (df["period"] == df["period"].max())]
    classes = {c for c, _ in X.requirement_pairs(q)}
    end = df[(df["measure"] == "businesses_end") & df["industry_code"].isin(classes)]["value"].sum()
    new = df[(df["measure"] == "entries") & df["industry_code"].isin(classes)]["value"].sum()
    row = C.cost_requirement(q, C.load_flows(), C.load_assumptions(), C.load_licences(), 91.54)[0]
    # The ABS perturbs cells, so the bands need not add exactly to the total.
    assert row["businesses"] == pytest.approx(end, rel=0.02)
    assert row["newPerYear"] == pytest.approx(new, rel=0.05)


def test_fees_are_shown_beside_the_figure_never_in_it():
    q = next(q for q in load_requirements().requirements if q.id == "qld-builder-licence")
    row = C.cost_requirement(q, C.load_flows(), C.load_assumptions(), C.load_licences(), 91.54)[0]
    assert row["feesTotal"] > 0
    staff = 91.54 * (
        row["startHours"]["central"] * row["newPerYear"] + row["yearlyHours"]["central"] * row["businesses"]
    )
    assert row["cost"]["central"] == pytest.approx(staff, rel=1e-3)


def test_an_items_cost_is_the_sum_of_its_requirements():
    costs = {
        "a": {"costed": True, "upper": False, "businesses": 10, "cost": {"low": 1.0, "central": 2.0, "high": 3.0}},
        "b": {"costed": True, "upper": True, "businesses": 20, "cost": {"low": 1.0, "central": 1.0, "high": 1.0}},
        "c": {"costed": False, "why": "x"},
    }
    out = CC.record_totals(costs, {"rec": ["a", "b", "c"], "none": ["c"]})
    assert out["rec"]["cost"] == {"low": 2.0, "central": 3.0, "high": 4.0}
    assert out["rec"]["upper"] and out["rec"]["requirements"] == 2 and out["rec"]["of"] == 3
    assert "none" not in out


def test_money_is_shown_to_two_significant_figures():
    assert C.money(3_123_456) == "$3.1 million"
    assert C.money(14_200_000_000) == "$14 billion"
    assert C.money(366.16) == "$370"
    assert C.money(2_000_000_000) == "$2 billion"


def test_the_site_shows_the_cost_without_changing_severity_or_class():
    import datetime as dt

    from alicia.menu.explorer import build_payload
    from alicia.register.catalogue import load_records

    records = load_records().records

    def rows(menu):
        out = {}
        for r in menu["records"]:
            out[r["id"]] = r
            for q in r.get("requirements") or []:
                out[q["id"]] = q
        return out

    with_cost = build_payload(records, generated=dt.date(2026, 11, 27))
    a = rows(with_cost)
    b = rows(build_payload(records, generated=dt.date(2026, 11, 27), compliance_costs={}))
    assert a["qld-builder-licence"]["complianceCost"]["costed"]
    for k in a:
        assert a[k].get("impactClass") == b[k].get("impactClass"), k
        assert a[k].get("severity") == b[k].get("severity"), k
    assert with_cost["complianceCostCount"] > 900
