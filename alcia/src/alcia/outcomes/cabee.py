"""Business entries and exits by state x ANZSIC class x employment size: ABS CABEE (cat. 8165.0).

Each CABEE release publishes a class-level cube for its last one or two financial years. A
long panel is assembled by taking each year from successive releases:

- "own" vintage: a year is taken from the release in which it is the final year, with that
  release's industry coding (the ABS back-casts the final year's codes across a release);
- "overlap" vintage: the same year as published in the next release, kept for vintage checks.

Releases and cubes (employment size ranges) are listed in RELEASES with their source URLs.
Downloads are cached and their SHA-256 recorded. Cell values are perturbed by the ABS.
Data: Australian Bureau of Statistics, CC BY 4.0.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ..legislation.base import make_client
from ..legislation.http import Fetcher

ABS = "https://www.abs.gov.au"
LEGACY = ABS + "/ausstats/subscriber.nsf/log?openagent&{file}&8165.0&Data%20Cubes&{doc}&0&{rel}&{date}&{status}"
CURRENT = (
    ABS
    + "/statistics/economy/business-indicators/counts-australian-businesses-including-entries-and-exits/{slug}/{file}"
)


@dataclass(frozen=True)
class Release:
    label: str  # e.g. "Jun 2010 to Jun 2014"
    published: str  # ISO date
    url: str
    final_fy: int  # financial year (named by the year it ends) that is final in this release


def _legacy(file: str, doc: str, rel: str, date: str, status: str) -> str:
    return LEGACY.format(file=file, doc=doc, rel=rel.replace(" ", "%20"), date=date, status=status)


# Class x main state x employment size cubes, ANZSIC 2006. Found on the ABS release pages on
# 15 Oct 2026. The 2015-19 release page now redirects; 2018-19 is taken from the 2016-20 release.
RELEASES: tuple[Release, ...] = (
    Release(
        "Jun 2007 to Jun 2009",
        "2011-02-16",
        _legacy(
            "ind_class_emp.xls", "D7CD621EA247AC2DCA257838000EE537", "Jun 2007 to Jun 2009", "16.02.2011", "Previous"
        ),
        2009,
    ),
    Release(
        "Jun 2007 to Jun 2011",
        "2012-04-24",
        _legacy(
            "ind_class_emp.xls", "F394068356CEFC69CA2579E90017F9F2", "Jun 2007 to Jun 2011", "24.04.2012", "Previous"
        ),
        2011,
    ),
    Release(
        "Jun 2008 to Jun 2012",
        "2013-08-13",
        _legacy("816501.xls", "9F35ECB631EBF49ECA257BC5001634FF", "Jun 2008 to Jun 2012", "13.08.2013", "Latest"),
        2012,
    ),
    Release(
        "Jun 2009 to Jun 2013",
        "2014-06-23",
        _legacy("816501.xls", "3E734EC9B64A7BE5CA257CE700169734", "Jun 2009 to Jun 2013", "23.06.2014", "Previous"),
        2013,
    ),
    Release(
        "Jun 2010 to Jun 2014",
        "2015-04-08",
        _legacy("816502.xls", "B857CF0DB0E49DD5CA257E200014C371", "Jun 2010 to Jun 2014", "08.04.2015", "Latest"),
        2014,
    ),
    Release(
        "Jun 2011 to Jun 2015",
        "2016-02-26",
        _legacy("816502.xls", "0F13203DC3D529A6CA257F640011D95D", "Jun 2011 to Jun 2015", "26.02.2016", "Latest"),
        2015,
    ),
    Release(
        "Jun 2012 to Jun 2016",
        "2017-02-23",
        _legacy("816502.xls", "ED139A101C8C955DCA2580CF000DB52F", "Jun 2012 to Jun 2016", "23.02.2017", "Latest"),
        2016,
    ),
    Release(
        "Jun 2013 to Jun 2017",
        "2018-02-20",
        _legacy("816502.xls", "7242DE894DFDD3E5CA25823A000AE7A0", "Jun 2013 to Jun 2017", "20.02.2018", "Latest"),
        2017,
    ),
    Release(
        "June 2014 to June 2018",
        "2019-02-21",
        _legacy("816502.xls", "B164DBE8275CCE58CA2583A700121372", "June 2014 to June 2018", "21.02.2019", "Latest"),
        2018,
    ),
    Release("Jul 2016 to Jun 2020", "2021-02-19", CURRENT.format(slug="jul2016-jun2020", file="816502.xls"), 2020),
)

STATES = {
    "New South Wales": "NSW",
    "Victoria": "VIC",
    "Queensland": "QLD",
    "South Australia": "SA",
    "Western Australia": "WA",
    "Tasmania": "TAS",
    "Northern Territory": "NT",
    "Australian Capital Territory": "ACT",
}
STATES.update({abbr: abbr for abbr in STATES.values()})  # the 2007-11 release uses abbreviations
MEASURES = ("start", "entries", "exits", "balancing", "end")
BANDS = ("nonemp", "1-19", "20-199", "200+", "total")


def default_raw_dir() -> Path:
    """Raw cubes live in data/raw/abs_cabee/ at the repository root (never edited, not committed)."""
    from ..pipeline import store

    return store.raw_dir("abs_cabee")


def download(release: Release, folder: Path | None = None) -> Path:
    """Fetch a release's cube once; later calls reuse the cached file."""
    folder = folder or default_raw_dir()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (re.sub(r"[^A-Za-z0-9]+", "_", release.label) + ".xls")
    if not path.exists():
        with make_client() as client:
            path.write_bytes(Fetcher(client).content(release.url))
    return path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fy_of_sheet(name: str) -> int | None:
    """'2008-09' -> 2009; 'June 2014' -> 2014; 'June 2020 b' -> None (experimental point-in-time table)."""
    name = name.strip()
    if m := re.fullmatch(r"(\d{4})-(\d{2})", name):
        return int(m.group(1)) + 1
    if m := re.fullmatch(r"June (\d{4})(?: a)?", name):
        return int(m.group(1))
    return None


