"""Regulatory map (``regulatory-map.html``): a principal law and the instruments that sit within it, as a graph.

Owner request, 27 November 2026 (DECISIONS E-600): an Obsidian-style node-and-link view in which a main law links to
the instruments under it. The National Construction Code is the first map; its purpose is to show how adoption of the
code varies between the states and territories.

Each map is one file, ``data/processed/<topic>/regulatory_map.json``, in the shape set out in
``docs/plan_ncc_ingestion.md``, section 7, so a later map (work health and safety, food) needs no change here. This
module reads the files as they are, adds to each node the ALICIA register items that cite the same law, and works out
the per-jurisdiction summary shown under the graph. It does not change the data.
"""

from __future__ import annotations

import json
from pathlib import Path

from .growth import STATE_SHORT

ROOT = Path(__file__).resolve().parents[4]
MAPS = ROOT / "data" / "processed"
# Node fields the page uses; anything else in the file stays in the file.
NODE_KEYS = (
    "id",
    "type",
    "label",
    "jurisdiction",
    "url",
    "register_id",
    "register_records",
    "title",
    "code",
    "industry",
    "adoption",
    "transition",
    "agency",
    "topic",
    "provisions_varied",
    "inserted",
    "replaced",
    "deleted",
    "source",
)
LINK_KEYS = ("source", "target", "relation", "jurisdiction", "weight", "topic", "basis")
JURISDICTIONS = tuple(STATE_SHORT)
# The notes on how each map is built and its limits, by the map's folder.
METHODS = {"ncc": ("docs/ncc_variability.md", "docs/plan_ncc_ingestion.md")}


def map_files(base: Path = MAPS) -> list[Path]:
    """Every regulatory map the build can find, in folder order."""
    return sorted(base.glob("*/regulatory_map.json"))


def _register_index(menu: dict | None) -> dict[tuple[str, str], list[dict]]:
    """The ALICIA register items that cite each law, keyed by jurisdiction and the law's id in its official register.
    Register ids repeat between states (each state numbers its own Acts), so the jurisdiction is part of the key."""
    index: dict[tuple[str, str], dict[str, str]] = {}
    if not menu:
        return {}

    def add(j, reg_id, item):
        if reg_id and j:
            index.setdefault((str(j).upper(), str(reg_id)), {})[item["id"]] = item["title"]

    for r in menu.get("records", []):
        j = r.get("jurisdiction")
        for x in r.get("instruments", []) or []:
            add(j, x.get("register_id"), r)
        for law in r.get("laws", []) or []:
            add(j, law.get("registerId"), r)
        for q in r.get("requirements", []) or []:
            for law in q.get("laws", []) or []:
                add(q.get("jurisdiction") or j, law.get("registerId"), q)
    return {k: [{"id": i, "title": t} for i, t in sorted(v.items())] for k, v in index.items()}


def _titles(menu: dict | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for r in (menu or {}).get("records", []):
        out[r["id"]] = r["title"]
        for q in r.get("requirements", []) or []:
            out[q["id"]] = q["title"]
    return out


def summary(data: dict) -> dict:
    """Per jurisdiction: provisions varied in each volume, variation sets, laws giving effect to the code, other laws
    the state lists, and each adoption's date and transition. Volumes are the nodes a variation set's area sits in."""
    nodes = {n["id"]: n for n in data["nodes"]}
    contains = {lk["target"]: lk["source"] for lk in data["links"] if lk["relation"] == "contains"}
    volumes = [n for n in data["nodes"] if n["type"] == "volume"]
    rows = {
        j: {"j": j, "byVolume": {}, "provisions": 0, "sets": 0, "laws": 0, "otherLaws": 0, "adoptions": []}
        for j in JURISDICTIONS
    }
    for lk in data["links"]:
        j = lk.get("jurisdiction")
        if j not in rows:
            continue
        rel = lk["relation"]
        if rel == "varies-area":
            vol = contains.get(lk["target"])
            w = lk.get("weight") or 0
            rows[j]["byVolume"][vol] = rows[j]["byVolume"].get(vol, 0) + w
            rows[j]["provisions"] += w
            rows[j]["sets"] += 1
        elif rel in ("gives-effect-to", "consolidated-into"):
            rows[j]["laws"] += 1
        elif rel == "read-with":
            rows[j]["otherLaws"] += 1
        elif rel == "adopted-as":
            a = nodes[lk["target"]]
            rows[j]["adoptions"].append(
                {
                    "id": a["id"],
                    "edition": nodes[lk["source"]]["label"],
                    "adoption": a.get("adoption"),
                    "transition": a.get("transition"),
                }
            )
    used = [v for v in volumes if any(r["byVolume"].get(v["id"]) for r in rows.values())]
    editions = sorted({a["edition"] for r in rows.values() for a in r["adoptions"]})
    return {
        "volumes": [{"id": v["id"], "label": v["label"]} for v in used],
        "editions": editions,
        "rows": [r for r in rows.values() if r["sets"] or r["adoptions"] or r["laws"]],
    }


def load_map(path: Path, menu: dict | None = None) -> dict:
    """One map for the page: its nodes and links trimmed to the fields shown, the ALICIA items that cite each law,
    and the jurisdiction summary."""
    data = json.loads(path.read_text("utf-8"))
    index, titles = _register_index(menu), _titles(menu)
    nodes = []
    for n in data["nodes"]:
        m = {k: n[k] for k in NODE_KEYS if n.get(k) not in (None, "", [])}
        key = (str(n.get("jurisdiction", "")).upper(), str(n.get("register_id")))
        items = {i["id"]: i["title"] for i in index.get(key, [])} if n.get("register_id") else {}
        for rid in n.get("register_records") or []:
            items.setdefault(rid, titles.get(rid, rid))
        if items:
            m["alicia"] = [{"id": i, "title": t} for i, t in sorted(items.items())]
        m.pop("register_records", None)
        nodes.append(m)
    links = [{k: lk[k] for k in LINK_KEYS if lk.get(k) not in (None, "")} for lk in data["links"]]
    parents = {lk["target"] for lk in data["links"]}
    root = next((n for n in data["nodes"] if n["id"] not in parents and n["type"] != "law"), data["nodes"][0])
    rel = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name
    return {
        "id": path.parent.name,
        "title": root["label"],
        "root": root["id"],
        "note": data.get("note", ""),
        "builtOn": data.get("built_on"),
        "file": rel,
        "methods": list(METHODS.get(path.parent.name, ())),
        "nodes": nodes,
        "links": links,
        "summary": summary(data),
    }


def payload(menu: dict | None = None, repo: str = "", base: Path = MAPS) -> dict:
    """The page's data: every map found, and the short forms of the jurisdictions."""
    return {
        "maps": [load_map(p, menu) for p in map_files(base)],
        "states": STATE_SHORT,
        "repo": repo,
        "generated": (menu or {}).get("generated"),
    }
