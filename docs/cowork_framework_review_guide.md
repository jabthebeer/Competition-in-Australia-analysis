# Guide: checking the framework assessments with Claude Cowork

**Date:** 28 October 2026. **For:** the project owner, working in Claude Cowork. **Why:** every one of the register's 198 assessments was drafted by AI-assisted desk research and needs a person's check before the marks are relied on (`alicia/DECISIONS.md` E-86).

## What Cowork fills in

**The file:** [`docs/review/framework_assessments_review.csv`](review/framework_assessments_review.csv), one row per register item, written by `uv run python scripts/assessment_sheet.py` (in `alicia/`).

**Left-hand columns (read only):** the item (`record_id`, `kind`, `jurisdiction`, `title`, `family`), its overall mark, band, main driver, reach and confidence, its mark on each of the eight drivers, the reasons, the summary and the sources.

**Right-hand columns (Cowork fills only these):**

| Column | What goes in it | Allowed values |
|---|---|---|
| `review_verdict` | Do the marks fit the framework and the evidence? | `agrees`, `partly`, `differs`, `unsure` |
| `marks_suggested` | Changed marks, each as `driver ±n: reason` | Text, for example `capital -1: the cap deters new centres` |
| `main_driver_suggested` | A different main driver, if the evidence says another matters more | A driver id, or blank |
| `sources_checked` | The sources Cowork read, each as a URL | URLs separated by spaces |
| `reviewer_notes` | Why, for `partly` or `differs` (required), and anything else | Text |

## Step 1. Set the rules (paste once)

> You are checking draft assessments of Australian laws, regulatory settings and barriers against the ALICIA productivity framework (`docs/productivity_framework.md`; paste it in). Rules:
> 1. Mark only from evidence: official inquiries and reviews (Productivity Commission, ACCC, Treasury, RBA, OIA), legislation, regulators' pages, and peer-reviewed research. News and commentary may point to a source but are never the source.
> 2. Use the framework's marking guide for each driver, its overlap rules, and its counterfactual: a reform against what it replaced, a setting or barrier against the market without it.
> 3. Marks cover productivity and competition only. Do not lower a mark because the rule has safety, health or fairness benefits; say so in `reviewer_notes` instead.
> 4. Never invent a source, figure or quote. If you cannot find evidence, answer `unsure`.
> 5. Change only the five right-hand columns. Keep every row and every left-hand value exactly as it is.

## Step 2. Check the items, one batch at a time

Work in batches of about 25 rows, starting with the existing settings and barriers (they carry most of the negative marks), then the reforms family by family. For each batch, paste:

> For rows <first id> to <last id>: read each item's summary, marks, reasons and sources. Check the sources and look for official evidence on the item's effect on each driver. Fill the five review columns. Where a family repeats one assessment across jurisdictions, check one member in depth and note in `reviewer_notes` whether the others differ.

## Step 3. Check the work (paste once)

> List every row whose `review_verdict` is blank, and every `partly` or `differs` row without `reviewer_notes`, and fill them. Confirm no left-hand column has changed.

## Step 4. Hand it back to Claude Code

Save the sheet as `framework_assessments_review_completed.csv` and attach it in a Claude Code session, or upload it to `docs/review/`. Claude Code will:

1. validate it with `uv run python scripts/assessment_sheet.py --check <file>` (unchanged left-hand columns, allowed verdicts, notes where required);
2. apply the agreed changes to the records, setting each reviewed record's `review` to reviewed, by you, on the date;
3. re-run `alicia validate`, the tests and `scripts/register_summary.py`, and rebuild the website.
