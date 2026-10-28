"""Costing parameters (alicia.costing): parsers on SYNTHETIC slices of each publisher's layout, the merge, the
refresh logic with stubbed discovery (no network), the committed parameters.json and the register export.

Every table, workbook and CSV built here is synthetic: invented numbers in the publishers' layouts."""

from __future__ import annotations

import io
import json
import zipfile
from types import SimpleNamespace

import openpyxl
import pandas as pd
import pytest

from alicia.costing import (
    abs_anzsic,
    abs_asna,
    abs_australian_industry,
    abs_bcs,
    abs_berd,
    abs_cabee_latest,
    abs_capex,
    abs_cube,
    abs_eeh,
    abs_io,
    abs_mfp,
    abs_osca,
    base,
    oecd_fdi_rri,
    oecd_pmr,
    oecd_stri,
    params,
    pc_national,
    rba_hf2025,
    register,
)
from alicia.pipeline import store
from alicia.register.catalogue import load_records
from alicia.register.evaluation import load_evaluations

REPO_PARAMS = store.PROCESSED / "costing" / "parameters.json"


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """data/raw, data/processed and data/manifests under a temporary root."""
    for name, sub in (
        ("ROOT", ""),
        ("RAW", "data/raw"),
        ("PROCESSED", "data/processed"),
        ("MANIFESTS", "data/manifests"),
    ):
        monkeypatch.setattr(store, name, tmp_path / sub if sub else tmp_path)
    return tmp_path


def put_file(source: base.Source, release: base.Release, i: int, content: bytes) -> None:
    """Write a release's raw file as if downloaded, and record it in the manifest."""
    path = base.local_path(source.id, release.files[i])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    store.record_download(source.id, path, release.files[i].url, source.licence)


def xlsx(sheets: dict[str, list[list]]) -> bytes:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(name)
        for r in rows:
            ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def release(source: base.Source, *names: str, rid: str = "r1", date: str | None = "2026-01-01") -> base.Release:
    return base.Release(
        id=rid,
        date=date,
        files=tuple(base.RemoteFile(f"{rid}/{n}", f"https://example.org/{rid}/{n}") for n in names),
        page="https://example.org/latest-release",
    )


# ---------------------------------------------------------------- base


def test_num_keeps_integers_exact_and_rounds_floats():
    assert base.num(24410463.0) == 24410463 and isinstance(base.num(24410463.0), int)
    assert base.num(0.29420157894080373) == 0.2942016
    assert base.num(24410463.4) == 24410463
    assert base.num(float("nan")) is None
    assert base.num("text") == "text" and base.num(None) is None and base.num(True) is True


def test_value_reads_markers_as_null():
    assert base.value("np") is None and base.value("na") is None and base.value("") is None
    assert base.value("1,234.5") == 1234.5 and base.value("12.3^") == 12.3 and base.value(7) == 7.0


def test_dumps_is_deterministic_and_round_trips():
    doc = {"tables": {"b": {"rows": [{"y": 1, "x": "a"}], "columns": {"x": "text"}}, "a": {"rows": []}}, "schema": "s"}
    text = base.dumps(doc)
    assert json.loads(text) == doc
    assert text == base.dumps(json.loads(text))
    assert '\n{"x":"a","y":1}\n' in text  # one row per line, keys sorted


def test_table_finish_checks_columns_keys_and_sorts():
    t = base.Table("d", {"k": "code", "v": "count"}, ("k",), [{"k": "b", "v": 2.0}, {"k": "a", "v": 1.5}])
    assert [r["k"] for r in t.finish().rows] == ["a", "b"] and t.rows[1]["v"] == 2
    with pytest.raises(ValueError, match="duplicate"):
        base.Table("d", {"k": "code"}, ("k",), [{"k": "a"}, {"k": "a"}]).finish()
    with pytest.raises(ValueError, match="differ"):
        base.Table("d", {"k": "code"}, ("k",), [{"k": "a", "extra": 1}]).finish()


def test_is_newer_compares_release_fingerprints():
    old = {"release": release(abs_asna.SOURCE, "a.xlsx", rid="2024-25", date="2025-10-24").to_json()}
    assert not base.is_newer(base.Release.from_json(old["release"]), old)
    assert base.is_newer(release(abs_asna.SOURCE, "a.xlsx", rid="2025-26", date="2026-10-23"), old)
    assert not base.is_newer(release(abs_asna.SOURCE, "a.xlsx", rid="2023-24", date="2024-10-24"), old)
    # same release, a file added (CABEE cube 2 in December)
    assert base.is_newer(release(abs_asna.SOURCE, "a.xlsx", "b.xlsx", rid="2024-25", date="2025-10-24"), old)
    assert base.is_newer(release(abs_asna.SOURCE, "a.xlsx"), None)


ABS_PAGE = """<html><body>
<a href="/statistics/x/2024-25/5204005_GVA_by_Industry.xlsx">t5</a>
<a href="/statistics/x/jul2021-jun2025">previous</a>
<p>Reference period July 2022 - June 2026</p><p>Released 18/08/2026</p>
<p>Release date and time 18/12/2026 11:30am AEDT</p><p>Next release 18/12/2027</p>
<p>Reference year for chain volume measures and real income measures is 2024-25.</p></body></html>"""