def parse_cube(path: Path, release: Release) -> pd.DataFrame:
    """Long table: release, fy, state, anzsic (4-digit class), band, measure, value."""
    frames = []
    for sheet in pd.ExcelFile(path).sheet_names:
        fy = _fy_of_sheet(sheet)
        if fy is None:
            continue
        raw = pd.read_excel(path, sheet_name=sheet, header=None, dtype=object)
        header_row = next(i for i in range(12) if str(raw.iat[i, 3]).startswith("Operating at start"))
        if not str(raw.iat[header_row, 8]).startswith("Entries") or not str(raw.iat[header_row, 13]).startswith(
            "Exits"
        ):
            raise ValueError(f"{release.label} / {sheet}: unexpected column layout")
        year_first = str(raw.iat[header_row + 1, 0]).startswith("Year")
        rows = []
        for i in range(header_row + 2, len(raw)):
            r = raw.iloc[i]
            state_cell = r.iat[1] if year_first else r.iat[0]
            state = STATES.get(str(state_cell).strip())
            if state is None:
                continue
            if year_first:
                m = re.match(r"\s*(\d{4})\b", str(r.iat[2]))
                code = m.group(1) if m else None
            else:
                code = str(r.iat[1]).strip()
                code = code.split(".")[0].zfill(4) if code.replace(".", "").isdigit() else None
            if code is None or code == "9999":
                continue
            values = pd.to_numeric(r.iloc[3:28], errors="coerce").tolist()
            rows.append([state, code, *values])
        if not rows:
            raise ValueError(f"{release.label} / {sheet}: no data rows recognised")
        cols = ["state", "anzsic"] + [f"{m}|{b}" for m in MEASURES for b in BANDS]
        wide = pd.DataFrame(rows, columns=cols)
        long = wide.melt(id_vars=["state", "anzsic"], var_name="key", value_name="value")
        long[["measure", "band"]] = long["key"].str.split("|", expand=True)
        long = long.drop(columns="key")
        long.insert(0, "fy", fy)
        long.insert(0, "release", release.label)
        frames.append(long)
    if not frames:
        raise ValueError(f"{release.label}: no year sheets found")
    return pd.concat(frames, ignore_index=True)


