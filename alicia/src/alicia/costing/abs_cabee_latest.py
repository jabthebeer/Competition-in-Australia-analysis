"""ABS Counts of Australian Businesses, including Entries and Exits (8165.0): the latest release, for costing.

- Cube 1 (``8165DC01.xlsx``) of the latest release: businesses, entries and exits by ANZSIC division
  (``division_fy``, Table 1) and by employment size (``size_fy``, Table 13) for each year of the release, and
  survival of the businesses operating at the start of the release (``survival``, Table 2).
- Cube 2 (``8165DC02*.xlsx``, ANZSIC class × state × employment size) of the latest release that has one:
  businesses at the start of the year, entries, exits and businesses at the end, with entry and exit rates,
  for the cube's final year, summed over states (``class_size``), at class, subdivision and division level.

The ABS publishes cube 1 in August and cubes 2-11 in December. Until cube 2 of the latest release appears,
``class_size`` comes from the previous release's cube 2: the same file the stitched ``abs_cabee`` panel uses
for its last year (checked by SHA-256 against ``data/manifests/abs_cabee.json`` and by class totals against
``data/processed/abs_cabee/cabee_class_state_fy.csv.gz``). When the December release adds cube 2, discovery
sees it on the latest-release page and the refresh rebuilds this source. The 1-4 and 5-19 employee ranges are
kept apart (the stitched panel sums them to 1-19).

Cells are perturbed by the ABS, so class rows do not sum exactly to published totals. Data: ABS, CC BY 4.0.
"""

from __future__ import annotations

import gzip
import json
import re
from collections import defaultdict

import pandas as pd

from ..pipeline import store
from .base import (
    ABS_LICENCE,
    Release,
    Source,
    Table,
    abs_page,
    anzsic_codes,
    clean_text,
    division_by_name,
    fetch_files,
    fy_end,
    fy_label,
    local_path,
    release_slug,
    remote,
    sheet_rows,
    source_doc,
    value,
)

BASE = "https://www.abs.gov.au/statistics/economy/business-indicators/counts-australian-businesses-including-entries-and-exits"
PAGE = f"{BASE}/latest-release"
SOURCE = Source(
    id="abs_cabee_latest",
    title="Counts of Australian Businesses, including Entries and Exits (8165.0)",
    publisher="Australian Bureau of Statistics",
    licence=ABS_LICENCE,
    url=PAGE,
)
CUBE1 = r"/8165DC01[^/]*\.xlsx$"
CUBE2 = r"/8165DC02[^/]*\.xlsx$"
RELEASE_PAGE = re.compile(r"/counts-australian-businesses-including-entries-and-exits/[a-z]{3}(\d{4})-[a-z]{3}(\d{4})$")
COLUMNS1 = {
    "Operating at start of financial year": "start",
    "Entries - Births": "entries_births",
    "Entries - Other": "entries_other",
    "Entries - Total": "entries",
    "Exits - Cancellations": "exits_cancellations",
    "Exits - Other": "exits_other",
    "Exits - Total": "exits",
    "Net movement of surviving businesses": "net_movement",
    "Operating at end of financial year": "end",
    "Entry rate": "entry_rate_pct",
    "Exit rate": "exit_rate_pct",
}
SIZES = {
    "Non-employing": "nonemp",
    "1-4": "1-4",
    "5-19": "5-19",
    "20-199": "20-199",
    "200+": "200+",
    "Total employing": "employing",
    "Total": "total",
}
COUNT = "count of businesses"


def _end_year(url: str) -> int:
    m = RELEASE_PAGE.search(url)
    return int(m.group(2)) if m else 0


def discover() -> Release:
    page = abs_page(PAGE)
    c1 = page.files(CUBE1)
    if len(c1) != 1:
        raise ValueError(f"expected one cube 1 link on {PAGE}, found {len(c1)}")
    c2, c2_page = page.files(CUBE2), page
    if not c2:  # cube 2 comes later (December): use the latest earlier release that has it
        for url in sorted((u for u in page.links if RELEASE_PAGE.search(u)), key=_end_year, reverse=True):
            prev = abs_page(url)
            if c2 := prev.files(CUBE2):
                c2_page = prev
                break
    if len(c2) != 1:
        raise ValueError(f"expected one cube 2 link, found {len(c2)}")
    s1, s2 = release_slug(c1[0]), release_slug(c2[0])
    return Release(
        id=s1 if s1 == s2 else f"{s1} (cube 1); {s2} (cube 2)",
        date=page.released,
        files=(remote(c1[0]), remote(c2[0])),
        page=PAGE,
        next_release=page.next_release,
        extra=(
            ("cube1_reference_period", page.reference_period),
            ("cube2_reference_period", c2_page.reference_period),
            ("cube2_released", c2_page.released),
        ),
    )


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def _dash(s: str) -> str:
    return clean_text(s).replace("–", "-").replace("—", "-")