def test_abs_page_reads_release_dates_and_links(monkeypatch):
    monkeypatch.setattr(base, "get", lambda url, accept=None: SimpleNamespace(text=ABS_PAGE))
    p = base.abs_page("https://www.abs.gov.au/x/latest-release")
    assert p.reference_period == "July 2022 - June 2026"
    assert p.released == "2026-12-18"  # the later of 'Released' and an update
    assert p.next_release == "2027-12-18"
    assert p.files(r"/5204005_GVA_by_Industry\.xlsx$") == [
        "https://www.abs.gov.au/statistics/x/2024-25/5204005_GVA_by_Industry.xlsx"
    ]
    f = base.remote(p.files(r"\.xlsx$")[0])
    assert f.name == "2024-25/5204005_GVA_by_Industry.xlsx"


# ---------------------------------------------------------------- connectors, on synthetic slices


def test_anzsic_codelist_from_bundle():
    t = abs_anzsic.build(base.Release("CL_ANZSIC_2006 1.1.0", None, (), "https://example.org")).get("codes").finish()
    levels = pd.Series([r["level"] for r in t.rows]).value_counts().to_dict()
    assert levels == {"class": 506, "group": 214, "subdivision": 86, "division": 19}
    row = next(r for r in t.rows if r["code"] == "4511")
    assert row["division"] == "H" and row["parent"] == "451"


def tsw(series: dict[str, dict[int, float]], unit: str = "$ Millions") -> pd.DataFrame:
    """A long frame as abs_tsw.read returns it: description, unit, date (June of each year), value."""
    rows = [
        {"description": d, "unit": unit, "date": pd.Timestamp(f"{y}-06-01"), "value": v}
        for d, vals in series.items()
        for y, v in vals.items()
    ]
    return pd.DataFrame(rows)


def test_asna_tables_from_series_descriptions():
    t5 = abs_asna.tidy(
        tsw(
            {
                "Mining (B) ;  Current prices ;": {2025: 100.0, 2026: 110.0},
                "Mining (B) ;  Chain volume measures ;": {2025: 99.0, 2026: 101.0},
                "Mining (B) ;  Percentage of GVA at basic prices, current prices ;": {2025: 10.0, 2026: 11.0},
                "Mining (B) ;  Coal mining: Chain volume measures ;": {2026: 50.0},  # sub-industry, not kept
                "All industries ;  Current prices ;": {2025: 1000.0, 2026: 1000.0},
                "Gross value added at basic prices: Chain volume measures ;": {2025: 990.0, 2026: 995.0},
                "Gross domestic product: Current prices ;": {2025: 1100.0, 2026: 1150.0},
                "Gross domestic product: Chain volume measures ;": {2025: 1090.0, 2026: 1120.0},
            }
        )
    )
    tables = abs_asna.gva_tables(t5, "2024-25")
    gva = {(r["anzsic"], r["fy"]): r for r in tables["gva"].finish().rows}
    assert gva[("B", "2025-26")]["gva_current"] == 110 and gva[("B", "2025-26")]["gva_share_pct"] == 11
    assert gva[("TOT", "2024-25")]["gva_cvm"] == 990
    assert "reference year 2024-25" in tables["gva"].columns["gva_cvm"]
    assert tables["gdp"].finish().rows[-1] == {"fy": "2025-26", "gdp_current": 1150, "gdp_cvm": 1120}
    t46 = abs_asna.tidy(
        tsw(
            {
                "Mining ;  Compensation of employees ;": {2026: 30.0},
                "Mining ;  Gross operating surplus and gross mixed income ;": {2026: 70.0},
                "Mining ;  Total factor income ;": {2026: 100.0},
            }
        )
    )
    t48 = abs_asna.tidy(tsw({"Wages and salaries ;  Mining ;": {2026: 27.0}}))
    row = abs_asna.factor_table(t46, t48).finish().rows[0]
    assert row["labour_share"] == 0.3 and row["wages"] == 27 and row["anzsic"] == "B"
    with pytest.raises(ValueError, match="unrecognised industry"):
        abs_asna._wide(
            abs_asna.tidy(tsw({"Mystery ;  Total factor income ;": {2026: 1.0}})), {"Total factor income": "tfi"}, 2000
        )
    t1 = abs_asna.tidy(
        tsw(
            {
                "GDP per capita: Current prices ;": {2025: 100000.0, 2026: 105000.0},
                "GDP per capita: Chain volume measures ;": {2025: 101000.0, 2026: 102000.0},
                "Gross national income: Current prices ;": {2025: 2.5e6, 2026: 2.6e6},
                "GDP per capita: Chain volume measures - Percentage changes ;": {2026: 1.0},  # not kept
            }
        )
    )
    agg = abs_asna.aggregates_table(t1, "2024-25").finish()
    assert agg.rows[-1] == {
        "fy": "2025-26",
        "gdp_per_capita_current": 105000,
        "gdp_per_capita_cvm": 102000,
        "gni_current": 2.6e6,
    }
    with pytest.raises(ValueError, match="no series"):
        abs_asna.aggregates_table(abs_asna.tidy(tsw({"Terms of trade: Index ;": {2026: 100.0}})), "2024-25")


