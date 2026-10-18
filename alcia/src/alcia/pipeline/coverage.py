"""Which data can measure which legislation: a catalogue of processed panels, matched to records.

``build_catalogue`` summarises every processed panel (measures, industry codes by scheme and level,
geography levels and codes, period range). ``coverage`` matches a register record's ANZSIC codes
and jurisdiction against it and reports, for each panel, the finest industry level available for
each of the record's industries, whether the record's state (or finer areas within it) is covered,
and the period range — enough to see before any estimation whether a design is possible.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

import pandas as pd

from ..register.schema import ChangeRecord
from . import schema, store

CATALOGUE = store.PROCESSED / "catalogue.json"
LOCAL_LEVELS = ("GCCSA", "SA4", "SA3", "SA2", "SA2_2011", "LGA", "POA", "IVI_REGION", "CLUE_AREA")


def summarise(df: pd.DataFrame, source: str, table: str) -> list[dict]:
    """One catalogue entry per measure in a panel."""
    out = []
    for measure, g in df.groupby("measure"):
        industries: dict[str, dict[str, list[str]]] = {}
        for (scheme, level), h in g.groupby(["industry_scheme", "industry_level"]):
            industries.setdefault(scheme, {})[level] = sorted(h["industry_code"].unique().tolist())
        geos = {lvl: sorted(h["geo_code"].unique().tolist()) for lvl, h in g.groupby("geo_level")}
        local = g.loc[g["geo_level"].isin(LOCAL_LEVELS), ["geo_level", "geo_code"]].drop_duplicates()
        states_with_local = sorted(
            {s for s in (schema.state_of(lv, c) for lv, c in local.itertuples(index=False)) if s}
        )
        out.append(
            {
                "source": source,
                "table": table,
                "measure": measure,
                "unit": g["unit"].iloc[0],
                "period_type": sorted(g["period_type"].unique().tolist()),
                "first": g["period"].min().date().isoformat(),
                "last": g["period"].max().date().isoformat(),
                "rows": int(len(g)),
                "industries": industries,
                "geo": {lvl: (codes if len(codes) <= 20 else len(codes)) for lvl, codes in geos.items()},
                "local_states": states_with_local,
            }
        )
    return out


def build_catalogue() -> list[dict]:
    entries = []
    for source, table, path in store.panels():
        df = pd.read_parquet(path)
        entries += summarise(df, source, table)
    CATALOGUE.write_text(json.dumps(entries, indent=1) + "\n", encoding="utf-8")
    return entries


def load_catalogue() -> list[dict]:
    return json.loads(CATALOGUE.read_text("utf-8")) if CATALOGUE.exists() else []


@dataclass(frozen=True)
class Match:
    source: str
    table: str
    measure: str
    unit: str
    industry: str  # the record's industry code
    matched_code: str  # the code used in the panel ("" for all-industry panels)
    matched_level: str  # class, group, subdivision, division, total, inferred or occupation
    state: bool  # the record's state (or Australia, for a Commonwealth record) is covered
    local_levels: tuple[str, ...]  # finer geography available in the record's state
    first: str
    last: str
    period_type: str

    def as_dict(self) -> dict:
        return asdict(self)


RANK = {"class": 0, "group": 1, "retail-group": 2, "subdivision": 3, "division": 4, "inferred": 5}


def _industry_match(entry: dict, code: str) -> tuple[str, str] | None:
    """Finest ANZSIC level in the panel covering ``code``: (panel code, level)."""
    from .concord import composition

    ancestors = schema.anzsic_ancestors(code)
    best = None
    for scheme in ("ANZSIC06", "ANZSIC06-inferred"):
        levels = entry["industries"].get(scheme, {})
        for anc in ancestors:
            for level, codes in levels.items():
                if anc in codes:
                    lvl = "inferred" if scheme == "ANZSIC06-inferred" else level
                    if best is None or RANK.get(lvl, 9) < RANK.get(best[1], 9):
                        best = (anc, lvl)
    # Composite source groupings (e.g. Retail Trade groups) that contain the record's code.
    comp = composition()
    for group_code in entry["industries"].get("ANZSIC06", {}).get("retail-group", []):
        classes = [c.rstrip("*") for c in comp.get(group_code, [])]
        contains = any(c == code or _within(c, code) for c in classes)
        if contains and (best is None or RANK["retail-group"] < RANK.get(best[1], 9)):
            best = (group_code, "retail-group")
    if best:
        return best
    # Finer codes can be summed up to the record's code (e.g. classes to a division).
    for scheme in ("ANZSIC06", "ANZSIC06-inferred"):
        for codes in entry["industries"].get(scheme, {}).values():
            if any(_within(c, code) for c in codes if c and c != code):
                lvl = schema.ANZSIC_LEVEL_BY_LENGTH.get(len(code), "total")
                return (code, "inferred" if scheme == "ANZSIC06-inferred" else lvl)
    if "total" in entry["industries"].get("ANZSIC06", {}) or "none" in entry["industries"]:
        return ("", "total")
    return None


def _within(child: str, parent: str) -> bool:
    """Is ANZSIC code ``child`` inside ``parent`` (a division letter or a shorter numeric code)?"""
    from .. import anzsic

    if parent.isalpha():
        return anzsic.division(child) == parent
    return child.startswith(parent) and len(child) > len(parent)


def coverage(record: ChangeRecord, catalogue: list[dict] | None = None) -> list[Match]:
    catalogue = load_catalogue() if catalogue is None else catalogue
    out = []
    state = record.jurisdiction if record.jurisdiction != "CTH" else None
    for entry in catalogue:
        geo = entry["geo"]
        if state:
            state_ok = state in (geo.get("STE") or []) if isinstance(geo.get("STE"), list) else "STE" in geo
            local = tuple(lvl for lvl in LOCAL_LEVELS if lvl in geo and state in entry.get("local_states", []))
        else:
            state_ok = "AUS" in geo or "STE" in geo
            local = tuple(lvl for lvl in LOCAL_LEVELS if lvl in geo)
        for ind in record.industries:
            m = _industry_match(entry, ind.anzsic)
            if m is None:
                continue
            out.append(
                Match(
                    entry["source"],
                    entry["table"],
                    entry["measure"],
                    entry["unit"],
                    ind.anzsic,
                    m[0],
                    m[1],
                    state_ok,
                    local,
                    entry["first"],
                    entry["last"],
                    "/".join(entry["period_type"]),
                )
            )
    order = {**RANK, "occupation": 6, "total": 7}
    return sorted(out, key=lambda m: (m.industry, order.get(m.matched_level, 9), m.source, m.measure))
