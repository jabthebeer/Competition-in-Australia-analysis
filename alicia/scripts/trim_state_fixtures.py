"""Trim saved state register pages to the parts the parsers read, for committing as test fixtures.

ACT, NT and Victorian register content is not under a Creative Commons licence (see SOURCES.md), so
the repository keeps only factual extracts: dates, provision labels and the markup the parsers in
``alicia.legislation.states`` need. WA pages (CC BY 4.0) are committed whole.

Usage: uv run python scripts/trim_state_fixtures.py <kind: act|nt|vic> <saved page> <source url> <out>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HEADER = (
    "<!-- Trimmed extract for alicia's parser tests. Source: {url} (retrieved 14-15 October 2026). "
    "Only the parts the parser reads are kept; see alicia/SOURCES.md. -->\n"
)


def act(page: str) -> str:
    notified = re.search(r"Notified:\s*[^<(]+", page)
    parts = [f"<p>{notified.group(0).strip()}</p>"] if notified else []
    for table_id in ("commencement-table", "auto-repeal-table"):
        m = re.search(rf'<table[^>]*id="{table_id}".*?</table>', page, re.S)
        if m:
            parts.append(m.group(0))
    return "\n".join(parts)


def nt(page: str) -> str:
    pairs = re.findall(r"<label>[^<]+</label>\s*<span>[^<]*</span>", page)
    return "\n".join(f"<div>{p}</div>" for p in pairs)


def vic(page: str) -> str:
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    arr = json.loads(m.group(1))

    def val(i):
        return arr[i] if isinstance(i, int) and 0 <= i < len(arr) else i

    out: list = []
    for x in arr:
        if isinstance(x, dict) and "date" in x and "version" in x:
            slot = len(out)
            out.append(None)
            entry = {}
            for key in ("date", "version", "status"):
                if key in x:
                    out.append(val(x[key]))
                    entry[key] = len(out) - 1
            out[slot] = entry
    return f'<script type="application/json" id="__NUXT_DATA__">{json.dumps(out)}</script>'


def main() -> None:
    kind, src, url, dest = sys.argv[1:5]
    page = Path(src).read_text(encoding="utf-8")
    body = {"act": act, "nt": nt, "vic": vic}[kind](page)
    Path(dest).write_text(HEADER.format(url=url) + body + "\n", encoding="utf-8")
    print(f"Wrote {dest} ({len(body)} characters kept of {len(page)})")


if __name__ == "__main__":
    main()
