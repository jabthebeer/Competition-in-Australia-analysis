# Data sources register

Every dataset used, with where it came from and what it may be used for. Raw downloads live in `data/raw/<source>/` (not committed). Each file's URL, retrieval time, size and SHA-256 are in `data/manifests/<source>.json`. Built panels are in `data/processed/<source>/`, in the common format described in `alicia/src/alicia/pipeline/schema.py`. Feasibility and limits: [`docs/data_pipeline_feasibility.md`](../docs/data_pipeline_feasibility.md).

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
| Australian National Accounts: State Accounts, tables 1–10 (`abs_state_accounts`) | ABS | <https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-state-accounts/2024-25-financial-year> (file URLs in `data/manifests/abs_state_accounts.json`) | 18 Oct 2026 (2024-25 release) | CC BY 4.0 | ANZSIC division × state and Australia, FY1989-90 to FY2024-25 | Gross value added (chain volume and current prices), total factor income, gross state product, GSP per person, real gross state income | Built; chain volume series do not add across industries |

## Controls (macroeconomic conditions)

Series that evaluations net out rather than outcomes (`alicia/src/alicia/pipeline/controls.py`, forward plan Phase 1). Panels are in `data/processed/controls/` (`state_quarter`, `state_month`, `industry_quarter`, `national_month`) and are left out of the outcome coverage catalogue. ABS Data API queries are recorded in `data/manifests/abs_api.json`.

| Source (connector id) | Publisher | URL | Accessed | Access / licence | Coverage | Key variables | Status |
|---|---|---|---|---|---|---|---|
| State Final Demand, 5206.0 (`abs_sfd`) | ABS (Data API, `ANA_SFD` 1.0.0) | <https://data.api.abs.gov.au/rest/data/ABS,ANA_SFD,1.0.0/VCH+C...20..Q> | 18 Oct 2026 | CC BY 4.0 | 8 states, quarterly, seasonally adjusted, from 1983-84 (chain volume from 1985-86) to Jun qtr 2026 | State final demand; private and public final demand; household consumption, total and 19 purposes; government consumption; business and dwelling investment; compensation of employees | Built |
| Population, ERP (`abs_erp`) | ABS (Data API, `ERP_Q` 1.0.0) | <https://data.api.abs.gov.au/rest/data/ABS,ERP_Q,1.0.0/1.3.TOT..Q> | 18 Oct 2026 | CC BY 4.0 | States and Australia, quarterly, Sep qtr 1981 to Mar qtr 2026 | Estimated resident population (end of quarter) | Built |
| Wage Price Index (`abs_wpi`) | ABS (Data API, `WPI` 1.2.0) | <https://data.api.abs.gov.au/rest/data/ABS,WPI,1.2.0/1.THRPEB.7+1.TOT.10+20..Q> | 18 Oct 2026 | CC BY 4.0 | States and Australia, quarterly, Sep qtr 1997 to Jun qtr 2026; seasonally adjusted for Australia only | Total hourly rates of pay excluding bonuses, private sector and all sectors | Built |
| Labour Force (`abs_lf`) | ABS (Data API, `LF` 1.0.0) | <https://data.api.abs.gov.au/rest/data/ABS,LF,1.0.0/M3+M9+M13+M12+M16.3.1599.10..M> (and the seasonally adjusted query, `.20..M`) | 18 Oct 2026 | CC BY 4.0. Survey estimates | Monthly, Feb 1978 to Sep 2026; seasonally adjusted for 6 states and Australia, original for all 8 | Employed, labour force, unemployment rate, participation rate, employment-to-population ratio | Built |
| Building Approvals (`abs_ba`) | ABS (Data API, `BA_GCCSA` 1.0.0) | <https://data.api.abs.gov.au/rest/data/ABS,BA_GCCSA,1.0.0/1+2.1.9.TOT.100+110+TOT.20+10..M> | 18 Oct 2026 | CC BY 4.0 | States, Greater Capital Cities and rest of state, monthly, original (from 1961 or 1983 by series) | Dwelling units approved; value of building work approved (total, residential, houses) | Built |
| National accounts, gross value added by industry (`abs_gva`) | ABS (Data API, `ANA_IND_GVA` 1.0.0) | <https://data.api.abs.gov.au/rest/data/ABS,ANA_IND_GVA,1.0.0/VCH+C...20..AUS.Q> | 18 Oct 2026 | CC BY 4.0 | Australia, 19 divisions and 31 sub-industries, quarterly, seasonally adjusted, Sep qtr 1974 to Jun qtr 2026 | Gross value added, chain volume | Built |
| Business Indicators (`abs_qbis`) | ABS (Data API, `QBIS` 1.0.0) | <https://data.api.abs.gov.au/rest/data/ABS,QBIS,1.0.0/M1+M5+M7.CUR+CVM..TOT.20+10.AUS.Q> | 18 Oct 2026 | CC BY 4.0 | Australia, 17 divisions (not A or O; some measures cover fewer), quarterly from 1984 | Sales (current and chain volume), wages, gross operating profits | Built |
| Index of Commodity Prices, table I2 (`rba_commodity`) | Reserve Bank of Australia | <https://www.rba.gov.au/statistics/tables/xls/i02hist.xlsx> | 18 Oct 2026 (published 1 Oct 2026) | CC BY 4.0 (rba.gov.au/copyright) | Monthly, Jul 1982 to Sep 2026 | All items, rural, non-rural, base metals, bulk; A$, SDR and US$ (index 2024/25 = 100) | Built |

## Parser only

| Source (connector) | Publisher | URL | Accessed | Access / licence | Coverage | Key variables | Status |
|---|---|---|---|---|---|---|---|
| Internet Vacancy Index (`jsa_ivi`) | Jobs and Skills Australia | <https://www.jobsandskills.gov.au/data/internet-vacancy-index> | Not reached: connection refused from the build environment, 18 Oct 2026 | CC BY 4.0 (per publisher) | ANZSCO occupation × state from 2006; regions from 2010 | Online job advertisements | Parser written and tested on a synthetic workbook only; save workbooks to `data/raw/jsa_ivi/` and run `alicia pipeline build jsa_ivi` |

## Used by earlier analyses

Listed in `alicia/SOURCES.md`: CPI (ABS Data API), State Accounts, Labour Force table 05, and the legislation registers.

## To do

| Source | Publisher | URL | Accessed | Access / licence | Coverage | Key variables | Status |
|---|---|---|---|---|---|---|---|
| Australian Industry | ABS | | | Public | | Industry value added, turnover | To do |
| Corporate tax transparency; taxation statistics by industry | ATO | | | Public | | Total income, taxable income, entity; counts and margins by fine industry | To do |
| Product Market Regulation | OECD | | | Public | | PMR indicators | To do |
| Productivity data | PC / ABS | | | Public | | MFP, labour productivity | To do |
