"""Compliance cost: the staff time each requirement costs the businesses it binds, a year (DECISIONS E-700)."""

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
        if r["counts_from"] != "abs":
            continue  # a regulator's list of the entities bound: counted exactly (E-701)
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


def test_a_sourced_costing_follows_its_source_and_counts_the_entities_listed(published):
    """FAR (E-701): BEAR's $11.5 million a year for 149 ADIs, an entity, for the 329 entities APRA lists."""
    a = C.load_assumptions()
    o = a["overrides"]["cth-financial-accountability-regime"]
    sc = o["source_cost"]
    hours = sc["cost_a_year"] / sc["entities"] / C.work_rate()
    assert o["yearly_hours"]["central"] == pytest.approx(hours, abs=0.05)
    assert o["yearly_hours"]["low"] == pytest.approx(hours * sc["range"]["low"], abs=0.05)
    assert o["yearly_hours"]["high"] == pytest.approx(hours * sc["range"]["high"], abs=0.05)
    r = next(x for x in published if x["requirement"] == "cth-financial-accountability-regime")
    assert r["hours_from"] == "override" and r["upper_bound"] == "no" and r["evidence"] == "analogue"
    assert int(r["businesses"]) == sum(g["count"] for g in o["entities"]["groups"]) == 329
    assert r["counts_from"] == o["entities"]["label"]
    # Every class it is spread over is one the requirement reaches, and the classes add up to its cost.
    q = next(q for q in load_requirements().requirements if q.id == r["requirement"])
    reach = {c for c, _ in X.requirement_pairs(q)}
    _, by_class = C.cost_requirement(q, C.load_flows(), a, C.load_licences(), C.work_rate())
    assert set(by_class) <= reach
    assert sum(v["central"] for v in by_class.values()) == pytest.approx(float(r["cost"]), rel=1e-6)


def test_every_costing_card_is_well_formed():
    """Each card (E-702) points at a requirement or family on the register, says how good its evidence is, and
    quotes a source."""
    reqs = load_requirements().requirements
    ids, families = {q.id for q in reqs}, {q.family for q in reqs}
    by_req, by_family = C.load_cards()
    assert by_req, "the FAR card is missing"
    for key, card in [*by_req.items(), *by_family.items()]:
        assert key in (ids if key in by_req else families), card["file"]
        assert card["evidence"] in ("sourced", "analogue"), card["file"]
        assert card["basis"] and card["task"], card["file"]
        assert ("source_cost" in card) or ("yearly_hours" in card), card["file"]
        for when in ("start_hours", "yearly_hours"):
            h = card[when]
            assert 0 <= h["low"] <= h["central"] <= h["high"], card["file"]
        assert card["sources"], card["file"]
        for s in card["sources"]:
            assert s["url"].startswith("https://") and s["quote"] and s["locator"] and s["accessed"], card["file"]
        assert card["review"]["status"] in ("draft", "checked"), card["file"]


def test_a_family_card_costs_each_member_and_counts_only_its_states(tmp_path):
    """A card for a family applies to every member without a card of its own; a group limited to some states
    counts only for those states' requirements."""
    q = next(q for q in load_requirements().requirements if q.id == "qld-builder-licence")
    card = {
        "applies_to": {"family": q.family},
        "evidence": "sourced",
        "task": "t",
        "basis": "b",
        "start_hours": {"low": 0, "central": 0, "high": 0},
        "yearly_hours": {"low": 1, "central": 2, "high": 3},
        "entities": {
            "label": "holders",
            "source": {},
            "note": "",
            "groups": [
                {"name": "Qld", "count": 100, "classes": ["3020"], "states": ["QLD"]},
                {"name": "NSW", "count": 900, "classes": ["3020"], "states": ["NSW"]},
            ],
        },
        "sources": [],
        "review": {"status": "draft"},
    }
    (tmp_path / "x.json").write_text(__import__("json").dumps(card))
    a = C.load_assumptions(cards=tmp_path)
    assert q.family in a["families"] and not a["overrides"]
    row, by_class = C.cost_requirement(q, C.load_flows(), a, C.load_licences(), 91.54)
    assert row["evidence"] == "sourced" and row["businesses"] == 100 and not row["upper"]
    assert row["cost"]["central"] == pytest.approx(2 * 91.54 * 100)
    assert set(by_class) == {"3020"}


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


def test_a_kinds_default_frequency_reproduces_its_hours_each_year():
    """With no frequency in its words, a requirement costs what the kind's hours say (E-703)."""
    a = C.load_assumptions()
    for k, v in a["tasks"]["kinds"].items():
        for s in ("low", "central", "high"):
            assert v["hours_a_time"][s] * v["times_a_year"] == pytest.approx(a["kinds"][k]["yearly_hours"][s]), k


def test_frequency_is_read_from_the_requirements_own_words():
    from types import SimpleNamespace as NS

    rules = C.load_assumptions()["tasks"]

    def q(what, quote="x" * 20):
        return NS(what=what, title="t", sources=[NS(locator="s 1", title="Act", quote=quote)])

    assert C.frequency(q("Pay gaming machine tax each month on the premises."), rules)["times"] == 12
    assert C.frequency(q("Pay the levy in quarterly instalments."), rules)["times"] == 4
    assert C.frequency(q("Lodge a report each financial year."), rules)["times"] == 1
    assert C.frequency(q("Renew it.", "a check conducted at least every 5 years"), rules)["times"] == 0.2
    # A frequency word that describes something else is not a frequency.
    assert C.frequency(q("Comply once annual turnover passes $3 million."), rules) is None
    assert C.frequency(q("Charge a monthly fee of at most 4%."), rules) is None
    # The 'what' wins over the quotes.
    f = C.frequency(q("Pay tax each month.", "an annual return"), rules)
    assert f["times"] == 12 and f["where"] == "what"


def test_a_calculated_figure_uses_the_frequency_it_quotes(published):
    a = C.load_assumptions()
    rows = [r for r in published if r["evidence"] == "calculated"]
    assert rows
    for r in rows:
        task = a["tasks"]["kinds"][r["kind"]]
        assert float(r["yearly_hours"]) == pytest.approx(task["hours_a_time"]["central"] * float(r["times_a_year"]))
        assert r["frequency_phrase"] and r["frequency_from"], r["requirement"]
