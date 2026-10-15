"""Federal Register of Legislation (legislation.gov.au) adapter.

Uses the public REST API (https://api.prod.legislation.gov.au/v1/, OData style, no key).

How dates are read:
- assent (Acts) or making date (instruments): ``makingDate`` on the title;
- registration: ``asMadeRegisteredAt``;
- repeal or cessation: the first matching entry in ``statusHistory``;
- commencement of a principal Act or instrument: the start of its first version;
- commencement of an AMENDING Act or instrument: the register has no structured s 2
  commencement table, but every compilation (version) of the principal it amends lists the
  amendments it incorporates (``reasons[].affectedByTitle``). The start date of a version
  that cites the amendment is when that amendment took effect in the principal. This is
  the date that matters for evaluation, and it is reported per principal and provision.
"""

from __future__ import annotations

import datetime as dt
import re
from urllib.parse import quote

import httpx

from ..register.schema import Instrument
from .base import RegisterCommencement, RegisterDates, Version
from .cache import JsonCache

API = "https://api.prod.legislation.gov.au/v1"
SITE = "https://www.legislation.gov.au"
ID_RE = re.compile(r"\b([CF]\d{4}[A-Z]\d{5})\b")
AFFECT_KINDS = "[amending,repealing,commencing,modifying,ceasing,savingTransitionalOrApplication,sunsetAltering]"
VERSION_FIELDS = "titleId,start,end,name,status,registerId,compilationNumber,reasons"
ENDED_STATUSES = {"Repealed", "Ceased", "NeverEffective"}


def _q(value: str) -> str:
    return quote(value, safe="$,()'=")


def _url(path: str, **params: str) -> str:
    if not params:
        return f"{API}/{path}"
    return f"{API}/{path}?" + "&".join(f"{_q(k)}={_q(v)}" for k, v in params.items())


def _date(value: str | None) -> dt.date | None:
    """API dates are local date-times without a zone, e.g. '2022-11-09T00:00:00'."""
    return dt.date.fromisoformat(value[:10]) if value else None


def _status(value: object) -> str | None:
    # Some endpoints return enum names ("InForce"), others numbers; keep whichever is given.
    return None if value is None else str(value)


class FederalRegister:
    jurisdiction = "CTH"

    def __init__(self, cache: JsonCache | None = None, max_principals: int = 6, today: dt.date | None = None):
        self.cache = cache
        self.max_principals = max_principals
        self.today = today or dt.date.today()

    # --- HTTP -----------------------------------------------------------------------------
    def _get(self, client: httpx.Client, url: str) -> dict:
        if self.cache and (hit := self.cache.get(url)) is not None:
            return hit
        resp = client.get(url, headers={"Accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()
        if self.cache:
            self.cache.put(url, data)
        return data

    # --- Lookups --------------------------------------------------------------------------
    def resolve_id(self, instrument: Instrument, client: httpx.Client) -> tuple[str | None, list[str]]:
        """Register ID from the record, its URL, or an exact title search."""
        for candidate in (instrument.register_id, str(instrument.register_url or "")):
            if candidate and (m := ID_RE.search(candidate)):
                return m.group(1), []
        name = instrument.title.replace("'", "''")
        data = self._get(client, _url("titles", **{"$filter": f"name eq '{name}'", "$select": "id,name,collection"}))
        hits = data.get("value", [])
        if len(hits) == 1:
            return hits[0]["id"], []
        if not hits:
            return None, [f"no Federal Register title named '{instrument.title}'"]
        ids = ", ".join(h["id"] for h in hits)
        return None, [f"several Federal Register titles named '{instrument.title}' ({ids}); set register_id"]

    def title(self, client: httpx.Client, title_id: str) -> dict:
        return self._get(client, _url(f"titles('{title_id}')"))

    def versions(self, client: httpx.Client, title_id: str) -> list[dict]:
        url = _url("Versions", **{"$filter": f"titleId eq '{title_id}'", "$orderby": "start asc",
                                  "$select": VERSION_FIELDS})
        return self._get(client, url).get("value", [])

    def principals_affected(self, client: httpx.Client, title_id: str) -> list[dict]:
        criteria = f"affects(\"{title_id}\",{AFFECT_KINDS})"
        url = _url(f"titles/search(criteria='{criteria}')", **{"$select": "id,name,collection,isPrincipal"})
        return [t for t in self._get(client, url).get("value", []) if t.get("isPrincipal")]

    # --- Adapter interface ------------------------------------------------------------------
    def lookup(self, instrument: Instrument, client: httpx.Client) -> RegisterDates:
        now = dt.datetime.now(dt.UTC)
        title_id, notes = self.resolve_id(instrument, client)
        if title_id is None:
            return RegisterDates(jurisdiction="CTH", title=instrument.title, register_id=None, url=None,
                                 method="api", retrieved_at=now, notes=tuple(notes))

        t = self.title(client, title_id)
        notes = list(notes)
        if t.get("name") and t["name"] != instrument.title:
            notes.append(f"register title is '{t['name']}'")
        repealed = next((_date(h.get("start")) for h in t.get("statusHistory", [])
                         if _status(h.get("status")) in ENDED_STATUSES), None)

        commencements: list[RegisterCommencement] = []
        versions: list[Version] = []
        if t.get("isPrincipal"):
            raw = self.versions(client, title_id)
            versions = [_version(v) for v in raw]
            if versions:
                commencements.append(RegisterCommencement(
                    date=versions[0].start, what="first version in force (as made)",
                    basis="start of the earliest version on the register"))
        else:
            principals = self.principals_affected(client, title_id)
            if len(principals) > self.max_principals:
                notes.append(f"amends {len(principals)} principal titles; checked the first {self.max_principals}")
            for p in principals[: self.max_principals]:
                found = False
                for v in self.versions(client, p["id"]):
                    for r in v.get("reasons") or []:
                        by = r.get("affectedByTitle") or {}
                        if by.get("titleId") != title_id:
                            continue
                        found = True
                        start = _date(v["start"])
                        scheduled = " (scheduled: not yet in force)" if start and start > self.today else ""
                        commencements.append(RegisterCommencement(
                            date=start,
                            what=f"{by.get('provisions') or 'provisions'} amending {p['name']}{scheduled}",
                            basis=f"start of {p['name']} compilation {v.get('compilationNumber')}",
                        ))
                if not found:
                    notes.append(f"no compilation of {p['name']} cites this instrument "
                                 "(not yet compiled, never commenced, or repealed first)")

        return RegisterDates(
            jurisdiction="CTH",
            title=t.get("name") or instrument.title,
            register_id=title_id,
            url=f"{SITE}/{title_id}/latest/versions",
            method="api",
            retrieved_at=now,
            assent_or_made=_date(t.get("makingDate")),
            registered=_date(t.get("asMadeRegisteredAt")),
            commencements=tuple(sorted(set(commencements), key=lambda c: (c.date, c.what))),
            repealed=repealed,
            status=_status(t.get("status")),
            versions=tuple(versions),
            notes=tuple(notes),
        )


def _version(v: dict) -> Version:
    amended_by = tuple(
        f"{(r.get('affectedByTitle') or {}).get('titleId')}: {(r.get('affectedByTitle') or {}).get('provisions')}"
        for r in v.get("reasons") or [] if r.get("affectedByTitle")
    )
    return Version(start=_date(v["start"]), end=_date(v.get("end")),
                   label=f"compilation {v.get('compilationNumber')} ({v.get('registerId')})", amended_by=amended_by)
