"""ANZSIC 2006 (Revision 2.0) codelist: division, subdivision, group and class codes and titles.

Built from the codelist bundled with the package (``alicia/data/anzsic2006.json``, ABS Data API
``CL_ANZSIC_2006`` 1.1.0). Discovery asks the ABS Data API for the latest version of the codelist; if the ABS
publishes a newer version, it is downloaded to ``data/raw/abs_anzsic/`` and the table is built from it instead.
"""

from __future__ import annotations

import hashlib
import json
from importlib import resources

from .base import ABS_LICENCE, Release, Source, Table, fetch_files, get, local_path, remote, source_doc

API = "https://data.api.abs.gov.au/rest/codelist/ABS/CL_ANZSIC_2006"
STRUCTURE = "application/vnd.sdmx.structure+json"
BUNDLED = "alicia/src/alicia/data/anzsic2006.json"
SOURCE = Source(
    id="abs_anzsic",
    title="Australian and New Zealand Standard Industrial Classification (ANZSIC), 2006 (Revision 2.0)",
    publisher="Australian Bureau of Statistics",
    licence=ABS_LICENCE,
    url=f"{API}/latest",
)
LEVELS = {1: "division", 2: "subdivision", 3: "group", 4: "class"}


def _bundled_bytes() -> bytes:
    return resources.files("alicia.data").joinpath("anzsic2006.json").read_bytes()


def bundled() -> dict:
    return json.loads(_bundled_bytes().decode("utf-8"))


def discover() -> Release:
    stubs = get(f"{API}/latest?detail=allstubs", accept=STRUCTURE).json()["data"]["codelists"]
    version = stubs[0]["version"]
    have = bundled()["codelist"].split()[-1]
    newer = remote(f"{API}/{version}", folder=version, name="CL_ANZSIC_2006.json", accept=STRUCTURE)
    return Release(
        id=f"CL_ANZSIC_2006 {version}",
        date=None,
        files=() if version == have else (newer,),
        page=f"{API}/latest",
        extra=(("version", version),),
    )


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def codes_from_api(payload: dict) -> list[dict]:
    """Codes from an SDMX-JSON codelist response, as the bundled file stores them (the total is dropped)."""
    cl = payload["data"]["codelists"][0]
    return [{"code": c["id"], "name": c["name"], "parent": c.get("parent")} for c in cl["codes"] if c["id"] != "TOT"]


def table(codes: list[dict]) -> Table:
    by_code = {c["code"]: c for c in codes}

    def division(code: str) -> str:
        while len(code) > 1:
            code = by_code[code]["parent"]
        return code

    rows = [
        {
            "code": c["code"],
            "level": LEVELS[len(c["code"])],
            "name": c["name"],
            "parent": None if len(c["code"]) == 1 else c["parent"],
            "division": division(c["code"]),
        }
        for c in codes
    ]
    return Table(
        description=(
            "ANZSIC 2006 (Revision 2.0) codes and titles at every level, with each code's parent and division. "
            "Divisions are letters A-S; subdivisions 2 digits, groups 3, classes 4."
        ),
        columns={
            "code": "code: ANZSIC 2006",
            "level": "text: division, subdivision, group or class",
            "name": "text",
            "parent": "code: ANZSIC 2006 (null for a division)",
            "division": "code: ANZSIC 2006 division",
        },
        keys=("code",),
        rows=rows,
    )


def build(release: Release) -> dict[str, Table]:
    if release.files:
        payload = json.loads(local_path(SOURCE.id, release.files[0]).read_text("utf-8"))
        return {"codes": table(codes_from_api(payload))}
    return {"codes": table(bundled()["codes"])}


def document(release: Release) -> dict:
    """Per-source document; when built from the bundled file, it is recorded as the input."""
    tables = build(release)
    if release.files:
        return source_doc(SOURCE, release, tables)
    b = bundled()
    derived = [
        {
            "file": BUNDLED,
            "sha256": hashlib.sha256(_bundled_bytes()).hexdigest(),
            "from": b["source"],
            "codelist": b["codelist"],
            "response_sha256": b["response_sha256"],
            "retrieved": b["retrieved"],
        }
    ]
    return source_doc(SOURCE, release, tables, derived_from=derived, retrieved=b["retrieved"])
