"""Summary-statistics pages for the website: state and industry growth, and economic conditions.

Both pages are built from processed panels in ``data/processed`` (committed, so the Pages workflow
can rebuild them) and use the explorer's design. Growth rates, shares and indexes are computed in
the page from the levels embedded here, so every number shown can be traced to a panel.

- ``growth.html``: gross state product; gross value added, employment and business entry and exit
  by ANZSIC division and state (State Accounts, Labour Force EQ06, CABEE); barriers to entry and
  business dynamism (``alicia.menu.competition``). A slider picks any span of financial years.
- ``conditions.html``: the macroeconomic control series (``alicia.pipeline.controls``): state final
  demand, household consumption, unemployment, population, wages, dwelling approvals, commodity
  prices and national industry output; company profitability and market power by barriers to entry
  (``alicia.menu.competition``).
"""

from __future__ import annotations

import datetime as dt
import json
from importlib import resources

import pandas as pd

from .. import anzsic
from ..pipeline import controls, schema, store
from ..register.evaluation import Evaluation, current_evaluation
from ..register.schema import ChangeRecord
from . import competition

STATES = (*schema.STATES, "AUS")
STATE_NAMES = {v: k for k, v in schema.STATE_NAMES.items()} | {"AUS": "Australia"}
DIVISIONS = tuple("ABCDEFGHIJKLMNOPQRS")
TOTAL = "TOT"
# Preset periods for the slider. Financial years, named by the year in which they start (2014 = 2014-15).
WINDOWS = (
    {"id": "10y", "label": "Last 10 years", "start": 2014, "end": 2024},
    {"id": "5y", "label": "Last 5 years", "start": 2019, "end": 2024},
    {"id": "0414", "label": "2004-05 to 2014-15", "start": 2004, "end": 2014},
    {"id": "9404", "label": "1994-95 to 2004-05", "start": 1994, "end": 2004},
    {"id": "all", "label": "All years", "start": 1989, "end": 2024},
)
REPO_MAIN = "https://github.com/jabthebeer/Competition-in-Australia-analysis/blob/main/"
PAGES = (
    ("index.html", "Legislation menu"),
    ("growth.html", "State and industry growth"),
    ("conditions.html", "Economic conditions"),
)
# The Policy costing tab is built separately (Vite, `npm run build:site` in regulatory-burden-tool/) and added
# to the site only when that build is given, so the nav never links to a missing page.
COSTING_PAGE = ("costing.html", "Policy costing")
COSTING_ASSETS = "costing-assets"
GROWTH_NOTES = {
    "gva": (
        "Output is gross value added, adjusted for inflation (chain volume measures). Shares of a state's output "
        "use current prices, because inflation-adjusted figures don't add up across industries. 'All industries' "
        "also includes the rent value of owner-occupied homes, which is not an industry."
    ),
    "emp": (
        "Jobs are employed people by the industry of their main job, averaged over the four Labour Force surveys "
        "in each financial year. They are survey estimates, so small industries in small states (Tasmania, the "
        "Northern Territory and the ACT) can jump around from year to year."
    ),
    "biz": (
        "Business counts come from the ABS business register, from 2007-08 on. Rates are averages of the yearly "
        "rates over the period. The ABS slightly alters small counts to protect confidentiality, and counts shift "
        "between releases, so rates are more reliable than changes in counts."
    ),
}
CONDITIONS_NOTES = {
    "sfd": "Adjusted for inflation and seasonal patterns. Published for states and territories only, so there is no "
    "Australia line.",
    "unemp": (
        "Seasonally adjusted for the six states and Australia. The Northern Territory and ACT lines are 12-month "
        "averages, because the ABS doesn't publish seasonally adjusted figures for them in this series."
    ),
    "pop": "Estimated resident population at the end of each quarter.",
    "wpi": "Hourly pay rates excluding bonuses, all sectors, not seasonally adjusted.",
    "dwell": "Homes approved over the previous 12 months, per 1,000 residents.",
    "commodity": "Index, 2024-25 = 100, in Australian dollars.",
    "natgva": "Output adjusted for inflation and seasonal patterns. Growth over 5 and 10 years is the average yearly "
    "rate from the same quarter.",
}
# Links for the datasets each page uses (checked 26 Oct 2026). The ATO's own site blocks automated checks, so the
# ATO link is to the dataset on data.gov.au the data were downloaded from.
SOURCES = {
    "state_accounts": (
        "ABS, Australian National Accounts: State Accounts",
        "https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-state-accounts/latest-release",
    ),
    "lfs_detailed": (
        "ABS, Labour Force, Australia, Detailed",
        "https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia-detailed/latest-release",
    ),
    "cabee": (
        "ABS, Counts of Australian Businesses, including Entries and Exits",
        "https://www.abs.gov.au/statistics/economy/business-indicators/counts-australian-businesses-including-entries-and-exits/latest-release",
    ),
    "ato": (
        "ATO, Taxation Statistics, company tables (data.gov.au)",
        "https://data.gov.au/data/dataset/taxation-statistics-2022-23",
    ),
    "rba_rdp": (
        "RBA, Hambur and Freestone (2025), Research Discussion Paper 2025-05",
        "https://www.rba.gov.au/publications/rdp/2025/2025-05.html",
    ),
    "rba_yields": (
        "RBA, table F2.1: government bond yields",
        "https://www.rba.gov.au/statistics/tables/#interest-rates",
    ),
    "rba_commodity": (
        "RBA, table I2: index of commodity prices",
        "https://www.rba.gov.au/statistics/tables/#commodity-prices",
    ),
    "national_accounts": (
        "ABS, Australian National Accounts: National Income, Expenditure and Product",
        "https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-national-income-expenditure-and-product/latest-release",
    ),
    "population": (
        "ABS, National, state and territory population",
        "https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population/latest-release",
    ),
    "wpi": (
        "ABS, Wage Price Index, Australia",
        "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/wage-price-index-australia/latest-release",
    ),
    "labour_force": (
        "ABS, Labour Force, Australia",
        "https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia/latest-release",
    ),
    "building": (
        "ABS, Building Approvals, Australia",
        "https://www.abs.gov.au/statistics/industry/building-and-construction/building-approvals-australia/latest-release",
    ),
    "grattan": (
        "Grattan Institute, Competition in Australia: too little of a good thing? (2017)",
        "https://grattan.edu.au/report/competition-in-the-australian-economy/",
    ),
    "anzsic": (
        "ABS, Australian and New Zealand Standard Industrial Classification (ANZSIC) 2006",
        "https://www.abs.gov.au/statistics/classifications/australian-and-new-zealand-standard-industrial-classification-anzsic/2006-revision-2-0",
    ),
}


