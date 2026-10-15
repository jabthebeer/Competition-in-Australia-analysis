# QAN (Qantas Airways Limited): annual-report extraction log

Agent run: 2026-10-05, start `Mon Oct  5 00:15:52 UTC 2026`, end `Mon Oct  5 00:22:30 UTC 2026` (approx.; all three reports in one session).
Fiscal year ends 30 June.

## Source and access checks

- Annual reports page: `https://investor.qantas.com/investors/?page=annual-reports` (static HTML; all PDF links present without JavaScript). It lists annual reports 2000 to 2026 (2001-2004 also have separate Financial Reports; 2005 onward the Annual Report contains the full financial statements).
- robots.txt:
  - `https://investor.qantas.com/robots.txt`: no robots.txt exists (request redirects to `/Error.html?aspxerrorpath=/robots.txt`, an HTML error page). No restrictions, so `robots_txt_ok = true`.
  - `https://www.qantas.com/robots.txt` (checked, though no files were downloaded from it): `User-agent: *` disallows only `/cis/`, `/cgi-bin/`, `/agentsPdf/`, `/static/`, `/hotels/...`, `/my-booking/`, `/book-flights/`, etc. Nothing relevant.
- Terms of use: the investor site footer links to the qantas.com Website Terms of Use (last updated 12 December 2023). They contain **no explicit prohibition on automated access or downloading** (no robot, spider or scraper clause). However, clause 2.2 says "You may use our websites only for your personal and non-commercial purposes", and clause 2.3 forbids copying, storing or distributing material "except to the extent permitted by relevant copyright legislation". Non-commercial research use with no redistribution (the PDFs are git-ignored) appears consistent with this, but **flag for the project lead**.
- Did not access asx.com.au, aggregators, EDGAR or Wayback.
- Requests: 1 homepage, 1 annual-reports page, 1 terms page, 3 robots.txt, 3 PDFs, each at least 1 s apart. UA `Mozilla/5.0 (X11; Linux x86_64) research-replication`.

## FY2005

- URL: https://investor.qantas.com/FormBuilder/_Resource/_module/doLLG5ufYkCyEPjF1tpgyw/file/annual-reports/2005AnnualReport.pdf
- Downloaded 2026-10-05T00:16:51Z, HTTP 200, 2,430,333 bytes, 128 pages, sha256 `eb936d8bf845603d9cada0b37a4d6e67eea4fd500a9385fa283251b525531e17`.
- Extraction approx. 00:17:40 to 00:19:10 UTC (JSON written 00:21:50). About 3.5 min including shared setup.
- Text-based PDF (Acrobat Distiller 2005); no scanned pages. PDF page = printed page + 2.
- Pages viewed: 67 (Statement of Financial Performance, printed 65), 68 (Statement of Financial Position, printed 66), 76-77 (Notes 2-3, printed 74-75), 43 (performance summary with FTE, printed 41), 110 (Note 34 geographic, printed 108).
- Basis: **AGAAP pre-IFRS** ("Statements of Financial Performance"). FY2006 report will restate FY2005 under AIFRS; an AIFRS transition note is in this report (pdf pp.117-120).
- Two column sets (Qantas Group consolidated, Qantas parent); Group 2005 column used.
- Presentation: by nature (manpower, fuel and oil, aircraft operating variable, D&A, etc.), plus some activity lines (selling and marketing, tours and travel, capacity hire). No cost of sales. Share of associates sits inside Expenditure; interest revenue is netted in "Net borrowing costs".
- Identity: 12,648.8 - 11,527.1 = EBIT 1,121.7 (matches printed); -211.5 + 117.0 = 1,027.2 = printed PBT. Difference 0.0.
- Employees: average FTE 35,520 (performance summary, outside the audited statements).
- Confidence: **high**.

## FY2015

