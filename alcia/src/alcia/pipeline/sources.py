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
    status: str = "built"  # built, parser only, planned or not feasible

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
        Source(
            "abs_cabee_local",
            "Counts of Australian Businesses: businesses by division and SA2, June 2009-2013",
            "ABS",
            "https://www.abs.gov.au/ausstats/abs@.nsf/mf/8165.0",
            "CC BY 4.0",
            "annual (30 June), two archived releases",
            "ANZSIC 2006 division",
            "SA2 (ASGS 2011)",
            "businesses at 30 June 2009-2013 by employment size; stocks only",
        ),
        Source(
            "abs_retail",
            "Retail Trade, Australia",
            "ABS",
            "https://data.api.abs.gov.au/rest/dataflow/ABS/RT",
            "CC BY 4.0",
            "monthly (turnover); quarterly (volume)",
            "15 retail subgroups (6 are single ANZSIC classes) and 6 groups",
            "state",
            "turnover, current prices, April 1982 to June 2025 (series ended); chain-volume turnover by group",
        ),
        Source(
            "abs_lfs",
            "Labour Force, Australia, Detailed (table EQ06)",
            "ABS",
            "https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia-detailed",
            "CC BY 4.0",
            "quarterly (mid-quarter months)",
            "ANZSIC 2006 group (industry of main job)",
            "state",
            "employed persons, full-time employed, hours actually worked; Nov 1984 to Feb 2026 (survey estimates)",
        ),
        Source(
            "abs_regional",
            "Data by Region (ASGS 2021 and LGA 2021 dataflows)",
            "ABS",
            "https://data.api.abs.gov.au/rest/dataflow/ABS/ABS_REGIONAL_ASGS2021",
            "CC BY 4.0",
            "annual",
            "ANZSIC 2006 division",
            "SA2 and LGA",
            "businesses at 30 June 2021-2025; employee jobs (LEED) 2017-18 to 2022-23",
        ),
        Source(
            "abs_asgs",
            "ASGS Edition 3 correspondences (postcode to SA2, SA3, SA4, GCCSA, LGA)",
            "ABS",
            "https://data.gov.au/data/dataset/asgs-edition-3-2021-correspondences",
            "CC BY 4.0",
            "one-off (2021 boundaries)",
            "none",
            "postcode to statistical areas",
            "population shares used to move postcode counts to statistical areas",
        ),
        Source(
            "abr_abn",
            "ABN Bulk Extract",
            "Australian Business Register",
            "https://data.gov.au/data/dataset/abn-bulk-extract",
            "CC BY 3.0 AU",
            "weekly snapshot (14 Oct 2026 used)",
            "ANZSIC 2006 inferred from business names (class, group or division)",
            "postcode",
            "ABN cancellations by month; ABNs and GST registrations active since a month (survivors); active ABNs",
        ),
        Source(
            "asic_business_names",
            "ASIC Business Names Dataset",
            "ASIC",
            "https://data.gov.au/data/dataset/asic-business-names",
            "CC BY 3.0 AU",
            "weekly snapshot (Oct 2026 used)",
            "ANZSIC 2006 inferred from the business name",
            "postcode (from the ABN)",
            "registrations by month since June 2012 (survivors before the last year); cancellations; names held",
        ),
        Source(
            "asic_companies",
            "ASIC Company Dataset",
            "ASIC",
            "https://data.gov.au/data/dataset/asic-companies",
            "CC BY 3.0 AU",
            "weekly snapshot (Oct 2026 used)",
            "ANZSIC 2006 inferred from the company name",
            "postcode (from the ABN)",
            "registrations by month since 1991 (survivors before the last year); deregistrations; companies held",
        ),
        Source(
            "clue_melbourne",
            "Census of Land Use and Employment: business establishments",
            "City of Melbourne",
            "https://data.melbourne.vic.gov.au/explore/dataset/business-establishments-with-address-and-industry-classification/",
            "CC BY 4.0",
            "annual (census years 2002-2024)",
            "ANZSIC 2006 class",
            "CLUE small area (City of Melbourne only)",
            "business establishments; also used to test the name classifier",
        ),
        Source(
            "jsa_ivi",
            "Internet Vacancy Index",
            "Jobs and Skills Australia",
            "https://www.jobsandskills.gov.au/data/internet-vacancy-index",
            "CC BY 4.0",
            "monthly",
            "ANZSCO occupation (not industry)",
            "state; IVI region",
            "online job advertisements; parser only (site not reachable here, files must be saved by hand)",
            status="parser only",
        ),
    )
}

MEASURE_LABELS = {
    "businesses_start": "businesses at the start of the year",
    "businesses_end": "businesses at the end of the year",
    "entries": "entries",
    "exits": "exits",
    "turnover": "turnover",
    "turnover_volume": "turnover in volume terms",
    "employed": "employed persons",
    "employed_full_time": "employed full-time",
    "hours_actual": "hours actually worked",
    "businesses": "businesses (30 June)",
    "employee_jobs": "employee jobs",
    "abn_cancellations": "ABN cancellations",
    "abn_active_since": "active ABNs by start month (survivors)",
    "gst_active_since": "GST registrations by start month (survivors)",
    "abn_active": "active ABNs",
    "business_name_registrations": "business-name registrations",
    "business_name_cancellations": "business-name cancellations (last 12 months, Australia only)",
    "business_names_registered": "business names held",
    "company_registrations": "company registrations",
    "company_deregistrations": "company deregistrations (last 12 months)",
    "companies_registered": "companies registered",
    "establishments": "business establishments",
    "online_vacancies": "online job vacancies",
}


def measure_label(measure: str) -> str:
    return MEASURE_LABELS.get(measure, measure.replace("_", " "))
