# Costing parameters: data dictionary

Methods note for the Policy costing tab (forward plan [`forward_plan_policy_costing.md`](forward_plan_policy_costing.md), phase P2), 23 October 2026. It describes `data/processed/costing/parameters.json`, which the tab bundles at build time, and how it is kept current. The releases listed below are those committed on 23 October 2026; `parameters.json` itself is authoritative.

## Files

| File | Written by | What it holds |
|---|---|---|
| `data/processed/costing/sources/<source>.json` | `alicia costing-params --refresh` (or `--rebuild`) | One source: its release (identifier, date, next release, the page it was read from), each raw file's URL, SHA-256, size and retrieval date, and its tables. Some also carry `checks` (CABEE) or `derived_from` (the bundled ANZSIC codelist) |
| `data/processed/costing/parameters.json` | `alicia costing-params` (every run) | The merge of every per-source file: `schema` ("alicia-costing-parameters"), `version` (1), `vintage` (the latest release date among the sources), `sources` (id, title, publisher, release, release_date, next_release, url, files [{url, sha256}], licence, retrieved, status) and `tables` |
| `data/processed/costing/register.json` | `alicia costing-register` | The register as the tab's reference class: one entry per record (id, title, jurisdiction, family, direction, rationale, sources, channels, industries with exposure, primary commencement, review status, and the current evaluation's id, verdict, grade, finding, date, archived flag and page) |
| `data/manifests/<source>.json` | the connectors (`store.record_download`) | URL, retrieval time, size and SHA-256 of every raw download |
| `data/raw/<source>/<release>/...` | the connectors | The downloads (not committed) |

Each table in `parameters.json` is `{source, description, columns: {name: unit}, rows: [...]}`. Every row has exactly the declared columns. The table id is `<source>.<table>`.

## Commands

```bash
cd alicia
uv run alicia costing-params                 # merge the committed per-source files into parameters.json (no downloads)
uv run alicia costing-params --rebuild       # rebuild each source whose raw files are in data/raw/, then merge
uv run alicia costing-params --refresh       # download and rebuild only the sources with a newer release, then merge
uv run alicia costing-params --refresh --report summary.md   # also write a Markdown summary (old -> new release, or failed: reason)
uv run alicia costing-params --refresh --strict              # exit 1 if a source fails or is missing (default: exit 0)
uv run alicia costing-params --refresh --source abs_asna     # limit the refresh or rebuild to some sources
uv run alicia costing-register               # write data/processed/costing/register.json
```

The Pages workflow runs `uv run alicia costing-params --refresh --report "$RUNNER_TEMP/costing-refresh.md"` and then `uv run alicia costing-register` from `alicia/` every day before the site build.

## How the refresh works

For each source, in the order listed below:

1. **Discover.** Read the publisher's latest-release page or API and form the release: its identifier, release date, next release date (if stated) and the files the connector needs. No year is hard-coded.
2. **Compare.** The release is new when its identifier, date or set of files differs from the committed per-source file and it is not older. A cube added to an existing release (CABEE cube 2 in December) counts as new.
3. **Update.** Download only that source's files (into a folder named after the release), build its tables and replace its per-source file.
4. **Fall back.** If discovery, download or parsing fails, the committed file is kept, the source is marked `status: "fallback"` in `parameters.json`, a warning is printed and the run still exits 0 (1 under `--strict`).

The run therefore needs no `data/raw/`: only an updated source is downloaded. Builds are deterministic (sorted keys, stable row order, no build timestamps; dates come from the manifests), so rebuilding from the same raw files gives byte-identical output (tested).

| Source | Discovered from | A new release is |
|---|---|---|
| `abs_anzsic` | ABS Data API codelist `CL_ANZSIC_2006`, latest version | a newer codelist version (then downloaded and built from the API instead of the bundled file) |
| `abs_asna`, `abs_mfp`, `abs_australian_industry`, `abs_io`, `abs_eeh`, `abs_bcs`, `abs_berd` | the ABS latest-release page: reference period, "Released" date (or a later "Release date and time" update), next release, file links | a new release folder (e.g. `2025-26`) or release date. ASNA also reads the chain volume reference year from the page; I-O follows the page's methodology link to the concordance workbook |
| `abs_cabee_latest` | the ABS latest-release page; while it has only cube 1, the most recent earlier release with a cube 2 | a new release, or cube 2 appearing on the latest-release page (due 18 Dec 2026) |
| `abs_osca` | the OSCA latest-release page (version folder) and that version's data downloads page | a new OSCA version. An in-place revision of the same workbook within a version is not detected |
| `oecd_pmr`, `oecd_stri`, `oecd_fdi_rri` | OECD SDMX: the dataflow's latest version and the available time range and observation count for Australia | a new version, a new year or a changed observation count. The OECD API states no release date |
| `abs_capex` | the ABS latest-release page and the ABS Data API (dataflow version, last available quarter) | a new quarter or release |
| `pc_national` | the PC report page: the workbook link with its S3 `VersionId`, and the report's release date | a re-uploaded workbook (new `VersionId`) |
| `rba_hf2025` | the RDP page, its supplementary-information page and the zip's `Last-Modified` header | a re-uploaded zip |

Hosts the refresh needs: `www.abs.gov.au`, `data.api.abs.gov.au`, `sdmx.oecd.org`, `www.pc.gov.au`, `assets.pc.gov.au`, `www.rba.gov.au`.

