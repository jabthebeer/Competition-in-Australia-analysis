"""Evaluation results: schema rules, cross-checks against the register, and the WA file's numbers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from alicia.register.catalogue import load_records
from alicia.register.evaluation import Evaluation, load_evaluations, write_evaluation

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


def test_weeknight_reevaluation_matches_the_registered_run():
    """The 2010 weeknight re-evaluation file must equal its estimate.json and follow the first evaluation."""
    folder = ANALYSIS.parent / "wa_weeknight_2010"
    est = json.loads((folder / "estimate.json").read_text(encoding="utf-8"))
    evs = {e.id: e for e in load_evaluations().evaluations}
    ev = evs["wa-trading-hours-weeknight-2010-new-data"]
    assert not est["blind"] and est["null_matches_design_stage"]
    assert ev.follows == "wa-trading-hours-2010-2012" and ev.follows in evs
    out = {o.id: o for o in ev.outcomes}
    for oid, res in (("retail-businesses-perth", est["C"]), ("general-retail-turnover", est["A"])):
        o = out[oid]
        assert (o.estimate, o.p_value, o.mde_80) == (res["estimate"], res["p"], res["null"]["mde_80"])
        assert [o.interval.low, o.interval.high] == res["interval_90"]
        assert (o.no_effect_range.low, o.no_effect_range.high) == (res["null"]["q05"], res["null"]["q95"])
        assert o.finding == res["finding"]
    hours = est["B_descriptive"]["hours"]
    assert out["general-retail-hours"].estimate == hours["estimate"]
    assert out["general-retail-hours"].finding == "descriptive-only"
    es = {e.outcome: e for e in ev.event_studies}
    assert [p.estimate for p in es["retail-businesses-perth"].points] == [
        p["estimate"] for p in est["C"]["event_study"]
    ]
    assert [p.estimate for p in es["general-retail-turnover"].points] == [
        p["estimate"] for p in est["A"]["event_study"]
    ]
    verdict = "inconclusive" if est["C"]["finding"] == "no-detectable-effect" else None
    assert ev.verdict == verdict


def test_current_evaluation_prefers_the_follow_up():
    from alicia.register.evaluation import current_evaluation

    evs = load_evaluations().evaluations
    current = current_evaluation(evs)
    # The Phase 5 re-evaluation (same day, with a recorded run time) is now the current one for both WA records;
    # the evaluation it supersedes is archived and never current.
    assert current["wa-trading-hours-weeknight-2010"] == "wa-trading-hours-2010-2012-phase5"
    assert current["wa-trading-hours-sunday-2012"] == "wa-trading-hours-2010-2012-phase5"
    assert current["cth-nqf-childcare-2012"] == "childcare-nqf-2012-phase5"
    assert "wa-trading-hours-2010-2012" not in current.values()


def test_phase5_evaluations_match_the_registered_run():
    """Each Phase 5 evaluation file must equal its specification's estimate.json and archive what it supersedes."""
    from alicia.register.evaluation import archived
    from alicia.runner.spec import load

    evs = {e.id: e for e in load_evaluations().evaluations}
    arch = archived(evs.values())
    for spec_id, folder in (("phase5-reevaluations", "reevaluations"), ("phase5-new-families", "new_families")):
        spec = load(spec_id)
        est = json.loads((ANALYSIS.parent / "phase5" / folder / "estimate.json").read_text(encoding="utf-8"))
        assert est["mode"].startswith("UNBLINDED")
        for case in spec.cases:
            res = next(c for c in est["cases"] if c["id"] == case["id"])
            ev = evs[case["id"]]
            assert (ev.verdict, ev.grade) == (res["verdict"], res["grade"]), ev.id
            assert ev.supersedes == tuple(case["supersedes"]) and ev.follows == case["follows"]
            assert all(arch[old] == ev.id for old in ev.supersedes)
            assert ev.evaluated_at is not None and ev.id not in arch
            out = {o.id: o for o in ev.outcomes}
            rows = [(r.outcome, r.layer) for r in ev.estimators]
            assert len(rows) == len(set(rows)), ev.id
            for o in case["outcomes"]:
                r = res["outcomes"][o["key"]]
                reg = r["registered"]
                oid = o["key"] if o["kind"] == "price" else {"entries": "entry-rate", "exits": "exit-rate"}[o["key"]]
                got = out[oid]
                assert (got.estimate, got.p_value, got.mde_80) == (reg["estimate"], reg["p"], reg["mde_80"])
                assert [got.interval.low, got.interval.high] == reg["interval_90"]
                assert got.role == o["role"] and got.preregistered
                layers = {x.layer: x for x in ev.estimators if x.outcome == oid}
                assert set(layers) == set(r["layers"]), (ev.id, oid)
                assert [k for k, x in layers.items() if x.registered] == [o["layer"]]
                assert all(layers[k].estimate == v["estimate"] for k, v in r["layers"].items())
                if r["pre_inside_95"] is False:
                    assert got.finding == "not-identified"


