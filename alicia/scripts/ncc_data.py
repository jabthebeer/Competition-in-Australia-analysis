"""Build ALICIA's National Construction Code (NCC) tables and regulatory map data.

Plan: docs/plan_ncc_ingestion.md (phases N0, N1 and N4, and the regulatory map).
Methods and results: docs/ncc_variability.md.

Inputs, saved to data/raw/ncc/ with --download (not committed):
- the NCC 2025 dataset, version 1.2 (XML, one file per volume), published by
  the Australian Building Codes Board (ABCB) on data.gov.au under CC BY 4.0;
- the ABCB pages "NCC 2022 state and territory adoption dates" and
  "NCC 2025 state and territory adoption information".

Outputs, in data/processed/ncc/:
- adoption_history.csv: every edition of each volume since BCA 96, by
  jurisdiction, from the "History of adoption" table in each volume;
- adoption_2022.csv: NCC 2022 adoption by jurisdiction and provision area;
- adoption_2025.csv: NCC 2025 adoption and transition by jurisdiction;
- variations.csv: every state and territory variation in NCC 2025;
- variation_counts.csv: variations by volume, jurisdiction and technical area;
- other_legislation.csv: each jurisdiction's list of other legislation
  affecting buildings, with its administering agency;
- referenced_documents.csv: the standards the NCC references, and where;
- regulatory_map.json: nodes and typed parent-to-child links for the
  regulatory map (spec in docs/plan_ncc_ingestion.md, section 7);
- sources.json: what was read, with SHA-256 and retrieval dates.

Every row keeps the source wording it came from. Attribution required by the
licence: "The National Construction Code 2025 was provided by the Australian
Building Codes Board under the CC BY 4.0 licence."

Usage (from alicia/):
    uv run python scripts/ncc_data.py --download   # fetch, then build
    uv run python scripts/ncc_data.py              # build from data/raw/ncc/
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/ncc"
OUT = ROOT / "data/processed/ncc"

STATES = ["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"]
STATE_NAMES = {
    "ACT": "Australian Capital Territory",
    "NSW": "New South Wales",
    "NT": "Northern Territory",
    "QLD": "Queensland",
    "SA": "South Australia",
    "TAS": "Tasmania",
    "VIC": "Victoria",
    "WA": "Western Australia",
}

DATASET_2025 = "https://data.gov.au/data/dataset/national-construction-code-2025-version-1-2"
_B = "https://data.gov.au/data/dataset/9655eee9-da6a-4727-8514-83bab03ec318/resource/"
VOLUMES_2025 = {
    # key: (file, url)
    "vol1": (
        "ncc-2025-volume-one-v1.2.zip",
        _B + "2ae4c72d-99b3-4956-97d3-a7eabffe8da8/download/ncc-2025-volume-one-v1.2.zip",
    ),
    "vol2": (
        "ncc-2025-volume-two-v1.2.zip",
        _B + "14f03bed-e205-4dc4-bb37-32c83b314824/download/ncc-2025-volume-two-v1.2.zip",
    ),
    "vol3": (
        "ncc-2025-volume-three-v1.2.zip",
        _B + "b7ccc1ea-03c3-458e-a9eb-ce545a268bed/download/ncc-2025-volume-three-v1.2.zip",
    ),
    "housing": (
        "ncc-2025-housing-provisions-v1.2.zip",
        _B + "7adb04c2-8435-4b46-8a34-110213aa1b1e/download/ncc-2025-housing-provisions-v1.2.zip",
    ),
    "livable": (
        "ncc-2025-livable-housing-design-v1.2.zip",
        _B + "94649762-d98a-4ee8-96ce-958051d193af/download/ncc-2025-livable-housing-design-v1.2.zip",
    ),
}
PAGES = {
    "adoption_2022": (
        "abcb_ncc2022_adoption_dates.html",
        "https://www.abcb.gov.au/ncc-2022-state-and-territory-adoption-dates",
    ),
    "adoption_2025": (
        "abcb_ncc2025_adoption_information.html",
        "https://ncc.abcb.gov.au/ncc-2025/ncc-2025-state-and-territory-adoption-information",
    ),
}
LICENCE = "CC BY 4.0"
ATTRIBUTION = (
    "The National Construction Code 2025 was provided by the Australian Building Codes Board "
    "under the CC BY 4.0 licence."
)

# Existing register items about NCC adoption (regulation-register/records/).
NCC2022_RECORDS = {
    "ACT": "act-ncc-2022-2024",
    "NSW": "nsw-ncc-2022-2023",
    "NT": "nt-ncc-2022-2023",
    "QLD": "qld-ncc-2022-2024",
    "SA": "sa-ncc-2022-2024",
    "TAS": "tas-ncc-2022-2024",
    "VIC": "vic-ncc-2022-2024",
    "WA": "wa-ncc-2022-2025",
}


# --------------------------------------------------------------------------- helpers


def norm(s: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(s or "")).strip()


def text(el: ET.Element | None) -> str:
    return norm("".join(el.itertext())) if el is not None else ""


def title_of(el: ET.Element) -> str:
    return text(el.find("title"))


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def parse_date(s: str) -> str:
    """The first 'd Mon yyyy' date in s, as ISO, or ''."""
    m = re.search(r"(\d{1,2})\s+([A-Z][a-z]{2,8})\.?\s+(\d{4})", s)
    if not m:
        return ""
    day, mon, year = m.groups()
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            return (
                dt.datetime.strptime(f"{int(day)} {mon[:3] if fmt == '%d %b %Y' else mon} {year}", fmt)
                .date()
                .isoformat()
            )
        except ValueError:
            continue
    return ""


def long_date(iso: str) -> str:
    """'2027-05-01' -> '1 May 2027', the form the ABCB pages use."""
    if not iso:
        return ""
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B')} {d.year}"


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- download


def download() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    log = {}
    items = list(VOLUMES_2025.values()) + list(PAGES.values())
    for name, url in items:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ALICIA research script)"})
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
        (RAW / name).write_bytes(data)
        log[name] = {"url": url, "retrieved_at": dt.date.today().isoformat()}
        print(f"saved {name} ({len(data):,} bytes)")
    (RAW / "retrieved.json").write_text(json.dumps(log, indent=1) + "\n")


def load_volume(key: str) -> ET.Element:
    name, _ = VOLUMES_2025[key]
    with zipfile.ZipFile(RAW / name) as z:
        member = next(n for n in z.namelist() if n.endswith("contents.xml"))
        return ET.fromstring(z.read(member))


# --------------------------------------------------------------------------- adoption history (XML)


def table_rows(table: ET.Element) -> list[list[str]]:
    rows = []
    for tr in table.iter("tr"):
        rows.append([text(c) for c in tr if c.tag in ("td", "th")])
    return rows


def adoption_history(vols: dict[str, ET.Element]) -> list[dict]:
    out = []
    for key in ("vol1", "vol2", "vol3"):
        root = vols[key]
        volume = root.attrib.get("short-title", key)
        page = next(p for p in root.iter("page") if title_of(p).lower().startswith("history of adoption"))
        table = next(page.iter("table"))
        rows = table_rows(table)
        header, body = rows[0], rows[1:]
        for r in body:
            edition = r[0]
            cells = dict(zip(header[1:], r[1:], strict=False))
            national = parse_date(cells.get("Commonwealth", ""))
            for jur, cell in cells.items():
                iso = parse_date(cell)
                status = "adopted" if iso else ("not adopted" if re.search(r"not adopt", cell, re.I) else "other")
                lag = (dt.date.fromisoformat(iso) - dt.date.fromisoformat(national)).days if iso and national else ""
                out.append(
                    {
                        "volume": volume,
                        "edition": edition,
                        "jurisdiction": jur,
                        "cell": cell,
                        "date": iso,
                        "status": status,
                        "lag_days_vs_commonwealth": lag,
                        "source": f"{DATASET_2025} ({volume}, Preface, '{title_of(page)}', Table 1)",
                    }
                )
    return out


# --------------------------------------------------------------------------- adoption pages (HTML)


class TableParser(HTMLParser):
    """Collects the text of every cell of every table on a page."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self.depth = 0
        self.cell: list[str] | None = None
        self.row: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.depth += 1
            self.tables.append([])
        elif tag == "tr" and self.depth:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(norm("".join(self.cell)))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.tables[-1].append(self.row)
            self.row = None
        elif tag == "table":
            self.depth -= 1

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def page_tables(name: str) -> tuple[list[list[list[str]]], str]:
    raw = (RAW / name).read_text(encoding="utf-8", errors="replace")
    p = TableParser()
    p.feed(raw)
    body = norm(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style).*?</\1>", " ", raw, flags=re.S)))
    return p.tables, body


