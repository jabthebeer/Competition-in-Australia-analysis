"""Shared types for reading dates from legislation registers.

Each register (the Federal Register of Legislation, and each state and territory's) gets
an adapter that turns what the register publishes into ``RegisterDates``. Adapters never
guess: a date they can't read is left as ``None`` with a note saying why.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Literal, Protocol

import httpx

from ..register.schema import Instrument

Method = Literal["api", "html", "none"]


@dataclass(frozen=True)
class RegisterCommencement:
    date: dt.date
    what: str
    basis: str  # where in the register the date came from, e.g. "compilation start date"


@dataclass(frozen=True)
class Version:
    """One point-in-time version (compilation) of a principal Act or instrument."""

    start: dt.date
    end: dt.date | None
    label: str
    amended_by: tuple[str, ...] = ()


@dataclass(frozen=True)
class RegisterDates:
    jurisdiction: str
    title: str
    register_id: str | None
    url: str | None
    method: Method
    retrieved_at: dt.datetime
    assent_or_made: dt.date | None = None
    registered: dt.date | None = None
    commencements: tuple[RegisterCommencement, ...] = ()
    repealed: dt.date | None = None
    status: str | None = None
    versions: tuple[Version, ...] = ()
    notes: tuple[str, ...] = ()
    role: str | None = None  # the instrument's role in the record (set by gather)

    def as_dict(self) -> dict[str, object]:
        def iso(d: dt.date | None) -> str | None:
            return d.isoformat() if d else None

        return {
            "jurisdiction": self.jurisdiction,
            "title": self.title,
            "register_id": self.register_id,
            "url": self.url,
            "method": self.method,
            "retrieved_at": self.retrieved_at.isoformat(timespec="seconds"),
            "assent_or_made": iso(self.assent_or_made),
            "registered": iso(self.registered),
            "commencements": [
                {"date": c.date.isoformat(), "what": c.what, "basis": c.basis} for c in self.commencements
            ],
            "repealed": iso(self.repealed),
            "status": self.status,
            "versions": [
                {"start": v.start.isoformat(), "end": iso(v.end), "label": v.label, "amended_by": list(v.amended_by)}
                for v in self.versions
            ],
            "notes": list(self.notes),
            "role": self.role,
        }


class RegisterAdapter(Protocol):
    jurisdiction: str

    def lookup(self, instrument: Instrument, client: httpx.Client) -> RegisterDates: ...


@dataclass
class Unsupported:
    """Fallback for a register with no machine-readable dates: records must carry sourced dates."""

    jurisdiction: str
    reason: str
    notes: list[str] = field(default_factory=list)

    def lookup(self, instrument: Instrument, client: httpx.Client) -> RegisterDates:
        return RegisterDates(
            jurisdiction=self.jurisdiction,
            title=instrument.title,
            register_id=instrument.register_id,
            url=str(instrument.register_url) if instrument.register_url else None,
            method="none",
            retrieved_at=dt.datetime.now(dt.UTC),
            notes=(self.reason, *self.notes),
        )


USER_AGENT = (
    "alcia/0.1 (research on Australian regulation and competition; "
    "https://github.com/jabthebeer/Competition-in-Australia-analysis)"
)


def make_client(transport: httpx.BaseTransport | None = None) -> httpx.Client:
    """An HTTP client with a descriptive User-Agent and conservative timeouts."""
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=httpx.Timeout(30.0, connect=15.0),
        follow_redirects=True,
        transport=transport,
    )
