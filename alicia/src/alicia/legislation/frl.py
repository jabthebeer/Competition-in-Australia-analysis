"""Federal Register of Legislation (legislation.gov.au) adapter.

Uses the public REST API (https://api.prod.legislation.gov.au/v1/, OData style, no key;
content CC BY 4.0, "Sourced from the Federal Register of Legislation").

Where each date comes from:
- assent (Acts) or making date (instruments): ``makingDate`` on the title;
- registration: ``asMadeRegisteredAt``;
- repeal or cessation: the first matching entry in ``statusHistory``;
- the law's own commencement: the s 2 "Commencement information" table in the as-made
  Word document (column 3 gives the date once known), or for instruments without a table,
  a sentence such as "This instrument commences on 1 April 2017";
- when an AMENDING law took effect in the law it amends: each compilation (version) of the
  principal lists the amendments it incorporates (``reasons[].affectedByTitle``), so the
  start of a version that cites the amendment is when it took effect, per schedule;
- version starts of a principal law (a delayed commencement shows up as a version boundary).

Known gaps: the API has no structured commencement field; a provision that amends nothing
never appears in a version list; proclamation dates are only in the proclamation's text.
"""

from __future__ import annotations

import datetime as dt
import re
import time
import zipfile
from urllib.parse import quote

import httpx

from ..register.schema import Instrument
from .base import RegisterCommencement, RegisterDates, Version
from .cache import JsonCache
from .http import Fetcher
from .text import commencement_in_prose, commencement_table, docx_tables, docx_text, find_dates

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


def as_made_word_url(register_id: str) -> str:
    return _url(
        f"documents/find(registerId='{register_id}',type='Primary',format='Word',"
        "uniqueTypeNumber=0,volumeNumber=0,rectificationVersionNumber=0)"
    )


def _date(value: str | None) -> dt.date | None:
    """API dates are local date-times without a zone, e.g. '2022-11-09T00:00:00'."""
    return dt.date.fromisoformat(value[:10]) if value else None


def _status(value: object) -> str | None:
    # Some endpoints return enum names ("InForce"), others numbers; keep whichever is given.
    return None if value is None else str(value)


