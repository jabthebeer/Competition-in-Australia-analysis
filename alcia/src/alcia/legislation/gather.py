"""Gather the effective date of a regulatory change, and check it against the register.

The record's own sourced commencement (chosen by a person, because only some provisions
change competition conditions) is the date used for evaluation. The registers are read to
confirm it: each instrument's assent/making date and commencement dates are compared with
the record, and every disagreement is reported.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from typing import Literal

import httpx

from ..register.schema import ChangeRecord, Instrument
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


ACT_ROLES = ("principal", "amending")


def _readable(rd: RegisterDates) -> bool:
    return rd.method != "none"


def reconcile(record: ChangeRecord, register: Iterable[RegisterDates]) -> EffectiveDates:
    """Compare a record with what the registers say. Pure: no network.

    Rules:
    - Judge against the record's own jurisdiction's instruments when it lists any (a state
      record may also cite a Commonwealth Act, whose dates are context only); otherwise
      against all of them.
    - "confirmed": the effective date equals a register commencement date or version start.
    - "differs": the register states explicit commencement dates and none matches. Version
      starts alone never contradict a date (a principal law's first version starts at assent
      or registration, not necessarily at commencement).
    - "unconfirmed": nothing readable to compare against.
    - The assent/making date is checked against the Acts and principal instruments only.
    """
    register = tuple(register)
    eff = record.effective_commencement
    issues: list[str] = []

    own = [r for r in register if r.jurisdiction == record.jurisdiction]
    basis = [r for r in (own or register) if _readable(r)]

    rec_assent = record.dates.assent_or_made.date
    reg_assents = {r.assent_or_made for r in basis if r.assent_or_made and r.role in ACT_ROLES}
    if rec_assent and reg_assents and rec_assent not in reg_assents:
        shown = ", ".join(sorted(d.isoformat() for d in reg_assents))
        issues.append(f"assent/making date {rec_assent.isoformat()} not found in register ({shown})")

    for rd in register:
        if rd.repealed and eff and rd.repealed <= eff.date:
            issues.append(
                f"{rd.title}: register shows repeal on {rd.repealed.isoformat()}, on or before the effective date"
            )
        issues.extend(f"{rd.title}: {n}" for n in rd.notes)

    commenced = {c.date for r in basis for c in r.commencements}
    starts = {v.start for r in basis for v in r.versions}
    if eff is None:
        status: Status = "not-commenced"
    elif eff.date in commenced | starts:
        status = "confirmed"
    elif commenced:
        status = "differs"
        near = sorted(commenced | starts, key=lambda d: abs((d - eff.date).days))[:3]
        issues.append(
            f"effective date {eff.date.isoformat()} not among register commencement dates; nearest: "
            + ", ".join(d.isoformat() for d in near)
        )
    else:
        status = "unconfirmed"
        if own and not basis:
            issues.append(f"no readable {record.jurisdiction} register entry; other registers are context only")

    if record.dates.announced.date and eff and record.dates.announced.date > eff.date:
        issues.append("announcement date is after the effective date")
    if rec_assent and eff and rec_assent > eff.date:
        issues.append("assent/making date is after the effective date")
    if not record.verified.dates:
        issues.append(
            "record marks its dates as not fully verified"
            + (f": {record.verified.notes}" if record.verified.notes else "")
        )

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


AdapterFor = Callable[[Instrument, str], RegisterAdapter]


def gather(record: ChangeRecord, client: httpx.Client | None, adapter_for: AdapterFor) -> EffectiveDates:
    """Look up every instrument of a record in its own register, then reconcile.

    Each instrument goes to the register its URL or identifier belongs to (a state record can
    cite a Commonwealth Act). With ``client=None`` (offline), registers are not consulted and
    the result relies on the record's sourced dates alone.
    """
    found: list[RegisterDates] = []
    if client is not None:
        for inst in record.instruments:
            adapter = adapter_for(inst, record.jurisdiction)
            try:
                found.append(replace(adapter.lookup(inst, client), role=inst.role))
            except Exception as exc:  # one unreadable page must not stop a batch; report it on the record
                found.append(
                    _failed(adapter.jurisdiction, inst.title, f"register lookup failed ({type(exc).__name__}): {exc}")
                )
    return reconcile(record, found)


def _failed(jurisdiction: str, title: str, note: str) -> RegisterDates:
    return RegisterDates(
        jurisdiction=jurisdiction,
        title=title,
        register_id=None,
        url=None,
        method="none",
        retrieved_at=dt.datetime.now(dt.UTC),
        notes=(note,),
    )
