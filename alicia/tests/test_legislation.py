"""Federal Register adapter and date reconciliation, replayed offline from recorded responses.

The fixtures are real Federal Register API responses (recorded by
scripts/record_frl_fixtures.py, long version lists trimmed). The records built here are
ILLUSTRATIVE test fixtures.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import httpx
import pytest

from alicia.legislation.base import RegisterCommencement, RegisterDates, Unsupported, Version, make_client
from alicia.legislation.cache import JsonCache
from alicia.legislation.frl import FederalRegister
from alicia.legislation.gather import gather, reconcile
from alicia.register.schema import ChangeRecord, Instrument

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "frl" / "responses.json").read_text("utf-8"))
SRC = "https://example.org/illustrative-source"
TODAY = dt.date(2026, 10, 15)


def no_sleep(seconds: float) -> None:
    pass


def replay(request: httpx.Request) -> httpx.Response:
    body = FIXTURES["responses"].get(str(request.url))
    if body is None:
        return httpx.Response(404, json={"error": f"no fixture for {request.url}"})
    return httpx.Response(200, json=body)


@pytest.fixture
def client():
    with make_client(transport=httpx.MockTransport(replay)) as c:
        yield c


def test_amending_act_commencement_comes_from_principal_compilation(client):
    r = FederalRegister(today=TODAY, sleep=no_sleep).lookup(
        Instrument(title="Mutual Recognition Amendment Act 2021", role="amending"), client
    )
    assert r.register_id == "C2021A00050"
    assert r.assent_or_made == dt.date(2021, 6, 24)
    assert [c.date for c in r.commencements] == [dt.date(2021, 7, 1)]
    assert "Mutual Recognition Act 1992" in r.commencements[0].what
    assert "compilation 7" in r.commencements[0].basis


def test_staged_commencement_is_reported_per_schedule(client):
    r = FederalRegister(today=TODAY, sleep=no_sleep).lookup(
        Instrument(
            title="Treasury Laws Amendment (More Competition, Better Prices) Act 2022",
            register_id="C2022A00054",
            role="amending",
        ),
        client,
    )
    dates = sorted({c.date for c in r.commencements})
    assert dates == [dt.date(2022, 11, 10), dt.date(2023, 11, 9)]
    sch2 = [c for c in r.commencements if c.date == dt.date(2023, 11, 9)]
    assert {c.what.split(" amending ")[1] for c in sch2} == {
        "Competition and Consumer Act 2010",
        "Australian Securities and Investments Commission Act 2001",
    }


def test_principal_instrument_versions(client):
    r = FederalRegister(today=TODAY, sleep=no_sleep).lookup(
        Instrument(
            title="Competition and Consumer (Industry Codes—Food and Grocery) Regulations 2024",
            role="regulation",
        ),
        client,
    )
    assert r.register_id == "F2024L01651"
    assert r.assent_or_made == dt.date(2024, 12, 12)
    assert r.registered == dt.date(2024, 12, 16)
    # The code's obligations applied from 1 April 2025: a version boundary, not the first version.
    assert {dt.date(2024, 12, 16), dt.date(2025, 4, 1)} <= {v.start for v in r.versions}
    # No as-made Word document in the fixtures: reported, not guessed.
    assert any("as-made Word document unavailable" in n for n in r.notes)


def test_unknown_title_is_reported_not_guessed():
    def empty(request):
        return httpx.Response(200, json={"value": []})

    with make_client(transport=httpx.MockTransport(empty)) as c:
        r = FederalRegister(sleep=no_sleep).lookup(Instrument(title="No Such Act 2099", role="principal"), c)
    assert r.register_id is None
    assert r.notes == ("no Federal Register title named 'No Such Act 2099'",)


def test_id_is_taken_from_register_url(client):
    reg = FederalRegister(sleep=no_sleep)
    inst = Instrument(title="x", role="amending", register_url="https://www.legislation.gov.au/C2021A00050/asmade/text")
    assert reg.resolve_id(inst, client) == ("C2021A00050", [])


def test_cache_round_trip(tmp_path):
    cache = JsonCache(tmp_path)
    assert cache.get("https://x/y") is None
    cache.put("https://x/y", {"a": 1})
    assert cache.get("https://x/y") == {"a": 1}
    assert JsonCache(tmp_path, max_age=dt.timedelta(seconds=-1)).get("https://x/y") is None


# --- Reconciliation (pure) -------------------------------------------------------------------


def record(commenced, assent="2021-06-24", verified=True) -> ChangeRecord:
    return ChangeRecord.model_validate(
        {
            "id": "cth-illustrative-2021",
            "family": None,
            "title": "ILLUSTRATIVE (test fixture)",
            "jurisdiction": "CTH",
            "summary": "Illustrative.",
            "instruments": [
                {
                    "title": "Mutual Recognition Amendment Act 2021",
                    "register_url": None,
                    "register_id": None,
                    "role": "amending",
                    "provisions": None,
                }
            ],
            "dates": {
                "announced": {"date": "2020-12-11", "source": SRC},
                "assent_or_made": {"date": assent, "source": SRC},
                "commenced": [{"date": d, "what": "x", "source": SRC} for d in commenced],
            },
            "direction": "enhancing",
            "direction_rationale": "Illustrative.",
            "direction_sources": [],
            "channels": ["barriers"],
            "industries": [{"anzsic": "3232", "name": "Electrical Services", "exposure": "direct"}],
            "comparison": "Illustrative.",
            "confounders": [],
            "price_series": None,
            "notes": None,
            "verified": {"dates": verified, "notes": None if verified else "secondary source only"},
        }
    )


def reg(
    *commence: str,
    assent: str = "2021-06-24",
    versions: tuple[str, ...] = (),
    jurisdiction: str = "CTH",
    role: str = "amending",
    method: str = "api",
) -> RegisterDates:
    return RegisterDates(
        jurisdiction=jurisdiction,
        role=role,
        title="Mutual Recognition Amendment Act 2021",
        register_id="C2021A00050",
        url=None,
        method=method,
        retrieved_at=dt.datetime(2026, 10, 15, tzinfo=dt.UTC),
        assent_or_made=dt.date.fromisoformat(assent),
        commencements=tuple(RegisterCommencement(dt.date.fromisoformat(d), "x", "y") for d in commence),
        versions=tuple(Version(dt.date.fromisoformat(v), None, "v") for v in versions),
    )


def test_confirmed_when_register_matches():
    res = reconcile(record(["2021-07-01"]), [reg("2021-07-01")])
    assert res.status == "confirmed"
    assert res.issues == ()
    assert res.timing.as_dict()["first_full_fy"] == "2021-22"


def test_confirmed_by_a_later_version_start():
    res = reconcile(
        record(["2025-04-01"], assent="2024-12-12"),
        [reg("2024-12-16", assent="2024-12-12", versions=("2024-12-16", "2025-04-01"))],
    )
    assert res.status == "confirmed"


def test_differs_lists_nearest_register_dates():
    res = reconcile(record(["2021-08-01"]), [reg("2021-07-01")])
    assert res.status == "differs"
    assert any("nearest: 2021-07-01" in i for i in res.issues)


def test_version_starts_alone_never_contradict():
    # A principal law's first version starts at assent; a later commencement is not a contradiction.
    res = reconcile(record(["2012-07-01"]), [reg(versions=("2012-06-21", "2013-04-12"), role="principal")])
    assert res.status == "unconfirmed"


def test_own_jurisdiction_instruments_decide():
    rec = record(["2022-02-01"], assent="2021-12-09").model_copy(update={"jurisdiction": "SA"})
    cth = reg("2021-07-01")  # the Commonwealth Act: context only for a state record
    blocked = reg(jurisdiction="SA", method="none")
    res = reconcile(rec, [cth, blocked])
    assert res.status == "unconfirmed"
    assert not any("assent/making date" in i for i in res.issues)
    assert any("no readable SA register entry" in i for i in res.issues)
    # A record listing only a Commonwealth instrument is judged against it.
    assert reconcile(record(["2021-07-01"]).model_copy(update={"jurisdiction": "ACT"}), [cth]).status == "confirmed"


def test_assent_check_ignores_regulations():
    res = reconcile(record(["2021-07-01"]), [reg("2021-07-01", assent="2021-12-09", role="regulation")])
    assert not any("assent/making date" in i for i in res.issues)


def test_assent_mismatch_and_unverified_are_flagged():
    res = reconcile(record(["2021-07-01"], assent="2021-06-25", verified=False), [reg("2021-07-01")])
    assert any("assent/making date 2021-06-25 not found" in i for i in res.issues)
    assert any("not fully verified: secondary source only" in i for i in res.issues)


def test_unconfirmed_without_register_dates_and_not_commenced():
    assert reconcile(record(["2021-07-01"]), []).status == "unconfirmed"
    res = reconcile(record([]), [reg("2021-07-01")])
    assert res.status == "not-commenced"
    assert res.timing is None


def test_gather_offline_and_with_unsupported_register(client):
    rec = record(["2021-07-01"])
    assert gather(rec, None, lambda i, j: FederalRegister(sleep=no_sleep)).status == "unconfirmed"
    res = gather(rec, client, lambda i, j: Unsupported(j, "not built"))
    assert res.status == "unconfirmed"
    assert any("not built" in i for i in res.issues)


def test_gather_with_federal_register(client):
    res = gather(
        record(["2021-07-01"]),
        client,
        lambda i, j: FederalRegister(today=TODAY, read_commencement_text=False, sleep=no_sleep),
    )
    assert res.status == "confirmed"
    assert res.as_dict()["register"][0]["register_id"] == "C2021A00050"
