"""Read the current official text of a law in any jurisdiction, and the ABLIS listing for a service, for drafting
requirements (``regulation-register/requirements/README.md`` explains the whole workflow).

A source is named by a short spec:

  frl:<title id>            Commonwealth, Federal Register (latest compilation)            -> register-text
  corpus:<version id>       NSW or SA (or a fallback), Open Australian Legal Corpus copy    -> corpus-copy
  qld:<act id>              Queensland register HTML, e.g. qld:act-2006-003                 -> register-text
  tas:<act id>              Tasmanian register HTML (falls back to the corpus if cut off)   -> register-text
  wa:<law_aNNN>             WA register, the current Word document                          -> document
  act:<A id>                ACT register, latest republication PDF, e.g. act:2001-66        -> document
  nt:<NAME>                 NT register PDF, by the name in its URL                         -> document
  vic:<yy-numaaver>         Victoria, an authorised PDF the owner saved (data/raw/vic_legislation/), e.g. vic:17-51aa023
                            -> document (cited by the register's in-force page)
  page:<url>                any web page (e.g. a Victorian regulator; the Vic register's documents are disallowed)

Usage (in alicia/):
  uv run python scripts/law_sources.py look qld:act-2006-003 "must not carry on" "licence"
  uv run python scripts/law_sources.py index "Food Act"                      # corpus laws whose citation matches
  uv run python scripts/law_sources.py ablis https://ablis.business.gov.au/service/nsw/<slug>/<id>

In Python (for a batch script): ``from law_sources import src, clip, ablis``. ``clip(spec, start, end, locator,
title, publisher)`` returns a ready ``Source`` dict whose quote runs from ``start`` to ``end`` in the text.

Courtesy: every request is spaced out (law_text.PAUSE, and 10 seconds for the ACT register, which asks for it).
ABLIS's public pages may be read a few at a time, never in bulk; quote only the first sentence of a description,
unaltered and attributed (its copyright allows unaltered, non-commercial reproduction only). Bulk use waits for
the ABLIS API key (docs/ablis_brief.md).
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import law_text as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "data" / "processed" / "legislation" / "oalc_laws.csv.gz"
VIC_DIR = ROOT / "data" / "raw" / "vic_legislation"
VIC_CATALOGUE = ROOT / "data" / "processed" / "legislation" / "vic_catalogue.csv"
_INDEX: list[dict] | None = None


def index(pattern: str, jurisdiction: str | None = None) -> list[dict]:
    """Corpus laws whose citation matches ``pattern`` (a regular expression)."""
    global _INDEX
    if _INDEX is None:
        with gzip.open(INDEX, "rt", encoding="utf-8") as fh:
            _INDEX = list(csv.DictReader(fh))
    return [
        r
        for r in _INDEX
        if re.search(pattern, r["citation"]) and (jurisdiction is None or r["jurisdiction"] == jurisdiction)
    ]


def _page(url: str, delay: float = 3.0) -> str:
    time.sleep(delay)
    return L.get(url).text


def _key(url: str) -> str:
    return "doc-" + hashlib.sha256(url.encode()).hexdigest()[:16]


def wa_current(law: str) -> tuple[str, str]:
    page = _page(f"https://www.legislation.wa.gov.au/legislation/statutes.nsf/{law}.html")
    docs = sorted(set(re.findall(r"mrdoc_(\d+)\.docx", page)), key=int)
    flat = re.sub(r"<[^>]+>", " ", page).replace("\n", " ")
    cur = re.search(r"Currency start Currency end.*?(\d{1,2} \w{3} \d{4}) Current", flat)
    url = (
        f"https://www.legislation.wa.gov.au/legislation/statutes.nsf/RedirectURL?OpenAgent&query=mrdoc_{docs[-1]}.docx"
    )
    return url, (cur.group(1) if cur else "")


def act_latest(aid: str) -> tuple[str, str, str]:
    """The ACT register's latest republication of an Act (``2001-66``) or a subordinate law (``sl/2011-36``). The
    newest republication is often offered only as ``current`` (no dated link yet), so that is preferred; the version
    returned is then ``current`` and the label names its republication number and date."""
    kind, num = ("sl", aid[3:]) if aid.startswith("sl/") else ("a", aid)
    page = _page(f"https://www.legislation.act.gov.au/{kind}/{num}/", delay=10.0)  # the ACT register's crawl delay
    title = re.search(r"<title>([^<]+)</title>", page)
    label = title.group(1).strip() if title else ""
    if f"/DownloadFile/{kind}/{num}/current/PDF/{num}.PDF" in page:
        cur = re.search(r"R(\d+) \(current\) (\d{1,2} \w+ \d{4})", re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page)))
        url = f"https://www.legislation.act.gov.au/DownloadFile/{kind}/{num}/current/PDF/{num}.PDF"
        return url, "current", (f"R{cur.group(1)}, from {cur.group(2)}; " if cur else "") + label
    versions = sorted(set(re.findall(rf"/DownloadFile/{kind}/{num}/(\d{{8}}-\d+)/PDF/{num}\.PDF", page)))
    url = f"https://www.legislation.act.gov.au/DownloadFile/{kind}/{num}/{versions[-1]}/PDF/{num}.PDF"
    return url, versions[-1][:8], label


def nt_pdf(name: str) -> str | None:
    page = _page(f"https://legislation.nt.gov.au/Legislation/{name}")
    m = re.search(r"https://legislation.nt.gov.au/api/sitecore/Act/PDF\?id=\d+", page)
    return m.group(0) if m else None


def src(spec: str) -> tuple[str, str, str, str | None, str]:
    """(url, text, checked, corpus version id, version note) for a source spec."""
    kind, _, arg = spec.partition(":")
    flat = lambda t: " ".join(t.split())  # noqa: E731
    if kind == "frl":
        text, meta = L.frl_latest(arg)
        note = f"compilation {meta['compilation']} from {meta['start'][:10]}" if meta.get("compilation") else ""
        return meta["url"], flat(text), "register-text", None, note
    if kind == "corpus":
        row = next(r for r in index(".") if r["version_id"] == arg)
        return row["url"], flat(L.corpus_text(arg)), "corpus-copy", arg, f"version of {arg.split(':')[1].split('/')[0]}"
    if kind in ("qld", "tas"):
        base = {"qld": "https://www.legislation.qld.gov.au", "tas": "https://www.legislation.tas.gov.au"}[kind]
        url = f"{base}/view/whole/html/inforce/current/{arg}"
        try:
            return url, flat(L.fetch_doc(url, _key(url))[0]), "register-text", None, "current"
        except Exception as exc:  # the Tasmanian register cuts large downloads off
            jur = "tasmania" if kind == "tas" else "queensland"
            rows = [r for r in index(".", jur) if r["version_id"].endswith("/" + arg)]
            if not rows:
                raise
            vid = rows[0]["version_id"]
            print(f"   ({kind} register failed: {type(exc).__name__}; using corpus {vid})", file=sys.stderr)
            return url, flat(L.corpus_text(vid)), "corpus-copy", vid, f"version of {vid.split(':')[1].split('/')[0]}"
    if kind == "wa":
        url, cur = wa_current(arg)
        return url, flat(L.fetch_doc(url, _key(url))[0]), "document", None, f"version current from {cur}"
    if kind == "act":
        url, v, title = act_latest(arg)
        note = (
            f"current republication ({title})"
            if v == "current"
            else f"republication of {v[6:8]}/{v[4:6]}/{v[:4]} ({title})"
        )
        return url, flat(L.fetch_doc(url, _key(url))[0]), "document", None, note
    if kind == "nt":
        url = nt_pdf(arg)
        if not url:
            raise SystemExit(f"no NT PDF for {arg}")
        return url, flat(L.fetch_doc(url, _key(url))[0]), "document", None, "current reprint"
    if kind == "vic":
        # Victoria: an authorised PDF the owner saved from the register (data/raw/vic_legislation/, not committed),
        # named like 17-51aa023 (Act 51 of 2017, authorised version 023). The register's documents disallow automated
        # fetching, so the quote cites the register's in-force page for the Act.
        yy, num, ver = re.match(r"(\d\d)-(\d+)aa(\d+)", arg).groups()
        pdf = next(VIC_DIR.glob(f"{arg}*.pdf"))
        out = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
        year = ("19" if int(yy) > 30 else "20") + yy
        with VIC_CATALOGUE.open(encoding="utf-8", newline="") as fh:
            url = next(r["url"] for r in csv.DictReader(fh) if r["register_id"] == f"{num}/{year}")
        return url, flat(out), "document", None, f"authorised version {ver}, saved by the owner"
    if kind == "page":
        return arg, flat(L.fetch_doc(arg, _key(arg))[0]), "web-page", None, ""
    raise ValueError(f"unknown source spec {spec!r}")


def look(spec: str, *patterns: str, width: int = 380, limit: int = 1) -> None:
    """Print where each pattern (a regular expression) occurs in the source's text, with context."""
    url, text, checked, _, version = src(spec)
    print(f"== {spec} [{checked}; {version}] {len(text):,} characters\n   {url}")
    for p in patterns:
        hits = [m.start() for m in re.finditer(p, text)]
        print(f"  /{p[:50]}/ {len(hits)} hit(s)")
        for i in hits[:limit]:
            print("    ", text[max(0, i - 60) : i + width])


