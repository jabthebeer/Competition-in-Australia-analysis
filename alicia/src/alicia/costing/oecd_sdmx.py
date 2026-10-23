"""Shared reader for OECD SDMX dataflows (sdmx.oecd.org), used by the PMR, STRI and FDI RRI connectors.

Discovery asks the OECD for the dataflow's latest version and the data actually available for the query
(time range and number of observations, from the ``availableconstraint`` endpoint). The release identifier is
built from those, so a new year, a revision that changes the number of observations or a new dataflow version
counts as a new release. The OECD states no release dates through the API: ``date`` is null.
"""

from __future__ import annotations

import csv
import io
import re

from .base import Release, RemoteFile, Source, Table, get, local_path, value

SDMX = "https://sdmx.oecd.org/public/rest"
STRUCTURE_XML = "application/vnd.sdmx.structure+xml;version=2.1"
# Not verified on oecd.org, which refused our requests (HTTP 403) on 22 and 23 October 2026.
LICENCE = (
    "OECD terms and conditions; CC BY 4.0 is the OECD default for data published from 1 July 2024 "
    "(open-by-default policy, seen in search results only; oecd.org refused direct requests)"
)


def source(id_: str, title: str, agency: str, flow: str) -> Source:
    return Source(id_, title, "OECD", LICENCE, f"{SDMX}/dataflow/{agency}/{flow}/latest")


def discover(src: Source, agency: str, flow: str, key: str) -> Release:
    xml = get(f"{SDMX}/dataflow/{agency}/{flow}/latest").text
    m = re.search(r'<structure:Dataflow id="[^"]+" agencyID="[^"]+" version="([^"]+)"', xml)
    if not m:
        raise ValueError(f"{flow}: no dataflow version in the OECD response")
    version = m.group(1)
    avail = get(f"{SDMX}/availableconstraint/{agency},{flow},{version}/{key}/all/all?mode=available").text
    start = re.search(r"<common:StartPeriod[^>]*>(\d{4})", avail)
    end = re.search(r"<common:EndPeriod[^>]*>(\d{4})", avail)
    obs = re.search(r'id="obs_count">\s*<common:AnnotationTitle>(\d+)<', avail)
    if not (start and end):
        raise ValueError(f"{flow}: no time range in the availability response")
    count = obs.group(1) if obs else "?"
    rid = f"{flow} v{version}, {start.group(1)}-{end.group(1)}, {count} observations"
    url = f"{SDMX}/data/{agency},{flow},{version}/{key}?format=csvfilewithlabels"
    folder = re.sub(r"[^A-Za-z0-9.-]+", "_", f"v{version}_{end.group(1)}_{count}")
    return Release(
        id=rid,
        date=None,
        files=(RemoteFile(f"{folder}/{src.id}.csv", url),),
        page=f"{SDMX}/dataflow/{agency}/{flow}/{version}",
        extra=(
            ("version", version),
            ("first_year", start.group(1)),
            ("last_year", end.group(1)),
            ("observations", count),
        ),
    )


def read(src: Source, release: Release) -> list[dict]:
    """The SDMX-CSV (with labels) rows of the release's data file."""
    text = local_path(src.id, release.files[0]).read_text("utf-8-sig")
    if not text.startswith("STRUCTURE"):
        raise ValueError(f"{src.id}: the data file is not SDMX-CSV ({text[:60]!r})")
    return list(csv.DictReader(io.StringIO(text)))


def obs(r: dict) -> float | None:
    return value(r.get("OBS_VALUE"))


def check(rows: list[dict], column: str, allowed: set[str]) -> None:
    seen = {r[column] for r in rows}
    if seen - allowed:
        raise ValueError(f"unexpected {column} values {sorted(seen - allowed)}")


def years(table: Table) -> str:
    ys = sorted({r["year"] for r in table.rows})
    return f"{ys[0]}-{ys[-1]}" if ys else ""
