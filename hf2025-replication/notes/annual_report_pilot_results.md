# Annual-report extraction pilot: results (2026-10-05)

Protocol: `annual_report_pilot.md`. Six Claude agents ran in parallel, one per firm, each targeting FY2005, FY2015 and FY2024. Outputs:
- extractions and logs: `data/raw/annual_reports/{extractions,logs}/`
- PDFs: `data/raw/annual_reports/pdfs/`, git-ignored

## Coverage and accuracy

| Firm | FY2005 | FY2015 | FY2024 | Presentation | Identity check (all years) |
|---|---|---|---|---|---|
| Wesfarmers (WES) | ✓ (AGAAP) | ✓ | ✓ | by function in 2005, by nature after | 0 |
| Woolworths (WOW) | ✓ (AGAAP) | ✓ | ✓ | by function | 0 (see terms issue below) |
| Telstra (TLS) | ✓ (AGAAP; 7 section PDFs) | ✓ | ✓ | by nature | 0 |
| Qantas (QAN) | ✓ (AGAAP) | ✓ | ✓ | by nature | 0 |
| Brambles (BXB) | ✗ archive starts FY2007 | ✓ (US$) | ✓ (US$) | by nature | 0 |
| BlueScope (BSL) | ✓ (concise, AGAAP) | ✓ (concise) | ✓ | by nature | 0 |

- **17 of 18 reports obtained.** In all 17, revenue less the listed expenses reproduces printed profit before tax exactly.
- **Independent check.** For each of the 632 extracted values with a page citation, I searched the text layer of the cited PDF page (`pdftotext`, separately from the agents). All 632 were found.
  - The one apparent miss, Telstra FY2005 employees, cites page 6 of the second section PDF, where it appears.
  - This check shows that no value was invented. It does not prove the right column was used, so I also checked the year columns by hand for Qantas FY2015 and Telstra FY2005; both were correct.
- **Effort:** about 1.0 million subagent tokens for 17 reports, roughly 58k per report. Wall-clock time was about 5–8 minutes per agent, with all six running in parallel.

## What blocks scaling (in order of severity)

1. **Website terms.** Every firm's site needs its own terms check *before* downloading.
   - **Woolworths' terms prohibit any "robot, spider … or other mechanism to retrieve" content** (clause 1.3(b)(v)). The agent noticed this only after downloading, which is a protocol deviation. Its WOW files are kept locally and **not committed**, pending the user's decision.
   - Telstra's terms authorise viewing "using your web browser", and its robots.txt blocks named AI crawlers.
   - Qantas limits use to "personal and non-commercial purposes".
   - Wesfarmers, Brambles and BlueScope have no relevant restriction.
   - At 200 firms, a meaningful share of sites will exclude automated retrieval, and that would bias the sample.
   - **The compliant alternative:** the user downloads PDFs in a browser, which the terms permit, and agents extract only from local files.
2. **Mid-2000s coverage.** One of six archives (Brambles) starts at FY2007. Some sites load their archives with JavaScript, and BlueScope's data feed is disallowed by robots.txt, so finding report URLs is the main bottleneck.
3. **Accounting breaks.**
   - AGAAP → AIFRS between FY2005 and FY2006 changes the revenue definition (asset-sale proceeds were included before), goodwill amortisation, and sometimes the presentation itself (Wesfarmers moved from by function to by nature).
   - AASB 16 in 2019–20 changes the lease lines.
   - A clean "mid-2000s" window should therefore start in FY2006.
4. **Cost concept.** Four of six firms report expenses **by nature**, with no cost of sales.
   - A De Loecker–Eeckhout–Unger cost-of-goods-sold markup is not available consistently.
   - BLADE-style variables are: gross output = income; labour = employee benefits; intermediates = total expenses − labour − D&A − fixed costs (H&F Appendix A.2). These can be built from by-nature statements, which brings them closer to H&F's own markup definition.
   - Firms reporting by function need the employee-benefits note, which is missing in some pre-2006 reports.
5. **Multinationals.** Consolidated figures include foreign operations; Brambles, for example, is mostly offshore and reports in US$. These figures can support firm markups, but not Australian market shares.

## Rough cost of scaling (at about 58k tokens per report)

| Panel | Reports | Subagent tokens |
|---|---|---|
| ASX-50 non-financials, FY2006–FY2025 | ~1,000 | ~60 M |
| ASX-200 non-financials, FY2006–FY2025 | ~3,000–4,000 | ~200 M |

## Assessment

The extraction is accurate and fast. The binding constraints are legal and coverage, not technical. A listed-firm panel would still be a selected sample of large firms, used only for *changes*, bridged to BLADE as the project brief requires. Whether to scale is the user's call; options are listed in the check-in message.