def cube(title: str, years: list[str], blocks: list[tuple[str | None, list[tuple[str, list]]]]) -> list[list]:
    """Rows of a 5260.0.55.002-style data cube sheet."""
    rows = [["Australian Bureau of Statistics"], [title], [], [None, *years]]
    for heading, data in blocks:
        if heading:
            rows.append([heading])
        rows += [[label, *vals] for label, vals in data]
    return rows + [["(a)\xa0Reference\xa0year\xa0for\xa0indexes\xa0is\xa02023-24 =\xa0100.0"], ["© Commonwealth"]]


def test_cube_reader_nests_block_headings():
    rows = cube(
        "Table 2",
        ["2022-23", "2023-24", "2024-25"],
        [
            ("Productivity indexes", [("\xa0\xa0Capital\xa0productivity", [101, 100, 99])]),
            ("Percentage changes to productivity indexes (d)", []),
            ("Productivity indexes", [("\xa0\xa0Capital\xa0productivity", [1.0, "na", -1.0])]),
        ],
    )
    data, notes = abs_cube.read(rows)
    assert data[0].path == ("Productivity indexes",) and data[0].values == {2023: 101.0, 2024: 100.0, 2025: 99.0}
    assert data[1].path == ("Percentage changes to productivity indexes", "Productivity indexes")
    assert data[1].values[2024] is None
    assert abs_cube.index_reference(notes) == "2023-24"
    assert abs_cube.industry_code("16\xa0Market\xa0sector\xa0industries\xa0(c)") == "MKT16"
    assert abs_cube.industry_code("Machinery & equipment - Computers") is None


def test_mfp_industry_and_capital_stock_tables():
    years = ["2022-23", "2023-24", "2024-25"]
    a = "A\xa0Agriculture,\xa0forestry\xa0and\xa0fishing"
    sheets = {}
    for sheet, sections in abs_mfp.INDEX_TABLES.items():
        sheets[sheet] = cube(sheet, years, [(h, [(a, [99, 100, 101])]) for h in sections])
    for sheet, sections in abs_mfp.SHARE_TABLES.items():
        sheets[sheet] = cube(sheet, years, [(h, [(a, [0.29, 0.3, 0.31])]) for h in sections])
    table, ref = abs_mfp.industry_table(sheets)
    row = table.finish().rows[-1]
    assert ref == "2023-24" and row["anzsic"] == "A" and row["fy"] == "2024-25"
    assert row["mfp_qa"] == 101 and row["capital_services"] == 101 and row["labour_income_share"] == 0.31
    assert table.columns["mfp_qa"] == "index (2023-24 = 100)"
    t12 = cube(
        "Table 12",
        years,
        [
            ("B Mining (incorporated)", [("Land", [10, 10, 10]), ("Non-dwelling construction", [5, 5, "np"])]),
            ("B Mining (unincorporated)", [("Land", [1, 1, 1])]),
        ],
    )
    pks = {r["fy"]: r for r in abs_mfp.capital_stock_table(t12).finish().rows}
    assert pks["2023-24"]["pks_all_assets"] == 16 and pks["2023-24"]["pks_fixed_assets"] == 5
    assert pks["2024-25"]["components_not_published"] == 1 and pks["2024-25"]["components"] == 3


AI_ITEMS = list(abs_australian_industry.ITEMS)


def test_australian_industry_tables():
    t1 = [
        ["Table 1 Key data by industry division and subdivision"],
        [None, *AI_ITEMS],
        [None, "'000", *["$m"] * 7],
        ["Mining"],
        ["06 Coal mining"],
        ["2024-25", 50.0, 1, 2, 3, 4, 5, 6, 7],
        ["Total mining"],
        ["2024-25", 60.0, 1, 2, 3, 4, 5, 6, 7],
        ["Auxiliary Finance and Insurance Services"],
        ["64 Auxiliary Finance and Insurance Services"],
        ["2024-25", 1.0, 1, 2, 3, 4, 5, 6, 7],
        ["Total selected industries"],
        ["2024-25", 100.0, 1, 2, 3, 4, 5, 6, 7],
    ]
    rows = {r["anzsic"]: r for r in abs_australian_industry.industry_table(t1).finish().rows}
    assert rows["06"]["level"] == "subdivision" and rows["06"]["employment"] == 50
    assert rows["B"]["level"] == "division" and rows["TOT"]["iva"] == 7 and rows["64"]["name"]
    names, years_, units = [None], [None], [None]
    for item in AI_ITEMS:
        names += [item, None]
        years_ += ["2023-24", "2024-25"]
        units += ["$m", "$m"] if item != "Employment at end of June" else ["'000", "'000"]
    t5 = [["Table 5"], names, years_, units, ["0–4 EMPLOYEES"], ["Mining", *range(16)], ["TOTAL"]]
    t5.append(["Total selected industries", *range(16)])
    size = {(r["anzsic"], r["size_band"], r["fy"]): r for r in abs_australian_industry.size_table(t5).finish().rows}
    assert size[("B", "0-4", "2024-25")]["employment"] == 1 and size[("B", "0-4", "2023-24")]["wages"] == 2
    assert size[("TOT", "total", "2024-25")]["iva"] == 15


