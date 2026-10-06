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

These documents are **not** committed to this public repository (see `docs/phase0_proposal.md` F-06). Check them by hash against the URLs above.

## Data used for identifiers (not bundled)

| Dataset | Publisher | Release | URL | Accessed | Used for |
|---|---|---|---|---|---|
| Counts of Australian Businesses, including Entries and Exits, July 2022 – June 2026 | ABS | 18 Aug 2026 (next release 18 Dec 2026) | <https://www.abs.gov.au/statistics/economy/business-indicators/counts-australian-businesses-including-entries-and-exits/latest-release> | 6 Oct 2026 | Employment-size bands (non-employing, 1–4, 5–19, 20–199, 200+) in `parameters.ts`, so tidy exports merge with ABS data. No figures are bundled. |
| ANZSIC 2006 (Australian and New Zealand Standard Industrial Classification) | ABS | 2006 (rev. 2.0) | <https://www.abs.gov.au/statistics/classifications/australian-and-new-zealand-standard-industrial-classification-anzsic> | not downloaded | Format of the optional `industry` code (division letter or 2–4 digit code) |

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
