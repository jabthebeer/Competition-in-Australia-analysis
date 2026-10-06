# BSL (BlueScope Steel Limited): annual-report extraction log

Agent session start: 2026-10-05T00:15:52Z. End: 2026-10-05T00:23Z (about 7 minutes of wall-clock time for all three reports, including the shared URL discovery). Minutes per report in the JSON (`minutes_spent` = 4) are that total split across the three reports, rounded up.

## Source discovery and robots.txt (shared)

- `https://www.bluescope.com/robots.txt` fetched at 00:15:56Z (HTTP 200). `User-agent: *` disallows `/content/forms/`, `/etc/`, `/libs/`, `/bin/`, `/system/`, `/crx/`, `/apps/`, `/var/`, `/tmp/`, `/*filter?*`, `/*.html?*`, `/*.json`, `/*.xml`, `/*.js`, `/*.css`. The target path `/content/dam/bluescope/corporate/bluescope-com/investor/documents/*.pdf` is **not disallowed**, so robots_txt_ok = true.
- Terms of use: I found no explicit prohibition on automated downloading (not searched exhaustively).
- `https://www.bluescope.com/investors/annual-reports` redirects to `/investors/results-presentations/annual-reports`, fetched once. The year filter (2002 to 2026) is in the static HTML, but the document list is loaded by JavaScript, probably from a `.json` endpoint, which robots.txt disallows. I did not fetch any JS or JSON. `/investors/results-presentations/results-archive` (one fetch) is also JavaScript-rendered.
- WebSearch (restricted to bluescope.com) returned the FY2024 PDF URL directly. It did not index the FY2005 or FY2015 annual-report PDFs. It did show the site's filename convention for other years, e.g. `2009_BlueScope_FY_Report_Annual_Report_Part_Two.pdf` and `2023_bluescope_fy_report_annual_report.pdf`.
- I sent HEAD requests, 1.2 s apart, for `2015_BlueScope_FY_Report_Annual_Report.pdf` and `2005_BlueScope_FY_Report_Annual_Report.pdf`. Both returned 200 with `application/pdf` (last-modified 2023-06-23, when the site was migrated). There was also one HEAD for `2009_..._Part_One.pdf` to test the convention; that file was not downloaded.
- User agent was `Mozilla/5.0 (X11; Linux x86_64) research-replication`, with at most one request per second. I did not access asx.com.au or any third-party site.

## FY2005