def _header(rows: list[list]) -> tuple[int, dict[int, str]]:
    for i, r in enumerate(rows):
        cols = {c: COLUMNS1[_dash(v)] for c, v in enumerate(r) if c > 0 and _dash(v) in COLUMNS1}
        if "start" in cols.values() and "end" in cols.values():
            return i, cols
    raise ValueError("no CABEE cube 1 header row found")


def _blocks(rows: list[list]):
    """(fy, label, {column: value}) for a cube 1 table with financial-year heading rows."""
    hi, cols = _header(rows)
    fy = None
    for r in rows[hi + 2 :]:
        label = _dash(r[0])
        if not label or label.startswith("©"):
            continue
        if re.fullmatch(r"\d{4}-\d{2}", label):
            fy = fy_label(fy_end(label))
            continue
        if all(value(r[c]) is None for c in cols if c < len(r)):
            continue  # a heading such as "Employing"
        if fy is None:
            raise ValueError(f"row {label!r} before any financial year")
        yield fy, label, {name: value(r[c]) if c < len(r) else None for c, name in cols.items()}


def division_table(rows: list[list]) -> Table:
    out, kept = [], set()
    for fy, label, vals in _blocks(rows):
        if label.lower() == "all industries":
            code, name = "TOT", "All industries"
        elif label.lower() == "currently unknown":
            code, name = "UNKNOWN", "Currently unknown"
        else:
            code = division_by_name(label)
            if code is None:
                raise ValueError(f"Table 1: unknown division {label!r}")
            name = anzsic_codes()[code]["name"]
        kept.update(vals)
        out.append({"anzsic": code, "name": name, "fy": fy} | vals)
    cols = [c for c in COLUMNS1.values() if c in kept]
    years = sorted({r["fy"] for r in out})
    return Table(
        description=(
            f"Businesses, entries and exits by ANZSIC division, FY{years[0]} to FY{years[-1]} (8165.0 cube 1, "
            "Table 1). start/end: operating at the start/end of the financial year; entries and exits split into "
            "births/other and cancellations/other; rates as published (entries or exits per 100 businesses "
            "operating at the start). UNKNOWN = industry currently unknown; TOT = all industries."
        ),
        columns={
            "anzsic": "code: ANZSIC 2006 division, UNKNOWN or TOT",
            "name": "text",
            "fy": "financial year (YYYY-YY)",
        }
        | {c: ("per cent" if c.endswith("_pct") else COUNT) for c in cols},
        keys=("anzsic", "fy"),
        rows=[{k: r.get(k) for k in ["anzsic", "name", "fy", *cols]} for r in out],
    )


def size_table(rows: list[list]) -> Table:
    out, kept = [], set()
    for fy, label, vals in _blocks(rows):
        band = SIZES.get(label)
        if band is None:
            raise ValueError(f"Table 13: unknown size range {label!r}")
        kept.update(vals)
        out.append({"size_band": band, "fy": fy} | vals)
    cols = [c for c in COLUMNS1.values() if c in kept]
    years = sorted({r["fy"] for r in out})
    return Table(
        description=(
            f"Businesses, entries and exits by employment size, FY{years[0]} to FY{years[-1]} (8165.0 cube 1, "
            "Table 13). size_band: nonemp (non-employing), 1-4, 5-19, 20-199, 200+ employees, employing (all "
            "employing) or total. net_movement: businesses that changed size range while surviving."
        ),
        columns={"size_band": "text: employment size range", "fy": "financial year (YYYY-YY)"}
        | {c: ("per cent" if c.endswith("_pct") else COUNT) for c in cols},
        keys=("size_band", "fy"),
        rows=[{k: r.get(k) for k in ["size_band", "fy", *cols]} for r in out],
    )


