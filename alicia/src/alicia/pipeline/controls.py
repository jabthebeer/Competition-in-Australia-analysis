"""Macroeconomic control series for the regression framework (docs/forward_plan_macro_controls.md, Phase 1).

These are conditions a reform evaluation should net out, not outcomes: state demand, labour-market
slack, population, wages, building activity, national industry cycles and commodity prices. They are
written in the common panel format to ``data/processed/controls/`` and are left out of the outcome
coverage catalogue (``store.panels``).

Tables
- ``state_quarter``: state final demand and its components (chain volume and current prices,
  seasonally adjusted; ABS 5206 via dataflow ANA_SFD); estimated resident population (ERP_Q,
  population at the end of the quarter); Wage Price Index, total hourly rates excluding bonuses
  (WPI; private sector and all sectors, original and seasonally adjusted).
- ``state_month``: Labour Force (LF; employed, labour force, unemployment, participation and
  employment-to-population rates; seasonally adjusted for the six states and Australia, original for
  all eight); building approvals (BA_GCCSA; dwelling units and value of building work, original, by
  state and by Greater Capital City / rest of state).
- ``industry_quarter``: national gross value added by ANZSIC division and selected sub-industries
  (chain volume, seasonally adjusted; ANA_IND_GVA); Business Indicators sales, wages and gross
  operating profits by division (QBIS; current prices, and chain volume sales).
- ``national_month``: RBA index of commodity prices (statistical table I2; all items, rural,
  non-rural, base metals and bulk commodities, in A$, SDR and US$); Australian Government bond yields
  (table F2.1, monthly from May 2013; 2, 3, 5 and 10 years and the 10-year indexed bond), used for the
  risk-free rate in the cost of equity on the Economic conditions page.

Periods are the first day of the month or quarter. Data: ABS Data API (CC BY 4.0) and Reserve Bank
of Australia (CC BY 4.0).
"""

from __future__ import annotations

import openpyxl
import pandas as pd

from . import abs_api, schema, store

DIR = "controls"
RBA_SOURCE = "rba"
RBA_LICENCE = "CC BY 4.0, Reserve Bank of Australia (rba.gov.au/copyright)"
RBA_I2 = "https://www.rba.gov.au/statistics/tables/xls/i02hist.xlsx"
RBA_F2 = "https://www.rba.gov.au/statistics/tables/xls/f02hist.xlsx"
ADJUSTMENT = {"10": "original", "20": "seasonally adjusted", "30": "trend"}

# ANA_SFD (DATA_ITEM, SECTOR) -> measure stem; household consumption by purpose goes in ``breakdown``.
SFD_ITEMS = {
    ("SFD", "SSS"): "state_final_demand",
    ("PFD", "PSS"): "private_final_demand",
    ("GFD", "GSS"): "public_final_demand",
    ("FCEH", "PHS"): "household_consumption",
    ("FCE", "GGS"): "government_consumption",
    ("GFC_BUS", "PSS"): "business_investment",
    ("GFC_DWL", "PSS"): "dwelling_investment",
    ("COE", "SSS"): "compensation_of_employees",
}
SFD_PRICES = {"VCH": ("volume", "AUD m, chain volume"), "C": ("current", "AUD m")}
LF_MEASURES = {
    "M3": ("employed_persons", "persons '000"),
    "M9": ("labour_force", "persons '000"),
    "M13": ("unemployment_rate", "%"),
    "M12": ("participation_rate", "%"),
    "M16": ("employment_to_population", "%"),
}
WPI_SECTORS = {"7": "all sectors", "1": "private sector"}
BA_MEASURES = {"1": ("dwelling_approvals", "dwelling units"), "2": ("building_approvals_value", "AUD '000")}
BA_TYPES = {"TOT": "", "100": "residential", "110": "houses"}
QBIS_MEASURES = {"M1": "sales", "M5": "wages", "M7": "gross_operating_profits"}
QBIS_PRICES = {"CUR": ("current", "AUD m"), "CVM": ("volume", "AUD m, chain volume")}


def _quarter(p: pd.Series) -> pd.Series:
    return pd.PeriodIndex(p.str.replace("-Q", "Q"), freq="Q").to_timestamp()


def _month(p: pd.Series) -> pd.Series:
    return pd.to_datetime(p, format="%Y-%m")


def _geo(region: pd.Series) -> tuple[pd.Series, pd.Series]:
    level = region.map(lambda r: "AUS" if r == "AUS" else ("STE" if r in schema.STATE_CODES else "GCCSA"))
    code = region.map(lambda r: schema.STATE_CODES.get(r, r))
    return level, code


def _frame(raw: pd.DataFrame, source: str, period: pd.Series, vintage: str, **cols) -> pd.DataFrame:
    level, code = _geo(raw["REGION"]) if "REGION" in raw else ("AUS", "AUS")
    out = pd.DataFrame(
        {"geo_level": level, "geo_code": code, "period": period, "value": raw["OBS_VALUE"], "vintage": vintage} | cols,
        index=raw.index,
    )
    out["source"] = source
    return out


