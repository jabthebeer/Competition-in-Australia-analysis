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


# ---- Phase P2 harmonisation ----------------------------------------------------------------------------------


def test_section_sum_treats_missing_rental_as_unsplit():
    from alicia.international import harmonise as h

    assert h._section_sum({"M": 10.0, "N": 5.0, "N77": 1.0}, [["M", 1], ["N", 1], ["N77", -1]]) == (14.0, False)
    assert h._section_sum({"M": 10.0, "N": 5.0}, [["M", 1], ["N", 1], ["N77", -1]]) == (15.0, True)
    assert h._section_sum({"M": 10.0}, [["M", 1], ["N", 1]]) == (None, False)


def _bd_rows(country, year, sections, active=100.0, births=10.0, deaths=8.0):
    rows = []
    for a in sections:
        for stage, age, v in (("ACTIVE", "_T", active), ("B", "Y_LT1", births), ("D", "_T", deaths)):
            rows.append(
                {
                    "country": country,
                    "measure": "ENT",
                    "activity": a,
                    "size_class": "_T",
                    "age": age,
                    "business_stage": stage,
                    "unit_measure": "ENT_EM",
                    "period": str(year),
                    "value": v,
                }
            )
    return rows


def test_oecd_demography_sums_sections_and_needs_every_group_for_the_total():
    import pandas as pd

    from alicia.international import harmonise as h

    full = [*"BCDEFGHIJKLMNPQRS", "N77"]
    df = pd.DataFrame(_bd_rows("FRA", 2018, [a for a in full if a != "K"]) + _bd_rows("CAN", 2018, ["C"]))
    out = pd.DataFrame(h.oecd_demography(df))
    fra = out[out["country"] == "FRA"].set_index(["group", "measure"])["value"]
    assert fra[("MAN", "birth_rate")] == pytest.approx(10.0) and fra[("MAN", "net_entry_rate")] == pytest.approx(2.0)
    # finance (K) is missing, but it is not in the business-economy total
    assert ("FIN", "birth_rate") not in fra.index and fra[("ALL", "birth_rate")] == pytest.approx(10.0)
    # PRO = M + N - N77: (100 + 100 - 100) active, (10 + 10 - 10) births
    assert fra[("PRO", "birth_rate")] == pytest.approx(10.0)
    # Canada has manufacturing only: no total
    assert set(out[out["country"] == "CAN"]["group"]) == {"MAN"}


def test_hours_break_test_and_optional_activities():
    from alicia.international import harmonise as h

    assert h._broken({"lp_growth_hour": (78.5, 100.0), "lp_growth_person": (104.1, 100.0)})  # AUS manufacturing 2018
    assert not h._broken({"lp_growth_hour": (97.0, 100.0), "lp_growth_person": (99.0, 100.0)})
    P = {("AUS", 2019, "L"): 1.0, ("AUS", 2019, "L68A"): 1.0}
    V = {("AUS", 2018, "L"): 1.0, ("AUS", 2018, "L68A"): 1.0, ("AUS", 2018, "N77"): 1.0}
    f, missing = h._formula([(P, 2019), (V, 2018)], "AUS", 2019, [["L", 1], ["L68A", -1], ["N77", 1]])
    assert missing == ["N77"] and f == [("L", 1), ("L68A", -1)]


