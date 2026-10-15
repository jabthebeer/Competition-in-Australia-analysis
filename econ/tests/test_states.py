"""State and territory adapters, date-text parsing and register routing (offline).

Fixtures in tests/fixtures/states are real register responses saved on 14-15 October 2026
(the Queensland legislative history is trimmed). Instruments built here point at them.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import zipfile
from pathlib import Path

import httpx
import pytest

from regimpact.legislation.adapters import register_for
from regimpact.legislation.base import make_client
from regimpact.legislation.states import (
    AustralianCapitalTerritory,
    NorthernTerritory,
    Queensland,
    Tasmania,
    Victoria,
    WesternAustralia,
    state_adapters,
)
from regimpact.legislation.text import commencement_in_prose, commencement_table, docx_tables, find_dates, parse_date
from regimpact.register.schema import Instrument

FX = Path(__file__).parent / "fixtures" / "states"
D = dt.date
TAS = json.loads((FX / "tas_table_mutual_recognition_amendment_2021.json").read_text("utf-8"))

ROUTES = {
    "https://www.legislation.qld.gov.au/view/xml/asmade/act-2016-004": "qld_02_act-2016-004_aspassed.xml",
    "https://www.legislation.tas.gov.au/view/xml/asmade/act-2021-020": "tas_02_act-2021-020_asmade.xml",
    "https://legislation.act.gov.au/a/2015-47/": "act_01_A2015-47_TaxiIndustryInnovation_landing.html",
    "https://www.legislation.wa.gov.au/legislation/statutes.nsf/law_a147199.html": (
        "wa_01_law_a147199_TransportRoadPassengerServicesAct2018.html"
    ),
    "https://www.legislation.wa.gov.au/legislation/statutes.nsf/RedirectURL?OpenAgent&query=law_a147199_table1.docx": (
        "wa_02_law_a147199_table1_HistoryOfThisAct.docx"
    ),
    "https://legislation.nt.gov.au/~/link.aspx?_id=A1F4EC33A0E74C729760960833DAD93D&_z=z&format=assented": (
        "nt_01_CPRT_Legislation_Amendment_Licensing_Act2026_assented.html"
    ),
    "https://www.legislation.vic.gov.au/in-force/acts/commercial-passenger-vehicle-industry-act-2017": (
        "vic_01_CPVI_Act2017_inforce_version_history.html"
    ),
}


def replay(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if url == TAS["url"]:
        return httpx.Response(200, json=TAS["body"])
    name = ROUTES.get(url)
    if name is None:
        return httpx.Response(404, text=f"no fixture for {url}")
    return httpx.Response(200, content=(FX / name).read_bytes())


@pytest.fixture
def client():
    with make_client(transport=httpx.MockTransport(replay)) as c:
        yield c


def no_sleep(seconds: float) -> None:
    pass


def inst(title, url=None, rid=None, role="amending"):
    return Instrument(title=title, register_url=url, register_id=rid, role=role)


# --- Adapters against real pages -----------------------------------------------------------------


def test_queensland_assent_from_as_made_xml(client):
    r = Queensland(sleep=no_sleep).lookup(
        inst(
            "Tackling Alcohol-Fuelled Violence Legislation Amendment Act 2016",
            "https://www.legislation.qld.gov.au/view/html/asmade/act-2016-004",
        ),
        client,
    )
    assert r.register_id == "act-2016-004"
    assert r.assent_or_made == D(2016, 3, 4)
    assert any("principal Act's legislative history" in n for n in r.notes)


def test_queensland_history_gives_each_amending_acts_dates():
    text = (FX / "qld_04_LiquorAct1992_legislative_history_TRIMMED.xml").read_text("utf-8")
    commencements, versions = Queensland._history(text)
    tafv = {c.date for c in commencements if c.what.startswith("act-2016-004")}
    assert {D(2016, 3, 4), D(2016, 7, 1), D(2016, 9, 1), D(2017, 2, 1)} <= tafv
    assert D(2016, 7, 1) in {v.start for v in versions}


def test_tasmania_commencement_table(client):
    r = Tasmania(sleep=no_sleep).lookup(
        inst(
            "Mutual Recognition (Tasmania) Amendment Act 2021",
            "https://www.legislation.tas.gov.au/view/whole/html/asmade/act-2021-020",
        ),
        client,
    )
    assert r.assent_or_made == D(2021, 11, 12)
    assert D(2021, 12, 22) in {c.date for c in r.commencements}
    # The proclamation row is a different title and is not counted as this Act's commencement.
    assert all("Proclamation" not in c.what for c in r.commencements)


def test_act_commencement_table_and_notified_date(client):
    r = AustralianCapitalTerritory(sleep=no_sleep).lookup(
        inst(
            "Road Transport (Public Passenger Services) (Taxi Industry Innovation) Amendment Act 2015",
            "https://legislation.act.gov.au/DownloadFile/a/2015-47/20160520-62425/PDF/2015-47.PDF",
            "A2015-47",
        ),
        client,
    )
    assert r.register_id == "A2015-47"
    assert r.assent_or_made == D(2015, 11, 24)
    assert [(c.what, c.date) for c in r.commencements] == [
        ("s 1, s 2", D(2015, 11, 24)),
        ("s 3", D(2016, 5, 20)),
        ("s 30", D(2016, 5, 20)),
        ("remainder", D(2016, 8, 1)),
    ]


def test_western_australia_assent_and_history(client):
    r = WesternAustralia(sleep=no_sleep).lookup(
        inst(
            "Transport (Road Passenger Services) Act 2018",
            "https://www.legislation.wa.gov.au/legislation/statutes.nsf/law_a147199.html",
            role="principal",
        ),
        client,
    )
    assert r.assent_or_made == D(2018, 10, 30)
    dates = sorted({c.date for c in r.commencements})
    assert dates[0] == D(2018, 10, 30)
    assert {D(2019, 2, 28), D(2019, 4, 1), D(2019, 7, 1)} <= set(dates)
    # Gazette dates in "(see ... Gazette 26 Feb 2019 ...)" are not commencements.
    assert D(2019, 2, 26) not in dates


def test_northern_territory_assented_page(client):
    r = NorthernTerritory(sleep=no_sleep).lookup(
        inst(
            "Commercial Passenger (Road) Transport Legislation Amendment (Licensing) Act 2026",
            "https://legislation.nt.gov.au/~/link.aspx?_id=A1F4EC33A0E74C729760960833DAD93D&_z=z&format=assented",
        ),
        client,
    )
    assert r.assent_or_made == D(2026, 3, 31)
    assert [c.date for c in r.commencements] == [D(2026, 7, 1)]


def test_northern_territory_without_assented_link_says_so(client):
    r = NorthernTerritory(sleep=no_sleep).lookup(inst("Some Act", "https://example.org/x.pdf"), client)
    assert r.method == "none" and "as-assented page" in r.notes[0]


def test_victoria_version_dates_only(client):
    r = Victoria(sleep=no_sleep).lookup(
        inst(
            "Commercial Passenger Vehicle Industry Act 2017",
            "https://www.legislation.vic.gov.au/as-made/acts/commercial-passenger-vehicle-industry-act-2017",
            role="principal",
        ),
        client,
    )
    assert len(r.versions) == 25
    assert r.commencements[0].date == D(2017, 8, 23)
    assert r.assent_or_made is None
    assert any("robots" in n for n in r.notes)


def test_missing_identifier_is_reported(client):
    r = Queensland(sleep=no_sleep).lookup(inst("Some Act", None), client)
    assert r.method == "none" and "act-2016-004" in r.notes[0]


def test_nsw_and_sa_are_marked_blocked(client):
    adapters = state_adapters(sleep=no_sleep)
    for j in ("NSW", "SA"):
        r = adapters[j].lookup(inst("Some Act"), client)
        assert "Cloudflare" in r.notes[0]


# --- Routing -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "rid", "record", "expected"),
    [
        ("https://www.legislation.gov.au/C2021A00050/asmade", None, "NSW", "CTH"),
        (None, "C2021A00050", "VIC", "CTH"),
        ("https://legislation.act.gov.au/a/2015-47/", None, "ACT", "ACT"),
        ("https://www.parliament.nsw.gov.au/bills/x", "2021 No 17", "NSW", "NSW"),
        (None, None, "WA", "WA"),
    ],
)
def test_register_routing(url, rid, record, expected):
    assert register_for(inst("x", url, rid), record) == expected


# --- Text helpers --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("9 November 2022", D(2022, 11, 9)),
        ("30 Oct 2018", D(2018, 10, 30)),
        ("31/03/2026", D(2026, 3, 31)),
        ("Date of commencement, 1.7.2016, sec 2", D(2016, 7, 1)),
        ("2016-03-04T00:00:00+10:00", D(2016, 3, 4)),
        ("1 Sept 2019", D(2019, 9, 1)),
        ("31 February 2020", None),
        ("no date here", None),
    ],
)
def test_parse_date(text, expected):
    assert parse_date(text) == expected


def test_find_dates_keeps_order():
    assert find_dates("from 1 July 2021 until 30/06/2022") == [D(2021, 7, 1), D(2022, 6, 30)]


def _docx(body_xml: str) -> bytes:
    w = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    doc = f'<?xml version="1.0"?><w:document {w}><w:body>{body_xml}</w:body></w:document>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", doc)
    return buf.getvalue()


def _row(*cells: str) -> str:
    return "<w:tr>" + "".join(f"<w:tc><w:p><w:r><w:t>{c}</w:t></w:r></w:p></w:tc>" for c in cells) + "</w:tr>"


def test_commonwealth_s2_table_from_a_word_document():
    # ILLUSTRATIVE document shaped like a Commonwealth s 2 commencement table.
    table = (
        "<w:tbl>"
        + _row("Commencement information")
        + _row("Column 1", "Column 2", "Column 3")
        + _row("Provisions", "Commencement", "Date/Details")
        + _row("1.  Sections 1 to 3", "The day this Act receives the Royal Assent.", "9 November 2022")
        + _row("2.  Schedule 2", "The day after the end of 12 months.", "9 November 2023")
        + "</w:tbl>"
    )
    rows = commencement_table(docx_tables(_docx(table)))
    assert rows == [
        ("Sections 1 to 3", "The day this Act receives the Royal Assent.", "9 November 2022"),
        ("Schedule 2", "The day after the end of 12 months.", "9 November 2023"),
    ]


def test_commencement_in_prose():
    assert commencement_in_prose("This instrument commences on 1 April 2017.") == [D(2017, 4, 1)]
    assert commencement_in_prose("commences on a day to be fixed by Proclamation") == []


def test_wa_commencement_segments_ignore_gazette_dates():
    text = "Pt. 1: 30 Oct 2018 (see s. 2(a)); Pt. 2: 28 Feb 2019 (see s. 2(b) and Gazette 26 Feb 2019 p. 449)"
    got = WesternAustralia.parse_commencement(text, "Example Act")
    assert [c.date for c in got] == [D(2018, 10, 30), D(2019, 2, 28)]
