> Research note for [`forward_plan_policy_costing.md`](../../forward_plan_policy_costing.md), compiled on 22 October 2026 by a Claude Code research agent from the sources listed. Figures carry the agent's verification tags where given ([P] primary source read, [A] abstract or official summary, [S] secondary only, UNVERIFIED). Downloaded copies mentioned below were kept in a temporary session folder and are not committed. Nothing here is a default parameter until it passes the P3 evidence-library check.

# Public data sources for the policy-costing tool (checked 22 Oct 2026)

I checked every item below against the publisher's own page, file or SDMX API on 22 Oct 2026, unless it is marked **UNVERIFIED**. The downloads I used to check them are in a temporary session folder (not committed) (folders `pages/`, `abs/`, `oecd/`, `dl_*`). Nothing was added to the repo.

## Main findings

- **No ABS SDMX dataflow exists for**:
  - Industry MFP (5260.0.55.002);
  - the annual ASNA industry tables (capital stock, factor income);
  - Input-Output tables;
  - CABEE entries and exits;
  - EEH;
  - BERD.
  
  I checked all 1,229 ABS dataflow IDs. `ABS_ANA_MFP` does not exist. These sources are XLSX only.
- **ASNA 2025-26 is due 23 Oct 2026, tomorrow.** Industry MFP 2025-26 is due 19 Feb 2027.
- **The CABEE connector is one release behind.**
  - Jul 2022–Jun 2026 came out on 18 Aug 2026, but only as cube 1 (tables 1–16).
  - The ABS says cube 1 tables 17–20 and cubes 2–11 come in December. That includes cube 2 (class × state × size), which the connector uses. The next release is 18 Dec 2026.
- **The OIA labour rate is not based on AWOTE.**
  - The Regulatory Burden Measurement Framework (July 2026) uses $52.31/h × 1.75 = $91.54/h. A footnote sources the $52.31 to EEH released January 2024, Data Cube 6 (full-time non-managerial employees paid at the adult rate), with tax computed on the ATO Simple Tax Calculator at 2024-25 rates.
  - The next update is "scheduled for February 2028 … yet to be confirmed".
  - `regulatory-burden-tool/src/engine/parameters.ts` already holds these values.
- **The ABS stopped publishing I-O multipliers.** The 2023-24 methodology says the ABS "has not published I-O multipliers since the 1998-99 issue and does not plan to compile and reissue this table".
- **The PC no longer publishes effective rates of assistance (ERA).** TAR 2024-25 says "historical estimates of the effective rate of assistance (no longer published since TAR 2021–22)".
- **New burden-related sources found:**
  - ATO cost-of-compliance tables (COC 1–3) in Taxation Statistics 2023-24.
  - The BCS 2024-25 barrier "Government regulations and/or compliance", by size and industry.
  - The PC's estimate that Australian Government regulation costs about $115–160b a year in compliance and delay costs.
- **RBA RDP 2025-05 (Hambur & Freestone) supplementary zip** contains:
  - BLADE-derived markups by division, FY2004–2017;
  - concentration measures by division (top-4 share, HHI and others), 2002–2019.
  
  `hf2025-replication/` already holds this zip.

## Summary table

