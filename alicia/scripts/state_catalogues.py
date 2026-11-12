"""Phase D, batch D-2: a catalogue of the laws in force in each state and territory (methods rule 10).

One file per jurisdiction, ``data/processed/legislation/<state>_catalogue.csv`` (metadata only, no law texts), with
the Commonwealth catalogue's columns plus where each row was listed from and a signal score:

- **NSW, Qld, WA, SA, Tas:** the Open Australian Legal Corpus index (``oalc_laws.csv.gz``), laws in force when the
  corpus scraped each register (by 10 March 2025; ``as_at`` keeps the date). Rows the corpus marks as repealed are
  dropped. The NSW and SA registers refuse automated requests; the Queensland register's lists load by script; so
  the corpus is the list for all five (plan_states.md). The signal score reads each law's corpus text.
- **Victoria:** the register's sitemap (in-force Acts and statutory rules), then each in-force page's title, number
  and latest version date, fetched with the 2-second delay its robots.txt asks for (``fetch-vic``). The register's
  document server is not used: its robots.txt disallows automated fetching. The score reads the title only.
- **Northern Territory:** the register's in-force lists by title, Acts and subordinate legislation (``fetch-nt``).
  The score reads the title only.
- **ACT:** not fetched. The register's in-force lists are under ``/results``, which its robots.txt disallows, and
  AustLII's robots.txt bars Anthropic's agents. The owner saved the two lists from a browser on 12 November 2026
  (Acts in force, 348 entries; subordinate laws in force, 227), kept as ``data/raw/state_registers/act_acts.html`` and
  ``act_subordinate.html`` (not committed). Entries for a former name ("See ...") are skipped; Commonwealth Acts
  listed by the ACT register are set aside, as the Commonwealth catalogue holds them. The score reads the title only.

Then, for every jurisdiction:

1. **Title triage** sets aside series that never oblige businesses directly (appropriations, amending and
   commencement laws, appointments, naming orders, validations, parliamentary and judicial office), with the reason.
2. **Signals.** A score from the law's text (or title) for licences, registration, levies and duties, offences and
   business words; ``high``, ``medium`` or ``low``. Laws with the strongest signals are screened first (plan_states.md,
   method 2). The score orders the work; it is not a call.
3. **Calls already made.** Laws cited by an existing state requirement are called Y, with the requirement ids.
   Calls made by hand are kept when the catalogue is rebuilt.

Usage (in alicia/):
    uv run python scripts/state_catalogues.py fetch-vic   # about 45 minutes; resumes where it stopped
    uv run python scripts/state_catalogues.py fetch-nt
    uv run python scripts/state_catalogues.py build
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
LEG = ROOT / "data" / "processed" / "legislation"
RAW = ROOT / "data" / "raw" / "state_registers"
OALC = ROOT / "data" / "raw" / "oalc"
MANIFEST = ROOT / "data" / "manifests" / "state_catalogues.json"
REQS = ROOT / "regulation-register" / "requirements"
HEADERS = {"User-Agent": "alicia-research/0.1 (non-commercial research)"}
VIC = "https://www.legislation.vic.gov.au"
NT = "https://legislation.nt.gov.au"
CORPUS = {
    "NSW": "new_south_wales",
    "QLD": "queensland",
    "WA": "western_australia",
    "SA": "south_australia",
    "TAS": "tasmania",
}
STATES = ("NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT")
FIELDS = [
    "register_id",
    "name",
    "collection",
    "year",
    "url",
    "listed_from",
    "as_at",
    "triage",
    "signal",
    "signals",
    "call",
    "requirements",
    "reason",
]
# Title triage (methods rule 10), for state titles. Anything not matched goes to screening.
TRIAGE = [
    (r"\(Cwlth\)", "a Commonwealth Act (screened in the Commonwealth catalogue)"),
    (r"\bAppropriation\b|Supply Act", "appropriation"),
    (
        r"\bAmendment\b|\bAmending\b|\(Amendment|Statute Law|Miscellaneous (Acts|Provisions)|"
        r"\bRepeal\b|Consequential|Savings and Transitional|Transitional (Provisions|Arrangements)",
        "amending, repealing or transitional law",
    ),
    (r"Commencement|Proclamation", "commencement order or proclamation"),
    (r"\bAppointment|\bDelegation", "appointment or delegation"),
    (r"\bNaming\b|Place Names?|Geographical Names|Name of", "naming"),
    (r"Validation|Validating", "validation of past acts"),
    (
        r"Parliament|Electoral|Constitution\b|Governor|Ministers? of the Crown|Judges|Judicial|Remuneration Tribunal|"
        r"Members of Parliament|Legislative (Council|Assembly)",
        "parliament, elections or public office",
    ),
    (r"Superannuation \(|Superannuation Act|Pension", "public sector superannuation or pensions"),
    (r"\bGrant\b.*\bLand\b|Land Grant|Vesting|Revocation of Dedication|Trust Deed|Private Act", "a grant or vesting"),
    (r"\b\d+ (Vic|Will|Geo|Edw)\b", "an old Act cited by its regnal year (Imperial, private or local)"),
    (
        r"(?<!Real )Estate (Act|Leasing)|Church|Cathedral|Chapel|Trust Estate|Land Sale Act",
        "a private Act about named property or a named body",
    ),
]
SIGNALS = [  # (name, pattern, weight) over a law's text; titles use TITLE_SIGNALS
    (
        "licensing offence",
        r"must not\b[^.;]{0,200}\bunless\b[^.;]{0,120}\b(licen[cs]|regist|permit|accredit|approv)",
        3,
    ),
    ("licence", r"\blicen[cs]e[ds]?\b|\bpermit holder\b|\baccredit", 1),
    ("registration", r"\bregist(er|ration|ered)\b", 1),
    ("levy or duty", r"\b(levy|duty|tax|royalt(y|ies))\b[^.;]{0,80}\b(payable|is liable|must pay|imposed)", 2),
    ("offence", r"\bmaximum penalty\b|\bpenalty units?\b|\bcommits an offence\b", 1),
    ("business", r"\b(business|employer|operator of|occupier of|trader|premises)\b", 1),
]
TITLE_SIGNALS = [
    ("licence", r"Licen[cs]|Permit|Accredit|Registration|Registered", 2),
    ("levy or duty", r"Levy|Levies|Tax\b|Duties|Duty\b|Royalt|Fees|Charges", 2),
    ("industry", r"Industry|Trading|Trade|Business|Dealers?|Agents?|Contractors?|Operators?|Retail", 1),
    ("safety or standards", r"Safety|Standards?|Code\b|Hazard|Dangerous|Environment|Protection", 1),
]


def get(client: httpx.Client, url: str) -> httpx.Response:
    for attempt in range(4):
        try:
            r = client.get(url, timeout=60)
            if r.status_code < 500:
                return r
        except httpx.HTTPError:
            pass
        time.sleep(2 ** (attempt + 1))
    raise SystemExit(f"could not fetch {url}")


# ---- Victoria: sitemap, then each in-force page (2-second delay, robots.txt)
def fetch_vic() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / "vic_index.jsonl"
    done = {json.loads(x)["url"] for x in out.read_text("utf-8").splitlines()} if out.exists() else set()
    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        index = get(client, f"{VIC}/sitemap.xml").text
        pages = re.findall(r"<loc>([^<]+)</loc>", index)
        urls = []
        for p in pages:
            time.sleep(2)
            urls += [
                u
                for u in re.findall(r"<loc>([^<]+)</loc>", get(client, p).text)
                if re.match(rf"{VIC}/in-force/(acts|statutory-rules)/[^/]+$", u)
            ]
        (RAW / "vic_sitemap.txt").write_text("\n".join(sorted(set(urls))) + "\n", "utf-8")
        todo = [u for u in sorted(set(urls)) if u not in done]
        print(f"{len(set(urls))} in-force titles in the sitemap; {len(todo)} to fetch", flush=True)
        with out.open("a", encoding="utf-8") as fh:
            for i, u in enumerate(todo):
                time.sleep(2)
                r = get(client, u)
                s = r.text
                title = re.search(r"<title>(.*?) \| legislation\.vic\.gov\.au</title>", s)
                number = re.search(r"(Act|SR) number ([0-9A-Za-z/.-]+)", s)
                latest = re.search(r'"(\d{4}-\d{2}-\d{2})","[0-9A-Z]+","In force"', s)
                rec = {
                    "url": u,
                    "status": r.status_code,
                    "title": title.group(1).replace("&amp;", "&").strip() if title else None,
                    "number": number.group(2) if number else None,
                    "version_date": latest.group(1) if latest else None,
                    "collection": "Act" if "/in-force/acts/" in u else "Statutory rule",
                    "fetched": dt.date.today().isoformat(),
                }
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
                if i % 100 == 0:
                    print(f"  {i + 1}/{len(todo)} {rec['title']}", flush=True)


# ---- Northern Territory: the in-force lists by title
def fetch_nt() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    rows = []
    for path, coll in (
        ("/en/LegislationPortal/Acts/By-Title?status=inforce", "Act"),
        ("/en/LegislationPortal/Subordinate-Legislation/By-Title?status=inforce", "Subordinate legislation"),
    ):
        # A fresh client for each list: the portal keeps the last list in a session cookie.
        with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
            s = get(client, NT + path).text
        # Only the A-Z list's entries (they carry replaceHistory), not the menu's links.
        for href, name in re.findall(r'<a href="(/en/Legislation/[^"]+)" onclick="replaceHistory[^>]*>([^<]+)</a>', s):
            rows.append({"url": NT + href, "title": name.strip(), "collection": coll})
        time.sleep(5)
    seen, out = set(), []
    for r in rows:
        if r["url"] not in seen:
            seen.add(r["url"])
            out.append(r | {"fetched": dt.date.today().isoformat()})
    (RAW / "nt_index.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), "utf-8")
    print(f"NT: {sum(r['collection'] == 'Act' for r in out)} Acts, {sum(r['collection'] != 'Act' for r in out)} others")


# ---- Building the catalogues
def triage(name: str) -> str:
    return next((why for pat, why in TRIAGE if re.search(pat, name)), "")


def score(text: str, table: list) -> tuple[int, list[str]]:
    hits = [(n, w) for n, pat, w in table if re.search(pat, text, re.I if table is SIGNALS else 0)]
    return sum(w for _, w in hits), [n for n, _ in hits]


def band(points: int, text_based: bool) -> str:
    hi, mid = (6, 3) if text_based else (3, 2)
    return "high" if points >= hi else "medium" if points >= mid else "low"


def year_of(name: str) -> str:
    m = re.search(r"\b(1[89]\d\d|20\d\d)\b", name)
    return m.group(1) if m else ""


def clean(citation: str) -> str:
    return re.sub(r"\s*\((NSW|Qld|WA|SA|Tas)\)\s*$", "", citation).strip()


def corpus_rows(state: str) -> list[dict]:
    texts: dict[str, str] = {}
    with gzip.open(OALC / f"{CORPUS[state]}.jsonl.gz", "rt", encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            texts[d["version_id"]] = d.get("text", "")
    rows = []
    with gzip.open(LEG / "oalc_laws.csv.gz", "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["jurisdiction"] != CORPUS[state] or "(Repealed)" in r["citation"]:
                continue
            name = clean(r["citation"])
            points, hits = score(texts.get(r["version_id"], ""), SIGNALS)
            rows.append(
                {
                    "register_id": r["url"].rstrip("/").split("/")[-1].split("=")[-1],
                    "name": name,
                    "collection": "Act" if r["type"] == "primary_legislation" else "Instrument",
                    "year": year_of(name),
                    "url": r["url"],
                    "listed_from": "Open Australian Legal Corpus v7.1.0",
                    "as_at": r["when_scraped"][:10],
                    "triage": triage(name),
                    "signal": band(points, True),
                    "signals": "; ".join(hits),
                }
            )
    return rows


SMALL = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to", "under", "with"}


def titlecase(text: str) -> str:
    """'AGENTS LICENSING ACT 1979' or 'agents-licensing-act-1979' to 'Agents Licensing Act 1979'."""
    words = re.split(r"(\s+|-)", text.lower()) if text.isupper() else text.replace("-", " ").split(" ")
    words = [w for w in words if w and w != "-"] if not text.isupper() else words
    out, first = [], True
    for w in words:
        if not w.strip():
            out.append(w)
            continue
        bare = w.strip("()")
        out.append(w if (bare in SMALL and not first) else w.replace(bare, bare[:1].upper() + bare[1:], 1))
        first = False
    return "".join(out) if text.isupper() else " ".join(out)


ACT_PAGES = {"Act": RAW / "act_acts.html", "Subordinate law": RAW / "act_subordinate.html"}


def act_records() -> list[dict]:
    """The ACT's lists of laws in force, from the pages the owner saved. A row for a former name ("See ...") points
    to the current name's own row, so it is skipped."""
    import html

    recs, seen = [], set()
    for coll, path in ACT_PAGES.items():
        if not path.exists():
            continue
        saved = dt.date.fromtimestamp(path.stat().st_mtime).isoformat()
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", path.read_text("utf-8", errors="replace"), re.S):
            if 'class="previous-name"' in row:
                continue
            link = re.search(r'<a href="(https://www\.legislation\.act\.gov\.au/(?:a|sl)/[^"]+)">([^<]+)</a>', row)
            if not link or link.group(1) in seen:
                continue
            seen.add(link.group(1))
            number = re.search(r'<td data-order="\d+">\s*([A-Z]+\d{4}-\d+)\s*</td>', row)
            recs.append(
                {
                    "url": link.group(1),
                    "title": html.unescape(link.group(2)).strip(),
                    "number": number.group(1) if number else None,
                    "collection": "Act" if coll == "Act" else coll,
                    "fetched": saved,
                }
            )
    return recs


