# Sources, licences and attribution (`alcia/`, `regulation-register/`)

## Bundled data

| File | Source | Version | Licence | Retrieved |
|---|---|---|---|---|
| `src/alcia/data/anzsic2006.json` | ABS Data API codelist `CL_ANZSIC_2006` <https://data.api.abs.gov.au/rest/codelist/ABS/CL_ANZSIC_2006/1.1.0> (19 divisions, 86 subdivisions, 215 groups, 506 classes) | 1.1.0 | CC BY 4.0, Australian Bureau of Statistics | 14 Oct 2026 (response SHA-256 in the file) |
| `src/alcia/data/cpi17_classes.json` | ABS Data API, CPI dataflow 1.1.0, codelist `CL_CPI_INDEX_17`: the 87 expenditure classes <https://data.api.abs.gov.au/rest/dataflow/ABS/CPI/1.1.0?references=codelist> | 17th series | CC BY 4.0, Australian Bureau of Statistics | 15 Oct 2026 (response SHA-256 in the file) |

Regenerate with `scripts/fetch_anzsic.py` and `scripts/fetch_cpi_classes.py`.

## Legislation registers read by `alcia dates`

| Register | Endpoint used | Terms |
|---|---|---|
| Federal Register of Legislation | <https://api.prod.legislation.gov.au/v1/> (titles, versions, search, documents) | CC BY 4.0. **Attribution: "Sourced from the Federal Register of Legislation at" the retrieval date** (each report entry carries `retrieved_at`) |
| Queensland legislation | <https://www.legislation.qld.gov.au/view/xml/…> | CC BY 4.0 |
| Tasmanian legislation | <https://www.legislation.tas.gov.au/projectdata?…> and `/view/xml/…` | CC BY 4.0 |
| ACT legislation register | <https://legislation.act.gov.au/{a,sl}/…/> | Robots.txt crawl-delay 10 s (respected). Copyright terms point to the JACS copyright policy; licence not confirmed |
| WA legislation | <https://www.legislation.wa.gov.au/legislation/statutes.nsf/…> | CC BY 4.0 |
| NT legislation | <https://legislation.nt.gov.au/…format=assented> | NT copyright policy allows reuse on conditions; not a CC licence |
| Victorian legislation | <https://www.legislation.vic.gov.au/in-force/…> (version dates only) | "Personal use only"; document hosts disallowed by robots.txt, so not fetched |
| NSW, SA | Not read | Both return a Cloudflare challenge to automated requests |

Register responses used as test fixtures (`tests/fixtures/`) were retrieved on 14–15 October 2026. Large responses are trimmed, with their structure unchanged. The ACT, NT and Victorian fixtures, whose content is not under a Creative Commons licence, are reduced to factual extracts: dates, provision labels and the markup the parsers read (`scripts/trim_state_fixtures.py`). The WA fixture is a whole page (CC BY 4.0).

## Outcome data

The data pipeline's sources (CABEE, Retail Trade, Labour Force EQ06, Data by Region, ASGS correspondences, ABN Bulk Extract, ASIC registers, City of Melbourne CLUE, Internet Vacancy Index) are listed with URLs, access dates and licences in [`data/SOURCES.md`](../data/SOURCES.md); raw files' checksums are in `data/manifests/`.

First case (all Australian Bureau of Statistics, CC BY 4.0). Downloads are cached in `alcia/.cache/` (not committed); the built CABEE panel is committed in `data/processed/abs_cabee/`.

| Data | Source | Used for |
|---|---|---|
| Counts of Australian Businesses, including Entries and Exits (8165.0): ANZSIC class × state × employment size cubes | 15 releases, Jun 2007–Jun 2009 to Jul 2021–Jun 2025 (the registered analyses use the first 10); each release URL, publication date and SHA-256 are in `data/processed/abs_cabee/cabee_manifest.json` | Entry and exit rates |
| Consumer Price Index, 17th series | ABS Data API, dataflow `ABS,CPI,1.1.0` <https://data.api.abs.gov.au/rest/data/ABS,CPI,1.1.0/…> (index numbers by capital city, quarterly) | Relative food and clothing prices |
| Australian National Accounts: State Accounts (5220.0), 2024-25 | <https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-state-accounts/2024-25-financial-year> (tables 5220002–5220009) | Retail gross value added (chain volume) and compensation of employees |
| Labour Force, Australia, Detailed, March 2026, table 05 | <https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia-detailed/mar-2026/6291005.xlsx> | Employment by state and industry division |

The WA trading-hours dates were checked against the WA register's *Retail Trading Hours Act 1987* page and its "History of this Act" (<https://www.legislation.wa.gov.au/legislation/statutes.nsf/law_a696.html>, CC BY 4.0), retrieved 15 October 2026.

## Register records

Every date in `regulation-register/records/*.json` carries its own source URL. The records were drafted by AI-assisted desk research on 14–15 October 2026 from official registers, gazettes, government and regulator pages, and published research. They have not yet been reviewed by a person (`review.status = "draft"`).

## Research behind the design documents

See the source lists in `docs/econometric_foundation_scoping.md` (§12) and `docs/impact_evaluation_design.md` (§11).