def test_stan_productivity_chain_links_and_divides_by_employment():
    import pandas as pd

    from alicia.international import harmonise as h

    acts = ["A", "B", "C", "D_E", "F", "G", "H", "I", "J", "K", "L", "L68A", "M_N", "N77", "O", "P", "Q", "R", "S", "T"]
    size = {"L68A": 0.2, "N77": 0.1}  # small parts, so the groups that subtract them stay positive
    vh, va = [], []

    def row(a, measure, base, unit, year, value, mult):
        return dict(
            country="ITA",
            activity=a,
            measure=measure,
            price_base=base,
            unit_measure=unit,
            period=str(year),
            value=value,
            unit_mult=mult,
        )

    for a in acts:
        k = size.get(a, 1.0)
        vh.append(row(a, "B1G", "Y", "XDC", 2019, 106.0 * k, 6))  # value added up 6% in volume
        for y, hours, persons in ((2018, 100.0, 100.0), (2019, 102.0, 101.0)):
            e = 0.0 if a == "L68A" else k  # imputed rent has no hours or workers
            vh.append(row(a, "EMP", "_Z", "H", y, hours * e, 6))
            vh.append(row(a, "EMP", "_Z", "PS", y, persons * e, 3))
        va.append({"country": "ITA", "activity": a, "year": 2018, "value_added_mn": 100.0 * k})
    out = pd.DataFrame(h.stan_productivity(pd.DataFrame(vh), va)).set_index(["group", "measure"])["value"]
    # value added +6%, hours +2%, persons +1%, in every group and so in the total
    for g in ("MAN", "RES", "PRO", "ALL"):
        assert out[(g, "lp_growth_hour")] == pytest.approx(100 * (1.06 / 1.02 - 1))
        assert out[(g, "lp_growth_person")] == pytest.approx(100 * (1.06 / 1.01 - 1))


def test_ratings_start_from_the_source_and_drop_for_mismatches():
    import pandas as pd

    from alicia.international import harmonise as h

    if not (OUT / "anzsic_isic4.json").exists():
        pytest.skip("concordance not built")
    df = pd.DataFrame(
        [
            h._rows("AUS", "MAN", "birth_rate", 2018, 10.0, "ABS CABEE"),
            h._rows("AUS", "MAN", "net_entry_rate", 2018, 1.0, "ABS CABEE"),
            h._rows("AUS", "RES", "net_entry_rate", 2018, 1.0, "ABS CABEE"),
            h._rows("AUS", "ICT", "lp_growth_person", 2018, 1.0, h.ABS_ACCOUNTS),
            h._rows("AUS", "CON", "lp_growth_person", 2018, 1.0, h.ABS_ACCOUNTS),
            h._rows("AUS", "CON", "lp_growth_hour", 2018, 1.0, "ABS 5260"),
            h._rows("AUS", "TRD", "lp_growth_hour", 2018, 1.0, h.ABS_HOURS),
            h._rows("WA", "ICT", "lp_growth_person", 2018, 1.0, h.ABS_ACCOUNTS),
            h._rows("CAN", "RES", "birth_rate", 2018, 1.0, "OECD SDBS", "rental and leasing not split out"),
            h._rows("FRA", "MAN", "birth_rate", 2018, 1.0, "OECD SDBS"),
            h._rows("FRA", "MAN", "lp_growth_hour", 2018, 1.0, "OECD STAN"),
        ]
    )
    h.BREAKS[:] = [{"country": "AUS", "group": "CON", "year": y} for y in (2018, 2019, 2019)]  # one repeated
    h.BREAKS += [{"country": "FRA", "group": "MAN", "year": y} for y in (2018, 2019)]
    try:
        r = h.rate(df, class_split={"MAN": 0.07, "RES": 0.23}, sub_split={})
    finally:
        h.BREAKS.clear()
    r = r.set_index(["country", "group", "measure"])
    assert r.loc[("AUS", "MAN", "birth_rate"), "comparability"] == "low"
    assert r.loc[("AUS", "MAN", "net_entry_rate"), "comparability"] == "medium"
    assert r.loc[("AUS", "RES", "net_entry_rate"), "comparability"] == "low"  # 23% split
    # ABS output and jobs: medium (financial years), one lower where divisions and ISIC differ (76% for ICT)
    assert r.loc[("AUS", "CON", "lp_growth_person"), "comparability"] == "medium"
    assert r.loc[("AUS", "ICT", "lp_growth_person"), "comparability"] == "low"
    assert r.loc[("WA", "ICT", "lp_growth_person"), "comparability"] == "low"  # a state follows Australia's rules
    assert r.loc[("AUS", "TRD", "lp_growth_hour"), "comparability"] == "low"  # survey hours
    # breaks in survey or STAN hours do not lower the ABS's official per-hour series; repeated years count once
    assert r.loc[("AUS", "CON", "lp_growth_hour"), "comparability"] == "medium"
    assert r.loc[("FRA", "MAN", "lp_growth_hour"), "comparability"] == "medium"
    assert r.loc[("CAN", "RES", "birth_rate"), "comparability"] == "medium"
    assert r.loc[("FRA", "MAN", "birth_rate"), "comparability"] == "high"