- URL: https://investor.qantas.com/FormBuilder/_Resource/_module/doLLG5ufYkCyEPjF1tpgyw/file/annual-reports/2015_qantas_annual_report.pdf
- Downloaded 2026-10-05T00:16:56Z, HTTP 200, 10,280,162 bytes, 106 pages, sha256 `719a33e0ccb8c9b0c4ec37942e6d8b86983a597e736e1b78a110b534a4163dd1`.
- Extraction approx. 00:19:10 to 00:19:50 UTC. About 2 min.
- Text-based PDF (InDesign). PDF page = printed page + 1.
- Pages viewed: 51 (Consolidated Income Statement, printed 50), 53 (Consolidated Balance Sheet, printed 52), 61-62 (Note 3(F) geographic and Note 4 other revenue/expenditure, printed 60-61), 16 (FTE reduction narrative).
- Basis: AIFRS. Single "Revenue and other income" total, so other income cannot be separated. Expenses by nature. Separate impairment lines (CGU: nil in 2015; specific assets 28).
- Note 4 footnote: 2014 comparatives restated (reclassification); 2015 current-year figures used as reported.
- Identity: 15,816 - 14,768 + 90 - 349 = 789 = printed PBT. Difference 0.
- Employees: no group FTE/headcount printed in the Annual Report.
- Confidence: **high**.

## FY2024

- URL: https://investor.qantas.com/FormBuilder/_Resource/_module/doLLG5ufYkCyEPjF1tpgyw/file/annual-reports/2024-Annual-Report.pdf
- Downloaded 2026-10-05T00:17:17Z, HTTP 200, 9,970,989 bytes, 144 pages, sha256 `25209f6821cff582f11f6bf7c1036ea91b14460132a4455c31ccc139c7289327`.
- Extraction approx. 00:19:50 to 00:20:10 UTC (JSON written 00:21:50). About 2 min.
- Text-based PDF (Word 365). PDF page = printed page + 2.
- Pages viewed: 68 (Consolidated Income Statement, printed 66), 70 (Consolidated Balance Sheet, printed 68), 78 (Note 2(C) ROIC, printed 76), 79-80 (Notes 3-7, printed 77-78).
- Basis: AIFRS, with AASB 16 (right-of-use assets 1,315 shown outside PP&E). Single "Revenue and other income" total. Expenses by nature; the employee line is now "Salaries, wages and other benefits". "Net gain on disposal of assets" (18) appears as a negative item within Expenditure. Impairment is only in Note 7 (nil in 2024).
- Identity: 21,939 - 19,854 + 117 - 318 = 1,884 = printed PBT. Difference 0.
- Employees: no group FTE/headcount printed in the Annual Report.
- Confidence: **high**.

## Cross-year notes and scaling issues

- The Qantas archive is complete (2000-2026) on a single static page, with stable direct PDF links, so it is easy to automate. But file names are irregular (`2005AnnualReport.pdf`, `2015_qantas_annual_report.pdf`, `2018-Annual-Report-ASX.pdf`, `2024-Annual-Report.pdf`), and 2010-2018 also list "Annual Review" PDFs (summary documents without full financial statements) that must not be confused with the Annual Report. Links must be parsed from the page, not guessed.
- Airline by-nature presentation has no cost of sales or materials line. "Fuel" was mapped to `raw_materials_and_inventory` as the only consumables line. "Aircraft operating variable" (landing fees, maintenance, catering, handling) and "Other" are also largely intermediate inputs. A DEU-style COGS needs an explicit, uniform rule for by-nature filers (e.g. total expenditure less employee costs and D&A).
- Employee counts are not in the FY2015 or FY2024 annual reports. They would need another document (Annual Review, Sustainability Report, data book).
- Label drift across years ("Manpower and staff related" became "Salaries, wages and other benefits"; "Borrowing costs" became "Finance costs"), plus the AGAAP to AIFRS break in FY2005/06 and the AASB 16 break in FY2020.
- Terms of use limit use to "personal and non-commercial purposes" (see above). This needs a policy decision for a 200-firm run.
