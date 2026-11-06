"""Barriers to entry and profitability for the website, after Grattan Institute (2017), from public data.

Recreates the spirit of Grattan's charts on barriers to entry, business dynamism and profitability
(Minifie, Chisholm and Percival, *Competition in Australia: too little of a good thing?*) with public data
in place of IBISWorld and Morningstar:

- sectors and their barriers-to-entry group: ``alicia.barriers`` (ANZSIC classes, after Grattan's lists);
- company income, profit, tax and book equity by sector: ATO Taxation Statistics, Company Table 4
  (``alicia.pipeline.ato_company``);
- business entry and exit by sector and state: ABS Counts of Australian Businesses (``abs_cabee``);
- the risk-free rate for the cost of equity: RBA 10-year government bond yield (``controls``, table F2.1);
- concentration and mark-ups by division: Hambur and Freestone (2025), RBA RDP 2025-05, from BLADE
  (``data/processed/costing``, source ``rba_hf2025``).

The pages compute returns, super-normal profit and mark-ups from the sums embedded here, so the user can
change the years and the cost of equity. Methods and limitations: docs/methods_competition_charts.md.
"""

from __future__ import annotations

import json

import pandas as pd

from .. import anzsic, barriers
from ..pipeline import controls, schema, store

STATES = (*schema.STATES, "AUS")
PROFIT_MEASURES = ("total_income", "profit_before_tax", "tax_payable", "total_assets", "total_liabilities")
RISK_PREMIUM = 6.0  # market risk premium, per cent (Grattan 2017, Box 2, after Fernandez et al. 2016)
TAX_RATE = 30.0  # company tax rate, per cent, to put super-normal profit before tax (Grattan's mark-up)
COSTING = store.PROCESSED / "costing" / "parameters.json"
NOTES = {
    "classification": (
        "Industries are grouped by barriers to entry as in Grattan Institute's 2017 report: each detailed industry "
        "goes in the group of the sector Grattan names, or by its broad industry otherwise. Grattan called its own "
        "grouping 'inherently subjective'; every choice and its reason is listed in the project's barriers file."
    ),
    "ato": (
        "Company tax returns added up by industry (ATO). Companies only: sole traders, partnerships and trusts are "
        "left out, and so are state-owned businesses that pay tax to their state instead (several electricity "
        "networks, water utilities and ports). Companies choose their own industry code and some large ones change "
        "it, so sector totals can jump between years; averaging over several years smooths this. Equity is book "
        "value and includes goodwill, which Grattan removed, so returns read lower where firms grew by buying others."
    ),
    "excluded": (
        "A year in which a sector's reported liabilities exceed its assets can't give a sensible return, so it is "
        "left out. The large case is banking in 2021-22, where reported liabilities exceed assets by about "
        "$600 billion."
    ),
    "coe": (
        "The cost of equity is the average 10-year government bond rate over the chosen years plus 6 percentage "
        "points, the same for every sector. Grattan used the same 6 points, adjusted for each sector's risk with "
        "Morningstar data that aren't public. You can type in a different rate."
    ),
    "cabee": (
        "Entry and exit rates are new and closed businesses per 100 operating at the start of each year (ABS "
        "business register). The ABS slightly alters small counts to protect confidentiality."
    ),
    "employing": (
        "Counting businesses with employees. Since about 2016, rideshare drivers and delivery riders registering as "
        "sole traders have swamped the counts in a few industries (taxis, couriers and transport support), so they "
        "are left out by default."
    ),
    "rba": (
        "From Hambur and Freestone (2025), RBA Research Discussion Paper 2025-05, using the ABS's confidential BLADE "
        "business data. Each broad industry is the average of its detailed industries, with bigger industries "
        "counting for more. Years are as labelled by the authors."
    ),
}


def _num(v, digits: int = 1):
    return None if v is None or pd.isna(v) else round(float(v), digits)


def _groups_meta() -> list[dict]:
    meta = barriers.groups()
    return [{"id": g, **meta[g]} for g in barriers.GROUPS]


