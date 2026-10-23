"""Layer B back-test against PC National (analyses/costing_calibration/backtest.py; policy costing P4)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "analyses" / "costing_calibration" / "backtest.py"


@pytest.fixture(scope="module")
def bt():
    spec = importlib.util.spec_from_file_location("costing_backtest", HERE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def result(bt):
    return bt.run()


def test_backtest_outputs_are_up_to_date(bt, result):
    """backtest.json and docs/costing_calibration.md are what the script writes from the committed parameters."""
    assert json.loads(bt.OUT.read_text("utf-8")) == json.loads(json.dumps(result))
    assert bt.DOC.read_text("utf-8") == bt.markdown(result)


def test_every_pc_industry_has_input_output_weights(bt):
    weights = bt.industry_weights(bt.load_tables())
    assert [w["pcn_no"] for w in weights] == list(range(1, 115))
    assert all(0 <= w["labour_share"] <= 1 for w in weights)
    dwellings = next(w for w in weights if w["name"] == "Ownership of dwellings")
    assert dwellings["ioig"] == ["6700", "6701"] and dwellings["labour_share"] < 0.05


def test_layer_b_identities(bt):
    weights = bt.industry_weights(bt.load_tables())
    everyone = list(range(1, 115))
    # An economy-wide labour productivity shock raises GDP by the same percentage (fixed rate of return).
    assert bt.predict(weights, "lp", 0.1, everyone)["layer_b"] == pytest.approx(0.1)
    # An economy-wide Hicks-neutral shock is scaled up by 1 / (1 - alpha) as capital accumulates.
    alpha = 1 - sum(w["wages"] for w in weights) / sum(w["va"] for w in weights)
    assert bt.predict(weights, "mfp", 0.1, everyone)["layer_b"] == pytest.approx(0.1 / (1 - alpha))
    # Linear in the shock.
    a = bt.predict(weights, "lp", 0.4, [70, 71])["layer_b"]
    assert bt.predict(weights, "lp", 0.8, [70, 71])["layer_b"] == pytest.approx(2 * a)


def test_backtest_results(result):
    cases = {(c["code"], c["bound"], c["size"]): c for c in result["cases"]}
    # L1's bounds bracket PC National's result.
    assert cases[("L1", "lower", 0.14)]["layer_b"] < cases[("L1", "lower", 0.14)]["pc_real_gdp"]
    assert cases[("L1", "upper", 0.24)]["layer_b"] > cases[("L1", "upper", 0.24)]["pc_real_gdp"]
    # Wage-bill weights beat value-added weights for the broad licensing shock (interpretation A-P10).
    l2 = cases[("L2", None, 0.8)]
    assert abs(l2["layer_b_error"]) < 0.1 < abs(l2["naive_error"])
    band = result["model_error_band"]
    assert band["lp"]["low"] <= 1 <= band["lp"]["high"] and band["mfp"]["low"] <= 1 <= band["mfp"]["high"]
