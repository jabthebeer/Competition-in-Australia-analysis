"""Summary-statistics page for the website: Structural competitive conditions (``growth.html``), with the economic
conditions at its end; also the site's nav, landing page and build.

The page is built from processed panels in ``data/processed`` (committed, so the Pages workflow can rebuild it) and
uses the explorer's design. Growth rates, shares and indexes are computed in the page from the levels embedded here,
so every number shown can be traced to a panel.

- Structural competitive conditions: gross state product; gross value added, employment and business entry and exit
  by ANZSIC division and state (State Accounts, Labour Force EQ06, CABEE); barriers to entry and business dynamism
  (``alicia.menu.competition``). A slider picks any span of financial years.
- Economic conditions, at the end of the same page (its own page, ``conditions.html``, until 11 Nov 2026; that
  address now forwards there): the macroeconomic control series (``alicia.pipeline.controls``): state final demand,
  household consumption, unemployment, population, wages, dwelling approvals, commodity prices and national industry
  output; company profitability and market power by barriers to entry (``alicia.menu.competition``). Optional markers
  show when the register's major reforms started (an overall framework mark of +3 or more, or -3 or less).
"""

from __future__ import annotations

import datetime as dt
import json
from importlib import resources

import pandas as pd

from .. import anzsic
from ..international import concordance, site
from ..pipeline import controls, schema, store
from ..register.evaluation import Evaluation
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
HOME_PAGE = ("index.html", "Home")
COMPETITION_PAGE = ("growth.html", "Structural competitive conditions")
MENU_PAGE = ("menu.html", "Legislative levers influencing competition")
LENS_PAGE = ("industry-lens.html", "Industry lens")
OVERVIEW_PAGE = ("regulatory-overview.html", "Regulatory overview by industry")
FRAMEWORK_PAGE = ("framework.html", "Framework")
METHODOLOGY_PAGE = ("methodology.html", "Methodology")
# Every page the site builds, in nav order (owner decision, 11 Nov 2026, DECISIONS E-135). Pages keep their addresses
# when renamed, so links made before still work.
PAGES = (HOME_PAGE, COMPETITION_PAGE, MENU_PAGE, LENS_PAGE, FRAMEWORK_PAGE, METHODOLOGY_PAGE)
# The nav groups the pages by what they are for: the two views, then how the site is made. A page the build does
# not write (the regulatory overview, until it is built) shows as coming soon, without a link.
NAV_GROUPS = (
    ("Top down", (COMPETITION_PAGE, MENU_PAGE)),
    ("Bottom up", (LENS_PAGE, OVERVIEW_PAGE)),
    ("About", (FRAMEWORK_PAGE, METHODOLOGY_PAGE)),
)
# Short labels for the nav, so it fits on one line; each page's heading keeps its full name (owner decision,
# 14 Nov 2026, DECISIONS E-159).
NAV_LABELS = {
    COMPETITION_PAGE[0]: "Competitive conditions",
    MENU_PAGE[0]: "Legislative levers",
    OVERVIEW_PAGE[0]: "Regulatory overview",
}
# The nav's groups sit in a <details> that is open in the markup, so they show without scripts. This keeps it open
# on wide screens, where its Menu button is hidden, and closed on a phone until the reader opens it.
NAV_SCRIPT = (
    '(()=>{const d=document.currentScript.previousElementSibling,m=matchMedia("(max-width: 640px)"),'
    's=()=>{d.open=!m.matches;};s();m.addEventListener("change",s);})();'
)
# Short forms of the states and territories, for places where space is tight (Style Manual).
STATE_SHORT = {"NSW": "NSW", "VIC": "Vic", "QLD": "Qld", "SA": "SA", "WA": "WA", "TAS": "Tas", "NT": "NT", "ACT": "ACT"}
# Every page on the site is a work in progress. One "Beta" badge sits beside the site's name in the nav, and each
# page's heading ends with "(beta)", whose marker explains it on hover, focus or tap. (The archived econometric
# pages carry no marker.)
BETA_TIP = "Work in progress: this page is still being built and checked, so its content may change."
# Economic conditions was its own page until 11 Nov 2026; it is now the end of Structural competitive conditions,
# and its old address forwards there.
CONDITIONS_PAGE = "conditions.html"
CONDITIONS_ANCHOR = "economic-conditions"
# The Policy costing tab (regulatory-burden-tool/) is archived and not part of the live site (owner decision,
# 11 Nov 2026, DECISIONS E-135). The code stays: given its build (`npm run build:site`), `alicia site --costing`
# still adds it, after the grouped nav.
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
    "prod": (
        "Output per worker is output, adjusted for inflation (State Accounts), divided by the number of people "
        "employed (Labour Force, four surveys averaged over the financial year). It counts people, not hours, so "
        "industries with many part-time workers read lower, and the level is at current prices. Employment in small "
        "industries in small states is a survey estimate that jumps around, so their productivity is noisy. All "
        "industries includes the rent of owner-occupied homes, which has no workers, so its output per worker reads "
        "high."
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
    "abs_mfp": (
        "ABS, Estimates of Industry Multifactor Productivity",
        "https://www.abs.gov.au/statistics/industry/industry-overview/estimates-industry-multifactor-productivity/latest-release",
    ),
    "anzsic": (
        "ABS, Australian and New Zealand Standard Industrial Classification (ANZSIC) 2006",
        "https://www.abs.gov.au/statistics/classifications/australian-and-new-zealand-standard-industrial-classification-anzsic/2006-revision-2-0",
    ),
    "oecd_sdbs": (
        "OECD, Structural and Demographic Business Statistics: employer business demography",
        "https://sdmx.oecd.org/public/rest/dataflow/OECD.SDD.TPS/DSD_SDBSBD_ISIC4@DF_BD_EMP_B_D/latest",
    ),
    "oecd_stan": (
        "OECD, STAN Database for Structural Analysis (2025 edition)",
        "https://sdmx.oecd.org/public/rest/dataflow/OECD.STI.PIE/DSD_STAN@DF_STAN_2025/latest",
    ),
    "oecd_pmr": (
        "OECD, Product Market Regulation indicators",
        "https://sdmx.oecd.org/public/rest/dataflow/OECD.ECO.GCRD/DSD_PMR@DF_PMR/latest",
    ),
    "oecd_stri": (
        "OECD, Services Trade Restrictiveness Index",
        "https://sdmx.oecd.org/public/rest/dataflow/OECD.TAD.TPD/DSD_STRI@DF_STRI_MAIN/latest",
    ),
    "oecd_fdi": (
        "OECD, FDI Regulatory Restrictiveness Index",
        "https://sdmx.oecd.org/public/rest/dataflow/OECD.DAF.INV/DSD_FDIRRI_SCORES@DF_FDIRRI_SCORES/latest",
    ),
    "abs_isic": (
        "ABS, correspondence between ANZSIC 2006 and ISIC Rev. 4",
        "https://www.abs.gov.au/statistics/classifications/australian-and-new-zealand-standard-industrial-classification-anzsic/2006-revision-2-0/correspondences/anzsic-2006-isic-rev-4",
    ),
}


