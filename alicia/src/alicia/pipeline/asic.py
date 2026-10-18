"""ASIC business-names and company registers as count panels by month, state and postcode.

Both datasets (data.gov.au ``asic-business-names`` and ``asic-companies``, CC BY 3.0 AU, weekly) are
current snapshots with no location and no industry:
- location comes from joining the ABN to the ABN Bulk Extract (state and postcode of the main
  business location, as at that extract);
- industry is inferred from the name (``alicia.pipeline.names``).

What the snapshots support:
- registrations by month since the national business-names register opened (28 May 2012), and
  company registrations since 1991, for names and companies still on the register or removed in
  the last year (removed earlier = not in the file, so older months are survivors only);
- cancellations and deregistrations for the last 12 months only (October 2025 on, in the October
  2026 extracts; a handful of older dates also appear);
- monthly counts run to the last full month before the extract date;
- the stock of registered names and companies on the snapshot date.
"""

from __future__ import annotations

import zipfile

import pandas as pd

from . import names, schema, store

LICENCE = "CC BY 3.0 AU, Australian Securities and Investments Commission"
BN_SOURCE, CO_SOURCE = "asic_business_names", "asic_companies"
BN_ZIP, CO_ZIP = "business_names_202610.zip", "company_202610.zip"
BN_URL = (
    "https://data.gov.au/data/dataset/bc515135-4bb6-4d50-957a-3713709a76d3/resource/"
    "45eddcf9-07c1-4c5c-a1aa-ff109a033977/download/business_names_202610.zip"
)
CO_URL = (
    "https://data.gov.au/data/dataset/7b8656f9-606d-4337-af29-66b89b2eeefb/resource/"
    "d6d03876-71a4-4e82-8c77-2e4df5da4236/download/company_202610.zip"
)
BN_START = pd.Timestamp("2012-06-01")  # first full month of the national register
CO_START = pd.Timestamp("1991-01-01")  # national companies scheme


def _read(source: str, zname: str, url: str, usecols: list[str]) -> tuple[pd.DataFrame, pd.Timestamp]:
    """The extract and its snapshot date (the date stamped on the file inside the zip)."""
    path = store.download(source, url, zname, LICENCE)
    with zipfile.ZipFile(path) as z:
        member = z.infolist()[0]
        with z.open(member) as fh:
            df = pd.read_csv(fh, sep="\t", dtype=str, usecols=usecols, encoding="utf-8-sig", quoting=3)
    return df, pd.Timestamp(*member.date_time[:3])


def _complete_months(dates: pd.Series, start: pd.Timestamp, snapshot: pd.Timestamp) -> pd.Series:
    """Dates from ``start`` up to the end of the last full month before the snapshot."""
    return dates.notna() & (dates >= start) & (dates < snapshot.to_period("M").to_timestamp())