def index_rows(state: str) -> list[dict]:
    path = RAW / f"{state.lower()}_index.jsonl"
    recs = [json.loads(x) for x in path.read_text("utf-8").splitlines()] if path.exists() else []
    if state == "ACT":
        recs = act_records()
    if state == "VIC":  # every in-force title in the sitemap; a page not yet read is named from its address
        have = {d["url"] for d in recs if d.get("title")}
        site = RAW / "vic_sitemap.txt"
        for u in site.read_text("utf-8").split() if site.exists() else []:
            if u not in have:
                coll = "Act" if "/in-force/acts/" in u else "Statutory rule"
                recs.append(
                    {
                        "url": u,
                        "title": titlecase(u.rstrip("/").split("/")[-1]),
                        "collection": coll,
                        "fetched": "",
                        "from_address": True,
                    }
                )
    rows = []
    for d in recs:
        if not d.get("title"):
            continue
        name = titlecase(d["title"]) if d["title"].isupper() else d["title"]
        points, hits = score(name, TITLE_SIGNALS)
        source = {
            "VIC": "Victorian Legislation register",
            "NT": "NT Legislation register",
            "ACT": "ACT Legislation Register (lists saved by the owner)",
        }[state]
        rows.append(
            {
                "register_id": d.get("number") or d["url"].rstrip("/").split("/")[-1],
                "name": name,
                "collection": "Act" if d["collection"] == "Act" else "Instrument",
                "year": year_of(name),
                "url": d["url"],
                "listed_from": source + (" sitemap (name from the address)" if d.get("from_address") else ""),
                "as_at": d.get("fetched", ""),
                "triage": triage(name),
                "signal": band(points, False),
                "signals": "; ".join(hits) + (" (title only)" if hits else ""),
            }
        )
    return rows


