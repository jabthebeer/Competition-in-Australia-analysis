"""Comparing Australia with similar economies (docs/forward_plan_international_benchmarking.md).

- ``concordance``: ANZSIC 2006 to ISIC Rev. 4 (ABS correspondence) and the common industry groups.
- ``stan``: industry value added for OECD economies (OECD STAN 2025).
- ``wdi``: GDP per head, population and trade openness (World Bank World Development Indicators).
- ``peers``: the similarity ranking that proposes a peer group for the owner to approve.

Raw downloads go to ``data/raw/<source>/`` with a manifest, as in the pipeline; outputs go to
``data/processed/international/``.
"""

from __future__ import annotations

from ..pipeline import store

OUT = store.PROCESSED / "international"

# The 38 OECD members (ISO 3166-1 alpha-3), November 2026.
OECD = (  # noqa: SIM905 (one line per row of members reads better than 38 lines)
    "AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX "
    "NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA"
).split()


def prose(doc: str) -> str:
    """A module docstring's body (after its first paragraph) as Markdown: wrapped lines joined, bullets kept."""
    paras = []
    for para in doc.strip().split("\n\n")[1:]:
        lines: list[str] = []
        for line in para.splitlines():
            line = line.strip()
            if line.startswith("- ") or not lines:
                lines.append(line)
            else:
                lines[-1] += " " + line
        paras.append("\n".join(lines))
    return "\n\n".join(paras)
