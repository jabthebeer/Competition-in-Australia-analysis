"""Check that every quoted source in the requirements register traces back to its primary source, and that every
requirement names who administers it (owner, 18 November 2026). Runs offline, in a few seconds:

    uv run python scripts/check_traceability.py

Every claim in a requirement rests on a source that records the address of the document, the provision quoted (its
locator), the exact words and the date they were read. A reader needs two more things to find those words again when
a link cannot take them straight there:

- **A locator for every source**: the section, clause, page or heading the words sit under.
- **The version quoted, for every source on an official legislation register**: a compilation (Commonwealth), an
  authorised version (Victoria), a dated corpus copy (its ``corpus_version_id``), or the register's current version,
  which the ``accessed`` date fixes. Registers keep their earlier versions, so the words can be found after the law
  changes.

It also checks that every state, territory and Commonwealth requirement names who administers it
(``administration``), except where the law quoted names no body; those are listed in ``NO_BODY`` with the reason.
How a source is opened (at the section, the words, a PDF page, or the law) is ``source_links.deep_link``. Prints how
the sources are opened and which version each quotes, then any problems; exits 1 if there are problems.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from collections.abc import Iterator

from alicia.register.requirements import Requirement, Source, load_requirements
from alicia.register.source_links import deep_link

# The official legislation registers: their sources must name the version they quote.
LEGISLATION = re.compile(
    r"^https://(?:www\.)?legislation\.(?:gov\.au|nsw\.gov\.au|vic\.gov\.au|qld\.gov\.au|wa\.gov\.au|sa\.gov\.au"
    r"|tas\.gov\.au|act\.gov\.au|nt\.gov\.au)/"
)
VERSION = re.compile(r"current|version|compilation|as at|as made|reprint|republication", re.I)
# Requirements whose quoted law names no body that administers them (searched 18 November 2026).
NO_BODY = {
    "nsw-electricity-asp-accreditation": "The Electricity Supply Act 1995 leaves accreditation of service providers "
    "to the regulations, which were not read.",
    "nsw-short-term-rental-night-cap": "The planning instrument quoted sets the cap but names no body that enforces "
    "it.",
    "nsw-workplace-surveillance-notice": "The Workplace Surveillance Act 2005 names no regulator; its offences are "
    "prosecuted in the courts.",
    "nsw-land-sales-disclosure": "The Conveyancing Act 1919 enforces off-the-plan disclosure through the purchaser's "
    "right to rescind (ss 66ZO, 66ZP) and names no body that enforces it.",
    "wa-land-sales-disclosure": "The Strata Titles Act 1985 enforces disclosure before contract through the buyer's "
    "right to avoid the contract (s 159) and names no body that enforces it.",
}


def sources(q: Requirement) -> Iterator[tuple[str, Source]]:
    """Every quoted source in a requirement, with the part of the record it supports."""
    for s in q.sources:
        yield "source", s
    for t in q.triggers:
        for s in t.sources:
            yield "trigger", s
    for r in q.reach:
        for s in r.sources:
            yield "reach", s
    for a in q.administration:
        for s in a.sources:
            yield "administration", s


def version(s: Source) -> str:
    """Which version of the document a source quotes: 'corpus copy', 'named', 'web page as read' or '' (none)."""
    if s.corpus_version_id:
        return "corpus copy"
    if VERSION.search(s.locator or ""):
        return "named"
    if not LEGISLATION.match(str(s.url)):
        return "web page as read"  # guidance pages and council documents: the accessed date is the version
    return ""


def an(word: str) -> str:
    return "an" if word[0] in "aeiou" else "a"


def problems(reqs: list[Requirement]) -> list[str]:
    """Sources a reader could not trace, and requirements that name no administering body without a reason."""
    out = []
    for q in reqs:
        for part, s in sources(q):
            if not (s.locator or "").strip():
                out.append(f"{q.id}: {an(part)} {part} source has no locator ({s.url})")
            if not version(s):
                out.append(f"{q.id}: {an(part)} {part} source on a legislation register names no version "
                           f"({s.url}, {s.locator})")
        if q.tier != "local" and not q.administration and q.id not in NO_BODY:
            out.append(f"{q.id}: names no body that administers it")
        if q.id in NO_BODY and q.administration:
            out.append(f"{q.id}: now names its administering body, so remove it from NO_BODY")
    return out


def summary(reqs: list[Requirement]) -> dict[str, Counter]:
    """How the register's sources are opened and which version each quotes, for the check's report."""
    how, ver, part = Counter(), Counter(), Counter()
    for q in reqs:
        law_ids = tuple(law.register_id or "" for law in q.laws)
        for p, s in sources(q):
            how[deep_link(str(s.url), s.locator, s.quote, law_ids)["how"]] += 1
            ver[version(s) or "none"] += 1
            part[p] += 1
    return {"opened at": how, "version": ver, "part": part}


def main() -> int:
    reqs = load_requirements()
    if reqs.problems:
        print("\n".join(reqs.problems))
        return 1
    qs = reqs.requirements
    for name, counts in summary(qs).items():
        print(f"{name}: " + ", ".join(f"{k} {v:,}" for k, v in counts.most_common()))
    named = sum(1 for q in qs if q.administration)
    print(f"administering body named: {named:,} of {len(qs):,} requirements; "
          f"none named in the law quoted: {len(NO_BODY)}")
    found = problems(qs)
    print("\n".join(found) if found else "every source has a locator and, on a legislation register, a version")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