def state_code(name: str) -> str:
    for code, full in STATE_NAMES.items():
        if name.lower().startswith(full.lower()):
            return code
    return ""


def status_2022(cell: str) -> str:
    c = cell.lower()
    if "not adopt" in c:
        return "not adopted"
    if "basix" in c:
        return "state scheme"
    if "limited to" in c:
        return "adopted with a lower standard"
    if "ncc 2019" in c:
        return "earlier edition kept"
    if parse_date(cell):
        return "adopted"
    return "date not on this page"


def adoption_2022() -> list[dict]:
    name, url = PAGES["adoption_2022"]
    tables, body = page_tables(name)
    m = re.search(r"correct as at (\d{1,2} \w+ \d{4})", body)
    as_at = parse_date(m.group(1)) if m else ""
    table = next(t for t in tables if t and t[0] and t[0][0].startswith("State"))
    header = table[0]
    out = []
    for r in table[1:]:
        st = state_code(r[0])
        for area, cell in zip(header[1:], r[1:], strict=False):
            if area.lower().startswith("further"):
                continue
            # Some cells end with a link to the government's page; keep only the adoption wording.
            cell = re.sub(
                r"\s*(?:Northern Territory|Western Australian|South Australian|Tasmanian|Victorian|NSW|ACT)"
                r" Government$",
                "",
                cell,
            )
            out.append(
                {
                    "jurisdiction": st,
                    "provision_area": area,
                    "cell": cell,
                    "date": parse_date(cell),
                    "status": status_2022(cell),
                    "as_at": as_at,
                    "register_record": NCC2022_RECORDS.get(st, ""),
                    "source": url,
                }
            )
    return out