| # | Source | Use in tool | Granularity | Access | Pipeline status | Verified? |
|---|---|---|---|---|---|---|
| 1 | ABS Industry MFP 5260.0.55.002, 2024-25 | MFP/LP trends, capital deepening, income shares | 16 market-sector divisions (A–N, R, S) + aggregates | XLSX | New (2024 vintage inside the hf2025 H&F zip) | Yes; no SDMX |
| 2 | ABS ASNA 5204.0, 2024-25 | GVA, net capital stock, CoE, GOS by industry | 19 divisions (some sub-industries) | XLSX | New (pipeline has 5220.0 and quarterly `ANA_IND_GVA`) | Yes |
| 3 | ABS Australian Industry 8155.0, 2024-25 | Subdivision baseline: employment, wages, sales, IVA, OPBT; size splits | Subdivision; size × division | SDMX `AUSTRALIAN_INDUSTRY` 1.1.0 (no size) + XLSX | Listed "To do" in `data/SOURCES.md`; hf2025 has the API CSV | Yes |
| 4 | ABS I-O tables 5209.0.55.001, 2023-24 | Build own Leontief multipliers, cost pass-through | 115 IOIGs | XLSX | New | Yes |
| 5 | ABS CABEE 8165.0, Jul 2022–Jun 2026 | Business counts, entry and exit by industry × size | Division (cube 1); class × state × size (cube 2, Dec) | XLSX; division counts only in `ABS_REGIONAL_*` | In pipeline (to the 2021–25 release) | Yes |
| 6 | ABS Characteristics of Australian Business (BCS), 2024-25 | Regulation-as-barrier prevalence, innovation | Size (4 bands), division, state | XLSX (2024-25); SDMX `ABS_IT_BARRIER` (2018–2020 only) | New | Yes |
| 7 | ABS EEH 6306.0 (May 2025); AWE 6302.0 (May 2026); WPI | Labour rates by industry and employer size; indexation | Division/occupation/employer size; AWE division | EEH XLSX; SDMX `AWE` 1.0.0, `WPI` 1.2.0 | WPI in pipeline (totals only); EEH and AWE new | Yes |
| 8 | ABS Business Indicators 5676.0; CAPEX 5625.0 | Investment and profit baseline | Division (CAPEX: mining and manufacturing subdivisions) | SDMX `QBIS` 1.0.0; `CAPEX` 1.0.0, `CAPEX_EST` 1.0.0 | QBIS in pipeline; CAPEX new | Yes |
| 9 | ABS BLADE | Firm-level work (restricted) | Firm | DataLab only | Not usable | Note only |
| 10 | ABS BERD 8104.0, 2023-24 | R&D intensity by industry × size | Subdivision × employment size | XLSX | New | Yes |
| 11 | OECD PMR 2023, STRI 2025, FDI RRI 2025 | Regulatory stringency benchmarks | Economy-wide + sector | OECD SDMX | New (PMR listed as "To do") | Yes (values pulled) |
| 12 | OECD STAN 2025 edition; OECD Productivity Database (PDB) | International industry comparisons | ISIC Rev.4 | OECD SDMX | New | STAN yes; PDB query failed (HTTP 500) |
| 13 | RBA RDP 2025-05 supplementary; Chart Pack | Markup and concentration priors | Division, 2004–2017 / 2002–2019 | ZIP; PDF | Zip in hf2025; Chart Pack new | Yes |
| 14 | PC TAR 2024-25; Productivity Insights; dynamic-economy report | Assistance by industry; burden anchors | Industry groupings | XLSX/PDF | New | Yes (Pitch partly) |
| 15 | ATO Taxation Statistics 2023-24 (incl. COC tables); small business tax gap | Tax compliance time; company items by fine industry | Fine industry; entity type × turnover band | XLSX via data.gov.au | Listed "To do"; CTT in hf2025 | Data yes; tax gap UNVERIFIED |
| 16 | OIA Published Impact Analyses | Validation cases | Per proposal | HTML + PDF/DOCX; not machine-readable | Framework in hand; register new | Yes |
| 17 | ABS OSCA 2024 licensing flags; LFS EQ08/EQ09; JSA | Occupational licensing exposure | 6-digit occupation | XLSX | New | OSCA yes; JSA UNVERIFIED (unreachable) |
| 18 | ABR ABN Bulk Extract | Entity stock and cancellations | ABN | data.gov.au | In pipeline | Pipeline record |
| + | ABS Labour Account (`LABOUR_ACCT_Q` 1.1, `ABS_LABOUR_ACCT` 1.0.0) | Hours and jobs by subdivision (LP denominators) | Subdivision, quarterly to 2026-Q2 | SDMX | New | Yes |

