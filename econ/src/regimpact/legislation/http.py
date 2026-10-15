"""Polite, cached HTTP for register adapters.

Waits between requests to the same host (the ACT register asks for 10 seconds), retries
timeouts and server errors with backoff, and caches responses on disk.
"""

from __future__ import annotations

import time
from urllib.parse import urlsplit

import httpx

from .cache import JsonCache

# Minimum seconds between requests to a host. Registers' robots.txt crawl-delays where stated.
HOST_INTERVALS = {
    "legislation.act.gov.au": 10.0,
    "www.legislation.act.gov.au": 10.0,
    "www.legislation.gov.au": 10.0,
}
DEFAULT_INTERVAL = 1.0
RETRY_WAITS = (2.0, 4.0)

_last: dict[str, float] = {}


def _wait(host: str, sleep=time.sleep, clock=time.monotonic) -> None:
    interval = HOST_INTERVALS.get(host, DEFAULT_INTERVAL)
    if host in _last:
        remaining = interval - (clock() - _last[host])
        if remaining > 0:
            sleep(remaining)
    _last[host] = clock()


class Fetcher:
    """GET with per-host spacing, retries and an optional cache. ``sleep`` is injectable for tests."""

    def __init__(self, client: httpx.Client, cache: JsonCache | None = None, sleep=time.sleep):
        self.client = client
        self.cache = cache
        self.sleep = sleep

    def _request(self, url: str, headers: dict[str, str] | None) -> httpx.Response:
        host = urlsplit(url).hostname or ""
        waits = list(RETRY_WAITS)
        while True:
            _wait(host, sleep=self.sleep)
            try:
                resp = self.client.get(url, headers=headers)
            except httpx.TransportError:  # includes timeouts
                if not waits:
                    raise
            else:
                if resp.status_code < 500 or not waits:
                    resp.raise_for_status()
                    return resp
            self.sleep(waits.pop(0))

    def json(self, url: str) -> dict:
        if self.cache and (hit := self.cache.get(url)) is not None:
            return hit
        data = self._request(url, {"Accept": "application/json"}).json()
        if self.cache:
            self.cache.put(url, data)
        return data

    def text(self, url: str) -> str:
        key = f"text:{url}"
        if self.cache and (hit := self.cache.get(key)) is not None:
            return hit["text"]
        text = self._request(url, None).text
        if self.cache:
            self.cache.put(key, {"text": text})
        return text

    def content(self, url: str) -> bytes:
        """Raw bytes (not cached: callers cache what they derive from them)."""
        return self._request(url, None).content