def test_abs_growth_chain_links_divisions_and_drops_hours_breaks():
    import pandas as pd

    from alicia.international import harmonise as h

    if not (OUT / "anzsic_isic4.json").exists():
        pytest.skip("concordance not built")
    rows = []
    for d, cur, vol1, n1, h1 in (("F", 100.0, 110.0, 105.0, 105.0), ("G", 300.0, 302.0, 100.0, 140.0)):
        rows.append(("WA", d, 2019, vol1 / 1.1, cur, 100.0, 100.0))  # volumes rebased: growth is what counts
        rows.append(("WA", d, 2020, vol1, cur, n1, h1))
    inp = pd.DataFrame(
        rows, columns=["geo_code", "industry_code", "year", "gva_volume", "gva_current", "employed", "hours_actual"]
    )
    inp.loc[inp["industry_code"] == "G", "gva_volume"] = [300.0, 302.0]
    out = pd.DataFrame(h.abs_growth(inp.set_index(["geo_code", "industry_code", "year"]), "WA"))
    trd = out[(out["group"] == "TRD") & (out["year"] == 2020)].set_index("measure")["value"]
    va = (100 * 1.1 + 300 * 302 / 300) / 400  # each division's volume growth, weighted by last year's prices
    assert trd["va_growth"] == pytest.approx(100 * (va - 1))
    assert trd["emp_growth"] == pytest.approx(100 * (205 / 200 - 1))
    assert trd["lp_growth_person"] == pytest.approx(100 * (va / (205 / 200) - 1))
    assert "lp_growth_hour" not in trd  # hours +22.5% against persons +2.5%: a break, dropped
    assert set(out["source"]) == {h.ABS_ACCOUNTS}


@pytest.mark.skipif(not (OUT / "benchmark_inputs.parquet").exists(), reason="harmonised inputs not built")
def test_built_survival_matches_the_oecd_published_rates():
    import pandas as pd

    from alicia.international import oecd

    df = pd.read_parquet(OUT / "benchmark_inputs.parquet")
    sv = oecd.read("sdbs_survival")
    pub = sv[(sv["age"] == "Y3") & (sv["unit_measure"] == "PT_ENT_B") & (sv["size_class"] == "_T")]
    pub = pub[pub["activity"] == "C"].assign(year=lambda x: x["period"].astype(int)).set_index(["country", "year"])
    # the core peers exactly; a few others (Iceland, Finland, Denmark, 2015-2017) differ where births were revised
    ours = df[(df["measure"] == "survival_3y") & (df["group"] == "MAN") & df["country"].isin(peers.APPROVED["core"])]
    ours = ours.set_index(["country", "year"])["value"]
    common = ours.index.intersection(pub.index)
    assert len(common) > 30
    assert (ours[common] - pub.loc[common, "value"]).abs().max() < 0.1


@pytest.mark.skipif(not (OUT / "benchmark_inputs.parquet").exists(), reason="harmonised inputs not built")
def test_built_inputs_rate_australias_gross_rates_low_and_net_change_medium():
    import pandas as pd

    df = pd.read_parquet(OUT / "benchmark_inputs.parquet")
    a = df[(df["country"] == "AUS") & (df["group"] == "ALL") & (df["year"] == 2019)].set_index("measure")
    assert a.loc["birth_rate", "comparability"] == "low" and a.loc["net_entry_rate", "comparability"] == "medium"
    assert 5 < a.loc["birth_rate", "value"] < 15 and -5 < a.loc["net_entry_rate", "value"] < 5
    assert set(df["comparability"]) <= {"low", "medium", "high"}
    assert set(peers.APPROVED["core"]) <= set(df[(df["measure"] == "birth_rate") & (df["group"] == "ALL")]["country"])


