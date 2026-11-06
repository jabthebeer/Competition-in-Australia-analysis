# Fact-check of the ALICIA website (29 October – 6 November 2026)

**Covers:**
- the legislation menu (171 register records, with extra checks on the 34 behind the evaluations);
- the Policy costing tab's evidence library (64 entries);
- the About page and the growth and conditions pages.

**Method:** each claim was checked against its cited source, or against an official source where the citation did not support it. Records are still `draft`: none has been reviewed by a person.

## Summary

| Area | Checked | Result |
|---|---|---|
| Register: dates against their cited sources | 281 dated claims in 170 records | 170 dates appear in their source. 49 do not appear verbatim: on reading, most are the same date in other words (an income year, "Friday, 11 December, 2020") or a correct date on a page that does not state it. 62 sources block automated access (mostly NSW and SA government sites) |
| Register: dates against official registers (date gatherer, 18 Oct 2026) | 171 records | 38 confirmed. The 7 "differs" are all correct: each policy applied later than its law commenced (e.g. default market offer prices from 1 July 2019). 3 not yet commenced. 123 unconfirmed |
| Register: ANZSIC codes, names, date order, jurisdictions | 171 records | No errors |
| Evaluated records | 34 | **1 error** (below). The rest are confirmed or consistent with official sources; 4 rest on sites that block automated access |
| Evidence library quotes and values | 64 entries (9 cite spreadsheets or the project plan) | 52 of 55 checkable quotes confirmed in the source: 48 automatically, 4 Treasury table rows by hand. Every value and range in the Treasury MEB tables matches. Of 3 blocked sources, 2 are confirmed independently (BNvR 2020's 1.6%, cited by the PC; Mistura and Roulet's 2.1%, in the abstract); Klapper, Laeven and Rajan (2004) is not checked |
| About page (RBM facts) | Contact details, labour rates, next update, quotes | All match the RBM PDF (same hash as recorded): pp. 4, 10, 12, 13 |
| Conditions page notes | Commodity index base, unemployment series | Correct: the RBA file is indexed 2024/25 = 100; the data has no seasonally adjusted series for the NT and ACT |

## Errors corrected

| Record | Was | Now | Source |
|---|---|---|---|
| `nsw-e-conveyancing-mandate-2018` (evaluated) | First mandate 1 May 2018 | **1 July 2018**: standalone transfers, standalone caveats, and mortgages and discharges, under Conveyancing Rules v4 (in force 15 May 2018) | Registrar General, "Revised Conveyancing Rules" (13 Apr 2018); 1 July 2019 for all mainstream dealings, Registrar General, NSW eConveyancing news (June 2019) |

**Effect on results:** the registered e-conveyancing evaluation (18 Oct 2026) treats NSW from 2017-18 (first post year 2018). With the corrected date, NSW starts in 2018-19. The result ("no detectable effect", grade Weak) is **not re-run**. The econometric evaluations are archived (`alicia/DECISIONS.md` E-87), and ALICIA now assesses items against the productivity framework only (owner decision, 6 Nov 2026, E-113). The archived result stands as registered, with this caveat. The item's framework assessment does not depend on the start month.

## Provenance corrected (dates unchanged)

- **"Verified" from search snippets.** Seven records were marked dates-verified although their notes said the source was not read.
  - Now read in the source: the national NQF (ACECQA Wave I report, PDF p. 16: "The NQF began on 1 January 2012"), WA's NQF (Table 6, PDF p. 35: 1 August 2012) and the NT container deposit refund (NT register, SL 49: commencement 3 January 2012).
  - Marked unverified, with the reason: NSW ride-share, SA fuel price reporting, SA taxi licence reform, Victorian energy deregulation.
- **Automatic mutual recognition (ACT, NT, SA, Tasmania, Victoria).** The start dates rested on a Victorian Health page that no longer gives any dates, so all five are now marked unverified. The evidence conflicts:
  - **ACT:** an ACT Planning page reportedly gives 1 July 2022 for full implementation.
  - **NT:** NT boards give both 1 July 2021 and 1 July 2022.
- **Better sources cited:**
  - SA commercial stamp duty: RevenueSA Information Circular 103 PDF. The dates were right: 7 December 2015, 1 July 2017, 1 July 2018.
  - The EPBC reform: tranche 1 from 20 February 2026 and the National EPA from 1 July 2026, per DCCEEW, replacing "as announced".
  - The non-compete ban: announced 25 March 2025, per Treasury's Impact Analysis, p. 53.
- **Resolved:** due-diligence item 7, the January 2015 Melbourne fare changes behind the taxi evaluation's confounded fares result. PTV's 2014–15 annual report, PDF p. 6, confirms them.

## Open, for a person (official sources block automated access)

1. **Automatic mutual recognition start dates** for the ACT, NT, SA, Tasmania and Victoria.
2. **NSW records:** fuel price reporting 2016 (evaluated; its date may be a registration deadline) and ride-share 2015. The NSW registers and Transport for NSW block automated requests.
3. **SA records:** fuel price reporting 2021 (evaluated; consistent with the gazetted text as quoted in search results) and taxi licence reform 2025.
4. **Correct dates whose cited page does not state them:**
   - gas emergency price cap (23 Dec 2022);
   - $25,000 instant asset write-off (29 Jan 2019);
   - Sydney lockout start and repeal dates;
   - small business restructuring (1 Jan 2021);
   - motor vehicle repair information scheme (1 Jul 2022);
   - WA and NSW short-term rental registers.

   Each needs a source that states the date.
5. **Klapper, Laeven and Rajan (2004)**, evidence entry `c4.epsilon.klr2004`: NBER blocks the download.
