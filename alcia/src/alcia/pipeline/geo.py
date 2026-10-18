"""Postcodes to ABS statistical areas (ASGS Edition 3, 2021 boundaries).

Registers record Australia Post postcodes. The ABS correspondences (data.gov.au, "ASGS 2021
correspondences", CC BY 4.0) give, for each postcode, the population-weighted share falling in each
SA2, SA3, SA4, GCCSA and LGA (RATIO_FROM_TO). ``apportion`` uses those shares to move postcode-level
counts to statistical areas; results are fractional and labelled "apportioned from postcodes".
Population weights stand in for business locations, which is an approximation.
"""

from __future__ import annotations

import io
import zipfile

import pandas as pd

from . import schema, store

SOURCE = "abs_asgs"
ZIP = "asgs2021correspondences.zip"
URL = (
    "https://data.gov.au/data/dataset/2c79581f-600e-4560-80a8-98adb1922dfc/resource/"
    "33d822ba-138e-47ae-a15f-460279c3acc3/download/asgs2021correspondences.zip"
)
LICENCE = "CC BY 4.0, Australian Bureau of Statistics"
FILES = {
    "SA2": ("CG_POSTCODE_2021_SA2_2021.xlsx", "SA2_CODE_2021", "SA2_NAME_2021"),
    "SA3": ("CG_POSTCODE_2021_SA3_2021.xlsx", "SA3_CODE_2021", "SA3_NAME_2021"),
    "SA4": ("CG_POSTCODE_2021_SA4_2021.xlsx", "SA4_CODE_2021", "SA4_NAME_2021"),
    "GCCSA": ("CG_POSTCODE_2022_GCCSA_2021.xlsx", "GCCSA_CODE_2021", "GCCSA_NAME_2021"),
    "LGA": ("CG_POSTCODE_2021_LGA_2021.xlsx", "LGA_CODE_2021", "LGA_NAME_2021"),
}


def build() -> pd.DataFrame:
    path = store.download(SOURCE, URL, ZIP, LICENCE)
    parts = []
    with zipfile.ZipFile(path) as z:
        for level, (name, code_col, name_col) in FILES.items():
            df = pd.read_excel(io.BytesIO(z.read(name)), dtype=str)
            pc_col = next(c for c in df.columns if c.startswith("POSTCODE"))
            parts.append(
                pd.DataFrame(
                    {
                        "postcode": df[pc_col].str.zfill(4),
                        "level": level,
                        "code": df[code_col],
                        "name": df[name_col],
                        "ratio": pd.to_numeric(df["RATIO_FROM_TO"]),
                        "quality": df.get("OVERALL_QUALITY_INDICATOR", ""),
                    }
                )
            )
    out = pd.concat(parts, ignore_index=True).dropna(subset=["ratio"])
    d = store.PROCESSED / "geo"
    d.mkdir(parents=True, exist_ok=True)
    out.to_parquet(d / "postcode_2021_to_asgs.parquet", index=False)
    return out


def concordance() -> pd.DataFrame:
    path = store.PROCESSED / "geo" / "postcode_2021_to_asgs.parquet"
    return pd.read_parquet(path) if path.exists() else build()


def apportion(panel: pd.DataFrame, level: str) -> pd.DataFrame:
    """Move POA (postcode) rows of a panel to an ASGS level using population shares."""
    if level not in FILES:
        raise ValueError(f"level must be one of {sorted(FILES)}")
    poa = panel[panel["geo_level"] == "POA"]
    c = concordance()
    c = c[c["level"] == level][["postcode", "code", "ratio"]]
    m = poa.merge(c, left_on="geo_code", right_on="postcode", how="inner")
    m["value"] = m["value"] * m["ratio"]
    keys = [k for k in schema.COLUMNS if k not in ("value", "geo_level", "geo_code", "adjustment")]
    out = m.groupby([*keys, "code"], dropna=False, observed=True)["value"].sum().reset_index()
    out = out.rename(columns={"code": "geo_code"}).assign(geo_level=level, adjustment="apportioned from postcodes")
    return schema.make(out)