# Each source's licence, as recorded in data/SOURCES.md (the Excel exports list it). Grattan's report is cited, not
# used as data.
OECD_LICENCE = "CC BY 4.0 is the OECD default for data from 1 July 2024 (not verified: oecd.org refused requests)"
LICENCES = (
    {k: "CC BY 4.0" for k in SOURCES}
    | {"ato": "CC BY 2.5 AU", "grattan": ""}
    | {k: OECD_LICENCE for k in ("oecd_sdbs", "oecd_stan", "oecd_pmr", "oecd_stri", "oecd_fdi")}
)


def abs_productivity() -> dict:
    """The ABS's official productivity indexes by industry, Australia (5260.0.55.002, read from the costing
    parameters): labour productivity (value added per hour worked) and multifactor productivity, on the hours-worked
    basis, for the 16 market-sector divisions and the market sector as a whole (MKT16). Financial years by their
    first calendar year; empty if the parameters are not built."""
    if not competition.COSTING.exists():
        return {"years": [], "lp": {}, "mfp": {}, "release": ""}
    params = json.loads(competition.COSTING.read_text("utf-8"))
    rows = params["tables"].get("abs_mfp.industry", {}).get("rows", [])
    years = sorted({int(r["fy"][:4]) for r in rows})
    out: dict = {"lp": {}, "mfp": {}}
    for r in rows:
        i = years.index(int(r["fy"][:4]))
        for key, col in (("lp", "lp_hours"), ("mfp", "mfp_hours")):
            out[key].setdefault(r["anzsic"], [None] * len(years))[i] = r.get(col)
    meta = next((m for m in params.get("sources", []) if m.get("id") == "abs_mfp"), {})
    title = meta.get("title", "ABS 5260.0.55.002")
    release = f"{title}, {meta.get('release', '')} release ({meta.get('release_date', '')})"
    return {"years": years, **out, "release": release}


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


