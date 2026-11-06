"""Barriers to entry and profitability: the ATO company connector, the barriers classification, and the
website payloads built from them (``alicia.menu.competition``)."""

from __future__ import annotations

import openpyxl
import pandas as pd
import pytest

from alicia import anzsic, barriers
from alicia.pipeline import ato_company, store

ITEMS = (
    "Total income3\n$",
    "Total expenses\n$",
    "Total profit or loss\n$",
    "Taxable income or loss\n$",
    "Tax payable\n$",
    "Total assets\n$",
    "Total liabilities\n$",
    "Depreciation expenses\n$",
    "Interest expenses within Australia\n$",
    "Total salary and wage expenses\n$",
)


def _workbook(path, rows_4b, rows_4a, items=ITEMS):
    """A Company Table 4 workbook laid out as the ATO's: title row, blank row, headings, data."""
    wb = openpyxl.Workbook()
    wb.active.title = "Notes"
    b = wb.create_sheet("Table 4B")
    b.append(["Taxation statistics: Companies, key items by industry code"])
    b.append([])
    b.append(["Industry code4", "Broad industry2", "Fine industry2", "Business description", "Companies\nno.", *items])
    for r in rows_4b:
        b.append(r)
    a = wb.create_sheet("Table 4A")
    a.append(["Taxation statistics: Companies, key items by broad and fine industry"])
    a.append([])
    a.append(["Broad industry2", "Fine industry2", "Companies\nno.", *items])
    for r in rows_4a:
        a.append(r)
    wb.save(path)
    return path


def _items(income, profit, assets, liabilities):
    # income, expenses, profit, taxable, tax, assets, liabilities, depreciation, interest, wages ($)
    return [income, income - profit, profit, profit, profit * 0.3, assets, liabilities, 1e6, 2e6, 3e6]


def test_heading_strips_footnote_digits_and_line_breaks():
    assert ato_company.heading("Total income3\n$") == "total income $"
    assert ato_company.heading("Industry code4") == "industry code"
    assert ato_company.heading("Income tax liability 2018–19 $") == "income tax liability 2018–19 $"


def test_tables_4b_and_4a_are_read_summed_to_anzsic_and_totalled(tmp_path):
    path = _workbook(
        tmp_path / "t4.xlsx",
        rows_4b=[
            [62210, "K. Finance", "622 Depository", "Banking", 90, *_items(200e9, 50e9, 4000e9, 3700e9)],
            [62290, "K. Finance", "622 Depository", "Other Depository", 2000, *_items(20e9, 3e9, 300e9, 280e9)],
            [46231, "I. Transport", "462 Road Passenger", "Taxi Service Operation", 300, *_items(1e9, 0.1e9, 2e9, 1e9)],
            [46239, "I. Transport", "462 Road Passenger", "Other Road Transport", 200, *_items(1e9, 0.1e9, 2e9, 1e9)],
            [None, None, "Other", "Other", 1000, *_items(1e9, 0.5e9, 1e9, 0)],
        ],
        rows_4a=[
            ["K. Finance", "622 Depository Financial Intermediation", 2090, *_items(220e9, 53e9, 4300e9, 3980e9)],
            ["I. Transport", "Rail Freight and Passenger Transport", 40, *_items(9e9, 1e9, 20e9, 10e9)],
            ["Z. Other2", "Other2", 1000, *_items(1e9, 0.5e9, 1e9, 0)],
        ],
    )
    cls = ato_company.tidy_class(ato_company.read_by_code(path), 2022, "test")
    v = cls.set_index(["industry_code", "measure"])["value"]
    assert v[("6221", "total_income")] == pytest.approx(200_000)  # $ to AUD million
    assert v[("4623", "companies")] == 500  # 46231 + 46239 -> class 4623
    assert v[("", "total_income")] == pytest.approx(200_000 + 20_000 + 2_000 + 1_000)  # 'Other' is in the total
    assert set(cls["industry_level"]) == {"class", "total"}
    assert (cls["period"] == pd.Timestamp(2022, 7, 1)).all()

    grp = ato_company.tidy_group(ato_company.read_by_group(path), 2022, "test")
    levels = grp.drop_duplicates("industry_code").set_index("industry_code")["industry_level"].to_dict()
    assert levels == {"622": "group", "47": "subdivision", "": "total"}


def test_a_workbook_without_the_balance_sheet_is_refused(tmp_path):
    items = tuple(i for i in ITEMS if not i.startswith("Total assets"))
    path = _workbook(tmp_path / "t4.xlsx", [[62210, "K", "622", "Banking", 1, *range(9)]], [], items=items)
    with pytest.raises(ato_company.LayoutError, match="total_assets"):
        ato_company.read_by_code(path)


def test_barriers_classification_is_valid_and_follows_grattans_sectors():
    assert barriers.check() == []
    named = {
        "2630": "natural_monopoly",  # electricity distribution
        "5220": "natural_monopoly",  # airports
        "5299": "low_barriers",  # toll roads share the class with many small transport-support firms
        "5801": "natural_monopoly",  # wired telecommunications
        "4110": "scale_economies",  # supermarkets
        "4900": "scale_economies",  # airlines
        "5910": "scale_economies",  # internet service providers
        "6221": "heavy_regulation",  # banks
        "4271": "heavy_regulation",  # pharmacies
        "9209": "heavy_regulation",  # sports betting
        "6910": "low_barriers",  # legal services (division default)
        "0600": "tradeable",  # coal mining
        "8401": "public",  # hospitals
    }
    assert {c: barriers.group(c) for c in named} == named
    # Every ANZSIC class has a group.
    classes = [c for c in anzsic._codes() if len(c) == 4]
    assert all(barriers.group(c) in barriers.GROUPS for c in classes)