# Each source's licence, as recorded in data/SOURCES.md (the Excel exports list it). Grattan's report is cited, not
# used as data.
LICENCES = {k: "CC BY 4.0" for k in SOURCES} | {"ato": "CC BY 2.5 AU", "grattan": ""}


def _sources(*keys: str) -> dict:
    return {k: {"label": SOURCES[k][0], "url": SOURCES[k][1], "licence": LICENCES[k]} for k in keys}


def _fy_year(period: pd.Series) -> pd.Series:
    """First day of a financial year -> the year it starts."""
    return period.dt.year


def _series(df: pd.DataFrame, index: list, digits: int = 0) -> list:
    s = df.reindex(index)
    return [None if pd.isna(v) else (round(float(v), digits) if digits else int(round(v))) for v in s]


def _division_list() -> list[dict]:
    return [{"code": c, "name": anzsic.name(c) or c} for c in DIVISIONS] + [{"code": TOTAL, "name": "All industries"}]


def growth_payload(repo_base: str = REPO_MAIN) -> dict:
    sa = store.read_panel("abs_state_accounts", "industry_state_fy")
    sa = sa.assign(year=_fy_year(sa["period"]), div=sa["industry_code"].replace("", TOTAL))
    years = list(range(int(sa["year"].min()), int(sa["year"].max()) + 1))

    def gva(measure: str) -> dict:
        d = sa[sa["measure"] == measure]
        return {
            s: {
                c: _series(g.set_index("year")["value"], years)
                for c, g in d[d["geo_code"] == s].groupby("div")
                if c in (*DIVISIONS, TOTAL)
            }
            for s in STATES
        }

    def gsp(measure: str, digits: int = 0) -> dict:
        d = sa[sa["measure"] == measure]
        return {s: _series(d[d["geo_code"] == s].set_index("year")["value"], years, digits) for s in STATES}

    # Employment: four mid-quarter surveys per financial year (Aug, Nov, Feb, May).
    lfs = store.read_panel("abs_lfs", "industry_state_quarter")
    lfs = lfs[(lfs["measure"] == "employed") & lfs["industry_level"].isin(["division", "total"])]
    fy = lfs["period"].dt.year - (lfs["period"].dt.month < 7)
    lfs = lfs.assign(year=fy, div=lfs["industry_code"].replace("", TOTAL))
    counts = lfs.groupby(["geo_code", "div", "year"])["value"].agg(["mean", "size"])
    counts = counts[counts["size"] == 4]["mean"]
    emp_years = list(
        range(int(counts.index.get_level_values("year").min()), int(counts.index.get_level_values("year").max()) + 1)
    )
    emp = {
        s: {c: _series(counts.loc[(s, c)], emp_years, 3) for c in (*DIVISIONS, TOTAL) if (s, c) in counts.index}
        for s in STATES
    }

    # Businesses: CABEE classes summed to divisions, states summed to Australia.
    cab = store.read_panel("abs_cabee", "class_state_fy")
    cab = cab[cab["breakdown"] == ""]
    cab = cab.assign(year=_fy_year(cab["period"]), div=cab["industry_code"].map(lambda c: anzsic.division(c[:2])))
    by = cab.groupby(["measure", "geo_code", "div", "year"])["value"].sum()
    tot = cab.groupby(["measure", "geo_code", "year"])["value"].sum()
    tot.index = pd.MultiIndex.from_tuples([(m, g, TOTAL, y) for m, g, y in tot.index], names=by.index.names)
    by = pd.concat([by, tot])
    aus = by.groupby(level=["measure", "div", "year"]).sum()
    aus.index = pd.MultiIndex.from_tuples([(m, "AUS", c, y) for m, c, y in aus.index], names=by.index.names)
    by = pd.concat([by, aus]).sort_index()
    biz_years = sorted(int(y) for y in cab["year"].unique())
    measures = {"businesses_start": "start", "businesses_end": "end", "entries": "entries", "exits": "exits"}
    biz = {
        s: {
            c: {short: _series(by.loc[(m, s, c)], biz_years) for m, short in measures.items()}
            for c in (*DIVISIONS, TOTAL)
            if ("entries", s, c) in by.index
        }
        for s in STATES
    }

    return {
        "generated": dt.date.today().isoformat(),
        "repo": repo_base,
        "states": list(STATES),
        "stateNames": STATE_NAMES,
        "divisions": _division_list(),
        "windows": list(WINDOWS),
        "years": years,
        "gsp": {"volume": gsp("gsp_volume"), "current": gsp("gsp_current"), "perCapita": gsp("gsp_per_capita")},
        "gva": {"volume": gva("gva_volume"), "current": gva("gva_current")},
        "empYears": emp_years,
        "emp": emp,
        "bizYears": biz_years,
        "biz": biz,
        "vintages": {
            "gva": sa["vintage"].iloc[0],
            "emp": "ABS 6291.0.55.001 EQ06, March 2026 release (data to February 2026)",
            "biz": "ABS 8165.0, releases Jun 2007-Jun 2009 to Jul 2021-Jun 2025",
        },
        "notes": GROWTH_NOTES,
        "barriers": competition.barriers_payload(),
        "sources": _sources("state_accounts", "lfs_detailed", "cabee", "ato", "rba_rdp", "grattan", "anzsic"),
    }


