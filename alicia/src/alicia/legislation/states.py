"""State and territory register adapters.

What each register exposes, and what is read here (checked 14-15 October 2026):

- Queensland: as-made XML (assent or notification date); for a principal Act, its
  legislative-history XML (each amending Act's commencement, and reprint effective dates).
- Tasmania: the amendment commencement table (JSON) searched by title; as-made XML for assent.
- ACT: the landing page's notified date and commencement table.
- WA: the Act's page (assent date) and its "History of this Act" table (commencement text).
- NT: the as-assented page (assent, commencement, gazette date), when the record links it.
- Victoria: in-force version dates only; assent and commencement are only in documents the
  site asks robots not to fetch.
- NSW and SA: not read; both registers block automated requests (Cloudflare challenge).

Every adapter needs a document identifier, taken from the record's register_url or
register_id. Without one it says so rather than searching by guesswork.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import time
import xml.etree.ElementTree as ET
import zipfile
from urllib.parse import quote

import httpx

from ..register.schema import Instrument
from .base import RegisterCommencement, RegisterDates, Unsupported, Version
from .cache import JsonCache
from .http import Fetcher
from .text import docx_tables, parse_date


def _src(instrument: Instrument) -> str:
    return " ".join(filter(None, [str(instrument.register_url or ""), instrument.register_id or ""]))


def _norm_title(s: str) -> str:
    return " ".join(s.replace(" ", " ").replace("—", "-").replace("–", "-").lower().split())


def _result(jurisdiction: str, instrument: Instrument, url: str | None, method: str = "html", **kw) -> RegisterDates:
    kw.setdefault("notes", ())
    return RegisterDates(
        jurisdiction=jurisdiction,
        title=kw.pop("title", instrument.title),
        register_id=kw.pop("register_id", instrument.register_id),
        url=url,
        method=method,
        retrieved_at=dt.datetime.now(dt.UTC),
        **kw,
    )


class _Base:
    jurisdiction = ""

    def __init__(self, cache: JsonCache | None = None, sleep=time.sleep):
        self.cache = cache
        self.sleep = sleep

    def fetcher(self, client: httpx.Client) -> Fetcher:
        return Fetcher(client, self.cache, sleep=self.sleep)

    def missing_id(self, instrument: Instrument, example: str) -> RegisterDates:
        return _result(
            self.jurisdiction,
            instrument,
            None,
            method="none",
            notes=(
                f"no {self.jurisdiction} register document identifier (e.g. {example}) in the record's "
                "register_url or register_id",
            ),
        )


# --- Queensland --------------------------------------------------------------------------------


class Queensland(_Base):
    jurisdiction = "QLD"
    BASE = "https://www.legislation.qld.gov.au"
    DOC = re.compile(r"\b((?:act|sl)-\d{4}-[0-9a-z]+)\b", re.I)

    def lookup(self, instrument: Instrument, client: httpx.Client) -> RegisterDates:
        m = self.DOC.search(_src(instrument))
        if not m:
            return self.missing_id(instrument, "act-2016-004")
        doc = m.group(1).lower()
        fetch = self.fetcher(client)
        notes: list[str] = []
        asmade = fetch.text(f"{self.BASE}/view/xml/asmade/{doc}")
        root = re.search(r"<(?:act|sl|subordleg)\b([^>]*)>", asmade)
        attrs = dict(re.findall(r'([\w.]+)="([^"]*)"', root.group(1))) if root else {}
        made = parse_date(attrs.get("assent.date") or attrs.get("publication.date"))
        commencements: list[RegisterCommencement] = []
        versions: list[Version] = []
        if instrument.role == "principal" and doc.startswith("act-"):
            commencements, versions = self._history(fetch.text(f"{self.BASE}/view/xml/inforce/current/{doc}/lh"))
        else:
            notes.append(
                "an amending Act's commencement is recorded in the principal Act's legislative history; "
                "list the principal Act (role 'principal') in the record to check it"
            )
        return _result(
            "QLD",
            instrument,
            f"{self.BASE}/view/html/asmade/{doc}",
            method="api",
            title=attrs.get("title") or instrument.title,
            register_id=doc,
            assent_or_made=made,
            commencements=tuple(commencements),
            versions=tuple(versions),
            notes=tuple(notes),
        )

    @staticmethod
    def _history(xml_text: str) -> tuple[list[RegisterCommencement], list[Version]]:
        root = ET.fromstring(xml_text.encode("utf-8"))
        title = root.get("title") or root.get("id") or "principal Act"
        out = []
        for entry in root.iter("actentry"):
            doc_id = entry.get("doc.id")
            for c in entry.iter("commencement"):
                if d := parse_date(c.get("commence.date")):
                    out.append(
                        RegisterCommencement(d, f"{doc_id} in {title}", "Queensland legislative history: commencement")
                    )
        versions = []
        for r in root.iter("reprintentry"):
            if d := parse_date(r.get("effective.date")):
                refs = tuple(f"{x.get('target.doc.id')}: {(x.text or '').strip()}" for x in r.findall("legref"))
                versions.append(Version(d, None, f"reprint effective {d.isoformat()}", refs))
                for x in r.findall("legref"):
                    out.append(
                        RegisterCommencement(
                            d,
                            f"{x.get('target.doc.id')} in {title}",
                            "Queensland legislative history: reprint effective date",
                        )
                    )
        return out, versions


# --- Tasmania ----------------------------------------------------------------------------------


class Tasmania(_Base):
    jurisdiction = "TAS"
    BASE = "https://www.legislation.tas.gov.au"
    DOC = re.compile(r"\b((?:act|sr)-\d{4}-\d+)\b", re.I)

    def table_url(self, title: str) -> str:
        expr = f'"Commencement.Source Title"=?"{title}"? AND "Commencement.Commence Date" < "99990101000000"'
        return f"{self.BASE}/projectdata?ds=EnAct-AmendmentTableDataSource&expression={quote(expr)}&start=1&count=50"

    @staticmethod
    def _value(row: dict, key: str) -> str | None:
        v = row.get(key)
        v = v.get("__value__") if isinstance(v, dict) else v
        return v if isinstance(v, str) else None

    def lookup(self, instrument: Instrument, client: httpx.Client) -> RegisterDates:
        fetch = self.fetcher(client)
        rows = fetch.json(self.table_url(instrument.title)).get("data", [])
        if isinstance(rows, dict):  # a single matching row comes back as an object, not a list
            rows = [rows]
        own = [
            r
            for r in rows
            if _norm_title(self._value(r, "Commencement.Source Title") or "") == _norm_title(instrument.title)
        ]
        made = next(
            (
                parse_date(self._value(r, "Commencement.Assent Or Gazette Date"))
                for r in own
                if self._value(r, "Commencement.Assent Or Gazette Date")
            ),
            None,
        )
        commencements = sorted(
            {
                RegisterCommencement(
                    d,
                    f"{instrument.title} ({self._value(r, 'Commencement.Target Type') or 'provisions'})",
                    "Tasmanian amendment commencement table",
                )
                for r in own
                if (d := parse_date(self._value(r, "Commencement.Commence Date")))
            },
            key=lambda c: c.date,
        )
        notes: list[str] = []
        url = None
        if m := self.DOC.search(_src(instrument)):
            url = f"{self.BASE}/view/html/asmade/{m.group(1).lower()}"
            if made is None:
                xml = fetch.text(f"{self.BASE}/view/xml/asmade/{m.group(1).lower()}")
                if a := re.search(r'ASSENT\.DATE="([^"]+)"', xml):
                    made = parse_date(a.group(1))
        if not own:
            notes.append("title not found in the Tasmanian amendment commencement table")
        if len(commencements) > 1:
            notes.append("several commencement dates: later ones may be expiries of transitional provisions")
        return _result(
            "TAS",
            instrument,
            url,
            method="api",
            assent_or_made=made,
            commencements=tuple(commencements),
            notes=tuple(notes),
        )


# --- ACT ---------------------------------------------------------------------------------------


class AustralianCapitalTerritory(_Base):
    jurisdiction = "ACT"
    BASE = "https://legislation.act.gov.au"
    DOC = re.compile(r"(?:/(a|sl|di|ni)/(\d{4}-\d+))|\b(A|SL|DI|NI)(\d{4}-\d+)\b")

    def lookup(self, instrument: Instrument, client: httpx.Client) -> RegisterDates:
        m = self.DOC.search(_src(instrument))
        if not m:
            return self.missing_id(instrument, "A2015-47")
        kind, num = (m.group(1), m.group(2)) if m.group(1) else (m.group(3).lower(), m.group(4))
        url = f"{self.BASE}/{kind}/{num}/"
        page = self.fetcher(client).text(url)
        notified = re.search(r"Notified:\s*([^<(]+)", page)
        commencements = []
        table = re.search(r'<table[^>]*id="commencement-table".*?</table>', page, re.S)
        for row in re.findall(r"<tr>(.*?)</tr>", table.group(0), re.S) if table else []:
            cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
            if len(cells) >= 2 and (d := parse_date(cells[1])):
                commencements.append(
                    RegisterCommencement(
                        d, cells[0], f"ACT commencement table ({cells[2] if len(cells) > 2 else ''})".strip()
                    )
                )
        repeal = re.search(r'id="auto-repeal-table".*?<td[^>]*>[^<]*</td>\s*<td[^>]*>([^<]+)</td>', page, re.S)
        return _result(
            "ACT",
            instrument,
            url,
            register_id=f"{kind.upper()}{num}",
            assent_or_made=parse_date(notified.group(1)) if notified else None,
            commencements=tuple(commencements),
            repealed=parse_date(repeal.group(1)) if repeal else None,
            notes=() if commencements else ("no commencement table found on the page",),
        )


# --- Western Australia -------------------------------------------------------------------------


class WesternAustralia(_Base):
    jurisdiction = "WA"
    BASE = "https://www.legislation.wa.gov.au/legislation/statutes.nsf"
    DOC = re.compile(r"\blaw_([as]\d+)\b")

    def lookup(self, instrument: Instrument, client: httpx.Client) -> RegisterDates:
        m = self.DOC.search(_src(instrument))
        if not m:
            return self.missing_id(instrument, "law_a147199 (the Act's page on the WA register)")
        law = m.group(1)
        fetch = self.fetcher(client)
        url = f"{self.BASE}/law_{law}.html"
        page = fetch.text(url)
        label = re.search(r"(?:Assent|Gazettal|Publication) Date:</th>\s*<td>([^<]+)</td>", page)
        notes: list[str] = []
        commencements: list[RegisterCommencement] = []
        try:
            history = docx_tables(fetch.content(f"{self.BASE}/RedirectURL?OpenAgent&query=law_{law}_table1.docx"))
        except (httpx.HTTPStatusError, zipfile.BadZipFile, KeyError):
            history = []
            notes.append("'History of this Act' table unavailable or not a Word document")
        want = _norm_title(instrument.title)
        row_assent = None
        for rows in history:
            for r in rows:
                if len(r) >= 4 and _norm_title(r[0]) == want:
                    commencements += self.parse_commencement(r[3], instrument.title)
                    row_assent = row_assent or parse_date(r[2])
        if history and not commencements:
            notes.append("no commencement row for this title in 'History of this Act', or its text did not parse")
        return _result(
            "WA",
            instrument,
            url,
            # An amending Act listed in its principal Act's history: take its own assent from that row.
            assent_or_made=row_assent or (parse_date(label.group(1)) if label else None),
            register_id=f"law_{law}",
            commencements=tuple(commencements),
            notes=tuple(notes),
        )

    @staticmethod
    def parse_commencement(text: str, title: str) -> list[RegisterCommencement]:
        """'Pt. 1: 30 Oct 2018 (see s. 2(a)); Pt. 2 ...: 28 Feb 2019 (see ... Gazette ...)' -> one per segment."""
        out = []
        for seg in text.replace(" ", " ").split(";"):
            head, sep, tail = seg.rpartition(":")
            body = tail if sep else seg
            body = body.split("(")[0]  # drop "(see s. 2(b) and Gazette ...)"
            if d := parse_date(body):
                out.append(
                    RegisterCommencement(
                        d, (head.strip() or "whole") + f" ({title})", "WA 'History of this Act' commencement"
                    )
                )
        return out


# --- Northern Territory ------------------------------------------------------------------------


class NorthernTerritory(_Base):
    jurisdiction = "NT"

    def lookup(self, instrument: Instrument, client: httpx.Client) -> RegisterDates:
        url = str(instrument.register_url or "")
        if "legislation.nt.gov.au" not in url or "format=assented" not in url:
            return _result(
                "NT",
                instrument,
                url or None,
                method="none",
                notes=(
                    "NT: link the as-assented page (…link.aspx?_id=…&format=assented) to read assent and commencement",
                ),
            )
        page = self.fetcher(client).text(url)
        fields = {
            k.strip().rstrip(":"): v.strip()
            for k, v in re.findall(r"<label>([^<]+)</label>\s*<span>([^<]*)</span>", page)
        }
        com = parse_date(fields.get("Commencement"))
        notes = (f"remarks: {fields['Remarks']}",) if fields.get("Remarks") else ()
        return _result(
            "NT",
            instrument,
            url,
            assent_or_made=parse_date(fields.get("Assent")),
            commencements=(RegisterCommencement(com, instrument.title, "NT as-assented page"),) if com else (),
            notes=notes,
        )


# --- Victoria ----------------------------------------------------------------------------------


class Victoria(_Base):
    jurisdiction = "VIC"
    BASE = "https://www.legislation.vic.gov.au"
    DOC = re.compile(r"/(?:as-made|in-force)/(acts|statutory-rules)/([a-z0-9-]+)")

    def lookup(self, instrument: Instrument, client: httpx.Client) -> RegisterDates:
        m = self.DOC.search(_src(instrument))
        if not m:
            return self.missing_id(instrument, "…/as-made/acts/<title-slug>")
        url = f"{self.BASE}/in-force/{m.group(1)}/{m.group(2)}"
        try:
            page = self.fetcher(client).text(url)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 404:
                raise
            return _result(
                "VIC",
                instrument,
                url,
                method="none",
                notes=(
                    "no in-force page (an amending Act is not kept in force on its own); "
                    "assent and commencement are not machine-readable on the Victorian register",
                ),
            )
        notes = [
            "Victoria: assent and commencement are only in documents the site asks robots not to fetch; "
            "the first in-force version date is used instead"
        ]
        versions = self.versions(page)
        if not versions:
            notes.append("no in-force versions found (an amending Act is not kept in force on its own)")
        first = (
            (RegisterCommencement(versions[0].start, "first in-force version", "Victorian in-force version dates"),)
            if versions
            else ()
        )
        return _result("VIC", instrument, url, commencements=first, versions=tuple(versions), notes=tuple(notes))

    @staticmethod
    def versions(page: str) -> list[Version]:
        m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
        if not m:
            return []
        arr = json.loads(m.group(1))

        def val(i):
            return arr[i] if isinstance(i, int) and 0 <= i < len(arr) else i

        out = []
        for x in arr:
            if isinstance(x, dict) and "date" in x and "version" in x and (d := parse_date(str(val(x["date"])))):
                out.append(Version(d, None, f"version {val(x['version'])} ({val(x.get('status'))})"))
        return sorted(set(out), key=lambda v: v.start)


BLOCKED = "register blocks automated requests (Cloudflare challenge); relying on the record's sourced dates"


def state_adapters(cache: JsonCache | None = None, sleep=time.sleep) -> dict[str, object]:
    return {
        "QLD": Queensland(cache, sleep),
        "TAS": Tasmania(cache, sleep),
        "ACT": AustralianCapitalTerritory(cache, sleep),
        "WA": WesternAustralia(cache, sleep),
        "NT": NorthernTerritory(cache, sleep),
        "VIC": Victoria(cache, sleep),
        "NSW": Unsupported("NSW", f"NSW {BLOCKED}"),
        "SA": Unsupported("SA", f"SA {BLOCKED}"),
    }