@pytest.mark.skipif(not (OUT / "benchmark_inputs_states.parquet").exists(), reason="harmonised inputs not built")
def test_built_australia_is_on_abs_financial_years_and_the_states_add_up():
    import json

    import pandas as pd

    from alicia.pipeline import store

    df = pd.read_parquet(OUT / "benchmark_inputs.parquet")
    st = pd.read_parquet(OUT / "benchmark_inputs_states.parquet")
    # STAN's Australian value added is labelled by the year the financial year starts; its jobs are calendar years
    check = json.loads((OUT / "comparability.json").read_text("utf-8"))["stan_australia"]
    assert check["output_by_start_year"] > 0.95 > 0.5 > check["output_by_end_year"]
    assert check["persons_calendar_year"] > 0.95 > check["persons_financial_year"]
    # Australia's construction output growth is the state accounts', labelled by the year the financial year ends
    sa = store.read_panel("abs_state_accounts", "industry_state_fy")
    e = sa[(sa["measure"] == "gva_volume") & (sa["geo_code"] == "AUS") & (sa["industry_code"] == "E")]
    v = e.set_index(e["period"].dt.year + 1)["value"]
    ours = df[(df["country"] == "AUS") & (df["measure"] == "va_growth") & (df["group"] == "CON")].set_index("year")
    for y in (2016, 2020, 2025):
        assert ours.loc[y, "value"] == pytest.approx(100 * (v[y] / v[y - 1] - 1))
    # the state file's Australia is the national figure, wherever both use the same source
    nat = df[df["country"] == "AUS"].set_index(["measure", "group", "year"])["value"]
    aus = st[st["state"] == "AUS"].set_index(["measure", "group", "year"])
    same = aus[aus["source"] != "ABS accounts and LFS hours"]
    assert (same["value"] - nat.reindex(same.index)).abs().max() < 1e-9
    # every state has every measure; NT construction jobs are rated low (a small survey sample), NSW's medium
    assert set(st["state"]) == {"AUS", "NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"}
    assert st.groupby("state")["measure"].nunique().min() == 8
    r = st[(st["measure"] == "emp_growth") & (st["group"] == "CON") & (st["year"] == 2019)].set_index("state")
    assert r.loc["NT", "comparability"] == "low" and r.loc["NSW", "comparability"] == "medium"


# ---- Phase P3 benchmark engine -------------------------------------------------------------------------------


def test_quantile_matches_r_type_7():
    from alicia.international import benchmark as b

    xs = [3.0, 1.0, 4.0, 1.5, 9.0, 2.6]
    # R: quantile(c(3, 1, 4, 1.5, 9, 2.6), c(.25, .5, .75), type = 7) -> 1.775 2.8 3.75
    assert [round(b.quantile(xs, q), 10) for q in (0.25, 0.5, 0.75)] == [1.775, 2.8, 3.75]
    assert b.quantile([5.0], 0.25) == 5.0


def test_persistence_needs_most_years_on_one_side():
    from alicia.international import benchmark as b

    assert b.persistent(["below", "below", "within"]) == "below"
    assert b.persistent(["below", "above", "within", "below"]) is None  # half is not most
    assert b.persistent(["above"]) is None  # one year is too few


def _cells(au: dict, peers_: dict, measure="net_entry_rate", group="TRN", rating="medium"):
    import pandas as pd

    rows = [
        dict(country="AUS", group=group, measure=measure, year=y, value=v, comparability=rating) for y, v in au.items()
    ]
    for c, vals in peers_.items():
        rows += [
            dict(country=c, group=group, measure=measure, year=y, value=v, comparability="high")
            for y, v in vals.items()
        ]
    return pd.DataFrame(rows)


CORE6 = ["CAN", "GBR", "NZL", "FRA", "ESP", "ITA"]


