"""Comparing Australia with similar economies (``alicia.international``): the common industry groups, the ABS
ANZSIC to ISIC correspondence parser, the STAN and WDI readers, and the peer-similarity ranking."""

from __future__ import annotations

import json

import pytest

from alicia import anzsic
from alicia.international import OECD, OUT, concordance, peers, prose, stan, wdi

# Laid out as the ABS correspondence page: a division and group heading, a class with two partial matches
# (the second on a continuation row), a class with one full match, then a heading that ends the class above.
PAGE = """
<table><tr><th>ANZSIC 2006</th><th>ISIC Rev. 4</th></tr>
<tr><td>A</td><td>Agriculture</td><td></td><td></td></tr>
<tr><td>011</td><td>Nursery</td><td></td><td></td><td></td></tr>
<tr><td></td><td>0111</td><td>Nursery Production (Under Cover)</td><td>0129p</td><td>Perennial crops</td></tr>
<tr><td></td><td></td><td></td><td>0130p</td><td>Plant propagation</td></tr>
<tr><td></td><td>0113</td><td>Turf&nbsp;Growing</td><td>0130</td><td>Plant propagation</td></tr>
<tr><td>012</td><td>Mushrooms</td><td></td><td></td><td></td></tr>
<tr><td></td><td></td><td></td><td>9999p</td><td>Should be ignored: no class above it</td></tr>
</table>
"""


def test_groups_cover_each_classification_once():
    g = concordance.groups()
    isic = [d for grp in g["groups"] for d in grp["isic"]]
    divisions = [d for sec, ds in g["isic_sections"].items() if sec != "U" for d in ds]
    assert sorted(isic) == sorted(divisions) and len(isic) == len(set(isic))
    anz = [d for grp in g["groups"] for d in grp["anzsic_divisions"]]
    assert sorted(anz) == sorted(c for c in anzsic._codes() if len(c) == 1 and c.isalpha())
    codes = {a for grp in g["groups"] for a, _ in grp["stan"]}
    assert codes <= set("ABCFGHIJKLOPQRST") | {"D_E", "L68A", "M_N", "N77"}
    assert concordance.isic_group("6201") == "ICT" and concordance.isic_group("7710") == "RES"
    assert concordance.isic_group("9900") is None


def test_parse_reads_classes_matches_and_partial_flags():
    assert concordance.parse(PAGE) == [
        ("0111", "0129", True),
        ("0111", "0130", True),
        ("0113", "0130", False),
    ]


def test_check_reports_pairs_missing_from_one_direction():
    forward = [("0111", "0129", True), ("0111", "0130", True)]
    reverse = [("0129", "0111", False)]
    c = concordance.check(forward, reverse)
    assert c["only_in_anzsic_to_isic"] == [["0111", "0130"]] and c["only_in_isic_to_anzsic"] == []
    assert "0111" not in c["codelist_classes_without_a_match"] and "0113" in c["codelist_classes_without_a_match"]


def test_assign_takes_the_majority_group_and_breaks_ties_by_division():
    pairs = [
        ("7000", "6201", True),  # computer system design: ISIC 62 (ICT) twice, 33 (manufacturing) once
        ("7000", "6202", True),
        ("7000", "3312", True),
        ("9419", "4520", True),  # automotive repair: one trade, one other services -> tie, its division (S) wins
        ("9419", "9529", True),
        ("7552", "9900", False),  # only ISIC 99: kept with its ANZSIC division (O)
    ]
    a = concordance.assign(pairs)
    assert a["7000"]["group"] == "ICT" and a["7000"]["share"] == pytest.approx(2 / 3, abs=1e-4)
    assert a["7000"]["other_groups"] == ["MAN"]
    assert a["9419"]["group"] == "OTH"
    assert a["7552"]["group"] == "PUB" and a["7552"]["share"] == 0


