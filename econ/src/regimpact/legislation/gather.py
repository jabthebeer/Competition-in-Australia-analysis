"""Gather the effective date of a regulatory change, and check it against the register.

The record's own sourced commencement (chosen by a person, because only some provisions
change competition conditions) is the date used for evaluation. The registers are read to
confirm it: each instrument's assent/making date and commencement dates are compared with
the record, and every disagreement is reported.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Literal

import httpx

from ..register.schema import ChangeRecord
from ..timing import Timing, timing
from .base import RegisterAdapter, RegisterDates

Status = Literal["confirmed", "differs", "unconfirmed", "not-commenced"]

STATUS_HELP: dict[str, str] = {
    "confirmed": "a register date matches the record's effective date",
    "differs": "the register has dates, but none matches the record's effective date",
    "unconfirmed": "no machine-readable register date to check against (sourced date only)",
    "not-commenced": "the change has not commenced",
}


@dataclass(frozen=True)
class EffectiveDates:
    record_id: str
    jurisdiction: str
    title: str
    effective: dt.date | None
    effective_what: str | None
    effective_source: str | None
    announced: dt.date | None
    assent_or_made: dt.date | None
    timing: Timing | None
    status: Status
    register: tuple[RegisterDates, ...]
    issues: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        def iso(d: dt.date | None) -> str | None:
            return d.isoformat() if d else None

        return {
            "record_id": self.record_id,
            "jurisdiction": self.jurisdiction,
            "title": self.title,
            "effective_date": iso(self.effective),
            "effective_what": self.effective_what,
            "effective_source": self.effective_source,
            "announced": iso(self.announced),
            "assent_or_made": iso(self.assent_or_made),
            "timing": self.timing.as_dict() if self.timing else None,
            "status": self.status,
            "issues": list(self.issues),
            "register": [r.as_dict() for r in self.register],
        }


def _register_dates_for(rd: RegisterDates) -> set[dt.date]:
    dates = {c.date for c in rd.commencements}
    dates.update(v.start for v in rd.versions)
    return dates


def reconcile(record: ChangeRecord, register: Iterable[RegisterDates]) -> EffectiveDates:
    """Compare a record with what the registers say. Pure: no network."""
    register = tuple(register)
    eff = record.effective_commencement
    issues: list[str] = []

    rec_assent = record.dates.assent_or_made.date
    reg_assents = {r.assent_or_made for r in register if r.assent_or_made}
    if rec_assent and reg_assents and rec_assent not in reg_assents:
        shown = ", ".join(sorted(d.isoformat() for d in reg_assents))
        issues.append(f"assent/making date {rec_assent.isoformat()} not found in register ({shown})")

    for rd in register:
        if rd.repealed and eff and rd.repealed <= eff.date:
            issues.append(f"{rd.title}: register shows repeal on {rd.repealed.isoformat()}, "
                          f"on or before the effective date")
        issues.extend(f"{rd.title}: {n}" for n in rd.notes)

    if eff is None:
        status: Status = "not-commenced"
    else:
        known = set().union(*(_register_dates_for(r) for r in register)) if register else set()
        if eff.date in known:
            status = "confirmed"
        elif known:
            status = "differs"
            near = sorted(known, key=lambda d: abs((d - eff.date).days))[:3]
            issues.append(
                f"effective date {eff.date.isoformat()} not among register dates; nearest: "
                + ", ".join(d.isoformat() for d in near)
            )
        else:
            status = "unconfirmed"

    if record.dates.announced.date and eff and record.dates.announced.date > eff.date:
        issues.append("announcement date is after the effective date")
    if rec_assent and eff and rec_assent > eff.date:
        issues.append("assent/making date is after the effective date")
    if not record.verified.dates:
        issues.append("record marks its dates as not fully verified" +
                      (f": {record.verified.notes}" if record.verified.notes else ""))

    return EffectiveDates(
        record_id=record.id,
        jurisdiction=record.jurisdiction,
        title=record.title,
        effective=eff.date if eff else None,
        effective_what=eff.what if eff else None,
        effective_source=str(eff.source) if eff else None,
        announced=record.dates.announced.date,
        assent_or_made=rec_assent,
        timing=timing(eff.date) if eff else None,
        status=status,
        register=register,
        issues=tuple(issues),
    )


AdapterFor = Callable[[str], RegisterAdapter]


def gather(record: ChangeRecord, client: httpx.Client | None, adapter_for: AdapterFor) -> EffectiveDates:
    """Look up every instrument of a record in its register, then reconcile.

    With ``client=None`` (offline), registers are not consulted and the result relies on the
    record's sourced dates alone.
    """
    found: list[RegisterDates] = []
    if client is not None:
        adapter = adapter_for(record.jurisdiction)
        for inst in record.instruments:
            try:
                found.append(adapter.lookup(inst, client))
            except httpx.HTTPError as exc:
                found.append(_failed(record.jurisdiction, inst.title, f"register request failed: {exc}"))
    return reconcile(record, found)


def _failed(jurisdiction: str, title: str, note: str) -> RegisterDates:
    return RegisterDates(jurisdiction=jurisdiction, title=title, register_id=None, url=None, method="none",
                         retrieved_at=dt.datetime.now(dt.UTC), notes=(note,))
