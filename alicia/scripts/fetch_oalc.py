"""Stream the Open Australian Legal Corpus and keep its legislation: an index of laws in force for NSW and SA, whose
registers refuse automated requests, and a cross-check for the Commonwealth, Queensland, WA and Tasmania.

Usage: uv run python scripts/fetch_oalc.py

Source: Isaacus (Umar Butler), Open Australian Legal Corpus v7.1.0, https://huggingface.co/datasets/isaacus/open-
australian-legal-corpus, CC BY 4.0 (the corpus); the legislation in it is CC BY 4.0 from each register, "Sourced from
the <register> at 10 March 2025". Not an official source: each law is cited by its official register URL (DECISIONS
E-118, which lists the corpus's limitations).

The 9.4 GB ``corpus.jsonl`` is read once as a stream, at a pinned revision, and never stored whole: court decisions
are dropped; each law's text goes to ``data/raw/oalc/<jurisdiction>.jsonl.gz`` (not committed); its metadata goes to
``data/processed/legislation/oalc_laws.csv.gz``; the stream's size and SHA-256 go to ``data/manifests/oalc.json``.
A dropped connection resumes from the last byte read.
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import json
import sys
import time
from contextlib import ExitStack
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
REVISION = "ef45e3fec41a960919a31149eee6dab9aa39f725"  # v7.1.0, as listed by the Hugging Face API on 6 Nov 2026
URL = f"https://huggingface.co/datasets/isaacus/open-australian-legal-corpus/resolve/{REVISION}/corpus.jsonl"
RAW = ROOT / "data" / "raw" / "oalc"
OUT = ROOT / "data" / "processed" / "legislation" / "oalc_laws.csv.gz"
MANIFEST = ROOT / "data" / "manifests" / "oalc.json"
KEEP = ("primary_legislation", "secondary_legislation")
FIELDS = ("version_id", "type", "jurisdiction", "source", "citation", "url", "date", "when_scraped", "chars", "sha256")


def main() -> None:
    with ExitStack() as files:
        run(files)


def run(files: ExitStack) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    offset, buf, lines, kept = 0, b"", 0, 0
    texts: dict[str, gzip.GzipFile] = {}
    meta_f = files.enter_context(gzip.open(OUT, "wt", newline="", encoding="utf-8"))  # noqa: SIM115 (ExitStack)
    meta = csv.DictWriter(meta_f, fieldnames=FIELDS)
    meta.writeheader()
    started = time.time()
    total = None

    def handle(line: bytes) -> None:
        nonlocal lines, kept
        lines += 1
        doc = json.loads(line)
        if doc.get("type") not in KEEP:
            return
        kept += 1
        text = doc.get("text") or ""
        j = doc["jurisdiction"]
        if j not in texts:
            texts[j] = files.enter_context(gzip.open(RAW / f"{j}.jsonl.gz", "wb"))  # noqa: SIM115
        texts[j].write(line + b"\n")
        meta.writerow(
            {k: doc.get(k) for k in FIELDS[:8]}
            | {"chars": len(text), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
        )

    with httpx.Client(timeout=httpx.Timeout(120, connect=60), follow_redirects=True) as client:
        attempts = 0
        while True:
            headers = {"Range": f"bytes={offset}-"} if offset else {}
            try:
                with client.stream("GET", URL, headers=headers) as r:
                    r.raise_for_status()
                    if offset and r.status_code != 206:
                        raise RuntimeError(f"server ignored the range request (status {r.status_code})")
                    if total is None:
                        total = int(r.headers.get("content-length", 0)) + offset
                    for chunk in r.iter_bytes(1 << 20):
                        digest.update(chunk)
                        offset += len(chunk)
                        buf += chunk
                        *complete, buf = buf.split(b"\n")
                        for line in complete:
                            if line.strip():
                                handle(line)
                        if lines and lines % 20000 < len(complete):
                            print(f"{offset / 1e9:.2f} of {total / 1e9:.2f} GB; {lines} documents, {kept} laws",
                                  file=sys.stderr, flush=True)  # fmt: skip
                break
            except (httpx.HTTPError, RuntimeError) as exc:
                attempts += 1
                if attempts > 8:
                    raise
                print(f"connection lost at {offset} bytes ({exc}); resuming", file=sys.stderr, flush=True)
                time.sleep(min(60, 2**attempts))
    if buf.strip():
        handle(buf)
    meta_f.close()
    for f in texts.values():
        f.close()  # flushed before the manifest is written; ExitStack closing again is harmless
    if total and offset != total:
        raise RuntimeError(f"read {offset} bytes, expected {total}")
    MANIFEST.write_text(
        json.dumps(
            {
                "source": "oalc",
                "files": [
                    {
                        "url": URL,
                        "revision": REVISION,
                        "version": "7.1.0",
                        "retrieved": dt.date.today().isoformat(),
                        "bytes": offset,
                        "sha256": digest.hexdigest(),
                        "licence": "CC BY 4.0 (corpus); legislation CC BY 4.0 from each register, as at 10 March 2025",
                        "note": f"{lines} documents read; {kept} laws (primary and secondary legislation) kept",
                    }
                ],
            },
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    mins = (time.time() - started) / 60
    print(
        f"Done: {lines} documents, {kept} laws kept, {offset} bytes in {mins:.0f} minutes; SHA-256 {digest.hexdigest()}"
    )


if __name__ == "__main__":
    main()