## Conventions

- **Industry codes.** ANZSIC 2006 codes (division letter; 2-digit subdivision; 3-digit group; 4-digit class), joined to titles through `abs_anzsic.codes`. Codes for other rows: `TOT` (the total of the industries the table covers: read each description for its coverage), `OWN` (ownership of dwellings, ASNA), `UNKNOWN` (industry currently unknown, CABEE), `MKT16` (market sector, divisions A-N, R and S) and `SEL12` (selected industries, A-K and R) in the MFP tables. I-O tables use IOIG codes (`abs_io.ioig_anzsic` maps them to classes); PC National uses its 114 industries; CAPEX its own industry codes, with an `anzsic` column where one applies.
- **Years.** Financial years as `YYYY-YY` (2024-25 is July 2024 to June 2025). OECD indicators use calendar years (PMR: the vintage year); the RBA tables use the authors' `fyear`.
- **Units.** Every column states its unit. Money is AUD million in current prices unless stated (BERD: AUD thousand). Chain volume columns name their reference year where the ABS states it. Indexes name their reference year. Shares say whether they are proportions (0-1) or per cent.
- **Numbers.** Published integers are kept exactly; other values keep 7 significant digits (never fewer than their integer digits). `null` means not published (`np`, `na`, a blank cell or a confidentialised cell), not zero.
- **Derived values** are labelled "derived" in the unit or description (for example ASNA `labour_share`, CABEE class-level rates, MFP productive capital stock sums, the PC `gsp_gap`).

## Tables

### `abs_anzsic`: Australian and New Zealand Standard Industrial Classification (ANZSIC), 2006 (Revision 2.0)

Australian Bureau of Statistics. Release: CL_ANZSIC_2006 1.1.0 (no release date stated). Licence: CC BY 4.0, Australian Bureau of Statistics.

- **`abs_anzsic.codes`** (825 rows). ANZSIC 2006 (Revision 2.0) codes and titles at every level, with each code's parent and division. Divisions are letters A-S; subdivisions 2 digits, groups 3, classes 4.
  Columns: `code` (code: ANZSIC 2006); `division` (code: ANZSIC 2006 division); `level` (text: division, subdivision, group or class); `name` (text); `parent` (code: ANZSIC 2006 (null for a division)).

### `abs_asna`: Australian System of National Accounts (5204.0)

Australian Bureau of Statistics. Release: 2025-26 (2026-10-23). Licence: CC BY 4.0, Australian Bureau of Statistics.

- **`abs_asna.capital`** (300 rows). Capital stock by ANZSIC division, FY2011-12 to FY2025-26 (ASNA Table 58): net capital stock (end of year), gross fixed capital formation and consumption of fixed capital, in current prices and chain volume measures; capital services index; average age of the gross stock. OWN = ownership of dwellings. Productive capital stock is not in this table (see abs_mfp).
  Columns: `anzsic` (code: ANZSIC 2006 division or OWN); `average_age` (years); `capital_services` (index (2024-25 = 100)); `cfc_current` (AUD million, current prices); `cfc_cvm` (AUD million, chain volume measures (reference year 2024-25)); `fy` (financial year (YYYY-YY)); `gfcf_current` (AUD million, current prices); `gfcf_cvm` (AUD million, chain volume measures (reference year 2024-25)); `name` (text); `ncs_current` (AUD million, current prices); `ncs_cvm` (AUD million, chain volume measures (reference year 2024-25)).
