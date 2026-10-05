# TLS (Telstra) annual-report extraction log

Firm: Telstra Group Limited (ABN 56 650 620 303), listed parent since the 2022 restructure. Before that it was Telstra Corporation Limited (ABN 33 051 775 556). Fiscal year ends 30 June.
Agent session start: 2026-10-05T00:15:53Z (protocol read). Session end: 2026-10-05T00:23Z (approx.).

## Source, robots.txt and terms (shared by all three years)

- Archive page: https://www.telstra.com.au/aboutus/investors/reports. It is server-rendered HTML, and all PDF links appear in the static page, so WebSearch was not needed.
- robots.txt was fetched at 2026-10-05T00:15:56Z from both https://www.telstra.com.au/robots.txt and https://www.telstra.com/robots.txt; the two are identical.
  - `User-agent: *` disallows `/forms`, `/products/`, `/search`, `/aboutus/media/jump-page` and specific `/content/dam/tcom/personal/...` and `/business-enterprise/...` PDFs.
  - It does **not** disallow `/aboutus/investors/` or `/content/dam/tcom/about-us/investors/`, so the result is **OK**.
  - The file has a "Block AI bots" group (CCBot, Bytespider, Diffbot, etc., `Disallow: /`). Our UA `Mozilla/5.0 (X11; Linux x86_64) research-replication` is not in that list. Note for scale-up: a crawler identifying as an AI agent might be listed in future versions.