CABEE_HEAD = [
    None,
    "Operating at start of financial year",
    "Entries - \nBirths",
    "Entries - \nOther",
    "Entries - \nTotal",
    "Exits - \nCancellations",
    "Exits - \nOther",
    "Exits - \nTotal",
    "Operating at end of financial year",
    "Change",
    "Percentage change",
    "Entry rate",
    "Exit rate",
]


def test_cabee_cube1_tables():
    t1 = [["Table 1"], [], [], CABEE_HEAD, [None, "no."], ["2025-26"]]
    t1 += [
        ["Mining", 100, 5, 5, 10, 4, 4, 8, 102, 2, 2.0, 10.0, 8.0],
        ["Currently Unknown", 3, 0, 0, 0, 1, 0, 1, 2, -1],
    ]
    t1 += [["All Industries", 103, 5, 5, 10, 5, 4, 9, 104, 1, 1.0, 9.7, 8.7]]
    rows = {r["anzsic"]: r for r in abs_cabee_latest.division_table(t1).finish().rows}
    assert rows["B"]["entries"] == 10 and rows["B"]["entry_rate_pct"] == 10 and rows["UNKNOWN"]["exit_rate_pct"] is None
    head13 = CABEE_HEAD[:8] + ["Net movement of surviving businesses"] + CABEE_HEAD[8:]
    t13 = [["Table 13"], [], [], head13, [None, "no."], ["2025-26"], ["Non–employing", 10, 1, 1, 2, 1, 0, 1, 0, 11]]
    t13 += [["Employing"], ["1–4", 5, 1, 0, 1, 0, 0, 0, -1, 5], ["Total", 15, 2, 1, 3, 1, 0, 1, 0, 16]]
    bands = {r["size_band"]: r for r in abs_cabee_latest.size_table(t13).finish().rows}
    assert set(bands) == {"nonemp", "1-4", "total"} and bands["1-4"]["net_movement"] == -1


def test_cabee_class_table_keeps_split_bands_and_aggregates():
    rows = []
    for state, k in (("NSW", 1), ("VIC", 2)):
        for band in ("1-4", "5-19", "total"):
            for measure, v in (("start", 100), ("entries", 10), ("exits", 5), ("end", 105)):
                rows.append(
                    {"fy": 2025, "state": state, "anzsic": "4511", "band": band, "measure": measure, "value": v * k}
                )
    t, fy, _ = abs_cabee_latest.class_table(pd.DataFrame(rows), "Jul 2021 to Jun 2025")
    out = {(r["anzsic"], r["size_band"]): r for r in t.finish().rows}
    assert fy == 2025 and out[("4511", "1-4")]["start"] == 300 and out[("4511", "1-4")]["entry_rate_pct"] == 10
    assert out[("45", "total")]["level"] == "subdivision" and out[("H", "5-19")]["exits"] == 15


def test_io_primary_inputs_employment_and_concordance():
    codes = [f"{i:04d}" for i in range(1101, 1151)]  # 50 synthetic IOIGs
    n = len(codes)
    t5 = [
        [None, "Use", *codes, None],
        [None, "Table 5", *[f"Industry {c}" for c in codes], "Total Industry Uses"],
        ["From Industry", None, *[None] * n, "T4"],
        ["T1", "Total Intermediate Use", *[10] * n, 10 * n],
        ["P1", "Compensation of employees", *[3] * n, 3 * n],
        ["P2", "Gross operating surplus mixed income", *[5] * n, 5 * n],
        ["P3", "Taxes less subsidies on products", *[1] * n, n],
        ["P4", "Other taxes less subsidies on production", *[1] * n, n],
        ["P5", "Complementary imports", *[0] * n, 0],
        ["P6", "Competing imports", *[2] * n, 2 * n],
        ["", "Australian Production", *[22] * n, 22 * n],
        ["", "Value Added", *[9] * n, 9 * n],
    ]
    flows, names = abs_io.primary_inputs(t5)
    assert flows["1101"]["gva"] == 9 and flows["TOT"]["coe"] == 150 and names["1150"] == "Industry 1150"
    jobs = abs_io.employment(
        [[None, None, "Full-time", "Part-time", "Full-time equivalent (b)"], ["1101", "x", 1.5, 0.5, 1.75]]
    )
    assert jobs["1101"] == {"employed_full_time": 1.5, "employed_part_time": 0.5, "employed_fte": 1.75}
    conc = [
        ["IOIG", "IOIG Descriptor", "ANZSIC Code", "ANZSIC Descriptor"],
        [101, "Sheep", 141, "x"],
        [None, None, 142, "y"],
    ]
    conc += [[1203, "Wine", 1213, "z"], [1204, "Tobacco", 1220, "w"]]
    pairs = [p | {"basis": "published"} for p in abs_io.concordance(conc)]
    assert pairs[0] == {"ioig": "0101", "anzsic": "0141", "basis": "published"} and len(pairs) == 4
    derived = abs_io.derived_pairs({"0101", "1205"}, pairs)
    assert {p["anzsic"] for p in derived} == {"1213", "1220"} and all(p["ioig"] == "1205" for p in derived)