def survival_table(rows: list[list]) -> Table:
    hi = next(i for i, r in enumerate(rows) if any(_dash(v).startswith("Operating in June") for v in r))
    head = [_dash(v) for v in rows[hi]]
    base_col = next(c for c, v in enumerate(head) if v.startswith("Operating in June"))
    cohort = int(re.search(r"(\d{4})", head[base_col]).group(1))
    surv = {c: int(re.search(r"(\d{4})", v).group(1)) for c, v in enumerate(head) if v.startswith("Survived to June")}
    out = []
    for r in rows[hi + 2 :]:
        label = _dash(r[0])
        if not label or label.startswith("©"):
            continue
        code = {"all industries": "TOT", "currently unknown": "UNKNOWN"}.get(label.lower()) or division_by_name(label)
        if code is None:
            raise ValueError(f"Table 2: unknown division {label!r}")
        for c, year in surv.items():
            rate = value(r[c + 1]) if c + 1 < len(r) and _dash(head[c + 1]) == "Survival rate" else None
            out.append(
                {
                    "anzsic": code,
                    "cohort": f"June {cohort}",
                    "years": year - cohort,
                    "operating_at_cohort": value(r[base_col]),
                    "survived": value(r[c]),
                    "survival_rate_pct": rate,
                }
            )
    return Table(
        description=(
            f"Survival of businesses operating in June {cohort}, by ANZSIC division (8165.0 cube 1, Table 2): "
            "number still operating after 1 to 4 years and the survival rate as published."
        ),
        columns={
            "anzsic": "code: ANZSIC 2006 division, UNKNOWN or TOT",
            "cohort": "text: month the cohort was operating",
            "years": "years after the cohort month",
            "operating_at_cohort": COUNT,
            "survived": COUNT,
            "survival_rate_pct": "per cent",
        },
        keys=("anzsic", "years"),
        rows=out,
    )


# ---------------------------------------------------------------- cube 2


def parse_cube2(path) -> pd.DataFrame:
    """Long table (fy, state, anzsic, band, measure, value) from a class × state × size cube, keeping the 1-4
    and 5-19 employee ranges apart. Sheet and column rules follow ``alicia.outcomes.cabee``."""
    from ..outcomes import cabee

    frames = []
    book = pd.ExcelFile(path)
    for sheet in book.sheet_names:
        if cabee._fy_of_sheet(sheet) is None and not re.fullmatch(r"Table \d+", sheet.strip()):
            continue
        raw = pd.read_excel(book, sheet_name=sheet, header=None, dtype=object)
        fy = cabee._fy_of_sheet(sheet, str(raw.iat[3, 0]))
        if fy is None:
            continue
        header_row = next(i for i in range(12) if str(raw.iat[i, 3]).startswith("Operating at start"))
        columns = cabee._columns(raw, header_row)
        if "start|1-4" not in columns:
            raise ValueError(f"{sheet}: cube 2 has no separate 1-4 employee range")
        year_first = str(raw.iat[header_row + 1, 0]).startswith("Year")
        rows = []
        for i in range(header_row + 2, len(raw)):
            r = raw.iloc[i]
            state = cabee.STATES.get(str(r.iat[1] if year_first else r.iat[0]).strip())
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
            rows.append([state, code, *pd.to_numeric(r.iloc[list(columns.values())], errors="coerce").tolist()])
        wide = pd.DataFrame(rows, columns=["state", "anzsic", *columns])
        long = wide.melt(id_vars=["state", "anzsic"], var_name="key", value_name="value")
        long[["measure", "band"]] = long["key"].str.split("|", expand=True)
        frames.append(long.drop(columns="key").assign(fy=fy))
    if not frames:
        raise ValueError(f"{path.name}: no class tables found")
    return pd.concat(frames, ignore_index=True)


BANDS2 = ("nonemp", "1-4", "5-19", "20-199", "200+", "total")


def class_table(long: pd.DataFrame, release_label: str) -> tuple[Table, int, pd.DataFrame]:
    fy = int(long["fy"].max())
    d = long[(long["fy"] == fy) & long["measure"].isin(["start", "entries", "exits", "end"])]
    nat = d.groupby(["anzsic", "band", "measure"], as_index=False)["value"].sum(min_count=1)
    codes = anzsic_codes()
    unknown = sorted(set(nat["anzsic"]) - set(codes))
    if unknown:
        raise ValueError(f"cube 2: classes not in ANZSIC 2006: {unknown[:10]}")
    acc: dict[tuple[str, str], dict] = defaultdict(lambda: {"start": 0.0, "entries": 0.0, "exits": 0.0, "end": 0.0})
    for r in nat.itertuples():
        if pd.isna(r.value):
            continue
        for code in (r.anzsic, r.anzsic[:2], codes[r.anzsic[:2]]["parent"]):
            acc[(code, r.band)][r.measure] += r.value
    levels = {1: "division", 2: "subdivision", 4: "class"}
    rows = []
    for (code, band), v in acc.items():
        start = v["start"]
        rows.append(
            {
                "anzsic": code,
                "level": levels[len(code)],
                "size_band": band,
                "start": v["start"],
                "entries": v["entries"],
                "exits": v["exits"],
                "end": v["end"],
                "entry_rate_pct": round(100 * v["entries"] / start, 2) if start else None,
                "exit_rate_pct": round(100 * v["exits"] / start, 2) if start else None,
            }
        )
    table = Table(
        description=(
            f"Businesses, entries and exits by ANZSIC class, subdivision and division × employment size, "
            f"FY{fy_label(fy)}, all states summed (8165.0 cube 2 of the {release_label} release). size_band: nonemp "
            "(non-employing), 1-4, 5-19, 20-199, 200+ employees or total. Subdivision and division rows are sums "
            "of perturbed class cells, so they differ slightly from published totals. Rates: entries or exits per "
            "100 businesses operating at the start of the year (derived). Classes the ABS codes as unknown "
            "(9999) are left out."
        ),
        columns={
            "anzsic": "code: ANZSIC 2006 class, subdivision or division",
            "level": "text",
            "size_band": "text: employment size range",
            "start": COUNT,
            "entries": COUNT,
            "exits": COUNT,
            "end": COUNT,
            "entry_rate_pct": "per cent, derived",
            "exit_rate_pct": "per cent, derived",
        },
        keys=("anzsic", "size_band"),
        rows=rows,
    )
    return table, fy, nat