def adoption_2025() -> list[dict]:
    name, url = PAGES["adoption_2025"]
    tables, _ = page_tables(name)
    table = next(t for t in tables if t and t[0] and t[0][0].lower().startswith("state"))
    out = []
    for r in table[1:]:
        st = state_code(r[0])
        cell, transition = r[1], r[2] if len(r) > 2 else ""
        parts = re.findall(r"(BCA|PCA):\s*(\d{1,2} [A-Z][a-z]+ \d{4})", cell)
        for code, part in parts or [("NCC", cell)]:
            iso = parse_date(part)
            out.append(
                {
                    "jurisdiction": st,
                    "code": code,
                    "cell": cell,
                    "date": iso,
                    "status": "adopted" if iso else ("not adopted" if "not adopted" in cell.lower() else "other"),
                    "transition": transition,
                    "source": url,
                }
            )
    return out


# --------------------------------------------------------------------------- variations (XML)


def area_index(root: ET.Element) -> tuple[dict[str, str], dict[str, str]]:
    """Technical section and part titles by number (e.g. 'J' -> 'Energy efficiency', 'H6' -> ...).

    Schedules (definitions, referenced documents, the state appendices) share
    numbers with the Housing Provisions' sections, so they are left out."""
    sections = {
        s.attrib["num"]: title_of(s)
        for s in root.iter("ncc-section")
        if s.attrib.get("type") != "schedule" and s.attrib.get("num")
    }
    parts = {p.attrib.get("num", ""): title_of(p) for p in root.iter("part")}
    return sections, parts


def technical_area(volume_key: str, codes: list[str], sections: dict, parts: dict) -> tuple[str, str] | None:
    """The technical section (or, in Volume Two, the H part) that the first usable code belongs to."""
    if volume_key == "livable":
        return "LHD", "Livable Housing Design Standard"
    for code in codes:
        code = re.sub(r"^(?:ACT|NSW|NT|QLD|SA|TAS|VIC|WA)\s*", "", (code or "").strip())
        if not code:
            continue
        if volume_key == "vol2":
            m = re.match(r"(H\d+)", code)
            if m and m.group(1) in parts:
                return m.group(1), parts[m.group(1)]
        if volume_key == "housing":
            m = re.match(r"(\d+)(?:\.|$)", code)
            if m and m.group(1) in sections:
                return m.group(1), sections[m.group(1)]
        m = re.match(r"([A-J])\d", code)
        if m and m.group(1) in sections:
            return m.group(1), sections[m.group(1)]
    return None


