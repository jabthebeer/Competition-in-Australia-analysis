"""Planning land-use terms by state, matched to ANZSIC classes (phase E, batch E-3).

Reads each state's standard land-use definitions and writes two tables:
- data/processed/legislation/land_use_definitions.csv: state, term, definition
  (quoted from the instrument), instrument, locator, URL, as at;
- data/processed/legislation/land_use_terms.csv: for each ANZSIC class and state,
  the land-use term(s) the class most likely falls under, with a confidence.

Sources (all cached under data/raw/law_text/):
- QLD: Planning Regulation 2017, schedule 3 (use terms) and schedule 24
  (dictionary), current register text;
- WA: Planning and Development (Local Planning Schemes) Regulations 2015,
  schedule 1 (model provisions) cl 38, current register Word document;
- NSW: the Standard Instrument definitions as they appear in the Shoalhaven
  Local Environmental Plan 2014 dictionary (a sample council), corpus copy;
- ACT: Territory Plan 2023 (NI2023-540), Part G Dictionary, Table 1, register PDF.
SA, Tasmania and the NT are not covered: their planning sites refuse automated
requests (docs/plan_councils.md, E-361). Victoria waits for its batch.

How classes are matched: each class (or its group) is given one or more use types
(the crosswalk below), and each use type points to the matching term(s) in each
state. 'h' means the term or class description names that use; 'm' means it is
judged from the definitions. Confidence is high when both steps are 'h', medium
when one is, and low when neither is. A local scheme can still list a use
differently, define industry impact levels (Qld) or prohibit a use in a zone.

Run from alicia/: uv run python scripts/land_use_terms.py
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import law_text as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/processed/legislation"
CLASSES = ROOT / "data/processed/anzsic/anzsic2006_classes.csv"

QLD_URL = "https://www.legislation.qld.gov.au/view/whole/html/inforce/current/sl-2017-0078"
WA_URL = "https://www.legislation.wa.gov.au/legislation/statutes.nsf/RedirectURL?OpenAgent&query=mrdoc_47905.docx"
NSW_VID = "nsw_legislation:2024-12-06/epi-2014-0179"
NSW_URL = "https://legislation.nsw.gov.au/view/whole/html/inforce/2024-12-06/epi-2014-0179"
ACT_URL = "https://www.legislation.act.gov.au/DownloadFile/ni/2023-540/copy/182892/PDF/2023-540.PDF"
INSTRUMENTS = {
    "QLD": ("Planning Regulation 2017 (Qld)", QLD_URL, "register-text"),
    "WA": ("Planning and Development (Local Planning Schemes) Regulations 2015 (WA)", WA_URL, "register-text"),
    "NSW": ("Shoalhaven Local Environmental Plan 2014 (NSW), Standard Instrument definitions", NSW_URL, "corpus-copy"),
    "ACT": ("Territory Plan 2023 (NI2023-540) (ACT), Part G Dictionary", ACT_URL, "document"),
}
NSW_DROP = {
    "storey",
    "the Act",
    "private open space",
    "waterway",
    "road",
    "demolition",
    "earthworks",
    "canal estate development",
    "residential flat building",
}


def key(url: str) -> str:
    import hashlib

    return "doc-" + hashlib.sha256(url.encode()).hexdigest()[:16]


def qld() -> list[dict]:
    q = L.fetch_doc(QLD_URL, key(QLD_URL))[0].splitlines()
    s3 = max(n for n, x in enumerate(q) if x.startswith("Schedule 3 Use terms for local planning instruments"))
    s4 = next(n for n, x in enumerate(q) if n > s3 and x.startswith("Schedule 4 "))
    d24 = " ".join(q[max(n for n, x in enumerate(q) if x.startswith("Schedule 24 Dictionary")) + 1 :])
    out = []
    found = [
        m.groups()
        for x in q[s3:s4]
        if (m := re.match(r"^(.+?) \1 (see the Planning Regulation 2017 , schedule 24 \.|means .*)$", x))
    ]
    names = [t for t, _ in found]
    for t, d in found:
        if d.startswith("means"):
            out.append({"term": t, "definition": f"{t} {d}", "locator": f"sch 3, use term {t}"})
            continue
        longer = [n for n in names if n != t and n.endswith(" " + t)]
        mm = next(
            (
                m
                for m in re.finditer(re.escape(t) + r"( — \(a\))? means", d24)
                if not any(d24[: m.start() + len(t)].endswith(n) for n in longer)
            ),
            None,
        )
        if not mm:
            raise SystemExit(f"QLD: no definition for {t}")
        seg = d24[mm.start() : mm.start() + 900]
        j = seg.find(". ", len(t) + 6)
        out.append(
            {"term": t, "definition": seg[: j + 1] if j > 0 else seg[:400], "locator": f"sch 24, definition {t}"}
        )
    return out


def wa() -> list[dict]:
    w = L.fetch_doc(WA_URL, key(WA_URL))[0].splitlines()
    i = [n for n, x in enumerate(w) if x.strip().startswith("38. Land use terms used")][-1]
    out, cur = [], None
    for line in w[i + 2 :]:
        line = line.strip()
        if line.startswith(("Part ", "Division ")) or re.match(r"^\d+\.", line):
            break
        m = re.match(r"^([a-z][^.;:]{1,60}?) means (.*)$", line)
        if m:
            cur = {"term": m.group(1).strip(), "definition": line, "locator": f"sch 1 cl 38, {m.group(1).strip()}"}
            out.append(cur)
        elif cur and line:
            cur["definition"] += " " + line
    return out


def nsw() -> list[dict]:
    lines = L.corpus_text(NSW_VID).splitlines()
    a = next(n for n, x in enumerate(lines) if x.strip() == "Land Use Table")
    b = next(n for n, x in enumerate(lines) if n > a and re.match(r"^Part 3\b", x))
    table = " ".join(lines[a:b]).lower()
    d = [n for n, x in enumerate(lines) if x.strip() == "Dictionary"][-1]
    out, prev = [], None
    for line in lines[d:]:
        m = re.match(r"^([a-z][^.;:]{1,70}?) means( |—)(.*)$", line)
        if not m:
            if prev is not None and re.match(r"^\([a-z]+\)", line) and len(prev["definition"]) < 900:
                prev["definition"] += " " + line
            else:
                prev = None
            continue
        prev = None
        t = m.group(1).strip()
        stem = re.escape(t.lower()[:-1]) if len(t) > 4 else re.escape(t.lower())
        use = re.search(
            r"means (a |an |the )?(building or place|building, place|place|land|development|premises|the use of)", line
        ) or line.rstrip().endswith("means—")
        if (re.search(stem, table) or use) and t not in NSW_DROP:
            prev = {"term": t, "definition": line, "locator": f"Dictionary, definition {t}"}
            out.append(prev)
    return out


def act() -> list[dict]:
    pdf = L.CACHE / "act-territory-plan-2023-part-g.pdf"
    if not pdf.exists():
        pdf.parent.mkdir(parents=True, exist_ok=True)
        pdf.write_bytes(L.get(ACT_URL).content)
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    lines = text.splitlines()
    a = [n for n, x in enumerate(lines) if x.strip() == "Table 1 – land use definitions"][-1]
    b = next(n for n, x in enumerate(lines) if n > a and x.strip().startswith("Definitions – terms and concepts"))
    out, cur = [], None
    for line in lines[a + 1 : b]:
        if any(s in line for s in ("Authorised by", "Part G - Dictionary", "Effective:")) or line.strip().startswith(
            ("Definition", "page ")
        ):
            continue
        left = line[:94].strip()
        if not left:
            continue
        if re.match(r"^[a-zA-Zé][^.;:]{1,70}? (has|have) the same meaning", left):
            cur = None
            continue
        m = re.match(r"^([a-zA-Zé][^.;:]{1,70}?) means? (.*)$", left)
        if m and not (cur and cur["definition"].rstrip().endswith(("and", "or", ","))):
            cur = {"term": m.group(1).strip(), "definition": left, "locator": f"Part G, Table 1, {m.group(1).strip()}"}
            out.append(cur)
        elif cur:
            sep = "" if cur["definition"].endswith("-") else " "
            cur["definition"] += sep + left
    raw = " ".join(
        subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True).stdout.split()
    )
    for d in out:
        q = " ".join(d["definition"].split())
        q = re.split(r"(?<=\.) (?=[a-z][a-z’' -]{2,40} (?:means|includes) )|, (?=[a-z][a-z’' -]{2,40} means )", q)[0]
        words = q.split(" ")
        while words and " ".join(words) not in raw:  # keep the verbatim part (the PDF's columns can reorder text)
            words.pop()
        d["definition"] = " ".join(words)
    return out


# Crosswalk: ANZSIC class -> use type -> each state's land-use term.
# Use type -> state terms. 'h' = the term names this kind of use; 'm' = judged from the definition.
U = {
    "ext_ag": {
        "QLD": [("animal husbandry", "h"), ("cropping", "h")],
        "WA": [("agriculture\xa0— extensive", "h")],
        "NSW": [("extensive agriculture", "h")],
        "ACT": [("agriculture", "h")],
    },
    "grazing": {
        "QLD": [("animal husbandry", "h")],
        "WA": [("agriculture\xa0— extensive", "h")],
        "NSW": [("extensive agriculture", "h")],
        "ACT": [("agriculture", "h")],
    },
    "cropping": {
        "QLD": [("cropping", "h")],
        "WA": [("agriculture\xa0— extensive", "h")],
        "NSW": [("extensive agriculture", "h")],
        "ACT": [("agriculture", "h")],
    },
    "hort": {
        "QLD": [("cropping", "h")],
        "WA": [("agriculture\xa0— intensive", "h")],
        "NSW": [("horticulture", "h")],
        "ACT": [("horticulture", "h")],
    },
    "int_plant": {
        "QLD": [("intensive horticulture", "h")],
        "WA": [("agriculture\xa0— intensive", "h")],
        "NSW": [("intensive plant agriculture", "h")],
        "ACT": [("horticulture", "m")],
    },
    "nursery": {
        "QLD": [("wholesale nursery", "h")],
        "WA": [("agriculture\xa0— intensive", "h")],
        "NSW": [("intensive plant agriculture", "m")],
        "ACT": [("horticulture", "m")],
    },
    "turf": {
        "QLD": [("cropping", "m")],
        "WA": [("agriculture\xa0— intensive", "h")],
        "NSW": [("intensive plant agriculture", "m")],
        "ACT": [("horticulture", "m")],
    },
    "viticulture": {
        "QLD": [("cropping", "h")],
        "WA": [("agriculture\xa0— intensive", "h")],
        "NSW": [("horticulture", "m")],
        "ACT": [("horticulture", "m")],
    },
    "int_animal": {
        "QLD": [("intensive animal industry", "h")],
        "WA": [("animal husbandry\xa0— intensive", "h")],
        "NSW": [("intensive livestock agriculture", "h")],
        "ACT": [("intensive animal farming", "h")],
    },
    "poultry": {
        "QLD": [("intensive animal industry", "h")],
        "WA": [("animal husbandry\xa0— intensive", "h")],
        "NSW": [("poultry farm", "h")],
        "ACT": [("intensive animal farming", "h")],
    },
    "pigs": {
        "QLD": [("intensive animal industry", "h")],
        "WA": [("animal husbandry\xa0— intensive", "h")],
        "NSW": [("pig farm", "h")],
        "ACT": [("intensive animal farming", "h")],
    },
    "dairy": {
        "QLD": [("animal husbandry", "m"), ("intensive animal industry", "m")],
        "WA": [("agriculture\xa0— extensive", "m")],
        "NSW": [("intensive livestock agriculture", "h")],
        "ACT": [("agriculture", "m")],
    },
    "bees": {
        "QLD": [("animal husbandry", "m")],
        "WA": [("agriculture\xa0— extensive", "m")],
        "NSW": [("bee keeping", "h")],
        "ACT": [("agriculture", "m")],
    },
    "aqua": {
        "QLD": [("aquaculture", "h")],
        "WA": [("agriculture\xa0— intensive", "h")],
        "NSW": [("pond-based aquaculture", "h"), ("tank-based aquaculture", "h"), ("oyster aquaculture", "h")],
        "ACT": [("agriculture", "m")],
    },
    "forestry": {
        "QLD": [("permanent plantation", "m")],
        "WA": [("tree farm", "h")],
        "NSW": [("forestry", "h")],
        "ACT": [("plantation forestry", "h")],
    },
    "rural_ind": {
        "QLD": [("rural industry", "h")],
        "WA": [("industry\xa0— primary production", "h")],
        "NSW": [("rural industry", "h")],
        "ACT": [("agriculture", "m")],
    },
    "mining": {
        "QLD": [],
        "WA": [("mining operations", "h")],
        "NSW": [("mining", "h"), ("open cut mining", "h")],
        "ACT": [("mining industry", "h")],
    },
    "extractive": {
        "QLD": [("extractive industry", "h")],
        "WA": [("industry\xa0— extractive", "h")],
        "NSW": [("extractive industry", "h")],
        "ACT": [("sand and gravel extraction", "h")],
    },
    "ind_light": {
        "QLD": [("low impact industry", "m"), ("service industry", "m")],
        "WA": [("industry\xa0— light", "m")],
        "NSW": [("light industry", "m")],
        "ACT": [("light industry", "m")],
    },
    "ind_gen": {
        "QLD": [("medium impact industry", "m")],
        "WA": [("industry", "h")],
        "NSW": [("general industry", "m")],
        "ACT": [("general industry", "m")],
    },
    "ind_heavy": {
        "QLD": [("high impact industry", "m"), ("special industry", "m")],
        "WA": [("industry", "h")],
        "NSW": [("heavy industry", "m"), ("hazardous industry", "m"), ("offensive industry", "m")],
        "ACT": [("hazardous industry", "m"), ("offensive industry", "m")],
    },
    "abattoir": {
        "QLD": [("high impact industry", "m")],
        "WA": [("abattoir", "h")],
        "NSW": [("livestock processing industry", "h")],
        "ACT": [("offensive industry", "m")],
    },
    "sawmill": {
        "QLD": [("medium impact industry", "m")],
        "WA": [("industry", "h")],
        "NSW": [("sawmill or log processing works", "h")],
        "ACT": [("general industry", "m")],
    },
    "artisan": {
        "QLD": [("service industry", "m"), ("low impact industry", "m")],
        "WA": [("industry\xa0— light", "m")],
        "NSW": [("artisan food and drink industry", "h")],
        "ACT": [("light industry", "m")],
    },
    "winery": {
        "QLD": [("winery", "h")],
        "WA": [("winery", "h")],
        "NSW": [("artisan food and drink industry", "m"), ("general industry", "m")],
        "ACT": [("light industry", "m"), ("general industry", "m")],
    },
    "brewery": {
        "QLD": [("low impact industry", "m"), ("medium impact industry", "m")],
        "WA": [("brewery", "h")],
        "NSW": [("artisan food and drink industry", "m"), ("general industry", "m")],
        "ACT": [("light industry", "m"), ("general industry", "m")],
    },
    "hightech": {
        "QLD": [("research and technology industry", "h")],
        "WA": [("industry\xa0— light", "m")],
        "NSW": [("high technology industry", "h")],
        "ACT": [("light industry", "m")],
    },
    "marine_ind": {
        "QLD": [("marine industry", "h")],
        "WA": [("industry", "m")],
        "NSW": [("boat building and repair facility", "h")],
        "ACT": [("general industry", "m")],
    },
    "elec_gen": {
        "QLD": [("renewable energy facility", "m"), ("major electricity infrastructure", "m")],
        "WA": [("wind farm", "m")],
        "NSW": [("electricity generating works", "h")],
        "ACT": [("power generation station", "h")],
    },
    "utility": {
        "QLD": [("utility installation", "h"), ("substation", "m")],
        "WA": [],
        "NSW": [("water supply system", "m"), ("sewerage system", "m")],
        "ACT": [("service reticulation", "m"), ("treatment plant", "m")],
    },
    "elec_net": {
        "QLD": [("major electricity infrastructure", "h"), ("substation", "h")],
        "WA": [],
        "NSW": [],
        "ACT": [("major electrical sub-station", "h")],
    },
    "telecom": {
        "QLD": [("telecommunications facility", "h")],
        "WA": [("telecommunications infrastructure", "h")],
        "NSW": [("telecommunications facility", "h")],
        "ACT": [("communications facility", "h")],
    },
    "data_centre": {
        "QLD": [("low impact industry", "m"), ("warehouse", "m")],
        "WA": [("industry\xa0— light", "m")],
        "NSW": [("data centre", "h")],
        "ACT": [("data centre", "h")],
    },
    "waste": {
        "QLD": [("special industry", "m"), ("high impact industry", "m")],
        "WA": [("waste disposal facility", "h"), ("waste storage facility", "m")],
        "NSW": [("waste disposal facility", "h"), ("waste or resource transfer station", "h")],
        "ACT": [("landfill site", "h"), ("waste transfer station", "h")],
    },
    "recovery": {
        "QLD": [("medium impact industry", "m")],
        "WA": [("resource recovery centre", "h")],
        "NSW": [("resource recovery facility", "h")],
        "ACT": [("recycling facility", "h")],
    },
    "depot": {
        "QLD": [("transport depot", "h")],
        "WA": [("transport depot", "h")],
        "NSW": [("transport depot", "h"), ("truck depot", "m")],
        "ACT": [("freight transport facility", "m")],
    },
    "plant_depot": {
        "QLD": [("transport depot", "m")],
        "WA": [("transport depot", "m")],
        "NSW": [("depot", "h")],
        "ACT": [("industrial trades", "m")],
    },
    "freight": {
        "QLD": [("transport depot", "m"), ("warehouse", "m")],
        "WA": [("transport depot", "m")],
        "NSW": [("freight transport facility", "h")],
        "ACT": [("freight transport facility", "h")],
    },
    "warehouse": {
        "QLD": [("warehouse", "h")],
        "WA": [("warehouse/storage", "h")],
        "NSW": [("warehouse or distribution centre", "h")],
        "ACT": [("warehouse", "h"), ("storage facility", "m")],
    },
    "wholesale": {
        "QLD": [("warehouse", "h")],
        "WA": [("warehouse/storage", "h")],
        "NSW": [("wholesale supplies", "h"), ("warehouse or distribution centre", "h")],
        "ACT": [("warehouse", "h")],
    },
    "trade_supplies": {
        "QLD": [("hardware and trade supplies", "h"), ("warehouse", "m")],
        "WA": [("trade supplies", "h")],
        "NSW": [("hardware and building supplies", "m"), ("wholesale supplies", "m")],
        "ACT": [("industrial trades", "h")],
    },
    "fuel_depot": {
        "QLD": [("high impact industry", "m"), ("warehouse", "m")],
        "WA": [("fuel depot", "h")],
        "NSW": [("liquid fuel depot", "h")],
        "ACT": [("liquid fuel depot", "h")],
    },
    "port": {"QLD": [("port service", "h")], "WA": [], "NSW": [("port facilities", "h")], "ACT": []},
    "wharf": {
        "QLD": [("landing", "h"), ("port service", "m")],
        "WA": [],
        "NSW": [("wharf or boating facilities", "h"), ("charter and tourism boating facility", "m")],
        "ACT": [("aquatic recreation facility", "m")],
    },
    "airport": {
        "QLD": [("air service", "h")],
        "WA": [],
        "NSW": [("air transport facility", "h"), ("airport", "h")],
        "ACT": [("airport", "h")],
    },
    "passenger": {
        "QLD": [("transport depot", "m")],
        "WA": [("transport depot", "m")],
        "NSW": [("passenger transport facility", "h"), ("transport depot", "m")],
        "ACT": [("transport facility", "m")],
    },
    "rail": {
        "QLD": [],
        "WA": [],
        "NSW": [("freight transport facility", "m"), ("passenger transport facility", "m")],
        "ACT": [("railway use", "h")],
    },
    "vehicle_sales": {
        "QLD": [("outdoor sales", "h"), ("showroom", "m")],
        "WA": [("motor vehicle, boat or caravan sales", "h")],
        "NSW": [("vehicle sales or hire premises", "h")],
        "ACT": [("vehicle sales", "h")],
    },
    "vehicle_repair": {
        "QLD": [("low impact industry", "m"), ("service industry", "m")],
        "WA": [("motor vehicle repair", "h")],
        "NSW": [("vehicle repair station", "h"), ("vehicle body repair workshop", "h")],
        "ACT": [("industrial trades", "m"), ("light industry", "m")],
    },
    "service_station": {
        "QLD": [("service station", "h")],
        "WA": [("service station", "h")],
        "NSW": [("service station", "h")],
        "ACT": [("service station", "h")],
    },
    "shop": {"QLD": [("shop", "h")], "WA": [("shop", "h")], "NSW": [("shop", "h")], "ACT": [("shop", "h")]},
    "supermarket": {
        "QLD": [("shop", "h")],
        "WA": [("shop", "h")],
        "NSW": [("shop", "h"), ("neighbourhood supermarket", "h")],
        "ACT": [("supermarket", "h"), ("shop", "h")],
    },
    "liquor_store": {
        "QLD": [("shop", "h")],
        "WA": [("liquor store\xa0— small", "h"), ("liquor store\xa0— large", "h")],
        "NSW": [("shop", "h")],
        "ACT": [("shop", "h")],
    },
    "bulky": {
        "QLD": [("showroom", "h")],
        "WA": [("bulky goods showroom", "h")],
        "NSW": [("specialised retail premises", "h")],
        "ACT": [("bulky goods retailing", "h")],
    },
    "hardware": {
        "QLD": [("hardware and trade supplies", "h")],
        "WA": [("trade supplies", "m"), ("bulky goods showroom", "m")],
        "NSW": [("hardware and building supplies", "h"), ("timber yard", "m")],
        "ACT": [("bulky goods retailing", "h")],
    },
    "garden": {
        "QLD": [("garden centre", "h")],
        "WA": [("garden centre", "h")],
        "NSW": [("garden centre", "h"), ("plant nursery", "h"), ("landscaping material supplies", "m")],
        "ACT": [("retail plant nursery", "h"), ("bulk landscape supplies", "m")],
    },
    "rural_supplies": {
        "QLD": [("agricultural supplies store", "h")],
        "WA": [("trade supplies", "m")],
        "NSW": [("rural supplies", "h")],
        "ACT": [("industrial trades", "m")],
    },
    "restricted": {
        "QLD": [("adult store", "h")],
        "WA": [("restricted premises", "h")],
        "NSW": [("restricted premises", "h")],
        "ACT": [("shop", "m")],
    },
    "accom": {
        "QLD": [("short-term accommodation", "h"), ("tourist park", "m"), ("resort complex", "m")],
        "WA": [("hotel", "m"), ("caravan park", "m")],
        "NSW": [
            ("tourist and visitor accommodation", "h"),
            ("hotel or motel accommodation", "h"),
            ("caravan park", "m"),
        ],
        "ACT": [("commercial accommodation use", "h"), ("motel", "h"), ("caravan park/camping ground", "m")],
    },
    "restaurant": {
        "QLD": [("food and drink outlet", "h")],
        "WA": [("restaurant/cafe", "h")],
        "NSW": [("restaurant or cafe", "h"), ("food and drink premises", "h")],
        "ACT": [("restaurant", "h"), ("café", "h")],
    },
    "takeaway": {
        "QLD": [("food and drink outlet", "h")],
        "WA": [("fast food outlet/lunch bar", "h")],
        "NSW": [("take away food and drink premises", "h")],
        "ACT": [("take-away food shop", "h")],
    },
    "catering": {
        "QLD": [("low impact industry", "m"), ("function facility", "m")],
        "WA": [("industry\xa0— light", "m"), ("reception centre", "m")],
        "NSW": [("light industry", "m"), ("function centre", "m")],
        "ACT": [("light industry", "m")],
    },
    "pub": {
        "QLD": [("hotel", "h"), ("bar", "h")],
        "WA": [("hotel", "h"), ("tavern", "h"), ("small bar", "h")],
        "NSW": [("pub", "h")],
        "ACT": [("drink establishment", "h")],
    },
    "club": {
        "QLD": [("club", "h")],
        "WA": [("club premises", "h")],
        "NSW": [("registered club", "h")],
        "ACT": [("club", "h")],
    },
    "office": {
        "QLD": [("office", "h")],
        "WA": [("office", "h")],
        "NSW": [("office premises", "h")],
        "ACT": [("office", "h")],
    },
    "business": {
        "QLD": [("office", "m"), ("shop", "m")],
        "WA": [("office", "m")],
        "NSW": [("business premises", "h")],
        "ACT": [("business agency", "h")],
    },
    "personal": {
        "QLD": [("shop", "h")],
        "WA": [("shop", "h")],
        "NSW": [("business premises", "h")],
        "ACT": [("personal service", "h")],
    },
    "creative": {
        "QLD": [("theatre", "m"), ("office", "m")],
        "WA": [("office", "m")],
        "NSW": [("creative industry", "h")],
        "ACT": [("craft workshop", "m"), ("office", "m")],
    },
    "film": {
        "QLD": [("theatre", "h")],
        "WA": [("office", "m"), ("industry\xa0— light", "m")],
        "NSW": [("creative industry", "h")],
        "ACT": [("office", "m")],
    },
    "research": {
        "QLD": [("research and technology industry", "m"), ("office", "m")],
        "WA": [("office", "m"), ("industry\xa0— light", "m")],
        "NSW": [("high technology industry", "m"), ("office premises", "m")],
        "ACT": [("scientific research establishment", "h")],
    },
    "medical": {
        "QLD": [("health care service", "h")],
        "WA": [("medical centre", "h"), ("consulting rooms", "h")],
        "NSW": [("medical centre", "h"), ("health consulting rooms", "m")],
        "ACT": [("health facility", "h")],
    },
    "hospital": {
        "QLD": [("hospital", "h")],
        "WA": [("hospital", "h")],
        "NSW": [("hospital", "h")],
        "ACT": [("hospital", "h")],
    },
    "res_care": {
        "QLD": [("residential care facility", "h")],
        "WA": [],
        "NSW": [("residential care facility", "h")],
        "ACT": [("residential care accommodation", "h")],
    },
    "child_care": {
        "QLD": [("childcare centre", "h")],
        "WA": [("child care premises", "h")],
        "NSW": [("early education and care facility", "h"), ("centre-based child care facility", "h")],
        "ACT": [("early childhood education and care", "h")],
    },
    "school": {
        "QLD": [("educational establishment", "h")],
        "WA": [("educational establishment", "h")],
        "NSW": [("educational establishment", "h"), ("school", "h")],
        "ACT": [("educational establishment", "h")],
    },
    "tertiary": {
        "QLD": [("educational establishment", "h")],
        "WA": [("educational establishment", "h")],
        "NSW": [("educational establishment", "h")],
        "ACT": [("educational establishment", "h")],
    },
    "training": {
        "QLD": [("educational establishment", "m"), ("indoor sport and recreation", "m")],
        "WA": [("educational establishment", "m")],
        "NSW": [("business premises", "m"), ("recreation facility (indoor)", "m")],
        "ACT": [("educational establishment", "m"), ("indoor recreation facility", "m")],
    },
    "community": {
        "QLD": [("community use", "h"), ("community care centre", "m")],
        "WA": [("community purpose", "h")],
        "NSW": [("community facility", "h")],
        "ACT": [("community activity centre", "h")],
    },
    "gov": {
        "QLD": [("office", "m")],
        "WA": [("civic use", "h")],
        "NSW": [("public administration building", "h")],
        "ACT": [("public agency", "m"), ("office", "m")],
    },
    "justice": {
        "QLD": [("office", "m")],
        "WA": [("civic use", "h")],
        "NSW": [("public administration building", "h")],
        "ACT": [("civic administration", "h")],
    },
    "corrections": {
        "QLD": [("detention facility", "h")],
        "WA": [("corrective institution", "h")],
        "NSW": [],
        "ACT": [("corrections facility", "h")],
    },
    "emergency": {
        "QLD": [("emergency services", "h")],
        "WA": [("civic use", "m")],
        "NSW": [("emergency services facility", "h")],
        "ACT": [("emergency services facility", "h")],
    },
    "defence": {"QLD": [], "WA": [], "NSW": [], "ACT": [("defence installation", "h")]},
    "culture": {
        "QLD": [("community use", "h")],
        "WA": [("art gallery", "m"), ("community purpose", "m")],
        "NSW": [("information and education facility", "h")],
        "ACT": [("cultural facility", "h")],
    },
    "parks": {
        "QLD": [("park", "m"), ("tourist attraction", "m"), ("environment facility", "m")],
        "WA": [],
        "NSW": [("recreation area", "m"), ("environmental facility", "m")],
        "ACT": [("nature conservation area", "m"), ("parkland", "m")],
    },
    "entertainment": {
        "QLD": [("theatre", "h")],
        "WA": [("cinema/theatre", "h")],
        "NSW": [("entertainment facility", "h")],
        "ACT": [("indoor entertainment facility", "h"), ("community theatre", "m")],
    },
    "nightclub": {
        "QLD": [("nightclub entertainment facility", "h")],
        "WA": [("nightclub", "h")],
        "NSW": [("entertainment facility", "m")],
        "ACT": [("indoor entertainment facility", "m")],
    },
    "gym": {
        "QLD": [("indoor sport and recreation", "h")],
        "WA": [("recreation\xa0— private", "h")],
        "NSW": [("recreation facility (indoor)", "h")],
        "ACT": [("indoor recreation facility", "h")],
    },
    "sport_venue": {
        "QLD": [("outdoor sport and recreation", "h"), ("major sport, recreation and entertainment facility", "m")],
        "WA": [("recreation\xa0— private", "m")],
        "NSW": [("recreation facility (outdoor)", "h"), ("recreation facility (major)", "m")],
        "ACT": [("outdoor recreation facility", "h")],
    },
    "racing": {
        "QLD": [("major sport, recreation and entertainment facility", "h"), ("motor sport facility", "m")],
        "WA": [("recreation\xa0— private", "m")],
        "NSW": [("recreation facility (major)", "h")],
        "ACT": [("outdoor recreation facility", "m")],
    },
    "amusement": {
        "QLD": [("tourist attraction", "h"), ("indoor sport and recreation", "m")],
        "WA": [("amusement parlour", "h")],
        "NSW": [("amusement centre", "h"), ("recreation facility (major)", "m")],
        "ACT": [("indoor entertainment facility", "h")],
    },
    "casino": {
        "QLD": [("major sport, recreation and entertainment facility", "m")],
        "WA": [],
        "NSW": [("entertainment facility", "m")],
        "ACT": [("indoor entertainment facility", "m")],
    },
    "betting": {
        "QLD": [("shop", "h")],
        "WA": [("betting agency", "h")],
        "NSW": [("business premises", "m")],
        "ACT": [("shop", "m")],
    },
    "vet": {
        "QLD": [("veterinary service", "h")],
        "WA": [("veterinary centre", "h")],
        "NSW": [("veterinary hospital", "h")],
        "ACT": [("veterinary clinic", "h"), ("veterinary hospital", "h")],
    },
    "animal_est": {
        "QLD": [("animal keeping", "h")],
        "WA": [("animal establishment", "h")],
        "NSW": [("animal boarding or training establishment", "h")],
        "ACT": [("animal care facility", "h")],
    },
    "funeral": {
        "QLD": [("funeral parlour", "h"), ("crematorium", "h"), ("cemetery", "h")],
        "WA": [("funeral parlour", "h")],
        "NSW": [("funeral home", "h"), ("crematorium", "h"), ("cemetery", "h")],
        "ACT": [("funeral parlour", "h"), ("cemetery", "h")],
    },
    "laundry": {
        "QLD": [("service industry", "m"), ("low impact industry", "m")],
        "WA": [("shop", "m"), ("industry\xa0— light", "m")],
        "NSW": [("business premises", "m"), ("light industry", "m")],
        "ACT": [("personal service", "m"), ("light industry", "m")],
    },
    "repair": {
        "QLD": [("service industry", "m")],
        "WA": [("industry\xa0— light", "m")],
        "NSW": [("goods repair and reuse premises", "h"), ("light industry", "m")],
        "ACT": [("light industry", "m"), ("personal service", "m")],
    },
    "parking": {
        "QLD": [("parking station", "h")],
        "WA": [("car park", "h")],
        "NSW": [("car park", "h")],
        "ACT": [("car park", "h")],
    },
    "sex": {"QLD": [], "WA": [], "NSW": [("sex services premises", "h")], "ACT": []},
    "worship": {
        "QLD": [("place of worship", "h")],
        "WA": [("place of worship", "h")],
        "NSW": [("place of public worship", "h")],
        "ACT": [("place of worship", "h"), ("religious associated use", "m")],
    },
    "market": {
        "QLD": [("market", "h")],
        "WA": [("market", "h")],
        "NSW": [("market", "h")],
        "ACT": [("produce market", "m")],
    },
    "hire": {
        "QLD": [("outdoor sales", "m"), ("shop", "m")],
        "WA": [("trade supplies", "m"), ("shop", "m")],
        "NSW": [("vehicle sales or hire premises", "m"), ("retail premises", "m")],
        "ACT": [("industrial trades", "m"), ("shop", "m")],
    },
    "stock_yard": {
        "QLD": [("rural industry", "m")],
        "WA": [],
        "NSW": [("stock and sale yard", "h")],
        "ACT": [("stock/sale yard", "h")],
    },
}

# Group (3-digit) -> list of (use type, confidence of class-to-use match). Class codes (4-digit) override.
G = {
    "011": [("nursery", "h")],
    "012": [("hort", "h")],
    "013": [("hort", "h")],
    "014": [("ext_ag", "h")],
    "015": [("cropping", "h")],
    "016": [("dairy", "h")],
    "017": [("poultry", "h")],
    "018": [("grazing", "h")],
    "019": [("grazing", "m")],
    "020": [("aqua", "h")],
    "030": [("forestry", "h")],
    "041": [],
    "042": [],
    "051": [("forestry", "m")],
    "052": [("rural_ind", "m")],
    "060": [("mining", "h")],
    "070": [("mining", "m")],
    "080": [("mining", "h")],
    "091": [("extractive", "h")],
    "099": [("extractive", "m"), ("mining", "m")],
    "101": [],
    "109": [("plant_depot", "m")],
    "111": [("abattoir", "h")],
    "112": [("ind_gen", "m")],
    "113": [("ind_gen", "m")],
    "114": [("ind_gen", "m")],
    "115": [("ind_gen", "m")],
    "116": [("ind_gen", "m")],
    "117": [("ind_gen", "m")],
    "118": [("ind_gen", "m")],
    "119": [("ind_gen", "m")],
    "121": [("ind_gen", "m")],
    "122": [("ind_gen", "m")],
    "131": [("ind_gen", "m")],
    "132": [("ind_heavy", "m")],
    "133": [("ind_light", "m"), ("ind_gen", "m")],
    "134": [("ind_light", "m")],
    "135": [("ind_light", "m")],
    "141": [("sawmill", "h")],
    "149": [("ind_gen", "m")],
    "151": [("ind_heavy", "m")],
    "152": [("ind_gen", "m")],
    "161": [("ind_light", "m")],
    "162": [("ind_light", "m")],
    "170": [("ind_heavy", "h")],
    "181": [("ind_heavy", "h")],
    "182": [("ind_heavy", "m")],
    "183": [("ind_heavy", "h")],
    "184": [("ind_gen", "m")],
    "185": [("ind_gen", "m")],
    "189": [("ind_heavy", "m")],
    "191": [("ind_gen", "m")],
    "192": [("ind_gen", "m")],
    "201": [("ind_heavy", "m")],
    "202": [("ind_heavy", "m")],
    "203": [("ind_heavy", "m")],
    "209": [("ind_gen", "m")],
    "211": [("ind_heavy", "h")],
    "212": [("ind_heavy", "m")],
    "213": [("ind_heavy", "h")],
    "214": [("ind_gen", "m")],
    "221": [("ind_heavy", "m")],
    "222": [("ind_gen", "m")],
    "223": [("ind_gen", "m")],
    "224": [("ind_gen", "m")],
    "229": [("ind_gen", "m")],
    "231": [("ind_gen", "m")],
    "239": [("ind_gen", "m")],
    "241": [("ind_light", "m"), ("hightech", "m")],
    "242": [("hightech", "m"), ("ind_light", "m")],
    "243": [("ind_gen", "m")],
    "244": [("ind_gen", "m")],
    "245": [("ind_gen", "m")],
    "246": [("ind_gen", "m")],
    "249": [("ind_gen", "m")],
    "251": [("ind_gen", "m")],
    "259": [("ind_light", "m")],
    "261": [("elec_gen", "h")],
    "262": [("elec_net", "h")],
    "263": [("elec_net", "h"), ("utility", "m")],
    "264": [("office", "m")],
    "270": [("utility", "m")],
    "281": [("utility", "h")],
    "291": [("depot", "m")],
    "292": [("waste", "h"), ("recovery", "m")],
    "301": [("plant_depot", "m"), ("office", "m")],
    "302": [("plant_depot", "m"), ("office", "m")],
    "310": [("plant_depot", "m")],
    "321": [("office", "m"), ("plant_depot", "m")],
    "322": [("plant_depot", "m")],
    "323": [("plant_depot", "m")],
    "324": [("plant_depot", "m")],
    "329": [("plant_depot", "m")],
    "331": [("wholesale", "h")],
    "332": [("wholesale", "h")],
    "333": [("wholesale", "h"), ("trade_supplies", "m")],
    "341": [("wholesale", "h"), ("trade_supplies", "m")],
    "349": [("wholesale", "h")],
    "350": [("wholesale", "h")],
    "360": [("wholesale", "h")],
    "371": [("wholesale", "h")],
    "372": [("wholesale", "h")],
    "373": [("wholesale", "h")],
    "380": [("office", "m")],
    "391": [("vehicle_sales", "h")],
    "392": [("bulky", "m"), ("shop", "m")],
    "400": [("service_station", "h")],
    "411": [("supermarket", "h")],
    "412": [("shop", "h")],
    "421": [("bulky", "h")],
    "422": [("bulky", "m"), ("shop", "m")],
    "423": [("hardware", "h")],
    "424": [("shop", "h")],
    "425": [("shop", "h")],
    "426": [("shop", "h")],
    "427": [("shop", "h")],
    "431": [("warehouse", "m"), ("office", "m")],
    "432": [("office", "m")],
    "440": [("accom", "h")],
    "451": [("restaurant", "h")],
    "452": [("pub", "h")],
    "453": [("club", "h")],
    "461": [("depot", "h")],
    "462": [("passenger", "h")],
    "471": [("rail", "h"), ("freight", "m")],
    "472": [("rail", "h"), ("passenger", "m")],
    "481": [("port", "h")],
    "482": [("wharf", "h")],
    "490": [("airport", "h")],
    "501": [("wharf", "m"), ("airport", "m")],
    "502": [("utility", "m")],
    "510": [("freight", "m"), ("business", "m")],
    "521": [("port", "h")],
    "522": [("airport", "h")],
    "529": [("office", "m"), ("freight", "m")],
    "530": [("warehouse", "h")],
    "541": [("office", "h")],
    "542": [("office", "h")],
    "551": [("film", "h")],
    "552": [("creative", "h")],
    "561": [("office", "m")],
    "562": [("office", "m")],
    "570": [("office", "h")],
    "580": [("telecom", "h")],
    "591": [("office", "h")],
    "592": [("data_centre", "h")],
    "601": [("culture", "h")],
    "602": [("office", "h")],
    "621": [("office", "h")],
    "622": [("business", "h")],
    "623": [("office", "h")],
    "624": [("office", "h")],
    "631": [("office", "h")],
    "632": [("office", "h")],
    "633": [("office", "h")],
    "641": [("office", "h")],
    "642": [("office", "h")],
    "661": [("vehicle_sales", "m"), ("hire", "m")],
    "662": [],
    "663": [("hire", "h")],
    "664": [("office", "m")],
    "671": [("office", "m")],
    "672": [("business", "h")],
    "691": [("research", "h")],
    "692": [("office", "h")],
    "693": [("office", "h")],
    "694": [("office", "h")],
    "695": [("office", "h")],
    "696": [("office", "h")],
    "697": [("vet", "h")],
    "699": [("office", "m")],
    "700": [("office", "h")],
    "721": [("office", "h")],
    "722": [("business", "h")],
    "729": [("office", "h")],
    "731": [("plant_depot", "m")],
    "732": [("ind_light", "m"), ("warehouse", "m")],
    "751": [("gov", "h")],
    "752": [("gov", "h")],
    "753": [("gov", "h")],
    "754": [("justice", "h")],
    "755": [("gov", "m")],
    "760": [("defence", "h")],
    "771": [("emergency", "h")],
    "772": [("gov", "h")],
    "801": [("child_care", "h")],
    "802": [("school", "h")],
    "810": [("tertiary", "h")],
    "821": [("training", "m")],
    "822": [("office", "m")],
    "840": [("hospital", "h")],
    "851": [("medical", "h")],
    "852": [("medical", "h")],
    "853": [("medical", "h")],
    "859": [("medical", "m")],
    "860": [("res_care", "h")],
    "871": [("child_care", "h")],
    "879": [("community", "m")],
    "891": [("culture", "h")],
    "892": [("parks", "m")],
    "900": [("entertainment", "h")],
    "911": [("gym", "h")],
    "912": [("racing", "h")],
    "913": [("amusement", "h")],
    "920": [("betting", "h")],
    "941": [("vehicle_repair", "h")],
    "942": [("repair", "h")],
    "949": [("repair", "h")],
    "951": [("personal", "h")],
    "952": [("funeral", "h")],
    "953": [("personal", "m")],
    "954": [("worship", "h")],
    "955": [("office", "h")],
    "960": [],
}
C = {
    "0113": [("turf", "h")],
    "0114": [("int_plant", "h")],
    "0115": [("hort", "h")],
    "0121": [("int_plant", "h")],
    "0122": [("int_plant", "h")],
    "0131": [("viticulture", "h")],
    "0143": [("int_animal", "h")],
    "0146": [("cropping", "h")],
    "0149": [("cropping", "h")],
    "0191": [("grazing", "m"), ("animal_est", "m")],
    "0192": [("pigs", "h")],
    "0193": [("bees", "h")],
    "0201": [("aqua", "m")],
    "0202": [("aqua", "m")],
    "0302": [("forestry", "h")],
    "0521": [("rural_ind", "h")],
    "0522": [("rural_ind", "m")],
    "1111": [("abattoir", "h")],
    "1112": [("abattoir", "h")],
    "1113": [("ind_gen", "m")],
    "1174": [("artisan", "h"), ("shop", "m")],
    "1212": [("brewery", "h")],
    "1213": [("brewery", "m")],
    "1214": [("winery", "h")],
    "1311": [("ind_heavy", "m")],
    "1831": [("ind_heavy", "h")],
    "1892": [("ind_heavy", "h")],
    "2033": [("ind_heavy", "m")],
    "2034": [("ind_gen", "m")],
    "2391": [("marine_ind", "h")],
    "2392": [("marine_ind", "h")],
    "2394": [("ind_gen", "m"), ("airport", "m")],
    "2591": [("ind_light", "h")],
    "2911": [("depot", "m")],
    "2919": [("depot", "m")],
    "2921": [("waste", "h")],
    "2922": [("recovery", "h")],
    "3311": [("wholesale", "h")],
    "3321": [("fuel_depot", "h"), ("wholesale", "m")],
    "3331": [("wholesale", "h"), ("hardware", "m")],
    "3505": [("recovery", "m"), ("wholesale", "m")],
    "3606": [("wholesale", "h")],
    "4123": [("liquor_store", "h")],
    "4232": [("garden", "h")],
    "4245": [("vehicle_sales", "m"), ("shop", "m")],
    "4273": [("shop", "h")],
    "4513": [("catering", "h")],
    "4512": [("takeaway", "h")],
    "4623": [("depot", "m")],
    "5101": [("business", "m")],
    "5211": [("port", "h")],
    "5212": [("port", "h"), ("wharf", "m")],
    "5219": [("port", "m"), ("wharf", "m")],
    "5292": [("office", "m"), ("freight", "m")],
    "5291": [("office", "h")],
    "5301": [("rural_ind", "m"), ("warehouse", "m")],
    "5513": [("entertainment", "h")],
    "5512": [("office", "m")],
    "5514": [("film", "h")],
    "5521": [("office", "h")],
    "6010": [("culture", "h")],
    "6221": [("business", "h")],
    "6222": [("business", "h")],
    "6223": [("business", "h")],
    "6229": [("office", "m")],
    "6611": [("vehicle_sales", "h")],
    "6619": [("vehicle_sales", "m")],
    "6631": [("plant_depot", "m"), ("hire", "m")],
    "6711": [],
    "6712": [("office", "m")],
    "6925": [("research", "m"), ("ind_light", "m")],
    "6991": [("business", "m"), ("creative", "m")],
    "7712": [("office", "h")],
    "7714": [("corrections", "h")],
    "7311": [("plant_depot", "m")],
    "7313": [("plant_depot", "m")],
    "8211": [("gym", "m"), ("training", "m")],
    "8212": [("training", "m"), ("creative", "m")],
    "8591": [("emergency", "m")],
    "8921": [("parks", "m"), ("amusement", "m")],
    "9001": [("entertainment", "m"), ("creative", "m")],
    "9002": [("creative", "h")],
    "9003": [("entertainment", "h")],
    "9113": [("sport_venue", "h")],
    "9112": [("sport_venue", "m"), ("club", "m")],
    "9114": [("office", "m")],
    "9121": [("racing", "h")],
    "9129": [("animal_est", "m"), ("racing", "m")],
    "9201": [("casino", "h")],
    "9202": [("betting", "h")],
    "9209": [("betting", "h")],
    "9412": [("vehicle_repair", "h")],
    "9512": [("personal", "h")],
    "9531": [("laundry", "h")],
    "9532": [("personal", "m")],
    "9533": [("parking", "h")],
    "9534": [("sex", "h")],
    "9539": [("personal", "m")],
    "0420": [],
    "0411": [],
    "0412": [],
    "0413": [],
    "0414": [],
    "0419": [],
    "6620": [],
}


RANK = {"h": 2, "m": 1}


def confidence(a: str, b: str) -> str:
    return {4: "high", 3: "medium", 2: "low"}[RANK[a] + RANK[b]]


def main() -> None:
    defs = {"QLD": qld(), "WA": wa(), "NSW": nsw(), "ACT": act()}
    terms = {s: {d["term"] for d in v} for s, v in defs.items()}
    for u, by in U.items():
        for s, lst in by.items():
            for t, _ in lst:
                if t not in terms[s]:
                    raise SystemExit(f"{s}: crosswalk term {t!r} ({u}) not in the definitions")
    with open(OUT / "land_use_definitions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state", "term", "definition", "instrument", "locator", "url", "checked"])
        for s, v in defs.items():
            inst, url, checked = INSTRUMENTS[s]
            for d in v:
                w.writerow(
                    [
                        s,
                        d["term"].replace("\xa0", " "),
                        " ".join(d["definition"].split()),
                        inst,
                        d["locator"].replace("\xa0", " "),
                        url,
                        checked,
                    ]
                )
    rows = []
    with open(CLASSES, encoding="utf-8") as f:
        classes = list(csv.DictReader(f))
    for r in classes:
        uses = C.get(r["class"], G.get(r["group"]))
        if uses is None:
            raise SystemExit(f"no crosswalk for class {r['class']}")
        for s in defs:
            if not uses:
                rows.append(
                    [
                        s,
                        r["class"],
                        r["class_name"],
                        "",
                        "",
                        "",
                        "no premises use: the activity is not carried on at fixed premises a planning scheme regulates",
                    ]
                )
                continue
            for u, c1 in uses:
                matches = U[u][s]
                if not matches:
                    rows.append(
                        [
                            s,
                            r["class"],
                            r["class_name"],
                            u,
                            "",
                            "",
                            f"no standard term in {s} for this use; a local scheme or other law governs it",
                        ]
                    )
                for t, c2 in matches:
                    rows.append([s, r["class"], r["class_name"], u, t.replace("\xa0", " "), confidence(c1, c2), ""])
    with open(OUT / "land_use_terms.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state", "anzsic_class", "class_name", "use_type", "term", "confidence", "note"])
        w.writerows(rows)
    n = {s: len(v) for s, v in defs.items()}
    print(f"definitions {n}; {len(rows)} class-term rows")


if __name__ == "__main__":
    main()
