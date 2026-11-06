"""Find a law and search its text, so a requirement's quotes are copied from the official text, not recalled.

Usage (in alicia/):
  uv run python scripts/law_text.py index "Goods and Services Tax"    # laws in the corpus index whose citation matches
  uv run python scripts/law_text.py frl C2004A00446 "required to be registered"   # passages in the latest text
  uv run python scripts/law_text.py corpus "<version_id>" "food business"          # passages in the corpus copy
  uv run python scripts/law_text.py page "<url>" "<phrase>"                        # passages in any web page
  uv run python scripts/law_text.py doc "<url>" "<phrase>"                         # a PDF, Word or RTF document

Texts are cached in data/raw/law_text/ (not committed). Requests to the Federal Register are spaced out. Matching is
case-insensitive on text with whitespace collapsed; each hit prints with context so the exact words can be quoted.
"""

from __future__ import annotations

import gzip
import hashlib
import html
import json
import re
import sys
import time
from pathlib import Path

import httpx

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_text(data: bytes) -> str:
    """Every paragraph of a .docx, keeping non-breaking hyphens (as in section numbers such as 23-5) and tabs."""
    import io
    import xml.etree.ElementTree as ET
    import zipfile

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    out = []
    for p in root.iter(f"{W}p"):
        bits = []
        for el in p.iter():
            if el.tag == f"{W}t":
                bits.append(el.text or "")
            elif el.tag in (f"{W}noBreakHyphen", f"{W}softHyphen"):
                bits.append("-")
            elif el.tag in (f"{W}tab", f"{W}br"):
                bits.append(" ")
        out.append("".join(bits))
    return "\n".join(out)


ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "raw" / "law_text"
CORPUS = ROOT / "data" / "raw" / "oalc"
API = "https://api.prod.legislation.gov.au/v1"
SITE = "https://www.legislation.gov.au"
HEADERS = {"User-Agent": "alicia-research/0.1 (non-commercial research)"}
PAUSE = 5.0