def variations(vols: dict[str, ET.Element]) -> list[dict]:
    out = []
    for key, root in vols.items():
        volume = root.attrib.get("short-title") or title_of(root) or key
        sections, parts = area_index(root)
        parent = {c: p for p in root.iter() for c in p}

        def ancestor(el, tag, parent=parent):
            while el in parent:
                el = parent[el]
                if el.tag == tag:
                    return el
            return None

        for el in root.iter():
            st = el.attrib.get("state")
            if not (el.tag.endswith("-variation") and st in STATES):
                continue
            element = el.tag.removesuffix("-variation")
            sptc = el.attrib.get("sptc", "") or ""
            title = title_of(el)
            sec = ancestor(el, "ncc-section")
            in_schedule = sec is not None and bool(sec.attrib.get("state"))
            num = el.attrib.get("num", "") or ""
            # Codes to place the variation: its own clause code or number, then its ancestors'.
            codes, a = [sptc, num], el
            while a in parent:
                a = parent[a]
                codes += [a.attrib.get("sptc", ""), a.attrib.get("num", "")]
            if element == "glossentry":
                area = ("Definitions", "Definitions")
                term = text(el.find(".//glossterm")) or title
                provision = "definition: " + term
                title = title or term
            else:
                area = technical_area(key, codes, sections, parts) or (
                    ("State appendix", "Other provisions in the state appendix") if in_schedule else ("Other", "Other")
                )
                provision = sptc or (f"{element} {num}" if num else f"{element}: {title}")
            where = "state appendix" if in_schedule else "in the volume"
            out.append(
                {
                    "edition": "NCC 2025",
                    "volume": volume,
                    "jurisdiction": st,
                    "element": element,
                    "type": el.attrib.get("type", "") or "",
                    "provision": provision,
                    "area": area[0],
                    "area_title": area[1],
                    "title": title,
                    "where": where,
                    "xml_id": el.attrib.get("id", ""),
                }
            )
    return out


def variation_counts(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, dict] = {}
    for r in rows:
        k = (r["volume"], r["jurisdiction"], r["area"], r["area_title"])
        g = groups.setdefault(k, {"provisions": set(), "INSERT": 0, "REPLACE": 0, "DELETE": 0, "other": 0, "n": 0})
        g["provisions"].add(r["provision"])
        g["n"] += 1
        g[r["type"] if r["type"] in ("INSERT", "REPLACE", "DELETE") else "other"] += 1
    out = []
    for (volume, jur, area, area_title), g in sorted(groups.items()):
        out.append(
            {
                "edition": "NCC 2025",
                "volume": volume,
                "jurisdiction": jur,
                "area": area,
                "area_title": area_title,
                "provisions_varied": len(g["provisions"]),
                "variations": g["n"],
                "inserted": g["INSERT"],
                "replaced": g["REPLACE"],
                "deleted": g["DELETE"],
                "other": g["other"],
            }
        )
    return out


# --------------------------------------------------------------------------- state schedules (XML)

LAW_RE = re.compile(
    r"((?:[A-Z][\w’'&\-]*|\([A-Z&]+\))(?:,?\s(?:\([^)]*\)|of|and|the|for|on|to|in|[A-Z][\w’'&\-]*))*\s(?:Act|Regulations?|Code)\s\d{4})"
)


# Laws a state appendix names without a year, resolved against that state's
# register catalogue (data/processed/legislation/<state>_catalogue.csv).
NO_YEAR = {"NT": ["Building Act", "Building Regulations"]}


def law_names(s: str, state: str = "") -> list[str]:
    names = []
    for bare in NO_YEAR.get(state, []):
        if re.search(rf"\b{bare}(?!\s\d)", s):
            names.append(bare)
    for m in LAW_RE.findall(s):
        n = re.sub(r"\s\([A-Z&]+\)", "", m)  # drop '(EP&A)' style abbreviations
        n = re.sub(r"^(?:In|The|Section \d+ of the|Section \d+ of)\s+", "", n)
        n = (
            re.sub(r"^.*?\b(?:of|by) the\s+", "", n)
            if " of the " in n and not n.startswith(("Environmental", "Building"))
            else n
        )
        if n not in names:
            names.append(n)
    return names