def _dated_series(df: pd.DataFrame, start: str) -> tuple[list[str], dict]:
    df = df[df["period"] >= start]
    periods = sorted(df["period"].unique())
    idx = pd.DatetimeIndex(periods)
    out = {s: _series(g.set_index("period")["value"], idx, 3) for s, g in df.groupby("geo_code") if s in STATES}
    return [p.strftime("%Y-%m") for p in idx], out


def _evaluated_reforms(records: list[ChangeRecord], evaluations: list[Evaluation]) -> list[dict]:
    """Effective dates of evaluated changes, for optional markers on the charts."""
    by_id = {r.id: r for r in records}
    current = current_evaluation(evaluations)
    out = []
    for rid, ev_id in sorted(current.items()):
        r = by_id.get(rid)
        c = r.effective_commencement if r else None
        if c is None:
            continue
        out.append({"date": c.date.isoformat(), "jurisdiction": r.jurisdiction, "title": r.title, "evaluation": ev_id})
    return sorted(out, key=lambda d: d["date"])


def conditions_payload(
    records: list[ChangeRecord] | None = None,
    evaluations: list[Evaluation] | None = None,
    repo_base: str = REPO_MAIN,
) -> dict:
    sq = controls.load("state_quarter")
    sm = controls.load("state_month")
    iq = controls.load("industry_quarter")
    nm = controls.load("national_month")
    start = "1990-01-01"

    def pick(df, **eq):
        m = pd.Series(True, index=df.index)
        for k, v in eq.items():
            m &= df[k] == v
        return df[m]

    sfd_p, sfd = _dated_series(pick(sq, measure="state_final_demand_volume"), start)
    hhc_p, hhc = _dated_series(pick(sq, measure="household_consumption_volume", breakdown=""), start)
    pop_p, pop = _dated_series(pick(sq, measure="population"), start)
    wpi_p, wpi = _dated_series(
        pick(sq, measure="wage_price_index", breakdown="all sectors", adjustment="original"), start
    )

    # Unemployment: seasonally adjusted where published; 12-month average of the original otherwise.
    ur = pick(sm, measure="unemployment_rate")
    sa_states = set(ur.loc[ur["adjustment"] == "seasonally adjusted", "geo_code"])
    orig = ur[(ur["adjustment"] == "original") & ~ur["geo_code"].isin(sa_states)].sort_values("period")
    orig = orig.assign(value=orig.groupby("geo_code")["value"].transform(lambda v: v.rolling(12).mean()))
    ur = pd.concat([ur[ur["adjustment"] == "seasonally adjusted"], orig.dropna(subset=["value"])])
    ur_p, unemp = _dated_series(ur, start)

    # Dwelling approvals per 1,000 residents over 12 months (population interpolated to months).
    dw = pick(sm, measure="dwelling_approvals", breakdown="", adjustment="original")
    dw = dw[dw["geo_level"].isin(["STE", "AUS"])].sort_values("period")
    dw = dw.assign(value=dw.groupby("geo_code")["value"].transform(lambda v: v.rolling(12).sum()))
    popm = (
        pick(sq, measure="population")
        .assign(period=lambda d: d["period"] + pd.DateOffset(months=2))  # ERP is at the quarter's end
        .pivot_table(index="period", columns="geo_code", values="value")
        .resample("MS")
        .interpolate()
    )
    dw = dw.merge(popm.stack().rename("pop").reset_index(), on=["period", "geo_code"])
    dw = dw.assign(value=dw["value"] / dw["pop"] * 1000)
    dw_p, dwell = _dated_series(dw, start)

    com = pick(nm, measure="commodity_prices")
    com = com[com["breakdown"].str.endswith("- A$") & ~com["breakdown"].str.contains("spot|with bulk", regex=True)]
    com_p = sorted(com.loc[com["period"] >= start, "period"].unique())
    com_idx = pd.DatetimeIndex(com_p)
    commodity = {
        b.replace(" - A$", "").replace(" prices", ""): _series(g.set_index("period")["value"], com_idx, 2)
        for b, g in com.groupby("breakdown")
    }

    gva = pick(iq, source="abs_gva", breakdown="")
    gva = gva[gva["period"] >= start].assign(div=gva["industry_code"].replace("", TOTAL))
    nat_p = sorted(gva["period"].unique())
    nat_idx = pd.DatetimeIndex(nat_p)
    natgva = {c: _series(g.set_index("period")["value"], nat_idx) for c, g in gva.groupby("div")}

    return {
        "generated": dt.date.today().isoformat(),
        "repo": repo_base,
        "states": list(STATES),
        "stateNames": STATE_NAMES,
        "divisions": _division_list(),
        "quarterly": {
            "sfd": {"periods": sfd_p, "values": sfd},
            "hhc": {"periods": hhc_p, "values": hhc},
            "pop": {"periods": pop_p, "values": pop},
            "wpi": {"periods": wpi_p, "values": wpi},
        },
        "monthly": {
            "unemp": {"periods": ur_p, "values": unemp, "original": sorted(set(STATES) - sa_states)},
            "dwell": {"periods": dw_p, "values": dwell},
        },
        "commodity": {"periods": [p.strftime("%Y-%m") for p in com_idx], "values": commodity},
        "natgva": {"periods": [p.strftime("%Y-%m") for p in nat_idx], "values": natgva},
        "reforms": _evaluated_reforms(records or [], evaluations or []),
        "vintages": {
            src: "; ".join(sorted(df.loc[df["source"] == src, "vintage"].unique().tolist()))
            for df, srcs in (
                (sq, ("abs_sfd", "abs_erp", "abs_wpi")),
                (sm, ("abs_lf", "abs_ba")),
                (iq, ("abs_gva",)),
                (nm, ("rba_commodity",)),
            )
            for src in srcs
        },
        "notes": CONDITIONS_NOTES,
        "profit": competition.profit_payload(),
        "sources": _sources(
            "national_accounts",
            "population",
            "wpi",
            "labour_force",
            "building",
            "rba_commodity",
            "ato",
            "rba_yields",
            "rba_rdp",
            "grattan",
        ),
    }


