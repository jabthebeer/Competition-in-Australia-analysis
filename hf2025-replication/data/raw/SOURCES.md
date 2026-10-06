# Data and code sources

Untouched downloads go in this folder. `src/fetch_raw.py` downloads everything reproducibly. `MANIFEST.csv` records the URL, UTC access time, size and sha256 of every file actually used. Requests use a generic user agent with no personal information (DECISIONS D-013).

## Registered sources (status 2026-10-05)

| Source | Phase | Access route | Licence / terms | Local path | Status |
|---|---|---|---|---|---|
| H&F (2025) RDP 2025-05, PDF | 1 | User upload; rba.gov.au | CC BY 4.0 | `literature/rdp2025-05.pdf` (committed) | Obtained |
| H&F RDP 2025-05 supplementary information: model code (edited EMX MATLAB), input moments, Stata superelasticity code | 1 | `https://www.rba.gov.au/publications/rdp/2025/2025-05/rdp-2025-05-supplementary-information.zip` | RBA, CC BY 4.0 (EMX-derived code is CC0) | `hf2025_supplementary/` | Obtained |
| EMX (2023) replication package | 1 | Harvard Dataverse doi:10.7910/DVN/GVLDPZ (API) | CC0 1.0 | `emx2023_replication/` | Obtained |
| EMX (2023) *JPE* paper | 1 | chrisedmond.net | Copyright UChicago Press; read-only | `literature/emx2023_jpe.pdf` (git-ignored) | Obtained |
| Champion, Edmond & Hambur (2025) | 3 | chrisedmond.net | Copyright authors; read-only | `literature/champion_edmond_hambur_2025.pdf` (git-ignored) | Obtained |
| ABS *Australian Industry* (8155.0), all industries and years | 3 | ABS Data API `ABS,AUSTRALIAN_INDUSTRY,1.1.0` | CC BY 4.0 | `abs/AUSTRALIAN_INDUSTRY.csv` | Obtained |
| ABS national accounts key aggregates (5206.0) | 4 | ABS Data API `ABS,ANA_AGG,1.0.0` | CC BY 4.0 | `abs/ANA_AGG.csv` | Obtained |
| ABS estimated resident population, Australia, quarterly (3101.0) | 4 | ABS Data API `ABS,ERP_Q,1.0.0`, key `1.3.TOT.AUS.Q` | CC BY 4.0 | `abs/ERP_Q_AUS_persons_total.csv` | Obtained |
| ATO Corporate Tax Transparency, entity tax information, 2013–14 to 2024–25 | 3 | data.gov.au CKAN API, package `corporate-transparency` | CC BY 3.0 AU | `ato_ctt/` | Obtained |
| ABS *Counts of Australian Businesses* (8165.0) | 3 | abs.gov.au release spreadsheets (not in the Data API) | CC BY 4.0 | | To do (Phase 3) |
| ABS *Estimates of Industry Multifactor Productivity* (5260.0.55.002) | 3 | abs.gov.au release spreadsheets. The 2024 vintage is also inside the H&F zip | CC BY 4.0 | | To do (Phase 3) |
| e61: Andrews, Dwyer & Triggs (2023); Hambur (2023) Treasury WP version; PC competition work | 3 | e61.in, treasury.gov.au, pc.gov.au | Check on download | | To do (Phase 3) |
| Listed-company annual reports (pilot: WES, WOW, TLS, QAN, BXB, BSL) | 3 | Company websites only. **Never asx.com.au**: its terms ban automated access | Company copyright; each site's terms checked (see `annual_reports/logs/`) | `annual_reports/` (PDFs git-ignored) | Pilot done. See `notes/annual_report_pilot_results.md`. WOW withheld (D-011) |

## Hosts confirmed reachable from this environment (2026-10-05)

- rba.gov.au, chrisedmond.net, dataverse.harvard.edu, abs.gov.au, data.api.abs.gov.au, data.gov.au, treasury.gov.au, pc.gov.au, e61.in, pypi.org, archive.ubuntu.com, and the company websites used in the pilot.
- Not reachable or not usable:
  - web.archive.org: blocked;
  - sec.gov: 403, and it requires a contact e-mail in the user agent, which we do not send;
  - bhp.com: 403, bot protection;
  - csl.com: 429, rate-limited.