PLACES = (
    r"New South Wales|Victoria|Queensland|Western Australia|South Australia|Tasmania|Northern Territory|"
    r"Australian Capital Territory"
)


def norm(name: str) -> str:
    """A key for matching a law's name across sources: lower case, no punctuation, no jurisdiction in brackets or
    after the year (the register's requirements write "Local Government Act 1993 New South Wales")."""
    name = re.sub(r"\((NSW|Vic|Qld|WA|SA|Tas|ACT|NT)\)", "", name, flags=re.I)
    name = re.sub(rf"(\d{{4}})\s+({PLACES})\s*$", r"\1", name)
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def cited_laws() -> dict[str, list[tuple[str, str, str]]]:
    """For each state, the laws its requirements cite: (name, url, requirement id)."""
    out: dict[str, list] = defaultdict(list)
    for p in sorted(REQS.glob("*/*.json")) + sorted(REQS.glob("local/*/*.json")):
        q = json.loads(p.read_text("utf-8"))
        if q.get("tier") == "cth":
            continue
        for law in q.get("laws", []):
            if re.search(r"Local Law|By-?Law", law["title"], re.I):  # councils' own laws are phase E
                continue
            out[q["jurisdiction"]].append((law["title"], law.get("register_url") or "", q["id"]))
    return out


