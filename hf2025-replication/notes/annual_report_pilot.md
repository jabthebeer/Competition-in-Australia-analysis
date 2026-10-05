# Annual-report extraction pilot: protocol

**Purpose.** Test whether Claude agents can reliably extract firm-level financials from listed companies' annual-report PDFs, as a free substitute for a commercial database. The aim is to support listed-firm markup estimates (De Loecker, Eeckhout & Unger 2020 style: sales, cost of goods sold or operating costs, and capital) for 2004 to the latest year.

**Pilot scope.** 6 firms × 3 fiscal years (FY2005, FY2015, FY2024) = 18 reports, one agent per firm. A firm's FY2005 is the fiscal year ending in calendar 2005.

**Decision rule after the pilot.** Scale up only if all three hold:
- (a) extraction is accurate on spot-checks;
- (b) old (mid-2000s) reports are usable;
- (c) the cost per report is acceptable.

## Rules (all agents)

1. **Never fabricate or estimate.**
   - Every non-null value must be printed in the report.
   - Record it exactly as printed, with:
     - its verbatim line label;
     - its unit (e.g. `$m`, `$'000`);
     - the PDF page index (1-based, as used by the Read tool `pages` parameter);
     - the printed page number, if any.
   - If a value is not printed, record `null` with a reason.
   - Do not compute missing items. Derived values go only in the `checks` block, clearly labelled.
2. **Visual confirmation is mandatory.**
   - Use `pdftotext -layout -f N -l N` only to *locate* pages.
   - Then view every page you take numbers from with the Read tool (`pages` parameter, at most 20 pages per call).
   - Confirm each number against the rendered image. Text extraction can misalign columns.
3. **Sources.** Use the company's own website only (investor relations or annual report archive).
   - **Do not access asx.com.au.** Its terms of use prohibit any "spider, screen scraper, robot … or other similar process".
   - Do not use paywalled sites or third-party aggregators (annualreports.com, Morningstar, etc.).
   - Do not use SEC EDGAR or the Wayback Machine.
   - WebSearch may be used to *find* the direct PDF URL on the company's own domain.
4. **Politeness and terms.**
   - Before downloading from a domain, fetch `https://<domain>/robots.txt`. If the target path is disallowed for `User-agent: *`, do not download; record this instead.
   - If the site's terms of use are easy to find and explicitly prohibit automated downloading, stop and record this.
   - Use the user agent `Mozilla/5.0 (X11; Linux x86_64) research-replication`. Never send personal information.
   - Make at most one request per second, and download only the target reports. No crawling.
5. **Which numbers.**
   - **Consolidated group**, not the parent entity.
   - The **current-year column, as originally reported** in that year's report, not the comparatives.
   - Continuing plus discontinued operations exactly as the statement presents them: record both if both are shown.
6. **Files** (paths relative to `hf2025-replication/`):
   - PDF: `data/raw/annual_reports/pdfs/{TICKER}_FY{YYYY}_annual_report.pdf` (git-ignored; record its sha256).
   - Extraction: `data/raw/annual_reports/extractions/{TICKER}_FY{YYYY}.json`.
   - Log: `data/raw/annual_reports/logs/{TICKER}.md`, recording for each report:
     - URLs and the robots.txt check;
     - start and end timestamps (`date -u`);
     - difficulties (scanned or image-only pages, restatements, discontinued operations, dual-listed structures, mixed presentation);
     - a confidence rating (high / medium / low).

## JSON schema (one file per firm-year)

```json
{
  "ticker": "WES", "company": "Wesfarmers Limited", "fiscal_year": 2005,
  "period_end": "2005-06-30", "currency": "AUD", "unit_as_printed": "$m",
  "accounting_basis": "AGAAP pre-IFRS | AIFRS",
  "source_url": "...", "accessed_utc": "...", "pdf_sha256": "...", "pdf_pages": 0,
  "robots_txt_ok": true,
  "expense_presentation": "by_function | by_nature | mixed",
  "income_statement_page": {"pdf_page": 0, "printed_page": "..."},
  "income_statement_lines": [
    {"label": "verbatim label", "value": 0.0, "pdf_page": 0, "note": "sign as printed; brackets = negative"}
  ],
  "fields": {
    "revenue":                       {"value": null, "label": null, "pdf_page": null, "note": ""},
    "other_income":                  {"value": null, "label": null, "pdf_page": null, "note": ""},
    "cost_of_sales":                 {"value": null, "label": null, "pdf_page": null, "note": ""},
    "gross_profit":                  {"value": null, "label": null, "pdf_page": null, "note": ""},
    "raw_materials_and_inventory":   {"value": null, "label": null, "pdf_page": null, "note": "by-nature: raw materials/consumables used, purchases, changes in inventories"},
    "employee_benefits_expense":     {"value": null, "label": null, "pdf_page": null, "note": "may be in a note if by_function"},
    "depreciation_and_amortisation": {"value": null, "label": null, "pdf_page": null, "note": ""},
    "impairment":                    {"value": null, "label": null, "pdf_page": null, "note": ""},
    "selling_general_admin_lines":   [{"label": "", "value": null, "pdf_page": null}],
    "ebit":                          {"value": null, "label": null, "pdf_page": null, "note": "only if printed"},
    "finance_costs":                 {"value": null, "label": null, "pdf_page": null, "note": ""},
    "profit_before_tax":             {"value": null, "label": null, "pdf_page": null, "note": ""},
    "income_tax_expense":            {"value": null, "label": null, "pdf_page": null, "note": ""},
    "net_profit_after_tax":          {"value": null, "label": null, "pdf_page": null, "note": "attributable to members, and total, if both shown"},
    "ppe_net":                       {"value": null, "label": null, "pdf_page": null, "note": "balance sheet"},
    "intangible_assets":             {"value": null, "label": null, "pdf_page": null, "note": ""},
    "total_assets":                  {"value": null, "label": null, "pdf_page": null, "note": ""},
    "employees":                     {"value": null, "label": null, "pdf_page": null, "note": "headcount or FTE; say which"},
    "australian_revenue_share":      {"value": null, "label": null, "pdf_page": null, "note": "only if geographic split printed; record AU revenue and total"}
  },
  "checks": {
    "income_statement_identity": "revenue + other income - listed expenses (+/- associates) - finance costs vs printed PBT; report the difference",
    "identity_difference": null
  },
  "minutes_spent": null,
  "confidence": "high | medium | low",
  "issues": []
}
```
