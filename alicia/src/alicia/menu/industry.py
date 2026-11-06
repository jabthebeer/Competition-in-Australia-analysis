"""Summary statistics for the industries a register item affects, shown beside its framework assessment.

Context, not effects: the figures describe the affected industries as they are now (size, business turnover,
performance, competition and investment), next to the same figure for all industries, so a reader can judge how
much an item matters and how competitive its industries look. None of them measures what the item did.

Everything comes from files committed to the repository, so the Pages workflow can rebuild the page:

- ``data/processed/costing/parameters.json`` (``alicia costing-params``): ABS Counts of Australian Businesses
  (FY2024-25, by class), Australian Industry (by subdivision), industry multifactor productivity (by division),
  Characteristics of Australian Business, capital expenditure and business R&D, and the RBA's concentration and
  mark-up series (Hambur and Freestone 2025, from BLADE);
- ``data/processed/abs_cabee/class_state_fy.parquet``: business counts by class and state, for the item's own
  state and the change over ten years.

Each figure is reported at the finest level its source publishes (class, subdivision or division) and says so.
"""

from __future__ import annotations

import json
from functools import cached_property

import pandas as pd

from .. import anzsic
from ..register.schema import ChangeRecord

STATE_NAMES = {
    "CTH": "Australia",
    "NSW": "NSW",
    "VIC": "Victoria",
    "QLD": "Queensland",
    "WA": "WA",
    "SA": "SA",
    "TAS": "Tasmania",
    "ACT": "the ACT",
    "NT": "the NT",
}
# The years each source contributes (financial years; the RBA series end when its BLADE extract does).
AI_FY = "2024-25"
BERD_FY = "2023-24"
CAPEX_FY = "2024-25"
MFP_FROM, MFP_TO = "2014-15", "2024-25"
PANEL_FROM, PANEL_TO = 2014, 2024  # financial years by the year they start: 2014-15 and 2024-25
SOURCE_KEYS = (
    "abs_cabee_latest",
    "abs_australian_industry",
    "abs_mfp",
    "rba_hf2025",
    "abs_bcs",
    "abs_capex",
    "abs_berd",
)
NOTE = (
    "These figures describe the industries an item affects as they are now. They are context for the assessment, "
    "not measures of what the item did. Business counts and turnover are for the detailed industries listed; "
    "employment, value added and margins are for the subdivisions that contain them (ABS Australian Industry); "
    "productivity growth, concentration, mark-ups and the survey answers are for the broad industry (ANZSIC "
    "division) of the first industry listed. Concentration and mark-ups come from the RBA's work on the ABS's "
    "confidential firm data (BLADE) and end in 2019 and 2017."
)


# Every measure the snapshot can report: group, label ({where} is the item's state), number format, source, and the
# glossary entry that defines it on the page.
MEASURES: dict[str, tuple[str, str, str, str, str | None]] = {
    "biz": ("Size", "Businesses operating", "int", "abs_cabee_latest", None),
    "employing": ("Size", "Share with employees", "pct0", "abs_cabee_latest", "employing"),
    "biz_here": ("Size", "Businesses operating in {where}", "int", "abs_cabee_latest", None),
    "jobs": ("Size", "People employed", "int", "abs_australian_industry", None),
    "jobs_share": ("Size", "Share of all employment", "pct1", "abs_australian_industry", None),
    "entry": ("Business turnover", "Entry rate", "pct1", "abs_cabee_latest", "entry"),
    "exit": ("Business turnover", "Exit rate", "pct1", "abs_cabee_latest", "exit"),
    "biz_growth": (
        "Business turnover",
        "Growth in business numbers, a year{in}",
        "pct1s",
        "abs_cabee_latest",
        "avgGrowth",
    ),
    "va_worker": ("Performance", "Value added per worker", "dollars", "abs_australian_industry", "valueAdded"),
    "margin": ("Performance", "Profit margin (EBITDA ÷ sales)", "pct1", "abs_australian_industry", "ebitda"),
    "lp": ("Performance", "Labour productivity growth, a year", "pct1s", "abs_mfp", "labourProductivity"),
    "mfp": ("Performance", "Multifactor productivity growth, a year", "pct1s", "abs_mfp", "mfp"),
    "top4": ("Competition", "Share of sales made by the 4 biggest firms", "pct0", "rba_hf2025", "topShare"),
    "markup": ("Competition", "Mark-up (price over marginal cost)", "ratio", "rba_hf2025", "markupRba"),
    "no_comp": ("Competition", "Businesses reporting no effective competition", "pct0", "abs_bcs", "noCompetition"),
    "reg": ("Competition", "Businesses hampered by regulation or compliance", "pct0", "abs_bcs", "regHampered"),
    "capex": ("Investment and innovation", "Capital spending as a share of value added", "pct1", "abs_capex", "capex"),
    "rd": ("Investment and innovation", "Business R&D as a share of value added", "pct2", "abs_berd", "rd"),
}
TILES = ("biz", "entry", "va_worker", "top4")


