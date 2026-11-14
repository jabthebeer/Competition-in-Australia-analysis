"""The Industry lens (beta): framework marks placed by market position, the page's data, and the state map."""

from __future__ import annotations

import json
import re

from alicia.menu import growth, lens
from alicia.pipeline import boundaries
from alicia.register import competition as C
from alicia.register.catalogue import load_records
from alicia.register.requirements import load_requirements
from alicia.register.schema import Assessment, DriverMark


def assessment(*marks) -> Assessment:
    ms = [DriverMark.model_validate(m) for m in marks]
    top = max(ms, key=lambda m: abs(m.mark))
    return Assessment.model_validate(
        {
            "summary": "x",
            "marks": [m.model_dump() for m in ms],
            "main_driver": top.driver,
            "reach": "narrow",
            "confidence": "low",
            "assessed_on": "2026-11-07",
        }
    )


def mark(driver, value, **kw):
    return {"driver": driver, "mark": value, "reason": "because"} | kw


def test_each_driver_has_a_column_and_bans_or_caps_also_reach_the_largest_players():
    assert set(C.DRIVER_POSITIONS) == {
        "entry-exit",
        "competition",
        "market-integration",
        "capital",
        "labour",
        "burden",
        "innovation",
        "prices-taxes",
    }
    dm = DriverMark.model_validate
    assert C.positions(dm(mark("entry-exit", -1))) == ("entrants",)
    assert C.positions(dm(mark("entry-exit", -2))) == ("entrants", "dominant")  # an exclusive right shelters incumbents
    assert C.positions(dm(mark("burden", -1))) == ("smaller",)
    assert C.positions(dm(mark("competition", 1))) == ("smaller", "dominant")
    assert C.positions(dm(mark("entry-exit", -1, positions=["smaller"]))) == ("smaller",)  # a growth threshold


def test_a_column_adds_up_its_marks_and_flags_mixed_ones():
    cells = C.effects(assessment(mark("labour", 1), mark("burden", -1), mark("entry-exit", -2)))
    assert cells["smaller"]["effect"] == "mixed" and len(cells["smaller"]["marks"]) == 2
    # The same ±2 entry mark lands with entrants and with monopolies and oligopolies; each cell words it for its own
    # position (DECISIONS E-137).
    same = ("effect", "strength", "marks")
    assert [cells["entrants"][k] for k in same] == [cells["dominant"][k] for k in same]
    assert cells["entrants"]["effect"] == "negative"
    assert cells["entrants"]["phrase"] == "Harder to start up or enter"
    assert cells["dominant"]["phrase"] == "Shelters monopolies and oligopolies from rivals"
    assert cells["smaller"]["phrase"] == C.EFFECT_PHRASES["smaller"]["mixed"]
    assert cells["entrants"]["strength"] == "strong" and cells["smaller"]["strength"] == "weak"
    placed = C.placed_marks(assessment(mark("competition", 1)))
    assert placed == [{"driver": "Competition", "mark": 1, "reason": "because", "positions": ["smaller", "dominant"]}]


def test_every_requirement_is_assessed_and_agrees_with_the_register_on_the_same_law():
    records = {r.id: r for r in load_records().records}
    reqs = load_requirements().requirements
    assert len(reqs) >= 159 and all(q.assessment.framework == "1.0" for q in reqs)
    for q in reqs:
        for rid in q.records:
            r = records[rid]
            if r.kind == "setting" and r.family == "payroll-tax":  # requirements mirror the payroll tax settings
                assert {(m.driver, m.mark) for m in q.assessment.marks} == {
                    (m.driver, m.mark) for m in r.assessment.marks
                }
                growth_mark = next(m for m in q.assessment.marks if m.driver == "entry-exit")
                assert growth_mark.positions == ("smaller",)
    unmarked = [q.id for q in reqs if not q.assessment.marks]
    assert unmarked and all(
        q.assessment.main_driver is None and q.assessment.summary for q in reqs if not q.assessment.marks
    )


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
    assert p["markLabels"]["-2"] == "Major harm" and p["classes"][0]["mark"] == ""
    assert len(p["map"]["areas"]) == 8 and all(a["path"].startswith("M") for a in p["map"]["areas"])
    ids = {r["id"] for r in p["rows"]}
    assert {"nsw-food-business-registration", "cth-gst-registration"} <= ids
    assert not ids & {r.id for r in records if r.ended is not None}  # repealed or replaced items are left out
    assert all((lens.ROOT / r["file"]).exists() for r in p["rows"])
    post = next(r for r in p["rows"] if r["id"] == "cth-postal-reserved-services")
    assert post["marks"][0]["positions"] == ["entrants", "dominant"] and post["framework"]["total"] == -2
    gst = next(r for r in p["rows"] if r["id"] == "cth-gst-registration")
    assert gst["reach"][0]["classes"] == "all" and {tuple(m["positions"]) for m in gst["marks"]} == {("smaller",)}
    mixed = next(
        r for r in p["rows"] if r["type"] == "requirement" and r["framework"].get("total") == 0 and r.get("marks")
    )
    assert "total" in mixed["framework"]  # a total of 0 is kept, not dropped as empty


