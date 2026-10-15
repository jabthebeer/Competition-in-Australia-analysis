# WES (Wesfarmers Limited): annual-report extraction log

Agent session start 2026-10-05 00:15:52 UTC; end about 00:23 UTC (`date -u`). Fiscal year ends 30 June.

## Source discovery and permissions (shared by all three reports)

- robots.txt: `https://www.wesfarmers.com.au/robots.txt` was fetched at 00:15:56 UTC (HTTP 200). For `User-agent: *` it disallows only `/sitefinity`, `/logs`, `/flash`, `/sustainability-new` and `/temporary2023567`. The report PDFs are under `/docs/default-source/...`, which is **allowed**.
- Terms of use: `https://www.wesfarmers.com.au/terms-of-use` was fetched and searched. It covers copyright, images and liability, and contains **no prohibition on automated access or downloading**.
- Archive page: `https://www.wesfarmers.com.au/investor-centre/company-performance-news/reports`. It is a static HTML page that lists annual reports from 1999-2000 to 2026. JavaScript was not needed and WebSearch was not used. The first request was reset (curl error 35) and a retry 2 s later succeeded. `/investor-centre/company-performance-news/annual-reports` shows only the latest report.
- asx.com.au, aggregators, EDGAR and Wayback were not accessed. Requests were spaced at least 1 s apart, and only the 3 target PDFs plus 4 HTML/robots pages were requested.
- Note for the pilot: the scratchpad directory is shared between agents. An initial `reports.html` there belonged to another agent's firm (Woolworths). All WES temporary files were moved to `scratchpad/WES/`.

## FY2005 (year ended 30 June 2005)

- URL: https://www.wesfarmers.com.au/docs/default-source/reports/2004-2005-annual-report.pdf?sfvrsn=ff299fba_2
- File: `data/raw/annual_reports/pdfs/WES_FY2005_annual_report.pdf`. 120 pages, 4.3 MB. sha256 `0066518d2007ea8f9af3892cfc524188ba9abc591784921355fc06c8c98b92ad`. The PDF was re-assembled by pdftk in 2016 and has a text layer (not scanned).
- Timing: download 00:16:53 to 00:16:58 UTC. Extraction finished about 00:21 UTC, interleaved with the other years, so roughly 3 min.
- Basis: AGAAP (pre-IFRS). The income statement is the "Statement of financial performance" on PDF page 56 (printed p54), in $000.
- Expense presentation: **by function**. The face shows a single line, "Expenses from ordinary activities", and note 4 (PDF 69) splits it into Cost of goods sold, Distribution, Sales and marketing, Direct selling, Administration and Other.
- Key values ($000):

| Item | Value | Label | Location |
|---|---|---|---|
| Revenue | 8,190,389 | Revenues from ordinary activities | p56 |
| Cost of sales | 4,523,007 | Cost of goods sold | note 4, PDF 69 |
| PBT | 880,304 | | |
| Net profit attributable to members | 618,300 | | |
| Total assets | 7,314,348 | | |

- Employee benefits: the audited accounts **do not print** total employee expense. The figure recorded is $950m, "to employees as salaries, wages and other benefits", from the unaudited value-added table on PDF 7 (printed p5). It is in $m, not $000.
- Identity check: 8,190,389 − 7,156,621 − 90,430 (goodwill amortisation) − 102,837 + 39,803 = 880,304, which equals the printed PBT. **Difference 0.**
- Difficulties:
  - AGAAP revenue includes gross proceeds on asset sales, interest received and insurance premiums.
  - Goodwill is amortised and shown on its own line on the face.
  - Intangible assets include goodwill.
  - No consolidated EBIT is printed. The segment note shows EBIT *before corporate overheads*, and the financial summary shows "Net profit before interest and tax" of $949m on a different definition. EBIT was left null and both alternatives are described in a note.
  - There is no geographic revenue split.
  - The employee figure (30,000) is a rounded headcount.
  - The insurance segment's costs sit inside the functional expense lines.
- Pages viewed: 3, 7, 50, 56, 57, 66, 67, 68, 69, 78.
- Confidence: **high** for the statement figures. Medium for the employee-cost proxy.

## FY2015 (year ended 30 June 2015)