def _classes(codes) -> pd.DataFrame:
    """Class -> sector key, sector label and barriers group. Codes that are not ANZSIC 2006 classes (CABEE has a
    few small ones, such as 0310) are left out."""
    rows = []
    for c in sorted(c for c in set(codes) if anzsic.name(c) is not None):
        key, label = barriers.sector(c)
        rows.append({"code": c, "sector": key, "label": label, "group": barriers.group(c)})
    return pd.DataFrame(rows)


def _whole_groups(classes: set[str]) -> list[str] | None:
    """The ANZSIC groups a set of classes makes up exactly, or None if it splits a group."""
    groups = sorted({c[:3] for c in classes})
    members = {c for c in anzsic._codes() if len(c) == 4 and c[:3] in groups}
    return groups if members == classes else None


def ato_sectors() -> tuple[list[int], list[dict]]:
    """Company sums by sector and income year, 2018-19 on.

    A sector made of whole ANZSIC groups takes the group table (4A), which publishes every group in every
    year; a sector that splits a group sums its classes from the industry-code table (4B), which leaves some
    out in some years (banking in 2018-19 and 2019-20, for example). A missing year is null, not zero."""
    panel = store.read_panel("ato_company", "class_fy")
    panel = panel[(panel["industry_level"] == "class") & panel["measure"].isin(PROFIT_MEASURES)]
    panel = panel.assign(year=panel["period"].dt.year)
    years = sorted(int(y) for y in panel["year"].unique())
    grp = store.read_panel("ato_company", "group_fy")
    grp = grp[(grp["industry_level"] == "group") & grp["measure"].isin(PROFIT_MEASURES)]
    grp = grp.assign(year=grp["period"].dt.year)
    grp = grp[grp["year"].isin(years)]
    cls = _classes(c for c in anzsic._codes() if len(c) == 4)
    by_class = panel.merge(cls, left_on="industry_code", right_on="code")
    class_sums = by_class.pivot_table(index=["sector", "year"], columns="measure", values="value", aggfunc="sum")
    out = []
    for key, g in cls.groupby("sector"):
        whole = _whole_groups(set(g["code"]))
        if whole:
            rows = grp[grp["industry_code"].isin(whole)]
            s = rows.pivot_table(index="year", columns="measure", values="value", aggfunc="sum")
            basis, published = "group", sorted(set(rows["industry_code"]))
        elif key in class_sums.index.get_level_values("sector"):
            s = class_sums.loc[key]
            basis, published = "class", sorted(set(g["code"]) & set(by_class["code"]))
        else:
            continue
        if s.empty:
            continue
        s = s.reindex(index=years, columns=list(PROFIT_MEASURES))
        out.append(
            {
                "key": key,
                "label": g["label"].iloc[0],
                "group": g["group"].iloc[0],
                "basis": basis,
                "codes": published,
                "income": [_num(v, 3) for v in s["total_income"]],
                "pbt": [_num(v, 3) for v in s["profit_before_tax"]],
                "npat": [_num(v, 3) for v in s["profit_before_tax"] - s["tax_payable"]],
                "equity": [_num(v, 3) for v in s["total_assets"] - s["total_liabilities"]],
                "assets": [_num(v, 0) for v in s["total_assets"]],
            }
        )
    return years, sorted(out, key=lambda r: (barriers.GROUPS.index(r["group"]), r["label"]))


def _income_weights() -> dict[str, float]:
    panel = store.read_panel("ato_company", "class_fy")
    inc = panel[(panel["industry_level"] == "class") & (panel["measure"] == "total_income")]
    return inc.groupby("industry_code")["value"].mean().to_dict()


