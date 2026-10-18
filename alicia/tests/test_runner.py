"""Specification files and the runner (forward plan Phase 4)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from alicia.register.catalogue import load_records
from alicia.register.evaluation import default_evaluations_dir
from alicia.runner import run as runner
from alicia.runner.spec import Specification, analyses_dir, load, load_all

ALICIA = Path(__file__).resolve().parents[1]


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_every_specification_is_valid_and_points_at_real_things():
    specs, problems = load_all()
    assert not problems
    assert {s.id for s in specs} >= {
        "wa-trading-hours-2010-2012",
        "high-evaluability-batch",
        "wa-trading-hours-weeknight-2010-new-data",
        "childcare-nqf-wa-delay-2012",
    }
    records = {r.id for r in load_records().records}
    for s in specs:
        assert set(s.records) <= records, s.id
        for e in s.evaluations:
            assert (default_evaluations_dir() / f"{e}.json").exists(), e
        folder = analyses_dir() / s.analysis
        for st in s.stages:
            assert (folder / st.script).exists(), (s.id, st.script)
            for w in st.writes:
                assert (ALICIA / w).exists(), (s.id, w)
        assert (ALICIA.parent / s.plan).exists(), s.plan
        # every evaluation file is written by an evaluation stage
        written = {Path(w).stem for st in s.stages if st.kind == "evaluation" for w in st.writes}
        assert written == set(s.evaluations), s.id


def test_evaluations_name_the_records_their_specification_lists():
    for s in load_all()[0]:
        for e in s.evaluations:
            ev = json.loads((default_evaluations_dir() / f"{e}.json").read_text("utf-8"))
            assert set(ev["records"]) <= set(s.records), e
            assert ev.get("follows") in (None, s.follows) or s.id == "high-evaluability-batch", e


def test_stage_check_reports_identical_changed_and_created(tmp_path, monkeypatch):
    folder = tmp_path / "analyses" / "toy"
    folder.mkdir(parents=True)
    (folder / "write.py").write_text(
        "import sys, pathlib\npathlib.Path(sys.argv[1]).write_text(sys.argv[2])\n", encoding="utf-8"
    )
    monkeypatch.setattr(runner, "ALICIA", tmp_path)
    monkeypatch.setattr(runner, "analyses_dir", lambda: tmp_path / "analyses")
    out = tmp_path / "out.txt"

    def spec(text: str) -> Specification:
        return Specification.model_validate(
            {
                "id": "toy",
                "title": "Toy",
                "analysis": "toy",
                "plan": "README.md",
                "records": ["toy-record"],
                "hypothesis": "mixed",
                "stages": [
                    {
                        "name": "s",
                        "kind": "derived",
                        "script": "write.py",
                        "args": [str(out), text],
                        "writes": ["out.txt"],
                    }
                ],
            }
        )

    (r,) = runner.run(spec("a"), echo=lambda *_: None)
    assert r.outputs[0].status == "created" and not r.reproduced
    (r,) = runner.run(spec("a"), echo=lambda *_: None)
    assert r.outputs[0].status == "identical" and r.reproduced
    (r,) = runner.run(spec("b"), echo=lambda *_: None)
    assert r.outputs[0].status == "changed" and not r.reproduced


def test_registered_estimate_needs_a_committed_design(monkeypatch):
    s = load("wa-trading-hours-weeknight-2010-new-data")
    monkeypatch.setattr(runner, "uncommitted", lambda paths: list(paths))
    with pytest.raises(PermissionError):
        runner.run(s, ["estimate"], echo=lambda *_: None)