def test_eeh_reads_all_ages_estimates_and_standard_errors():
    rows = [
        ["Table 6"],
        [None, "17 years and under", "All ages"],
        ["ESTIMATES"],
        ["AVERAGE HOURLY TOTAL CASH EARNINGS ($)"],
    ]
    rows += [["Under 20 employees", None, 43.0], ["STANDARD ERROR"], ["AVERAGE HOURLY TOTAL CASH EARNINGS ($)"]]
    rows += [["Under 20 employees", None, 0.5]]
    assert abs_eeh.read(rows) == {"Under 20 employees": {"hourly_cash_earnings": 43.0, "hourly_cash_earnings_se": 0.5}}


def test_bcs_reads_groups_and_categories():
    rows = [
        ["Table 7"],
        ["Characteristics of Australian Business"],
        [None, *abs_bcs.COMPETITION],
        [None, "%", "%", "%", "%"],
    ]
    rows += [["Total", 16.5, 12.2, 13.2, 58.2], ["Employment size"], ["0–4 persons", 20.6, 10.8, 11, 57.6]]
    rows += [["Industry"], ["Mining", 31.2, 16.2, "np", 42.2], ["Footnotes"], ["np not available"]]
    out = {(r["group"], r["category"]): r for r in abs_bcs.read(rows, abs_bcs.COMPETITION)}
    assert out[("total", "total")]["five_or_more"] == 58.2 and out[("size", "0-4")]["one_or_two"] == 10.8
    assert out[("industry", "B")]["three_or_four"] is None


def test_berd_subdivisions_with_unpublished_cells():
    rows = [["Table 1"], [None, *abs_berd.SIZES], [None, *["$'000"] * 5], ["2023-24"], ["Mining"]]
    rows += [["Coal mining", None, None, 5, None, 9], ["Total mining", 1, 2, 5, 3, 11], ["Total", 1, 2, 5, 3, 11]]
    out = {r["anzsic"]: r for r in abs_berd.table(rows, "2023-24").finish().rows}
    assert out["06"]["rd_20_199"] == 5 and out["06"]["rd_0_4"] is None and out["B"]["level"] == "division"
    assert out["TOT"]["rd_total"] == 11


def test_osca_licensing_flag_and_build(sandbox):
    assert abs_osca.licensing("Registration or licensing is required.") == ("required", None)
    flag, note = abs_osca.licensing("Registration or licensing may be required for certain services such as auditing.")
    assert flag == "may be required" and note.startswith("Registration")
    assert abs_osca.licensing(None) == (None, None)
    rel = release(abs_osca.SOURCE, "OSCA_Category_Descriptions.xlsx", rid="2024-version-1-0")
    head = [
        "Identifier",
        "Principal Title",
        "Alternative Title",
        "Lead Statement",
        "Registration or Licensing",
        "Skill Level",
    ]
    book = {
        "Contents ": [["OSCA Category Descriptions"], ["Released at 11:30am (Canberra time) 28 July 2025"]],
        "Table 1": [
            ["Table 1"],
            head,
            ["111131", "Manager", None, "x", None, 1],
            ["253111", "Doctor", None, "x", "Registration or licensing is required.", 1],
        ],
        "Table 2": [["Table 2"], ["Identifier", "Occupation Title"], [1, "Managers"], [1111, "Chief Executives"]],
    }
    put_file(abs_osca.SOURCE, rel, 0, xlsx(book))
    t = abs_osca.build(rel)
    occ = {r["osca"]: r for r in t["occupations"].finish().rows}
    assert occ["253111"]["licensing"] == "required" and occ["111131"]["unit_group"] == "1111"
    assert "released 28 July 2025" in t["occupations"].description
    assert {r["code"]: r["level"] for r in t["groups"].finish().rows} == {"1": "major group", "1111": "unit group"}


OECD_CSV = (
    "STRUCTURE,STRUCTURE_ID,STRUCTURE_NAME,ACTION,REF_AREA,Reference area,MEASURE,Measure,FREQ,"
    "Frequency of observation,TIME_PERIOD,Time period,OBS_VALUE,Observation value,UNIT_MEASURE,Unit of measure\n"
    "DATAFLOW,X,PMR,I,AUS,Australia,PMR,Product market regulation,A,Annual,2023,,1.346708,,0_TO_6,0-6 scale\n"
    "DATAFLOW,X,PMR,I,AUS,Australia,SECTPMR,Sector indicators,A,Annual,2023,,,,0_TO_6,0-6 scale\n"
)


def test_oecd_pmr_build_from_sdmx_csv(sandbox):
    rel = release(oecd_pmr.SOURCE, "oecd_pmr.csv", date=None)
    put_file(oecd_pmr.SOURCE, rel, 0, OECD_CSV.encode())
    rows = oecd_pmr.build(rel)["indicators"].finish().rows
    assert rows == [{"label": "Product market regulation", "measure": "PMR", "value": 1.346708, "year": 2023}]