def state_schedules(vols: dict[str, ET.Element]) -> tuple[list[dict], list[dict]]:
    """Each state's introduction (the laws that adopt the code) and its list of other legislation."""
    intros, others = [], []
    for key in ("vol1", "vol2", "vol3"):
        root = vols[key]
        volume = root.attrib.get("short-title", key)
        for sec in root.iter("ncc-section"):
            st = sec.attrib.get("state")
            if st not in STATES:
                continue
            for page in sec.findall("page"):
                t = title_of(page)
                body = text(page.find("content"))
                if t.endswith("Introduction"):
                    intros.append({"volume": volume, "jurisdiction": st, "page": t, "text": body})
                elif "Other legislation" in t:
                    first = text(page.find("content/p"))
                    intros.append({"volume": volume, "jurisdiction": st, "page": t, "text": first})
                    for topic in page.findall("content/section"):
                        name = re.sub(r"^\d+\.\s*", "", title_of(topic))
                        agency, laws = "", []
                        for sub in topic.findall("section"):
                            st_title = title_of(sub)
                            if st_title.startswith("Administering"):
                                agency = "; ".join(text(p) for p in sub.findall("p") if text(p))
                            elif st_title.startswith("Relevant"):
                                for p in sub.findall("p"):
                                    a = p.find("a")
                                    for line in [text(p)] if text(p) else []:
                                        laws.append((line, a.attrib.get("href", "") if a is not None else ""))
                        for law, href in laws:
                            others.append(
                                {
                                    "volume": volume,
                                    "jurisdiction": st,
                                    "topic": name,
                                    "agency": agency,
                                    "legislation": law,
                                    "url": href,
                                }
                            )
    return intros, others


def merge_volumes(rows: list[dict], keys: list[str]) -> list[dict]:
    merged: dict[tuple, dict] = {}
    for r in rows:
        k = tuple(r[x] for x in keys)
        m = merged.setdefault(k, dict(r, volume=[]))
        if r["volume"] not in m["volume"]:
            m["volume"].append(r["volume"])
    out = []
    for m in merged.values():
        m["volume"] = "; ".join(m["volume"])
        out.append(m)
    return out


# --------------------------------------------------------------------------- referenced documents (XML)


def referenced_documents(vols: dict[str, ET.Element]) -> list[dict]:
    root = vols["vol1"]
    sec = next(s for s in root.iter("ncc-section") if title_of(s) == "Referenced documents")
    table = next(sec.iter("table"))
    rows = table_rows(table)
    header, body = rows[0], rows[1:]
    out = []
    for r in body:
        d = dict(zip(header, r, strict=False))
        if not d.get("No."):
            continue
        out.append(
            {
                "document": d.get("No.", ""),
                "date": d.get("Date", ""),
                "title": d.get("Title", ""),
                "volume_one": d.get("Volume One", ""),
                "volume_two": d.get("Volume Two", ""),
                "housing_provisions": d.get("Housing Provisions", ""),
                "volume_three": d.get("Volume Three", ""),
            }
        )
    return out


# --------------------------------------------------------------------------- regulatory map


