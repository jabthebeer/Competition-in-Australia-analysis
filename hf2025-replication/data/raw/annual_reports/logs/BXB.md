# BXB: Brambles Limited (annual-report extraction pilot log)

Agent session start: 2026-10-05 00:15:52 UTC. End: 2026-10-05 00:20:30 UTC (about 5 min wall-clock for all three reports, including writing files).

## Site checks (shared)

- `https://www.brambles.com/robots.txt` (HTTP 200): `User-agent: *` / `Disallow:` (empty), so nothing is disallowed.
- Terms (`https://www.brambles.com/legal`): a standard copyright clause. Content may not be "reproduced ... distributed or transmitted" without consent, except as permitted under the Copyright Act 1968 (Cth). There is **no explicit prohibition on automated downloading**, so I proceeded. PDFs are stored locally only (git-ignored) and are not redistributed.
- Archive page: `https://www.brambles.com/annual-reports` (static HTML; PDF links are in the page source, no JavaScript needed). The listing goes back to **2007** only. `https://www.brambles.com/results-centre` also starts at FY2007.
- User agent: `Mozilla/5.0 (X11; Linux x86_64) research-replication`. Requests were spaced at 1 s or more. asx.com.au was not accessed.

## FY2005 (year ended 30 June 2005): NOT OBTAINED

- Start/end: 00:16:00 to 00:16:50 UTC.
- No FY2005 report is listed on /annual-reports or /results-centre.
- Two WebSearches (restricted to brambles.com and brambles.com.au) found no FY2005 PDF.
- One targeted HEAD request on the legacy URL pattern used for 2007 to 2010: `https://www.brambles.com/Content/cms/pdf/legacy/new/Annual%20Reports/2005/2005.pdf` returned **HTTP 404**.
- I used no other source, per protocol. The JSON has all fields null.
- Structure: in FY2005 Brambles was a DLC (Brambles Industries Limited on ASX, Brambles Industries plc on LSE), unified as Brambles Limited in December 2006. The combined DLC accounts would have been the target.
- Search results show a "Request an Annual Report" page (not fetched). Printed copies may be obtainable from the company, but not through an automated process.
- Confidence (that the report is not on the company site): high.

## FY2015 (year ended 30 June 2015): OBTAINED

- URL: https://www.brambles.com/Content/cms/pdf/ResultsCentre/2015_Full-Year_Results/Brambles_2015_Annual_Report_Final.pdf
- Downloaded 00:16:52 UTC; 96 pages; sha256 `36340105aa9bb1bab44eec2113a971a46f8d1171ad1ae0be5f6fdd508d0504a6`.
- Start/end: 00:16:52 to 00:18:10 UTC.
- Text-based PDF (not scanned). Pages were located with pdftotext and **visually confirmed** with Read: PDF pp. 5, 40, 42, 51, 52, 53.
- Income statement: PDF p40 (printed 38). Balance sheet: PDF p42 (printed 40). Note 4 segments: PDF pp. 51 and 52. Note 5 operating expenses: PDF p53.
- Presentation: a single "Operating expenses" line on the face, with a by-nature analysis in Note 5 (employment costs, transport, repairs, subcontractors, raw materials and consumables, occupancy, D&A, impairment, etc.). There is no cost of sales or gross profit. Classified as `by_nature`.
- Key values (US$M): Sales revenue 5,464.6; Other income 114.7; Operating expenses (4,641.6); Employment costs 892.8; Raw materials and consumables 447.7; D&A 549.0; PBT 826.6; NPAT 584.4; PPE 4,424.7; Total assets 7,594.6.
- Checks: the income-statement identity difference is 0.0 when the printed finance revenue (13.8) is included. Note 5 sums to 4,641.6, Note 5A sums to 892.8, and D&A components sum to 549.0, all exact.
- Difficulties: a discontinued-operations line ((1.1), Recall demerger) and reporting in USD. Employees are printed only as "more than 14,000". The 2014 segment comparatives were restated, which does not affect current-year values.
- Confidence: high.

## FY2024 (year ended 30 June 2024): OBTAINED

- URL: https://www.brambles.com/Content/cms/FY24-Results/pdf/Brambles_2024_Annual_Report.pdf
- Downloaded 00:16:55 UTC; 97 PDF pages (two-up spreads, printed pages 1 to about 190); sha256 `462ab56f700784d5f7a475ce021307a86f9a51f15c42dc55b9d2bcdeccce66e8`.
- Start/end: 00:18:10 to 00:18:52 UTC (then JSON writing).
- Text-based PDF. Pages **visually confirmed** with Read: PDF pp. 44, 45, 49, 50, 59, 91.
- Statement of comprehensive income: PDF p44 (printed 85). Balance sheet: PDF p45 (printed 86). Note 2 segments: PDF p49 (printed 94 and 95). Note 3 operating expenses: PDF p50 (printed 97). Note 15: PDF p59 (printed 114). Employees: PDF p91 (printed 178).
- Presentation: as in FY2015, a single "Operating expenses" line with a by-nature analysis in Note 3. Classified as `by_nature`.
- Key values (US$m): Sales revenue 6,545.4; Other income and other revenue 262.9; Operating expenses (5,540.3); Employment costs 1,108.1; D&A 802.0; PBT 1,126.3; NPAT 779.9; PPE 6,003.0 (plus right-of-use assets of 773.7 shown separately); Total assets 8,731.1; Employees 12,743.
- **Raw materials: null.** Note 3 has no separate raw materials line. The footnote says raw materials used for repairs are included in "Repairs and maintenance" (1,345.6). The by-nature materials series is therefore not consistent between FY2015 and FY2024.
- Checks: the identity difference is 0.0, including finance revenue 16.2 and the hyperinflation line (8.4). Note 3 sums to 5,540.3, D&A components sum to 802.0, and Note 15 intangibles sum to 235.3, all exact.
- Difficulties: the two-up spread layout means printed and PDF page numbers diverge. Goodwill is combined with intangibles on the balance sheet (Note 15 split recorded). 2023 comparatives were restated for hyperinflation, which does not affect current-year values.
- Confidence: high.

## Notes relevant to scaling

- The website archive covers only FY2007 onward, so the FY2004 to FY2006 years (the DLC era) are unavailable from the company site. This is likely a common pattern for mid-2000s reports.
- The "by_nature" classification rests on a note-level breakdown; the face of the statement shows a single aggregate "Operating expenses" line. Line items change across years (raw materials disappears), so mapping to COGS-like concepts needs firm-specific judgement.
- Brambles reports in USD and has major structural breaks (Recall demerger 2013, IFCO demerger 2019, AASB 16 in 2020).