def _cvm_reference_year(sa: pd.DataFrame) -> int | None:
    """The reference year of the chain volume series (the financial year, by its first year, in which they equal
    current prices for every division of Australia), so levels can say whose prices they are in."""
    a = sa[(sa["geo_code"] == "AUS") & sa["measure"].isin(("gva_volume", "gva_current")) & (sa["div"] != TOTAL)]
    w = a.pivot_table(index=["div", "year"], columns="measure", values="value")
    same = w[(w["gva_volume"] - w["gva_current"]).abs() < 0.5].reset_index().groupby("year")["div"].nunique()
    full = same[same == w.index.get_level_values("div").nunique()]
    return int(full.index[-1]) if len(full) else None


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
        # Five decimals keep the four-quarter mean of figures published to three decimals exact: rounding it to three
        # put two heatmap cells on the wrong side of their display rounding.
        s: {c: _series(counts.loc[(s, c)], emp_years, 5) for c in (*DIVISIONS, TOTAL) if (s, c) in counts.index}
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
        "cvmRef": _cvm_reference_year(sa),
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
        "productivity": abs_productivity(),
        # Industries classified differently in other countries' statistics (ISIC): a † and hover note on the page
        # and the comparisons with similar economies (phase P4, E-107)
        "intl": {"title": concordance.NOTE_TITLE, "notes": concordance.division_notes(), **site.payload()},
        "sources": _sources(
            "state_accounts",
            "lfs_detailed",
            "cabee",
            "abs_mfp",
            "ato",
            "rba_rdp",
            "grattan",
            "anzsic",
            "abs_isic",
            "oecd_sdbs",
            "oecd_stan",
            "oecd_pmr",
            "oecd_stri",
            "oecd_fdi",
        ),
    }


def _dated_series(df: pd.DataFrame, start: str) -> tuple[list[str], dict]:
    df = df[df["period"] >= start]
    periods = sorted(df["period"].unique())
    idx = pd.DatetimeIndex(periods)
    out = {s: _series(g.set_index("period")["value"], idx, 3) for s, g in df.groupby("geo_code") if s in STATES}
    return [p.strftime("%Y-%m") for p in idx], out


MAJOR_MARK = 3


def _major_reforms(records: list[ChangeRecord]) -> list[dict]:
    """Effective dates of reforms with a strong framework mark (overall +3 or more, or -3 or less), for optional
    markers on the charts."""
    out = []
    for r in records:
        c, a = r.effective_commencement, r.assessment
        if r.kind != "reform" or c is None or a is None or abs(a.total) < MAJOR_MARK:
            continue
        out.append({"date": c.date.isoformat(), "jurisdiction": r.jurisdiction, "title": r.title, "mark": a.total})
    return sorted(out, key=lambda d: (d["date"], d["jurisdiction"]))


def conditions_payload(records: list[ChangeRecord] | None = None, repo_base: str = REPO_MAIN) -> dict:
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
        "reforms": _major_reforms(records or []),
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


