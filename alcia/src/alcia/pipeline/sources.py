"""Registry of data sources the pipeline can build panels from.

Each entry says who publishes the data, under what licence, and at what industry and geographic
detail, so the menu and data/SOURCES.md can describe every panel. Feasibility notes are in
docs/data_pipeline_feasibility.md.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    publisher: str
    url: str
    licence: str
    frequency: str
    industry: str  # classification and finest level
    geography: str  # finest geography
    measures: str
    status: str = "built"  # built, planned or not feasible

    def as_dict(self) -> dict:
        return asdict(self)


SOURCES: dict[str, Source] = {
    s.id: s
    for s in (
        Source(
            "abs_cabee",
            "Counts of Australian Businesses, including Entries and Exits",
            "ABS",
            "https://www.abs.gov.au/statistics/economy/business-indicators/counts-australian-businesses-including-entries-and-exits",
            "CC BY 4.0",
            "annual (financial year)",
            "ANZSIC 2006 class",
            "state",
            "businesses operating, entries, exits, by employment size",
        ),
    )
}