def test_the_page_renders_with_no_placeholders_left_and_is_linked_from_the_landing_page():
    html = growth.render(lens.PAGE[0], lens.payload(load_records().records), lens.PAGE[0], standalone=True)
    assert not re.search(r"__[A-Z_]+__", html) and "<title>ALICIA Industry lens (beta)</title>" in html
    link = (
        r'<a href="industry-lens.html" aria-current="page"[^>]*>'
        r'Industry lens <span class="beta-tag">\(beta\)</span></a>'
    )
    assert re.search(link, html)
    assert '<h1>Industry lens <span class="beta">' in html and 'class="beta-tip"' in html
    data = json.loads(re.search(r'id="page-data">(.*?)</script>', html, re.S).group(1))
    assert data["default"] == {"division": "H", "class": "", "state": "NSW"}  # a division first; its classes are tags
    assert '<a class="view-link" href="industry-lens.html"' in growth.landing({"industry-lens.html"})


def test_the_state_map_is_projected_into_a_1000_wide_frame():
    canberra, sydney, perth = (
        boundaries.albers(149.13, -35.28),
        boundaries.albers(151.21, -33.87),
        boundaries.albers(115.86, -31.95),
    )
    assert perth[0] < canberra[0] < sydney[0] and canberra[1] < sydney[1]  # west to east; Canberra south of Sydney
    square = [[[140, -30], [150, -30], [150, -40], [140, -40], [140, -30]]]
    islet = [[[145, -42], [145.001, -42], [145.001, -42.001], [145, -42]]]
    geo = {
        "features": [
            {
                "properties": {"state_code_2021": "1", "state_name_2021": "New South Wales"},
                "geometry": {"type": "MultiPolygon", "coordinates": [square, islet]},
            }
        ]
    }
    m = boundaries.svg_map(geo, "STE")
    area = m["areas"][0]
    assert (
        m["viewBox"].startswith("0 0 1000 ") and area["abbr"] == "NSW" and area["path"].count("M") == 1
    )  # islet dropped
    stored = json.loads(lens.MAP.read_text("utf-8"))
    assert {a["abbr"] for a in stored["areas"]} == {"NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"}


def test_market_structure_matches_its_sources_recomputed_independently():
    import pandas as pd

    m = lens.market()
    assert m["years"][0] == 2007 and len(m["years"]) == len(m["cabee"]["NSW"]["4511"][0])
    d = pd.read_parquet(lens.CABEE)
    for state, cls in (("NSW", "4511"), ("QLD", "7712"), ("WA", "0142")):
        x = d[(d.industry_level == "class") & (d.industry_code == cls) & (d.geo_code == state)]
        tot = x[(x.breakdown == "") & (x.period == x.period.max())].set_index("measure").value
        entry, exit_, sizes, counts = m["cabee"][state][cls]
        assert entry[-1] == round(100 * tot["entries"] / tot["businesses_start"], 1)
        assert exit_[-1] == round(100 * tot["exits"] / tot["businesses_start"], 1)
        assert counts == [
            int(tot["businesses_start"]),
            int(tot["entries"]),
            int(tot["exits"]),
            int(tot["businesses_end"]),
        ]
        ends = (
            x[(x.breakdown != "") & (x.measure == "businesses_end") & (x.period == x.period.max())]
            .set_index("breakdown")
            .value
        )
        assert sizes == [int(ends[b]) for b in lens.SIZE_BANDS]
    rates = [v for st in m["cabee"].values() for row in st.values() for v in row[0] + row[1] if v is not None]
    assert rates and min(rates) >= 0
    ai = json.loads(lens.AUS_INDUSTRY.read_text("utf-8"))["tables"]["size_division"]["rows"]
    h = {r["size_band"]: r["sales"] for r in ai if r["anzsic"] == "H" and r["fy"] == m["sizeSalesYear"]}
    assert m["sizeSales"]["H"] == {
        "under20": h["0-4"] + h["5-19"],
        "20-199": h["20-199"],
        "200+": h["200+"],
        "total": h["total"],
    }
    assert "K" not in m["sizeSales"]  # finance and insurance is not in the ABS size table
    rba = json.loads(lens.RBA.read_text("utf-8"))["tables"]["concentration"]["rows"]
    last_h = max(
        (r for r in rba if r["division"] == "H" and r.get("top4_weighted") is not None), key=lambda r: r["fyear"]
    )
    assert m["top4"]["H"]["years"][-1] == last_h["fyear"] and m["top4"]["H"]["weighted"][-1] == round(
        100 * last_h["top4_weighted"], 1
    )


def test_division_figures_are_the_sum_of_their_classes():
    m = lens.market()
    divs = {c["code"]: c["division"] for c in lens.classes()}
    h = m["cabeeDivision"]["NSW"]["H"]
    rows = [v for k, v in m["cabee"]["NSW"].items() if divs[k] == "H"]
    assert h[3][0] == sum(r[3][0] or 0 for r in rows) and h[3][1] == sum(r[3][1] or 0 for r in rows)
    assert h[2] == [sum((r[2] or [0, 0, 0, 0])[i] or 0 for r in rows) for i in range(4)]
    assert h[0][-1] == round(100 * h[3][1] / h[3][0], 1)