def test_division_fit_weights_classes_by_businesses():
    assigned = {"7000": {"group": "ICT"}, "6910": {"group": "PRO"}, "5801": {"group": "ICT"}}
    fit = concordance.division_fit(assigned, {"7000": 30.0, "6910": 70.0, "5801": 10.0})
    assert fit["PRO"]["in_group"] == pytest.approx(0.7) and fit["PRO"]["covered"] == 1
    assert fit["ICT"]["in_group"] == 1 and fit["ICT"]["covered"] == pytest.approx(10 / 40)
    assert fit["PRO"]["classes_elsewhere"][0]["anzsic"] == "7000"


def _stan_rows(country, values, year=2016):
    return [
        {"country": country, "country_name": country, "activity": a, "year": year, "value_added_mn": v}
        for a, v in values.items()
    ]


BASE = {a: 10.0 for a in ("A", "B", "C", "D_E", "F", "G", "H", "I", "J", "K", "O", "P", "Q", "R", "S")}
BASE |= {"T": 0.0, "L": 30.0, "L68A": 20.0, "N77": 2.0, "M_N": 12.0, "_T": 192.0}


def test_group_values_apply_the_stan_formulas():
    v = peers.group_values(_stan_rows("AUS", BASE))[("AUS", 2016)]
    assert v["RES"] == 12.0  # L - L68A + N77
    assert v["PRO"] == 10.0  # M_N - N77
    assert v["OTH"] == 20.0  # R + S + T
    assert sum(v.values()) + BASE["L68A"] == BASE["_T"]
    assert stan.additivity(_stan_rows("AUS", BASE)) == pytest.approx(0)


def test_rental_stays_in_professional_services_when_not_split():
    rows = _stan_rows("TUR", {k: v for k, v in BASE.items() if k != "N77"})
    v = peers.group_values(rows)[("TUR", 2016)]
    assert v["RES"] == 10.0 and v["PRO"] == 12.0
    assert peers.unsplit_rental(rows) == {("TUR", 2016)}


def test_structure_drops_real_estate_when_imputed_rent_is_missing():
    rows = []
    for y in range(2015, 2020):
        rows += _stan_rows("AUS", BASE, y) + _stan_rows("KOR", {k: v for k, v in BASE.items() if k != "L68A"}, y)
    s = peers.structure(peers.group_values(rows), (2015, 2019))
    assert "RES" in s["AUS"]["groups"] and "RES" not in s["KOR"]["groups"]
    assert sum(s["KOR"]["shares"].values()) == pytest.approx(1)
    assert peers.dissimilarity(s["AUS"]["shares"], s["KOR"]["shares"]) == pytest.approx(0)


def test_dissimilarity_is_zero_for_equal_structures_and_one_for_disjoint():
    assert peers.dissimilarity({"a": 0.5, "b": 0.5}, {"a": 0.25, "b": 0.25}) == 0
    assert peers.dissimilarity({"a": 1.0, "b": 0.0}, {"a": 0.0, "b": 1.0}) == 1


def test_rank_puts_the_most_similar_economy_first(monkeypatch):
    monkeypatch.setattr(peers, "OECD", ["AUS", "TWN", "FAR", "MID"])
    rows = []
    for y in range(2015, 2020):
        rows += _stan_rows("AUS", BASE, y) + _stan_rows("TWN", BASE, y)
        rows += _stan_rows("MID", BASE | {"B": 40.0}, y) + _stan_rows("FAR", BASE | {"B": 0.0, "C": 80.0}, y)
    wdi_rows = [
        {"country": c, "indicator": ind, "year": y, "value": v}
        for y in range(2015, 2020)
        for c, inc in (("AUS", 50e3), ("TWN", 50e3), ("MID", 40e3), ("FAR", 20e3))
        for ind, v in (("gdp_per_head_ppp", inc), ("population", 25e6), ("trade_share_gdp", 45.0))
    ]
    r = peers.rank(rows, wdi_rows, peers.WEIGHTS, (2015, 2019))["ranking"]
    assert [x["country"] for x in r] == ["TWN", "MID", "FAR"]
    assert r[0]["score"] == 0 and r[0]["distance"]["structure"] == 0


