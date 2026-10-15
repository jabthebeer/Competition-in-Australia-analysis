"""Evaluability screen rules. All records here are ILLUSTRATIVE test fixtures."""

from __future__ import annotations

from regimpact.menu.screen import Coverage, screen_all
from regimpact.register.schema import ChangeRecord

SRC = "https://example.org/illustrative-source"
COV = Coverage(outcome="illustrative", first_fy=2008, last_fy=2025, note="")


def rec(id, jurisdiction, commenced, family=None, anzsic="4623", verified=True) -> ChangeRecord:
    return ChangeRecord.model_validate(
        {
            "id": id,
            "family": family,
            "title": "ILLUSTRATIVE",
            "jurisdiction": jurisdiction,
            "summary": "x",
            "instruments": [
                {
                    "title": "Illustrative Act",
                    "register_url": None,
                    "register_id": None,
                    "role": "principal",
                    "provisions": None,
                }
            ],
            "dates": {"commenced": [{"date": commenced, "what": "x", "source": SRC}] if commenced else []},
            "direction": "enhancing",
            "direction_rationale": "x",
            "direction_sources": [],
            "channels": ["barriers"],
            "industries": [{"anzsic": anzsic, "name": "x", "exposure": "direct"}],
            "comparison": "x",
            "confounders": [],
            "price_series": None,
            "notes": None,
            "verified": {"dates": verified, "notes": None},
        }
    )


def test_staggered_state_reform_with_good_window_rates_high():
    recs = [rec("nsw-a-2016", "NSW", "2016-07-01", "fam"), rec("vic-a-2017", "VIC", "2017-07-01", "fam")]
    s = screen_all(recs, COV)["nsw-a-2016"]
    assert s.rating == "high"
    assert s.comparison == "staggered"
    assert (s.pre_years, s.post_years) == (9, 9)


def test_national_change_is_industry_only():
    s = screen_all([rec("cth-a-2016", "CTH", "2016-07-01")], COV)["cth-a-2016"]
    assert s.comparison == "industry-only"
    assert s.rating == "medium"


def test_covid_window_short_post_period_and_unverified_dates_rate_low():
    s = screen_all([rec("wa-a-2021", "WA", "2021-03-01", verified=False)], COV)["wa-a-2021"]
    assert s.rating == "low"
    text = " ".join(s.weaknesses)
    assert "COVID" in text and "dates not fully verified" in text


def test_short_pre_period_and_broad_industry():
    s = screen_all([rec("sa-a-2009", "SA", "2009-07-01", anzsic="46")], COV)["sa-a-2009"]
    assert any("only 2 financial year(s) of outcome data before 2009-10" in w for w in s.weaknesses)
    assert any("division or subdivision" in w for w in s.weaknesses)


def test_overlapping_changes_are_flagged_but_family_members_are_not():
    recs = [
        rec("nsw-a-2016", "NSW", "2016-07-01", "fam"),
        rec("vic-a-2017", "VIC", "2017-07-01", "fam"),
        rec("nsw-b-2017", "NSW", "2017-03-01"),
        rec("cth-c-2016", "CTH", "2016-01-01", anzsic="46"),
    ]
    s = screen_all(recs, COV)["nsw-a-2016"]
    assert s.overlapping == ("cth-c-2016", "nsw-b-2017")


def test_not_commenced():
    s = screen_all([rec("cth-a-2027", "CTH", None)], COV)["cth-a-2027"]
    assert s.rating == "not-yet"