- **`abs_asna.factor_income`** (315 rows). Factor income by ANZSIC division, FY2011-12 to FY2025-26 (ASNA Tables 46 and 48): compensation of employees (wages and salaries plus employers' social contributions), gross operating surplus and gross mixed income, total factor income. labour_share = coe / tfi (derived here; mixed income of unincorporated businesses is counted with capital). OWN = ownership of dwellings; TOT = all industries.
  Columns: `anzsic` (code: ANZSIC 2006 division, OWN or TOT); `coe` (AUD million, current prices); `employer_contributions` (AUD million, current prices); `fy` (financial year (YYYY-YY)); `gos_gmi` (AUD million, current prices); `labour_share` (proportion (0-1), derived); `name` (text); `tfi` (AUD million, current prices); `wages` (AUD million, current prices).
- **`abs_asna.gdp`** (15 rows). Gross domestic product, FY2011-12 to FY2025-26 (ASNA Table 5).
  Columns: `fy` (financial year (YYYY-YY)); `gdp_current` (AUD million, current prices); `gdp_cvm` (AUD million, chain volume measures (reference year 2024-25)).
- **`abs_asna.gva`** (315 rows). Gross value added at basic prices by ANZSIC division, FY2011-12 to FY2025-26 (ASNA Table 5). OWN = ownership of dwellings; TOT = all industries (GVA at basic prices). Shares are as published (the workbook labels the unit 'proportion' but the values are per cent). Chain volume series are not additive.
  Columns: `anzsic` (code: ANZSIC 2006 division, OWN or TOT); `fy` (financial year (YYYY-YY)); `gva_current` (AUD million, current prices); `gva_cvm` (AUD million, chain volume measures (reference year 2024-25)); `gva_share_pct` (per cent of total GVA at basic prices, current prices); `name` (text).

### `abs_mfp`: Estimates of Industry Multifactor Productivity (5260.0.55.002)

Australian Bureau of Statistics. Release: 2024-25 (2026-02-06; next release 2027-02-19). Licence: CC BY 4.0, Australian Bureau of Statistics.

- **`abs_mfp.industry`** (360 rows). Productivity, inputs and factor shares by market-sector division, FY2005-06 to FY2024-25 (5260.0.55.002 Tables 1, 6-11, 14 and 19). Value-added based indexes; '_qa' on the quality-adjusted hours basis, '_hours' on the hours-worked basis. Income shares (Table 14) are the labour and capital shares of value added used for value-added MFP; cost shares (Table 19) are shares of gross output, unsmoothed, used for gross-output MFP (may end a year earlier). null = not available.
  Columns: `anzsic` (code: ANZSIC 2006 division, MKT16 or SEL12); `capital_cost_share` (proportion (0-1)); `capital_income_share` (proportion (0-1)); `capital_productivity` (index (2023-24 = 100)); `capital_services` (index (2023-24 = 100)); `combined_inputs_hours` (index (2023-24 = 100)); `combined_inputs_qa` (index (2023-24 = 100)); `fy` (financial year (YYYY-YY)); `gva` (index (2023-24 = 100)); `intermediate_cost_share` (proportion (0-1)); `labour_cost_share` (proportion (0-1)); `labour_income_share` (proportion (0-1)); `labour_input_hours` (index (2023-24 = 100)); `labour_input_qa` (index (2023-24 = 100)); `lp_hours` (index (2023-24 = 100)); `lp_qa` (index (2023-24 = 100)); `mfp_hours` (index (2023-24 = 100)); `mfp_qa` (index (2023-24 = 100)); `name` (text).
- **`abs_mfp.market_sector`** (460 rows). Market-sector (16 industries, divisions A-N, R and S) productivity measures, last 20 years (5260.0.55.002 Table 2): value-added indexes ('kind' index), growth accounting contributions to output growth ('kind' growth, percentage points, natural log growth x 100) and two-period average income shares ('kind' share). Units by kind: index: index (2023-24 = 100); growth: per cent (natural log growth x 100); share: proportion (0-1).
  Columns: `fy` (financial year (YYYY-YY)); `kind` (text: index, growth or share); `measure` (text: measure id); `value` (see 'kind': index, per cent (log growth x 100) or proportion (0-1)).
- **`abs_mfp.productive_capital_stock`** (320 rows). Productive capital stock by market-sector division, FY2005-06 to FY2024-25 (5260.0.55.002 Table 12, incorporated plus unincorporated), summed here over asset types: all assets (including land and inventories) and fixed assets (excluding land and inventories). The sum of chain volume components is an approximation, and components the ABS does not publish ('np') are left out of the sum: check components_not_published before using a row.
  Columns: `anzsic` (code: ANZSIC 2006 division); `components` (count of asset x sector series summed); `components_not_published` (count of series not published (np) in that year); `fy` (financial year (YYYY-YY)); `name` (text); `pks_all_assets` (AUD million, chain volume measures (sum of components)); `pks_fixed_assets` (AUD million, chain volume measures (sum of components)).

### `abs_australian_industry`: Australian Industry (8155.0)

Australian Bureau of Statistics. Release: 2024-25 (2026-09-18). Licence: CC BY 4.0, Australian Bureau of Statistics.

- **`abs_australian_industry.industry`** (300 rows). Key data by ANZSIC subdivision and division, FY2022-23 to FY2024-25 (8155.0 Table 1). level: subdivision, division (the ABS division total) or total (all selected industries). Finance and insurance covers subdivision 64 only; divisions O, P and Q are private sector only. Employment is at end of June.
  Columns: `anzsic` (code: ANZSIC 2006 subdivision, division or TOT); `ebitda` (AUD million, current prices); `employment` (thousand persons); `fy` (financial year (YYYY-YY)); `iva` (AUD million, current prices); `level` (text); `name` (text); `opbt` (AUD million, current prices); `sales` (AUD million, current prices); `total_expenses` (AUD million, current prices); `total_income` (AUD million, current prices); `wages` (AUD million, current prices).
- **`abs_australian_industry.size_division`** (285 rows). Key data by employment range and ANZSIC division, FY2022-23 to FY2024-25 (8155.0 Table 5). size_band: employees (0-4, 5-19, 20-199, 200+) or total. Excludes finance and insurance (division K); divisions O, P and Q are private sector only.
  Columns: `anzsic` (code: ANZSIC 2006 division or TOT); `ebitda` (AUD million, current prices); `employment` (thousand persons); `fy` (financial year (YYYY-YY)); `iva` (AUD million, current prices); `name` (text); `opbt` (AUD million, current prices); `sales` (AUD million, current prices); `size_band` (text: employment range (employees)); `total_expenses` (AUD million, current prices); `total_income` (AUD million, current prices); `wages` (AUD million, current prices).

### `abs_cabee_latest`: Counts of Australian Businesses, including Entries and Exits (8165.0)

Australian Bureau of Statistics. Release: jul2022-jun2026 (cube 1); jul2021-jun2025 (cube 2) (2026-08-18; next release 2026-12-18). Licence: CC BY 4.0, Australian Bureau of Statistics.

- **`abs_cabee_latest.class_size`** (3594 rows). Businesses, entries and exits by ANZSIC class, subdivision and division × employment size, FY2024-25, all states summed (8165.0 cube 2 of the Jul 2021 to Jun 2025 release). size_band: nonemp (non-employing), 1-4, 5-19, 20-199, 200+ employees or total. Subdivision and division rows are sums of perturbed class cells, so they differ slightly from published totals. Rates: entries or exits per 100 businesses operating at the start of the year (derived). Classes the ABS codes as unknown (9999) are left out.
  Columns: `anzsic` (code: ANZSIC 2006 class, subdivision or division); `end` (count of businesses); `entries` (count of businesses); `entry_rate_pct` (per cent, derived); `exit_rate_pct` (per cent, derived); `exits` (count of businesses); `level` (text); `size_band` (text: employment size range); `start` (count of businesses).
- **`abs_cabee_latest.division_fy`** (84 rows). Businesses, entries and exits by ANZSIC division, FY2022-23 to FY2025-26 (8165.0 cube 1, Table 1). start/end: operating at the start/end of the financial year; entries and exits split into births/other and cancellations/other; rates as published (entries or exits per 100 businesses operating at the start). UNKNOWN = industry currently unknown; TOT = all industries.
  Columns: `anzsic` (code: ANZSIC 2006 division, UNKNOWN or TOT); `end` (count of businesses); `entries` (count of businesses); `entries_births` (count of businesses); `entries_other` (count of businesses); `entry_rate_pct` (per cent); `exit_rate_pct` (per cent); `exits` (count of businesses); `exits_cancellations` (count of businesses); `exits_other` (count of businesses); `fy` (financial year (YYYY-YY)); `name` (text); `start` (count of businesses).
- **`abs_cabee_latest.size_fy`** (28 rows). Businesses, entries and exits by employment size, FY2022-23 to FY2025-26 (8165.0 cube 1, Table 13). size_band: nonemp (non-employing), 1-4, 5-19, 20-199, 200+ employees, employing (all employing) or total. net_movement: businesses that changed size range while surviving.
  Columns: `end` (count of businesses); `entries` (count of businesses); `entries_births` (count of businesses); `entries_other` (count of businesses); `entry_rate_pct` (per cent); `exit_rate_pct` (per cent); `exits` (count of businesses); `exits_cancellations` (count of businesses); `exits_other` (count of businesses); `fy` (financial year (YYYY-YY)); `net_movement` (count of businesses); `size_band` (text: employment size range); `start` (count of businesses).
- **`abs_cabee_latest.survival`** (84 rows). Survival of businesses operating in June 2022, by ANZSIC division (8165.0 cube 1, Table 2): number still operating after 1 to 4 years and the survival rate as published.
  Columns: `anzsic` (code: ANZSIC 2006 division, UNKNOWN or TOT); `cohort` (text: month the cohort was operating); `operating_at_cohort` (count of businesses); `survival_rate_pct` (per cent); `survived` (count of businesses); `years` (years after the cohort month).

### `abs_io`: Australian National Accounts: Input-Output Tables (5209.0.55.001)

Australian Bureau of Statistics. Release: 2023-24 (2026-03-25; next release 2027-03-24). Licence: CC BY 4.0, Australian Bureau of Statistics.

- **`abs_io.industries`** (116 rows). Output and primary inputs by input-output industry group (IOIG), 2023-24 financial year (5209.0.55.001 Table 5, industry by industry flow table, direct allocation of competing imports; employment from Table 20). gva is value added at basic prices as published (= coe + gos_mi + other_taxes_on_production). TOT = total industry uses (employment summed over IOIGs). Weights for Layer B: wage bill coe/TOT.coe, value added gva/TOT.gva.
  Columns: `coe` (AUD million, basic prices); `competing_imports` (AUD million, basic prices); `complementary_imports` (AUD million, basic prices); `employed_fte` (thousand full-time equivalent persons); `employed_full_time` (thousand persons); `employed_part_time` (thousand persons); `gos_mi` (AUD million, basic prices); `gva` (AUD million, basic prices); `intermediate_use` (AUD million, basic prices); `ioig` (code: IOIG (4 digits) or TOT); `name` (text); `other_taxes_on_production` (AUD million, basic prices); `output` (AUD million, basic prices); `taxes_on_products` (AUD million, basic prices).
- **`abs_io.ioig_anzsic`** (510 rows). IOIG to ANZSIC 2006 class concordance as published by the ABS with the input-output methodology ('Industry and Product Concordance Tables', sheet 'IOIG(2022) to ANZSIC06'), one row per IOIG x class (basis 'published'). Where the tables publish an IOIG that the concordance splits (1205 'Wine, spirits and tobacco' in 2023-24, the concordance's 1203 and 1204), rows for it are added with a 'derived' basis, so every IOIG in the tables maps to classes. Class 6711 maps to two IOIGs (imputed and actual rent) in the published concordance.
  Columns: `anzsic` (code: ANZSIC 2006 class); `basis` (text: published, or derived (with the rule)); `ioig` (code: IOIG (4 digits)).

### `abs_eeh`: Employee Earnings and Hours, Australia (6306.0), Data Cube 6

Australian Bureau of Statistics. Release: may-2025 (2026-01-23). Licence: CC BY 4.0, Australian Bureau of Statistics.

- **`abs_eeh.by_employer_size`** (6 rows). Earnings and hours of full-time non-managerial employees paid at the adult rate, all ages, by employer size (number of employees), May 2025 (6306.0 Data Cube 6, Table 6). _se columns are the ABS's standard errors.
  Columns: `employees` (thousand employees); `employees_se` (thousand employees: standard error); `employer_size` (text: employees (<20, 20-49, 50-99, 100-999, 1000+, total)); `hourly_cash_earnings` (AUD per hour, before tax); `hourly_cash_earnings_se` (AUD per hour, before tax: standard error); `weekly_cash_earnings` (AUD per week, before tax); `weekly_cash_earnings_se` (AUD per week, before tax: standard error); `weekly_hours_paid` (hours per week); `weekly_hours_paid_se` (hours per week: standard error).
- **`abs_eeh.by_industry`** (19 rows). Earnings and hours of full-time non-managerial employees paid at the adult rate, all ages, by ANZSIC division, May 2025 (6306.0 Data Cube 6, Table 3). TOT = all industries. Division A is out of scope. _se columns are the ABS's standard errors.
  Columns: `anzsic` (code: ANZSIC 2006 division or TOT); `employees` (thousand employees); `employees_se` (thousand employees: standard error); `hourly_cash_earnings` (AUD per hour, before tax); `hourly_cash_earnings_se` (AUD per hour, before tax: standard error); `weekly_cash_earnings` (AUD per week, before tax); `weekly_cash_earnings_se` (AUD per week, before tax: standard error); `weekly_hours_paid` (hours per week); `weekly_hours_paid_se` (hours per week: standard error).

### `abs_bcs`: Characteristics of Australian Business, data cube 1

Australian Bureau of Statistics. Release: 2024-25 (2026-06-25). Licence: CC BY 4.0, Australian Bureau of Statistics.

- **`abs_bcs.barriers`** (105 rows). Barriers to general business activities or performance, 2024-25 financial year (BCS data cube 1, Table 6): per cent of businesses reporting each barrier, by innovation status, employment size (persons), ANZSIC division, state and location. Columns: economic_uncertainty = Uncertainty about economic conditions; supply_chain = Supply chain issues; lack_of_funds = Lack of access to additional funds; cost_of_inputs = Cost of inputs; accounts_receivable = Outstanding accounts receivable limiting cash flow; internet_access = Internet access issues; skills_within_business = Lack of skilled persons: within the business; skills_labour_market = Lack of skilled persons: within the labour market; skills_any = Lack of skilled persons: any lack of skilled persons; government_regulation = Government regulations and/or compliance; lack_of_demand = Lack of customer demand for goods or services; lower_margins = Lower profit margins to remain competitive; environmental = Environmental factors; other = Other factors; none = No hampering factors.
  Columns: `accounts_receivable` (per cent of businesses); `category` (code: employment size (persons), ANZSIC 2006 division, state or location); `cost_of_inputs` (per cent of businesses); `economic_uncertainty` (per cent of businesses); `environmental` (per cent of businesses); `government_regulation` (per cent of businesses); `group` (text: total, size, industry, state or location); `internet_access` (per cent of businesses); `lack_of_demand` (per cent of businesses); `lack_of_funds` (per cent of businesses); `lower_margins` (per cent of businesses); `none` (per cent of businesses); `other` (per cent of businesses); `population` (text: all, innovation_active or non_innovation_active); `skills_any` (per cent of businesses); `skills_labour_market` (per cent of businesses); `skills_within_business` (per cent of businesses); `supply_chain` (per cent of businesses).
- **`abs_bcs.competition`** (35 rows). Amount of competition experienced, 2024-25 financial year (BCS data cube 1, Table 7): per cent of businesses, by employment size (persons), ANZSIC division, state and location. Columns: no_effective_competition = None/captive market/no effective competition; one_or_two = One or two competitors; three_or_four = Three or four competitors; five_or_more = Five or more competitors.
  Columns: `category` (code: employment size (persons), ANZSIC 2006 division, state or location); `five_or_more` (per cent of businesses); `group` (text: total, size, industry, state or location); `no_effective_competition` (per cent of businesses); `one_or_two` (per cent of businesses); `population` (text: all, innovation_active or non_innovation_active); `three_or_four` (per cent of businesses).

### `abs_berd`: Research and Experimental Development, Businesses, Australia (8104.0)

Australian Bureau of Statistics. Release: 2023-24 (2025-08-22). Licence: CC BY 4.0, Australian Bureau of Statistics.

- **`abs_berd.subdivision_size`** (105 rows). Business expenditure on R&D by ANZSIC subdivision and employment size, 2023-24 financial year (8104.0 data cube 2, Table 1). level: subdivision, division (ABS total) or total. Size columns are persons employed; null = not published, so sizes need not add to rd_total.
  Columns: `anzsic` (code: ANZSIC 2006 subdivision, division or TOT); `level` (text); `rd_0_4` (AUD thousand, current prices); `rd_200_plus` (AUD thousand, current prices); `rd_20_199` (AUD thousand, current prices); `rd_5_19` (AUD thousand, current prices); `rd_total` (AUD thousand, current prices).

### `abs_osca`: OSCA - Occupation Standard Classification for Australia: category descriptions

Australian Bureau of Statistics. Release: 2024-version-1-0 (2024-12-06). Licence: CC BY 4.0, Australian Bureau of Statistics.

- **`abs_osca.groups`** (593 rows). OSCA 2024, Version 1.0 major, sub-major, minor and unit groups (category descriptions, Table 2).
  Columns: `code` (code: OSCA group (1 to 4 digits)); `level` (text); `title` (text).
- **`abs_osca.occupations`** (1156 rows). OSCA 2024, Version 1.0 occupations (six-digit identifiers) with their skill level and the 'Registration or Licensing' statement of the category descriptions (released 28 July 2025): 187 occupations where registration or licensing is required, 196 where it may be required, of 1156. No employment counts: the LFS codes occupation to ANZSCO, not OSCA.
  Columns: `licensing` (text: required, may be required, or null (no statement)); `licensing_note` (text: the statement where it adds to the flag, else null); `major_group` (code: OSCA major group (1 digit)); `osca` (code: OSCA occupation (6 digits)); `skill_level` (OSCA skill level (1 highest to 5)); `title` (text: principal title); `unit_group` (code: OSCA unit group (4 digits)).

### `oecd_pmr`: OECD Product Market Regulation indicators (PMR): Australia

OECD. Release: DSD_PMR@DF_PMR v1.4, 2018-2023, 94 observations (no release date stated). Licence: OECD terms and conditions; CC BY 4.0 is the OECD default for data published from 1 July 2024 (open-by-default policy, seen in search results only; oecd.org refused direct requests).

- **`oecd_pmr.indicators`** (88 rows). OECD Product Market Regulation indicators for Australia (economy-wide PMR, its components and the sector indicators), by PMR vintage. Scale 0-6, higher = more restrictive. E.g. measure PMR is the economy-wide indicator; SERVBARRIER barriers in service sectors; ADREG_BURDEN administrative and regulatory burden. Vintages 2018-2023.
  Columns: `label` (text); `measure` (code: OECD PMR measure); `value` (index, 0-6 scale (higher = more restrictive)); `year` (PMR vintage (year)).

### `oecd_stri`: OECD Services Trade Restrictiveness Index (STRI): Australia

OECD. Release: DSD_STRI@DF_STRI_MAIN v1.0, 2014-2025, 228 observations (no release date stated). Licence: OECD terms and conditions; CC BY 4.0 is the OECD default for data published from 1 July 2024 (open-by-default policy, seen in search results only; oecd.org refused direct requests).

- **`oecd_stri.sectors`** (228 rows). OECD Services Trade Restrictiveness Index (main STRI) for Australia by services sector. Index 0 (completely open to foreign services suppliers) to 1 (completely closed). Sector codes are the OECD's ISIC Rev. 4 based codes (e.g. H51 air transport, M691 legal, M692 accounting). Years 2014-2025.
  Columns: `label` (text); `sector` (code: OECD STRI sector (ISIC Rev. 4 based)); `value` (index, 0-1 (higher = more restrictive)); `year` (year).

### `oecd_fdi_rri`: OECD FDI Regulatory Restrictiveness Index (FDI RRI): Australia

OECD. Release: DSD_FDIRRI_SCORES@DF_FDIRRI_SCORES v2.0, 2018-2025, 2940 observations (no release date stated). Licence: OECD terms and conditions; CC BY 4.0 is the OECD default for data published from 1 July 2024 (open-by-default policy, seen in search results only; oecd.org refused direct requests).

- **`oecd_fdi_rri.restriction_types`** (30 rows). OECD FDI Regulatory Restrictiveness Index for Australia, all activities, by type of restriction: CLAS1_1 foreign equity limits, CLAS1_2 screening and approval, CLAS1_3 restrictions on key foreign personnel, _O other restrictions, _T total. Index 0 (open) to 1 (closed).
  Columns: `label` (text); `restriction` (code: OECD policy category); `value` (index, 0-1 (higher = more restrictive)); `year` (year).
- **`oecd_fdi_rri.sectors`** (588 rows). OECD FDI Regulatory Restrictiveness Index for Australia by sector (all types of restriction). Index 0 (open) to 1 (closed). Sector _T = all activities (the headline index). Years 2018-2025.
  Columns: `label` (text); `sector` (code: OECD FDI RRI activity); `value` (index, 0-1 (higher = more restrictive)); `year` (year).

### `abs_capex`: Private New Capital Expenditure and Expected Expenditure, Australia (5625.0)

Australian Bureau of Statistics. Release: jun-2026 (Data API CAPEX 1.0.0, to 2026-Q2) (2026-08-27; next release 2026-11-26). Licence: CC BY 4.0, Australian Bureau of Statistics.

- **`abs_capex.actual_fy`** (1035 rows). Actual private new capital expenditure by CAPEX industry and type of asset, FY2016-17 to FY2025-26: the sum of the four quarters of the original series (5625.0, ABS Data API CAPEX). asset: total, buildings_structures or equipment_plant_machinery. anzsic: the ANZSIC 2006 division or subdivision a CAPEX industry corresponds to (null for aggregates such as P95). flags: the ABS's quality flags on any of the quarters (x = an estimate has a relative standard error of 10% to 25%; z = over 50% (too unreliable for general use)).
  Columns: `anzsic` (code: ANZSIC 2006 division or subdivision, TOT, or null); `asset` (text: type of asset); `capex_current` (AUD million, current prices); `capex_cvm` (AUD million, chain volume measures (sum of quarters)); `flags` (text: ABS observation status codes, comma-separated, or null); `fy` (financial year (YYYY-YY)); `industry` (code: CAPEX industry (ABS codelist CL_CAP_ANZSIC06_NM)); `label` (text).

### `pc_national`: PC National CGE model results: National Competition Policy, modelling proposed reforms

Productivity Commission. Release: report released 2024-11-29; workbook VersionId 2honZkozE_IfFLvy71JB5tFXmQ4UGblu (2024-11-29). Licence: CC BY 4.0 (Productivity Commission copyright statement, https://www.pc.gov.au/copyright/); attribute 'Source: Productivity Commission'.

- **`pc_national.initial_gsp`** (115 rows). Initial gross state product by PC National industry (114 industries) and state, from the model database (2018-19). pcn_no 0 / TOTAL = all industries.
  Columns: `act` (AUD million, 2018-19); `name` (text); `nsw` (AUD million, 2018-19); `nt` (AUD million, 2018-19); `pcn_code` (code: PC National industry); `pcn_no` (PC National industry number (0 = total)); `qld` (AUD million, 2018-19); `sa` (AUD million, 2018-19); `tas` (AUD million, 2018-19); `total` (AUD million, 2018-19); `vic` (AUD million, 2018-19); `wa` (AUD million, 2018-19).
- **`pc_national.linearity`** (16 rows). PC National linearity tests: the scenario's shock scaled to 25, 50, 75 and 100 per cent. matches_main_tab: the 100 per cent row reproduces the scenario tab's real GDP (the B9 test tab's block headings name the other scenario than its row labels; rows follow the row labels).
  Columns: `cpi` (per cent change from the baseline (long run)); `matches_main_tab` (boolean); `national_net_revenue` (AUD million, 2023-24 (Australian Government net operating balance)); `real_gdp` (per cent change from the baseline (long run)); `scenario` (code: PC scenario code (from the row label)); `share_pct` (per cent of the original shock); `states_net_revenue` (AUD million, 2023-24 (states and territories net operating balance)); `tab` (text: workbook tab).
- **`pc_national.simulations`** (36 rows). PC National simulations for the NCP reform modelling, one row per results tab: the PC's scenario code and names, the sectors shocked, the scenario text (shocks, separated by ' | '), the variant (central, or a lower or higher bound test), and the published macroeconomic results and real GSP by state, as published. L1's real GSP block appears to be the L2 simulation's (AUST 0.386 against L1's real GDP of 0.192): do not use L1's state results. Column labels: real_gdp = Real GDP; real_consumption = Real consumption; real_investment = Real investment; real_government_consumption = Real government consumption; export_volumes = Export volumes; import_volumes = Import volumes; real_wages = Real wages; rate_of_return_on_capital = Rate of return on capital; employment = Employment; capital_stock = Capital stock; nominal_exchange_rate = Nominal exchange rate; gdp_deflator = GDP deflator; consumer_price_index = Consumer price index; export_price_index = Export price index; import_price_index = Import price index; terms_of_trade = Terms of trade; rental_price_of_capital = Rental price of capital; investment_price_index = Investment price index; government_price_index = Government price index; real_gsp_nsw = Real GSP, NSW; real_gsp_vic = Real GSP, VIC; real_gsp_qld = Real GSP, QLD; real_gsp_sa = Real GSP, SA; real_gsp_wa = Real GSP, WA; real_gsp_tas = Real GSP, TAS; real_gsp_nt = Real GSP, NT; real_gsp_act = Real GSP, ACT; real_gsp_aust = Real GSP, AUST; gsp_gap = real GSP (AUST) minus real GDP, derived (a large gap flags a tab to check; see L1).
  Columns: `capital_stock` (per cent change from the baseline (long run)); `code` (code: PC scenario code); `consumer_price_index` (per cent change from the baseline (long run)); `employment` (per cent change from the baseline (long run)); `export_price_index` (per cent change from the baseline (long run)); `export_volumes` (per cent change from the baseline (long run)); `gdp_deflator` (per cent change from the baseline (long run)); `government_price_index` (per cent change from the baseline (long run)); `gsp_gap` (percentage points, derived); `import_price_index` (per cent change from the baseline (long run)); `import_volumes` (per cent change from the baseline (long run)); `investment_price_index` (per cent change from the baseline (long run)); `long_name` (text); `nominal_exchange_rate` (per cent change from the baseline (long run)); `rate_of_return_on_capital` (per cent change from the baseline (long run)); `real_consumption` (per cent change from the baseline (long run)); `real_gdp` (per cent change from the baseline (long run)); `real_government_consumption` (per cent change from the baseline (long run)); `real_gsp_act` (per cent change from the baseline (long run)); `real_gsp_aust` (per cent change from the baseline (long run)); `real_gsp_nsw` (per cent change from the baseline (long run)); `real_gsp_nt` (per cent change from the baseline (long run)); `real_gsp_qld` (per cent change from the baseline (long run)); `real_gsp_sa` (per cent change from the baseline (long run)); `real_gsp_tas` (per cent change from the baseline (long run)); `real_gsp_vic` (per cent change from the baseline (long run)); `real_gsp_wa` (per cent change from the baseline (long run)); `real_investment` (per cent change from the baseline (long run)); `real_wages` (per cent change from the baseline (long run)); `rental_price_of_capital` (per cent change from the baseline (long run)); `scenario` (text: the shocks as described by the PC); `sectors` (text: PC National sectors shocked); `tab` (text: workbook tab); `terms_of_trade` (per cent change from the baseline (long run)); `title` (text); `variant` (text: central, lower or higher).

### `rba_hf2025`: Hambur and Freestone (2025), RBA RDP 2025-05: supplementary information (mark-ups and concentration)

Reserve Bank of Australia. Release: RDP 2025-05 supplementary zip (Last-Modified Tue, 12 Aug 2025 02:52:31 GMT) (no release date stated). Licence: CC BY 4.0 (RBA notice in the supplementary zip; Excluded Material excepted).

- **`rba_hf2025.concentration`** (278 rows). Industry concentration from BLADE, as used in Hambur and Freestone (2025), RBA RDP 2025-05 (supplementary 'Inputs/Industry cocnentrations.xlsx'): top-4, top-10 and top-20 firm shares, the top 5 per cent of firms' share and the Herfindahl index, computed within each industry and summarised for each ANZSIC division (and nationally, TOT) as the weighted average across industries (_weighted), the unweighted average (_mean) and the median (_median, null where not given); _industries: the number of industries summarised for that metric. Division HHIs are not published. fyear as labelled by the authors.
  Columns: `division` (code: ANZSIC 2006 division or TOT); `fyear` (year (authors' fyear)); `hhi_industries` (count of industries); `hhi_mean` (index (0-1)); `hhi_median` (index (0-1)); `hhi_weighted` (index (0-1)); `top10_industries` (count of industries); `top10_mean` (share (0-1)); `top10_median` (share (0-1)); `top10_weighted` (share (0-1)); `top20_industries` (count of industries); `top20_mean` (share (0-1)); `top20_median` (share (0-1)); `top20_weighted` (share (0-1)); `top4_industries` (count of industries); `top4_mean` (share (0-1)); `top4_median` (share (0-1)); `top4_weighted` (share (0-1)); `top5pc_industries` (count of industries); `top5pc_mean` (share (0-1)); `top5pc_median` (share (0-1)); `top5pc_weighted` (share (0-1)).
- **`rba_hf2025.markups`** (224 rows). Harmonic-mean firm mark-ups (price over marginal cost, De Loecker-Warzynski method) by ANZSIC division and for the aggregate (TOT), from BLADE, as used in Hambur and Freestone (2025), RBA RDP 2025-05 (supplementary 'Inputs/markups - harmonic.xls'). fyear as labelled by the authors.
  Columns: `division` (code: ANZSIC 2006 division or TOT); `fyear` (year (authors' fyear)); `markup` (ratio).

## Known limitations

- **Aggregation.** Everything here is published aggregate data. Firm-level mark-ups, productivity dispersion and frontier gaps cannot be estimated from it; the RBA mark-ups and concentration are the authors' BLADE-derived division summaries, 2004-2017 and 2002-2019.
- **Coverage differs by source.** Australian Industry covers selected industries (finance is subdivision 64 only; O, P and Q private sector only) and its size table excludes division K. EEH excludes division A. BCS excludes some divisions (O, P). CAPEX is private sector and excludes agriculture and public administration. MFP covers the 16 market-sector divisions. Each table's description states its coverage.
- **Vintages differ.** CABEE class × size is FY2024-25 (cube 2 of the Jul 2021-Jun 2025 release) while the division and size tables run to FY2025-26 (cube 1 of Jul 2022-Jun 2026), until the ABS adds cube 2 in December 2026. The I-O tables are 2023-24; ASNA is 2025-26; the PC National database is 2018-19.
- **Perturbed and confidential cells.** CABEE cells are perturbed by the ABS, so class rows summed to subdivisions and divisions differ slightly from published totals. Unpublished cells (BERD, MFP Table 12, BCS) are null; BERD size columns need not add to the total; check `components_not_published` before using an MFP productive capital stock row.
- **Approximations.** MFP productive capital stock by division is a sum of chain volume components (not strictly additive). CAPEX years are sums of four original-series quarters.
- **Classification mismatches.** The 2023-24 I-O tables publish IOIG 1205 "Wine, spirits and tobacco", which the concordance splits into 1203 and 1204; those classes are mapped to 1205 with a `derived` basis. Class 6711 maps to two IOIGs (imputed and actual rent).
- **Occupations.** OSCA has no employment counts. The Labour Force Survey's occupation tables (EQ08, EQ09) are coded to ANZSCO, not OSCA, and the LFS Detailed release ceased after March 2026; the ANZSCO-OSCA mapping is left as a limitation.
- **PC National workbook.** Values are as published. L1's real GSP block appears to come from the L2 simulation (AUST 0.386 against L1's real GDP of 0.192): `gsp_gap` flags it. In some tabs the industry contributions block does not line up with its headings (not extracted). The B9 linearity tab's block headings name the other scenario than its row labels; rows follow the row labels.
- **Release detection.** The OECD API states no release dates (`release_date` null); OSCA in-place revisions within a version are not detected; the PC and RBA files are versioned by their upload markers.
- **Licences.** ABS, PC and RBA: CC BY 4.0 (the RBA's notice in the zip excludes "Excluded Material"). OECD: CC BY 4.0 is the OECD's default for data published from 1 July 2024, but this could not be checked on oecd.org (HTTP 403 on 22 and 23 October 2026).

## Not built

Every source in the P2 brief is built (16). Not attempted in P2, and listed in the plan: ABS Labour Account hours (LP denominators), AWE and WPI by industry, ATO taxation statistics (turnover bands, cost of compliance tables), the input-output flow matrix (Leontief inverse for P4), and an ANZSCO to OSCA employment mapping.
