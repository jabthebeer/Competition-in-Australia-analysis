"""Policy costing P4: back-test of Layer B against the Productivity Commission's PC National simulations.

Layer B (docs/forward_plan_policy_costing.md §6.3; regulatory-burden-tool/docs/productivity_traceability.md
F-B-01 to F-B-05) turns industry productivity shocks into a long-run change in real GDP, under the closure PC
National uses for these simulations: fixed aggregate employment and a fixed rate of return, so capital adjusts.
With industry value added VA_i, wage bill W_i, capital income K_i = VA_i - W_i and aggregate capital share
alpha = sum K / sum VA:

- labour-augmenting shock x_i (labour productivity):     dlnY = sum_i (W_i / sum W) x_i
- Hicks-neutral value-added shock z_i (capital and labour productivity, "primary factor productivity"):
                                                           dlnY = sum_i (VA_i / sum VA) z_i / (1 - alpha)
- capital-augmenting shock k_i (capital productivity):    dlnY = sum_i (K_i / sum VA) k_i / (1 - alpha)

The naive alternative weights every shock by value-added share, with no capital response:
dlnY = sum_i (VA_i / sum VA) s_i.

Weights: value added by PC National industry is the PC's own 2018-19 database (pc_national.initial_gsp). Each
industry's labour share of factor income, coe / (coe + gos_mi), comes from the ABS input-output tables
2023-24 (abs_io.industries), matched to PC industries by name. "Ownership of dwellings" is the sum of IOIGs
6700 and 6701. The labour shares are a later year than the PC's database: an approximation, stated in the
results.

Cases (cases.json): the PC simulations whose shock is a productivity change in named industries, with
industries and sizes taken from the workbook's scenario text. L1 is reported as bounds because the workbook
does not list its 24 service industries. Rent, price and tariff simulations are not productivity shocks and are
not back-tested.

    uv run python analyses/costing_calibration/backtest.py      # from alicia/; writes backtest.json and the doc
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PARAMETERS = ROOT / "data" / "processed" / "costing" / "parameters.json"
OUT = HERE / "backtest.json"
DOC = ROOT / "docs" / "costing_calibration.md"
TOLERANCE = 0.15  # F-B-05: target within +/-15% of the PC's real GDP result for pure productivity shocks
DWELLINGS = ("6700", "6701")


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _expand(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi or lo) + 1))
    return out


def load_tables(path: Path = PARAMETERS) -> dict:
    tables = json.loads(path.read_text("utf-8"))["tables"]
    return {k: tables[k]["rows"] for k in ("pc_national.initial_gsp", "pc_national.simulations", "abs_io.industries")}


def industry_weights(tables: dict) -> list[dict]:
    """One row per PC National industry: value added (PC 2018-19), labour share (ABS I-O 2023-24), wage bill."""
    io = {r["ioig"]: r for r in tables["abs_io.industries"] if r["ioig"] != "TOT"}
    by_name = {_norm(r["name"]): r for r in io.values()}
    rows = []
    for pc in sorted(tables["pc_national.initial_gsp"], key=lambda r: r["pcn_no"]):
        if pc["pcn_no"] == 0:
            continue
        if _norm(pc["name"]) == "ownership of dwellings":
            matched = [io[k] for k in DWELLINGS]
        elif _norm(pc["name"]) in by_name:
            matched = [by_name[_norm(pc["name"])]]
        else:
            raise ValueError(f"PC National industry {pc['pcn_no']} {pc['name']!r} has no input-output match")
        coe = sum(m["coe"] for m in matched)
        gos = sum(m["gos_mi"] for m in matched)
        share = coe / (coe + gos) if coe + gos > 0 else 0.0
        va = pc["total"]
        rows.append(
            {
                "pcn_no": pc["pcn_no"],
                "name": pc["name"],
                "ioig": [m["ioig"] for m in matched],
                "va": va,
                "labour_share": share,
                "wages": va * share,
                "capital_income": va * (1 - share),
            }
        )
    return rows


def predict(weights: list[dict], shock_type: str, size: float, industries: list[int]) -> dict:
    """Predicted % change in real GDP from a uniform shock of ``size`` % in ``industries``."""
    hit = set(industries)
    va = sum(w["va"] for w in weights)
    wages = sum(w["wages"] for w in weights)
    alpha = 1 - wages / va
    in_va = sum(w["va"] for w in weights if w["pcn_no"] in hit)
    in_wages = sum(w["wages"] for w in weights if w["pcn_no"] in hit)
    in_capital = sum(w["capital_income"] for w in weights if w["pcn_no"] in hit)
    if shock_type == "lp":
        layer_b = size * in_wages / wages
    elif shock_type == "mfp":
        layer_b = size * in_va / va / (1 - alpha)
    elif shock_type == "kp":
        layer_b = size * in_capital / va / (1 - alpha)
    else:
        raise ValueError(f"unknown shock type {shock_type!r}")
    return {"layer_b": layer_b, "naive": size * in_va / va, "va_share": in_va / va, "wage_share": in_wages / wages}


def run(tables: dict | None = None, cases_path: Path = HERE / "cases.json") -> dict:
    tables = tables or load_tables()
    spec = json.loads(cases_path.read_text("utf-8"))
    sets = {k: _expand(v) for k, v in spec["industry_sets"].items()}
    weights = industry_weights(tables)
    sims = tables["pc_national.simulations"]
    alpha = 1 - sum(w["wages"] for w in weights) / sum(w["va"] for w in weights)
    results = []
    for case in spec["cases"]:
        matches = [s for s in sims if s["code"] == case["code"] and (s["real_gdp"] >= 0) == (case["sign"] > 0)]
        if len(matches) != 1:
            raise ValueError(f"case {case['code']} (sign {case['sign']}) matches {len(matches)} simulations")
        actual = matches[0]["real_gdp"]
        p = predict(weights, case["type"], case["size"], sets[case["industries"]])
        results.append(
            {
                "code": case["code"],
                "type": case["type"],
                "size": case["size"],
                "industries": case["industries"],
                "n_industries": len(sets[case["industries"]]),
                "target": case["target"],
                "bound": case.get("bound"),
                "note": case["note"],
                "pc_real_gdp": round(actual, 6),
                "layer_b": round(p["layer_b"], 6),
                "naive": round(p["naive"], 6),
                "layer_b_error": round(p["layer_b"] / actual - 1, 4),
                "naive_error": round(p["naive"] / actual - 1, 4),
                "va_share": round(p["va_share"], 6),
                "wage_share": round(p["wage_share"], 6),
            }
        )
    targets = [r for r in results if r["target"]]
    within = [r for r in targets if abs(r["layer_b_error"]) <= TOLERANCE]
    # Model-error band (interpretation A-P19): the range of PC National / Layer B across the target simulations of
    # each shock type the engine produces (labour productivity, capital and labour productivity). The engine keeps
    # Layer B's result as the central value and uses this band as the range for the step from industry shocks to GDP.
    bands = {}
    for kind in ("lp", "mfp"):
        ratios = [r["pc_real_gdp"] / r["layer_b"] for r in targets if r["type"] == kind]
        bands[kind] = {"low": round(min(ratios), 3), "high": round(max(ratios), 3), "cases": len(ratios)}
    return {
        "about": "Layer B back-test against PC National (alicia/analyses/costing_calibration/backtest.py).",
        "weights": {
            "value_added": "PC National initial GSP by industry, 2018-19 (pc_national.initial_gsp)",
            "labour_share": "ABS input-output tables 2023-24, coe / (coe + gos_mi) by IOIG (abs_io.industries)",
            "alpha": round(alpha, 6),
            "industries": [
                {
                    "pcn_no": w["pcn_no"],
                    "name": w["name"],
                    "ioig": w["ioig"],
                    "va": round(w["va"], 3),
                    "labour_share": round(w["labour_share"], 6),
                }
                for w in weights
            ],
        },
        "tolerance": TOLERANCE,
        "model_error_band": bands,
        "summary": {
            "targets": len(targets),
            "within_tolerance": len(within),
            "mean_abs_error_layer_b": round(sum(abs(r["layer_b_error"]) for r in targets) / len(targets), 4),
            "mean_abs_error_naive": round(sum(abs(r["naive_error"]) for r in targets) / len(targets), 4),
        },
        "cases": results,
    }


def _pct(x: float) -> str:
    return f"{x * 100:+.0f}%".replace("-", "−")


def _num(x: float, digits: int = 4) -> str:
    return f"{x:.{digits}f}".replace("-", "−")


def markdown(result: dict) -> str:
    s = result["summary"]
    lines = [
        "# Layer B calibration: back-test against PC National",
        "",
        "Generated by `alicia/analyses/costing_calibration/backtest.py` from `data/processed/costing/parameters.json`."
        " Do not edit by hand. Policy costing P4 (plan §6.3, traceability F-B-01 to F-B-05).",
        "",
        "**Question.** Layer B turns industry productivity shocks into a long-run change in real GDP with a"
        " reduced-form closure (fixed employment, fixed rate of return, so capital adjusts). Does it reproduce the"
        " Productivity Commission's computable general equilibrium model, PC National, on the PC's own published"
        " simulations (*National Competition Policy: modelling proposed reforms*, 2024)?",
        "",
        "**Formulas.** Wage bill W, value added VA, capital income K = VA − W, capital share"
        f" α = ΣK/ΣVA = {_num(result['weights']['alpha'], 3)}.",
        "",
        "| Shock | Layer B | Naive (value-added shares, no capital response) |",
        "|---|---|---|",
        "| Labour productivity x (labour-augmenting) | Σ (W_i/ΣW) x_i | Σ (VA_i/ΣVA) x_i |",
        "| Capital and labour productivity z (Hicks-neutral) | Σ (VA_i/ΣVA) z_i / (1 − α) | Σ (VA_i/ΣVA) z_i |",
        "| Capital productivity k (capital-augmenting) | Σ (K_i/ΣVA) k_i / (1 − α) | Σ (VA_i/ΣVA) k_i |",
        "",
        f"**Result.** {s['within_tolerance']} of {s['targets']} target simulations are within"
        f" ±{result['tolerance'] * 100:.0f}% of PC National's real GDP effect. Mean absolute error: Layer B"
        f" {s['mean_abs_error_layer_b'] * 100:.0f}%, naive {s['mean_abs_error_naive'] * 100:.0f}%.",
        "",
        "**Model-error band.** Across the target simulations, PC National's result divided by Layer B's ranges from"
        f" {result['model_error_band']['lp']['low']:.2f} to {result['model_error_band']['lp']['high']:.2f} for labour"
        f" productivity shocks ({result['model_error_band']['lp']['cases']} cases) and from"
        f" {result['model_error_band']['mfp']['low']:.2f} to {result['model_error_band']['mfp']['high']:.2f} for"
        f" capital and labour productivity shocks ({result['model_error_band']['mfp']['cases']} cases). The Policy"
        " costing engine keeps Layer B's result as the central value and uses this band as the range of the step"
        " from industry shocks to GDP (interpretation A-P19; evidence entry `layer-b.model-error.backtest`). The"
        " largest gaps are shocks confined to health care, which is mostly funded by government: Layer B overstates"
        " them, as it does capital productivity alone in retail (B2), a shock type no channel of the engine produces.",
        "",
        "| Simulation | Shock | Industries | Share of value added | Share of wages | PC National real GDP (%) |"
        " Layer B (%) | Error | Naive (%) | Error |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    kind = {"lp": "labour productivity", "mfp": "capital and labour productivity", "kp": "capital productivity"}
    for r in result["cases"]:
        label = r["code"] + (f" ({r['bound']} bound)" if r["bound"] else "") + ("" if r["target"] else " †")
        lines.append(
            f"| {label} | {kind[r['type']]} {_num(r['size'], 2)}% | {r['industries'].replace('_', ' ')}"
            f" ({r['n_industries']}) | {r['va_share'] * 100:.1f}% | {r['wage_share'] * 100:.1f}% |"
            f" {_num(r['pc_real_gdp'])} | {_num(r['layer_b'])} | {_pct(r['layer_b_error'])} |"
            f" {_num(r['naive'])} | {_pct(r['naive_error'])} |"
        )
    lines += [
        "",
        "† Not a target: L1's 24 service industries are not listed in the workbook, so the case is run with"
        " every non-agricultural industry at the lower (0.14%) and upper (0.24%) shock. PC National's result should"
        " lie between the two.",
        "",
        "**Notes.**",
        "",
        "- *Weights.* Value added by industry is the PC's own 2018-19 database (`pc_national.initial_gsp`). Labour"
        " shares are from the ABS input-output tables 2023-24 (`abs_io.industries`, compensation of employees over"
        " compensation plus gross operating surplus and mixed income), matched to PC industries by name; Ownership"
        " of dwellings is IOIGs 6700 and 6701. The later-year labour shares are an approximation.",
        "- *Closures.* D2 holds real government consumption fixed, unlike the other simulations, so a gap there"
        " reflects the closure as well as the weights.",
        "- *Not back-tested.* Rent removals (B3, D4, D5, H2, NZ1rep), import-price and tariff shocks (B7, H4,"
        " NZ3, NZ5), output shocks (B9, NZ1agr) and the regional shock (H3reg, which needs regional employment"
        " by industry) are not productivity shocks in named industries. L1's state results in the workbook look"
        " copied from L2 (`gsp_gap`); only its national real GDP is used.",
        "- *Use in the tool.* Layer B's weights in the Policy costing tab come from the latest ABS data (input-output"
        " tables, national accounts), not from the PC's 2018-19 database; this back-test checks the closure and"
        " the weighting rule, not those numbers.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    result = run()
    OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    DOC.write_text(markdown(result), encoding="utf-8")
    s = result["summary"]
    print(f"{s['within_tolerance']}/{s['targets']} within tolerance; MAE Layer B {s['mean_abs_error_layer_b']:.3f}")


if __name__ == "__main__":
    main()
