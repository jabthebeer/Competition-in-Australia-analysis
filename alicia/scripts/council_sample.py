"""Choose the phase E sample councils (docs/plan_councils.md, decision E2).

For each state with councils, the sample is the capital city plus:
- the regional city: the council with the most businesses outside the
  state's greater capital city area and outside the major cities remoteness
  class (so Newcastle and the Gold Coast, which are major cities, are not
  counted as regional);
- the rural council: the council with the median number of businesses among
  councils in outer regional, remote or very remote areas.

Inputs:
- data/raw/abs_asgs/{MB,LGA,RA}_2021_AUST.xlsx: ABS ASGS Edition 3 allocation
  files (download with --download);
- data/processed/abs_regional/division_local_year.parquet: ABS Data by Region,
  businesses by LGA (ASGS 2021), 30 June 2025.

A council's greater capital city area and remoteness are those of most of its
SA1s (each SA1 is assigned to the council holding most of its mesh blocks).
SA1 counts stand in for population.

Output: data/processed/legislation/council_sample.csv
"""

from __future__ import annotations

import argparse
import collections
import urllib.request
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/abs_asgs"
OUT = ROOT / "data/processed/legislation/council_sample.csv"
BASE = (
    "https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/"
    "edition-3-july-2021-june-2026/access-and-downloads/allocation-files/"
)
FILES = ("MB_2021_AUST.xlsx", "LGA_2021_AUST.xlsx", "RA_2021_AUST.xlsx")
CAPITALS = {
    "1": "17200",  # Sydney
    "2": "24600",  # Melbourne
    "3": "31000",  # Brisbane
    "4": "40070",  # Adelaide
    "5": "57080",  # Perth
    "6": "62810",  # Hobart
    "7": "71000",  # Darwin
}
STATES = {"1": "NSW", "2": "VIC", "3": "QLD", "4": "SA", "5": "WA", "6": "TAS", "7": "NT"}
RURAL_RA = {"Outer Regional Australia", "Remote Australia", "Very Remote Australia"}
PERIOD = "2025-06-30"


def download() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        urllib.request.urlretrieve(BASE + f, RAW / f)


def rows(name: str, cols: tuple[str, ...]):
    wb = openpyxl.load_workbook(RAW / name, read_only=True)
    ws = wb[wb.sheetnames[0]]
    it = ws.iter_rows(values_only=True)
    head = next(it)
    idx = [head.index(c) for c in cols]
    for r in it:
        if r[0] is None:
            continue
        yield tuple(r[i] for i in idx)


def council_attributes() -> pd.DataFrame:
    mb_lga = {
        mb: (code, name)
        for mb, code, name in rows("LGA_2021_AUST.xlsx", ("MB_CODE_2021", "LGA_CODE_2021", "LGA_NAME_2021"))
    }
    sa1_lga: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    sa1_gcc: dict[str, str] = {}
    for mb, sa1, gcc in rows("MB_2021_AUST.xlsx", ("MB_CODE_2021", "SA1_CODE_2021", "GCCSA_NAME_2021")):
        if mb in mb_lga:
            sa1_lga[sa1][mb_lga[mb]] += 1
        sa1_gcc[sa1] = gcc
    sa1_ra = {sa1: ra for sa1, ra in rows("RA_2021_AUST.xlsx", ("SA1_CODE_2021", "RA_NAME_2021"))}
    gcc: dict[tuple, collections.Counter] = collections.defaultdict(collections.Counter)
    ra: dict[tuple, collections.Counter] = collections.defaultdict(collections.Counter)
    for sa1, c in sa1_lga.items():
        lga = c.most_common(1)[0][0]
        gcc[lga][sa1_gcc.get(sa1)] += 1
        ra[lga][sa1_ra.get(sa1)] += 1
    out = []
    for lga in gcc:
        out.append(
            {
                "lga_code": lga[0],
                "lga_name": lga[1],
                "sa1s": sum(gcc[lga].values()),
                "gccsa": gcc[lga].most_common(1)[0][0],
                "remoteness": ra[lga].most_common(1)[0][0],
            }
        )
    return pd.DataFrame(out)


def businesses() -> pd.DataFrame:
    d = pd.read_parquet(ROOT / "data/processed/abs_regional/division_local_year.parquet")
    d = d[(d.geo_level == "LGA") & (d.industry_level == "total") & (d.period == pd.Timestamp(PERIOD))]
    return d[["geo_code", "value"]].rename(columns={"geo_code": "lga_code", "value": "businesses"})


def choose(df: pd.DataFrame) -> pd.DataFrame:
    picks = []
    for ste, state in STATES.items():
        s = df[df.lga_code.str[0] == ste].dropna(subset=["businesses"])
        s = s[~s.lga_name.str.contains("Unincorporated|No usual address|Migratory", regex=True)]
        cap = s[s.lga_code == CAPITALS[ste]].iloc[0]
        picks.append({**cap.to_dict(), "state": state, "role": "capital", "rule": "capital city council"})
        rest = s[s.gccsa.str.startswith("Rest of") & (s.remoteness != "Major Cities of Australia")]
        rest = rest.sort_values("businesses", ascending=False)
        reg = rest.iloc[0]
        picks.append(
            {
                **reg.to_dict(),
                "state": state,
                "role": "regional",
                "rule": "most businesses outside the greater capital city area and the major cities",
            }
        )
        rural = s[s.remoteness.isin(RURAL_RA) & (s.lga_code != reg.lga_code) & (s.lga_code != cap.lga_code)]
        rural = rural.sort_values(["businesses", "lga_code"]).reset_index(drop=True)
        r = rural.iloc[(len(rural) - 1) // 2]
        picks.append(
            {
                **r.to_dict(),
                "state": state,
                "role": "rural",
                "rule": f"median businesses among {len(rural)} outer regional, remote or very remote councils",
            }
        )
    cols = ["state", "role", "lga_code", "lga_name", "businesses", "gccsa", "remoteness", "rule"]
    return pd.DataFrame(picks)[cols]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--download", action="store_true", help="download the ABS allocation files first")
    a = ap.parse_args()
    if a.download or not all((RAW / f).exists() for f in FILES):
        download()
    df = council_attributes().merge(businesses(), on="lga_code", how="left")
    out = choose(df)
    out["businesses"] = out.businesses.astype(int)
    out["as_at"] = PERIOD
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