def test_stan_parse_reads_sdmx_csv_and_scales_to_millions():
    head = (
        "STRUCTURE,STRUCTURE_ID,STRUCTURE_NAME,ACTION,FREQ,Frequency of observation,REF_AREA,Reference area,"
        "ACTIVITY,Economic activity,MEASURE,Measure,PRICE_BASE,Price base,UNIT_MEASURE,Unit of measure,"
        "TIME_PERIOD,Time period,OBS_VALUE,Observation value,UNIT_MULT,Unit multiplier,OBS_STATUS,Observation status"
    )
    row = "DATAFLOW,x,STAN,I,A,Annual,CAN,Canada,B,Mining,B1G,Value added,V,Current,XDC,NC,2023,,2.5,,9,Bn,A,Normal"
    blank = row.replace(",2.5,", ",,")
    rows = stan.parse("\n".join([head, row, blank]))
    assert rows == [
        {
            "country": "CAN",
            "country_name": "Canada",
            "activity": "B",
            "year": 2023,
            "value_added_mn": 2500.0,
            "status": "A",
        }
    ]
    with pytest.raises(ValueError):
        stan.parse(head + "\n" + row.replace(",V,", ",Q,"))
    assert "+".join(OECD) in stan.url() and "L68A" in stan.url() and stan.url().count("B1G.V.XDC") == 1


def test_wdi_parse_and_licence_come_from_the_response():
    data = [
        {"page": 1, "pages": 1},
        [
            {"countryiso3code": "AUS", "country": {"value": "Australia"}, "date": "2019", "value": 25.4e6},
            {"countryiso3code": "AUS", "country": {"value": "Australia"}, "date": "2025", "value": None},
        ],
    ]
    assert wdi.parse(data, "SP.POP.TOTL") == [
        {"country": "AUS", "country_name": "Australia", "indicator": "population", "year": 2019, "value": 25.4e6}
    ]
    with pytest.raises(ValueError):
        wdi.parse([{"page": 1, "pages": 2}, []], "SP.POP.TOTL")
    meta = {
        "source": [
            {
                "concept": [
                    {
                        "variable": [
                            {
                                "metatype": [
                                    {"id": "IndicatorName", "value": "Population, total"},
                                    {"id": "License_Type", "value": "CC BY-4.0"},
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    assert wdi.licence(meta) == ("Population, total", "CC BY-4.0, World Bank")


def test_prose_keeps_bullets():
    doc = "Title.\n\nIntro line\n    continues.\n\n- one\n  more\n- two\n"
    assert prose(doc) == "Intro line continues.\n\n- one more\n- two"


@pytest.mark.skipif(not (OUT / "anzsic_isic4.json").exists(), reason="concordance not built")
def test_built_concordance_covers_every_anzsic_class():
    out = json.loads((OUT / "anzsic_isic4.json").read_text("utf-8"))
    classes = {c for c in anzsic._codes() if len(c) == 4}
    assert set(out["classes"]) == classes
    assert {c["group"] for c in out["classes"].values()} == {g["id"] for g in concordance.groups()["groups"]}
    assert out["checks"]["codelist_classes_without_a_match"] == []
    assert out["classes"]["7000"]["group"] == "ICT"


@pytest.mark.skipif(not (OUT / "peers.json").exists(), reason="peer ranking not built")
def test_built_peer_ranking_proposes_a_core_group_for_approval():
    out = json.loads((OUT / "peers.json").read_text("utf-8"))
    assert len(out["proposed_core"]) == peers.CORE and "AUS" not in out["proposed_core"]
    assert out["proposed_core"] == [r["country"] for r in out["ranking"][: peers.CORE]]
    assert len(out["ranking"]) == len(OECD) - 1
    assert out["checks"]["stan_groups_vs_total_max_gap"] < 0.01
    assert "awaiting owner approval" in out["status"]
