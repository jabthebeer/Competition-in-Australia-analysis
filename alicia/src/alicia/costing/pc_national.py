"""Productivity Commission: PC National CGE model results for *National Competition Policy: modelling proposed
reforms* (2024), for the Layer B back-test (forward plan P4).

From the PC's results workbook (``ncp-pc-national-modelling.xlsx``, linked from the report page):

- ``simulations``: one row per simulation tab (27 scenarios plus the lower- and higher-bound tests): the PC
  scenario code, names, the PC National sectors shocked, the scenario (shock) text, and the results as
  published: macroeconomic results and real GSP by state (per cent change from the baseline, long run);
- ``initial_gsp``: initial gross state product by PC National industry (114) and state, $ million 2018-19,
  from the model database ("Initial data" tab);
- ``linearity``: the linearity tests (the shock scaled to 25, 50, 75 and 100 per cent).

Not extracted: government accounts, CPI components and the industry contributions to real GSP. In some tabs
the contributions block's columns do not line up with its headings (in L2 the first data column matches AUST
in the real GSP block, not NSW), so any later use must align them by checking the totals. In L1, the real GSP
block (AUST 0.386) does not fit L1's real GDP (0.192) and nearly equals L2's real GSP: it appears to come from
the L2 simulation. Values are kept as published; ``gsp_gap`` shows real GSP (AUST) minus real GDP.

Licence: CC BY 4.0 under the PC's copyright statement; attribute "Source: Productivity Commission".
"""

from __future__ import annotations

import re

from .base import (
    Release,
    Source,
    Table,
    clean_text,
    fetch_files,
    get,
    links,
    local_path,
    page_text,
    remote,
    sheet_names,
    sheet_rows,
    value,
)

PAGE = "https://www.pc.gov.au/inquiries-and-research/competition-analysis/report"
SOURCE = Source(
    id="pc_national",
    title="PC National CGE model results: National Competition Policy, modelling proposed reforms",
    publisher="Productivity Commission",
    licence="CC BY 4.0 (Productivity Commission copyright statement, https://www.pc.gov.au/copyright/); "
    "attribute 'Source: Productivity Commission'",
    url=PAGE,
)
WORKBOOK = re.compile(r"^https://assets\.pc\.gov\.au/[^?]+/ncp-pc-national-modelling\.xlsx(\?VersionId=([\w.-]+))?$")
STATES = ("NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT")


def discover() -> Release:
    html = get(PAGE).text
    found = [u for u in links(html, PAGE) if WORKBOOK.match(u)]
    if len(found) != 1:
        raise ValueError(f"{PAGE}: expected one link to the PC National results workbook, found {len(found)}")
    url = found[0]
    version = WORKBOOK.match(url).group(2) or "unversioned"
    m = re.search(r"Released (\d{1,2}) ?/ ?(\d{1,2}) ?/ ?(\d{4})", page_text(html))
    date = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else None
    return Release(
        id=f"report released {date}; workbook VersionId {version}",
        date=date,
        files=(remote(url, folder=version, name="ncp-pc-national-modelling.xlsx"),),
        page=PAGE,
        extra=(("workbook_version", version),),
    )


def fetch(release: Release) -> None:
    fetch_files(SOURCE, release)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _find(rows: list[list], text: str, start: int = 0) -> int | None:
    return next((i for i in range(start, len(rows)) if clean_text(rows[i][0]) == text), None)


def simulation(tab: str, rows: list[list]) -> tuple[dict, dict[str, str]]:
    """One simulation tab: its description, macro results and real GSP. Also returns {column: label}."""

    def after(label: str) -> str:
        i = _find(rows, label)
        return clean_text(rows[i][2]) if i is not None and len(rows[i]) > 2 else ""

    code = after("PC scenario code:")
    sectors_i, scenario_i, macro_i = (
        _find(rows, "PC National sectors:"),
        _find(rows, "Scenario"),
        _find(rows, "Macroeconomic results (%)"),
    )
    if not code or scenario_i is None or macro_i is None:
        raise ValueError(f"{tab}: not in the simulation layout")
    sectors = " ".join(clean_text(r[2]) for r in rows[sectors_i:scenario_i] if len(r) > 2 and clean_text(r[2]))
    shocks = [" ".join(clean_text(v) for v in r if clean_text(v)) for r in rows[scenario_i + 1 : macro_i]]
    out = {
        "tab": tab,
        "code": code,
        "title": clean_text(rows[0][0]),
        "long_name": after("PC long name:"),
        "sectors": sectors,
        "scenario": " | ".join(s for s in shocks if s),
        "variant": "lower" if tab.endswith("_lower") else "higher" if tab.endswith("_higher") else "central",
    }
    labels = {}
    for r in rows[macro_i + 1 :]:
        label = clean_text(r[0])
        if not label:
            if labels:
                break
            continue
        col = _slug(label)
        labels[col] = label
        out[col] = value(r[2]) if len(r) > 2 else None
    gsp_i = _find(rows, "Real GSP (%)", macro_i)
    if gsp_i is None:
        raise ValueError(f"{tab}: no real GSP block")
    for r in rows[gsp_i + 1 : gsp_i + 12]:
        st = clean_text(r[0])
        if st in (*STATES, "AUST"):
            col = f"real_gsp_{st.lower()}"
            labels[col] = f"Real GSP, {st}"
            out[col] = value(r[2])
    return out, labels