def measures_dict() -> dict:
    return {
        k: {"group": g, "label": lab, "fmt": f, "source": s, "term": t} for k, (g, lab, f, s, t) in MEASURES.items()
    }


def _sig(v: float | None) -> float | None:
    return None if v is None else float(f"{v:.4g}")


def _rows(tables: dict, key: str) -> list[dict]:
    return tables.get(key, {}).get("rows", [])


def _dedupe(codes: list[str]) -> list[str]:
    """Drop codes inside another listed code (4110 inside 41 or G), so counts are not summed twice."""

    def inside(c: str, other: str) -> bool:
        if c == other:
            return False
        if other.isalpha():
            return (anzsic.division(c) if not c.isalpha() else c) == other
        return not c.isalpha() and c.startswith(other)

    return [c for c in codes if not any(inside(c, o) for o in codes)]


def _unit(code: str) -> str:
    """The Australian Industry unit for a code: its subdivision, or the division for a division code."""
    return code if code.isalpha() else code[:2]


def _growth(a, b, years: int) -> float | None:
    if a in (None, 0) or b is None or a <= 0 or b <= 0:
        return None
    return ((b / a) ** (1 / years) - 1) * 100


class IndustryStats:
    """Loads the sources once; ``snapshot(record)`` gives one item's statistics."""

    def __init__(self, params: dict, panel: pd.DataFrame | None = None):
        self.params = params
        self.tables = params.get("tables", {})
        self.panel = panel

    @classmethod
    def load(cls) -> IndustryStats | None:
        """None when the costing parameters have not been built (the page then shows no statistics)."""
        from ..costing.params import params_path
        from ..pipeline import store

        path = params_path()
        if not path.exists():
            return None
        params = json.loads(path.read_text("utf-8"))
        panel = None
        p = store.PROCESSED / "abs_cabee" / "class_state_fy.parquet"
        if p.exists():
            df = pd.read_parquet(p, columns=["measure", "industry_code", "geo_code", "breakdown", "period", "value"])
            df = df[(df["breakdown"] == "") & (df["measure"] == "businesses_end")]
            panel = df.assign(fy=df["period"].dt.year)[["industry_code", "geo_code", "fy", "value"]]
        return cls(params, panel)

    # --- Lookups -------------------------------------------------------------------------------------------
    @cached_property
    def _cabee(self) -> dict[str, dict]:
        return {r["anzsic"]: r for r in _rows(self.tables, "abs_cabee_latest.class_size") if r["size_band"] == "total"}

    @cached_property
    def _cabee_nonemp(self) -> dict[str, dict]:
        return {r["anzsic"]: r for r in _rows(self.tables, "abs_cabee_latest.class_size") if r["size_band"] == "nonemp"}

    @cached_property
    def _ai(self) -> dict[tuple[str, str], dict]:
        return {(r["anzsic"], r["fy"]): r for r in _rows(self.tables, "abs_australian_industry.industry")}

    @cached_property
    def _mfp(self) -> dict[tuple[str, str], dict]:
        return {(r["anzsic"], r["fy"]): r for r in _rows(self.tables, "abs_mfp.industry")}

    @cached_property
    def _conc(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for r in _rows(self.tables, "rba_hf2025.concentration"):
            if r.get("top4_weighted") is not None and r["fyear"] >= out.get(r["division"], {}).get("fyear", 0):
                out[r["division"]] = r
        return out

    @cached_property
    def _markup(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for r in _rows(self.tables, "rba_hf2025.markups"):
            if r["fyear"] >= out.get(r["division"], {}).get("fyear", 0):
                out[r["division"]] = r
        return out

    def _bcs(self, table: str, division: str | None) -> dict | None:
        group, cat = ("industry", division) if division else ("total", "total")
        return next(
            (
                r
                for r in _rows(self.tables, table)
                if r["group"] == group and r["category"] == cat and r["population"] == "all"
            ),
            None,
        )

    @cached_property
    def _capex(self) -> dict[str, float]:
        return {
            r["anzsic"]: r["capex_current"]
            for r in _rows(self.tables, "abs_capex.actual_fy")
            if r["anzsic"] and r["fy"] == CAPEX_FY and r["asset"] == "total" and r["capex_current"] is not None
        }

    @cached_property
    def _berd(self) -> dict[str, float]:
        return {
            r["anzsic"]: r["rd_total"]
            for r in _rows(self.tables, "abs_berd.subdivision_size")
            if r["rd_total"] is not None
        }

    @cached_property
    def sources(self) -> dict[str, dict]:
        out = {}
        for s in self.params.get("sources", []):
            if s.get("id") in SOURCE_KEYS:
                out[s["id"]] = {
                    "label": s["title"],
                    "url": s["url"],
                    "release": s.get("release"),
                    "licence": s.get("licence"),
                }
        return out

    # --- Pieces --------------------------------------------------------------------------------------------
    def _cabee_counts(self, codes: list[str]) -> dict | None:
        """National businesses, entries and exits in FY2024-25 for the codes (groups summed from their classes)."""
        tot = {"start": 0, "end": 0, "entries": 0, "exits": 0, "nonemp": 0}
        found = False
        for c in codes:
            lvl = anzsic.level(c)
            if lvl == "group":
                rows = [r for k, r in self._cabee.items() if len(k) == 4 and k.isdigit() and k.startswith(c)]
                ne = [r for k, r in self._cabee_nonemp.items() if len(k) == 4 and k.isdigit() and k.startswith(c)]
            else:
                rows = [self._cabee[c]] if c in self._cabee else []
                ne = [self._cabee_nonemp[c]] if c in self._cabee_nonemp else []
            for r in rows:
                found = True
                for k in ("start", "end", "entries", "exits"):
                    tot[k] += r[k] or 0
            tot["nonemp"] += sum(r["end"] or 0 for r in ne)
        return tot if found else None

    @cached_property
    def _cabee_all(self) -> dict:
        divs = [k for k, r in self._cabee.items() if r["level"] == "division"]
        return self._cabee_counts(divs) or {}

    def _panel_change(self, codes: list[str], where: str) -> tuple[float | None, float | None, float | None]:
        """Businesses at the end of FY2024-25 in ``where``, and the average yearly growth in their number since
        FY2014-15 (%), for the codes and for all industries."""
        if self.panel is None or self.panel.empty:
            return None, None, None
        df = self.panel if where == "CTH" else self.panel[self.panel["geo_code"] == where]
        if codes:
            ind = df["industry_code"]
            mask = pd.Series(False, index=df.index)
            for c in codes:
                if c.isalpha():
                    mask |= ind.map(lambda x, c=c: anzsic.division(x) == c)
                else:
                    mask |= ind.str.startswith(c)
            df_c = df[mask]
        else:
            df_c = df
        by = df_c.groupby("fy")["value"].sum()
        all_by = df.groupby("fy")["value"].sum()
        latest = by.get(PANEL_TO)
        years = PANEL_TO - PANEL_FROM
        chg = _growth(by.get(PANEL_FROM), latest, years)
        chg_all = _growth(all_by.get(PANEL_FROM), all_by.get(PANEL_TO), years)
        return (None if latest is None or pd.isna(latest) else float(latest)), chg, chg_all

    def _ai_sum(self, units: list[str], fy: str) -> dict | None:
        rows = [self._ai.get((u, fy)) for u in units]
        rows = [r for r in rows if r]
        if not rows:
            return None
        return {k: sum(r[k] or 0 for r in rows) for k in ("employment", "iva", "sales", "ebitda", "wages")}

    # --- The snapshot --------------------------------------------------------------------------------------
    def snapshot(self, record: ChangeRecord) -> dict:
        direct = [i.anzsic for i in record.industries if i.exposure == "direct"] or [
            i.anzsic for i in record.industries
        ]
        codes = _dedupe(direct)
        where = record.jurisdiction
        economy_wide = not codes
        div = None if economy_wide else (codes[0] if codes[0].isalpha() else anzsic.division(codes[0]))
        units = sorted({_unit(c) for c in codes})
        rows: list[list] = []
        levels: list[str] = []

        def add(measure, value, all_value, level, period):
            if level not in levels:
                levels.append(level)
            rows.append([measure, _sig(value), _sig(all_value), levels.index(level), period])

        named = ", ".join(f"{c} {anzsic.name(c) or ''}".strip() for c in codes) if codes else "all industries"
        lvl_codes = "all industries" if economy_wide else ("detailed industries listed" if len(codes) > 1 else named)
        lvl_units = (
            "all industries"
            if economy_wide
            else ", ".join(
                f"{'division' if u.isalpha() else 'subdivision'} {u} {anzsic.name(u) or ''}".strip() for u in units
            )
        )
        lvl_div = "all industries" if economy_wide else f"division {div} {anzsic.name(div) or ''}".strip()

        # Size
        cab = self._cabee_counts(codes) if codes else self._cabee_all
        cab_all = self._cabee_all
        if cab:
            add("biz", cab["end"], cab_all.get("end"), lvl_codes, "June 2025")
            if cab["end"]:
                emp_share = (1 - cab["nonemp"] / cab["end"]) * 100
                all_share = (1 - cab_all["nonemp"] / cab_all["end"]) * 100 if cab_all.get("end") else None
                add("employing", emp_share, all_share, lvl_codes, "June 2025")
        here, chg, chg_all = self._panel_change(codes, where)
        if where != "CTH" and here is not None:
            add("biz_here", here, None, lvl_codes, "June 2025")
        ai = self._ai_sum(units, AI_FY) if units else None
        ai_all = self._ai.get(("TOT", AI_FY))
        if ai is None and economy_wide:
            ai = ai_all
        if ai and ai_all:
            add("jobs", ai["employment"] * 1000, ai_all["employment"] * 1000, lvl_units, AI_FY)
            add("jobs_share", ai["employment"] / ai_all["employment"] * 100, 100.0, lvl_units, AI_FY)

        # Dynamism
        if cab and cab["start"]:
            all_start = cab_all.get("start")
            add(
                "entry",
                cab["entries"] / cab["start"] * 100,
                cab_all["entries"] / all_start * 100 if all_start else None,
                lvl_codes,
                "2024-25",
            )
            add(
                "exit",
                cab["exits"] / cab["start"] * 100,
                cab_all["exits"] / all_start * 100 if all_start else None,
                lvl_codes,
                "2024-25",
            )
        if chg is not None:
            add("biz_growth", chg, chg_all, lvl_codes, "2014-15 to 2024-25")

        # Performance
        if ai and ai_all and ai["employment"]:
            add(
                "va_worker",
                ai["iva"] / ai["employment"] * 1000,
                ai_all["iva"] / ai_all["employment"] * 1000,
                lvl_units,
                AI_FY,
            )
            if ai["sales"]:
                add(
                    "margin",
                    ai["ebitda"] / ai["sales"] * 100,
                    ai_all["ebitda"] / ai_all["sales"] * 100,
                    lvl_units,
                    AI_FY,
                )
        mk = "MKT16"
        d_key = div if not economy_wide else mk
        lp = _growth(
            self._mfp.get((d_key, MFP_FROM), {}).get("lp_hours"), self._mfp.get((d_key, MFP_TO), {}).get("lp_hours"), 10
        )
        lp_all = _growth(
            self._mfp.get((mk, MFP_FROM), {}).get("lp_hours"), self._mfp.get((mk, MFP_TO), {}).get("lp_hours"), 10
        )
        mfp = _growth(
            self._mfp.get((d_key, MFP_FROM), {}).get("mfp_hours"),
            self._mfp.get((d_key, MFP_TO), {}).get("mfp_hours"),
            10,
        )
        mfp_all = _growth(
            self._mfp.get((mk, MFP_FROM), {}).get("mfp_hours"), self._mfp.get((mk, MFP_TO), {}).get("mfp_hours"), 10
        )
        lvl_mfp = "market sector (16 industries)" if economy_wide else lvl_div
        if lp is not None:
            add("lp", lp, lp_all, lvl_mfp, f"{MFP_FROM} to {MFP_TO}")
        if mfp is not None:
            add("mfp", mfp, mfp_all, lvl_mfp, f"{MFP_FROM} to {MFP_TO}")

        # Competition
        c_key = "TOT" if economy_wide else div
        conc, conc_all = self._conc.get(c_key), self._conc.get("TOT")
        if conc and conc_all:
            add("top4", conc["top4_weighted"] * 100, conc_all["top4_weighted"] * 100, lvl_div, str(conc["fyear"]))
        m, m_all = self._markup.get(c_key), self._markup.get("TOT")
        if m and m_all:
            add("markup", m["markup"], m_all["markup"], lvl_div, str(m["fyear"]))
        bc, bc_all = (
            self._bcs("abs_bcs.competition", None if economy_wide else div),
            self._bcs("abs_bcs.competition", None),
        )
        if bc and bc_all and bc.get("no_effective_competition") is not None:
            add("no_comp", bc["no_effective_competition"], bc_all["no_effective_competition"], lvl_div, "2024-25")
        bb, bb_all = self._bcs("abs_bcs.barriers", None if economy_wide else div), self._bcs("abs_bcs.barriers", None)
        if bb and bb_all and bb.get("government_regulation") is not None:
            add("reg", bb["government_regulation"], bb_all["government_regulation"], lvl_div, "2024-25")

        # Investment and innovation
        ai_cap = self._ai_sum(units, CAPEX_FY) if units else ai_all
        cap_units = (
            units if units and all(u in self._capex for u in units) else ([div] if div and div in self._capex else [])
        )
        if economy_wide:
            cap_units = ["TOT"]
        if cap_units and ai_all:
            iva = (
                ai_cap["iva"]
                if cap_units == units and ai_cap
                else (self._ai.get((cap_units[0], CAPEX_FY)) or {}).get("iva")
            )
            if economy_wide:
                iva = ai_all["iva"]
            capex = sum(self._capex[u] for u in cap_units)
            if iva:
                add(
                    "capex",
                    capex / iva * 100,
                    self._capex.get("TOT", 0) / ai_all["iva"] * 100,
                    lvl_units if cap_units == units else lvl_div,
                    CAPEX_FY,
                )
        ai_rd = self._ai_sum(units, BERD_FY) if units else self._ai.get(("TOT", BERD_FY))
        ai_rd_all = self._ai.get(("TOT", BERD_FY))
        rd_units = units if units else ["TOT"]
        if ai_rd and ai_rd_all and all(u in self._berd for u in rd_units) and ai_rd["iva"]:
            rd = sum(self._berd[u] for u in rd_units) / 1000
            add(
                "rd",
                rd / ai_rd["iva"] * 100,
                self._berd.get("TOT", 0) / 1000 / ai_rd_all["iva"] * 100,
                lvl_units,
                BERD_FY,
            )

        # Rows: [measure, value, all industries, index into levels, period]; measures are defined once (MEASURES).
        return {"industries": named, "economyWide": economy_wide, "where": where, "levels": levels, "rows": rows}
