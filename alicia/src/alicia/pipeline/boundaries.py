"""Generalised ABS boundaries (ASGS Edition 3, 2021) as SVG paths for the website's maps.

The ABS publishes its digital boundaries through an ArcGIS map service (geo.abs.gov.au, CC BY 4.0). A query with
``maxAllowableOffset`` returns them already generalised, so a whole layer is small enough to embed in a page.
``build(level)`` downloads one layer once into ``data/raw/abs_boundaries/`` (recorded in the manifest), projects it
to the Australian Albers equal-area projection (EPSG:3577, the ABS's own), and writes
``data/processed/geo/<level>_2021_map.json``: one SVG path per area, in a 1000-unit-wide frame, with a label point.

States and territories (``STE``) are used now; council areas (``LGA``, layer 1, already generalised by the ABS) can
use the same code when the map gains them.
"""

from __future__ import annotations

import json
import math
from urllib.parse import urlencode

from . import store

SOURCE = "abs_boundaries"
LICENCE = "CC BY 4.0, Australian Bureau of Statistics"
SERVICE = "https://geo.abs.gov.au/arcgis/rest/services/ASGS2021"
LEVELS = {
    # level: (service, layer, code field, name field, generalisation in degrees)
    "STE": ("STE", 0, "state_code_2021", "state_name_2021", 0.03),
    "LGA": ("LGA", 1, "lga_code_2021", "lga_name_2021", 0.002),
}
STATE_ABBR = {"1": "NSW", "2": "VIC", "3": "QLD", "4": "SA", "5": "WA", "6": "TAS", "7": "NT", "8": "ACT"}
WIDTH = 1000.0
MIN_RING = 12.0  # drop islands smaller than this many square units in the 1000-wide frame (the largest ring stays)


def query_url(level: str) -> str:
    service, layer, code, name, offset = LEVELS[level]
    params = {
        "where": "1=1",
        "outFields": f"{code},{name}",
        "returnGeometry": "true",
        "outSR": "4326",
        "maxAllowableOffset": offset,
        "geometryPrecision": 4,
        "f": "geojson",
    }
    return f"{SERVICE}/{service}/MapServer/{layer}/query?{urlencode(params)}"


def albers(lon: float, lat: float) -> tuple[float, float]:
    """Australian Albers (EPSG:3577) on a sphere: standard parallels 18°S and 36°S, central meridian 132°E."""
    p1, p2, lam0 = math.radians(-18), math.radians(-36), math.radians(132)
    n = (math.sin(p1) + math.sin(p2)) / 2
    c = math.cos(p1) ** 2 + 2 * n * math.sin(p1)
    rho0 = math.sqrt(c) / n
    rho = math.sqrt(c - 2 * n * math.sin(math.radians(lat))) / n
    theta = n * (math.radians(lon) - lam0)
    return rho * math.sin(theta), rho0 - rho * math.cos(theta)


def _rings(geometry: dict) -> list[list[list[float]]]:
    if geometry["type"] == "Polygon":
        return list(geometry["coordinates"])
    if geometry["type"] == "MultiPolygon":
        return [ring for poly in geometry["coordinates"] for ring in poly]
    return []


def _area(ring: list[tuple[float, float]]) -> float:
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1], strict=True))) / 2


def _centroid(ring: list[tuple[float, float]]) -> tuple[float, float]:
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1], strict=True):
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    if not a:
        return ring[0]
    return cx / (3 * a), cy / (3 * a)


def svg_map(geojson: dict, level: str, keep=None) -> dict:
    """Project a GeoJSON layer and return its areas as SVG paths in a frame WIDTH units wide."""
    _, _, code_f, name_f, _ = LEVELS[level]
    feats = []
    for f in geojson["features"]:
        code = str(f["properties"][code_f])
        if keep and not keep(code):
            continue
        rings = [[albers(lon, lat) for lon, lat in ring] for ring in _rings(f["geometry"])]
        if rings:
            feats.append((code, f["properties"][name_f], rings))
    xs = [x for _, _, rings in feats for ring in rings for x, _ in ring]
    ys = [-y for _, _, rings in feats for ring in rings for _, y in ring]
    x0, y0 = min(xs), min(ys)
    scale = WIDTH / (max(xs) - x0)
    height = math.ceil((max(ys) - y0) * scale)
    out = []
    for code, name, rings in feats:
        frame = [[((x - x0) * scale, (-y - y0) * scale) for x, y in ring] for ring in rings]
        largest = max(frame, key=_area)
        kept = [r for r in frame if r is largest or _area(r) >= MIN_RING]
        path = "".join(
            "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in _dedupe(r)) + "Z"
            for r in sorted(kept, key=_area, reverse=True)
        )
        lx, ly = _centroid(largest)
        xs_, ys_ = [x for x, _ in largest], [y for _, y in largest]
        out.append(
            {
                "code": code,
                "name": name,
                "abbr": STATE_ABBR.get(code, "") if level == "STE" else "",
                "path": path,
                "label": [round(lx, 1), round(ly, 1)],
                "box": [round(min(xs_), 1), round(min(ys_), 1), round(max(xs_), 1), round(max(ys_), 1)],
            }
        )
    return {"level": level, "viewBox": f"0 0 {WIDTH:.0f} {height}", "areas": sorted(out, key=lambda a: a["code"])}


def _dedupe(ring):
    """Drop points that round to the same place as the one before, so paths stay short."""
    out, last = [], None
    for x, y in ring:
        key = (round(x, 1), round(y, 1))
        if key != last:
            out.append((x, y))
            last = key
    return out


def build(level: str = "STE", refresh: bool = False) -> dict:
    url = query_url(level)
    path = store.download(SOURCE, url, f"{level.lower()}_2021_generalised.geojson", LICENCE, refresh=refresh)
    geojson = json.loads(path.read_text("utf-8"))
    keep = (lambda code: code in STATE_ABBR) if level == "STE" else None  # no Other Territories (code 9)
    result = svg_map(geojson, level, keep)
    result |= {
        "source": "Australian Bureau of Statistics, ASGS Edition 3 (2021) digital boundaries, generalised",
        "url": url,
        "licence": LICENCE,
    }
    out = store.PROCESSED / "geo" / f"{level.lower()}_2021_map.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, separators=(",", ":")) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    m = build()
    print(len(m["areas"]), "areas", m["viewBox"], sum(len(a["path"]) for a in m["areas"]), "path characters")
