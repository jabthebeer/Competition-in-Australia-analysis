# ALCIA data pipeline: feasibility of sources and what was built

Methods note, 18 October 2026. This note covers the sources the owner proposed for moving from "no detectable effect" towards causal estimates at any scale, plus sources added. It records what each can and cannot identify, what was built, and the checks run. Everything here was read from the files themselves on the access dates in [`data/SOURCES.md`](../data/SOURCES.md). The code is in `alcia/src/alcia/pipeline/`.

## 1. Feasibility by source

| Source | Feasible? | Industry detail | Geography | Time | What it adds for identification | Main limits |
|---|---|---|---|---|---|---|
| **ABS Retail Trade** (RT) | Yes, **built** | 15 retail subgroups (6 are single ANZSIC classes, e.g. 4123 liquor, 4512 takeaway) and 6 groups | State | Monthly turnover Apr 1982 to Jun 2025; quarterly volumes | Monthly outcome for retail reforms (trading hours, liquor, container deposits): event time in months, not years | The series ended with June 2025. Turnover is in current prices by subgroup; volumes only by group. A seasonally adjusted series exists only at group level |
| **ABS Labour Force** (EQ06) | Yes, **built** | ANZSIC **group** (industry of main job) | State | Quarterly (mid-quarter months), Nov 1984 to Feb 2026 | Employment **and hours actually worked** by group × state. This corrects the earlier note: hours *are* published at group × state level | Survey estimates: 38% of group × state cells in Feb 2026 are under 1,000 persons, so sampling error is large. Latest release on 18 Oct 2026 is March 2026 |
| **ABN Bulk Extract** | Yes, **built** | None in the source; inferred from names (§3) | Postcode (main business location) | Monthly from Jul 1999 (status-change dates) | Local exits (ABN cancellations) by postcode and month; entity type (company, trust, sole trader …) | Snapshot only. Cancellations exclude ABNs later reactivated, and include ATO bulk cancellations (e.g. 0.86m in 2015, 1.22m in 2024). "Active since" counts are survivors only, not entries. True flows need successive weekly extracts (`snapshot_summary` starts the archive) |
| **ASIC business names** | Yes, **built** | Inferred from the name | Postcode, via the ABN (90% of current names located) | Monthly registrations from Jun 2012 | Monthly entry proxy (new trading names) | Snapshot: names cancelled more than ~12 months ago are absent, so earlier registrations are survivors. **Cancelled names carry no ABN**, so cancellations are national only (Oct 2025 on) |
| **ASIC companies** | Yes, **built** | Inferred from the name (7% of companies) | Postcode, via the ABN (59% of companies located) | Monthly registrations from 1991 | Incorporations by month; proprietary vs public | Deregistrations only for about the last 12 months. Many companies hold no ABN (no location). Company names say less about industry than trading names |
| **Internet Vacancy Index** (JSA) | Parser only | ANZSCO occupation (not industry) | State; IVI regions | Monthly from 2006 | Labour demand for regulated occupations (licensing, mutual recognition) | **The JSA site could not be reached from this environment** (connection refused, 18 Oct 2026). `jsa_ivi.py` parses workbooks saved by hand to `data/raw/jsa_ivi/`. It is tested on a synthetic workbook only, so check it against published totals first. Occupations do not map to ANZSIC codes, so the coverage catalogue does not match it to records |
| CABEE, later releases (suggested) | Yes, **built** | ANZSIC class × size | State | FY2007-08 to **FY2024-25** (was to 2019-20) | Five more post-years for every reform. Five releases (Jul 2017–Jun 2021 to Jul 2021–Jun 2025) were added in their new xlsx layouts | Level break at the join: FY2019-20 end-year count is 2.42m in the 2016–20 release but 2.31m in the 2017–21 release, so use rates across it. From 2021-22 the 1-19 band is 1-4 + 5-19 (perturbed cells summed) |
| ABS Data by Region (suggested) | Yes, **built** | Division | SA2, LGA, state | Businesses 30 Jun 2021–2025; employee jobs (LEED) 2017-18 to 2022-23 | Local stocks and jobs for local designs, e.g. a lockout precinct vs the rest of the state | Division only; stocks, not flows; short series |
| City of Melbourne CLUE (suggested) | Yes, **built** | ANZSIC **class** | 13 CLUE small areas, one LGA | Annual 2002–2024 | Fine local panel for Melbourne/Victorian changes. Also a labelled set (trading name + class) to test the name classifier | One municipality. Establishments are premises, not firms. CLUE splits a few classes (mapped back to ANZSIC; 0000 "vacant" dropped) |
| ASGS 2021 correspondences (suggested) | Yes, **built** | — | Postcode → SA2/SA3/SA4/GCCSA/LGA | — | Moves postcode counts (ABN, ASIC) to statistical areas (`geo.apportion`) | Population weights stand in for business locations; 2,641 postcodes have shares (the ABN data have 3,996, as PO-box and business postcodes have none) |
| ATO taxation statistics (suggested) | Not built | Fine industry (ATO codes) | National | Annual | Profit margins and counts by fine industry (markup proxies) | National only; ATO industry codes need a concordance to ANZSIC |
| NSW FuelCheck; liquor licence registers (suggested) | Not built | — | Site level | Daily / snapshot | Prices and outlet counts for fuel and liquor reforms | Separate scrapers and terms per state |
| ABS Payroll Jobs | Not feasible | — | — | — | — | Discontinued |

## 2. How panels map to legislation