def _vintage(flow: str, raw: pd.DataFrame) -> str:
    return f"ABS {flow} {abs_api.structure(flow)['version']} to {raw['TIME_PERIOD'].max()}"


def state_final_demand() -> pd.DataFrame:
    raw = abs_api.data("ANA_SFD", "VCH+C...20..Q")
    labels = next(d for d in abs_api.structure("ANA_SFD")["dimensions"] if d["id"] == "DATA_ITEM")["codes"]
    key = list(zip(raw["DATA_ITEM"], raw["SECTOR"], strict=True))
    purpose = raw["DATA_ITEM"].str.startswith("FCE_") & raw["SECTOR"].eq("PHS")
    keep = pd.Series([k in SFD_ITEMS for k in key], index=raw.index) | purpose
    raw = raw[keep]
    stem = raw.apply(lambda r: SFD_ITEMS.get((r["DATA_ITEM"], r["SECTOR"]), "household_consumption"), axis=1)
    price = raw["MEASURE"].map(SFD_PRICES)
    breakdown = (
        raw["DATA_ITEM"]
        .where(raw["DATA_ITEM"].str.startswith("FCE_"), "")
        .map(lambda c: labels.get(c, "").replace("Final consumption expenditure - ", "") if c else "")
    )
    return _frame(
        raw,
        "abs_sfd",
        _quarter(raw["TIME_PERIOD"]),
        _vintage("ANA_SFD", raw),
        measure=stem + "_" + price.str[0],
        unit=price.str[1],
        adjustment="seasonally adjusted",
        breakdown=breakdown,
        period_type="quarter",
    )


def population() -> pd.DataFrame:
    raw = abs_api.data("ERP_Q", "1.3.TOT..Q")
    return _frame(
        raw,
        "abs_erp",
        _quarter(raw["TIME_PERIOD"]),
        _vintage("ERP_Q", raw),
        measure="population",
        unit="persons",
        adjustment="original",
        period_type="quarter",
    )


def wages() -> pd.DataFrame:
    raw = abs_api.data("WPI", "1.THRPEB.7+1.TOT.10+20..Q")
    return _frame(
        raw,
        "abs_wpi",
        _quarter(raw["TIME_PERIOD"]),
        _vintage("WPI", raw),
        measure="wage_price_index",
        unit="index",
        adjustment=raw["TSEST"].map(ADJUSTMENT),
        breakdown=raw["SECTOR"].map(WPI_SECTORS),
        period_type="quarter",
    )


def labour_force() -> pd.DataFrame:
    sa = abs_api.data("LF", "M3+M9+M13+M12+M16+M18.3.1599.20..M")
    original = abs_api.data("LF", "M3+M9+M13+M12+M16.3.1599.10..M")
    raw = pd.concat([sa, original], ignore_index=True)
    meta = raw["MEASURE"].map(LF_MEASURES)
    return _frame(
        raw,
        "abs_lf",
        _month(raw["TIME_PERIOD"]),
        _vintage("LF", raw),
        measure=meta.str[0],
        unit=meta.str[1],
        adjustment=raw["TSEST"].map(ADJUSTMENT),
        period_type="month",
    )


def building_approvals() -> pd.DataFrame:
    raw = abs_api.data("BA_GCCSA", "1+2.1.9.TOT.100+110+TOT.20+10..M")
    raw = raw[~raw["REGION"].isin(["100", "150"])]  # weighted averages across capitals / rest of states
    meta = raw["MEASURE"].map(BA_MEASURES)
    return _frame(
        raw,
        "abs_ba",
        _month(raw["TIME_PERIOD"]),
        _vintage("BA_GCCSA", raw),
        measure=meta.str[0],
        unit=meta.str[1],
        adjustment=raw["TSEST"].map(ADJUSTMENT),
        breakdown=raw["BUILDING_TYPE"].map(BA_TYPES),
        period_type="month",
    )


def industry_gva() -> pd.DataFrame:
    raw = abs_api.data("ANA_IND_GVA", "VCH+C...20..AUS.Q")
    labels = next(d for d in abs_api.structure("ANA_IND_GVA")["dimensions"] if d["id"] == "DATA_ITEM")["codes"]
    ind = next(d for d in abs_api.structure("ANA_IND_GVA")["dimensions"] if d["id"] == "INDUSTRY")["codes"]
    division = raw["INDUSTRY"].str.fullmatch(r"[A-S]") & raw["SECTOR"].eq("SSS")
    total = raw["INDUSTRY"].eq("TOTAL") & raw["DATA_ITEM"].eq("GPP")
    raw = raw[division | total]
    breakdown = raw["DATA_ITEM"].map(
        lambda c: "" if c in ("GPM", "GPP") else labels.get(c, c).replace("Gross value added - ", "")
    )
    return _frame(
        raw,
        "abs_gva",
        _quarter(raw["TIME_PERIOD"]),
        _vintage("ANA_IND_GVA", raw),
        measure="gva_volume",
        unit="AUD m, chain volume",
        adjustment="seasonally adjusted",
        industry_level=raw["INDUSTRY"].map(lambda c: "total" if c == "TOTAL" else "division"),
        industry_code=raw["INDUSTRY"].map(lambda c: "" if c == "TOTAL" else c),
        industry_label=raw["INDUSTRY"].map(ind),
        breakdown=breakdown,
        period_type="quarter",
    )


