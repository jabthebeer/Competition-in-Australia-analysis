"""Check that every quote in regulation-register/requirements/ appears, word for word, in the source it cites.

Usage: uv run python scripts/check_requirement_quotes.py [--refresh]

- ``register-text`` sources on the Federal Register are checked against the law's latest compilation (read through
  ``scripts/law_text.py``, cached in data/raw/law_text/); ``--refresh`` downloads them again first.
- Other ``register-text`` sources (state and territory registers) and ``document`` sources are checked against the
  page or document (PDF, Word or RTF) at their URL.
- ``web-page`` sources are checked against the page as fetched.
- ``corpus-copy`` sources are checked against the Open Australian Legal Corpus document they name.
- Other sources are listed as not checked.

Matching ignores differences in whitespace only. Exit status 1 if any quote is not found.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import law_text  # noqa: E402

from alicia.register.requirements import load_requirements  # noqa: E402

FRL = re.compile(r"^https://www\.legislation\.gov\.au/([CF]\d{4}[A-Z]\d{5})/")


def norm(s: str) -> str:
    return " ".join(s.split())


def main(refresh: bool = False) -> int:
    reqs = load_requirements()
    if reqs.problems:
        print("\n".join(reqs.problems))
        return 1
    texts: dict[str, str] = {}
    found = missing = unchecked = 0
    for q in reqs.requirements:
        sources = [*q.sources, *(s for t in q.triggers for s in t.sources), *(s for r in q.reach for s in r.sources)]
        sources += list(q.competition.sources) if q.competition else []
        for s in sources:
            url = str(s.url)
            if s.checked == "register-text" and (m := FRL.match(url)):
                key = f"frl-{m.group(1)}"
                if key not in texts:
                    if refresh:
                        for ext in ("txt", "json"):
                            (law_text.CACHE / f"{key}.{ext}").unlink(missing_ok=True)
                    texts[key] = norm(law_text.frl_latest(m.group(1))[0])
            elif s.checked in ("register-text", "document"):
                key = "doc-" + hashlib.sha256(url.encode()).hexdigest()[:16]
                if key not in texts:
                    if refresh:
                        for ext in ("txt", "json"):
                            (law_text.CACHE / f"{key}.{ext}").unlink(missing_ok=True)
                    texts[key] = norm(law_text.fetch_doc(url, key)[0])
            elif s.checked == "web-page":
                key = "page-" + hashlib.sha256(url.encode()).hexdigest()[:16]
                if key not in texts:
                    if refresh:
                        (law_text.CACHE / f"{key}.txt").unlink(missing_ok=True)
                    texts[key] = norm(law_text.fetch(url, key))
            elif s.checked == "corpus-copy":
                key = f"corpus-{s.corpus_version_id}"
                if key not in texts:
                    texts[key] = norm(law_text.corpus_text(s.corpus_version_id))
            else:
                unchecked += 1
                print(f"not checked: {q.id}: {s.checked} {url}")
                continue
            if norm(s.quote) in texts[key]:
                found += 1
            else:
                missing += 1
                print(f"NOT FOUND: {q.id}: {s.locator}: {s.quote[:90]}…")
    n = len(reqs.requirements)
    print(f"{found} quote(s) found, {missing} not found, {unchecked} not checked, in {n} requirement(s)")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(refresh="--refresh" in sys.argv))
