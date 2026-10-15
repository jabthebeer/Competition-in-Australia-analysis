"""Register schema, catalogue loading, ANZSIC checks and timing (all offline).

Records built here are ILLUSTRATIVE test fixtures, not real regulatory changes.
"""

from __future__ import annotations

import copy
import datetime as dt
import json

import pytest
from pydantic import ValidationError

from regimpact import anzsic
from regimpact.register.catalogue import families, filter_records, load_records, write_record
from regimpact.register.schema import ChangeRecord, json_schema
from regimpact.timing import financial_year, fy_label, timing

SRC = "https://example.org/illustrative-source"


def illustrative(**over) -> dict:
    rec = {
        "id": "nsw-illustrative-2016",
        "family": "illustrative-family",
        "title": "ILLUSTRATIVE change (test fixture)",
        "jurisdiction": "NSW",
        "summary": "Illustrative record used only in tests.",
        "instruments": [
            {
                "title": "Illustrative Act 2016",
                "register_url": None,
                "register_id": None,
                "role": "principal",
                "provisions": None,
            }
        ],
        "dates": {
            "announced": {"date": "2015-06-01", "source": SRC},
            "assent_or_made": {"date": "2016-03-01", "source": SRC},
            "commenced": [{"date": "2016-11-01", "what": "Whole Act", "source": SRC}],
        },
        "direction": "enhancing",
        "direction_rationale": "Illustrative.",
        "direction_sources": [],
        "channels": ["barriers"],
        "industries": [{"anzsic": "4623", "name": "Taxi and Other Road Transport", "exposure": "direct"}],
        "comparison": "Illustrative.",
        "confounders": [],
        "price_series": None,
        "notes": None,
        "verified": {"dates": True, "notes": None},
    }
    rec.update(over)
    return rec


def test_valid_record_round_trips(tmp_path):
    rec = ChangeRecord.model_validate(illustrative())
    assert rec.review.status == "draft"
    path = write_record(rec, tmp_path)
    loaded = load_records(tmp_path)
    assert loaded.ok, loaded.problems
    assert loaded.records == [rec]
    assert path.name == "nsw-illustrative-2016.json"


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"id": "NSW_Bad"}, "kebab-case"),
        ({"jurisdiction": "XX"}, "jurisdiction"),
        ({"direction": "good"}, "direction"),
        ({"channels": ["barriers", "barriers"]}, "channels must not repeat"),
        ({"channels": ["prices"]}, "channels"),
        ({"industries": [{"anzsic": "46a", "name": "x", "exposure": "direct"}]}, "ANZSIC"),
        ({"instruments": []}, "instruments"),
        ({"extra_field": 1}, "extra"),
    ],
)
def test_invalid_records_are_rejected(change, message):
    with pytest.raises(ValidationError, match=message):
        ChangeRecord.model_validate(illustrative(**change))


def test_a_date_needs_a_source():
    rec = illustrative()
    rec["dates"]["announced"] = {"date": "2015-06-01", "source": None}
    with pytest.raises(ValidationError, match="needs a source"):
        ChangeRecord.model_validate(rec)


def test_reviewed_needs_reviewer():
    with pytest.raises(ValidationError, match="needs 'by' and 'on'"):
        ChangeRecord.model_validate(illustrative(review={"status": "reviewed"}))


def test_effective_commencement_prefers_primary_then_earliest():
    rec = illustrative()
    rec["dates"]["commenced"] = [
        {"date": "2017-01-01", "what": "Main reform", "source": SRC, "primary": True},
        {"date": "2016-11-01", "what": "Definitions", "source": SRC},
    ]
    assert ChangeRecord.model_validate(rec).effective_commencement.date == dt.date(2017, 1, 1)
    for c in rec["dates"]["commenced"]:
        c["primary"] = False
    assert ChangeRecord.model_validate(rec).effective_commencement.date == dt.date(2016, 11, 1)
    rec["dates"]["commenced"] = []
    assert ChangeRecord.model_validate(rec).effective_commencement is None