def test_sectors_merge_listed_classes_and_label_split_groups():
    assert barriers.sector("6221") == barriers.sector("6229") == ("6221", "Banks and other deposit-takers")
    assert barriers.sector("4123") == ("4123", "Liquor retailing")
    assert barriers.sector("4121") == ("412", "Specialised food retailing, other")
    assert barriers.sector("0111") == ("011", "Nursery and floriculture production")


def test_aggregate_group_follows_the_listing_then_the_weights_then_the_count():
    assert barriers.aggregate_group("47", {}) == "natural_monopoly"  # listed itself
    assert barriers.aggregate_group("412", {"4123": 9.0, "4121": 3.0, "4122": 2.0}) == "scale_economies"
    assert barriers.aggregate_group("412", {"4123": 1.0, "4121": 3.0}) == "low_barriers"
    assert barriers.aggregate_group("412", {}) == "low_barriers"  # three of its four classes


needs_ato = pytest.mark.skipif(
    not (store.PROCESSED / "ato_company" / "class_fy.parquet").exists(), reason="ATO company panels not built"
)


@needs_ato
def test_ato_panels_cover_the_income_years_with_every_item():
    cls = store.read_panel("ato_company", "class_fy")
    grp = store.read_panel("ato_company", "group_fy")
    assert sorted(cls["period"].dt.year.unique()) == list(range(2018, 2023))
    assert sorted(grp["period"].dt.year.unique()) == list(range(2014, 2023))
    assert set(cls["measure"]) == set(ato_company.MEASURES) == set(grp["measure"])
    # Companies' total equity is positive and in the trillions of dollars.
    tot = cls[(cls["industry_level"] == "total") & (cls["period"].dt.year == 2022)].set_index("measure")["value"]
    assert 1e6 < tot["total_assets"] - tot["total_liabilities"] < 1e7  # AUD million


@needs_ato
def test_profit_payload_sectors_are_aligned_and_banks_use_the_group_table():
    from alicia.menu import competition

    p = competition.profit_payload()
    n = len(p["years"])
    for s in p["sectors"]:
        assert all(len(s[k]) == n for k in ("income", "pbt", "npat", "equity")), s["key"]
        assert s["group"] in barriers.GROUPS
    banks = next(s for s in p["sectors"] if s["label"] == "Banks and other deposit-takers")
    assert banks["basis"] == "group" and banks["codes"] == ["622"]
    # Table 4B leaves banking out in 2018-19; the group table has it, with equity in the hundreds of billions.
    assert banks["equity"][p["years"].index(2018)] > 100_000
    # 2021-22: published liabilities exceed assets, so the page leaves that year out (equity <= 0).
    assert banks["equity"][p["years"].index(2021)] < 0
    s = p["series"]
    assert all(len(v) == len(s["years"]) for g in s["groups"].values() for v in g.values())
    assert any(e["code"] == "622" and e["year"] == 2021 for e in s["excluded"])
    assert p["yields"]["periods"][0] == "2013-05" and all(0 < v < 10 for v in p["yields"]["values"])


@needs_ato
def test_barriers_payload_counts_employing_businesses_within_all_businesses():
    from alicia.menu import competition

    b = competition.barriers_payload()
    years = b["bizYears"]
    for scope in ("all", "employing"):
        assert set(b["bizGroup"][scope]) == {*ato_company.schema.STATES, "AUS"}
        for g, cell in b["bizGroup"][scope]["AUS"].items():
            assert g in barriers.GROUPS and all(len(cell[k]) == len(years) for k in cell)
    i = years.index(2020)
    for g in barriers.GROUPS:
        e, a = b["bizGroup"]["employing"]["AUS"][g], b["bizGroup"]["all"]["AUS"][g]
        assert 0 < e["start"][i] < a["start"][i] and e["entries"][i] < a["entries"][i]
    # Australia is the sum of the states.
    nsw_plus = sum(b["bizGroup"]["all"][s]["low_barriers"]["entries"][i] for s in ato_company.schema.STATES)
    assert nsw_plus == b["bizGroup"]["all"]["AUS"]["low_barriers"]["entries"][i]
    # Every group can be broken into its sectors, for Australia and each state; the states add up to Australia.
    info = b["bizSectorInfo"]
    assert {g for _, g in info.values()} == set(barriers.GROUPS)
    assert set(b["bizSector"]["employing"]) <= set(info)
    for scope in ("all", "employing"):
        assert set(b["bizSectorState"][scope]) == set(ato_company.schema.STATES)
    key = next(k for k, (label, g) in info.items() if label == "Supermarkets")
    by_state = sum(
        b["bizSectorState"]["all"][s].get(key, {}).get("entries", [0] * len(years))[i] or 0
        for s in ato_company.schema.STATES
    )
    assert by_state == b["bizSector"]["all"][key]["entries"][i]
    assert set(next(iter(b["bizSectorState"]["all"]["NSW"].values()))) == {"start", "entries", "exits"}
