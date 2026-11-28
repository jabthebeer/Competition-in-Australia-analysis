"""List every WA council's local laws from the Government Gazette and find their permit clauses (E-8, DECISIONS E-368).

WA publishes each local law, amendment and repeal in the Government Gazette, and no consolidated local laws.
This script reads every Gazette from 1996 to 2026 and builds two tables:

- data/processed/legislation/wa_local_laws.csv: each local law made under the Local Government Act 1995, with the
  council (ABS LGA 2021), its Gazette number, date and line, whether it is a principal law, amendment or repeal,
  and, for the laws that can hold the council permit families, whether a later Gazette repeals it, whether it
  adopts another council's law, and the amendments after it.
- data/processed/legislation/wa_permit_clauses.csv: each clause in a law in force that needs a permit or licence
  for one of the 7 council families (street trading, busking, outdoor dining, signs, events, markets, filming).

Run: uv run python scripts/wa_local_laws.py [fetch] [build]
  fetch: download the yearly Gazette lists and each Gazette's text to data/raw/wa_gazette/ (about 7,000 PDFs;
         text is kept only for Gazettes that mention a local law). Needs pdftotext.
  build: parse the cached text and write the two tables.

Method and limits are in docs/plan_councils_wa.md. Clauses are found by pattern; each one is quoted word for word
from the Gazette, but the match itself is a draft for checking. A law is taken as in force when no later Gazette
names it in a repeal clause, which can miss a repeal worded another way.
"""

from __future__ import annotations

import collections
import csv
import datetime
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/wa_gazette"
OUT = ROOT / "data/processed/legislation"
SITE = "https://www.legislation.wa.gov.au/legislation"
GAZ = SITE + "/prod/gazettestore.nsf/FileURL/{0}.pdf/$FILE/G{1}.pdf"
YEARS = range(1996, 2027)
FAMILIES = {
    "council-street-trading-permit": r"(carry on|conduct|engage in|undertake)\s+(any\s+)?trading|conducts?\s+a\s+stall"
    r"|\bhawk|\bstallholder|trader.s permit|\bsell\b[^.;]{0,40}\b(goods|thoroughfare|public place)",
    "council-busking-permit": r"\bperform(s|ing)?\b(?! (any|the) (function|work|duties|activit))"
    r"|\bbusk|street entertain",
    "council-outdoor-dining-permit": r"outdoor (eating|dining)|eating (facility|area)|alfresco|dining area",
    "council-advertising-sign-approval": r"(erect|place|display|post|affix|paint|maintain|exhibit)\b[^.;]{0,50}"
    r"(\bsigns?\b|advertisement|advertising (sign|device)|\bbill\b)|advertise anything|advertising (sign|device)",
    "council-temporary-event-approval": r"(conduct|hold|organise|stage|run)\b[^.;]{0,30}"
    r"\b(function|event|festival|concert)s?\b",
    "council-filming-permit": r"^(?!.*\bsigns?\b).*(\bfilm(ing|s)?\b|photograph)",
    "council-market-licence": r"(conduct|hold|set up|establish|operate|run)\b[^.;]{0,30}\bmarkets?\b",
}
# Title words that mark a law able to hold one of the families.
CATEGORIES = {
    "thoroughfares": r"thoroughfare|trading|street|footpath|verge",
    "property": r"property|reserve|public place|foreshore|beach",
    "signs": r"\bsigns?\b|advertis",
    "dining": r"dining|outdoor eating|alfresco",
    "markets": r"market",
    "events": r"event|entertainment",
    "filming": r"film",
}
OTHER = (
    r"eating.?house|parking|health|dog|\bcats?\b|cemeter|bush fire|fencing|standing order|meeting|pest|waste"
    r"|animal|extractive|nuisance"
)
# Former and misprinted council names in the Gazette, mapped to the ABS 2021 name.
ALIASES = {
    "augusta-margaret river": "Augusta Margaret River",
    "geraldton": "Greater Geraldton",
    "greenough": "Greater Geraldton",
    "geraldton-greenough": "Greater Geraldton",
    "geraldton greenough": "Greater Geraldton",
    "mullewa": "Greater Geraldton",
    "roebourne": "Karratha",
    "broomehill": "Broomehill-Tambellup",
    "tambellup": "Broomehill-Tambellup",
    "kalgoorlie/boulder": "Kalgoorlie-Boulder",
    "derby/west kimberley": "Derby-West Kimberley",
    "derby / west kimberley": "Derby-West Kimberley",
    "derby l west kimberley": "Derby-West Kimberley",
    "donnybrook/balingup": "Donnybrook-Balingup",
    "morowa": "Morawa",
    "goomaling": "Goomalling",
    "goomai,i,ing": "Goomalling",
    "mt marshall": "Mount Marshall",
    "mt marshal1": "Mount Marshall",
    "mt magnet": "Mount Magnet",
    "wanner00": "Wanneroo",
    "ngaanyatjarrku": "Ngaanyatjarraku",
}
LG_ACT = re.compile(r"\s*LOCAL GOVERNMENT ACT 1995\s*$")