def test_nqf_wa_evaluation_matches_the_registered_run():
    """The NQF-in-WA evaluation file must equal its estimate.json and follow the batch evaluation."""
    folder = ANALYSIS.parent / "childcare_nqf_wa"
    est = json.loads((folder / "estimate.json").read_text(encoding="utf-8"))
    paths = json.loads((folder / "paths.json").read_text(encoding="utf-8"))
    evs = {e.id: e for e in load_evaluations().evaluations}
    ev = evs["childcare-nqf-wa-delay-2012"]
    assert not est["blind"] and est["null_matches_design_stage"]
    assert ev.follows == "childcare-nqf-2012"
    out = {o.id: o for o in ev.outcomes}
    for oid, key in (("childcare-exits", "exits"), ("child-care-prices", "prices"), ("childcare-entries", "entries")):
        r = est[key]["main"]["pooled"]
        o = out[oid]
        assert (o.estimate, o.p_value, o.mde_80) == (r["estimate"], r["p"], r["null"]["mde_80"])
        assert [o.interval.low, o.interval.high] == r["interval_90"]
    assert out["childcare-exits"].finding == est["exits"]["main"]["pooled"]["finding"]
    assert {o.finding for o in ev.outcomes if o.role == "descriptive"} == {"descriptive-only"}
    es = {e.outcome: e for e in ev.event_studies}
    assert [p.estimate for p in es["childcare-exits"].points] == [p["gap"] for p in paths["exits"]]
    assert ev.verdict == ("inconclusive" if est["exits"]["main"]["pooled"]["p"] >= 0.10 else ev.verdict)


def test_every_evaluation_has_key_insights_and_an_in_depth_method():
    import re

    from alicia.register.catalogue import load_records

    records = load_records().records
    evals = load_evaluations(records).evaluations
    assert evals
    for ev in evals:
        assert len(ev.key_insights) >= 4, ev.id
        assert ev.key_insights[0].startswith("The question:"), ev.id
        m = ev.method
        assert m is not None and m.equations and m.steps, ev.id
        texts = [e.text for e in m.equations] + [t.symbol for t in m.terms] + [m.inference, m.summary]
        for t in texts:
            # Markup is balanced and never nested: _{...}, ^{...} and hat{...} only.
            assert t.count("{") == t.count("}"), (ev.id, t)
            assert not re.search(r"\{[^}]*\{", t), (ev.id, t)
            assert "̂" not in t, (ev.id, t)  # combining hats render badly; use hat{...}


def test_methods_document_is_up_to_date():
    from alicia.register.catalogue import load_records
    from alicia.register.evaluation import methods_markdown

    records = load_records().records
    doc = Path(__file__).resolve().parents[2] / "docs" / "evaluation_methods.md"
    assert doc.read_text("utf-8") == methods_markdown(load_evaluations(records).evaluations), (
        "regenerate with: uv run alicia methods -o ../docs/evaluation_methods.md"
    )


def test_archived_evaluations_are_never_current_and_optional_fields_are_left_out(tmp_path):
    """ILLUSTRATIVE evaluations: a re-evaluation that supersedes the original, and a follow-up that does not."""
    from alicia.register.evaluation import archived, current_evaluation

    old = Evaluation.model_validate(minimal(id="old-eval"))
    side = Evaluation.model_validate(minimal(id="side-eval", follows="old-eval", evaluated_on="2026-10-16"))
    new = Evaluation.model_validate(
        minimal(
            id="new-eval",
            follows="old-eval",
            evaluated_on="2026-10-16",
            supersedes=["old-eval"],
            evaluated_at="2026-10-16T23:00:00+00:00",
        )
    )
    assert archived([old, side, new]) == {"old-eval": "new-eval"}
    # Same day: the one with a recorded run time is the later one, and archived evaluations are never current.
    assert current_evaluation([old, side, new])["wa-trading-hours-weeknight-2010"] == "new-eval"
    assert current_evaluation([new, old])["wa-trading-hours-weeknight-2010"] == "new-eval"
    write_evaluation(old, tmp_path)
    write_evaluation(new, tmp_path)
    assert not {"supersedes", "evaluated_at", "estimators"} & set(json.loads((tmp_path / "old-eval.json").read_text()))
    data = json.loads((tmp_path / "new-eval.json").read_text())
    assert data["supersedes"] == ["old-eval"] and "estimators" not in data


def test_an_evaluation_cannot_supersede_itself():
    with pytest.raises(ValidationError):
        Evaluation.model_validate(minimal(supersedes=["illustrative-eval"]))


