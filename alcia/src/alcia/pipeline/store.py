"""Where pipeline data lives, and how downloads are recorded.

Follows the repository's data rules (CLAUDE.md):
- raw downloads go to ``data/raw/<source>/`` at the repository root and are never edited;
  ``data/raw`` is not committed (large files);
- every download is recorded in ``data/manifests/<source>.json`` (URL, retrieval time, size,
  SHA-256, licence), which is committed, so each processed file can be rebuilt from raw data;
- tidy outputs in the common panel format go to ``data/processed/<source>/<table>.parquet``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import pandas as pd

from . import schema

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
MANIFESTS = ROOT / "data" / "manifests"
USER_AGENT = "ALCIA research pipeline (https://github.com/jabthebeer/Competition-in-Australia-analysis)"


def raw_dir(source: str) -> Path:
    d = RAW / source
    d.mkdir(parents=True, exist_ok=True)
    return d


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record_download(source: str, path: Path, url: str, licence: str, note: str = "") -> dict:
    """Add or replace the manifest entry for a raw file."""
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    mpath = MANIFESTS / f"{source}.json"
    manifest = json.loads(mpath.read_text("utf-8")) if mpath.exists() else {"source": source, "files": []}
    entry = {
        "file": str(path.relative_to(ROOT)),
        "url": url,
        "retrieved": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "licence": licence,
    }
    if note:
        entry["note"] = note
    manifest["files"] = [f for f in manifest["files"] if f["file"] != entry["file"]] + [entry]
    mpath.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return entry


def download(source: str, url: str, filename: str, licence: str, client=None, refresh: bool = False) -> Path:
    """Stream a file into data/raw/<source>/ once (unless refresh) and record it."""
    import httpx

    path = raw_dir(source) / filename
    if path.exists() and not refresh:
        return path
    tmp = path.with_suffix(path.suffix + ".part")
    own = client is None
    client = client or httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=120, follow_redirects=True)
    try:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with tmp.open("wb") as f:
                for chunk in resp.iter_bytes(1 << 20):
                    f.write(chunk)
    finally:
        if own:
            client.close()
    tmp.replace(path)
    record_download(source, path, url, licence)
    return path


def write_panel(df: pd.DataFrame, source: str, table: str) -> Path:
    schema.validate(df)
    d = PROCESSED / source
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{table}.parquet"
    df.to_parquet(path, index=False)
    return path


def read_panel(source: str, table: str) -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / source / f"{table}.parquet")


def panels() -> list[tuple[str, str, Path]]:
    """Every processed panel: (source, table, path)."""
    return [(p.parent.name, p.stem, p) for p in sorted(PROCESSED.glob("*/*.parquet"))]
