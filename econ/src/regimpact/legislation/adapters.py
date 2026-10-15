"""Route each instrument to the register it belongs to."""

from __future__ import annotations

import re
from functools import cache

from ..register.schema import Instrument
from .base import RegisterAdapter
from .cache import JsonCache
from .frl import ID_RE, FederalRegister
from .states import state_adapters

HOSTS = {
    "legislation.gov.au": "CTH",
    "legislation.nsw.gov.au": "NSW",
    "legislation.vic.gov.au": "VIC",
    "legislation.qld.gov.au": "QLD",
    "legislation.wa.gov.au": "WA",
    "legislation.sa.gov.au": "SA",
    "legislation.tas.gov.au": "TAS",
    "legislation.act.gov.au": "ACT",
    "legislation.nt.gov.au": "NT",
}


def register_for(instrument: Instrument, record_jurisdiction: str) -> str:
    """Which register an instrument lives in: by URL host, then Commonwealth ID, then the record."""
    url = str(instrument.register_url or "")
    if m := re.match(r"https?://(?:www\.)?([^/]+)", url):
        host = m.group(1).lower()
        if host in HOSTS:
            return HOSTS[host]
    if instrument.register_id and ID_RE.fullmatch(instrument.register_id.strip()):
        return "CTH"
    return record_jurisdiction


@cache
def _adapters() -> dict[str, RegisterAdapter]:
    shared = JsonCache()
    return {"CTH": FederalRegister(cache=shared), **state_adapters(shared)}


def adapter_for(instrument: Instrument, record_jurisdiction: str) -> RegisterAdapter:
    return _adapters()[register_for(instrument, record_jurisdiction)]
