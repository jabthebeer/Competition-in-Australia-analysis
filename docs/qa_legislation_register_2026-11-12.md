# Quality check of the legislation register (12 November 2026)

**Covers:**
- the 329 requirements in `regulation-register/requirements/`;
- the Commonwealth catalogue, `data/processed/legislation/cth_catalogue.csv` (1,263 Acts and 23,579 instruments);
- the website built from them, especially the Industry lens.

**When:** after the final Commonwealth batch (DECISIONS E-143), before phase D (states and territories).

**Who:** the same drafting process that wrote the register. This is not an independent review. Every requirement is still a `draft`, and none has been checked by a person (phase G).

## Summary

| Part | What was checked | Result |
|---|---|---|
| 1. Automated checks | Every requirement and catalogue row: numbers in descriptions missing from quotes, quote length and wording, locators, confidence, reach, marks, duplicate quotes, catalogue links | 8 fixes. The other flags were read and are by design (below) |
| 2. Sample of requirements | 30 drawn at random (seed 20261112): 25 Commonwealth drafts from phase C and 5 state requirements whose law was quoted after an ABLIS-first draft | No wrong law, section or reach. 11 descriptions or summaries said more than their quotes and were trimmed; 1 weak quote replaced. The same wording was then fixed in the rest of the 2 long service leave families |
| 3. Sample of 'no requirement' (N) calls | 40 drawn at random (20 Acts, 20 instruments), each read against its text; then the batch heading the miss came from; then every N Act re-scanned for duties on businesses | 1 miss in the sample led to 4 more. 3 Acts recalled Y and drafted, 1 recalled Y to draft, 1 recalled L, and 6 instruments recalled L. 10 reasons corrected |
| 4. Website | Site built; 7 pages and the Industry lens opened in Chromium at 1,280 and 390 pixels wide | No script errors and no sideways scroll. New requirements show for the right classes |

After the check: 329 requirements, 958 quotes re-found in the law's text, 0 validation problems, and all tests pass.

## Part 1: automated checks

**Fixed:**
- **My Health Record share-by-default:** the quote stopped before the period it describes, so it now runs to "period of 24 hours" (s 13(1)–(2)).
- **Aged care provider registration:** confidence lowered to medium. The quote is the Act's simplified outline, because registration is a condition of funding, not an offence.
- **Brisbane outdoor dining permit:** confidence lowered to medium. It is quoted from ABLIS and the council's web page; the local law's words are not yet quoted.
- **ASIC annual review fee:** confidence lowered to medium. The quote shows the regulations may prescribe the fee; who is liable (s 7) is not yet quoted.
- **Security sensitive biological agents event reporting:** the National Health Security Act 2007 added as a law (s 48), next to the Regulations it was drafted from.
- **Disability standards for premises:** a leading space removed from the quote.
- **Consumer data right rules:** the catalogue row now names the data holder requirement it supports; it had named an unrelated one.
- **Health practitioner registration (8 states and territories):** the quote of s 113(1) began at '(a) take or use a title', so it lacked the duty. It now starts at 'A person must not knowingly or recklessly'.

**Read and left as they are:**
- 38 quotes have none of the duty words searched for. They are:
    - award coverage clauses;
    - provisions that impose a levy or tax, or make an employer liable, in other words;
    - entitlement or scope clauses quoted next to a duty;
    - council web pages ('you will require this permit').
- 12 'numbers not in the quote' are years in the names of laws.
- 6 pairs of shared quotes are the same model-law provision in different states, or one provision behind 2 requirements.
- 3 council permits with high confidence also quote the local law.
- 3 short quotes are whole provisions.
- 1 catalogue name carries a zero-width character, as the Federal Register publishes it.

## Part 2: sample of requirements

Each of the 30 was read for whether the description, reach, triggers and framework marks follow from the quotes.

**Passed as drafted:** 19.

**Trimmed (description or summary said more than the quote):** 11.
- 6 descriptions: GMO dealing licence, Gas Market Code, transport safety reporting, Bulk Wheat Code, Water Market Rules and NSW livestock property identification (the quote covers the property identification code, not movement records).
- 2 summaries: ADI and general insurer authorisation mentioned prudential standards that the quoted offence does not cover.
- 3 portable long service leave records: the descriptions said employers "report eligible workers' service", but the quotes cover registration only. Across the 2 families, the descriptions were fixed in the 9 records whose quotes do not mention reporting, and the summaries in all 12.