def beta(tip_id: str = "beta-tip") -> str:
    """The "(beta)" after a page's heading, with a tip on hover, keyboard focus or tap: the page is a work in
    progress."""
    from html import escape

    return (
        f'<span class="beta"><button type="button" class="beta-btn" aria-describedby="{tip_id}">(beta)</button>'
        f'<span role="tooltip" class="beta-tip" id="{tip_id}">{escape(BETA_TIP)}</span></span>'
    )


def nav(current: str, pages: tuple = PAGES) -> str:
    """The site nav, on one line: the site's name (the link home) with its Beta badge, then the pages grouped as in
    ``NAV_GROUPS`` under short labels. On a phone the groups fold behind a Menu button (``NAV_SCRIPT``). ``pages``
    holds the pages this build writes; a grouped page that is not among them shows as coming soon, without a link,
    and a built page outside the groups (the archived Policy costing tab, when built) follows the groups as a plain
    link."""
    from html import escape

    built = {href for href, _ in pages}
    grouped = {href for _, group in NAV_GROUPS for href, _ in group}

    def link(href: str, label: str) -> str:
        attr = ' aria-current="page"' if href == current else ""
        short = NAV_LABELS.get(href, label)
        if short != label:
            attr += f' title="{escape(label)}"'
        return f'<a href="{href}"{attr}>{escape(short)}</a>'

    home = ' aria-current="page"' if current == HOME_PAGE[0] else ""
    brand = (
        f'<a class="brand" href="{HOME_PAGE[0]}"{home} aria-label="ALICIA (beta): home">'
        f'<span class="brand-name">ALICIA</span><span class="brand-beta" title="{escape(BETA_TIP)}">Beta</span></a>'
    )
    groups = []
    for title, group in NAV_GROUPS:
        gid = "nav-" + title.lower().replace(" ", "-")
        items = []
        for href, label in group:
            if href in built:
                items.append(f"<li>{link(href, label)}</li>")
            else:
                short = escape(NAV_LABELS.get(href, label))
                soon = '<span class="nav-note">(coming soon)</span>'
                items.append(f'<li><span class="nav-soon">{short} {soon}</span></li>')
        groups.append(
            f'<div class="nav-group"><p class="nav-label" id="{gid}">{escape(title)}</p>'
            f'<ul aria-labelledby="{gid}">{"".join(items)}</ul></div>'
        )
    groups += [link(href, label) for href, label in pages if href not in grouped and href != HOME_PAGE[0]]
    return (
        f'<nav class="site-nav" aria-label="ALICIA pages">{brand}'
        f'<details class="nav-menu" open><summary>Menu</summary><div class="nav-groups">{"".join(groups)}</div>'
        f"</details><script>{NAV_SCRIPT}</script></nav>"
    )


def long_date(d: dt.date) -> str:
    """A date as running text has it (Style Manual): 14 November 2026."""
    return f"{d.day} {d:%B %Y}"


def site_foot(generated: dt.date | None = None) -> str:
    """A page's closing lines: the register's draft status, that the site is unofficial, and when it was built."""
    return (
        '<footer class="site-foot">'
        "<p><strong>Draft.</strong> Register items and marks come from AI-assisted desk research and stay drafts "
        "until a person has checked them. Statistics come from official sources: the ABS, the ATO, the RBA and the "
        "OECD.</p>"
        "<p>Unofficial research, not an Australian Government product. "
        f"Updated {long_date(generated or dt.date.today())}.</p></footer>"
    )


def render(template: str, payload: dict, page: str, standalone: bool = False, pages: tuple = PAGES) -> str:
    """Fill a page template: shared styles, chart code and Excel export, navigation, then the embedded data."""
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = (
        _asset(template)
        .replace("/*__SITE_CSS__*/", _asset("site.css"))
        .replace("/*__CHARTS_JS__*/", _asset("charts.js") + "\n" + _asset("xlsx.js"))
        .replace("<!--__NAV__-->", nav(page, pages))
        .replace("<!--__BETA__-->", beta())
        .replace("__PAGE_DATA__", blob)
    )
    if standalone:
        html = (
            '<!doctype html>\n<html lang="en-AU">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            "</head>\n<body>\n" + html + "\n</body>\n</html>\n"
        )
    return html


