"""The cost of a licence for the business that holds it (phase 8 of the levers re-evaluation, DECISIONS E-173)."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest

from alicia.register.requirements import load_requirements

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("licence_costs", ROOT / "alicia" / "scripts" / "licence_costs.py")
LC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LC)


@pytest.fixture(scope="module")
def data():
    return LC.load()


def test_every_licence_is_a_requirement_with_sourced_fees(data):
    reqs = {q.id: q for q in load_requirements().requirements}
    assert data["items"], "no licences costed"
    for rid, item in data["items"].items():
        assert rid in reqs and reqs[rid].kind in ("licence", "registration"), rid
        assert int(item["renewal_years"]) >= 1
        whens = {f["when"] for f in item["fees"]}
        assert whens <= {"entry", "renewal"} and "entry" in whens, rid
        for f in item["fees"]:
            assert ("amount" in f) != ("fee_units" in f), f"{rid}: a fee is either dollars or fee units"
            assert len(f["source"]["quote"]) >= 20 and f["source"]["url"].startswith("https://"), rid
            if "fee_units" in f:
                assert reqs[rid].jurisdiction in data["fee_units"], f"{rid}: no fee unit value for its jurisdiction"
        if "fee_rounding" in item:
            assert item["fee_rounding"]["rule"] == "qld-tiered" and reqs[rid].jurisdiction == "QLD", rid
            assert "Rounding of amounts expressed as numbers of fee units" in item["fee_rounding"]["source"]["quote"]
    for rid in data.get("not_costed", {}):
        assert rid in reqs and rid not in data["items"], rid
    for when in ("entry", "renewal"):
        h = data["assumed_hours"][when]
        assert 0 < h["low"] <= h["central"] <= h["high"]


def test_fee_units_convert_as_the_law_says():
    units = {"QLD": {"value": 1.133}, "NT": {"value": 1.49, "round": "down-to-dollar"}}
    assert LC.dollars({"fee_units": 442.60}, "QLD", units) == 501.47
    # NT: 124 revenue units at $1.49 is $184.76, rounded down to $184 (Revenue Units Act 2009 s 3(2)).
    assert LC.dollars({"fee_units": 124}, "NT", units) == 184.0
    assert LC.dollars({"amount": 290.0}, "WA", units) == 290.0
    # Queensland regulations that round in tiers (for example the Liquor Regulation 2002 s 36DA): to the dollar over
    # $1,000, to 10 cents over $100, to 5 cents up to $100, one-half rounding up.
    assert LC.dollars({"fee_units": 1471}, "QLD", units, "qld-tiered") == 1667.0  # $1,666.64
    assert LC.dollars({"fee_units": 735.30}, "QLD", units, "qld-tiered") == 833.1  # $833.09
    assert LC.dollars({"fee_units": 60}, "QLD", units, "qld-tiered") == 68.0  # $67.98
    with pytest.raises(ValueError):  # the quoted rule stops at $5,000
        LC.dollars({"fee_units": 5000}, "QLD", units, "qld-tiered")


def test_the_labour_rate_is_the_frameworks_work_rate():
    # Regulatory Burden Measurement Framework (July 2026) p. 12, as the burden calculator records it.
    assert LC.work_rate() == 91.54


def test_the_burden_counts_renewals_within_ten_years():
    assert [LC.renewals(k) for k in (1, 2, 3, 5)] == [9, 4, 3, 1]
    # 4 hours to apply and 1 hour a year to renew: (4 + 9) x 91.54 / 10
    assert LC.burden_formula(4, 1, 1, 91.54) == 119.0


def test_the_published_costs_are_current():
    """The CSV matches a rebuild from the input file (the calculator and the formula agree, so no Node is needed)."""
    rows = LC.build(use_calculator=False)
    with LC.OUT.open(encoding="utf-8") as fh:
        published = list(csv.DictReader(fh))
    assert [r["requirement"] for r in published] == [r["requirement"] for r in rows]
    for p, r in zip(published, rows, strict=True):
        for k in LC.FIELDS:
            want = r[k]
            got = p[k]
            assert (float(got) == pytest.approx(float(want))) if isinstance(want, (int, float)) else got == want, (
                f"{r['requirement']} {k}: regenerate with: uv run python scripts/licence_costs.py"
            )
    # Entry is the entry fees plus the staff time to apply; renewal per year spreads a renewal over its years.
    for r in rows:
        assert r["entry_total"] == pytest.approx(r["entry_fees"] + r["entry_hours"] * 91.54, abs=0.01)
        if r["renewal_total"] != "":  # blank where the regulator works the renewal fee out for each licensee
            assert r["renewal_total_per_year"] == pytest.approx(r["renewal_total"] / r["renewal_years"], abs=0.01)


def test_the_levers_page_and_register_data_show_each_cost():
    """Each costed licence carries its cost on Legislative levers, as a row or inside its item, and in Register data
    (DECISIONS E-175). Costs sit beside severity: the requirement's severity is the same with or without them."""
    import datetime as dt

    from alicia.menu import licencecost, registerdata
    from alicia.menu.explorer import build_payload
    from alicia.register.catalogue import load_records

    costs = licencecost.load()
    assert set(costs) == {r["requirement"] for r in LC.build(use_calculator=False)}
    records = load_records().records
    menu = build_payload(records, generated=dt.date(2026, 11, 16), licence_costs=costs)
    every = menu["records"] + [q for r in menu["records"] for q in r.get("requirements", [])]
    shown = {r["id"]: r for r in every if r.get("licenceCost")}
    assert set(shown) == set(costs)
    assert menu["licenceCostCount"] == len(costs) and "beside" in menu["licenceCostNote"]
    nested = {q["id"] for r in menu["records"] for q in r.get("requirements", [])}
    assert "qld-security-licence" in nested and shown["qld-security-licence"]["licenceCost"]["entryTotal"] > 0
    for rid, r in shown.items():
        c = r["licenceCost"]
        assert c["sources"] and all(s["url"].startswith("https://") for s in c["sources"]), rid
        assert c["entryLow"] <= c["entryTotal"] <= c["entryHigh"], rid
    bare = build_payload(records, generated=dt.date(2026, 11, 16), licence_costs={})
    bare_every = {q["id"]: q for q in bare["records"] + [q for r in bare["records"] for q in r.get("requirements", [])]}
    assert all(bare_every[rid]["severity"] == r["severity"] for rid, r in shown.items())
    rows = {x["id"]: x for x in registerdata.payload(menu)["rows"]}
    for rid, c in costs.items():
        assert rows[rid]["entryCost"] == c["entryTotal"] and rows[rid]["burdenYear"] == c["burden"], rid
    assert rows["nsw-liquor-licence"]["renewalCostYear"] is None  # the regulator does not publish the fee