def ato_group_series() -> dict:
    """Return on equity by barriers group and income year, from Table 4A (ANZSIC groups), 2014-15 on.

    An ANZSIC group whose classes fall in different barriers groups takes the group with most of its company
    income in the class table (``barriers.aggregate_group``); those groups are listed. Group-years with
    liabilities above assets are left out and listed."""
    panel = store.read_panel("ato_company", "group_fy")
    panel = panel[(panel["industry_level"] != "total") & panel["measure"].isin(PROFIT_MEASURES)]
    w = panel.pivot_table(index=["industry_code", "period"], columns="measure", values="value").reset_index()
    weights = _income_weights()
    codes = sorted(w["industry_code"].unique())
    assigned = {c: barriers.aggregate_group(c, weights) for c in codes}
    w = w.assign(
        year=w["period"].dt.year,
        group=w["industry_code"].map(assigned),
        equity=w["total_assets"] - w["total_liabilities"],
        npat=w["profit_before_tax"] - w["tax_payable"],
    )
    years = sorted(int(y) for y in w["year"].unique())
    bad = w[~(w["equity"] > 0)]
    ok = w[w["equity"] > 0]
    sums = ok.groupby(["group", "year"])[["npat", "equity", "total_income"]].sum()
    series = {
        g: {
            "npat": [_num(sums["npat"].get((g, y)), 3) for y in years],
            "equity": [_num(sums["equity"].get((g, y)), 3) for y in years],
            "income": [_num(sums["total_income"].get((g, y)), 3) for y in years],
        }
        for g in barriers.GROUPS
    }
    mixed = []
    for c in codes:
        classes = [k for k in anzsic._codes() if len(k) == 4 and k.startswith(c)]
        if len({barriers.group(k) for k in classes}) > 1:
            mixed.append({"code": c, "label": anzsic.name(c), "group": assigned[c]})
    excluded = [
        {
            "code": r.industry_code,
            "label": anzsic.name(r.industry_code),
            "year": int(r.year),
            "group": r.group,
            "assets": _num(r.total_assets, 0),
        }
        for r in bad.itertuples()
        if r.total_assets and r.total_assets >= 1000  # list those with at least $1 billion of assets
    ]
    return {"years": years, "groups": series, "mixed": mixed, "excluded": excluded}


EMPLOYING = ("1-19 employees", "20-199 employees", "200+ employees")


def cabee_by_sector() -> tuple[list[int], dict, dict, dict, dict]:
    """Business counts, entries and exits, for all businesses and for employing businesses only: by sector for
    Australia and for each state, and by barriers group for each state and Australia; with each sector's label
    and group. Employing businesses are counted in the size band they were in (entries and exits by size, as the
    ABS publishes them), so a business that takes on its first employee is not an entry."""
    raw = store.read_panel("abs_cabee", "class_state_fy")
    years = sorted(int(y) for y in raw["period"].dt.year.unique())
    cls = _classes(raw["industry_code"])
    by_sector, by_group, by_sector_state = {}, {}, {}
    for scope, keep in (("all", raw["breakdown"] == ""), ("employing", raw["breakdown"].isin(EMPLOYING))):
        cab = raw[keep].assign(year=raw.loc[keep, "period"].dt.year)
        d = cab.merge(cls, left_on="industry_code", right_on="code")
        by_sector[scope], by_group[scope], by_sector_state[scope] = _cabee_arrays(d, years)
    info = {r.sector: [r.label, r.group] for r in cls.drop_duplicates("sector").itertuples()}
    return years, by_sector, by_group, by_sector_state, info


def _cabee_arrays(d: pd.DataFrame, years: list[int]) -> tuple[dict, dict, dict]:
    measures = {"businesses_start": "start", "businesses_end": "end", "entries": "entries", "exits": "exits"}
    # Sectors by state carry only what entry and exit rates and net change need, to keep the page small.
    flows = {k: v for k, v in measures.items() if k != "businesses_end"}

    def arrays(frame: pd.DataFrame, keys: list[str], measures: dict = measures) -> dict:
        s = frame.groupby([*keys, "measure", "year"])["value"].sum()
        out: dict = {}
        for idx in s.index.droplevel(["measure", "year"]).unique():
            idx = idx if isinstance(idx, tuple) else (idx,)
            cell = {}
            for m, short in measures.items():
                vals = s.get((*idx, m))
                cell[short] = [None if vals is None or y not in vals else int(round(vals[y])) for y in years]
            node = out
            for k in idx[:-1]:
                node = node.setdefault(k, {})
            node[idx[-1]] = cell
        return out

    states = arrays(d, ["geo_code", "group"])
    states["AUS"] = arrays(d, ["group"])
    return arrays(d, ["sector"]), states, arrays(d, ["geo_code", "sector"], flows)


