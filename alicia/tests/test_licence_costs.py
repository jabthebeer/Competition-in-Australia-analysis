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
    for when in ("entry", "renewal"):
        h = data["assumed_hours"][when]
        assert 0 < h["low"] <= h["central"] <= h["high"]


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
        assert r["renewal_total_per_year"] == pytest.approx(r["renewal_total"] / r["renewal_years"], abs=0.01)