def test_oecd_stri_and_fdi_rri_build(sandbox):
    stri = (
        "STRUCTURE,REF_AREA,ACTIVITY,Economic activity,STRI_TYPE,UNIT_MEASURE,TIME_PERIOD,OBS_VALUE\n"
        "DATAFLOW,AUS,H51,Air transport,MAIN_STRI,IX,2025,0.333\n"
    )
    rel = release(oecd_stri.SOURCE, "oecd_stri.csv", date=None)
    put_file(oecd_stri.SOURCE, rel, 0, stri.encode())
    assert oecd_stri.build(rel)["sectors"].finish().rows[0]["value"] == 0.333
    fdi = (
        "STRUCTURE,REF_AREA,ACTIVITY,Economic activity,POL_CAT,Policy category,MEASURE,UNIT_MEASURE,"
        "TIME_PERIOD,OBS_VALUE\n"
        "DATAFLOW,AUS,_T,Total,_T,Total,RR,IX,2025,0.244075\n"
        "DATAFLOW,AUS,_T,Total,CLAS1_2,Screening and approval,RR,IX,2025,0.2\n"
        "DATAFLOW,AUS,B,Mining,_T,Total,RR,IX,2025,0.1\n"
    )
    rel = release(oecd_fdi_rri.SOURCE, "oecd_fdi_rri.csv", date=None)
    put_file(oecd_fdi_rri.SOURCE, rel, 0, fdi.encode())
    t = oecd_fdi_rri.build(rel)
    assert len(t["sectors"].finish().rows) == 2 and len(t["restriction_types"].finish().rows) == 2


def test_capex_sums_complete_financial_years(sandbox):
    lines = [
        "STRUCTURE,MEASURE,PRICE_ADJUSTMENT,ASSET,INDUSTRY,Industry,TSEST,STATE,TIME_PERIOD,OBS_VALUE,UNIT_MULT,OBS_STATUS"
    ]
    for q, v in (("2024-Q3", 1), ("2024-Q4", 2), ("2025-Q1", 3), ("2025-Q2", 4), ("2025-Q3", 9)):
        for adj in ("CUR", "CVM"):
            flag = "x" if q == "2024-Q4" else ""
            lines.append(f"DATAFLOW,M1,{adj},TOT,P01,Mining,10,AUS,{q},{v},6,{flag}")
    rel = base.Release(
        "jun-2026",
        "2026-08-27",
        (base.RemoteFile("jun-2026/capex.csv", "https://example.org/capex.csv"),),
        "https://example.org",
        extra=(("last_quarter", "2025-Q3"),),
    )
    put_file(abs_capex.SOURCE, rel, 0, "\n".join(lines).encode())
    rows = abs_capex.build(rel)["actual_fy"].finish().rows
    assert rows == [
        {
            "anzsic": "B",
            "asset": "total",
            "capex_current": 10,
            "capex_cvm": 10,
            "flags": "x",
            "fy": "2024-25",
            "industry": "P01",
            "label": "Mining",
        }
    ]


def pc_tab(code: str, gdp: float, gsp: float) -> list[list]:
    rows = [[f"{code}: Title"], [], ["PC scenario code:", None, code], ["PC long name:", None, "Long name"]]
    rows += [["PC National sectors:", None, "Retail"], [], ["Scenario"], ["Capital productivity +0.1%"], []]
    rows += [["Macroeconomic results (%)"], ["Real GDP", None, gdp], ["Employment", None, 0], [None, None, None, "`"]]
    rows += [["Real GSP (%)"], *[[s, None, gsp] for s in pc_national.STATES], ["AUST", None, gsp]]
    return rows


def test_pc_national_parsers():
    s, labels = pc_national.simulation("L2_lower", pc_tab("L2", 0.07, 0.068))
    assert s["code"] == "L2" and s["variant"] == "lower" and s["real_gdp"] == 0.07 and s["real_gsp_wa"] == 0.068
    assert s["scenario"] == "Capital productivity +0.1%" and labels["real_gdp"] == "Real GDP"
    lin = [["Linearity"], ["Summary results"], [None, "GDP (%)", "CPI (%)", "National net revenue", "State"]]
    lin += [["L2 25%", 0.1, -0.05, 300, -35], ["L2 100%", 0.38, -0.19, 1200, -140]]
    out = pc_national.linearity("L2 - Linearity sensitivity test", lin)
    assert [r["share_pct"] for r in out] == [25, 100] and out[1]["national_net_revenue"] == 1200
    init = [
        ["Initial data"],
        [],
        ["Gross State Product, 2018-19 ($ million)"],
        [None, None, *pc_national.STATES, "Total"],
    ]
    init += [["Sheep", "1 ShpGranCattl", *[1.0] * 8, 8.0], ["Total", None, *[1.0] * 8, 8.0], []]
    rows = pc_national.initial_gsp(init)
    assert rows[0]["pcn_code"] == "ShpGranCattl" and rows[1]["pcn_no"] == 0 and rows[0]["wa"] == 1.0