def test_benchmark_flags_a_persistent_robust_gap_and_explains_the_rest():
    from alicia.international import benchmark as b

    years = range(2015, 2020)
    spread = {c: {y: 1.0 + 0.2 * i for y in years} for i, c in enumerate(CORE6)}  # peers 1.0 to 2.0
    flag = _cells({y: 0.2 for y in years}, spread)
    s, annual = b.benchmark(flag, CORE6)
    r = s[s["window"] == "2015-2019"].iloc[0]
    assert r["status"] == "flag" and r["side"] == "below" and r["years"] == 5 and r["rank"] == 7
    assert r["peer_median"] == pytest.approx(1.5) and r["gap"] == pytest.approx(-1.3)
    assert len(annual[annual["window"] == "2015-2019"]) == 5
    # the same gap with Australia's figure rated low is shown, not flagged
    low = _cells({y: 0.2 for y in years}, spread, rating="low")
    assert b.benchmark(low, CORE6)[0].iloc[0]["status"] == "outside, low comparability"
    # outside in two of five years only
    mixed = _cells({2015: 0.2, 2016: 0.2, 2017: 1.5, 2018: 1.5, 2019: 1.5}, spread)
    assert b.benchmark(mixed, CORE6)[0].iloc[0]["status"] == "outside, not persistent"
    # too few peers in each year
    few = _cells({y: 0.2 for y in years}, {c: spread[c] for c in CORE6[:3]})
    assert b.benchmark(few, CORE6)[0].iloc[0]["status"] == "too few years"


def test_leave_one_out_and_average_checks_can_stop_a_flag():
    from alicia.international import benchmark as b

    years = range(2015, 2020)
    # Australia just below the 25th percentile (0.85 with these six peers); leaving out any peer at 1.0 moves the
    # 25th percentile to 0.8, and Australia inside the range
    peers_ = {c: {y: 1.0 for y in years} for c in CORE6}
    peers_["CAN"] = {y: 0.5 for y in years}
    peers_["GBR"] = {y: 0.8 for y in years}
    s = b.benchmark(_cells({y: 0.84 for y in years}, peers_), CORE6)[0].iloc[0]
    assert s["side"] == "below" and s["status"] == "outside, fails leave-one-out"
    assert "FRA" in s["leave_one_out_failed_without"]
    # below the range in three years by a little, far above it in two: the average points the other way
    spread = {c: {y: 1.0 + 0.2 * i for y in years} for i, c in enumerate(CORE6)}
    s = b.benchmark(_cells({2015: 1.2, 2016: 1.2, 2017: 1.2, 2018: 9.0, 2019: 9.0}, spread), CORE6)[0].iloc[0]
    assert s["side"] == "below" and s["status"] == "outside, average on the other side"


def test_benchmark_windows_leave_out_the_pandemic_years():
    from alicia.international import benchmark as b

    assert b._years(_cells({y: 1.0 for y in range(2019, 2025)}, {}), "birth_rate", 2015, 2024) == [
        2019,
        2022,
        2023,
        2024,
    ]
    assert b._years(_cells({2018: 1.0, 2023: 1.0}, {}, measure="pmr_sector"), "pmr_sector", 2018, 2023) == [2018, 2023]


@pytest.mark.skipif(not (OUT / "benchmarks.parquet").exists(), reason="benchmarks not built")
def test_built_benchmarks_never_flag_a_low_rated_comparison():
    import pandas as pd

    s = pd.read_parquet(OUT / "benchmarks.parquet")
    assert not s[s["flag"]]["comparability"].eq("low").any()
    assert s[s["flag"]]["years"].min() >= 2
    assert set(s["status"]) <= {
        "flag",
        "outside, low comparability",
        "outside, fails leave-one-out",
        "outside, not persistent",
        "outside, average on the other side",
        "within the range",
        "too few years",
    }
    # Australia's gross birth rate is rated low (E-105, accepted in E-106), so it is never flagged
    assert not s[(s["measure"] == "birth_rate") & s["flag"]].shape[0]


@pytest.mark.skipif(
    __import__("shutil").which("Rscript") is None or not (OUT / "benchmarks.parquet").exists(),
    reason="R not installed, or benchmarks not built",
)
def test_r_cross_check_reproduces_the_benchmarks():
    import subprocess

    from alicia.pipeline import store

    done = subprocess.run(
        ["Rscript", "analysis/crosscheck_international_benchmarks.R"],
        cwd=store.ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    assert "CROSS-CHECK PASSED" in done.stdout