# ---------------------------------------------------------------- fetch


def gazette_ids(year: int) -> list[str]:
    page = RAW / f"year{year}.html"
    if not page.exists():
        page.write_text(httpx.get(f"{SITE}/statutes.nsf/gazettes{year}.html", timeout=120).text, encoding="utf-8")
    return sorted(set(re.findall(rf"gg{year}_\d+", page.read_text(encoding="utf-8", errors="replace"))))


def fetch_one(gid: str) -> None:
    txt = RAW / f"{gid}.txt"
    if txt.exists() and txt.stat().st_size:
        return
    pdf = RAW / f"{gid}.pdf"
    with httpx.stream("GET", GAZ.format(gid, gid[1:]), timeout=180, follow_redirects=True) as r:
        r.raise_for_status()
        with pdf.open("wb") as fh:
            for chunk in r.iter_bytes():
                fh.write(chunk)
    done = subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], capture_output=True)
    if done.returncode or "local law" not in txt.read_text(errors="replace").lower():
        txt.write_text("FAIL\n" if done.returncode else "NOLL\n")  # no local law: keep a marker only
    pdf.unlink()


def fetch() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    ids = [g for y in YEARS for g in gazette_ids(y)]
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(fetch_one, ids))
    print(f"{len(ids)} Gazettes cached in {RAW}")


# ---------------------------------------------------------------- councils and Gazette metadata


def councils() -> dict[str, str]:
    """ABS LGA 2021 names to codes for WA."""
    wb = openpyxl.load_workbook(ROOT / "data/raw/abs_asgs/LGA_2021_AUST.xlsx", read_only=True)
    rows = wb.active.iter_rows(values_only=True)
    head = list(next(rows))
    i, j, k = (head.index(c) for c in ("LGA_CODE_2021", "LGA_NAME_2021", "STATE_NAME_2021"))
    return {
        r[j].strip(): str(r[i])
        for r in rows
        if r[k] == "Western Australia" and not r[j].startswith(("No usual", "Migratory"))
    }


def gazette_meta() -> dict[str, dict]:
    meta = {}
    for f in sorted(RAW.glob("year*.html")):
        for row in re.findall(r"<tr>(.*?)</tr>", f.read_text(encoding="utf-8", errors="replace"), re.S):
            cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
            g = re.search(r"(gg\d{4}_\d+)", row)
            if g and len(cells) > 1:
                meta[g.group(1)] = {"date": cells[0], "no": cells[1]}
    return meta