**Weak quote replaced:** 1. The ACT construction long service record quoted a note pointing to s 31, so it and its cleaning and security sibling now quote s 31(1).

**Found by part 1's re-run:** the illegal logging record's title promised due diligence, but it quoted only the import offence (s 9). It now also quotes the due diligence offence (s 12(1)).

## Part 3: sample of N calls

**The sample.** Of the 20 Acts, 1 was wrong: the Sex Discrimination Act 1984, called N in batch 6 under the heading 'social security, family, health benefits, students or individuals'. Since 2022, s 47C has put a positive duty on every employer and every person conducting a business or undertaking. The 20 instruments were all right, though 4 older ones could not be read as text and rest on their parent Act's call. One N call was judged right on a closer read: the CASA unmanned aircraft directions (CASA 20/25) bind everyone who flies a drone, like road rules (rule 1).

**The heading.** All 31 Acts under that heading were then read. 4 more were wrong.

| Act | Was | Now | Why |
|---|---|---|---|
| Sex Discrimination Act 1984 | N | Y, drafted | Positive duty on employers and businesses (s 47C(1)) |
| Marriage Act 1961 | N | Y, drafted | Only an authorised celebrant may solemnise a marriage (s 101); registration needs set qualifications and a fit and proper test (s 39C(1)) |
| Child Support (Registration and Collection) Act 1988 | N | Y, drafted | Once notified, an employer must deduct child support from an employee's pay (s 46(1)–(2)) |
| Disability Discrimination Act 1992 | N | L | Contravening a disability standard is unlawful (s 32), which gives the 3 standards their force |
| Protection of Movable Cultural Heritage Act 1986 | N | Y, to draft | Exporting an Australian protected object needs a permit or certificate (s 9) |

The instruments under them followed. The Marriage Regulations 2017, the celebrancy qualifications determination, the celebrant fees determination and the professional development statement are L to celebrant registration. The Child Support Regulations 2018 are L to the deductions, and the Movable Cultural Heritage Regulations 2018 are L to its Act.

**Reasons corrected (call unchanged):** the Age and Racial Discrimination Acts (general anti-discrimination law, rule 1), the Fuel Tax Act 2006 (credits a business may choose to claim), the Port Statistics Act 1977 (information only on notice, s 5), the Crimes (Taxation Offences) Act 1980 (general criminal law), the Safety, Rehabilitation and Compensation Act 1988 (Commonwealth employees and Comcare licensees), and 3 instruments under the Sex Discrimination, Disability Discrimination and Child Support Acts.

**The re-scan.** Every Act still called N (875) was then searched offline in the corpus copy for duties on employers, operators, providers and other businesses. 67 had such wording. On reading, none is another miss. They are:
- voluntary schemes (student loans, carbon credits, the emissions registry);
- public bodies;
- amending Acts whose duties sit in a principal Act already called;
- prohibitions that bind everyone alike.

**What this says about batch 6.** Calls made from titles alone missed duties that sit in Acts with general-sounding names: 1 in 20 in the sample. The re-scan suggests the misses were concentrated under the one heading. But it searched for duty wording only, so it can miss a duty worded another way. Phase G should still sample the title-only calls.

## Part 4: website

The site was built with `uv run alicia site` and opened in Chromium (Playwright). The 7 pages were opened at 1,280 and 390 pixels wide: home, Structural competitive conditions (2 pages), Legislative levers, Industry lens, Framework and Methodology. There were no script errors and no sideways scroll.

On the Industry lens:
- marriage celebrant registration shows for class 9539 (other personal services n.e.c.);
- the sex discrimination positive duty shows for every class;
- the ACT long service registration shows for class 3011 (house construction);
- timber due diligence shows for class 3331 (timber wholesaling).

The child support deduction has no framework marks, so it shows only when 'Show laws with no material effect' is ticked. This is by design.

## Limits

- The samples are small: 30 of 329 requirements (9%) and 40 of 5,046 N calls.
- The checks were run by the process that drafted the register, so they share its blind spots. A person still needs to check the register (phase G).
- The re-scan searched for duty wording only. A duty worded another way, or one in an instrument with no corpus copy, would be missed.

## Follow-up

- Draft the 4 Commonwealth Y calls still to draft: the 2 ASIC continuing credit orders, the Disability Standards for Accessible Public Transport, and the Movable Cultural Heritage export permit.
- Quote s 7 of the ASIC review fee law and the Brisbane local law, so their confidence can return to high.
- Quotes from the calibration that are still weak: superannuation guarantee, ACT workers' compensation, and privacy for health service providers.
