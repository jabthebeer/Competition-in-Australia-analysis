"""Who is responsible for each item (the bodies registry) and what happened to its law since (history, timeline).

Records and bodies built here are ILLUSTRATIVE test fixtures, except where a test loads the committed register.
"""

from __future__ import annotations

import datetime as dt
import json
import re

import pytest
from pydantic import ValidationError

from alicia.menu import growth
from alicia.menu.explorer import build_payload
from alicia.register.bodies import check_records, department_of, load_bodies
from alicia.register.catalogue import load_records
from alicia.register.schema import ChangeRecord
from alicia.register.timeline import changed_by_index, changes_list, timeline

SRC = "https://example.org/illustrative-source"


def illustrative(**over) -> dict:
    rec = {
        "id": "nsw-illustrative-2016",
        "title": "ILLUSTRATIVE change (test fixture)",
        "jurisdiction": "NSW",
        "summary": "Illustrative record used only in tests.",
        "instruments": [{"title": "Illustrative Act 2016", "role": "principal"}],
        "dates": {
            "announced": {"date": "2015-06-01", "source": SRC},
            "assent_or_made": {"date": "2016-03-01", "source": SRC},
            "commenced": [{"date": "2016-11-01", "what": "Whole Act", "source": SRC}],
        },
        "direction": "enhancing",
        "direction_rationale": "Illustrative.",
        "channels": ["barriers"],
        "industries": [{"anzsic": "4623", "name": "Taxi and Other Road Transport", "exposure": "direct"}],
        "verified": {"dates": True},
    }
    rec.update(over)
    return rec


def _page_data(html: str) -> dict:
    return json.loads(re.search(r'<script type="application/json" id="page-data">(.*?)</script>', html, re.S).group(1))


def body(id, type="department", parent=None, jurisdiction="NSW"):
    return {
        "id": id,
        "name": id.upper(),
        "short": id,
        "jurisdiction": jurisdiction,
        "type": type,
        "parent": parent,
        "url": SRC,
        "source": SRC,
    }


def write_bodies(tmp_path, items):
    path = tmp_path / "bodies.json"
    path.write_text(json.dumps(items), encoding="utf-8")
    return path


BODIES = [body("nsw-dept"), body("nsw-regulator", "regulator", "nsw-dept")]


def record(**over) -> ChangeRecord:
    rec = illustrative(responsible=[{"body": "nsw-dept", "role": "administers", "source": SRC}])
    rec.update(over)
    return ChangeRecord.model_validate(rec)


def event(date, kind="amended", record=None):
    return {"date": date, "kind": kind, "what": "Illustrative change.", "source": SRC, "record": record}


# --- Schema ------------------------------------------------------------------------------------------------------


def test_history_must_be_in_date_order():
    with pytest.raises(ValidationError, match="date order"):
        record(history=[event("2020-01-01"), event("2019-01-01")])


def test_a_body_holds_each_role_once():
    twice = [{"body": "nsw-dept", "role": "administers", "source": SRC}] * 2
    with pytest.raises(ValidationError, match="each role once"):
        record(responsible=twice)
    both = [
        {"body": "nsw-dept", "role": "administers", "source": SRC},
        {"body": "nsw-dept", "role": "regulates", "source": SRC},
    ]
    assert len(record(responsible=both).responsible) == 2


def test_an_item_ends_with_its_last_repeal_or_replacement_to_date():
    assert record().ended is None
    assert record(history=[event("2018-01-01", "eased")]).ended is None
    r = record(history=[event("2018-01-01", "eased"), event("2021-03-08", "repealed")])
    assert r.ended.date == dt.date(2021, 3, 8) and r.ended.kind == "repealed"
    future = (dt.date.today() + dt.timedelta(days=30)).isoformat()
    assert record(history=[event(future, "repealed")]).ended is None


# --- Bodies registry ---------------------------------------------------------------------------------------------