def _rba(table: str) -> list[dict]:
    if not COSTING.exists():
        return []
    tables = json.loads(COSTING.read_text("utf-8"))["tables"]
    return tables.get(f"rba_hf2025.{table}", {}).get("rows", [])


def rba_concentration() -> dict:
    rows = [r for r in _rba("concentration") if r.get("top4_weighted") is not None]
    years = sorted({int(r["fyear"]) for r in rows})
    by = {}
    for r in rows:
        by.setdefault(r["division"], {})[int(r["fyear"])] = r
    measures = ("top4_weighted", "top10_weighted", "top20_weighted", "top5pc_weighted")
    return {
        "years": years,
        "values": {
            div: {
                m: [_num(v[y].get(m) * 100 if y in v and v[y].get(m) is not None else None, 4) for y in years]
                for m in measures
            }
            for div, v in sorted(by.items())
        },
    }


def rba_markups() -> dict:
    rows = _rba("markups")
    years = sorted({int(r["fyear"]) for r in rows})
    by = {}
    for r in rows:
        by.setdefault(r["division"], {})[int(r["fyear"])] = r["markup"]
    return {
        "years": years,
        "values": {div: [_num(v.get(y), 3) for y in years] for div, v in sorted(by.items())},
    }


def bond_yields() -> dict:
    nm = controls.load("national_month")
    y = nm[(nm["source"] == "rba_yields") & (nm["breakdown"] == "10 year bond")].sort_values("period")
    return {
        "periods": [p.strftime("%Y-%m") for p in y["period"]],
        "values": [_num(v, 3) for v in y["value"]],
        "vintage": y["vintage"].iloc[-1] if len(y) else "",
    }


def _divisions() -> list[dict]:
    return [{"code": c, "name": anzsic.name(c)} for c in "ABCDEFGHIJKLMNOPQRS"] + [
        {"code": "TOT", "name": "All industries"}
    ]


def _vintage(table: str) -> str:
    years = store.read_panel("ato_company", table)["period"].dt.year
    first, last = int(years.min()), int(years.max())
    table_name = "4B, by industry code" if table == "class_fy" else "4A, by ANZSIC group"
    return f"income years {first}-{(first + 1) % 100:02d} to {last}-{(last + 1) % 100:02d}, Table {table_name}"


def barriers_payload() -> dict:
    """For The state of competition in Australia page: entry and exit by barriers group and by sector (Australia and
    each state, so every group can be broken into its sectors), company profit by sector (for group shares, the
    sectors in each group and the entry-and-returns chart), and concentration by division."""
    ato_years, sectors = ato_sectors()
    biz_years, biz_sector, biz_states, biz_sector_states, biz_info = cabee_by_sector()
    for s in sectors:
        s.pop("assets", None)
    return {
        "groups": _groups_meta(),
        "atoYears": ato_years,
        "sectors": sectors,
        "bizYears": biz_years,
        "bizSector": biz_sector,
        "bizSectorState": biz_sector_states,
        "bizSectorInfo": biz_info,
        "bizGroup": biz_states,
        "concentration": rba_concentration(),
        "divisions": _divisions(),
        "vintages": {"ato": _vintage("class_fy")},
        "notes": {k: NOTES[k] for k in ("classification", "ato", "excluded", "cabee", "employing", "rba")},
    }


def profit_payload() -> dict:
    """For the Economic conditions page: company returns by sector and barriers group, and over time."""
    ato_years, sectors = ato_sectors()
    return {
        "groups": _groups_meta(),
        "years": ato_years,
        "sectors": sectors,
        "series": ato_group_series(),
        "yields": bond_yields(),
        "riskPremium": RISK_PREMIUM,
        "taxRate": TAX_RATE,
        "markups": rba_markups(),
        "divisions": _divisions(),
        "vintages": {"ato": _vintage("class_fy"), "atoGroups": _vintage("group_fy")},
        "notes": {k: NOTES[k] for k in ("classification", "ato", "excluded", "coe", "rba")},
    }