def linearity(tab: str, rows: list[list]) -> list[dict]:
    i = _find(rows, "Summary results")
    if i is None:
        raise ValueError(f"{tab}: no summary results")
    head = rows[i + 1]
    out = []
    # One or two blocks side by side: a label column followed by GDP, CPI and the two net revenues.
    starts = [c for c, v in enumerate(head) if clean_text(v) == "GDP (%)"]
    for s in starts:
        for r in rows[i + 2 : i + 12]:
            label = clean_text(r[s - 1]) if s - 1 < len(r) else ""
            m = re.fullmatch(r"(\S+) (\d+)%", label)
            if not m:
                continue
            out.append(
                {
                    "tab": tab,
                    "scenario": m.group(1),
                    "share_pct": int(m.group(2)),
                    "real_gdp": value(r[s]),
                    "cpi": value(r[s + 1]),
                    "national_net_revenue": value(r[s + 2]),
                    "states_net_revenue": value(r[s + 3]),
                }
            )
    return out


def initial_gsp(rows: list[list]) -> list[dict]:
    i = next(i for i, r in enumerate(rows) if clean_text(r[0]).startswith("Gross State Product"))
    head = [clean_text(v) for v in rows[i + 1]]
    cols = {c: v for c, v in enumerate(head) if v in (*STATES, "Total")}
    out = []
    for r in rows[i + 2 :]:
        name = clean_text(r[0])
        if not name:
            break
        m = re.fullmatch(r"(\d+) (\S+)", clean_text(r[1]))
        if name == "Total":
            no, code = 0, "TOTAL"
        elif m:
            no, code = int(m.group(1)), m.group(2)
        else:
            raise ValueError(f"Initial data: unexpected row {name!r}")
        out.append({"pcn_no": no, "pcn_code": code, "name": name} | {cols[c].lower(): value(r[c]) for c in cols})
    return out


def build(release: Release) -> dict[str, Table]:
    path = local_path(SOURCE.id, release.files[0])
    sims, labels, lin, init = [], {}, [], None
    for tab in sheet_names(path):
        rows = sheet_rows(path, tab)
        if tab == "Initial data":
            init = initial_gsp(rows)
        elif _find(rows, "Summary results") is not None:
            lin += linearity(tab, rows)
        elif _find(rows, "Macroeconomic results (%)") is not None:
            s, lab = simulation(tab, rows)
            sims.append(s)
            labels |= lab
    if init is None or not sims:
        raise ValueError("PC National workbook: initial data or simulation tabs not found")
    by_tab = {s["tab"]: s for s in sims}
    for r in lin:  # flag tests whose 100% row reproduces the main tab's real GDP
        main = by_tab.get(r["scenario"])
        r["matches_main_tab"] = bool(
            main and r["share_pct"] == 100 and abs((main.get("real_gdp") or 0) - (r["real_gdp"] or 0)) < 5e-4
        )
    for s in sims:
        gsp, gdp = s.get("real_gsp_aust"), s.get("real_gdp")
        s["gsp_gap"] = gsp - gdp if gsp is not None and gdp is not None else None
    labels["gsp_gap"] = "real GSP (AUST) minus real GDP, derived (a large gap flags a tab to check; see L1)"
    result_cols = [c for c in labels if c in {k for s in sims for k in s}]
    text = ["tab", "code", "title", "long_name", "sectors", "scenario", "variant"]
    rows = [{c: s.get(c) for c in [*text, *result_cols]} for s in sims]
    pct = "per cent change from the baseline (long run)"
    return {
        "simulations": Table(
            description=(
                "PC National simulations for the NCP reform modelling, one row per results tab: the PC's scenario "
                "code and names, the sectors shocked, the scenario text (shocks, separated by ' | '), the variant "
                "(central, or a lower or higher bound test), and the published macroeconomic results and real GSP "
                "by state, as published. L1's real GSP block appears to be the L2 simulation's (AUST 0.386 against "
                "L1's real GDP of 0.192): do not use L1's state results. Column labels: "
                + "; ".join(f"{c} = {labels[c]}" for c in result_cols)
                + "."
            ),
            columns={
                "tab": "text: workbook tab",
                "code": "code: PC scenario code",
                "title": "text",
                "long_name": "text",
                "sectors": "text: PC National sectors shocked",
                "scenario": "text: the shocks as described by the PC",
                "variant": "text: central, lower or higher",
            }
            | {c: pct for c in result_cols if c != "gsp_gap"}
            | {"gsp_gap": "percentage points, derived"},
            keys=("tab",),
            rows=rows,
        ),
        "initial_gsp": Table(
            description=(
                "Initial gross state product by PC National industry (114 industries) and state, from the model "
                "database (2018-19). pcn_no 0 / TOTAL = all industries."
            ),
            columns={
                "pcn_no": "PC National industry number (0 = total)",
                "pcn_code": "code: PC National industry",
                "name": "text",
            }
            | {s.lower(): "AUD million, 2018-19" for s in STATES}
            | {"total": "AUD million, 2018-19"},
            keys=("pcn_no",),
            rows=init,
        ),
        "linearity": Table(
            description=(
                "PC National linearity tests: the scenario's shock scaled to 25, 50, 75 and 100 per cent. "
                "matches_main_tab: the 100 per cent row reproduces the scenario tab's real GDP (the B9 test tab's "
                "block headings name the other scenario than its row labels; rows follow the row labels)."
            ),
            columns={
                "tab": "text: workbook tab",
                "scenario": "code: PC scenario code (from the row label)",
                "share_pct": "per cent of the original shock",
                "real_gdp": pct,
                "cpi": pct,
                "national_net_revenue": "AUD million, 2023-24 (Australian Government net operating balance)",
                "states_net_revenue": "AUD million, 2023-24 (states and territories net operating balance)",
                "matches_main_tab": "boolean",
            },
            keys=("tab", "scenario", "share_pct"),
            rows=lin,
        ),
    }