class FederalRegister:
    jurisdiction = "CTH"

    def __init__(
        self,
        cache: JsonCache | None = None,
        max_principals: int = 6,
        today: dt.date | None = None,
        read_commencement_text: bool = True,
        sleep=time.sleep,
    ):
        self.cache = cache
        self.max_principals = max_principals
        self.today = today or dt.date.today()
        self.read_commencement_text = read_commencement_text
        self.sleep = sleep

    # --- Lookups --------------------------------------------------------------------------
    def resolve_id(self, instrument: Instrument, fetch: Fetcher) -> tuple[str | None, list[str]]:
        """Register ID from the record, its URL, or an exact title search."""
        for candidate in (instrument.register_id, str(instrument.register_url or "")):
            if candidate and (m := ID_RE.search(candidate)):
                return m.group(1), []
        name = instrument.title.replace("'", "''")
        data = fetch.json(_url("titles", **{"$filter": f"name eq '{name}'", "$select": "id,name,collection"}))
        hits = data.get("value", [])
        if len(hits) == 1:
            return hits[0]["id"], []
        if not hits:
            return None, [f"no Federal Register title named '{instrument.title}'"]
        ids = ", ".join(h["id"] for h in hits)
        return None, [f"several Federal Register titles named '{instrument.title}' ({ids}); set register_id"]

    def versions(self, fetch: Fetcher, title_id: str) -> list[dict]:
        url = _url(
            "Versions", **{"$filter": f"titleId eq '{title_id}'", "$orderby": "start asc", "$select": VERSION_FIELDS}
        )
        return fetch.json(url).get("value", [])

    def principals_affected(self, fetch: Fetcher, title_id: str) -> list[dict]:
        criteria = f'affects("{title_id}",{AFFECT_KINDS})'
        url = _url(f"titles/search(criteria='{criteria}')", **{"$select": "id,name,collection,isPrincipal"})
        return [t for t in fetch.json(url).get("value", []) if t.get("isPrincipal")]

    def own_commencement(self, fetch: Fetcher, title_id: str) -> tuple[list[RegisterCommencement], list[str]]:
        """Commencement as stated in the law itself (s 2), read from the as-made Word document."""
        url = as_made_word_url(title_id)
        key = f"s2:{url}"
        cached = fetch.cache.get(key) if fetch.cache else None
        if cached is None:
            try:
                data = fetch.content(url)
            except httpx.HTTPStatusError as exc:
                return [], [f"as-made Word document unavailable ({exc.response.status_code})"]
            try:
                rows = commencement_table(docx_tables(data))
                prose = [] if rows else [d.isoformat() for d in commencement_in_prose(docx_text(data))]
            except (zipfile.BadZipFile, KeyError):
                return [], ["as-made document is not a readable Word (.docx) file; s 2 not checked"]
            cached = {"rows": rows, "prose": prose}
            if fetch.cache:
                fetch.cache.put(key, cached)
        out = []
        for provisions, rule, details in cached["rows"]:
            for d in find_dates(details):
                out.append(RegisterCommencement(d, f"{provisions}: {rule}", "s 2 commencement table (as made)"))
        for iso in cached["prose"]:
            out.append(
                RegisterCommencement(
                    dt.date.fromisoformat(iso), "commencement provision", "commencement sentence in the as-made text"
                )
            )
        notes = (
            []
            if out
            else [
                "no dated commencement found in the as-made text (e.g. 'a day to be fixed by "
                "Proclamation'); check the proclamation"
            ]
        )
        return out, notes

    # --- Adapter interface ------------------------------------------------------------------
    def lookup(self, instrument: Instrument, client: httpx.Client) -> RegisterDates:
        fetch = Fetcher(client, self.cache, sleep=self.sleep)
        now = dt.datetime.now(dt.UTC)
        title_id, notes = self.resolve_id(instrument, fetch)
        if title_id is None:
            return RegisterDates(
                jurisdiction="CTH",
                title=instrument.title,
                register_id=None,
                url=None,
                method="api",
                retrieved_at=now,
                notes=tuple(notes),
            )

        t = fetch.json(_url(f"titles('{title_id}')"))
        notes = list(notes)
        if t.get("name") and t["name"] != instrument.title:
            notes.append(f"register title is '{t['name']}'")
        repealed = next(
            (_date(h.get("start")) for h in t.get("statusHistory", []) if _status(h.get("status")) in ENDED_STATUSES),
            None,
        )

        commencements: list[RegisterCommencement] = []
        versions: list[Version] = []
        if self.read_commencement_text:
            own, own_notes = self.own_commencement(fetch, title_id)
            commencements += own
            notes += own_notes
        if t.get("isPrincipal"):
            versions = [_version(v) for v in self.versions(fetch, title_id)]
        else:
            principals = self.principals_affected(fetch, title_id)
            if len(principals) > self.max_principals:
                notes.append(f"amends {len(principals)} principal titles; checked the first {self.max_principals}")
            for p in principals[: self.max_principals]:
                found = False
                for v in self.versions(fetch, p["id"]):
                    for r in v.get("reasons") or []:
                        by = r.get("affectedByTitle") or {}
                        if by.get("titleId") != title_id:
                            continue
                        found = True
                        start = _date(v["start"])
                        scheduled = " (scheduled: not yet in force)" if start and start > self.today else ""
                        commencements.append(
                            RegisterCommencement(
                                date=start,
                                what=f"{by.get('provisions') or 'provisions'} amending {p['name']}{scheduled}",
                                basis=f"start of {p['name']} compilation {v.get('compilationNumber')}",
                            )
                        )
                if not found:
                    notes.append(
                        f"no compilation of {p['name']} cites this instrument "
                        "(not yet compiled, never commenced, or repealed first)"
                    )

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
        for r in v.get("reasons") or []
        if r.get("affectedByTitle")
    )
    return Version(
        start=_date(v["start"]),
        end=_date(v.get("end")),
        label=f"compilation {v.get('compilationNumber')} ({v.get('registerId')})",
        amended_by=amended_by,
    )
