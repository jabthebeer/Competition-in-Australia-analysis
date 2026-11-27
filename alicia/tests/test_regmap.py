"""The regulatory map page (DECISIONS E-600): its data is the map file as built, with the jurisdiction summary
recounted from the links."""

import json

import pytest

from alicia.menu import regmap

FILES = regmap.map_files()


@pytest.mark.skipif(not FILES, reason="no regulatory map built")
def test_map_keeps_every_node_and_link():
    raw = json.loads(FILES[0].read_text("utf-8"))
    m = regmap.load_map(FILES[0])
    assert len(m["nodes"]) == len(raw["nodes"]) and len(m["links"]) == len(raw["links"])
    ids = {n["id"] for n in m["nodes"]}
    assert all(lk["source"] in ids and lk["target"] in ids for lk in m["links"])
    assert m["root"] in ids and m["file"].endswith("regulatory_map.json")


@pytest.mark.skipif(not FILES, reason="no regulatory map built")
def test_summary_recounts_the_variations():
    raw = json.loads(FILES[0].read_text("utf-8"))
    s = regmap.summary(raw)
    nodes = {n["id"]: n for n in raw["nodes"]}
    for row in s["rows"]:
        sets = [n for n in raw["nodes"] if n["type"] == "variation-set" and n["jurisdiction"] == row["j"]]
        # Each variation set changes one area, so the sum of its provisions is the row's total.
        assert row["sets"] == len(sets)
        assert row["provisions"] == sum(n.get("provisions_varied", 0) for n in sets)
        assert row["provisions"] == sum(row["byVolume"].values())
        assert all(nodes[a["id"]]["jurisdiction"] == row["j"] for a in row["adoptions"])


def test_register_items_match_on_jurisdiction_and_id():
    # Register ids repeat between states, so a NSW law must not pick up a Tasmanian item with the same id.
    menu = {
        "records": [
            {
                "id": "tas-x",
                "title": "Tas item",
                "jurisdiction": "TAS",
                "instruments": [{"register_id": "act-2016-058"}],
            },
            {
                "id": "nsw-y",
                "title": "NSW item",
                "jurisdiction": "NSW",
                "type": "requirement",
                "laws": [{"registerId": "act-2016-058"}],
            },
        ]
    }
    index = regmap._register_index(menu)
    assert [i["id"] for i in index[("TAS", "act-2016-058")]] == ["tas-x"]
    assert [i["id"] for i in index[("NSW", "act-2016-058")]] == ["nsw-y"]


def test_payload_without_maps(tmp_path):
    assert regmap.payload(None, base=tmp_path)["maps"] == []