- URL: https://www.wesfarmers.com.au/docs/default-source/reports/2015-annual-report.pdf?sfvrsn=629d98ba_6
- File: `data/raw/annual_reports/pdfs/WES_FY2015_annual_report.pdf`. 144 pages, 8.5 MB. sha256 `ec29cc3230aa8c2a24f3e68fc436155cfe9d45e6197feedf86f12dc877d4be35`. Text layer present.
- Timing: download 00:18:10 to 00:18:14 UTC. Extraction finished about 00:21 UTC, roughly 2 min.
- Basis: AIFRS. The income statement is on PDF 90 (printed p88), in $m. The 2014 comparative column is labelled RESTATED; it was not used.
- Expense presentation: **by nature**.
- Key values ($m):

| Item | Value | Label |
|---|---|---|
| Revenue | 62,447 | |
| Raw materials and inventory | (43,045) | |
| Employee benefits expense | (8,198) | |
| EBIT | 3,759 | printed |
| Finance costs | (315) | |
| PBT | 3,444 | |
| NPAT | 2,440 | discontinued operations nil |

- Identity check: 62,447 − 59,100 + 330 + 82 − 315 = 3,444, which equals the printed PBT. **Difference 0.**
- Difficulties:
  - The balance sheet does not print a PP&E total, only Property 2,475 and Plant and equipment 7,730. The total of 10,205 is taken from note 7 on PDF 104.
  - Intangible assets of 4,601 exclude goodwill (14,708, shown separately).
  - Coles is still in the group (demerged in 2018).
  - Employees are about 205,000, a headcount that includes about 75,000 casuals.
  - The Australian share of revenue is 61,013 out of 62,447.
- Pages viewed: 56, 90, 91, 92, 97, 98, 99, 100, 104, 105.
- Confidence: **high**.

## FY2024 (year ended 30 June 2024)

- URL: https://www.wesfarmers.com.au/docs/default-source/asx-announcements/2024-annual-report-(including-appendix-4e).pdf?sfvrsn=1ab4e5bb_0. This is the annual report including Appendix 4E, hosted on wesfarmers.com.au.
- File: `data/raw/annual_reports/pdfs/WES_FY2024_annual_report.pdf`. 197 pages, 11.4 MB. sha256 `732227f8e85ff787e9c51fdcc0ab22fb10eb31395a6c715814f0292ee2a0b238`. Text layer present.
- Timing: download 00:19:00 to 00:19:05 UTC. Extraction finished about 00:21 UTC, roughly 2 min.
- Basis: AIFRS (AASB 16 applies). The income statement is on PDF 133 (printed p130), in $m.
- Expense presentation: **by nature**.
- Key values ($m):

| Item | Value | Label |
|---|---|---|
| Revenue | 44,189 | |
| Raw materials and inventory | (28,828) | |
| Employee benefits expense | (6,639) | |
| EBIT | 3,989 | Earnings before finance costs and income tax expense |
| Finance costs | (236) | Interest on lease liabilities |
| Finance costs | (166) | Other finance costs |
| PBT | 3,587 | |
| NPAT | 2,557 | |

- Identity check: 44,189 − 40,379 + 144 + 35 − 236 − 166 = 3,587, which equals the printed PBT. **Difference 0.**
- Difficulties:
  - Finance costs are printed as two lines with no total. `finance_costs.value` is null and both lines are listed as components.
  - EBIT is before lease interest.
  - PP&E of 5,653 excludes right-of-use assets (5,497).
  - "Goodwill and intangible assets" is a single combined line.
  - The geographic split covers only revenue from contracts with customers: Australia 41,192 out of 44,047.
  - Employees are about 120,000, a rounded headcount.
- Pages viewed: 3, 133, 134, 135, 142, 143, 144.
- Confidence: **high**.

## Notes for scaling

- Wesfarmers is an easy case. Every report back to 1999-2000 is linked from one static HTML archive page, every PDF has a text layer, and the URLs are predictable but carry an `sfvrsn` cache-buster, so the archive page has to be scraped once.
- The cross-year definitional breaks need harmonisation rules rather than better extraction:
  - AGAAP to AIFRS (2005/06): revenue definition, goodwill amortisation, and a by-function to by-nature switch at the same firm.
  - AASB 16 (2019/20): occupancy cost, finance costs, EBIT, and PP&E versus ROU assets.
  - Goodwill sometimes included in and sometimes excluded from intangibles.
- Employee cost is missing from pre-IFRS by-function reports and would need a proxy.
- The firm switches from by-function to by-nature between 2005 and 2015. A cost-of-goods-sold series therefore cannot be built consistently. Under AIFRS, "Raw materials and inventory" is the closest analogue.
