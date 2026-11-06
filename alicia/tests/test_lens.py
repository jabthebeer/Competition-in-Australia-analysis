"""The Industry lens (beta): competition coding by market position, the page's data, and the state map."""

from __future__ import annotations

import json
import re

import pytest
from pydantic import ValidationError

from alicia.menu import growth, lens
from alicia.pipeline import boundaries
from alicia.register import competition as C
from alicia.register.catalogue import load_records
from alicia.register.requirements import Requirement

SOURCE = {
    "title": "Example Act 2000",
    "publisher": "Federal Register of Legislation",
    "url": "https://www.legislation.gov.au/C2004A00001/latest/text",
    "locator": "s 10",
    "quote": "A person must not carry on a business without a licence.",
    "accessed": "2026-11-06",
    "checked": "register-text",
}


def req(**over) -> Requirement:
    base = {
        "id": "cth-example",
        "family": "example",
        "jurisdiction": "CTH",
        "tier": "cth",
        "title": "Hold a licence",
        "kind": "licence",
        "what": "Hold a licence before trading.",
        "laws": [{"title": "Example Act 2000", "jurisdiction": "CTH", "kind": "act", "register_id": "C2004A00001"}],
        "sources": [SOURCE],
        "triggers": [{"type": "entry"}],
        "reach": [{"scope": "listed", "classes": ["4511"], "sources": [SOURCE]}],
        "confidence": "high",
        "drafted_on": "2026-11-06",
    }
    return Requirement.model_validate(base | over)


def threshold(kind: str, value: float, unit: str = "AUD a year") -> dict:
    return {"type": kind, "test": ">=", "value": value, "unit": unit, "as_at": "2026-11-06", "sources": [SOURCE]}


def test_a_licence_before_trading_is_a_strong_cost_of_entry_and_registration_a_minor_one():
    assert C.rule_effects(req())["entrants"] | {"reason": ""} == {
        "effect": "negative",
        "strength": "strong",
        "reason": "",
    }
    weak = C.rule_effects(req(kind="registration"))
    assert weak["entrants"]["strength"] == "weak" and set(weak) == {"entrants"}


def test_size_thresholds_exempt_entrants_and_add_a_step_for_smaller_firms_unless_tiny_or_only_for_the_largest():
    gst = C.rule_effects(
        req(kind="registration", triggers=[threshold("turnover", 75_000, "AUD of GST turnover a year")])
    )
    assert gst["entrants"]["effect"] == "positive" and gst["smaller"]["effect"] == "negative"
    assert "$75,000 of GST turnover a year" in gst["smaller"]["reason"]
    assert C.rule_effects(req(kind="insurance", triggers=[threshold("payroll", 7_500)])) == {}  # applies to almost all
    big = C.rule_effects(req(kind="reporting", triggers=[threshold("revenue", 100_000_000)]))
    assert set(big) == {"entrants"}  # only the largest businesses: no step for small and medium ones
    staff = C.rule_effects(req(kind="reporting", triggers=[threshold("employees", 100, "employees")]))
    assert "100 employees" in staff["smaller"]["reason"]


def test_an_approval_any_business_may_need_for_an_activity_is_not_a_cost_of_entering_this_market():
    anywhere = req(
        kind="approval",
        triggers=[{"type": "activity"}],
        reach=[{"scope": "all", "condition": "if it clears habitat", "sources": [SOURCE]}],
    )
    assert C.rule_effects(anywhere) == {}
    assert C.rule_effects(req(kind="approval", triggers=[{"type": "activity"}]))["entrants"]["effect"] == "negative"


def test_duties_every_business_or_employer_meets_alike_are_left_uncoded():
    assert C.rule_effects(req(kind="standard", triggers=[{"type": "first-employee"}])) == {}
    assert C.rule_effects(req(kind="standard", triggers=[{"type": "ongoing"}])) == {}


def test_records_are_coded_from_their_direction_and_channels():
    records = {r.id: r for r in load_records().records}
    pharmacy = next(
        r for r in records.values() if r.direction == "weakening" and set(r.channels) == {"barriers", "number-or-type"}
    )
    eff = C.record_effects(pharmacy)
    assert set(eff) == {"entrants", "dominant"} and {e["effect"] for e in eff.values()} == {"negative"}
    for r in records.values():
        positions = {p for ch in r.channels for p in C.CHANNEL_POSITIONS[ch]}
        assert set(C.record_effects(r)) == positions
        assert {e["effect"] for e in C.record_effects(r).values()} <= {C.DIRECTION_EFFECT[r.direction]}


