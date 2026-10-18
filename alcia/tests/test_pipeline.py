"""Common panel format, state lookup and coverage matching, on ILLUSTRATIVE panels (not real data)."""

from __future__ import annotations

import pandas as pd
import pytest

from alcia.pipeline import schema
from alcia.pipeline.coverage import coverage, summarise
from alcia.register.catalogue import load_records


def toy(**over) -> pd.DataFrame:
    base = {
        "measure": "entries",
        "unit": "count",
        "industry_scheme": "ANZSIC06",
        "industry_level": "class",
        "industry_code": "4610",
        "geo_level": "STE",
        "geo_code": "NSW",
        "period_type": "fy",
        "period": "2014-07-01",
        "value": 1.0,
    }
    base.update(over)
    return pd.DataFrame([base])


def test_make_validates_codes_levels_and_duplicates():
    ok = schema.make(toy(), source="toy")
    assert list(ok.columns) == list(schema.COLUMNS)
    with pytest.raises(schema.PanelError, match="state abbreviation"):
        schema.make(toy(geo_code="5"), source="toy")
    with pytest.raises(schema.PanelError, match="length does not match"):
        schema.make(toy(industry_code="461"), source="toy")
    with pytest.raises(schema.PanelError, match="duplicate"):
        schema.make(pd.concat([toy(), toy()]), source="toy")


def test_state_of_geographies():
    assert schema.state_of("POA", "2600") == "ACT"
    assert schema.state_of("POA", "2000") == "NSW"
    assert schema.state_of("POA", "0800") == "NT"
    assert schema.state_of("SA2", "211011251") == "VIC"
    assert schema.state_of("LGA", "50080") == "WA"
    assert schema.state_of("STE", "QLD") == "QLD"
    assert schema.anzsic_ancestors("4610") == ["4610", "461", "46", "I"]


def test_coverage_finds_the_finest_level_and_local_geography():
    record = next(r for r in load_records().records if r.id == "nsw-heavy-vehicle-national-law-2014")
    by_class = schema.make(
        pd.concat([toy(geo_code="NSW"), toy(geo_code="WA"), toy(industry_code="4621", geo_code="NSW")]), source="a"
    )
    by_division = schema.make(toy(industry_level="division", industry_code="I", measure="employed"), source="b")
    by_postcode = schema.make(
        pd.concat(
            [
                toy(industry_scheme="none", industry_level="total", industry_code="", geo_level="POA", geo_code=pc)
                for pc in ("2000", "3000")
            ]
        ),
        source="c",
    )
    catalogue = summarise(by_class, "a", "t") + summarise(by_division, "b", "t") + summarise(by_postcode, "c", "t")
    matches = {(m.source, m.industry): m for m in coverage(record, catalogue)}
    assert matches[("a", "4610")].matched_level == "class" and matches[("a", "4610")].state
    assert matches[("b", "4610")].matched_level == "division"
    assert matches[("c", "4610")].matched_level == "total" and matches[("c", "4610")].local_levels == ("POA",)


def test_retail_trade_codes_map_to_anzsic_and_states():
    """ILLUSTRATIVE SDMX-CSV rows (not real values)."""
    from alcia.pipeline import abs_retail, concord

    raw = pd.DataFrame(
        {
            "INDUSTRY": ["02", "01", "20", "41", "02"],
            "TSEST": ["10", "20", "10", "20", "10"],
            "REGION": ["5", "1", "AUS", "2", "9"],
            "FREQ": ["M", "M", "M", "Q", "M"],
            "TIME_PERIOD": ["2012-08", "2012-08", "2012-08", "2012-Q3", "2012-08"],
            "OBS_VALUE": ["1.0", "2.0", "3.0", "4.0", "5.0"],
        }
    )
    t = abs_retail.tidy(raw, "turnover", "AUD m", {"02": "Liquor retailing"}, "test")
    assert len(t) == 4  # Other Territories dropped
    first = t.iloc[0]
    assert (first.industry_level, first.industry_code, first.geo_code) == ("class", "4123", "WA")
    assert tuple(t.iloc[1][["industry_level", "industry_code"]]) == ("retail-group", "RT01")
    assert tuple(t.iloc[2][["industry_level", "geo_level"]]) == ("total", "AUS")
    assert t.iloc[3].period == pd.Timestamp("2012-07-01") and t.iloc[3].adjustment == "seasonally adjusted"
    assert "4110" in concord.composition()["RT01"] and concord.retail_classes("45")[-1] == "4320"