- Terms of use (https://www.telstra.com.au/terms-of-use, last updated 09 Nov 2023):
  - There is no explicit prohibition on robots, spiders, scraping or automated downloading, so per the protocol we proceeded.
  - The terms do say "You are authorised to view the Telstra websites and its contents using your web browser … You must not otherwise reproduce … except as permitted by statute or with our prior written consent". We relied on the research fair-dealing exception. The PDFs are kept local and git-ignored, and are not redistributed. Flag this for the PI.
- Requests: 1 archive page, 1 terms page, 2 robots.txt files, 4 PDFs, each at least 1 s apart. No crawling.

## FY2005 (year ended 30 June 2005), AGAAP pre-IFRS

- Start 2026-10-05T00:16:54Z (download); end about 2026-10-05T00:18:05Z, plus about 2 min of shared setup.
- On the company site, the FY2005 Annual Report exists **only as 7 separate section PDFs**: Company Overview, OFR, Directors/Management/Employees, Directors Report, Remuneration Report, Financial Statements, Other Information. There is also a separate "2005 Annual Review".
  - Main file: https://www.telstra.com.au/content/dam/tcom/about-us/investors/pdf%20C/fin-statements.pdf, saved as `TLS_FY2005_annual_report.pdf`. sha256 a03c6f7a38ca6042b99d523483e333b6d689295a0ad9bf90945a60d1ea22a858; 170 pages; printed pages 227 onward.
  - Employee numbers: https://www.telstra.com.au/content/dam/tcom/about-us/investors/pdf%20C/directors-mgt-emp-share.pdf, saved as `TLS_FY2005_annual_report_sec_directors_mgt_employees.pdf`. sha256 eea8a72051e8ad43968ddb6d686f125f249db6924ebaf0dcbbdb35a6bbad2e0c; 50 pages. Downloaded at 00:17:45Z.
- Text PDF (Acrobat Distiller 6), not scanned, so pdftotext works well.
- Income statement ("Statement of Financial Performance"): pdf 2, printed 228. Balance sheet: pdf 3. Notes 2 and 3: pdf 38–40. Geographic: pdf 53. All were viewed with Read.
- Expense presentation: **by nature**. Lines are Labour 3,693; Goods and services purchased 4,147; Other expenses 4,055; D&A 3,766.
  - Revenue: Sales revenue 22,161.
  - Other revenue: 496. Under AGAAP this includes gross asset-sale proceeds of 226; the book value of 215 sits in Other expenses.
- Difficulties:
  - **A US$m convenience column sits right next to the A$ 2005 column**, and the Telstra Entity (parent) columns are also on the page. The values recorded are from the Telstra Group A$ column.
  - No total for intangible assets. Two lines (goodwill 2,287; other 1,581) are recorded as components, not summed.
  - Goodwill was amortised (AGAAP).
- Identity: 22,161 + 496 − 11,895 + 9 − 3,766 + 103 − 839 = 6,269 = printed PBT. **Difference 0.**
- Confidence: **high**.

## FY2015 (year ended 30 June 2015), AIFRS

- Start 2026-10-05T00:18:06Z; end about 2026-10-05T00:19:00Z, plus extraction write-up.
- URL: https://www.telstra.com.au/content/dam/tcom/about-us/investors/pdf%20D/telstra-annual-report-2015.pdf (downloaded 00:16:51Z).
  - sha256 9a006d08493a9ecfdcef5bd033bcc9c752ca07ce1713c3138f6be461e164b5b3; 191 pages.
  - This is a single full annual report. An HTML "interactive" version on a third-party domain (interactiveinvestorreports.com) was linked but not used.
- Income statement: pdf 73, printed 71. Balance sheet: pdf 75. Note 5 geographic: pdf 99. Note 6 income: pdf 100. Note 7 expenses: pdf 101. Employees (OFR): pdf 26. All were viewed.
- Expense presentation: **by nature**. Labour 4,921; Goods and services purchased 6,847; Other expenses 4,113; D&A 3,983.
  - Revenue (excluding finance income): 26,023.
  - Note 7 discloses Cost of goods sold of 3,079 inside Goods and services purchased.
- Difficulties:
  - There is a discontinued operation: profit of 19 below continuing profit. Operating lines are continuing only.
  - Labour includes labour substitution (contractor) costs of 816 (OFR), so it is broader than employee benefits.
  - A Read call with `pages: "73,75"` returned only page 73; use ranges or single pages.
- Identity: 26,023 + 584 − 15,881 + 19 − 3,983 + 157 − 846 = 6,073 = printed PBT (continuing). **Difference 0.**
- Confidence: **high**.

## FY2024 (year ended 30 June 2024), AIFRS

- Start 2026-10-05T00:19:00Z; end about 2026-10-05T00:20:06Z, plus extraction write-up.
- URL: https://www.telstra.com.au/content/dam/tcom/about-us/investors/pdf-g/telstra-annual-report-2024.pdf (the "Pages" version; downloaded 00:16:49Z).
  - sha256 ce43cd8ead8a43135c3eb3b382ee6606f13f7158e150bac08e03bb8e7e55587e; 204 pages.
- Income statement: pdf 91, printed 89. Balance sheet: pdf 93–94. Note 2.2: pdf 106. Table D (geographic): pdf 110. Note 2.3: pdf 117. Employees (OFR): pdf 27. All were viewed.
- Expense presentation: **by nature**. Note 2.3 says this explicitly.
  - Lines: Labour 4,291; Goods and services purchased 8,441; Net impairment losses on financial assets 92; Other expenses 3,114; D&A 4,479 (includes right-of-use depreciation of 619).
  - Revenue (excluding finance income): 22,928.
  - Cost of goods sold 2,883 is disclosed inside Goods and services purchased.
- Difficulties:
  - pdftotext garbles the contents page (overlapping duplicated glyphs), but the statement pages are clean.
  - The site also offers a "spreads" PDF, which was not used.
  - The company name changed to Telstra Group Limited.
- Identity: 22,928 + 554 − 15,938 − 16 − 4,479 + 112 − 696 = 2,465 = printed PBT. **Difference 0.**
- Confidence: **high**.

## Notes for scale-up

- Telstra's archive is excellent: every year from 1998 to 2026 is on one static page, and robots.txt allows it.
- Pre-2007 reports are split into section PDFs. File names are inconsistent (`fin-statements.pdf`, `financial-statement.pdf`, `20f.sec.3.pdf`), so a scraper must map sections to years using the page's headings or aria-labels, not the file names.
- Some years publish both a "spreads" and a "pages" PDF. Prefer "pages".
- Telstra's statements are by nature in every pilot year. Cost of sales has to come from a note (COGS for goods sold only), so a DEU-style COGS needs a rule for by-nature firms, for example Goods and services purchased, or adding Labour and Other expenses as well.
