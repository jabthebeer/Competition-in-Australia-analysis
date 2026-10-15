"""Regenerate src/regimpact/data/cpi17_classes.json: the CPI's 87 expenditure classes.

Usage: uv run python scripts/fetch_cpi_classes.py
Source: ABS Data API, CPI dataflow 1.1.0 (17th series), codelist CL_CPI_INDEX_17, CC BY 4.0.
Expenditure classes are the third level below "All groups CPI" (group > subgroup > class).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import httpx

URL = "https://data.api.abs.gov.au/rest/dataflow/ABS/CPI/1.1.0?references=codelist"
OUT = Path(__file__).resolve().parents[1] / "src" / "regimpact" / "data" / "cpi17_classes.json"


def main() -> None:
    resp = httpx.get(URL, headers={"Accept": "application/vnd.sdmx.structure+json"}, timeout=90)
    resp.raise_for_status()
    codelist = next(c for c in resp.json()["data"]["codelists"] if c["id"] == "CL_CPI_INDEX_17")
    by_id = {c["id"]: c for c in codelist["codes"]}

    def depth(code: str) -> int:
        d = 0
        while (parent := by_id[code].get("parent")) is not None:
            code, d = parent, d + 1
        return d if code == "10001" else -1

    classes = [{"code": c["id"], "name": c["name"],
                "subgroup": by_id[c["parent"]]["name"], "group": by_id[by_id[c["parent"]]["parent"]]["name"]}
               for c in codelist["codes"] if depth(c["id"]) == 3]
    payload = {
        "source": URL,
        "codelist": f"{codelist['id']} {codelist['version']}",
        "licence": "CC BY 4.0, Australian Bureau of Statistics",
        "retrieved": dt.date.today().isoformat(),
        "response_sha256": hashlib.sha256(resp.content).hexdigest(),
        "classes": classes,
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(classes)} expenditure classes to {OUT}")


if __name__ == "__main__":
    main()