def plain(page: str) -> str:
    page = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)
    page = re.sub(r"<br\s*/?>|</p>|</div>|</h\d>|</li>|</tr>", "\n", page, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", page))
    return "\n".join(" ".join(line.split()) for line in text.splitlines() if line.strip())


def fetch(url: str, key: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{key}.txt"
    if path.exists():
        return path.read_text("utf-8")
    time.sleep(PAUSE)
    r = httpx.get(url, headers=HEADERS, timeout=120, follow_redirects=True)
    r.raise_for_status()
    text = plain(r.text)
    path.write_text(text, "utf-8")
    (CACHE / f"{key}.json").write_text(
        json.dumps(
            {
                "url": url,
                "final_url": str(r.url),
                "retrieved": time.strftime("%Y-%m-%d"),
                "sha256": hashlib.sha256(r.content).hexdigest(),
            }
        ),
        "utf-8",
    )
    return text


def frl_latest(title_id: str) -> tuple[str, dict]:
    """The latest compilation of a Commonwealth law, read from its Word document(s) on the Federal Register."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path, meta_path = CACHE / f"frl-{title_id}.txt", CACHE / f"frl-{title_id}.json"
    if path.exists() and meta_path.exists():
        return path.read_text("utf-8"), json.loads(meta_path.read_text("utf-8"))
    q = (
        f"{API}/Versions?$filter=titleId eq '{title_id}'&$orderby=start desc&$top=10"
        "&$select=titleId,start,registerId,name"
    )
    time.sleep(PAUSE)
    today = time.strftime("%Y-%m-%d")
    found = httpx.get(q, headers=HEADERS, timeout=60).json()["value"]
    # The newest version already in force that has a document (a future, uncommenced version has none).
    v = next(x for x in found if x.get("registerId") and x["start"][:10] <= today)
    parts, digests = [], []
    for vol in range(0, 12):
        url = (
            f"{API}/documents/find(registerId='{v['registerId']}',type='Primary',format='Word',"
            f"uniqueTypeNumber=0,volumeNumber={vol},rectificationVersionNumber=0)"
        )
        time.sleep(PAUSE)
        r = httpx.get(url, headers=HEADERS, timeout=180, follow_redirects=True)
        if r.status_code == 404:
            if vol == 0:
                continue
            break
        r.raise_for_status()
        parts.append(docx_text(r.content))
        digests.append({"volume": vol, "sha256": hashlib.sha256(r.content).hexdigest()})
        if vol == 0:
            break
    if not parts:
        raise SystemExit(f"no Word document for {v['registerId']}")
    text = "\n".join(parts)
    meta = {
        "title_id": title_id,
        "compilation": v["registerId"],
        "start": v["start"],
        "name": v["name"],
        "url": f"{SITE}/{title_id}/latest/text",
        "retrieved": time.strftime("%Y-%m-%d"),
        "documents": digests,
    }
    path.write_text(text, "utf-8")
    meta_path.write_text(json.dumps(meta), "utf-8")
    return text, meta


def rtf_text(data: bytes) -> str:
    """Plain text of an RTF file: control words and groups stripped (enough to search and quote)."""
    s = data.decode("latin-1")
    s = re.sub(r"\\'([0-9a-f]{2})", lambda m: bytes.fromhex(m.group(1)).decode("cp1252", "replace"), s)
    s = re.sub(r"\\(par|line)\b ?", "\n", s)
    s = re.sub(r"\\[a-z]+-?\d* ?|[{}]", "", s)
    return s


def fetch_doc(url: str, key: str) -> tuple[str, dict]:
    """A PDF, Word (.docx) or RTF document (or an HTML page), as plain text; cached like the others."""
    import subprocess
    import tempfile

    CACHE.mkdir(parents=True, exist_ok=True)
    path, meta_path = CACHE / f"{key}.txt", CACHE / f"{key}.json"
    if path.exists() and meta_path.exists():
        return path.read_text("utf-8"), json.loads(meta_path.read_text("utf-8"))
    time.sleep(PAUSE)
    r = httpx.get(url, headers=HEADERS, timeout=180, follow_redirects=True)
    r.raise_for_status()
    data = r.content
    if data[:4] == b"%PDF":
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(data)
            f.flush()
            text = subprocess.run(["pdftotext", f.name, "-"], capture_output=True, text=True, check=True).stdout
        kind = "pdf"
    elif data[:2] == b"PK":
        text, kind = docx_text(data), "docx"
    elif data[:5] == b"{\\rtf":
        text, kind = rtf_text(data), "rtf"
    else:
        text, kind = plain(r.text), "html"
    meta = {
        "url": url,
        "final_url": str(r.url),
        "kind": kind,
        "retrieved": time.strftime("%Y-%m-%d"),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    path.write_text(text, "utf-8")
    meta_path.write_text(json.dumps(meta), "utf-8")
    return text, meta


def corpus_text(version_id: str) -> str:
    j = version_id.split(":")[0].replace("_legislation", "")
    names = {
        "federal_register_of": "commonwealth",
        "nsw": "new_south_wales",
        "queensland": "queensland",
        "western_australian": "western_australia",
        "south_australian": "south_australia",
        "tasmanian": "tasmania",
    }
    files = [CORPUS / f"{names[j]}.jsonl.gz"] if j in names else sorted(CORPUS.glob("*.jsonl.gz"))
    for f in files:
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                if version_id in line[:300]:
                    doc = json.loads(line)
                    if doc["version_id"] == version_id:
                        return "\n".join(" ".join(x.split()) for x in doc["text"].splitlines() if x.strip())
    raise SystemExit(f"{version_id} not in the corpus")


def find(text: str, phrase: str, width: int = 350, limit: int = 8) -> None:
    flat = " ".join(text.split())
    hits = [m.start() for m in re.finditer(re.escape(" ".join(phrase.split())), flat, re.I)]
    print(f"{len(hits)} hit(s) for {phrase!r}")
    for h in hits[:limit]:
        print("…" + flat[max(0, h - width) : h + width] + "…\n")


def main(argv: list[str]) -> None:
    cmd = argv[0]
    if cmd == "index":
        import csv

        with gzip.open(ROOT / "data" / "processed" / "legislation" / "oalc_laws.csv.gz", "rt", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if re.search(argv[1], r["citation"], re.I) and (len(argv) < 3 or r["jurisdiction"] == argv[2]):
                    print(r["jurisdiction"], "|", r["type"], "|", r["citation"], "|", r["url"], "|", r["version_id"])
    elif cmd == "frl":
        text, meta = frl_latest(argv[1])
        print(f"{len(text):,} characters; {meta}")
        for phrase in argv[2:]:
            find(text, phrase)
    elif cmd == "corpus":
        text = corpus_text(argv[1])
        for phrase in argv[2:]:
            find(text, phrase)
    elif cmd == "doc":
        key = "doc-" + hashlib.sha256(argv[1].encode()).hexdigest()[:16]
        text, meta = fetch_doc(argv[1], key)
        print(f"{len(text):,} characters; {meta}")
        for phrase in argv[2:]:
            find(text, phrase)
    elif cmd == "page":
        key = "page-" + hashlib.sha256(argv[1].encode()).hexdigest()[:16]
        text = fetch(argv[1], key)
        for phrase in argv[2:]:
            find(text, phrase)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