def _date(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")


def _abn_locations() -> pd.DataFrame:
    rec = store.PROCESSED / "abr_abn" / "records"
    if not any(rec.glob("*.parquet")):
        raise FileNotFoundError("build the ABN panels first ('alicia pipeline build abr_abn')")
    d = pd.read_parquet(rec, columns=["abn", "state", "postcode"])
    d["postcode"] = d["postcode"].where(d["postcode"].str.fullmatch(r"\d{4}"), "")
    d["state"] = d["state"].where(d["state"].isin(schema.STATES), "")
    return d


def _locate(df: pd.DataFrame, abn_col: str, locs: pd.DataFrame) -> pd.DataFrame:
    abn = pd.to_numeric(df[abn_col].str.replace(" ", ""), errors="coerce")
    out = df.assign(abn=abn.where(abn > 0).astype("Int64"))
    out = out.merge(locs, on="abn", how="left")
    out[["state", "postcode"]] = out[["state", "postcode"]].fillna("")
    return out


def _panel(
    d: pd.DataFrame, measure: str, period: pd.Series, breakdown: pd.Series | None, period_type: str = "month"
) -> list[pd.DataFrame]:
    """Counts at AUS, state and postcode (all industries) and by inferred industry (AUS, state)."""
    d = d.assign(period=period, breakdown=breakdown if breakdown is not None else "")
    parts = []
    specs = (
        ("AUS", None, False),
        ("STE", "state", False),
        ("POA", "postcode", False),
        ("AUS", None, True),
        ("STE", "state", True),
    )
    for level, col, by_ind in specs:
        g = d
        keys = ["period", "breakdown"]
        if col:
            g = g[g[col] != ""]
            keys.append(col)
        if by_ind:
            g = g[g["industry"] != ""]
            keys.append("industry")
        c = g.groupby(keys, observed=True).size().rename("value").reset_index()
        parts.append(
            pd.DataFrame(
                {
                    "measure": measure,
                    "period_type": period_type,
                    "geo_level": level,
                    "geo_code": c[col] if col else "AUS",
                    "breakdown": c["breakdown"],
                    "period": c["period"],
                    "value": c["value"],
                    "industry_scheme": "ANZSIC06-inferred" if by_ind else "none",
                    "industry_code": c["industry"] if by_ind else "",
                    "industry_level": c["industry"].map(names.level) if by_ind else "total",
                }
            )
        )
    return parts


def build_business_names() -> pd.DataFrame:
    cols = ["BN_NAME", "BN_STATUS", "BN_REG_DT", "BN_CANCEL_DT", "BN_ABN"]
    bn, snapshot = _read(BN_SOURCE, BN_ZIP, BN_URL, cols)
    bn["industry"] = bn["BN_NAME"].fillna("").str.strip().map(names.classify)
    bn = _locate(bn, "BN_ABN", _abn_locations())
    reg, cancel = _date(bn["BN_REG_DT"]), _date(bn["BN_CANCEL_DT"])
    month = lambda s: s.dt.to_period("M").dt.to_timestamp()  # noqa: E731
    parts = []
    keep = _complete_months(reg, BN_START, snapshot)
    parts += _panel(bn[keep], "business_name_registrations", month(reg[keep]), None)
    keep = _complete_months(cancel, BN_START, snapshot)
    parts += _panel(bn[keep], "business_name_cancellations", month(cancel[keep]), None)
    live = bn["BN_STATUS"].eq("Registered")
    parts += _panel(bn[live], "business_names_registered", pd.Series(snapshot, index=bn[live].index), None, "day")
    panel = schema.make(
        pd.concat(parts, ignore_index=True),
        source=BN_SOURCE,
        unit="count",
        adjustment="original",
        vintage=f"ASIC business names extract {snapshot:%Y-%m-%d}",
    )
    store.write_panel(panel, BN_SOURCE, "names_month")
    return panel


def build_companies() -> pd.DataFrame:
    cols = [
        "Company Name",
        "Type",
        "Status",
        "Date of Registration",
        "Date of Deregistration",
        "Current Name Indicator",
        "ABN",
    ]
    co, snapshot = _read(CO_SOURCE, CO_ZIP, CO_URL, cols)
    co = co[co["Current Name Indicator"].eq("Y")]
    co["industry"] = co["Company Name"].fillna("").map(names.classify)
    co = _locate(co, "ABN", _abn_locations())
    reg, dereg = _date(co["Date of Registration"]), _date(co["Date of Deregistration"])
    month = lambda s: s.dt.to_period("M").dt.to_timestamp()  # noqa: E731
    kind = co["Type"].map({"APTY": "proprietary", "APUB": "public"}).fillna("other")
    parts = []
    keep = _complete_months(reg, CO_START, snapshot)
    parts += _panel(co[keep], "company_registrations", month(reg[keep]), kind[keep])
    keep = _complete_months(dereg, CO_START, snapshot)
    parts += _panel(co[keep], "company_deregistrations", month(dereg[keep]), kind[keep])
    live = co["Status"].eq("REGD")
    parts += _panel(co[live], "companies_registered", pd.Series(snapshot, index=co[live].index), kind[live], "day")
    panel = schema.make(
        pd.concat(parts, ignore_index=True),
        source=CO_SOURCE,
        unit="count",
        adjustment="original",
        vintage=f"ASIC companies extract {snapshot:%Y-%m-%d}",
    )
    store.write_panel(panel, CO_SOURCE, "companies_month")
    return panel


def build() -> pd.DataFrame:
    return pd.concat([build_business_names(), build_companies()], ignore_index=True)
