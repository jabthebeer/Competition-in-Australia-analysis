"""The common outcome-panel format every data connector writes.

One row per (source, measure, industry, geography, period). Industry and geography carry their
classification scheme and level, so any panel can be matched to a register record's ANZSIC codes
and jurisdiction (``alicia.pipeline.coverage``).

Columns
- source: connector id, e.g. "abs_retail" (see ``alicia.pipeline.sources``)
- measure: e.g. "turnover", "employed", "hours_actual", "entries", "exits", "registrations"
- unit: e.g. "AUD m", "persons '000", "hours '000", "count"
- adjustment: "original", "seasonally adjusted", "trend", "chain volume" or ""
- industry_scheme: "ANZSIC06", "ANZSCO", "ANZSIC06-inferred" or "none"
- industry_level: "total", "division", "subdivision", "group", "class", or a source-specific
  grouping such as "retail-group" (with ``industry_code`` holding the nearest ANZSIC code)
- industry_code, industry_label
- geo_level: "AUS", "STE", "GCCSA", "SA4", "SA3", "SA2", "LGA", "POA" or a source-specific region
  ("SA2_2011": ASGS 2011 SA2s in older releases; "IVI_REGION": Jobs and Skills Australia regions;
  "CLUE_AREA": City of Melbourne small areas). SA2 and the other ASGS levels are 2021 boundaries
- geo_code: state abbreviation for STE (NSW, VIC, ...), ASGS code or postcode otherwise;
  "<state>:<name>" for IVI_REGION and the small-area name for CLUE_AREA
- breakdown: a further split within the cell, e.g. an employment-size band, entity type or sex
  ("" when none)
- period_type: "day", "week", "month", "quarter", "fy" or "year" (calendar); period: the period's first day
- value; vintage: release or retrieval date of the source data
"""

from __future__ import annotations

import pandas as pd

COLUMNS = (
    "source",
    "measure",
    "unit",
    "adjustment",
    "industry_scheme",
    "industry_level",
    "industry_code",
    "industry_label",
    "geo_level",
    "geo_code",
    "breakdown",
    "period_type",
    "period",
    "value",
    "vintage",
)
STRING_COLUMNS = tuple(c for c in COLUMNS if c not in ("period", "value"))
INDUSTRY_SCHEMES = {"ANZSIC06", "ANZSCO", "ANZSIC06-inferred", "none"}
INDUSTRY_LEVELS = {"total", "division", "subdivision", "group", "class", "retail-group", "occupation"}
GEO_LEVELS = {"AUS", "STE", "GCCSA", "SA4", "SA3", "SA2", "SA2_2011", "LGA", "POA", "IVI_REGION", "CLUE_AREA"}
PERIOD_TYPES = {"day", "week", "month", "quarter", "fy", "year"}
STATES = ("NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT")
STATE_CODES = {"1": "NSW", "2": "VIC", "3": "QLD", "4": "SA", "5": "WA", "6": "TAS", "7": "NT", "8": "ACT"}
STATE_NAMES = {
    "New South Wales": "NSW",
    "Victoria": "VIC",
    "Queensland": "QLD",
    "South Australia": "SA",
    "Western Australia": "WA",
    "Tasmania": "TAS",
    "Northern Territory": "NT",
    "Australian Capital Territory": "ACT",
}
ANZSIC_LEVEL_BY_LENGTH = {1: "division", 2: "subdivision", 3: "group", 4: "class"}


class PanelError(ValueError):
    pass


def make(df: pd.DataFrame, **constants) -> pd.DataFrame:
    """Add constant columns, order and type the columns, and validate."""
    out = df.copy()
    for k, v in constants.items():
        out[k] = v
    for c in COLUMNS:
        if c not in out:
            out[c] = ""
    out = out[list(COLUMNS)]
    for c in STRING_COLUMNS:
        out[c] = out[c].fillna("").astype(str)
    out["period"] = pd.to_datetime(out["period"]).dt.normalize()
    out["value"] = pd.to_numeric(out["value"], errors="coerce").astype(float)
    validate(out)
    return out.reset_index(drop=True)


def validate(df: pd.DataFrame) -> None:
    missing = [c for c in COLUMNS if c not in df]
    if missing:
        raise PanelError(f"missing columns: {missing}")
    checks = (
        ("industry_scheme", INDUSTRY_SCHEMES),
        ("industry_level", INDUSTRY_LEVELS),
        ("geo_level", GEO_LEVELS),
        ("period_type", PERIOD_TYPES),
    )
    for col, allowed in checks:
        bad = set(df[col].unique()) - allowed
        if bad:
            raise PanelError(f"{col}: unexpected values {sorted(bad)[:5]}")
    states = df.loc[df["geo_level"] == "STE", "geo_code"]
    if not set(states.unique()) <= set(STATES):
        raise PanelError(f"geo_code for STE must be a state abbreviation, got {sorted(set(states) - set(STATES))[:5]}")
    anz = df[
        df["industry_scheme"].str.startswith("ANZSIC06") & df["industry_level"].isin(ANZSIC_LEVEL_BY_LENGTH.values())
    ]
    wrong = anz[anz["industry_code"].str.len().map(ANZSIC_LEVEL_BY_LENGTH) != anz["industry_level"]]
    if len(wrong):
        example = wrong.iloc[0][["industry_code", "industry_level"]].to_dict()
        raise PanelError(f"ANZSIC code length does not match its level, e.g. {example}")
    keys = [c for c in COLUMNS if c not in ("value", "industry_label", "unit", "vintage")]
    dups = df.duplicated(subset=keys)
    if dups.any():
        raise PanelError(f"{int(dups.sum())} duplicate rows on the panel keys")


def anzsic_ancestors(code: str) -> list[str]:
    """A code and its parents, finest first: '4610' -> ['4610', '461', '46', 'I']."""
    from .. import anzsic

    out = [code]
    if len(code) >= 2:
        out += [code[:n] for n in (3, 2) if n < len(code)]
        div = anzsic.division(code)
        if div:
            out.append(div)
    return out


# Australia Post postcode ranges by state (ACT ranges sit inside NSW's, so they are checked first).
_POSTCODE_RANGES = (
    ("ACT", ((200, 299), (2600, 2618), (2900, 2920))),
    ("NSW", ((1000, 2599), (2619, 2899), (2921, 2999))),
    ("VIC", ((3000, 3999), (8000, 8999))),
    ("QLD", ((4000, 4999), (9000, 9999))),
    ("SA", ((5000, 5999),)),
    ("WA", ((6000, 6999),)),
    ("TAS", ((7000, 7999),)),
    ("NT", ((800, 999),)),
)


def state_of(geo_level: str, code: str) -> str | None:
    """The state a geographic code lies in, or None (Australia-wide, other territories, unknown)."""
    if geo_level == "STE":
        return code if code in STATES else None
    if geo_level == "POA":
        try:
            n = int(code)
        except ValueError:
            return None
        for st, ranges in _POSTCODE_RANGES:
            if any(lo <= n <= hi for lo, hi in ranges):
                return st
        return None
    if geo_level in {"GCCSA", "SA4", "SA3", "SA2", "SA2_2011", "LGA"} and code[:1] in STATE_CODES:
        return STATE_CODES[code[:1]]
    if geo_level == "IVI_REGION":
        st = code.split(":", 1)[0]
        return st if st in STATES else None
    if geo_level == "CLUE_AREA":
        return "VIC"
    return None
