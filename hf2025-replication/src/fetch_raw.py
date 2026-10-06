"""Download untouched raw inputs into data/raw/ and record provenance.

Every file is written once, as received, and logged in data/raw/MANIFEST.csv
(source id, path, URL, UTC access time, bytes, sha256). Re-running skips files
that already exist unless --refresh is given, so results stay pinned to the
recorded vintage.

Usage:
    python src/fetch_raw.py               # fetch everything not yet on disk
    python src/fetch_raw.py --only ato_ctt
    python src/fetch_raw.py --refresh     # re-download (new vintage)
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
LIT = ROOT / "literature"
MANIFEST = RAW / "MANIFEST.csv"

# Generic research user agent. Deliberately contains no personal information.
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) research-replication"}

ABS_API = "https://data.api.abs.gov.au/rest/data"
CKAN = "https://data.gov.au/data/api/3/action"


def abs_csv(flow: str, key: str = "all") -> str:
    return f"{ABS_API}/{flow}/{key}?format=csvfilewithlabels"


# source_id -> list of (relative path under ROOT, URL)
STATIC_SOURCES: dict[str, list[tuple[str, str]]] = {
    # H&F (2025) replication files: RBA, CC BY 4.0 (EMX-derived code inside is CC0).
    "hf2025_supplementary": [
        ("data/raw/hf2025_supplementary/rdp-2025-05-supplementary-information.zip",
         "https://www.rba.gov.au/publications/rdp/2025/2025-05/rdp-2025-05-supplementary-information.zip"),
    ],
    # EMX (2023) JPE replication package, Harvard Dataverse doi:10.7910/DVN/GVLDPZ, CC0 1.0.
    "emx2023_replication": [
        ("data/raw/emx2023_replication/emx2023_dataverse.zip",
         "https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/GVLDPZ"),
    ],
    # Copyrighted papers: downloaded for reading only; git-ignored.
    "literature": [
        ("literature/emx2023_jpe.pdf",
         "https://www.chrisedmond.net/Edmond%20Midrigan%20Xu%20JPE%202023.pdf"),
        ("literature/champion_edmond_hambur_2025.pdf",
         "https://www.chrisedmond.net/papers/CEH_Competition_Markups_Inflation_2025.pdf"),
    ],
    # ABS Data API (SDMX), CC BY 4.0.
    "abs_australian_industry": [
        ("data/raw/abs/AUSTRALIAN_INDUSTRY.csv", abs_csv("ABS,AUSTRALIAN_INDUSTRY,1.1.0")),
    ],
    "abs_national_accounts": [
        ("data/raw/abs/ANA_AGG.csv", abs_csv("ABS,ANA_AGG,1.0.0")),
    ],
    "abs_population": [
        # Estimated resident population, persons, all ages, Australia, quarterly.
        ("data/raw/abs/ERP_Q_AUS_persons_total.csv", abs_csv("ABS,ERP_Q,1.0.0", "1.3.TOT.AUS.Q")),
    ],
}


def ato_ctt_sources() -> list[tuple[str, str]]:
    """ATO Corporate Tax Transparency 'Report of Entity Tax Information' (CC BY 3.0 AU), via CKAN."""
    r = requests.get(f"{CKAN}/package_show", params={"id": "corporate-transparency"},
                     headers=HEADERS, timeout=60)
    r.raise_for_status()
    out = []
    for res in r.json()["result"]["resources"]:
        name = res["name"]
        if "Report of Entity Tax Information" not in name:
            continue
        year = name.split()[0]  # e.g. "2023-24"
        out.append((f"data/raw/ato_ctt/ato_ctt_{year}.xlsx", res["url"]))
    return sorted(out)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def append_manifest(row: dict) -> None:
    new = not MANIFEST.exists()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["source_id", "path", "url", "accessed_utc", "bytes", "sha256"])
        if new:
            w.writeheader()
        w.writerow(row)


def fetch(source_id: str, rel: str, url: str, refresh: bool) -> None:
    dest = ROOT / rel
    if dest.exists() and not refresh:
        print(f"  skip (exists) {rel}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            with requests.get(url, headers=HEADERS, timeout=600, stream=True) as r:
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            tmp.replace(dest)
            break
        except requests.RequestException as e:
            if attempt == 3:
                raise
            wait = 2 ** (attempt + 1)
            print(f"  retry in {wait}s after: {e}")
            time.sleep(wait)
    append_manifest({
        "source_id": source_id, "path": rel, "url": url,
        "accessed_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bytes": dest.stat().st_size, "sha256": sha256(dest),
    })
    print(f"  saved {rel} ({dest.stat().st_size:,} bytes)")
    time.sleep(1)  # be polite to servers


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", help="source ids to fetch")
    ap.add_argument("--refresh", action="store_true", help="re-download files that already exist")
    args = ap.parse_args()

    sources = dict(STATIC_SOURCES)
    if not args.only or "ato_ctt" in args.only:
        sources["ato_ctt"] = ato_ctt_sources()

    for sid, files in sources.items():
        if args.only and sid not in args.only:
            continue
        print(sid)
        for rel, url in files:
            fetch(sid, rel, url, args.refresh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
