# Data and document sources

**Rules for this file:**

- Every external document or dataset the tool relies on is recorded here, with its URL, release and access date.
- No data is bundled unless it is listed here.
- No figures are invented: illustrative inputs in tests and examples are labelled as such.

## Framework documents (the specification and its context)

| Document | Publisher | Release | URL | Accessed | SHA-256 |
|---|---|---|---|---|---|
| Regulatory Burden Measurement Framework (PDF, 15 pp.), **the spec** | OIA, PM&C | July 2026 (OIA page dated 1 Jul 2026; PDF created 26 Jun 2026) | <https://oia.pmc.gov.au/sites/default/files/2026-06/regulatory-burden-measurement-framework.pdf> (landing page: <https://oia.pmc.gov.au/resources/regulatory-burden-measurement-framework>) | 6 Oct 2026 | `646848f921eff3a80f6366f1eb03dec61254a3a6f0190877f19e51f640c74ac8` (identical to the copy supplied with the project brief) |
| Regulatory Burden Estimate calculator (xlsx), "Version July 2026" | OIA, PM&C | 1 Jul 2026 | <https://oia.pmc.gov.au/sites/default/files/2026-06/regulatory-burden-estimate-calculator.xlsx> | 6 Oct 2026 | `6bc19cb667a2229a3c770143d643f9ac2d62ad459aa8ab95a18c4ed6efdc8af7` |
| Australian Government Impact Analysis Framework: Practical Guide for Agencies (PDF, 25 pp.) | OIA, PM&C | 1 Jul 2026 | <https://oia.pmc.gov.au/sites/default/files/2026-06/impact-analysis-practical-guide.pdf> | 6 Oct 2026 | `7b3f3801e1385c3cd0f7041b4f915ad21f6072d6e618eec1eb794973dddef67e` |
| Dashboard Impact Analysis template (dotx) | OIA, PM&C | 1 Jul 2026 | <https://oia.pmc.gov.au/sites/default/files/2026-06/dashboard-impact-analysis-template.dotx> | 6 Oct 2026 | `21bcb343c02c0a8378e5d1d1fd37af91cb5dad1ac606c634badb7ea171eeaf76` |
| Preliminary Analysis checklist (docx) | OIA, PM&C | 1 Jul 2026 | <https://oia.pmc.gov.au/sites/default/files/2026-06/preliminary-analysis-checklist.docx> | 6 Oct 2026 | `495518732a0d1ab2a8339681144248f785f72115a0407ce0b1f1635c1934661e` |
| Cost Benefit Analysis guidance note (consulted for the scope-expansion note: 7% real discount rate, 3% and 10% sensitivity) | OIA, PM&C | 3 Aug 2023 (still listed; OIA notes references to the previous IA framework are out of date) | <https://oia.pmc.gov.au/resources/cost-benefit-analysis> | 6 Oct 2026 | not stored |
| *How to consider competition in impact analysis* (supplementary guidance, PDF, 13 pp.), consulted for the econometric foundation scoping note: three "competition tests"; compliance costs estimated under the RBM can describe a barrier to entry | OIA, PM&C | July 2026 (page dated 1 Jul 2026) | <https://oia.pmc.gov.au/sites/default/files/2026-06/competition-guidance.pdf> (landing page: <https://oia.pmc.gov.au/resources/guidance-assessing-impacts/impacts-competition>) | 14 Oct 2026 | `8408469f1c9de92a472f33cf74e264bc50f05822dc1145696f389676b5888678` |

These documents are **not** committed to this public repository (see `docs/phase0_proposal.md` F-06). Check them by hash against the URLs above.

## Data used for identifiers (not bundled)

| Dataset | Publisher | Release | URL | Accessed | Used for |
|---|---|---|---|---|---|
| Counts of Australian Businesses, including Entries and Exits, July 2022 – June 2026 | ABS | 18 Aug 2026 (next release 18 Dec 2026) | <https://www.abs.gov.au/statistics/economy/business-indicators/counts-australian-businesses-including-entries-and-exits/latest-release> | 6 Oct 2026 | Employment-size bands (non-employing, 1–4, 5–19, 20–199, 200+) in `parameters.ts`, so tidy exports merge with ABS data. No figures are bundled. |
| ANZSIC 2006 (Australian and New Zealand Standard Industrial Classification) | ABS | 2006 (rev. 2.0) | <https://www.abs.gov.au/statistics/classifications/australian-and-new-zealand-standard-industrial-classification-anzsic> | not downloaded | Format of the optional `industry` code (division letter or 2–4 digit code) |

## Used by the productivity and competition costing (policy brief, P0)

