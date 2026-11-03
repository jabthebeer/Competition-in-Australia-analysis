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


@pytest.mark.skipif(not (OUT / "anzsic_isic4.json").exists(), reason="concordance not built")
def test_division_notes_flag_the_mismatched_divisions():
    out = json.loads((OUT / "anzsic_isic4.json").read_text("utf-8"))
    divs = out["divisions"]
    assert set(divs) == {c for c in anzsic._codes() if len(c) == 1 and c.isalpha()}
    for v in divs.values():
        assert v["flag"] == (v["out_share"] >= concordance.FLAG or v["in_share"] >= concordance.FLAG)
        assert bool(v["note"]) == v["flag"]
    assert divs["J"]["in"][0]["anzsic"] == "7000" and divs["M"]["out"][0]["anzsic"] == "7000"
    assert not divs["A"]["flag"] and divs["S"]["flag"]
    assert "retail trade" in divs["F"]["note"]  # the merge with the other trade division is mentioned
    assert concordance.division_notes() == {d: v["note"] for d, v in divs.items() if v["flag"]}


@pytest.mark.skipif(not (OUT / "peers.json").exists(), reason="peer ranking not built")
def test_built_peer_ranking_proposes_a_core_group_for_approval():
    out = json.loads((OUT / "peers.json").read_text("utf-8"))
    assert len(out["proposed_core"]) == peers.CORE and "AUS" not in out["proposed_core"]
    assert out["proposed_core"] == [r["country"] for r in out["ranking"][: peers.CORE]]
    assert len(out["ranking"]) == len(OECD) - 1
    assert out["checks"]["stan_groups_vs_total_max_gap"] < 0.01
    assert out["core"] == peers.APPROVED["core"] and "approved" in out["status"]
    # The approved group swaps at most one economy of the proposal, for one ranked close behind
    rank = {r["country"]: r["rank"] for r in out["ranking"]}
    assert len(set(out["core"]) - set(out["proposed_core"])) <= 1
    assert all(rank[c] <= peers.CORE + 2 for c in out["core"])
    assert all(r["in_business_demography"] for r in out["ranking"] if r["country"] in out["core"])


# ---- Phase P1 connectors -------------------------------------------------------------------------------------


def test_oecd_parse_keeps_dimensions_and_drops_missing_values():
    from alicia.international import oecd

    ds = oecd.DATASETS["sdbs_births_deaths"]
    text = (
        "DATAFLOW,FREQ,REF_AREA,MEASURE,ACTIVITY,SIZE_CLASS,AGE,ENT_TYPE,BUSINESS_STAGE,UNIT_MEASURE,TIME_PERIOD,"
        "OBS_VALUE,UNIT_MULT,OBS_STATUS\n"
        "x,A,CAN,ENT,C,_T,Y_LT1,ENT_EMP,B,ENT_EM,2019,4200,0,A\n"
        "x,A,CAN,ENT,C,_T,_T,ENT_EMP,ACTIVE,ENT_EM,2019,60000,,A\n"
        "x,A,CAN,ENT,C,_T,_T,ENT_EMP,D,ENT_EM,2019,,0,M\n"
    )
    df = oecd.parse(text, ds)
    assert list(df.columns[:7]) == [
        "country",
        "measure",
        "activity",
        "size_class",
        "age",
        "business_stage",
        "unit_measure",
    ]
    assert len(df) == 2 and set(df["business_stage"]) == {"B", "ACTIVE"}
    assert df["unit_mult"].tolist() == [0, 0] and df["value"].sum() == 64200
    with pytest.raises(ValueError):
        oecd.parse("<html>error</html>", ds)
    with pytest.raises(ValueError):
        oecd.parse("DATAFLOW,FREQ,REF_AREA,TIME_PERIOD,OBS_VALUE\nx,A,CAN,2019,1\n", ds)


def test_oecd_datasets_ask_only_for_the_oecd_members():
    from alicia.international import oecd

    for ds in oecd.DATASETS.values():
        assert "+".join(OECD) in ds.url and ds.url.startswith(oecd.SDMX) and ds.url.endswith("format=csvfile")
    # births are stage B at age under one; deaths stage D; the denominator for high growth is 10+ employees
    bd = oecd.DATASETS["sdbs_births_deaths"].key
    assert "ACTIVE+B+D" in bd and "_T+Y_LT1" in bd and "S_GE10" in bd


def test_recorded_url_reads_the_manifest(tmp_path, monkeypatch):
    from alicia.international import oecd
    from alicia.pipeline import store

    monkeypatch.setattr(store, "ROOT", tmp_path)
    monkeypatch.setattr(store, "RAW", tmp_path / "data" / "raw")
    monkeypatch.setattr(store, "MANIFESTS", tmp_path / "data" / "manifests")
    assert oecd.recorded_url("src", "t.csv") is None
    (tmp_path / "data" / "raw" / "src").mkdir(parents=True)
    f = tmp_path / "data" / "raw" / "src" / "t.csv"
    f.write_text("x", encoding="utf-8")
    store.record_download("src", f, "https://example.org/q?a=1", "CC BY 4.0")
    assert oecd.recorded_url("src", "t.csv") == "https://example.org/q?a=1"


def test_bds_parse_and_latest_release():
    from alicia.international import bds

    assert bds.latest_release('<a href="2021/">x</a><a href="2023/">y</a><a href="2022/">') == "2023"
    with pytest.raises(ValueError):
        bds.latest_release("<html></html>")
    text = "year,sector,fage,firms,emp,firmdeath_firms\n2019,44-45,a) 0,44570,202814,X\n2019,44-45,b) 1,35648,D,7208\n"
    df = bds.parse(text)
    assert set(df["measure"]) == {"firms", "emp", "firmdeath_firms"}
    assert len(df) == 4  # the suppressed cells ("X", "D") are left out
    assert df[(df["fage"] == "a) 0") & (df["measure"] == "firms")]["value"].item() == 44570


def test_coverage_reads_years_from_spans():
    from alicia.international import coverage

    assert coverage._last_year("2005-Q1 to 2025-Q3") == 2025 and coverage._last_year("2012 to 2018") == 2018
    assert coverage._last_year("") is None
    assert coverage.countries()[0] == "AUS" and set(peers.APPROVED["core"]) <= set(coverage.countries())


@pytest.mark.skipif(not (OUT / "sdbs_births_deaths.parquet").exists(), reason="business demography not built")
def test_built_business_demography_has_births_for_the_core_peers():
    from alicia.international import oecd

    df = oecd.read("sdbs_births_deaths")
    # by section: European members do not publish an all-industries total, so groups are summed from sections
    births = df[(df["business_stage"] == "B") & (df["measure"] == "ENT") & (df["activity"] == "C")]
    assert set(peers.APPROVED["core"]) <= set(births["country"])
    assert "AUS" not in set(df["country"]) and "USA" not in set(df["country"])
    # births are a plausible share of active employer enterprises (Canada, 2019)
    can = df[
        (df["country"] == "CAN") & (df["activity"] == "_T") & (df["size_class"] == "_T") & (df["period"] == "2019")
    ]
    can = can[(can["measure"] == "ENT") & (can["unit_measure"] == "ENT_EM")].set_index("business_stage")["value"]
    assert 0.03 < can["B"] / can["ACTIVE"] < 0.15