def date(s: str) -> datetime.date | None:
    for fmt in ("%d %B %Y", "%d %b %Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


# ---------------------------------------------------------------- local laws


class Laws:
    def __init__(self) -> None:
        self.codes = councils()
        self.lookup = {n.lower(): n for n in self.codes} | {n.lower().replace("-", " "): n for n in self.codes}
        self.lookup |= {k: v for k, v in ALIASES.items() if v in self.codes}
        self.cache: dict[str, list[str]] = {}
        self.rows: list[dict] = []
        self.starts: dict[str, list[int]] = collections.defaultdict(list)

    def text(self, g: str) -> list[str]:
        if g not in self.cache:
            self.cache[g] = (RAW / f"{g}.txt").read_text(errors="replace").split("\n")
        return self.cache[g]

    def council(self, s: str) -> str | None:
        if not re.search(r"\b(city|shire|town|municipality)\b", s, re.I):
            return None
        k = re.sub(r",\s*(city|shire|town) of\s*$", "", s.strip(), flags=re.I).lower()
        k = re.sub(r"^(the )?municipality of the ", "", k)
        k = re.sub(r"^(the )?(city|shire|town) of ?", "", k).strip()
        return self.lookup.get(k) or self.lookup.get(k.replace("-", " "))

    def heading(self, lines: list[str], i: int) -> tuple[str | None, str]:
        """Council and title of a notice headed 'LOCAL GOVERNMENT ACT 1995' at line i."""
        c, title = None, []
        for s in (x.strip() for x in lines[i + 1 : i + 12]):
            if not s or re.fullmatch(r"[—_\-–\s]+", s) or re.fullmatch(r"[A-Z ()]+ ACT \d{4}", s):
                continue
            if c is None:
                m = re.match(r"(?i)(?:the\s+)?(city|shire|town)\s+of\s+(.+?)\s+(\S.*LOCAL LAWS?.*)$", s)
                if m:  # council and title on one line
                    words = m.group(2).split() + m.group(3).split()
                    for n in range(min(4, len(words) - 1), 0, -1):
                        if found := self.lookup.get(" ".join(words[:n]).lower()):
                            c = found
                            title.append(" ".join(words[n:]))
                            break
                    if c and re.search(r"LOCAL LAWS?(\s+\d{4})?$", s, re.I):
                        break
                    if c:
                        continue
                c = self.council(s)
                if c is None:
                    break
                continue
            if s.startswith(("Under the powers", "In pursuance")) or s[:1].islower():
                break
            title.append(s)
            if re.search(r"LOCAL LAWS?(\s+\d{4})?$", s, re.I):
                break
        return c, re.sub(r"\s+", " ", " ".join(title))

    def scan_gazettes(self) -> None:
        for f in sorted(RAW.glob("gg*.txt")):
            g = f.stem
            lines = self.text(g)
            if lines[0].startswith(("NOLL", "FAIL")):
                continue
            for i, ln in enumerate(lines):
                if LG_ACT.match(ln):
                    c, t = self.heading(lines, i)
                    if c and re.search(r"LOCAL LAW", t, re.I):
                        self.rows.append(
                            {"gazette": g, "line": i + 1, "council": c, "lga": self.codes[c], "title": t.title()}
                        )
                        self.starts[g].append(i + 1)

    def section(self, g: str, line: int) -> str:
        lines = self.text(g)
        nxt = [x for x in sorted(self.starts[g]) if x > line]
        return "\n".join(lines[line - 1 : nxt[0] - 1 if nxt else len(lines)])


def kind(t: str) -> str:
    tl = t.lower()
    if re.search(r"\brepeal", tl) and "amendment" not in tl:
        return "repeal"
    return "amendment" if "amend" in tl else "principal"


def categories(t: str) -> list[str]:
    tl = t.lower()
    if re.search(OTHER, tl) and not re.search(r"thoroughfare|property|trading|sign", tl):
        return []
    return [c for c, p in CATEGORIES.items() if re.search(p, tl)]


def stem(t: str) -> str:
    return re.sub(r"\s*(\(no\.? ?\d+\)\s*)?\d{4}\s*$", "", t.lower()).strip()


def words(s: str) -> str:
    return re.sub(r"[^a-z]+", " ", s.lower())


ADOPT = re.compile(
    r"The (?:Shire|City|Town) of ((?:[A-Z][\w\-]+ ){1,4}?)(.{10,160}?Local Laws?)(?:,? (?:as )?published in the "
    r"Government Gazette (?:of|on) (\d{1,2} \w+ \d{4}))?[^.]{0,120}?(?:is|are) (?:hereby )?adopted"
)


def in_force(laws: Laws, meta: dict) -> list[dict]:
    """The latest principal law of each title per council, with later repeals, amendments and adoptions."""
    by = collections.defaultdict(list)
    for r in laws.rows:
        r["kind"], r["cats"] = kind(r["title"]), categories(r["title"])
        by[r["council"]].append(r)
    names = sorted(laws.codes, key=len, reverse=True)
    out = []
    for c, rs in by.items():
        rs.sort(key=lambda r: (r["gazette"], r["line"]))
        latest = {stem(r["title"]): r for r in rs if r["kind"] == "principal" and r["cats"]}
        for st, last in latest.items():
            later = [r for r in rs if (r["gazette"], r["line"]) > (last["gazette"], last["line"])]
            am = [
                r
                for r in later
                if r["kind"] == "amendment" and stem(r["title"]).replace(" amendment", "")[:25] == st[:25]
            ]
            key = re.sub(r" \d{4}$", "", words(last["title"]).strip())
            repealed = ""
            for r in later:
                if r["kind"] in ("repeal", "principal"):
                    sec = words(laws.section(r["gazette"], r["line"]))
                    for m in re.finditer(r"repeal", sec):
                        win = sec[m.start() : m.start() + 1200]
                        if key in win and "amendment local law" not in win[: win.find(key)][-60:]:
                            repealed = r["gazette"]
                            break
                if repealed:
                    break
            base = {}
            m = ADOPT.search(re.sub(r"\s+", " ", laws.section(last["gazette"], last["line"])))
            if m:
                blob = m.group(1) + m.group(2)
                bc = next((n for n in names if blob.startswith(n + " ")), None)
                d = date(m.group(3)) if m.group(3) else None
                ty = "property" if "property" in m.group(2).lower() else "thorough"
                cands = [
                    x
                    for x in by.get(bc, [])
                    if x["gazette"] < last["gazette"]
                    and (d is None or date(meta[x["gazette"]]["date"]) == d)
                    and ty in x["title"].lower()
                    and "amend" not in x["title"].lower()
                ]
                base = {
                    "adopted_from": bc or "?",
                    "base_gazette": cands[-1]["gazette"] if cands else "",
                    "base_line": cands[-1]["line"] if cands else "",
                }
                base["modified_clauses"] = " ".join(sorted(set(re.findall(r"[Cc]lause (\d+\.\d+)", m.string))))
            out.append(
                {
                    "council": c,
                    "lga": last["lga"],
                    "title": last["title"],
                    "categories": " ".join(last["cats"]),
                    "gazette": last["gazette"],
                    "gazette_no": meta[last["gazette"]]["no"],
                    "gazette_date": meta[last["gazette"]]["date"],
                    "line": last["line"],
                    "amendments": " ".join(a["gazette"] for a in am),
                    "repealed_by": repealed,
                    "adopted_from": base.get("adopted_from", ""),
                    "base_gazette": base.get("base_gazette", ""),
                    "base_line": base.get("base_line", ""),
                    "modified_clauses": base.get("modified_clauses", ""),
                }
            )
    return out


# ---------------------------------------------------------------- permit clauses

CLAUSE = re.compile(r"^\s*(\d{1,2}\.\d{1,3}[A-Z]?)\.?\s+(?:\((\d+)\)\s+)?(.*)$")
PROHIBIT = re.compile(r"(person|owner|occupier)[^.;]{0,40}\b(shall|must)\s+not\b|\bno person shall\b", re.I)
PERMIT = re.compile(r"\b(permit|licence|approval)\b", re.I)
SKIP = re.compile(r"cemeter|\bBoard\b|occupy a chair|contravention of|condition of (a|the) (permit|licence)")


def clauses(lines: list[str]) -> list[dict]:
    lines = [ln for ln in lines if "GOVERNMENT GAZETTE, WA" not in ln and not re.fullmatch(r"\s*\d{1,5}\s*", ln)]
    found, cur, div = [], None, ""
    for ln in lines:
        if md := re.match(r"\s*(?:Division|Subdivision)\s+\d+[A-Z]?\s*[—–-]\s*(.+)", ln):
            div = md.group(1).strip()
            continue
        m = CLAUSE.match(ln)
        if m and re.search(r"\S\s{3,}\S", m.group(3) or ""):  # a row of a table, such as the offences schedule
            cur = None
            continue
        if m and (m.group(2) or (m.group(3) and len(m.group(3)) < 90 and m.group(3)[:1].isupper())):
            cur = {"no": m.group(1), "heading": "" if m.group(2) else m.group(3).strip(), "div": div}
            cur["lines"] = [f"({m.group(2)}) {m.group(3)}" if m.group(2) else ""]
            found.append(cur)
            continue
        if cur:
            cur["lines"].append(ln)
    best: dict[str, tuple[int, dict]] = {}
    for c in found:  # the body, not the table of contents, is the longest copy of a clause
        n = sum(len(x) for x in c["lines"])
        if c["no"] not in best or n > best[c["no"]][0]:
            best[c["no"]] = (n, c)
    return [v[1] for v in best.values()]


def permit_clauses(lines: list[str]) -> list[dict]:
    hits = []
    for c in clauses(lines):
        subs, cur = [], None
        for ln in (x for x in c["lines"] if x.strip()):
            if ms := re.match(r"\s*\((\d+)\)\s+(.*)", ln):
                cur = [ms.group(1), [ms.group(2)]]
                subs.append(cur)
            elif cur:
                cur[1].append(ln)
            elif not subs:
                cur = [None, [ln]]
                subs.append(cur)
        for sub, ls in subs:
            text = re.sub(r"\s+", " ", " ".join(x.strip() for x in ls))
            first = text[:500]
            lead = re.match(r"(.{0,260}?(?:permit|licence|approval)[^—–]{0,80}?)([—–])\s*\(a\)", text)
            if lead and PROHIBIT.search(lead.group(1)):  # "A person shall not without a permit— (a) …"
                parts = re.split(r"\s\(([a-z]{1,2})\)\s", " " + text[lead.end() - 3 :])
                prev = None
                for k, t in zip(parts[1::2], parts[2::2], strict=False):
                    if re.fullmatch(r"(ii|iii|iv|vi|vii|viii|ix)", k) or (
                        k in ("i", "v", "x") and prev != chr(ord(k) - 1)
                    ):
                        continue
                    prev, t = k, t.strip()
                    if SKIP.search(t):
                        continue
                    for f, p in FAMILIES.items():
                        if re.search(p, t, re.I):
                            hits.append(
                                {
                                    "family": f,
                                    "clause": c["no"],
                                    "sub": sub,
                                    "item": k,
                                    "stem": lead.group(1).strip() + lead.group(2),
                                    "text": t,
                                    "heading": c["heading"],
                                }
                            )
            elif (m := PROHIBIT.search(first)) and m.start() < 120 and PERMIT.search(first) and not SKIP.search(first):
                sent = re.match(r".{0,700}?[.;](?=\s|$)", text)
                t = sent.group(0) if sent else first
                for f, p in FAMILIES.items():
                    facility = (
                        f == "council-outdoor-dining-permit"
                        and re.search(r"\bfacility\b", t)
                        and re.search(p, c["heading"] + " " + c["div"], re.I)
                    )
                    if re.search(p, t, re.I) or facility:
                        hits.append(
                            {
                                "family": f,
                                "clause": c["no"],
                                "sub": sub,
                                "item": "",
                                "stem": "",
                                "text": t,
                                "heading": c["heading"],
                            }
                        )
    return hits


def build() -> None:
    meta = gazette_meta()
    laws = Laws()
    laws.scan_gazettes()
    force = in_force(laws, meta)
    allrows = [dict(r, gazette_no=meta[r["gazette"]]["no"], gazette_date=meta[r["gazette"]]["date"]) for r in laws.rows]
    with (OUT / "wa_local_laws.csv").open("w", newline="", encoding="utf-8") as fh:
        cols = ["council", "lga", "title", "kind", "gazette", "gazette_no", "gazette_date", "line"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(allrows, key=lambda r: (r["council"], r["gazette"], r["line"])))
    with (OUT / "wa_local_laws_in_force.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(force[0]))
        w.writeheader()
        w.writerows(sorted(force, key=lambda r: (r["council"], r["gazette"])))
    hits = []
    for r in force:
        if r["repealed_by"] or r["adopted_from"] == "?" or (r["adopted_from"] and not r["base_gazette"]):
            continue
        g, ln = (r["base_gazette"], int(r["base_line"])) if r["adopted_from"] else (r["gazette"], int(r["line"]))
        for h in permit_clauses(laws.section(g, ln).split("\n")):
            hits.append(
                {
                    "council": r["council"],
                    "lga": r["lga"],
                    "law": r["title"],
                    "gazette": r["gazette"],
                    "line": r["line"],
                    "amendments": r["amendments"],
                    "adopted_from": r["adopted_from"],
                    "base_gazette": r["base_gazette"],
                    "base_line": r["base_line"],
                    "modified": "yes" if h["clause"] in r["modified_clauses"].split() else "",
                    **h,
                    "text": h["text"][:300],  # short extracts only (Gazettes are State of WA copyright)
                }
            )
    with (OUT / "wa_permit_clauses.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(hits[0]))
        w.writeheader()
        w.writerows(hits)
    live = [r for r in force if not r["repealed_by"]]
    print(
        f"{len(laws.rows)} local laws for {len({r['council'] for r in laws.rows})} councils; "
        f"{len(live)} laws in force hold the families"
    )
    fam = collections.defaultdict(set)
    for h in hits:
        fam[h["family"]].add(h["council"])
    for f, s in sorted(fam.items()):
        print(f"  {f}: {len(s)} councils")
    print(f"{len(hits)} clauses in {len({h['council'] for h in hits})} councils")


if __name__ == "__main__":
    args = sys.argv[1:] or ["build"]
    if "fetch" in args:
        fetch()
    if "build" in args:
        build()
