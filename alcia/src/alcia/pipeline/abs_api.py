"""ABS Data API (SDMX): dataflow structures and data queries, saved as raw files with manifests.

Data: Australian Bureau of Statistics, CC BY 4.0. Each data query is stored once in
``data/raw/abs_api/`` (named by dataflow and a hash of the query) and recorded in
``data/manifests/abs_api.json``.
"""

from __future__ import annotations

import hashlib
import io
import json
from functools import cache

import httpx
import pandas as pd

from . import store

BASE = "https://data.api.abs.gov.au/rest"
LICENCE = "CC BY 4.0, Australian Bureau of Statistics"
SOURCE = "abs_api"
CSV = "application/vnd.sdmx.data+csv"
STRUCTURE = "application/vnd.sdmx.structure+json"


def _client() -> httpx.Client:
    return httpx.Client(headers={"User-Agent": store.USER_AGENT}, timeout=180, follow_redirects=True)


@cache
def structure(flow: str, version: str = "latest") -> dict:
    """Dimensions (in key order) and their codelists: {"dimensions": [{"id", "codes": {code: name}}]}."""
    url = f"{BASE}/dataflow/ABS/{flow}/{version}?references=all"
    with _client() as c:
        resp = c.get(url, headers={"Accept": STRUCTURE})
        resp.raise_for_status()
    js = resp.json()["data"]
    codelists = {
        cl["id"]: {code["id"]: code.get("name", code["id"]) for code in cl.get("codes", [])}
        for cl in js.get("codelists", [])
    }
    dsd = js["dataStructures"][0]["dataStructureComponents"]["dimensionList"]["dimensions"]
    dims = []
    for d in sorted(dsd, key=lambda d: d.get("position", 0)):
        ref = d.get("localRepresentation", {}).get("enumeration", "")
        cl_id = ref.split("(")[0].split(":")[-1].split(".")[-1] if ref else ""
        dims.append({"id": d["id"], "codelist": cl_id, "codes": codelists.get(cl_id, {})})
    flow_meta = js["dataflows"][0]
    return {
        "flow": flow,
        "version": flow_meta.get("version", version),
        "name": flow_meta.get("name"),
        "dimensions": dims,
    }


def data(
    flow: str, key: str, version: str = "latest", start: str | None = None, end: str | None = None
) -> pd.DataFrame:
    """SDMX-CSV for one query, read from data/raw if already fetched."""
    if version == "latest":  # the data endpoint needs an explicit version
        version = structure(flow)["version"]
    params = "&".join(f"{k}={v}" for k, v in (("startPeriod", start), ("endPeriod", end)) if v)
    url = f"{BASE}/data/ABS,{flow},{version}/{key}" + (f"?{params}" if params else "")
    name = f"{flow}_{hashlib.sha256(url.encode()).hexdigest()[:16]}.csv"
    path = store.raw_dir(SOURCE) / name
    if not path.exists():
        with _client() as c:
            resp = c.get(url, headers={"Accept": CSV})
            resp.raise_for_status()
        path.write_text(resp.text, encoding="utf-8")
        store.record_download(SOURCE, path, url, LICENCE)
    return pd.read_csv(io.StringIO(path.read_text("utf-8")), dtype=str)


def key(dims: list[dict], **selected: str | list[str]) -> str:
    """Build an SDMX key in dimension order; unselected dimensions are left open."""
    parts = []
    for d in dims:
        v = selected.get(d["id"], "")
        parts.append("+".join(v) if isinstance(v, (list, tuple)) else v)
    return ".".join(parts)


def dump_structure(flow: str) -> str:
    """Readable summary of a dataflow's dimensions (for exploring)."""
    s = structure(flow)
    lines = [f"{s['flow']} v{s['version']}: {s['name']}"]
    for d in s["dimensions"]:
        codes = list(d["codes"].items())
        sample = ", ".join(f"{k}={v}" for k, v in codes[:8])
        lines.append(f"  {d['id']} ({d['codelist']}, {len(codes)} codes): {sample}{' …' if len(codes) > 8 else ''}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    import sys

    print(dump_structure(sys.argv[1]) if len(sys.argv) > 1 else json.dumps({"usage": "abs_api <FLOW>"}))