def test_only_one_primary_commencement():
    rec = illustrative()
    rec["dates"]["commenced"] = [
        {"date": "2017-01-01", "what": "a", "source": SRC, "primary": True},
        {"date": "2016-11-01", "what": "b", "source": SRC, "primary": True},
    ]
    with pytest.raises(ValidationError, match="at most one"):
        ChangeRecord.model_validate(rec)


def test_loader_reports_every_problem(tmp_path):
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    good = illustrative()
    (tmp_path / "wrong-name.json").write_text(json.dumps(good), encoding="utf-8")
    bad = copy.deepcopy(good)
    bad["id"] = "bad-direction"
    bad["direction"] = "good"
    (tmp_path / "bad-direction.json").write_text(json.dumps(bad), encoding="utf-8")
    result = load_records(tmp_path)
    text = "\n".join(result.problems)
    assert "broken.json: not valid JSON" in text
    assert "wrong-name.json: file name must match id" in text
    assert "bad-direction.json: direction" in text


def test_filters_and_families():
    a = ChangeRecord.model_validate(illustrative())
    b = ChangeRecord.model_validate(
        illustrative(
            id="vic-illustrative-2017",
            jurisdiction="VIC",
            direction="weakening",
            dates={"commenced": [{"date": "2017-07-01", "what": "Whole Act", "source": SRC}]},
            industries=[{"anzsic": "4520", "name": "Pubs, Taverns and Bars", "exposure": "direct"}],
        )
    )
    c = ChangeRecord.model_validate(illustrative(id="qld-illustrative", jurisdiction="QLD", dates={"commenced": []}))
    recs = [b, c, a]
    assert [r.id for r in filter_records(recs, jurisdiction="vic")] == [b.id]
    assert [r.id for r in filter_records(recs, direction="weakening")] == [b.id]
    assert {r.id for r in filter_records(recs, industry="46")} == {a.id, c.id}
    assert [r.id for r in filter_records(recs, text="taverns")] == []
    # Families sort by effective date; not-yet-commenced members go last.
    assert [r.id for r in families(recs)["illustrative-family"]] == [a.id, b.id, c.id]


def test_json_schema_exports():
    schema = json_schema()
    assert schema["title"] == "Regulatory change record"
    assert "jurisdiction" in schema["properties"]


def test_anzsic_lookup_and_checks():
    assert anzsic.name("4623") == "Taxi and Other Road Transport"
    assert anzsic.level("462") == "group"
    assert anzsic.division("4623") == "I"
    assert anzsic.division("I") == "I"
    assert anzsic.check("4623", "taxi & other road transport") == []
    assert anzsic.check("4623", "Taxis") == ["4623 is 'Taxi and Other Road Transport', not 'Taxis'"]
    assert anzsic.check("9999") == ["9999 is not an ANZSIC 2006 code"]


@pytest.mark.parametrize(
    ("day", "fy", "first_full", "share", "q", "q_full"),
    [
        ("2021-07-01", "2021-22", "2021-22", 1.0, "2021-Q3", "2021-Q3"),
        ("2021-06-30", "2020-21", "2021-22", 1 / 365, "2021-Q2", "2021-Q3"),
        ("2015-12-18", "2015-16", "2016-17", 196 / 366, "2015-Q4", "2016-Q1"),
        ("2020-10-01", "2020-21", "2021-22", 273 / 365, "2020-Q4", "2020-Q4"),
        ("2019-12-31", "2019-20", "2020-21", 183 / 366, "2019-Q4", "2020-Q1"),
    ],
)
def test_timing(day, fy, first_full, share, q, q_full):
    t = timing(dt.date.fromisoformat(day)).as_dict()
    assert t["first_exposed_fy"] == fy
    assert t["first_full_fy"] == first_full
    assert t["exposure_share_first_fy"] == round(share, 4)
    assert t["first_exposed_quarter"] == q
    assert t["first_full_quarter"] == q_full


def test_financial_year_labels():
    assert financial_year(dt.date(2016, 6, 30)) == 2016
    assert financial_year(dt.date(2016, 7, 1)) == 2017
    assert fy_label(2000) == "1999-00"
