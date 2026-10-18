# Data sources register

Every dataset used, with where it came from and what it may be used for. Raw downloads live in `data/raw/<source>/` (not committed). Each file's URL, retrieval time, size and SHA-256 are in `data/manifests/<source>.json`. Built panels are in `data/processed/<source>/`, in the common format described in `alcia/src/alcia/pipeline/schema.py`. Feasibility and limits: [`docs/data_pipeline_feasibility.md`](../docs/data_pipeline_feasibility.md).

## Built

| Source (connector) | Publisher | URL | Accessed | Access / licence | Coverage | Key variables | Status |
|---|---|---|---|---|---|---|---|
| Counts of Australian Businesses, including Entries and Exits, cube 2 (`abs_cabee`) | ABS | <https://www.abs.gov.au/statistics/economy/business-indicators/counts-australian-businesses-including-entries-and-exits> (15 releases; each cube URL in `data/manifests/abs_cabee.json`) | 15 Oct 2026 (Jun 2007–Jun 2009 to Jul 2016–Jun 2020); 14 and 18 Oct 2026 (Jul 2017–Jun 2021 to Jul 2021–Jun 2025) | CC BY 4.0. Cells perturbed by the ABS | ANZSIC class × state × employment size, FY2007-08 to FY2024-25 | Businesses at start and end of year, entries, exits | Built; level break between the 2016–20 and 2017–21 releases |
| Counts of Australian Businesses, businesses by industry division × SA2 (`abs_cabee_local`) | ABS | Jun 2007–Jun 2011 release, `sa2_emp.xls`; Jun 2009–Jun 2013 release, `816507.xls` (URLs in `data/manifests/abs_cabee_local.json`) | 18 Oct 2026 | CC BY 4.0. Cells perturbed by the ABS | Division × SA2 (ASGS 2011) × employment size, 30 June 2009–2013; June 2011 in both releases | Businesses operating (stocks; no entries or exits at this level) | Built; one table per release |
| Retail Trade, Australia (`abs_retail`) | ABS (Data API, dataflow `RT` 1.0.0) | <https://data.api.abs.gov.au/rest/data/ABS,RT,1.0.0/M1..10+20..M> and `/M3..20..Q` | 18 Oct 2026 | CC BY 4.0 | 15 retail subgroups and 6 groups × state; monthly Apr 1982–Jun 2025 (series ended), quarterly volumes | Turnover (current prices), chain-volume turnover | Built |
| Labour Force, Australia, Detailed, table EQ06 (`abs_lfs`) | ABS | <https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia-detailed/mar-2026/EQ06.xlsx> | 18 Oct 2026 (March 2026 release, the latest on that date) | CC BY 4.0. Survey estimates with sampling error | ANZSIC group × state, mid-quarter months Nov 1984–Feb 2026 | Employed, employed full-time, hours actually worked | Built |
| Data by Region (`abs_regional`) | ABS (Data API, `ABS_REGIONAL_ASGS2021` 1.6.0 and `ABS_REGIONAL_LGA2021` 1.6.0) | <https://data.api.abs.gov.au/rest/dataflow/ABS/ABS_REGIONAL_ASGS2021> | 18 Oct 2026 | CC BY 4.0 | Division × SA2, LGA, state; businesses 30 Jun 2021–2025; employee jobs 2017-18 to 2022-23 | Businesses (CABEE_*), employee jobs (LEED_*) | Built |
| ASGS Edition 3 correspondences (`abs_asgs`) | ABS (via data.gov.au) | <https://data.gov.au/data/dataset/2c79581f-600e-4560-80a8-98adb1922dfc> | 18 Oct 2026 | CC BY 4.0 | 2,641 postcodes (2021) to SA2, SA3, SA4, GCCSA, LGA | Population share of each postcode in each area | Built (lookup) |
| ABN Bulk Extract (`abr_abn`) | Australian Business Register (via data.gov.au) | <https://data.gov.au/data/dataset/abn-bulk-extract> (files `public_split_1_10.zip`, `public_split_11_20.zip`, extract of 14 Oct 2026) | 18 Oct 2026 | CC BY 3.0 AU. Record-level data (sole traders' postcodes) kept local; only counts committed | 20,595,728 ABNs; status dates from Jul 1999; postcode of main business location | Cancellations by month, active-since months, GST registrations, active stock; entity type; industry inferred from names; cancellations by SA4 × inferred industry × month (apportioned from postcodes) | Built; snapshot limits in the feasibility note |
| ASIC Business Names Dataset (`asic_business_names`) | ASIC (via data.gov.au) | <https://data.gov.au/data/dataset/asic-business-names> (`business_names_202610.zip`, extract of 14 Oct 2026) | 18 Oct 2026 | CC BY 3.0 AU | 3,313,726 names; registrations from Jun 2012; cancellations from Oct 2025 | Registrations, cancellations (national only), names held; location via ABN; inferred industry | Built |
| ASIC Company Dataset (`asic_companies`) | ASIC (via data.gov.au) | <https://data.gov.au/data/dataset/asic-companies> (`company_202610.zip`, extract of 13 Oct 2026) | 18 Oct 2026 | CC BY 3.0 AU | Registrations from 1991; deregistrations for about the last year | Registrations, deregistrations, companies registered; proprietary or public; location via ABN; inferred industry | Built |
| CLUE business establishments (`clue_melbourne`) | City of Melbourne | <https://data.melbourne.vic.gov.au/explore/dataset/business-establishments-with-address-and-industry-classification/> | 18 Oct 2026 (dataset processed 16 Mar 2026) | CC BY 4.0 | City of Melbourne, 13 small areas, census years 2002–2024 | Establishments by ANZSIC class; trading names (used to test the name classifier) | Built |

## Parser only

| Source (connector) | Publisher | URL | Accessed | Access / licence | Coverage | Key variables | Status |
|---|---|---|---|---|---|---|---|
| Internet Vacancy Index (`jsa_ivi`) | Jobs and Skills Australia | <https://www.jobsandskills.gov.au/data/internet-vacancy-index> | Not reached: connection refused from the build environment, 18 Oct 2026 | CC BY 4.0 (per publisher) | ANZSCO occupation × state from 2006; regions from 2010 | Online job advertisements | Parser written and tested on a synthetic workbook only; save workbooks to `data/raw/jsa_ivi/` and run `alcia pipeline build jsa_ivi` |

## Used by earlier analyses

Listed in `alcia/SOURCES.md`: CPI (ABS Data API), State Accounts, Labour Force table 05, and the legislation registers.

## To do

| Source | Publisher | URL | Accessed | Access / licence | Coverage | Key variables | Status |
|---|---|---|---|---|---|---|---|
| Australian Industry | ABS | | | Public | | Industry value added, turnover | To do |
| Corporate tax transparency; taxation statistics by industry | ATO | | | Public | | Total income, taxable income, entity; counts and margins by fine industry | To do |
| Product Market Regulation | OECD | | | Public | | PMR indicators | To do |
| Productivity data | PC / ABS | | | Public | | MFP, labour productivity | To do |