def check_identity(df: pd.DataFrame) -> pd.DataFrame:
    """Rows where start + entries - exits + balancing != end (beyond perturbation tolerance)."""
    w = df[df["band"] == "total"].pivot_table(
        index=["release", "fy", "state", "anzsic"], columns="measure", values="value", aggfunc="first"
    )
    gap = (w["start"] + w["entries"] - w["exits"] + w["balancing"].fillna(0) - w["end"]).abs()
    return w.assign(gap=gap)[gap > 0].reset_index()


def stitch(long: pd.DataFrame, releases: tuple[Release, ...] = RELEASES) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(panel, overlaps). The panel keeps one vintage per year: the release where the year is final,
    else the earliest release containing it. Overlaps hold every other vintage of the same years."""
    by_label = {r.label: r for r in releases}
    long = long.copy()
    long["final_fy"] = long["release"].map(lambda x: by_label[x].final_fy)
    long["published"] = long["release"].map(lambda x: by_label[x].published)
    long["own"] = long["fy"] == long["final_fy"]
    choice = (
        long[["release", "fy", "own", "published"]]
        .drop_duplicates()
        .sort_values(["fy", "own", "published"], ascending=[True, False, True])
        .drop_duplicates("fy")
    )
    keep = set(zip(choice["release"], choice["fy"], strict=True))
    mask = [(r, f) in keep for r, f in zip(long["release"], long["fy"], strict=True)]
    panel = long[mask].drop(columns=["final_fy", "published", "own"])
    overlaps = long[[not m for m in mask]].drop(columns=["final_fy", "published", "own"])
    return panel.reset_index(drop=True), overlaps.reset_index(drop=True)


def to_rates(panel: pd.DataFrame, band: str = "total") -> pd.DataFrame:
    """One row per fy x state x class: counts and entry/exit rates (per business operating at the start)."""
    w = (
        panel[panel["band"] == band]
        .pivot_table(index=["release", "fy", "state", "anzsic"], columns="measure", values="value", aggfunc="first")
        .reset_index()
    )
    w["entry_rate"] = w["entries"] / w["start"]
    w["exit_rate"] = w["exits"] / w["start"]
    return w


def build(raw_dir: Path | None = None, out_dir: Path | None = None) -> dict:
    """Download (if needed), parse and stitch every release; write the panel, overlaps and a manifest."""
    from ..pipeline import store

    out_dir = out_dir or store.PROCESSED / "abs_cabee"
    out_dir.mkdir(parents=True, exist_ok=True)
    parts, manifest = [], []
    for rel in RELEASES:
        path = download(rel, raw_dir)
        parts.append(parse_cube(path, rel))
        manifest.append(
            {
                "release": rel.label,
                "published": rel.published,
                "url": rel.url,
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    long = pd.concat(parts, ignore_index=True)
    panel, overlaps = stitch(long)
    panel.to_csv(out_dir / "cabee_class_state_fy.csv.gz", index=False)
    overlaps.to_csv(out_dir / "cabee_class_state_fy_overlaps.csv.gz", index=False)
    identity = check_identity(panel)
    summary = {
        "source": "ABS, Counts of Australian Businesses, including Entries and Exits (8165.0), CC BY 4.0",
        "releases": manifest,
        "panel_years": sorted(int(x) for x in panel["fy"].unique()),
        "rows": int(len(panel)),
        "identity_failures": int(len(identity)),
    }
    (out_dir / "cabee_manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