Every connector writes the same long format (`alcia/src/alcia/pipeline/schema.py`), one row per source × measure × industry × place × period:

- **Industry:** scheme (`ANZSIC06`, `ANZSIC06-inferred`, `ANZSCO`, `none`), level (class, group, subdivision, division, retail-group, total, occupation) and code.
- **Place:** level (AUS, STE, SA2, LGA, POA, CLUE_AREA, IVI_REGION …) and code.
- **Also:** breakdown (size band, entity type, company type), period type and start, value, vintage.

`alcia pipeline build [source …]` builds the panels in `data/processed/<source>/`. `alcia pipeline catalogue` summarises them in `data/processed/catalogue.json`. The catalogue matches each register record's ANZSIC codes and jurisdiction to the finest level each panel holds:

- the record's own code, then its ancestors (class → group → subdivision → division);
- retail groupings that contain it;
- finer codes that sum to it;
- an all-industry series.

The match also reports whether the record's state is covered and which finer areas exist in it. Run `alcia data <record-id>` for the full list. The menu explorer shows it per record under "Data that can measure it", with an "Outcome data: fine / local" filter.

Example: `nsw-lockout-2014` (classes 4520, 4530, 4511, 4512, 4123) now has 106 matches. These include:

- monthly takeaway turnover at class 4512 and liquor turnover at class 4123;
- quarterly employment and hours for group 451;
- CABEE entries and exits by class to 2024-25;
- inferred-industry ABN cancellations and business-name registrations by postcode;
- SA2/LGA business counts and jobs for division H.

## 3. Inferring industry from names

The ABN and ASIC registers have no industry field. `names.py` maps words in business names to an ANZSIC class, group or division, using 61 rules and 10 overrides. Override words that mark a name as a supplier, an association, a holding company or a consultancy send it to wholesale or leave it unclassified. Results are labelled `ANZSIC06-inferred` and never mixed with ABS codes.

**Validation:** City of Melbourne CLUE 2002–2024 gives 60,667 distinct trading-name × class pairs coded by CLUE staff. The names were split into two fixed halves by a hash of the name.

| Rules | Names tested | Coverage (share classified) | Precision (share classified correctly) |
|---|---|---|---|
| Version 1 (written before seeing CLUE) | 59,407 (all pairs, before CLUE's split codes were mapped back) | 17.2% | 69.1% |
| Version 2, tuning half (rules revised after reading its misclassified names) | 30,488 | 14.3% | 81.5% |
| **Version 2, held-out half** | 30,179 | **14.4%** | **81.3%** |

Precision varies by rule; the per-rule table is in `data/processed/clue_melbourne/classifier_validation.json`.

- **High:** legal 95%, architects 94%, pharmacies 92%, supermarkets 92%, hairdressing and beauty 90%, real estate 89%, cafes and restaurants 75%.
- **Low:** bakeries 28% (CLUE codes most as cafes or takeaway), clothing 60%, electrical 54%, "farm" names 0 of 22 (CBD head offices).

A central-city sample under-represents trades and farms, so precision for those rules elsewhere is unknown. Coverage in the registers is also partial: 7.8% of active ABNs, 18.8% of business names and 7.1% of companies get an inferred industry. Inferred-industry counts therefore measure **named** businesses in an industry. Use them as changes within industry × place over time, not as levels, and check that a reform does not change naming conventions.

## 4. What each source can support

- **Retail Trade (monthly, class or subgroup × state):** event studies at monthly frequency, with other states and unaffected retail subgroups as controls. This suits trading-hours, liquor and container-deposit changes. Assumption: parallel trends between treated and control subgroup × state series.
- **LFS (quarterly, group × state):** employment and hours for treated groups vs placebo groups and states. With small cells the minimum detectable effects are large, so pool groups or use state × group totals with many placebo groups.
- **ABN and ASIC (monthly, postcode):** local designs where a change applies to part of a state (lockout precincts, CBD trading zones, council-level rules). These compare treated postcodes or SA2s with similar untreated ones, by entity type. Exits (ABN cancellations) are complete for still-cancelled ABNs. Registrations are survivor-biased before the last year, so compare treated with control areas registered in the same months, where survivor bias is plausibly similar. Do not read the levels.
- **CABEE to FY2025:** five more post-years for the batch reforms, notably automatic mutual recognition (2021), and the 2022–23 container-deposit schemes. Use rates across the 2020/21 release join.
- **Data by Region and CLUE:** baselines for local treatment intensity (businesses and jobs by division in each SA2 or LGA). CLUE also gives annual class-level changes for Melbourne small areas.

Public data still cannot support firm-level markups or productivity. Those need BLADE or ATO microdata, which are not used here.

## 5. Registered analyses unchanged

The pre-registered evaluations (WA trading hours and the high-evaluability batch) read CABEE through `cabee.as_registered()`. This keeps releases up to Jul 2016–Jun 2020 and years up to 2019-20. It was checked that their input panels and overlap files are row-for-row identical to the committed versions they were run on (1,243,975 and 694,400 rows).

## 6. Not done

- IVI on real files (needs a manual download).
- Successive ABN weekly extracts (needed for true entry flows).
- CABEE SA2/LGA cubes after June 2013 (ASGS 2016 boundaries, then 2021). Businesses by division × SA2 for June 2009–2013 (ASGS 2011) are built (`abs_cabee_local`) and used in the Perth weeknight re-evaluation; those older cubes hold stocks only, not entries or exits.
- ATO industry statistics; FuelCheck; liquor licence registers.
