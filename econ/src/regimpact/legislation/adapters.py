"""Which adapter reads which jurisdiction's register."""

from __future__ import annotations

from functools import cache

from .base import RegisterAdapter, Unsupported
from .cache import JsonCache
from .frl import FederalRegister


@cache
def adapter_for(jurisdiction: str) -> RegisterAdapter:
    if jurisdiction == "CTH":
        return FederalRegister(cache=JsonCache())
    return Unsupported(jurisdiction, f"{jurisdiction} register: automatic date checks not built yet; "
                                     "relying on the record's sourced dates")