def business_indicators() -> pd.DataFrame:
    raw = abs_api.data("QBIS", "M1+M5+M7.CUR+CVM..TOT.20+10.AUS.Q")
    raw = raw[raw["INDUSTRY"].str.fullmatch(r"[A-S]|TOT")]
    ind = next(d for d in abs_api.structure("QBIS")["dimensions"] if d["id"] == "INDUSTRY")["codes"]
    price = raw["PRICE_ADJUSTMENT"].map(QBIS_PRICES)
    return _frame(
        raw,
        "abs_qbis",
        _quarter(raw["TIME_PERIOD"]),
        _vintage("QBIS", raw),
        measure=raw["MEASURE"].map(QBIS_MEASURES) + "_" + price.str[0],
        unit=price.str[1],
        adjustment=raw["TSEST"].map(ADJUSTMENT),
        industry_level=raw["INDUSTRY"].map(lambda c: "total" if c == "TOT" else "division"),
        industry_code=raw["INDUSTRY"].map(lambda c: "" if c == "TOT" else c),
        industry_label=raw["INDUSTRY"].map(ind),
        period_type="quarter",
    )


def read_rba_i2(path) -> pd.DataFrame:
    """An RBA statistical table (I2, F2.1) as a long frame: date, series_id, title, units, value."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb["Data"].iter_rows(values_only=True))
    wb.close()
    head = {r[0]: r[1:] for r in rows[:11] if r and r[0]}
    if "Series ID" not in head or "Title" not in head:
        raise ValueError(f"{path}: unexpected RBA I2 layout")
    body = [r for r in rows[11:] if r and r[0] is not None]
    ids = list(head["Series ID"])
    wide = pd.DataFrame([r[1 : len(ids) + 1] for r in body], columns=ids)
    wide.insert(0, "date", [r[0] for r in body])
    long = wide.melt(id_vars="date", var_name="series_id", value_name="value").dropna(subset=["value", "series_id"])
    meta = pd.DataFrame({"series_id": ids, "title": head["Title"], "units": head["Units"]}).dropna(subset=["series_id"])
    out = long.merge(meta)
    out["date"] = pd.to_datetime(out["date"])
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["value"])


def commodity_prices() -> pd.DataFrame:
    path = store.download(RBA_SOURCE, RBA_I2, "i02hist.xlsx", RBA_LICENCE)
    d = read_rba_i2(path)
    title = d["title"].str.replace("–", "-")
    return pd.DataFrame(
        {
            "source": "rba_commodity",
            "measure": "commodity_prices",
            "unit": d["units"],
            "adjustment": "original",
            "breakdown": title.str.replace(" commodity prices", "").str.replace("Commodity prices", "All items"),
            "geo_level": "AUS",
            "geo_code": "AUS",
            "period_type": "month",
            "period": d["date"].dt.to_period("M").dt.to_timestamp(),
            "value": d["value"],
            "vintage": f"RBA I2 to {d['date'].max():%Y-%m}",
        }
    )


def bond_yields() -> pd.DataFrame:
    path = store.download(RBA_SOURCE, RBA_F2, "f02hist.xlsx", RBA_LICENCE)
    d = read_rba_i2(path)
    return pd.DataFrame(
        {
            "source": "rba_yields",
            "measure": "bond_yield",
            "unit": "% a year",
            "adjustment": "original",
            "breakdown": d["title"].str.replace("Australian Government ", "", regex=False),
            "geo_level": "AUS",
            "geo_code": "AUS",
            "period_type": "month",
            "period": d["date"].dt.to_period("M").dt.to_timestamp(),
            "value": d["value"],
            "vintage": f"RBA F2.1 to {d['date'].max():%Y-%m}",
        }
    )


TABLES = {
    "state_quarter": (state_final_demand, population, wages),
    "state_month": (labour_force, building_approvals),
    "industry_quarter": (industry_gva, business_indicators),
    "national_month": (commodity_prices, bond_yields),
}


def _finish(frames: list[pd.DataFrame]) -> pd.DataFrame:
    df = pd.concat(frames, ignore_index=True)
    for col, default in (("industry_level", "total"), ("industry_code", ""), ("industry_label", "All industries")):
        if col not in df:
            df[col] = default
        df[col] = df[col].fillna(default)
    scheme = df["industry_level"].map(lambda lv: "ANZSIC06" if lv == "division" else "none")
    df["breakdown"] = df.get("breakdown", "").fillna("")
    return schema.make(df.assign(industry_scheme=scheme))


def build(tables=None) -> dict[str, pd.DataFrame]:
    """Build the control tables (all of them, or those named in ``tables``)."""
    out = {}
    for table, builders in TABLES.items():
        if tables is not None and table not in tables:
            continue
        panel = _finish([b() for b in builders])
        store.write_panel(panel, DIR, table)
        out[table] = panel
    return out


def load(table: str) -> pd.DataFrame:
    return store.read_panel(DIR, table)