def conditions_forward() -> str:
    """``conditions.html``: Economic conditions moved to the end of Structural competitive conditions (11 Nov 2026), so
    its old address forwards there and links made before the move still work. Nothing on the site links to it."""
    target = f"{COMPETITION_PAGE[0]}#{CONDITIONS_ANCHOR}"
    return (
        '<!doctype html>\n<html lang="en-AU">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>ALICIA: Economic conditions has moved</title>\n"
        f'<meta http-equiv="refresh" content="0; url={target}">\n'
        f'<link rel="canonical" href="{target}">\n'
        f'<script>location.replace("{target}");</script>\n'
        "</head>\n<body>\n"
        f'<p>Economic conditions is now part of <a href="{target}">{COMPETITION_PAGE[1]}</a>.</p>\n'
        "</body>\n</html>\n"
    )


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
    archive: bool = False,
) -> list:
    """Write the landing page (index.html), Legislative levers influencing competition (menu.html), the Framework and
    Methodology pages, Structural competitive conditions (growth.html, with the economic conditions at its end, and
    conditions.html forwarding there) and the Industry lens into ``out_dir``.

    Two archived parts are not on the live site and nothing there links to them (owner decisions, 11 Nov 2026,
    DECISIONS E-135 and E-136); their code stays. ``archive=True`` adds the econometric archive (archive.html and one
    page per evaluation); ``costing_dist`` adds the Policy costing tab from its build."""
    from pathlib import Path

    from . import framework as framework_page
    from . import home, lens, methodology
    from .archive import ARCHIVE_PAGE, build_archive
    from .explorer import build_explorer, menu_payload

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pages = PAGES + ((COSTING_PAGE,) if costing_dist else ())
    explorer_base = repo_base or None
    data_base = repo_base or REPO_MAIN
    menu = menu_payload(records, dates_report, evaluations)
    written = [build_explorer(records, out / MENU_PAGE[0], standalone=standalone, pages=pages, payload=menu)]
    fw_path = out / "framework.html"
    fw_html = framework_page.render(records, nav(FRAMEWORK_PAGE[0], pages), standalone, beta=beta())
    fw_path.write_text(fw_html, encoding="utf-8")
    written.append(fw_path)
    if archive:
        written.append(
            build_archive(
                records,
                out / ARCHIVE_PAGE,
                dates_report=dates_report,
                standalone=standalone,
                evaluations=evaluations,
                repo_base=explorer_base,
                nav=nav(ARCHIVE_PAGE, pages),
                evaluation_pages=True,
            )
        )
        written += sorted(out.glob("evaluation-*.html"))
    # Structural competitive conditions, with the economic conditions (once their own page) at its end.
    payload = growth_payload(data_base) | {"conditions": conditions_payload(records, data_base)}
    path = out / COMPETITION_PAGE[0]
    path.write_text(render(COMPETITION_PAGE[0], payload, COMPETITION_PAGE[0], standalone, pages), encoding="utf-8")
    written.append(path)
    path = out / CONDITIONS_PAGE
    path.write_text(conditions_forward(), encoding="utf-8")
    written.append(path)
    path = out / METHODOLOGY_PAGE[0]
    path.write_text(methodology.page(records, standalone, pages, repo=data_base), encoding="utf-8")
    written.append(path)
    lens_path = out / LENS_PAGE[0]
    lens_path.write_text(
        render(LENS_PAGE[0], lens.payload(records, repo_base=data_base), LENS_PAGE[0], standalone, pages),
        encoding="utf-8",
    )
    written.append(lens_path)
    if costing_dist:
        written += build_costing(out, costing_dist, pages)
    # Home: its figures come from the competition and levers pages' own data.
    built = {href for href, _ in pages} | {p.name for p in written}
    home_path = out / HOME_PAGE[0]
    home_path.write_text(home.page(payload, menu, built, standalone, pages), encoding="utf-8")
    written.append(home_path)
    return written