def _asset(name: str) -> str:
    return resources.files("alicia.menu").joinpath(f"templates/{name}").read_text("utf-8")


def nav(current: str, pages: tuple = PAGES) -> str:
    links = []
    for href, label in pages:
        attr = ' aria-current="page"' if href == current else ""
        links.append(f'<a href="{href}"{attr}>{label}</a>')
    return '<nav class="site-nav" aria-label="ALICIA pages">' + "".join(links) + "</nav>"


def render(template: str, payload: dict, page: str, standalone: bool = False, pages: tuple = PAGES) -> str:
    """Fill a page template: shared styles, chart code and Excel export, navigation, then the embedded data."""
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = (
        _asset(template)
        .replace("/*__SITE_CSS__*/", _asset("site.css"))
        .replace("/*__CHARTS_JS__*/", _asset("charts.js") + "\n" + _asset("xlsx.js"))
        .replace("<!--__NAV__-->", nav(page, pages))
        .replace("__PAGE_DATA__", blob)
    )
    if standalone:
        html = (
            '<!doctype html>\n<html lang="en-AU">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            "</head>\n<body>\n" + html + "\n</body>\n</html>\n"
        )
    return html


def build_costing(out_dir, dist, pages: tuple) -> list:
    """Copy the Policy costing build (``dist``: costing.html and costing-assets/) into the site and fill in its nav.

    The page keeps its own Content-Security-Policy (no network requests, DECISIONS #37 of the burden tool);
    a build without it is refused, as is one without the navigation placeholder."""
    import shutil
    from pathlib import Path

    out, dist = Path(out_dir), Path(dist)
    html = (dist / COSTING_PAGE[0]).read_text("utf-8")
    if html.count("<!--__NAV__-->") != 1:
        raise ValueError(f"{dist / COSTING_PAGE[0]} needs exactly one <!--__NAV__--> placeholder")
    if "connect-src 'none'" not in html:
        raise ValueError(f"{dist / COSTING_PAGE[0]} has lost its Content-Security-Policy (connect-src 'none')")
    top = f'<div class="alicia-site-top">{nav(COSTING_PAGE[0], pages)}</div>'
    page = out / COSTING_PAGE[0]
    page.write_text(html.replace("<!--__NAV__-->", top), encoding="utf-8")
    assets = out / COSTING_ASSETS
    if assets.exists():
        shutil.rmtree(assets)
    shutil.copytree(dist / COSTING_ASSETS, assets)
    return [page, *sorted(p for p in assets.rglob("*") if p.is_file())]


def build_site(
    out_dir,
    records: list[ChangeRecord],
    evaluations: list[Evaluation],
    dates_report=None,
    standalone: bool = True,
    repo_base: str | None = None,
    costing_dist=None,
) -> list:
    """Write the legislation menu (index.html), the two summary pages and, given its build, the Policy costing
    tab into ``out_dir``."""
    from pathlib import Path

    from .explorer import build_explorer

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pages = PAGES + ((COSTING_PAGE,) if costing_dist else ())
    explorer_base = repo_base or None
    data_base = repo_base or REPO_MAIN
    written = [
        build_explorer(
            records,
            out / "index.html",
            dates_report=dates_report,
            standalone=standalone,
            evaluations=evaluations,
            repo_base=explorer_base,
            nav=nav("index.html", pages),
            evaluation_pages=True,
        )
    ]
    written += sorted(out.glob("evaluation-*.html"))
    summaries = (
        ("growth.html", growth_payload(data_base)),
        ("conditions.html", conditions_payload(records, evaluations, data_base)),
    )
    for name, payload in summaries:
        path = out / name
        path.write_text(render(name, payload, name, standalone, pages), encoding="utf-8")
        written.append(path)
    if costing_dist:
        written += build_costing(out, costing_dist, pages)
    return written