def _panel_check(nat: pd.DataFrame, fy: int, release_label: str) -> list[str]:
    """Compare the class totals with the stitched abs_cabee panel (same cube) where it holds that year."""
    path = store.PROCESSED / "abs_cabee" / "cabee_class_state_fy.csv.gz"
    if not path.exists():
        return ["data/processed/abs_cabee panel not present; class totals not cross-checked"]
    with gzip.open(path, "rt", encoding="utf-8") as f:
        panel = pd.read_csv(f, dtype={"anzsic": str})
    p = panel[(panel["release"] == release_label) & (panel["fy"] == fy) & (panel["band"] == "total")]
    if p.empty:
        return [f"the abs_cabee panel has no {release_label} rows for FY{fy_label(fy)}; not cross-checked"]
    ours = nat[nat["band"] == "total"].pivot_table(index="anzsic", columns="measure", values="value", aggfunc="sum")
    theirs = p.groupby(["anzsic", "measure"])["value"].sum().unstack()
    common = [m for m in ("start", "entries", "exits", "end") if m in theirs]
    diff = (ours[common] - theirs.reindex(ours.index)[common]).abs().to_numpy()
    if (diff > 0).any():
        raise ValueError(f"class totals differ from the abs_cabee panel for FY{fy_label(fy)}")
    return [
        f"class totals (all sizes) for FY{fy_label(fy)} equal those in data/processed/abs_cabee/"
        f"cabee_class_state_fy.csv.gz (release {release_label}) for {', '.join(common)}"
    ]


def _manifest_check(sha: str, url: str) -> list[str]:
    mpath = store.MANIFESTS / "abs_cabee.json"
    if not mpath.exists():
        return []
    for e in json.loads(mpath.read_text("utf-8"))["files"]:
        if e["url"] == url:
            same = "the same file" if e["sha256"] == sha else "a different file (the ABS has revised it)"
            return [f"cube 2 is {same} as recorded in data/manifests/abs_cabee.json ({e['file']})"]
    return []


def _release_label(url: str) -> str:
    """'.../jul2021-jun2025/8165DC02.xlsx' -> 'Jul 2021 to Jun 2025' (the abs_cabee panel's release label)."""
    m = re.search(r"/([a-z]{3})(\d{4})-([a-z]{3})(\d{4})/", url)
    return f"{m.group(1).title()} {m.group(2)} to {m.group(3).title()} {m.group(4)}" if m else url


def build(release: Release) -> dict[str, Table]:
    return _build(release)[0]


def _build(release: Release) -> tuple[dict[str, Table], list[str]]:
    c1, c2 = (local_path(SOURCE.id, f) for f in release.files)
    label = _release_label(release.files[1].url)
    long = parse_cube2(c2)
    classes, fy, nat = class_table(long, label)
    checks = _panel_check(nat, fy, label) + _manifest_check(store.sha256(c2), release.files[1].url)
    tables = {
        "division_fy": division_table(sheet_rows(c1, "Table 1")),
        "size_fy": size_table(sheet_rows(c1, "Table 13")),
        "survival": survival_table(sheet_rows(c1, "Table 2")),
        "class_size": classes,
    }
    return tables, checks


def document(release: Release) -> dict:
    tables, checks = _build(release)
    doc = source_doc(SOURCE, release, tables)
    doc["checks"] = checks
    return doc
