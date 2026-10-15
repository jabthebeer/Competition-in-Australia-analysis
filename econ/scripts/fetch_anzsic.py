"""Regenerate src/regimpact/data/anzsic2006.json from the ABS Data API codelist.

Usage: uv run python scripts/fetch_anzsic.py
Source: ABS, CL_ANZSIC_2006 version 1.1.0 (ANZSIC 2006, Revision 2.0), CC BY 4.0.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import httpx

URL = "https://data.api.abs.gov.au/rest/codelist/ABS/CL_ANZSIC_2006/1.1.0"
OUT = Path(__file__).resolve().parents[1] / "src" / "regimpact" / "data" / "anzsic2006.json"


def main() -> None:
    resp = httpx.get(URL, headers={"Accept": "application/vnd.sdmx.structure+json"}, timeout=90)
    resp.raise_for_status()
    codelist = resp.json()["data"]["codelists"][0]
    codes = [
        {"code": c["id"], "name": c["name"], "parent": c.get("parent")} for c in codelist["codes"] if c["id"] != "TOT"
    ]
    payload = {
        "source": URL,
        "codelist": f"{codelist['id']} {codelist['version']}",
        "title": codelist["name"],
        "licence": "CC BY 4.0, Australian Bureau of Statistics",
        "retrieved": dt.date.today().isoformat(),
        "response_sha256": hashlib.sha256(resp.content).hexdigest(),
        "codes": codes,
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(codes)} codes to {OUT}")


if __name__ == "__main__":
    main()
