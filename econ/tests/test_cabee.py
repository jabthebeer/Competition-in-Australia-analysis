"""CABEE stitching rules, on small ILLUSTRATIVE frames (not ABS data)."""

from __future__ import annotations

import pandas as pd

from regimpact.outcomes.cabee import Release, _fy_of_sheet, check_identity, stitch, to_rates

RELS = (
    Release("A", "2015-01-01", "https://example.invalid/a", 2014),
    Release("B", "2016-01-01", "https://example.invalid/b", 2015),
)


def rows(release, fy, start, entries, exits, end, balancing=0):
    base = {"release": release, "fy": fy, "state": "WA", "anzsic": "4110", "band": "total"}
    values = {"start": start, "entries": entries, "exits": exits, "balancing": balancing, "end": end}
    return [{**base, "measure": m, "value": v} for m, v in values.items()]


def test_sheet_names_map_to_financial_years():
    assert _fy_of_sheet("2008-09") == 2009
    assert _fy_of_sheet("June 2014") == 2014
    assert _fy_of_sheet("June 2014 a") == 2014
    assert _fy_of_sheet("June 2020 b") is None
    assert _fy_of_sheet("Contents") is None


def test_stitch_keeps_the_release_where_each_year_is_final():
    long = pd.DataFrame(
        rows("A", 2013, 100, 10, 8, 102)
        + rows("A", 2014, 102, 12, 9, 105)
        + rows("B", 2014, 102, 13, 9, 106)  # revised later: an overlap, not the panel value
        + rows("B", 2015, 106, 11, 10, 107)
    )
    panel, overlaps = stitch(long, RELS)
    chosen = panel[["release", "fy"]].drop_duplicates().sort_values("fy").values.tolist()
    # 2013 is final in no release, so the earliest release containing it is used.
    assert chosen == [["A", 2013], ["A", 2014], ["B", 2015]]
    assert overlaps[["release", "fy"]].drop_duplicates().values.tolist() == [["B", 2014]]
    rates = to_rates(panel).set_index("fy")
    assert rates.loc[2014, "entry_rate"] == 12 / 102


def test_identity_check_flags_only_broken_rows():
    long = pd.DataFrame(rows("A", 2013, 100, 10, 8, 102) + rows("A", 2014, 102, 12, 9, 110))
    bad = check_identity(long)
    assert bad["fy"].tolist() == [2014]
    assert bad["gap"].tolist() == [5]
