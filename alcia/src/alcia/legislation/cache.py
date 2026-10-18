"""A small on-disk cache of register responses, keyed by URL.

Keeps repeat runs polite to the registers and makes a run reproducible: each entry stores
the URL and the time it was fetched. The cache folder is not committed.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path


def default_cache_dir() -> Path:
    return Path(__file__).resolve().parents[3] / ".cache" / "legislation"


class JsonCache:
    def __init__(self, folder: Path | None = None, max_age: dt.timedelta | None = dt.timedelta(days=7)):
        self.folder = folder or default_cache_dir()
        self.max_age = max_age

    def _path(self, url: str) -> Path:
        return self.folder / f"{hashlib.sha256(url.encode()).hexdigest()[:32]}.json"

    def get(self, url: str) -> dict | None:
        path = self._path(url)
        if not path.exists():
            return None
        entry = json.loads(path.read_text(encoding="utf-8"))
        fetched = dt.datetime.fromisoformat(entry["fetched_at"])
        if self.max_age is not None and dt.datetime.now(dt.UTC) - fetched > self.max_age:
            return None
        return entry["body"]

    def put(self, url: str, body: dict) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        entry = {"url": url, "fetched_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"), "body": body}
        self._path(url).write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")