def test_the_registry_checks_parents(tmp_path):
    bodies, problems = load_bodies(write_bodies(tmp_path, BODIES))
    assert problems == [] and department_of(bodies["nsw-regulator"], bodies).id == "nsw-dept"
    bad = [
        *BODIES,
        body("nsw-dept"),
        body("nsw-orphan", "agency", "nsw-none"),
        body("nsw-sub", "agency", "nsw-regulator"),
        body("nsw-dept2", parent="nsw-dept"),
    ]
    problems = load_bodies(write_bodies(tmp_path, bad))[1]
    assert any("duplicate id 'nsw-dept'" in p for p in problems)
    assert any("nsw-orphan: unknown parent" in p for p in problems)
    assert any("nsw-sub: parent 'nsw-regulator' is not a department" in p for p in problems)
    assert any("nsw-dept2: a department has no parent" in p for p in problems)


def test_records_name_known_bodies_and_someone_who_administers_them(tmp_path):
    bodies = load_bodies(write_bodies(tmp_path, BODIES))[0]
    assert check_records([record()], bodies) == []
    unknown = record(responsible=[{"body": "nsw-nobody", "role": "administers", "source": SRC}])
    assert "unknown body 'nsw-nobody'" in check_records([unknown], bodies)[0]
    regulator_only = record(responsible=[{"body": "nsw-regulator", "role": "regulates", "source": SRC}])
    assert "needs a body that administers it" in check_records([regulator_only], bodies)[0]


def test_the_committed_register_tags_every_item():
    bodies, problems = load_bodies()
    records = load_records().records
    assert problems == [] and check_records(records, bodies) == []
    ids = {r.id for r in records}
    assert all(h.record in ids for r in records for h in r.history if h.record)
    # The owner's example: DCCEEW administers the EPBC Act.
    epbc = next(r for r in records if r.id == "cth-epbc-reform-2025")
    assert any(x.body == "cth-dcceew" and x.role == "administers" for x in epbc.responsible)
    # And the lockout laws have ended.
    lockout = next(r for r in records if r.id == "nsw-lockout-2014")
    assert lockout.ended and lockout.ended.record == "nsw-lockout-repeal-kings-cross-2021"


# --- Timeline and menu -------------------------------------------------------------------------------------------


def test_the_timeline_merges_own_dates_and_later_changes_in_order():
    later = record(id="nsw-illustrative-repeal-2021", title="Repeal", history=[])
    r = record(history=[event("2019-05-01", "eased"), event("2021-03-08", "repealed", later.id)])
    t = timeline(r, {later.id: later.title}, today=dt.date(2020, 1, 1))
    assert [e["kind"] for e in t] == ["announced", "made", "commenced", "eased", "repealed"]
    assert [e["own"] for e in t] == [True, True, True, False, False]
    assert t[-1]["recordTitle"] == "Repeal" and t[-1]["upcoming"] and not t[-2]["upcoming"]
    changed = changed_by_index([r, later])
    assert changes_list(changed.get(later.id, [])) == [
        {"record": r.id, "title": r.title, "kind": "repealed", "label": "Repealed"}
    ]
    # The record that made the change lists what it changed only if its own history says so.
    assert r.id not in changed


def test_the_menu_payload_carries_bodies_ended_and_timeline(tmp_path):
    bodies = load_bodies(write_bodies(tmp_path, BODIES))[0]
    r = record(
        responsible=[
            {"body": "nsw-regulator", "role": "regulates", "source": SRC},
            {"body": "nsw-dept", "role": "administers", "source": SRC},
        ],
        history=[event("2021-03-08", "repealed")],
    )
    data = build_payload([r], bodies=bodies)
    p = data["records"][0]
    assert (
        set(data["bodies"]) == {"nsw-dept", "nsw-regulator"} and data["bodies"]["nsw-regulator"]["parent"] == "nsw-dept"
    )
    assert p["ended"]["kind"] == "repealed" and p["timeline"][-1]["kind"] == "repealed"
    assert [x["body"] for x in p["responsible"]] == ["nsw-regulator", "nsw-dept"]
    # The timeline carries the dates and the history, so the raw fields are left out.
    assert "dates" not in p and "history" not in p
    html = growth.render("explorer.html", data, "index.html", standalone=True)
    assert _page_data(html)["records"][0]["ended"]["date"] == "2021-03-08"
    for hook in ('id="f-body"', 'value="ended"', "Who is responsible", '"Timeline"', "body="):
        assert hook in html