def build_map(vols, history, ad22, ad25, var_counts, intros, others, refdocs, catalogue) -> dict:
    nodes: dict[str, dict] = {}
    links: list[dict] = []

    def node(id_, **kw):
        nodes.setdefault(id_, {"id": id_, **kw})
        return id_

    def link(source, target, relation, **kw):
        links.append({"source": source, "target": target, "relation": relation, **kw})

    abcb = {"publisher": "Australian Building Codes Board", "url": DATASET_2025, "licence": LICENCE}
    node(
        "ncc",
        type="code",
        label="National Construction Code",
        jurisdiction="national",
        body="nat-abcb",
        url="https://ncc.abcb.gov.au/",
        source=abcb,
    )

    # Editions
    node(
        "ncc-2022",
        type="edition",
        label="NCC 2022",
        jurisdiction="national",
        source={"publisher": "Australian Building Codes Board", "url": PAGES["adoption_2022"][1]},
    )
    node("ncc-2025", type="edition", label="NCC 2025", jurisdiction="national", source=abcb)
    link("ncc", "ncc-2022", "edition")
    link("ncc", "ncc-2025", "edition")

    # Volumes and technical areas of NCC 2025
    vol_ids = {}
    for key, root in vols.items():
        label = root.attrib.get("short-title") or title_of(root) or key
        vid = node(
            f"ncc-2025-{key}",
            type="volume",
            label=f"NCC 2025 {label}",
            jurisdiction="national",
            industry=root.attrib.get("industry", ""),
            source=abcb,
        )
        vol_ids[label] = vid
        link("ncc-2025", vid, "contains")
    for r in var_counts:
        vid = vol_ids[r["volume"]]
        aid = node(
            f"{vid}-{slug(r['area'])}",
            type="area",
            label=r["area_title"] or r["area"],
            code=r["area"],
            jurisdiction="national",
            source=abcb,
        )
        if not any(x["source"] == vid and x["target"] == aid for x in links):
            link(vid, aid, "contains")

    # State adoption of NCC 2025
    ad25_by = collections.defaultdict(list)
    for r in ad25:
        ad25_by[r["jurisdiction"]].append(r)
    intro_by = collections.defaultdict(list)
    for r in intros:
        intro_by[r["jurisdiction"]].append(r)
    cat = collections.defaultdict(list)
    for r in catalogue:
        cat[r["jurisdiction"]].append(r)

    for st in STATES:
        rows = ad25_by.get(st, [])
        status = "; ".join(
            f"{r['code']}: {r['cell'] if r['code'] == 'NCC' else (long_date(r['date']) or r['status'])}" for r in rows
        )
        aid = node(
            f"ncc-2025-{st.lower()}",
            type="adoption",
            label=f"NCC 2025 in {STATE_NAMES[st]}",
            jurisdiction=st,
            adoption=status,
            transition=(rows[0]["transition"] if rows else ""),
            source={"publisher": "Australian Building Codes Board", "url": PAGES["adoption_2025"][1]},
        )
        link("ncc-2025", aid, "adopted-as", jurisdiction=st)
        # Laws that give the code legal effect, named in the state's own schedule
        seen = set()
        for intro in intro_by.get(st, []):
            for name in law_names(intro["text"], st):
                if name in seen:
                    continue
                seen.add(name)
                c, matched = find_law(cat, st, name)
                label = c["name"] if c and name in NO_YEAR.get(st, []) else name
                lid = node(
                    f"law-{st.lower()}-{slug(label)}",
                    type="law",
                    label=label,
                    jurisdiction=st,
                    register_id=(c or {}).get("register_id", ""),
                    url=(c or {}).get("url", ""),
                    matched=matched,
                )
                quote = next((s for s in re.split(r"(?<=[.;])\s+", intro["text"]) if name in s), "")
                relation = "consolidated-into" if "consolidated into" in quote else "gives-effect-to"
                link(
                    lid,
                    aid,
                    relation,
                    jurisdiction=st,
                    basis={
                        "source": DATASET_2025,
                        "locator": f"{intro['volume']}, {STATE_NAMES[st]} schedule, '{intro['page']}'",
                        "quote": quote[:400],
                    },
                )
        # Variations by technical area
        for r in var_counts:
            if r["jurisdiction"] != st:
                continue
            vid = vol_ids[r["volume"]]
            area_id = f"{vid}-{slug(r['area'])}"
            sid = node(
                f"{area_id}-{st.lower()}",
                type="variation-set",
                label=f"{st} variations: {r['area_title'] or r['area']} ({r['volume']})",
                jurisdiction=st,
                provisions_varied=r["provisions_varied"],
                inserted=r["inserted"],
                replaced=r["replaced"],
                deleted=r["deleted"],
                source=abcb,
            )
            link(aid, sid, "varies", jurisdiction=st, weight=r["provisions_varied"])
            link(sid, area_id, "varies-area", jurisdiction=st, weight=r["provisions_varied"])
        # Other legislation affecting buildings, as listed by the state
        for o in others:
            if o["jurisdiction"] != st:
                continue
            c, matched = find_law(cat, st, o["legislation"])
            lid = node(
                f"law-{st.lower()}-{slug(o['legislation'])}",
                type="other-law",
                label=o["legislation"],
                jurisdiction=st,
                agency=o["agency"],
                topic=o["topic"],
                register_id=(c or {}).get("register_id", ""),
                url=o["url"] or (c or {}).get("url", ""),
                matched=matched,
            )
            link(
                aid,
                lid,
                "read-with",
                jurisdiction=st,
                topic=o["topic"],
                basis={
                    "source": DATASET_2025,
                    "locator": (
                        f"{o['volume']}, {STATE_NAMES[st]} schedule, "
                        f"'Other legislation affecting buildings', {o['topic']}"
                    ),
                },
            )

    # State adoption of NCC 2022, joined to the register's records
    by22 = collections.defaultdict(list)
    for r in ad22:
        by22[r["jurisdiction"]].append(r)
    for st in STATES:
        rows = by22.get(st, [])
        aid = node(
            f"ncc-2022-{st.lower()}",
            type="adoption",
            label=f"NCC 2022 in {STATE_NAMES[st]}",
            jurisdiction=st,
            adoption="; ".join(f"{r['provision_area']}: {r['cell']}" for r in rows),
            register_records=[NCC2022_RECORDS[st]],
            source={
                "publisher": "Australian Building Codes Board",
                "url": PAGES["adoption_2022"][1],
                "as_at": rows[0]["as_at"] if rows else "",
            },
        )
        link("ncc-2022", aid, "adopted-as", jurisdiction=st)

    # Referenced documents (standards) by technical area
    area_of_clause = {}
    for key, root in vols.items():
        sections, parts = area_index(root)
        label = root.attrib.get("short-title") or key
        area_of_clause[label] = (key, sections, parts)
    col_volume = {
        "volume_one": "Volume One",
        "volume_two": "Volume Two",
        "housing_provisions": "Housing Provisions",
        "volume_three": "Volume Three",
    }
    for d in refdocs:
        did = node(
            f"std-{slug(d['document'])}-{slug(d['date'])}",
            type="standard",
            label=f"{d['document']} ({d['date']})",
            title=d["title"],
            jurisdiction="national",
            source=abcb,
        )
        for col, vlabel in col_volume.items():
            refs = [x.strip() for x in d[col].split(",") if x.strip() and x.strip() != "N/A"]
            if vlabel not in vol_ids or not refs:
                continue
            key, sections, parts = area_of_clause[vlabel]
            counts = collections.Counter()
            for ref in refs:
                area = technical_area(key, [ref], sections, parts)
                if area:
                    counts[area] += 1
            for (code, ttl), n in counts.items():
                area_id = node(
                    f"{vol_ids[vlabel]}-{slug(code)}",
                    type="area",
                    label=ttl or code,
                    code=code,
                    jurisdiction="national",
                    source=abcb,
                )
                if not any(x["source"] == vol_ids[vlabel] and x["target"] == area_id for x in links):
                    link(vol_ids[vlabel], area_id, "contains")
                link(area_id, did, "references", weight=n)

    return {
        "note": (
            "Regulatory map data for the National Construction Code (beta). Nodes are laws, the code, its editions, "
            "volumes, technical areas, state adoptions, state variation sets, other legislation and "
            "referenced standards; "
            "links run from parent to child and are typed. Built by alicia/scripts/ncc_data.py from "
            "the NCC 2025 dataset "
            "(data.gov.au) and ABCB adoption pages. Spec: docs/plan_ncc_ingestion.md, section 7. " + ATTRIBUTION
        ),
        "built_on": dt.date.today().isoformat(),
        "node_types": sorted({n["type"] for n in nodes.values()}),
        "relations": sorted({x["relation"] for x in links}),
        "nodes": list(nodes.values()),
        "links": links,
    }