def test_every_requirement_reaches_all_the_classes_its_law_covers():
    reqs = {q.id: q for q in load_requirements().requirements}
    assert not [q.id for q in reqs.values() if any("Calibration" in (r.note or "") for r in q.reach)]
    from alicia.register.requirements import reach_classes

    def classes(i):
        return {c for r in reqs[i].reach for c in reach_classes(r)}

    retail = classes("cth-award-ma000004")
    assert {"4110", "4251", "4260", "4310", "1174"} <= retail  # the award's own definition of general retail
    assert not retail & {"3911", "4000", "4511"}  # vehicles, fuel and food services are excluded (cl 4.2)
    assert {"3011", "3020", "3222"} <= classes("cth-award-ma000020") and "3232" not in classes("cth-award-ma000020")
    assert "3020" in classes("qld-builder-licence") and "3020" not in classes("nsw-builder-licence")
    assert {"4123", "4520", "4511"} <= classes("vic-liquor-licence")


def test_award_coverage_checked_against_the_awards_text_is_sourced_clause_by_clause():
    reqs = {q.id: q for q in load_requirements().requirements}

    def entry(i, cls):
        return next(r for r in reqs[i].reach if cls in r.classes)

    def quoted(i, cls, words):
        return any(words in s.quote for s in entry(i, cls).sources)

    # Mining: exploration is covered only on a lease (cl 4.3(a)(x)); salt and quarrying are excluded (cl 4.3(a))
    assert entry("cth-award-ma000011", "1012").condition and quoted(
        "cth-award-ma000011", "1012", "which is not on a mining lease or tenement"
    )
    assert entry("cth-award-ma000011", "0990").condition and quoted("cth-award-ma000011", "0990", "(vii) salt;")
    # Building: landscaping only with building works (cl 4.3(a)(ii)); electrical and plumbing awards excluded (cl 4.4)
    assert entry("cth-award-ma000020", "3291").condition and quoted("cth-award-ma000020", "3291", "landscaping")
    assert quoted("cth-award-ma000020", "3011", "Plumbing and Fire Sprinklers Award 2020")
    # Pastoral: cotton is a broadacre field crop (cl 4.2(e)), not excluded; horticulture is (cl 4.3)
    assert entry("cth-award-ma000035", "0152").condition and quoted("cth-award-ma000035", "0142", "Wine Industry Award")
    for q in reqs.values():  # every condition on an award cites the clause it rests on
        if q.id.startswith("cth-award-"):
            assert all("cl " in r.condition for r in q.reach if r.condition), q.id


def test_items_assessed_as_economy_wide_reach_every_industry_on_the_lens():
    p = lens.payload(load_records().records)
    rows = {r["id"]: r for r in p["rows"]}
    assert rows["nsw-insurance-duty"].get("economyWide") and rows["nsw-planning-zoning"].get("economyWide")
    assert not rows["cth-pharmacy-location-rules"].get("economyWide")


def test_the_page_leads_with_pain_points_and_overlap_and_names_who_administers_each_law():
    # Owner, 12 November 2026 (DECISIONS E-150): no lede; pain points, regulatory overlap, the industry's own laws and
    # the across-states view come before the framework table and the market figures.
    html = growth.render(lens.PAGE[0], lens.payload(load_records().records), lens.PAGE[0], standalone=True)
    assert 'class="lede"' not in html and 'class="toc"' in html
    order = ["h-pain", "h-overlap", "h-laws", "h-states", "h-table", "h-market"]
    at = [html.index(f'<h2 id="{i}">') for i in order]
    assert at == sorted(at)
    p = lens.payload(load_records().records)
    rows = {r["id"]: r for r in p["rows"]}
    food = rows["nsw-food-business-registration"]
    assert food["family"] == "food-business-registration" and food["regime"] == "food-safety"
    assert {a["who"] for a in food["admin"]} == {"NSW Food Authority", "Local councils"}
    assert food["overlap"] == {"Licenses, registers or accredits": ["NSW Food Authority", "Local councils"]}
    assert food["stages"] == ["start"]
    assert "overlap" not in rows["cth-gst-registration"]  # no overlap is dropped, not kept as an empty object
    regimes = {g["id"]: g for g in p["regimes"]}
    assert regimes["food-safety"]["issues"] and all(i["pub"] and i["quote"] for i in regimes["food-safety"]["issues"])
    assert all(i["status"] != "addressed" for g in p["regimes"] for i in g.get("issues", []))
    logged = json.loads((lens.default_register_dir() / "requirement-gaps.json").read_text("utf-8"))["gaps"]
    assert p["gaps"] and all(p["gaps"][g["family"]][g["jurisdiction"]] == g["status"] for g in logged)
    assert set(p["businessFacing"]) < set(p["functions"])
