"""Gap paths for display (not part of the registered inference): the deseasonalised WA-minus-others
gap by period for childcare, with the 5th-95th percentile of the same path across the placebo
industries (exits: named industries; prices: CPI classes) in each period.

Run after estimate.py: uv run python analyses/childcare_nqf_wa/paths.py
Writes: analyses/childcare_nqf_wa/paths.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import spec

HERE = Path(__file__).resolve().parent


def band(childcare: pd.DataFrame, placebos: dict[str, pd.DataFrame], windows) -> list[dict]:
    main = spec.path(childcare, windows)
    others = pd.DataFrame({k: spec.path(df, windows) for k, df in placebos.items()})
    q = others.quantile([0.05, 0.95], axis=1).T
    return [
        {
            "time": str(t.date()),
            "gap": round(float(v), 3),
            "low": round(float(q.loc[t, 0.05]), 3),
            "high": round(float(q.loc[t, 0.95]), 3),
        }
        for t, v in main.items()
        if t in q.index
    ]


def main() -> None:
    abn = spec.abn_counts()
    rel = spec.cpi()
    classes = [c for c in spec.cpi_placebos() if c in rel.index.get_level_values(0)]
    out = {
        "exits": band(
            spec.abn_panel(abn, spec.CHILDCARE_CLASS),
            {c: spec.abn_panel(abn, c) for c in spec.abn_placebos(abn)},
            spec.MONTHLY,
        ),
        "prices": band(
            spec.cpi_panel(rel, spec.CPI_CHILD_CARE),
            {c: spec.cpi_panel(rel, c) for c in classes},
            spec.QUARTERLY,
        ),
    }
    (HERE / "paths.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print({k: len(v) for k, v in out.items()})


if __name__ == "__main__":
    main()
