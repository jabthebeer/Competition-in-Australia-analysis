# Review of OIA's Regulatory Burden Estimate calculator (July 2026)

**Workbook:** `regulatory-burden-estimate-calculator.xlsx`, "Version July 2026"
- Source: <https://oia.pmc.gov.au/resources/regulatory-burden-estimate-calculator>
- SHA-256: `6bc19cb6…4c8af7`
- Accessed 6 October 2026.

**Why this matters to the project:**
- The IA Practical Guide (p. 7) points agencies to this workbook, so users will compare our tool's results with it.
- Its conventions help settle some RBM ambiguities.
- Its outputs are **not** a reliable validation benchmark (see below).

## Method

1. Read every formula on the `2. Calculator` and `3. Estimates` sheets.
2. Entered OIA's own four training examples (sheet `5. Examples`) into copies of the workbook.
3. Recalculated them with LibreOffice (headless).
4. Compared the outputs with the answers OIA states for each example.

## Results

| OIA example | OIA's stated 10-year answer | Workbook output | Matches? |
|---|---|---|---|
| A: 110 wholesalers, 22 h/yr, $150/h | $3.63m (=110×22×150×10) | **$3.267m** | No |
| B: 15,000 centres, 4 h initial course, 1 h refresher every 3 years (entered as frequency ⅓ a year) | $9.61m | $9.6117m | Yes, by coincidence: ongoing costs only run in years 2–10, and 9 × ⅓ happens to equal the 3 refreshers (years 4, 7, 10) |
| C: 9 applications/yr, approval 35 → 19 days, $13,800/day | $19.87m (=9×16×13,800×10) | **$0.125m** | No |
| D: 30,000 retailers, $800 + 2 h set-up, 1 h/yr from year 2 | $54.21m | $54.2082m | Yes |
| D with 2 staff per entity | set-up should double with staff | set-up labour unchanged; ongoing doubles | No |

## Defects identified

1. **Year 1 omits recurring costs.**
   - The instructions say "Initial Cost (Year 1) … includes one-off setup/upfront costs PLUS the first year of recurring operating costs".
   - However, the formulas (`2. Calculator`!I29:I33 and F40:F44) include set-up costs only, and `3. Estimates`!C4:C6 take year 1 from them.
   - So recurring costs are counted for 9 years, not 10. This explains Example A.
2. **Both delay-cost formulas are mis-specified.**
   - Year 1 is `B×F×D` (income per day × entities × recurrence), with no length of delay.
   - Ongoing is `C×D×F` (days × recurrence × entities), with no dollar value.
   - The "standby expenses" named in the description have no input column. This explains Example C.
3. **Set-up labour ignores staff per entity.** `I29` is `B×F×G`, with no `H`.
4. **The period-of-analysis input is unused.** `B11`/`B20` (named `Projection_years`) isn't referenced by any formula. The estimates sheet is fixed at 10 years, and the annual average is hard-coded as ÷ 10.
5. **Scope limitations** (design choices rather than bugs):
   - one entity count for every cost item;
   - no split by Business / Community organisations / Individuals, so it can't produce the RBE table by sector;
   - no reform, current-vs-reformed or BAU adjustment;
   - several defined names left over from an older version (`Discount_rate`, `NET_PRESENT_VALUE__NPV`, …) point to `#REF!`.
6. **Sign convention in Example C.** The example is a burden *reduction* (faster approvals), but its answer is given without a sign. RBM p. 11 requires reductions to be entered as negatives.

## Conventions this project adopts from the workbook

- **Work rate.** It uses the work rate **91.54** directly (cell `C9`), which supports interpretation A-02.
- **Delay costs.** It describes delay costs as "standby expenses + lost income", which supports A-01 (adding an "additional expenses" input). It also measures delays in **days**, so the tool will accept days, weeks or months.
- **Ongoing costs from year 2.** Example D treats ongoing costs as starting "after the year installed" (from year 2). The tool can represent this as `ongoing` with `startYear: 2`.
- **Test cases.** The four examples, with OIA's *stated* answers, become illustrative tests (T-ANN-08, T-DEL-05).

## Reproducing this review

The scripts used were throwaway and aren't committed. To reproduce:

1. Open a copy of the workbook and enter each example's values in the cells labelled "INPUT HERE".
2. Recalculate.
3. Read `3. Estimates`!B7 (the 10-year total).
