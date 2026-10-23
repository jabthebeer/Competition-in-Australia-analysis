# Guide: checking the evidence library with Claude Cowork

**For:** the project owner, working in Claude Cowork. **Why:** the plan's P3 acceptance test ("every default entry [P] or [A] and checked by Cowork", [`forward_plan_policy_costing.md`](../forward_plan_policy_costing.md) §9).

The evidence library holds every parameter the productivity costing uses: 60 entries, 48 of them defaults. Each one was read against its source when it was compiled, but none has had an independent check. Cowork checks each row of the review sheet against its source. Claude Code then marks the checked entries in the library.

**Time:** about 2 hours of Cowork work over five batches.

## The file

[`evidence_library_review.csv`](evidence_library_review.csv): one row per entry, UTF-8, opens in Excel.

**Left-hand columns (read only):**
- `id`, `formula` and `parameter`: what the entry is and which formula uses it.
- `is_default`: whether the costing uses it by default.
- `value`, `low`, `high`, `units`: the numbers to check.
- `tag`: [P] full text, or [A] abstract only.
- `citation`, `url`, `locator`: where to look. "p. 10 (PDF p. 11)" means printed page 10, which is page 11 of the PDF file.
- `quote`: exact text from the source. Several excerpts from the same place are joined with " … ".
- `derivation`: how `value`, `low` and `high` come from the source. Some are arithmetic, e.g. "0.72 ÷ 2.09 = 0.344".
- `review_status`: `draft` until checked.

**Right-hand columns (Cowork fills only these):**

| Column | What goes in it |
|---|---|
| `check_value` | `same` if `value`, `low` and `high` follow from the source as `derivation` says; otherwise the numbers you find |
| `check_quote` | `exact` if every excerpt appears word for word at the locator; otherwise the correct text |
| `check_locator` | `same` if the page, table or section is right; otherwise the correct one |
| `verdict` | `agrees`, `differs` or `unsure` |
| `reviewer_notes` | Anything else: what you searched, a better source, or a concern about the method |

## Prompts

**1. Set the rules (paste once)**, with the CSV in the task folder:

```text
You are checking an evidence library for an economic costing tool. The folder has evidence_library_review.csv, one row per parameter. For each row I name:
1. Open the url and find the place given in locator. "p. 10 (PDF p. 11)" means printed page 10 = page 11 of the PDF.
2. Check that each excerpt in quote (excerpts are separated by " … ") appears word for word there. Ignore differences in line breaks and spacing only.
3. Check that value, low and high follow from the source as derivation describes; redo any arithmetic.
4. Rows tagged A were read in the abstract only: check them against the abstract on the url.
5. Rows whose citation is the ALICIA project plan are the tool's own assumptions: check only that the quote is in the plan at the locator.
6. Fill only check_value, check_quote, check_locator, verdict and reviewer_notes. Use "same" or "exact" when the row is right. Do not change any other column, row or the order of rows.
7. verdict is agrees, differs or unsure. Never guess: if you cannot open the source or find the text, use unsure and say why in reviewer_notes.
Save the CSV after each batch.
```

**2. Check one batch at a time**, replacing `[BATCH]`:

| Batch | Rows whose id starts with | Rows |
|---|---|---|
| 1 | `c1.`, `c2.`, `c3.`, `c4.` | 9 |
| 2 | `c5.`, `c6.`, `c7.` | 15 |
| 3 | `c8.`, `c9.`, `c10.` | 11 |
| 4 | `c11.` | 12 |
| 5 | `layer-b.`, `general.` | 13 |

```text
Check the rows in [BATCH] as set out in the rules. Then show me a table: id, verdict, and a one-line reason for any row that is not "agrees".
```

## Notes on sources

- **Paywalled journals.** Chirinko, Fazzari and Meyer (2011), Garicano, Lelarge and Van Reenen (2016), Gourio and Roys (2014) and Bloom, Griffith and Van Reenen (2002) are tagged [A]: the url opens the abstract.
- **KPMG figures** (`c11.*.kpmg`) are as Treasury reports them in its own tables. Check them in Treasury's tables, not in the KPMG reports.
- **Spreadsheets.** The ABS rows (`c3.alpha.abs-mfp`, `layer-b.alpha.abs-mfp`) point to a table, row and columns in the ABS workbook. The quote is the table and row headings, not a sentence.

## Afterwards

Send the saved CSV to Claude Code. It will:
- mark each `agrees` row as checked in the library (`review: {status: "checked", by, on}`);
- fix each `differs` row from your notes, then ask you to check that row again;
- rebuild the sheet with `npx tsx scripts/evidence-sheet.ts`, which keeps your check columns.

No default is final until its row is `agrees`.