def clip(
    spec: str, start: str, end: str, locator: str, title: str, publisher: str, accessed: str | None = None
) -> dict:
    """A Source dict quoting the text from ``start`` to the end of ``end``, exactly as it appears."""
    url, text, checked, vid, version = src(spec)
    i = text.index(start)
    j = text.index(end, i) + len(end)
    out = {
        "title": title,
        "publisher": publisher,
        "url": url,
        "locator": f"{locator} ({version})" if version else locator,
        "quote": text[i:j],
        "accessed": accessed or dt.date.today().isoformat(),
        "checked": checked,
    }
    if vid:
        out["corpus_version_id"] = vid
    return out


def _between(text: str, start: str, stops: list[str]) -> str | None:
    i = text.find(start)
    if i < 0:
        return None
    i += len(start)
    ends = [k for k in (text.find(s, i) for s in stops) if k >= 0]
    return text[i : min(ends) if ends else len(text)].strip()


def ablis(url: str) -> dict:
    """The fields of one ABLIS public service page: description, service type, Acts, regulations, local laws,
    administering agency; and ``quote``, the description's first sentence (the most the drafts quote)."""
    _, text, *_ = src("page:" + url)
    out = {
        "url": url,
        "id": url.rstrip("/").rsplit("/", 1)[1],
        "description": _between(text, "Description ", [" Service type"]),
        "type": _between(text, "Service type ", [" A licence", " A ", " Eligibility", " Fees"]),
        "acts": _between(text, "Act(s) name ", [" Local law(s) name", " Regulation(s) name", " Administering agency"]),
        "regulations": _between(text, "Regulation(s) name ", [" Local law(s) name", " Administering agency"]),
        "local_laws": _between(text, "Local law(s) name ", [" Administering agency"]),
        "agency": _between(text, "Administering agency ", [" Contact details"]),
    }
    if out["description"]:
        out["quote"] = out["description"].split(". ")[0].rstrip(".") + "."
    return out


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[0] not in ("look", "index", "ablis"):
        raise SystemExit(__doc__)
    cmd, arg, *rest = argv
    if cmd == "look":
        look(arg, *rest)
    elif cmd == "index":
        for r in index(arg)[:40]:
            print(f"{r['version_id']:70} {r['citation']}")
    else:
        for k, v in ablis(arg).items():
            print(f"{k:12} {v}")


if __name__ == "__main__":
    main(sys.argv[1:])