def test_results_tables_validate_widths_and_stars():
    from alicia.register.evaluation import ResultsTable, stars

    table = {
        "id": "illustrative-table",
        "title": "Illustrative",
        "columns": [{"label": "A"}, {"label": "B"}],
        "panels": [
            {
                "title": "Panel A",
                "rows": [
                    {"label": "β", "coefficients": [{"estimate": 1.0, "spread": 0.5, "p_value": 0.04}, None]},
                    {"label": "N", "values": ["10", "12"]},
                ],
            }
        ],
        "spread_label": "Placebo standard deviation",
    }
    assert ResultsTable.model_validate(table).panels[0].rows[0].width == 2
    bad = json.loads(json.dumps(table))
    bad["panels"][0]["rows"][1]["values"] = ["10"]
    with pytest.raises(ValidationError):
        ResultsTable.model_validate(bad)
    both = json.loads(json.dumps(table))
    both["panels"][0]["rows"][1]["coefficients"] = [None, None]
    with pytest.raises(ValidationError):
        ResultsTable.model_validate(both)
    assert [stars(p) for p in (0.005, 0.049, 0.05, 0.099, 0.1, None)] == ["***", "**", "*", "*", "", ""]


def test_every_current_evaluation_has_a_regression_table():
    from alicia.register.evaluation import archived

    evs = load_evaluations().evaluations
    gone = archived(evs)
    for ev in evs:
        if ev.id not in gone:
            assert ev.tables, ev.id
            registered = [c for t in ev.tables for p in t.panels for r in p.rows for c in r.coefficients if c]
            assert registered, ev.id


def test_phase5_tables_match_the_registered_run_and_samples():
    from alicia.runner.spec import load

    evs = {e.id: e for e in load_evaluations().evaluations}
    for spec_id, folder in (("phase5-reevaluations", "reevaluations"), ("phase5-new-families", "new_families")):
        base = ANALYSIS.parent / "phase5" / folder
        est = {c["id"]: c for c in json.loads((base / "estimate.json").read_text(encoding="utf-8"))["cases"]}
        stats = {c["id"]: c for c in json.loads((base / "table_stats.json").read_text(encoding="utf-8"))["cases"]}
        for case in load(spec_id).cases:
            table = evs[case["id"]].tables[0]
            layers = ["twoway", "state_year", "saturated", "controls", "imputation", "sdid", "gsynth"]
            feasible = [o for o in case["outcomes"] if est[case["id"]]["outcomes"][o["key"]]["feasible"]["ok"]]
            assert len(table.panels) == len(feasible)
            for o, panel in zip(feasible, table.panels, strict=True):
                r = est[case["id"]]["outcomes"][o["key"]]
                s = stats[case["id"]]["outcomes"][o["key"]]
                assert s["reproduces"]
                rows = {row.label: row for row in panel.rows}
                coefs = rows["Reform × post (β)"].coefficients
                for k, c in zip(layers, coefs, strict=True):
                    lay = r["layers"][k]
                    assert (c.estimate, c.spread, c.p_value) == (lay["estimate"], lay["placebo_sd"], lay["p"])
                    assert c.registered == (k == o["layer"])
                assert rows["Observations"].values == tuple(f"{s['layers'][k]['nobs']:,}" for k in layers)


def test_tables_documents_are_up_to_date():
    from alicia.register.catalogue import load_records
    from alicia.register.tables import tables_latex, tables_markdown

    evals = load_evaluations(load_records().records).evaluations
    docs = Path(__file__).resolve().parents[2] / "docs"
    hint = (
        "regenerate with: uv run alicia tables -o ../docs/econometric_tables.md --latex ../docs/econometric_tables.tex"
    )
    assert (docs / "econometric_tables.md").read_text("utf-8") == tables_markdown(evals), hint
    assert (docs / "econometric_tables.tex").read_text("utf-8") == tables_latex(evals), hint


def test_phase5_robustness_reproduces_the_registered_run():
    """The as-registered variant must equal estimate.json; the robustness table must show it, not pre-registered."""
    from alicia.runner.spec import load

    evs = {e.id: e for e in load_evaluations().evaluations}
    for spec_id, folder in (("phase5-reevaluations", "reevaluations"), ("phase5-new-families", "new_families")):
        base = ANALYSIS.parent / "phase5" / folder
        est = {c["id"]: c for c in json.loads((base / "estimate.json").read_text(encoding="utf-8"))["cases"]}
        rob = {c["id"]: c for c in json.loads((base / "robustness.json").read_text(encoding="utf-8"))["cases"]}
        for case in load(spec_id).cases:
            table = next(t for t in evs[case["id"]].tables if t.id.endswith("-robustness"))
            assert "not pre-registered" in table.title
            registered_row = table.panels[0].rows[0].coefficients
            outs = [o for o in case["outcomes"] if o["key"] in rob[case["id"]]["outcomes"]]
            for o, c in zip(outs, registered_row, strict=True):
                reg = est[case["id"]]["outcomes"][o["key"]]["registered"]
                v = rob[case["id"]]["outcomes"][o["key"]]["variants"][0]
                assert v["label"] == "As registered"
                # Placebos are re-estimated; the fixed-effects solver converges to a tolerance, so allow rounding.
                assert (v["estimate"], v["p"]) == (reg["estimate"], reg["p"])
                assert abs(v["placebo_sd"] - reg["placebo_sd"]) <= 0.002
                assert c.estimate == reg["estimate"] and c.registered