def test_rba_markups_and_concentration_from_zip(sandbox):
    rel = release(rba_hf2025.SOURCE, "rdp.zip", date=None)
    markups = xlsx(
        {
            "aggr": [["fyear", "wing_m_DLW_tl_m_w_y"], [2004, 1.187293]],
            "div": [["fyear", "division", "wding_m_DLW_tl_m_w_y"], [2004, "A", 1.20321]],
        }
    )
    conc = xlsx(
        {
            "Overview": [["Sheet information"]],
            "all_top4share": [
                ["fyear", "wtop4share_go", "count_firm", "top4share_go_industry", "med_top4share_go", "industries"],
                [2002, 0.39, 1, 0.4, 0.34, 444],
            ],
            "div_top4share": [
                [
                    "fyear",
                    "division",
                    "wtop4share_go",
                    "count_firm",
                    "top4share_go_industry",
                    "med_top4share_go_industry",
                    "industries",
                ],
                [2002, "A", 0.12, 1, 0.22, 0.16, 49],
            ],
        }
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(rba_hf2025.MARKUPS, markups)
        z.writestr(rba_hf2025.CONCENTRATION, conc)
        z.writestr("Model/code.m", "% model code: never run")
    put_file(rba_hf2025.SOURCE, rel, 0, buf.getvalue())
    t = rba_hf2025.build(rel)
    assert {(r["division"], r["markup"]) for r in t["markups"].finish().rows} == {("TOT", 1.187293), ("A", 1.20321)}
    conc_rows = {r["division"]: r for r in t["concentration"].finish().rows}
    assert conc_rows["A"]["top4_weighted"] == 0.12 and conc_rows["TOT"]["top4_industries"] == 444
    assert conc_rows["A"]["hhi_weighted"] is None


# ---------------------------------------------------------------- refresh, merge and the command


def fake_connector(sid: str, rid: str, date: str, fail: str | None = None):
    """A connector whose discovery is stubbed (no network): one raw file and one table."""
    src = base.Source(sid, f"Title {sid}", "Publisher", "CC BY 4.0", f"https://example.org/{sid}")
    rel = release(src, "data.csv", rid=rid, date=date)

    def discover():
        if fail == "discover":
            raise ConnectionError("publisher unreachable")
        return rel

    def fetch(r):
        put_file(src, r, 0, f"value\n{rid}\n".encode())

    def build(r):
        if fail == "build":
            raise ValueError("layout changed")
        text = base.local_path(src.id, r.files[0]).read_text().splitlines()[1]
        return {
            "t": base.Table("A table.", {"release": "text", "n": "count"}, ("release",), [{"release": text, "n": 1}])
        }

    return SimpleNamespace(SOURCE=src, discover=discover, fetch=fetch, build=build)


def quiet(*_, **__):
    pass


def test_refresh_new_release_replaces_the_file(sandbox):
    assert params.run(refresh=True, conns=[fake_connector("s1", "2024-25", "2025-10-24")], log=quiet) == 0
    old = base.read_source_doc("s1")
    assert old["release"]["id"] == "2024-25" and old["tables"]["t"]["rows"][0]["release"] == "2024-25"
    # Unchanged release: nothing downloaded or rewritten.
    outcomes = [params.refresh_one(fake_connector("s1", "2024-25", "2025-10-24"), log=quiet)]
    assert outcomes[0].state == "unchanged"
    report = sandbox / "report.md"
    assert (
        params.run(refresh=True, conns=[fake_connector("s1", "2025-26", "2026-10-23")], report=str(report), log=quiet)
        == 0
    )
    new = base.read_source_doc("s1")
    assert new["release"]["id"] == "2025-26" and new["tables"]["t"]["rows"][0]["release"] == "2025-26"
    p = json.loads(params.params_path().read_text())
    assert p["vintage"] == "2026-10-23" and p["sources"][0]["status"] == "current"
    assert "2024-25 → 2025-26 | updated" in report.read_text()


@pytest.mark.parametrize("fail", ["discover", "build"])
def test_refresh_failure_falls_back_and_strict_exits_non_zero(sandbox, fail):
    params.run(refresh=True, conns=[fake_connector("s1", "2024-25", "2025-10-24")], log=quiet)
    committed = base.source_path("s1").read_text()
    broken = [fake_connector("s1", "2025-26", "2026-10-23", fail=fail)]
    report = sandbox / "report.md"
    assert params.run(refresh=True, conns=broken, report=str(report), log=quiet) == 0
    assert base.source_path("s1").read_text() == committed  # the committed file is kept
    p = json.loads(params.params_path().read_text())
    assert p["sources"][0]["status"] == "fallback" and p["sources"][0]["release"] == "2024-25"
    assert "failed:" in report.read_text()
    assert params.run(refresh=True, strict=True, conns=broken, log=quiet) == 1


def test_merge_is_deterministic_and_rebuild_is_identical(sandbox):
    conns = [fake_connector("s2", "b", "2026-02-01"), fake_connector("s1", "a", "2026-01-01")]
    params.run(refresh=True, conns=conns, log=quiet)
    first = params.params_path().read_bytes()
    params.run(rebuild=True, conns=conns, log=quiet)
    assert params.params_path().read_bytes() == first
    p = json.loads(first)
    assert [s["id"] for s in p["sources"]] == ["s2", "s1"]  # connector order
    assert list(p["tables"]) == ["s1.t", "s2.t"]


def test_rebuild_skips_sources_without_raw_files(sandbox):
    params.run(refresh=True, conns=[fake_connector("s1", "a", "2026-01-01")], log=quiet)
    for f in (sandbox / "data" / "raw" / "s1").rglob("*.csv"):
        f.unlink()
    assert params.rebuild_one(fake_connector("s1", "a", "2026-01-01")).state == "skipped"


def test_a_missing_source_fails_strict(sandbox):
    assert params.run(conns=[fake_connector("s1", "a", "2026-01-01")], strict=True, log=quiet) == 1


# ---------------------------------------------------------------- the committed parameters.json


@pytest.fixture(scope="module")
def committed():
    if not REPO_PARAMS.exists():
        pytest.skip("parameters.json not built")
    return json.loads(REPO_PARAMS.read_text("utf-8"))


def test_parameters_top_level_shape(committed):
    assert set(committed) == {"schema", "version", "vintage", "sources", "tables"}
    assert committed["schema"] == "alicia-costing-parameters" and committed["version"] == 1
    assert committed["vintage"] is None or isinstance(committed["vintage"], str)
    need = {
        "id",
        "title",
        "publisher",
        "release",
        "release_date",
        "next_release",
        "url",
        "files",
        "licence",
        "retrieved",
        "status",
    }
    for s in committed["sources"]:
        assert set(s) == need, s["id"]
        assert s["url"].startswith("https://") and s["status"] in ("current", "fallback")
        assert all(f["url"].startswith("https://") and len(f["sha256"]) == 64 for f in s["files"])
    assert {s["id"] for s in committed["sources"]} == set(params.CONNECTORS)


def test_every_table_declares_a_unit_for_every_column(committed):
    ids = {s["id"] for s in committed["sources"]}
    for tid, t in committed["tables"].items():
        assert set(t) == {"source", "description", "columns", "rows"}, tid
        assert t["source"] in ids and tid.startswith(t["source"] + ".")
        assert t["description"] and t["columns"] and t["rows"], tid
        assert all(isinstance(u, str) and u.strip() for u in t["columns"].values()), tid
        cols = set(t["columns"])
        assert all(set(r) == cols for r in t["rows"]), tid


def test_parameters_json_is_the_merge_of_the_committed_source_files(committed):
    merged = params.merge(params.load_connectors())
    assert base.dumps(merged) + "\n" == REPO_PARAMS.read_text("utf-8")


def test_committed_tables_have_expected_coverage(committed):
    t = committed["tables"]
    cabee = t["abs_cabee_latest.class_size"]["rows"]
    assert {r["size_band"] for r in cabee} == {"nonemp", "1-4", "5-19", "20-199", "200+", "total"}
    gov = {r["category"]: r["government_regulation"] for r in t["abs_bcs.barriers"]["rows"] if r["population"] == "all"}
    assert gov["total"] == 20.2 and gov["0-4"] == 17.3 and gov["200+"] == 29.1
    eeh = {r["employer_size"]: r["hourly_cash_earnings"] for r in t["abs_eeh.by_employer_size"]["rows"]}
    assert eeh["<20"] == 43 and eeh["1000+"] == 59.6
    lic = [r["licensing"] for r in t["abs_osca.occupations"]["rows"]]
    assert lic.count("required") == 187 and lic.count("may be required") == 196
    assert len(t["pc_national.initial_gsp"]["rows"]) == 115


# ---------------------------------------------------------------- the register export


def test_register_export():
    records = load_records().records
    evals = load_evaluations(records).evaluations
    doc = register.export(records, evals)
    assert doc["schema"] == "alicia-costing-register" and doc["version"] == 1
    assert [r["id"] for r in doc["records"]] == sorted(r.id for r in records if r.kind == "reform")
    fields = {
        "id",
        "title",
        "jurisdiction",
        "family",
        "direction",
        "direction_rationale",
        "direction_sources",
        "channels",
        "industries",
        "commencement",
        "commencement_is_primary",
        "review_status",
        "evaluation",
    }
    assert all(set(r) == fields for r in doc["records"])
    assert set(doc["channels"]) >= {c for r in doc["records"] for c in r["channels"]}
    evaluated = [r for r in doc["records"] if r["evaluation"]]
    assert evaluated and all(
        set(r["evaluation"]) == {"id", "verdict", "grade", "finding", "evaluated_on", "archived", "page"}
        for r in evaluated
    )
    assert base.dumps(doc) == base.dumps(register.export(records, evals))  # deterministic


def test_register_flags_records_with_only_archived_evaluations():
    records = load_records().records
    evals = load_evaluations(records).evaluations
    by_id = {e.id: e for e in evals}
    gone = {o for e in evals for o in e.supersedes}
    # A record covered by an archived evaluation and its successor only.
    new, old, rid = next(
        (e, by_id[o], rid)
        for e in evals
        for o in e.supersedes
        for rid in by_id[o].records
        if rid in e.records
        and not [x for x in evals if rid in x.records and x.id not in {o, e.id} and x.id not in gone]
    )
    # Drop the record from the newer evaluation's coverage: its archived evaluation is then shown, flagged.
    trimmed = new.model_copy(update={"records": tuple(r for r in new.records if r != rid) or ("x",)})
    doc = register.export(records, [trimmed if e.id == new.id else e for e in evals])
    entry = next(r for r in doc["records"] if r["id"] == rid)
    assert entry["evaluation"]["id"] == old.id and entry["evaluation"]["archived"] is True