def law_key(name: str) -> str:
    """A law title for matching: lower case, without a trailing register number such as '(2021-759)'."""
    name = re.sub(r"\s*\(\d{4}-\d+\)\s*$", "", name)
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def find_law(cat: dict, state: str, name: str) -> tuple[dict | None, str]:
    """The state's catalogue row for a law named in the NCC, and how it was matched."""
    key = law_key(name)
    rows = cat.get(state, [])
    exact = [r for r in rows if law_key(r["name"]) == key]
    if len(exact) == 1:
        return exact[0], "title"
    if name in NO_YEAR.get(state, []):
        dated = [r for r in rows if re.fullmatch(re.escape(key) + r" \d{4}", law_key(r["name"]))]
        if len(dated) == 1:
            return dated[0], "title without year (inferred)"
    return None, "not in the state catalogue"


def load_catalogue() -> list[dict]:
    rows = []
    for st in STATES:
        f = ROOT / f"data/processed/legislation/{st.lower()}_catalogue.csv"
        if not f.exists():
            continue
        with f.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                rows.append({"jurisdiction": st, "register_id": r["register_id"], "name": r["name"], "url": r["url"]})
    return rows


# --------------------------------------------------------------------------- main


def build() -> None:
    vols = {k: load_volume(k) for k in VOLUMES_2025}
    OUT.mkdir(parents=True, exist_ok=True)

    hist = adoption_history(vols)
    write_csv(
        OUT / "adoption_history.csv",
        hist,
        ["volume", "edition", "jurisdiction", "cell", "date", "status", "lag_days_vs_commonwealth", "source"],
    )
    ad22 = adoption_2022()
    write_csv(
        OUT / "adoption_2022.csv",
        ad22,
        ["jurisdiction", "provision_area", "cell", "date", "status", "as_at", "register_record", "source"],
    )
    ad25 = adoption_2025()
    write_csv(
        OUT / "adoption_2025.csv", ad25, ["jurisdiction", "code", "cell", "date", "status", "transition", "source"]
    )

    var = variations(vols)
    write_csv(
        OUT / "variations.csv",
        var,
        [
            "edition",
            "volume",
            "jurisdiction",
            "element",
            "type",
            "provision",
            "area",
            "area_title",
            "title",
            "where",
            "xml_id",
        ],
    )
    counts = variation_counts(var)
    write_csv(
        OUT / "variation_counts.csv",
        counts,
        [
            "edition",
            "volume",
            "jurisdiction",
            "area",
            "area_title",
            "provisions_varied",
            "variations",
            "inserted",
            "replaced",
            "deleted",
            "other",
        ],
    )

    intros, others = state_schedules(vols)
    others = merge_volumes(others, ["jurisdiction", "topic", "legislation"])
    write_csv(
        OUT / "other_legislation.csv", others, ["jurisdiction", "topic", "agency", "legislation", "url", "volume"]
    )
    refdocs = referenced_documents(vols)
    write_csv(
        OUT / "referenced_documents.csv",
        refdocs,
        ["document", "date", "title", "volume_one", "volume_two", "housing_provisions", "volume_three"],
    )

    m = build_map(vols, hist, ad22, ad25, counts, intros, others, refdocs, load_catalogue())
    (OUT / "regulatory_map.json").write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    retrieved = json.loads((RAW / "retrieved.json").read_text()) if (RAW / "retrieved.json").exists() else {}
    sources = []
    for name, url in list(VOLUMES_2025.values()) + list(PAGES.values()):
        p = RAW / name
        sources.append(
            {
                "file": name,
                "url": url,
                "retrieved_at": retrieved.get(name, {}).get("retrieved_at", ""),
                "bytes": p.stat().st_size,
                "sha256": sha256(p),
                "licence": LICENCE,
                "publisher": "Australian Building Codes Board",
            }
        )
    (OUT / "sources.json").write_text(
        json.dumps({"attribution": ATTRIBUTION, "dataset": DATASET_2025, "files": sources}, indent=1) + "\n"
    )

    print(
        f"adoption_history {len(hist)}, adoption_2022 {len(ad22)}, adoption_2025 {len(ad25)}, variations {len(var)}, "
        f"variation_counts {len(counts)}, other_legislation {len(others)}, referenced_documents {len(refdocs)}, "
        f"map {len(m['nodes'])} nodes / {len(m['links'])} links"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--download", action="store_true", help="fetch the inputs to data/raw/ncc/ first")
    args = ap.parse_args()
    if args.download:
        download()
    build()