**Licences.**
- ABS: CC BY 4.0 (ABS copyright page).
- RBA: CC BY 4.0 for "most other material" (RBA copyright page).
- OIA: CC BY 4.0 (OIA copyright page).
- PC: CC BY 4.0 (TAR 2024-25 copyright text).
- ATO files on data.gov.au: CC BY 2.5 AU (data.gov.au metadata).
- OECD: CC BY 4.0 is the default for content published from 1 Jul 2024, but specific datasets can carry other terms. I saw this only in search results, because oecd.org returned 403. Treat it as partly verified.

## Notes by source

**1. ABS Estimates of Industry Multifactor Productivity (5260.0.55.002)**
- **Latest release:** 2024-25, released 6 Feb 2026. Next release 19 Feb 2027. Annual.
- **Coverage:** 16 market-sector industries (A–N, R, S) and a 12-industry "selected industries" aggregate. Hours-worked and quality-adjusted (QALI) bases.
- **Files:**
  - `52600550021_2025.xlsx`: tables 1–19. MFP, LP, capital productivity, GVA, labour input, capital services, productive capital stock, rental prices, income shares (Table 14), and gross-output MFP with cost shares (Table 19).
  - `52600550022_2025.xlsx`: tables 20–26 (experimental). Growth accounting, including IT vs non-IT capital deepening (Table 20) and industry contributions of capital, hours and MFP (Table 25).
  - `52600550023_2025.xlsx`: tables 27–42, experimental state productivity.
- **Key figures, 2024-25:** market-sector MFP −0.5%, labour productivity −0.2% (hours basis). Two-period average income shares are labour 0.55 and capital 0.45 (Table 2).
- **Access:** no SDMX dataflow.
- **Use in tool:** baseline productivity growth by industry; capital and labour shares to turn cost shocks into TFP-equivalent losses; capital deepening.

**2. ABS Australian System of National Accounts (5204.0)**
- **Latest release:** 2024-25, released 24 Oct 2025. Next release 23 Oct 2026. Annual.
- **XLSX tables (prefix `.../australian-system-national-accounts/2024-25/`):**
  - `5204005_GVA_by_Industry.xlsx`;
  - `5204046_Factor_Income_By_Industry.xlsx` (CoE, GOS+GMI, total factor income);
  - `5204048_Comp_Employees_By_Industry.xlsx`;
  - `5204058_Capital_Stock_By_Industry.xlsx` (GFCF, net capital stock, CFC, capital services index, average age);
  - `5204063_Net_Capital_Stock_By_Industry.xlsx` (by asset);
  - `5204072_Unit_Labour_Costs.xlsx`.
- **Productive capital stock** is not in 5204 Table 58. It is in MFP Table 12.
- **SDMX:** `ANA_INC` is split by institutional sector, not by industry.
- **Use in tool:** capital-output ratios and factor shares by division.

**3. ABS Australian Industry (8155.0)**
- **Latest release:** 2024-25, released 19 Jun 2026. A wholesale and retail data cube was added on 18 Sep 2026. Annual.
- **Data cube `81550DO001_202425.xlsx`:**
  - Tables 1–4 by division and subdivision: employment, wages, sales, total income and expenses, OPBT, EBITDA, IVA.
  - Table 5: the same key items by employment range (0–4, 5–19, 20–199, 200+) × division.
- **Data cube `81550DO007_202425.xlsx`:** state × employment range.
- **SDMX:** `ABS,AUSTRALIAN_INDUSTRY,1.1.0`, 108 industry codes, to FY2025. The API has no size dimension.
- **Not included:** the number of businesses (use CABEE for counts). Finance is only subdivision 64; O, P and Q are private sector only.
- **Use in tool:** the core per-industry and per-size denominators, e.g. a burden as a share of IVA or OPBT.