def test_a_hand_coded_assessment_overrides_the_rules_and_a_setting_link_brings_its_coding():
    own = {
        "effects": [
            {"position": "dominant", "effect": "positive", "reason": "Opens the network to rivals on equal terms."}
        ],
        "assessed_on": "2026-11-06",
    }
    effects, basis, _ = C.requirement_effects(req(competition=own), {})
    assert basis == "assessed" and set(effects) == {"dominant"}
    with pytest.raises(ValidationError, match="each position at most once"):
        req(competition=own | {"effects": own["effects"] * 2})
    records = load_records().records
    settings = {r.id: r for r in records if r.kind == "setting"}
    setting = next(iter(settings.values()))
    effects, basis, sid = C.requirement_effects(req(records=[setting.id]), settings)
    assert basis == "register" and sid == setting.id and effects == C.record_effects(setting)


def test_the_page_data_covers_every_class_state_and_law_and_points_at_real_files():
    records = load_records().records
    p = lens.payload(records)
    assert len(p["classes"]) == 506 and [s["code"] for s in p["states"]] == [
        "NSW",
        "VIC",
        "QLD",
        "SA",
        "WA",
        "TAS",
        "NT",
        "ACT",
    ]
    assert [x["id"] for x in p["positions"]] == ["entrants", "smaller", "dominant"]
    assert len(p["map"]["areas"]) == 8 and all(a["path"].startswith("M") for a in p["map"]["areas"])
    ids = {r["id"] for r in p["rows"]}
    assert {"nsw-food-business-registration", "cth-gst-registration"} <= ids
    assert not ids & {r.id for r in records if r.ended is not None}  # repealed or replaced items are left out
    root = lens.ROOT
    assert all((root / r["file"]).exists() for r in p["rows"])
    food = next(r for r in p["rows"] if r["id"] == "nsw-food-business-registration")
    assert "4511" in food["reach"][0]["classes"] and food["effects"]["entrants"]["effect"] == "negative"
    gst = next(r for r in p["rows"] if r["id"] == "cth-gst-registration")
    assert gst["reach"][0]["classes"] == "all" and gst["basis"] == "rule"


def test_the_page_renders_with_no_placeholders_left_and_is_linked_from_the_landing_page():
    html = growth.render(lens.PAGE[0], lens.payload(load_records().records), lens.PAGE[0], standalone=True)
    assert not re.search(r"__[A-Z_]+__", html) and "<title>ALICIA Industry lens (beta)</title>" in html
    assert '<a href="industry-lens.html" aria-current="page">Industry lens (beta)</a>' in html
    data = json.loads(re.search(r'id="page-data">(.*?)</script>', html, re.S).group(1))
    assert data["default"] == {"class": "4511", "state": "NSW"}
    assert '<a class="view-link" href="industry-lens.html">' in growth.landing({"industry-lens.html"})


def test_the_state_map_is_projected_into_a_1000_wide_frame():
    canberra, sydney, perth = (
        boundaries.albers(149.13, -35.28),
        boundaries.albers(151.21, -33.87),
        boundaries.albers(115.86, -31.95),
    )
    assert perth[0] < canberra[0] < sydney[0] and canberra[1] < sydney[1]  # west to east; Canberra south of Sydney
    square = {"type": "Polygon", "coordinates": [[[140, -30], [150, -30], [150, -40], [140, -40], [140, -30]]]}
    island = {"type": "Polygon", "coordinates": [[[145, -42], [145.001, -42], [145.001, -42.001], [145, -42]]]}
    geo = {
        "features": [
            {
                "properties": {"state_code_2021": "1", "state_name_2021": "New South Wales"},
                "geometry": {"type": "MultiPolygon", "coordinates": [square["coordinates"], island["coordinates"]]},
            }
        ]
    }
    m = boundaries.svg_map(geo, "STE")
    area = m["areas"][0]
    assert (
        m["viewBox"].startswith("0 0 1000 ") and area["abbr"] == "NSW" and area["path"].count("M") == 1
    )  # the islet is dropped
    stored = json.loads((lens.MAP).read_text("utf-8"))
    assert {a["abbr"] for a in stored["areas"]} == {"NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"}