- URL: https://www.bluescope.com/content/dam/bluescope/corporate/bluescope-com/investor/documents/2005_BlueScope_FY_Report_Annual_Report.pdf
- Downloaded 2026-10-05T00:17:24Z: 84 pages, 2,119,363 bytes, sha256 `94fb174c914b1fe9a7bd17a68dd7ee314af01691ea6f339e7304edf687421e2e`.
- Extraction took about 00:17:30 to 00:19:00Z.
- The document is the 2004/05 Annual Report with a **concise financial report** (AASB 1039) on PDF pp. 64 to 79. It is AGAAP, the last pre-AIFRS year; the AIFRS transition disclosures are on pp. 71 to 73. The PDF has a text layer and no scanned pages.
- Statement of financial performance: PDF p64 (printed 62). It is **by nature**. Statement of financial position: PDF p66 (printed 64). Note 3 segments: p74. Note 4 revenue: p76. Employees ("17,500 employees", Chairman's Message): p10. I viewed each of these pages as an image to confirm the numbers.
- Key values ($M):
  - Revenue from ordinary activities: 7,981.6. Note 4 gives sales revenue 7,940.7 and other revenue 40.9.
  - Raw materials and consumables used: (3,296.8). Changes in inventories: +146.7.
  - Employee benefits expense: (1,347.0).
  - PBT: 1,354.1.
- Identity difference: **0.0**.
- Difficulties:
  - Concise report only, so there are no expense or employee notes and no geographic split (australian_revenue_share is null).
  - Under AGAAP, revenue includes other revenue, and the expenses include the "carrying amount of non-current assets sold".
  - The employee count is a rounded narrative figure.
  - Printed page numbers are the PDF index minus 2.
- Confidence: **high**.

## FY2015

- URL: https://www.bluescope.com/content/dam/bluescope/corporate/bluescope-com/investor/documents/2015_BlueScope_FY_Report_Annual_Report.pdf
- Downloaded 2026-10-05T00:17:26Z: 82 pages, 7,264,518 bytes, sha256 `570f9960a209a3367125b9e824d0b731005fa5fb6ffe1a6185459b9cc94b16bc`.
- Extraction took about 00:19:00 to 00:20:00Z.
- The document is the Annual Report with a **concise financial report** (AASB 1039, PDF pp. 49 to 72, its own pagination -1- to -25-). AIFRS.
- Statement of comprehensive income: PDF p50 (printed "-2-"). It is **by nature**. Statement of financial position: p52 ("-4-"). Note 4(c) geographic: p59. Notes 5 (revenue) and 6 (other income): p61. I viewed each of these pages as an image.
- Key values ($M):
  - Revenue from continuing operations: 8,540.1 (sales 8,520.7 plus other revenue 19.4).
  - Other income: 20.3.
  - Raw materials: (4,750.5). Changes in inventories: (86.9).
  - Employee benefits: (1,581.0).
  - PBT: 222.3.
  - Australia: 3,800.9 of 8,552.3 geographic total.
- Identity difference: **0.0**.
- Difficulties:
  - Concise report, so there is no headcount anywhere in the report (employees is null). I checked the image-only pages 4 and 79; they are section covers.
  - Pages 73 to 76 are **scanned images** (the audit report). No numbers were needed from them.
  - Discontinued operations are shown separately (profit 2.2, sales 31.6). The geographic total includes the discontinued sales and excludes other revenue.
  - The 2014 comparatives are restated; I used the 2015 column as originally reported.
- Confidence: **high**.

## FY2024

- URL: https://www.bluescope.com/content/dam/bluescope/corporate/bluescope-com/investor/documents/2024_Bluescope_full_year_annual_report.pdf (found directly via WebSearch).
- Downloaded 2026-10-05T00:17:27Z: 165 pages, 12,014,853 bytes, sha256 `2dd4c552f912660d2a0d6c85b3cf6746c7948fa14e736051771ac50e3c3966e4`. pdfinfo printed harmless "Syntax Error" warnings about metadata objects.
- Extraction took about 00:20:00 to 00:21:45Z.
- This is the full financial report, AIFRS. Printed page numbers equal the PDF index.
- Statement of comprehensive income: p73. The face has a single aggregated "Expenses" line (15,904.7). The **by-nature** breakdown is in Note 3.1 on p87, where expenses are printed as positive amounts. Balance sheet: p74. Note 1.3 geographic (donut-chart labels): p83. Note 2 revenue: p84. Note 2.1 disaggregation: p85. Employees ("16,500+ employees"): p8. I viewed each of these pages as an image.
- Key values ($M):
  - Revenue from continuing operations: 17,055.3 (sales 17,009.4 plus other 45.9). Interest revenue of 56.7 is shown below operating profit.
  - Other income: 117.3.
  - Raw materials and consumables used: 10,456.8. Changes in inventories: (78.7).
  - Employee benefits expense: 2,483.7.
  - Profit before financing and income tax expense (EBIT): 1,331.7.
  - PBT: 1,267.3.
  - Australia: 5,362.0 of 17,009.4.
- Identity difference: **0.0**. The Note 3.1 lines also sum exactly to the face total.
- Difficulties:
  - The sign convention differs between the face (brackets) and Note 3.1 (positive). Values are recorded as printed.
  - Note 1.3 and Note 2.1 differ by 0.1 for Asia (2,341.4 vs 2,341.5) and New Zealand (712.3 vs 712.2), a rounding inconsistency in the source.
  - The headcount is a lower bound ("16,500+").
- Confidence: **high**.

## Notes for scaling

- BlueScope's archive page is JavaScript-rendered, and its data endpoint (`*.json`) is disallowed by robots.txt. WebSearch indexes only some years' PDFs. Older years had to be found by guessing the filename convention and checking with HEAD requests. That works for this firm but will not generalise across ~200 firms.
- For roughly 2005 to 2015, BlueScope published **concise financial reports** in the annual report. These contain the face statements but omit most notes, including employee numbers and, in FY2005, the geographic split. The full financial reports were "available on request" and may or may not be on the website as separate files (e.g. `*_FY_Results_Statutory_Report.pdf` or `*_Directors_Report.pdf` exist for some years).
- Under AGAAP (FY2005), revenue definitions differ: other revenue and asset-sale proceeds sit inside "revenue from ordinary activities". A harmonised revenue series therefore needs the note-level sales revenue.