**4. ABS Input-Output tables (5209.0.55.001)**
- **Latest release:** 2023-24, released 25 Mar 2026. Next release 24 Mar 2027.
- **Tables:**
  - Table 1: production by product × industry;
  - Tables 5–10: industry-by-industry flows and direct/total requirement coefficients;
  - Table 17: primary input content;
  - Table 20: employment by industry;
  - Tables 21–39: margins and taxes.
- **IOIGs:** 115 (I counted the industry rows of Table 8).
- **Multipliers:** discontinued, as quoted above. The tool must compute Leontief inverses itself.
- **Related:** Supply-Use tables come through SDMX `ABS_SU_TABLE_2024` 1.0.0 (to 2023-24). `ABS_SU_TABLE_2025` is defined but returned NoRecordsFound on 22 Oct 2026.
- **Use in tool:** input-cost pass-through along supply chains (use with care).

**5. ABS CABEE (8165.0)**
- **Latest release:** Jul 2022–Jun 2026, released 18 Aug 2026 (cube 1 tables 1–16 only). Next release 18 Dec 2026.
- **Cube 1 (`8165DC01.xlsx`):** division (Table 1); employment-size ranges (Tables 13–16); survival.
- **Key figures, 2025-26:** 2,814,778 businesses, 16.9% entry rate, 13.8% exit rate.
- **Access:** no CABEE dataflow. Division × SA2 counts only through `ABS_REGIONAL_*`.
- **Use in tool:** number of affected businesses by industry × size; churn baselines.

**6. ABS Characteristics of Australian Business (BCS)**
- **Latest release:** 2024-25, released 25 Jun 2026. The survey is now biennial and has merged the innovation and digital modules.
- **Key table:** `BCSDC01_2024–25.xlsx` Table 6, "Barriers to general business activities or performance". **"Government regulations and/or compliance":**

| Group | Share reporting the barrier |
|---|---|
| All businesses | 20.2% |
| 0–4 persons | 17.3% |
| 5–19 persons | 24.2% |
| 20–199 persons | 28.2% |
| 200+ persons | 29.1% |
| Agriculture (highest division) | 33.4% |
| Other services (lowest division) | 14.3% |

- **Other tables:** innovation (cubes 8–11, including barriers to innovation); competition faced (cube 1 Table 7).
- **SDMX:** `ABS_IT_BARRIER` 1.0.0 (measure 17 = government regulations; 2018–2020 only), `BCS_BUSINF` 2.0.0, `BCS_INN` 2.0.0.
- **Use in tool:** a prior for how burden incidence differs by size and industry, and a validation check.

**7. ABS earnings: EEH, AWE and WPI**
- **EEH 6306.0:**
  - Latest release May 2025, released 23 Jan 2026. Biennial; next release unknown.
  - Data Cube 6 `63060DO006_202505.xlsx` (full-time non-managerial adults) gives hourly earnings by industry and employer size.
  - Average hourly total cash earnings: $52.60 overall. By employer size: $43.00 (<20 employees), $46.80 (20–49), $49.90 (50–99), $53.90 (100–999), $59.60 (1,000+). These are before tax.
- **AWE 6302.0:**
  - Latest release May 2026, released 13 Aug 2026.
  - AWOTE (full-time adult ordinary time earnings, seasonally adjusted) is $2,083.70, up 3.7%.
  - SDMX: `ABS,AWE,1.0.0/3.1.3.7.TOT.20.AUS.S`, by division and sector.
- **WPI:**
  - Latest release June quarter 2026, released 19 Aug 2026. Next release 18 Nov 2026.
  - `WPI` 1.2.0 also has an industry dimension, which the pipeline does not yet pull.
- **Use in tool:** industry- and size-specific labour rates as an alternative to the OIA default; indexation.