def build() -> None:
    cited = cited_laws()
    summary = {}
    for state in STATES:
        rows = corpus_rows(state) if state in CORPUS else index_rows(state)
        path = LEG / f"{state.lower()}_catalogue.csv"
        kept = {}
        if path.exists():
            with path.open(encoding="utf-8", newline="") as fh:
                kept = {r["url"]: r for r in csv.DictReader(fh) if r.get("call") and r.get("reason")}
        by_key = {norm(r["name"]): r for r in rows}
        unmatched = []
        for name, url, rid in cited.get(state, []):
            r = by_key.get(norm(name))
            if r is None:
                unmatched.append((name, url, rid))
                continue
            ids = set(filter(None, r.get("requirements", "").split()))
            ids.add(rid)
            r["requirements"] = " ".join(sorted(ids))
            r["call"] = "Y"
            r["reason"] = "Cited by an existing requirement (calibration or D-1)"
        # A law cited by a requirement but missing from the list (the ACT, or a title spelt differently) is added,
        # so the catalogue accounts for every law the register uses.
        for name, url, rid in unmatched:
            key = norm(name)
            if key in by_key:
                r = by_key[key]
                r["requirements"] = " ".join(sorted(set(r["requirements"].split()) | {rid}))
                continue
            by_key[key] = r = {
                "register_id": url.rstrip("/").split("/")[-1] if url else "",
                "name": name,
                "collection": "Act" if re.search(r"\bAct\b", name) else "Instrument",
                "year": year_of(name),
                "url": url,
                "listed_from": "Cited by a requirement (not in the list read)",
                "as_at": "",
                "triage": "",
                "signal": "",
                "signals": "",
                "call": "Y",
                "requirements": rid,
                "reason": "Cited by an existing requirement (calibration or D-1)",
            }
            rows.append(r)
        for r in rows:
            old = kept.get(r["url"])
            if old and not r.get("call"):
                r.update({k: old[k] for k in ("call", "requirements", "reason")})
            for k in FIELDS:
                r.setdefault(k, "")
        rows.sort(key=lambda r: (r["collection"] != "Act", r["name"].lower()))
        with path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        screen = [r for r in rows if not r["triage"]]
        summary[state] = {
            "listed": len(rows),
            "acts": sum(r["collection"] == "Act" for r in rows),
            "instruments": sum(r["collection"] != "Act" for r in rows),
            "set_aside_by_triage": len(rows) - len(screen),
            "to_screen": len(screen),
            "signal": dict(Counter(r["signal"] or "none" for r in screen)),
            "called": dict(Counter(r["call"] for r in rows if r["call"])),
            "cited_not_listed": sum(r["listed_from"].startswith("Cited") for r in rows),
            "source": rows[0]["listed_from"] if rows and not rows[0]["listed_from"].startswith("Cited") else "",
        }
        print(state, json.dumps(summary[state]))
    MANIFEST.write_text(
        json.dumps(
            {
                "built": dt.date.today().isoformat(),
                "sources": {
                    "corpus": "Open Australian Legal Corpus v7.1.0 (Isaacus), CC BY 4.0: NSW, Qld, WA, SA, Tas",
                    "VIC": f"{VIC}/sitemap.xml and each in-force page (robots.txt crawl-delay 2)",
                    "NT": f"{NT}/en/LegislationPortal/Acts/By-Title?status=inforce and Subordinate-Legislation",
                    "ACT": "the register's in-force lists, saved from a browser by the owner (12 Nov 2026); "
                    "not fetched, as /results is disallowed by robots.txt",
                },
                "summary": summary,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


# ---- Re-estimate (plan_states.md, D-2): the work left, from the measured catalogues
SAMPLE = LEG / "screening_sample.csv"
CTH = LEG / "cth_catalogue.csv"
MINUTES = (0.57, 0.74, 1.31)  # active minutes a requirement, measured in calibration (estimate_legislation_links)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return max(0.0, c - h), p, min(1.0, c + h)


def estimate() -> None:
    """Requirements still to draft in each state, on three bases:

    - **sample:** phase B's hand-screened sample of 50 state laws (25 Acts, 25 instruments): its Y rates (95% Wilson
      interval) and requirements per Y law;
    - **Commonwealth outcome:** the rates the Commonwealth phase actually found. Phase B's sample rate for Acts proved
      close (it implied about 145 Y Acts; 150 were found), but its instrument rate was about 20 times too high,
      because most instruments under a Y Act support its requirements (L) rather than add new ones;
    - **planning:** Acts at the state sample's Y rate (state Acts license more than Commonwealth ones), with the
      Commonwealth's yield of requirements per Y law and its instrument rate.

    Laws already called (cited by a requirement) are left out of the count to screen.
    Hours are on phase B's terms (estimate_legislation_links):
    screening 1 to 5 seconds a law, drafting at the calibration's minutes a requirement, 0.1 to 0.5 minutes to attach
    a supporting instrument, and reach coded once a family (6.4 states a family) at 0.25 to 0.5 minutes.
    """
    sample = list(csv.DictReader(SAMPLE.open(encoding="utf-8", newline="")))
    rates = {}
    for t, coll in (("primary_legislation", "Act"), ("secondary_legislation", "Instrument")):
        g = [r for r in sample if r["sample"] == "states" and r["type"] == t]
        y = [r for r in g if r["call"] == "Y"]
        rates[coll] = (wilson(len(y), len(g)), sum(int(r["requirements"]) for r in y) / max(len(y), 1))
    cth = [r for r in csv.DictReader(CTH.open(encoding="utf-8", newline="")) if not r["triage"]]
    awards = len(list((REQS / "cth").glob("cth-award-*.json")))
    cth_reqs = len(list((REQS / "cth").glob("*.json"))) - awards  # awards are not in the catalogue
    kinds = (("Act", "Act"), ("Instrument", "LegislativeInstrument"))
    cth_n = {c: sum(1 for r in cth if r["collection"] == k) for c, k in kinds}
    cth_y = {c: sum(1 for r in cth if r["collection"] == k and r["call"] == "Y") for c, k in kinds}
    cth_l = sum(1 for r in cth if r["collection"] == "LegislativeInstrument" and r["call"] == "L") / cth_n["Instrument"]
    per_y = cth_reqs / max(sum(cth_y.values()), 1)

    def to_screen(state: str) -> dict[str, int]:
        rows = list(csv.DictReader((LEG / f"{state.lower()}_catalogue.csv").open(encoding="utf-8", newline="")))
        live = [r for r in rows if not r["triage"] and not r["call"]]
        return {c: sum(1 for r in live if r["collection"] == c) for c in ("Act", "Instrument")} | {
            "high": sum(1 for r in live if r["signal"] == "high")
        }

    out = []
    for state in STATES:
        n = to_screen(state)
        a = [sum(n[c] * rates[c][0][i] * rates[c][1] for c in ("Act", "Instrument")) for i in range(3)]
        b = sum(n[c] * cth_y[c] / cth_n[c] for c in ("Act", "Instrument")) * per_y
        plan = (n["Act"] * rates["Act"][0][1] + n["Instrument"] * cth_y["Instrument"] / cth_n["Instrument"]) * per_y
        out.append(
            {
                "state": state,
                "acts_to_screen": n["Act"],
                "instruments_to_screen": n["Instrument"],
                "high_signal": n["high"],
                "requirements_cth_outcome": round(b),
                "requirements_planning": round(plan),
                "requirements_sample_low": round(a[0]),
                "requirements_sample_central": round(a[1]),
                "requirements_sample_high": round(a[2]),
                "supporting_instruments": round(n["Instrument"] * cth_l),
                "basis": "measured catalogue",
            }
        )
    tot = {k: sum(r[k] for r in out) for k in out[0] if k not in ("state", "basis")}
    out.append({"state": "All", **tot, "basis": ""})
    with (LEG / "state_catalogue_estimate.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    laws = tot["acts_to_screen"] + tot["instruments_to_screen"]
    reqs = (tot["requirements_cth_outcome"], tot["requirements_planning"], tot["requirements_sample_high"])
    hours = [
        laws * sec / 3600 + q * m / 60 + tot["supporting_instruments"] * att / 60 + q / 6.4 * fam / 60
        for sec, q, m, att, fam in zip((1, 1, 5), reqs, MINUTES, (0.1, 0.2, 0.5), (0.25, 0.25, 0.5), strict=True)
    ]
    print(
        f"Sample rates: Acts {rates['Act'][0][1]:.0%} Y, {rates['Act'][1]:.1f} a Y law; instruments "
        f"{rates['Instrument'][0][1]:.0%} Y, {rates['Instrument'][1]:.1f} a Y law"
    )
    print(
        f"Commonwealth outcome: Acts {cth_y['Act']}/{cth_n['Act']} Y, instruments {cth_y['Instrument']}/"
        f"{cth_n['Instrument']} Y, {cth_l:.0%} of instruments L; {per_y:.2f} requirements a Y law (awards left out)"
    )
    print(f"Totals: {json.dumps(tot)}")
    print(f"Hours in session, phase B's terms (low, planning, high): {', '.join(f'{h:.0f}' for h in hours)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"fetch-vic": fetch_vic, "fetch-nt": fetch_nt, "build": build, "estimate": estimate}[cmd]()