| Document or dataset | Publisher | Release | URL | Accessed | Used for |
|---|---|---|---|---|---|
| OSCA – Occupation Standard Classification for Australia, 2024, Version 1.0: Category descriptions (xlsx; Table 1 lists 1,156 occupations, each with a six-digit identifier and a "Registration or Licensing" column) | ABS | 2024 v1.0 | <https://www.abs.gov.au/statistics/classifications/osca-occupation-standard-classification-australia/2024-version-1-0/data-downloads/OSCA%20Category%20Descriptions.xlsx> | 22 Oct 2026 (SHA-256 `4412b0a20a54ab7bab01063b83bec4ee0a29768204f84a36851d82b661238fe8`) | The six-digit code rule for licensed occupations in the brief schema, and the code in the synthetic test brief (381231, Electrician (General)). Not bundled |
| ANZSIC 2006 codelist `CL_ANZSIC_2006` 1.1.0 | ABS (Data API) | 1.1.0 | <https://data.api.abs.gov.au/rest/codelist/ABS/CL_ANZSIC_2006/1.1.0> (copy in `alicia/src/alicia/data/anzsic2006.json`, CC BY 4.0) | 14 Oct 2026 | Subdivision ranges of each division in `src/productivity/anzsic.ts`, checked against the bundled copy by test T-BRF-14 |
| Copyright statement | Productivity Commission | — | <https://www.pc.gov.au/copyright/> | 22 Oct 2026 | Licence of the PC National results workbook (CC BY 4.0), to be used for calibration in P4 |

## Real policies in the bundled examples (P6)

The figures in `examples/noncompete-ban.brief.json` come from these documents; each value's page is recorded in the brief's provenance. The documents are not committed: check them by hash.

| Document | Publisher | Release | URL | Accessed | SHA-256 | Used for |
|---|---|---|---|---|---|---|
| Impact Analysis: Non-compete clauses and other worker restraints (PDF, 96 pp.) | Treasury, published by the OIA | 21 Sep 2026 (announced 7 Sep 2026) | <https://oia.pmc.gov.au/sites/default/files/posts/2026/09/Impact%20Analysis.pdf> (landing page: <https://oia.pmc.gov.au/published-impact-analyses-and-reports/non-compete-clauses-and-other-worker-restraints>) | 25 Oct 2026 | `ad3f04f5fd2d547d948e6fa2ead7673a56f5971b6944a46d840ee5a4161bcab3` | The costing example: Options 2 and 3, the RBE inputs (Tables 4–6, pp. 51–53), timing (pp. 28, 50), Option 2's share of a full ban's mobility gain (p. 41), the competition screen notes (pp. 27, 41, 48–49, 62) |
| IA Summary for the same (PDF, 1 p.) | Treasury, published by the OIA | 21 Sep 2026 | <https://oia.pmc.gov.au/sites/default/files/posts/2026/09/IA%20Summary.pdf> | 25 Oct 2026 | `e451baea2aafefe41c1905d10ffbf985275364adca93e06da700dedaddc048fd` | The example's summary: prospective from 2027, $46.4 million familiarisation cost, the PC's $5.1 billion |
| National Competition Policy: modelling proposed reforms (study report with appendices) | Productivity Commission | 1 Nov 2024 (released 29 Nov 2024) | <https://assets.pc.gov.au/2025-10/competition-analysis-study-report-plus.pdf> | 25 Oct 2026 | `de1c726ffa1fcf59fb23cebd442648a6a87e5e465b219ba30e7b36f35900f918` | Already the source of the C8 evidence entries; p. 128 (PDF p. 134): automatic mutual recognition is outside the PC's licensing simulation |

## Data behind the default parameters (as cited by the RBM, not downloaded)

| Parameter | Value | Source as cited in RBM Appendix 2 | Next update |
|---|---|---|---|
| Work-related base hourly rate | $52.31 | ABS *Employee Earnings and Hours, Australia*, released January 2024, Data Cube 6 (full-time non-managerial employees paid at the adult rate); ATO Simple Tax Calculator, 2024–25 rates (RBM p. 12, fn 3–4) | Feb 2028 (unconfirmed, RBM p. 12, fn 2) |
| On-cost and overhead multiplier | 1.75 | RBM p. 12 | as above |
| Default work-related rate | $91.54 | RBM p. 12 (52.31 × 1.75, published to the cent) | as above |
| Default non-work (leisure) rate | $41 | RBM p. 13, fn 5 (Australian residents only) | as above |

## To be obtained in later phases

| Item | Phase | Status |
|---|---|---|
| ABS business size definitions (employment bands) for default cohorts | 3 | Bands taken from the ABS release above; the small/medium/large grouping (< 20, 20–199, 200+) follows conventional ABS usage and should be re-checked in Phase 3 |
| 3–5 published Impact Analyses with reproducible RBE costings (≥2 reforms; ≥1 with transition or start-up costs) | 5 | Not yet searched; OIA site is reachable from the build environment |
| ABS *Counts of Australian Businesses* | Future expansion | Out of scope for this project |