**8. ABS Business Indicators and CAPEX**
- **QBIS:** June 2026, released 31 Aug 2026; next release 30 Nov 2026. Already in the pipeline.
- **CAPEX:** June 2026, released 27 Aug 2026; next release 26 Nov 2026.
  - SDMX `CAPEX` 1.0.0 (actual and expected, by asset type) and `CAPEX_EST` 1.0.0.
  - The June 2026 data cover mining and manufacturing subdivisions, divisions H, N, R, S, and P-coded aggregates.
- **Use in tool:** investment baselines for the regulation → investment channel.

**9. BLADE (restricted)**
- Covers all active businesses from 2001-02 to the present. Access is only through the ABS DataLab for authorised researchers.
- Public outputs exist only as published aggregates: the H&F zip (13) and the PC's BLADE code (14). It cannot be committed.

**10. ABS BERD (8104.0)**
- **Latest release:** 2023-24, released 22 Aug 2025. Next release unknown.
- **Key file:** `81040DO002_202324.xlsx`, BERD by ANZSIC subdivision × employment size. No dataflow.
- **Use in tool:** R&D or innovation channel by industry × size.

**11. OECD regulatory indicators**
- **PMR:** `OECD.ECO.GCRD,DSD_PMR@DF_PMR,1.4`, query `/AUS..`. Vintages 2018 and 2023, scale 0–6. Australia, 2023:

| Indicator | Score |
|---|---|
| PMR, economy-wide | 1.35 |
| Administrative and regulatory burden | 2.31 |
| Barriers to entry | 1.55 |
| Barriers in service sectors | 1.91 |
| Transport | 1.86 |
| Energy | 0.71 |
| Lawyers | 1.29 |
| Retail sales of medicines | 3.5 |

- **STRI:** `OECD.TAD.TPD,DSD_STRI@DF_STRI_MAIN,1.0`, query `/A.AUS.STRI......`. Annual to 2025, 19 sectors. Australia, 2025: air transport 0.333, courier 0.386, legal 0.165, accounting 0.212.
- **FDI RRI:** `OECD.DAF.INV,DSD_FDIRRI_SCORES@DF_FDIRRI_SCORES,2.0`. Australia total 0.244 in 2025.
- **Release dates:** UNVERIFIED, because oecd.org returned 403.
- **Use in tool:** sector stringency benchmarks and elasticities from the literature.

**12. OECD STAN and Productivity Database**
- **STAN:** `OECD.STI.PIE,DSD_STAN@DF_STAN_2025,1.0`. Australia data run to 2024 (VA, employment, CoE, GOS, capital stock).
- **PDB by industry:** `OECD.SDD.TPS,DSD_PDB@DF_PDB_ISIC4_I4,1.0` is in the dataflow list, but every data query returned HTTP 500. UNVERIFIED.

**13. RBA**
- **RDP 2025-05, Hambur & Freestone (August 2025):**
  - Supplementary zip: <https://www.rba.gov.au/publications/rdp/2025/2025-05/rdp-2025-05-supplementary-information.zip>.
  - `Inputs/markups - harmonic.xls`: aggregate and 15-division markups (DLW method), 2004–2017.
  - `Industry cocnentrations.xlsx` (filename as published): top-4/10/20 shares and HHI, national and by division, 2002–2019.
- **Hambur (2021):** Treasury working paper, 28 Jun 2021. It has PDF and DOCX only, no data, and its licence is not stated on the page.
- **Chart Pack:** PDF, released 30 Sep 2026. Low value for this tool.
- **Use in tool:** markup priors for the productivity-impact module.

**14. Productivity Commission**
- **TAR 2024-25:** released 20 Aug 2026. Appendix B XLSX gives budgetary assistance by industry grouping, 2024-25. ERA is no longer published.
- **Productivity Insights:** the latest is the September 2026 update. There is a dashboard; I did not check whether it offers a data download.
- **"Creating a more dynamic and resilient economy":** released 19 Dec 2025.
  - It recommends a $10b cut to compliance and delay costs by 2030.
  - It estimates Australian Government regulation costs about $115–160b a year in compliance and delay costs.
  - It puts housing regulation costs at about $28.6b a year.
  - Supporting files: chart-data XLSX; `resilient-economy-blade.zip` (R code only).
