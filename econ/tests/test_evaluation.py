"""Evaluation results: schema rules, cross-checks against the register, and the WA file's numbers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from regimpact.register.catalogue import load_records
from regimpact.register.evaluation import Evaluation, load_evaluations, write_evaluation

ANALYSIS = Path(__file__).resolve().parents[1] / "analyses" / "wa_trading_hours"


def minimal(**over) -> dict:
    """An ILLUSTRATIVE evaluation (not a real result)."""
    base = {
        "id": "illustrative-eval",
        "title": "Illustrative",
        "records": ["wa-trading-hours-weeknight-2010"],
        "family": "retail-trading-hours",
        "evaluated_on": "2026-10-15",
        "hypothesis": "enhancing",
        "design": "x",
        "comparison": "x",
        "window": "x",
        "verdict": "inconclusive",
        "finding_label": "No detectable effect",
        "grade": "Moderate",
        "grade_reason": "x",
        "headline": "x",
        "category_summaries": {"competition": "x"},
        "preregistered": True,
        "outcomes": [
            {
                "id": "entry-rate",
                "label": "Entry",
                "category": "competition",
                "role": "primary",
                "unit": "per 100",
                "estimate": 1.0,
                "interval": {"low": -1.0, "high": 3.0},
                "no_effect_range": {"low": -2.0, "high": 2.0, "basis": "x"},
                "inference": "x",
                "finding": "no-detectable-effect",
                "preregistered": True,
            }
        ],
        "built_by": "x",
    }
    base.update(over)
    return base


def test_schema_rejects_inverted_intervals_and_unknown_event_outcomes():
    bad = minimal()
    bad["outcomes"][0]["interval"] = {"low": 3.0, "high": -1.0}
    with pytest.raises(ValidationError):
        Evaluation.model_validate(bad)
    with pytest.raises(ValidationError, match="unknown outcomes"):
        Evaluation.model_validate(
            minimal(
                event_studies=[
                    {
                        "outcome": "nope",
                        "title": "x",
                        "unit": "x",
                        "reference": "x",
                        "points": [{"period": "a", "k": 0, "estimate": 0}, {"period": "b", "k": 1, "estimate": 1}],
                    }
                ]
            )
        )


def test_loader_checks_records_family_and_file_name(tmp_path):
    records = load_records().records
    write_evaluation(Evaluation.model_validate(minimal(records=["no-such-record"])), tmp_path)
    write_evaluation(
        Evaluation.model_validate(minimal(id="other", records=["nsw-rideshare-2015"], family="retail-trading-hours")),
        tmp_path,
    )
    (tmp_path / "renamed.json").write_text(json.dumps(minimal(id="mismatch")), encoding="utf-8")
    problems = " | ".join(load_evaluations(records, tmp_path).problems)
    assert "unknown record 'no-such-record'" in problems
    assert "'nsw-rideshare-2015' is not in family" in problems
    assert "file name must match id 'mismatch'" in problems


def test_the_register_evaluations_load_cleanly():
    records = load_records().records
    result = load_evaluations(records)
    assert result.problems == []
    assert {e.id for e in result.evaluations} >= {"wa-trading-hours-2010-2012"}


def test_wa_evaluation_numbers_match_the_analysis_outputs():
    """The evaluation file must be the builder's output, not hand-edited."""
    est = json.loads((ANALYSIS / "estimate.json").read_text(encoding="utf-8"))
    post = json.loads((ANALYSIS / "posthoc.json").read_text(encoding="utf-8"))
    ev = next(e for e in load_evaluations().evaluations if e.id == "wa-trading-hours-2010-2012")
    out = {o.id: o for o in ev.outcomes}
    for oid, m in (("entry-rate", "entries"), ("exit-rate", "exits")):
        p = est[m]["primary"]
        assert out[oid].estimate == p["delta"]
        assert [out[oid].interval.low, out[oid].interval.high] == p["interval_90"]
        assert out[oid].p_value == p["p_industry_placebo"]
        assert out[oid].grade == est[m]["grade"]["grade"]
    food = est["prices"]["Food and non-alcoholic beverages"]
    assert out["food-prices"].estimate == food["estimate_log_points"]
    trend = post["food_price_trend_check"]["after_removing_each_citys_pre_reform_trend"]
    assert out["food-prices-detrended"].estimate == trend
    assert not out["food-prices-detrended"].preregistered
    desc = est["descriptive_productivity_and_pay"]
    assert out["output-per-worker"].estimate == desc["gva_per_worker"]["estimate_log_points"]
    assert out["real-pay-per-worker"].estimate == desc["real_coe_per_worker"]["estimate_log_points"]
    net = est["entries"]["event_study"]["net"]
    entries_es = next(e for e in ev.event_studies if e.outcome == "entry-rate")
    assert {str(p.k): p.estimate for p in entries_es.points if p.k != -1} == net
    assert ev.verdict == "inconclusive" and ev.grade == est["entries"]["grade"]["grade"]


def test_batch_evaluations_match_the_registered_run():
    """Each high-evaluability evaluation file must equal estimate.json, case by case."""
    est = json.loads((ANALYSIS.parent / "high_evaluability" / "estimate.json").read_text(encoding="utf-8"))
    evs = {e.id: e for e in load_evaluations().evaluations}
    assert est["mode"].startswith("UNBLINDED")
    for r in est["cases"]:
        ev = evs[r["id"]]
        assert ev.grade == r["grade"]
        assert ev.verdict == ("not-identified" if r["grade"] == "Not identified" else r["verdict"])
        out = {o.id: o for o in ev.outcomes}
        for oid, m in (("entry-rate", "entries"), ("exit-rate", "exits")):
            if r[m] is None:
                assert oid not in out
                continue
            main = r[m]["main"]
            assert out[oid].estimate == main["estimate"] and out[oid].p_value == main["p"]
            assert [out[oid].interval.low, out[oid].interval.high] == main["interval_90"]
        for var, oid in (("gva_per_worker", "output-per-worker"), ("real_coe_per_worker", "real-pay-per-worker")):
            assert out[oid].estimate == r["productivity"][var]["estimate"]
        if r["prices"]:
            prices = [o for o in ev.outcomes if o.category == "prices" and not o.id.endswith("-detrended")]
            assert sorted(o.estimate for o in prices) == sorted(v["estimate"] for v in r["prices"]["classes"].values())
