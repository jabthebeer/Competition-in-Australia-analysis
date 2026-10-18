"""CABEE businesses by ANZSIC division, SA2 and employment size, 30 June 2009 to 2013 (ASGS 2011).

Two archived Counts of Australian Businesses releases (ABS cat. 8165.0, CC BY 4.0) published
"Businesses by Industry Division by Statistical Area Level 2 by Employment Size Ranges":
- Jun 2007 to Jun 2011 release: June 2009, June 2010 and June 2011;
- Jun 2009 to Jun 2013 release: June 2011, June 2012 and June 2013.
Both use ASGS 2011 SA2s (geo level "SA2_2011", not comparable code-for-code with 2021 SA2s). June
2011 is in both releases, so each release is its own table and a series can be chained across the join.
The counts are stocks of businesses at 30 June (no entries or exits at this level), perturbed by
the ABS.
"""

from __future__ import annotations

import pandas as pd

from . import schema, store

SOURCE = "abs_cabee_local"
LICENCE = "CC BY 4.0, Australian Bureau of Statistics"
LEGACY = "https://www.abs.gov.au/ausstats/subscriber.nsf/log?openagent&{file}&8165.0&Data%20Cubes&{doc}&0&{rel}&{date}&Previous"
CUBES = (
    (
        "Jun 2007 to Jun 2011",
        "sa2_emp_jun2007_jun2011.xls",
        LEGACY.format(
            file="sa2_emp.xls",
            doc="EDE9D484D8E04574CA2579E90017FB8E",
            rel="Jun%202007%20to%20Jun%202011",
            date="24.04.2012",
        ),
    ),
    (
        "Jun 2009 to Jun 2013",
        "816507_jun2009_jun2013.xls",
        LEGACY.format(
            file="816507.xls",
            doc="C5583ACBDAFB7B20CA257CE700169934",
            rel="Jun%202009%20to%20Jun%202013",
            date="23.06.2014",
        ),
    ),
)
BANDS = {
    "Non employing": "non-employing",
    "1-4": "1-4 employees",
    "5-19": "5-19 employees",
    "20-199": "20-199 employees",
    "200+": "200+ employees",
    "Total": "",
}


def parse(path, release: str) -> pd.DataFrame:
    frames = []
    for sheet in pd.ExcelFile(path).sheet_names:
        if not sheet.startswith("June "):
            continue
        raw = pd.read_excel(path, sheet_name=sheet, header=None, dtype=str)
        hdr = next(i for i in range(12) if "Non employing" in raw.iloc[i].astype(str).tolist())
        cols = raw.iloc[hdr].astype(str).str.strip().tolist()
        band_cols = {j: BANDS[c] for j, c in enumerate(cols) if c in BANDS}
        code_col = next(
            j for j in range(len(cols)) if raw.iloc[hdr + 1 : hdr + 40, j].astype(str).str.fullmatch(r"\d{9}").any()
        )
        body = raw.iloc[hdr + 1 :]
        body = body[body[code_col].astype(str).str.fullmatch(r"\d{9}")]
        # "A    Agriculture, ..." or "A"; rows such as "Not classified" have no division letter
        division = body.iloc[:, 0].astype(str).str.strip().str.extract(r"^([A-S])(?:\s|$)", expand=False).fillna("")
        for j, band in band_cols.items():
            frames.append(
                pd.DataFrame(
                    {
                        "industry_code": division.to_numpy(),
                        "geo_code": body[code_col].to_numpy(),
                        "breakdown": band,
                        "period": pd.Timestamp(f"{sheet.split()[1]}-06-30"),
                        "value": pd.to_numeric(body[j], errors="coerce").to_numpy(),
                        "vintage": release,
                    }
                )
            )
    out = pd.concat(frames, ignore_index=True)
    return out[out["industry_code"].str.fullmatch(r"[A-S]")]


def build() -> pd.DataFrame:
    """One table per release (June 2011 is in both; keeping them apart lets series be chained)."""
    from .. import anzsic

    panels = []
    for release, name, url in CUBES:
        d = parse(store.download(SOURCE, url, name, LICENCE), release)
        d["industry_label"] = d["industry_code"].map(anzsic.name)
        panel = schema.make(
            d,
            source=SOURCE,
            measure="businesses",
            unit="count",
            adjustment="original",
            industry_scheme="ANZSIC06",
            industry_level="division",
            geo_level="SA2_2011",
            period_type="day",
        )
        table = "division_sa2_2011_release_" + release.split()[1] + "_" + release.split()[-1]
        store.write_panel(panel, SOURCE, table)
        panels.append(panel)
    return pd.concat(panels, ignore_index=True)