- **Productivity Pitch:** media release of 5 Dec 2024. Ideas are posted as individual pages on engage.pc.gov.au; no bulk download found (UNVERIFIED).

**15. ATO**
- **Taxation Statistics 2023-24:** data.gov.au package `taxation-statistics-2023-24`, created 21 Apr 2026.
  - Company Tables 4–5: items by fine industry; Table 5 covers 2009-10 to 2023-24.
  - Company Table 8: items by entity size.
  - **COC Table 1:** cost of taxation compliance by form type, 1998–99 to 2024–25.
  - **COC Table 2:** return-preparation time-box hours by entity type × lodgment method × business-income band. Example: companies lodging through agents with income of $1 to <$500k average 2.4 hours per form.
  - **COC Table 3:** FBT and BAS time-box data.
- **Small Business Benchmarks:** data.gov.au, to 2020-21.
- **Small business tax gap:** a search snippet gives a net 17.4% ($27.2b) for 2022-23, page updated 8 May 2026. UNVERIFIED: ato.gov.au returned 403 to every request.

**16. OIA Published Impact Analyses**
- URL: <https://oia.pmc.gov.au/published-impact-analyses-and-reports>, about 155 listing pages, with filters for assessment, category, document type and keyword.
- Burden estimates are only inside the attached PDF/DOCX files. I found no CSV or JSON export: `_format=json` returned 406 and `/export` returned 404.
- Annual compliance summaries (DOCX/PDF) are at `/summary-reports`.
- **Use in tool:** pick validation cases by hand (Phase 5).

**17. Occupational licensing**
- **ABS OSCA 2024 v1.0** (released 6 Dec 2024). `OSCA Category Descriptions.xlsx` (released 28 Jul 2025) has a "Registration or Licensing" column. Of 1,156 occupations, 187 are "is required" and 196 "may be required".
- **Employment by occupation:** combine OSCA with LFS EQ08 (occupation unit group × state) and EQ09 (division × occupation major group). The LFS Detailed release is marked "This release has ceased", with March 2026 the last edition.
- **ABS licence-holder counts:** none found. Qualifications and Work (ceased; 2022-23) has no licence items.
- **JSA:** the connection failed again. UNVERIFIED.

**18. ABR ABN Bulk Extract**
- Already in the pipeline (14 Oct 2026 extract, CC BY 3.0 AU).

## Not verified, or gaps

- OECD PDB data (HTTP 500).
- OECD release dates and licence text (oecd.org 403).
- ATO pages, including the tax gap (403).
- JSA (unreachable).
- Productivity Pitch bulk data.
- The Economic Record (2023) version of Hambur's paper (search result only).

Public data cannot support firm-level markups. Only the BLADE-derived division averages in the H&F zip exist.

## Sources

- ABS MFP: <https://www.abs.gov.au/statistics/industry/industry-overview/estimates-industry-multifactor-productivity/latest-release>
- ABS ASNA: <https://www.abs.gov.au/statistics/economy/national-accounts/australian-system-national-accounts/latest-release>
- ABS Australian Industry: <https://www.abs.gov.au/statistics/industry/industry-overview/australian-industry/latest-release>
- ABS I-O tables: <https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-input-output-tables/latest-release>; methodology: <https://www.abs.gov.au/methodologies/australian-national-accounts-input-output-tables-methodology/2023-24>
- ABS Supply Use tables: <https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-supply-use-tables/latest-release>
- ABS CABEE: <https://www.abs.gov.au/statistics/economy/business-indicators/counts-australian-businesses-including-entries-and-exits/latest-release>
- ABS BCS: <https://www.abs.gov.au/statistics/industry/technology-and-innovation/characteristics-australian-business/latest-release>
- ABS EEH: <https://www.abs.gov.au/statistics/labour/earnings-and-working-conditions/employee-earnings-and-hours-australia/latest-release>
- ABS AWE: <https://www.abs.gov.au/statistics/labour/earnings-and-working-conditions/average-weekly-earnings-australia/latest-release>
- ABS WPI: <https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/wage-price-index-australia/latest-release>
- ABS Business Indicators: <https://www.abs.gov.au/statistics/economy/business-indicators/business-indicators-australia/latest-release>
- ABS CAPEX: <https://www.abs.gov.au/statistics/economy/business-indicators/private-new-capital-expenditure-and-expected-expenditure-australia/latest-release>
- ABS BERD: <https://www.abs.gov.au/statistics/industry/technology-and-innovation/research-and-experimental-development-businesses-australia/latest-release>
- ABS BLADE: <https://www.abs.gov.au/statistics/data-integration/integrated-data/business-longitudinal-analysis-data-environment-blade>
- ABS OSCA: <https://www.abs.gov.au/statistics/classifications/osca-occupation-standard-classification-australia/2024-version-1-0/data-downloads>
- ABS LFS Detailed: <https://www.abs.gov.au/statistics/labour/employment-and-unemployment/labour-force-australia-detailed/latest-release>
- ABS Qualifications and Work: <https://www.abs.gov.au/statistics/people/education/qualifications-and-work/latest-release>
- ABS Data API dataflow list: <https://data.api.abs.gov.au/rest/dataflow/ABS?detail=allstubs>
- ABS licence: <https://www.abs.gov.au/website-privacy-copyright-and-disclaimer>
- OECD SDMX dataflow list: <https://sdmx.oecd.org/public/rest/dataflow/all/all/latest?detail=allstubs>
- OECD open-access policy (search result only): <https://www.oecd.org/en/about/oecd-open-by-default-policy.html>
- RBA RDP 2025-05: <https://www.rba.gov.au/publications/rdp/2025/2025-05.html>
- RBA Chart Pack: <https://www.rba.gov.au/chart-pack/>
- RBA licence: <https://www.rba.gov.au/copyright/>
- Treasury, Hambur (2021): <https://treasury.gov.au/publication/p2021-177591>
- PC TAR 2024-25: <https://www.pc.gov.au/ongoing/trade-assistance/2024-25>
- PC Productivity Insights: <https://www.pc.gov.au/ongoing/productivity-insights/>
- PC dynamic-economy report: <https://www.pc.gov.au/inquiries-and-research/resilient-economy/report/>
- PC Productivity Pitch: <https://www.pc.gov.au/inquiries-and-research/five-productivity-pillars/productivity-pitch-initiative/>
- ATO Taxation Statistics 2023-24: <https://data.gov.au/data/dataset/taxation-statistics-2023-24>
- ATO Small Business Benchmarks: <https://data.gov.au/data/dataset/small-business-benchmarks>
- ATO small business tax gap (UNVERIFIED, 403): <https://www.ato.gov.au/about-ato/research-and-statistics/in-detail/tax-gap/q-z-tax-gaps/small-business-income-tax-gap/latest-estimate-and-trends>
- OIA Regulatory Burden Measurement Framework: <https://oia.pmc.gov.au/resources/regulatory-burden-measurement-framework> (PDF: `/sites/default/files/2026-06/regulatory-burden-measurement-framework.pdf`)
- OIA Published Impact Analyses: <https://oia.pmc.gov.au/published-impact-analyses-and-reports>
- OIA summary reports: <https://oia.pmc.gov.au/summary-reports>
- OIA licence: <https://oia.pmc.gov.au/copyright-disclaimer>
- Repo files read: `data/SOURCES.md`, `regulatory-burden-tool/data/SOURCES.md`, `hf2025-replication/data/raw/SOURCES.md`
