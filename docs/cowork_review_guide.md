# Guide: checking the evaluated laws with Claude Cowork

**Date:** 18 October 2026. **For:** the project owner, working in Claude Cowork. **Why:** step 1 of the [due-diligence plan](due_diligence.md).

All 34 laws used by the current evaluations are draft records. Only 7 of their dates are confirmed against an official register: the NSW and SA registers block automated checks, and other records lack register identifiers. A wrong date, state or industry biases an evaluation towards "no effect". This guide gets Cowork to check every record against official sources, in a form Claude Code can validate and apply.

**Time:** about 2–3 hours of Cowork work over six batches. Your own time is mostly copying prompts and spot-checking.

## What Cowork fills in

**The file:** [`docs/review/evaluated_records_review.csv`](review/evaluated_records_review.csv), one row per law.

**Left-hand columns (read only):** what the record says and how the evaluations used it:
- `recorded_commencement`, `recorded_what`, `recorded_source`, `instruments`;
- `evaluation_window`, `evaluation_industries`, `evaluation_comparison`;
- `record_confounders`.

**Right-hand columns (Cowork fills only these):**

| Column | What goes in it | Allowed values |
|---|---|---|
| `check_commencement_date` | The date the change actually took effect | YYYY-MM-DD |
| `check_what_commenced` | What took effect that day, if different from `recorded_what` | Text |
| `check_source_url` | The official page or PDF that shows the date | An official URL |
| `check_quote` | A short exact quote from that source showing the date | Under 30 words |
| `date_verdict` | Does the recorded date agree? | `agrees`, `differs`, `unsure` |
| `industries_verdict` | Are the affected industries right? | `agrees`, `partly`, `differs`, `unsure` |
| `industries_suggested` | Better ANZSIC or CPI classes, with a reason | Text |
| `other_changes_in_window` | Other changes that could move the same outcomes, each as `YYYY-MM-DD — what — URL`, separated by ` \| ` | Text, or `none found` |
| `confidence` | How sure Cowork is about the row | `high`, `medium`, `low` |
| `reviewer_notes` | Anything else, including what was searched when unsure | Text |

## Before you start

1. **Download three files** from the repository, branch `claude/sharp-bell-4dsvcz`. On each file's page, use *Download raw file*:
   - https://github.com/jabthebeer/Competition-in-Australia-analysis/blob/claude/sharp-bell-4dsvcz/docs/review/evaluated_records_review.csv
   - https://github.com/jabthebeer/Competition-in-Australia-analysis/blob/claude/sharp-bell-4dsvcz/docs/due_diligence.md
   - https://github.com/jabthebeer/Competition-in-Australia-analysis/blob/claude/sharp-bell-4dsvcz/docs/cowork_review_guide.md (this guide)
2. **Put them in a new folder**, for example `ALICIA review`, and keep an untouched copy of the CSV somewhere else.
3. **In Cowork, start a new task with that folder selected.** Cowork must be able to open web pages. The NSW and SA registers block scripted downloads but open in a normal browser.

## Step 1. Set the rules (paste once)

```text
You are helping me check the inputs to an econometric evaluation of Australian competition reforms. This folder has evaluated_records_review.csv (one row per law or regulation our evaluations use) and due_diligence.md (background). Read both, then wait for my instructions.

Rules for everything in this task:
1. Dates must come from official sources only: the jurisdiction's legislation register (legislation.gov.au, legislation.nsw.gov.au, legislation.vic.gov.au, legislation.qld.gov.au, legislation.sa.gov.au, legislation.wa.gov.au, legislation.act.gov.au, legislation.nt.gov.au), a government gazette, or the responsible regulator's or department's own website. News, commentary and Wikipedia may point you to a source but are never the source.
2. Open every source you cite and copy a short exact quote (under 30 words) that shows the date into check_quote.
3. Never guess. If you cannot find an official source, set the verdict to unsure and write what you searched in reviewer_notes.
4. Write only in these columns: check_commencement_date, check_what_commenced, check_source_url, check_quote, date_verdict, industries_verdict, industries_suggested, other_changes_in_window, confidence, reviewer_notes. Do not change, reorder, add or delete any other column or any row.
5. Allowed values: date_verdict = agrees, differs or unsure; industries_verdict = agrees, partly, differs or unsure; confidence = high, medium or low. Dates as YYYY-MM-DD.
6. The NSW and South Australian legislation registers block automated downloads: open them in the browser.
7. Work only on the rows I name, and save the CSV after each batch.
```

## Step 2. Check the dates, one batch at a time

Run the prompt once per batch, replacing `[BATCH]` with the batch's text from the table. The order puts the newest and least-checked results first:

| Batch | Replace `[BATCH]` with | Rows |
|---|---|---|
| 1 | the rows whose family is fuel-price-transparency | 5 |
| 2 | the rows whose family is e-conveyancing-mandate | 5 |
| 3 | the rows whose family is rideshare-legalisation | 7 |
| 4 | the rows whose family is heavy-vehicle-national-law | 6 |
| 5 | the rows whose family is retail-energy-price-deregulation | 3 |
| 6 | the rows whose family is childcare-nqf, legal-profession-uniform-law, retail-trading-hours or container-deposit-scheme, and the row vic-taxi-licensing-2014 | 8 |

```text
Check the commencement dates for [BATCH]. For each row:
(a) Read recorded_commencement, recorded_what, recorded_source and instruments.
(b) On an official source, find the date the change in recorded_what actually took effect in that jurisdiction: commencement, not assent, gazettal or announcement. If what took effect differs from recorded_what (for example a trial, a registration deadline, or a phase-in), describe what did take effect in check_what_commenced.
(c) Fill check_commencement_date, check_source_url and check_quote.
(d) Set date_verdict: agrees if it is the same day, otherwise differs. For differs, say in reviewer_notes whether the correct date falls in a different financial year (July to June) or quarter from the recorded one. Compare with evaluation_window.
(e) Set confidence.
Save the CSV, then show me a table of the rows you did: record_id, recorded date, your date, verdict, source.
```

**Check yourself:**
- Open the source for one row in each batch and confirm the quote is really there.
- Any `differs` that moves the date into another financial year or quarter matters most: flag it to Claude Code.

## Step 3. Check the industries (paste once, after all date batches)

```text
Now check the industries for every row. record_industries and evaluation_industries list the ANZSIC 2006 classes (four-digit codes) and CPI classes the evaluations treat as affected by each law. Using the ABS class definitions (ANZSIC 2006, ABS catalogue 1292.0, on abs.gov.au) and what the law actually regulates:
- set industries_verdict to agrees if these are the businesses the law directly affects, partly if they include many unaffected businesses or miss affected ones, differs if they are wrong, or unsure;
- for partly or differs, put better codes in industries_suggested, each with a one-line reason and the ABS definition you relied on.
Do not suggest a code without checking its ABS definition. Save the CSV and summarise the rows that are not agrees.
```

## Step 4. Find other changes in each window (one batch at a time, as in step 2)

This is the confounder search. The Melbourne fares result was explained only after we saw it. It turned out to be a public transport fare change in January 2015, not the taxi reform.

```text
For each of [BATCH], search for other changes that could have moved the same outcomes in the same jurisdiction during evaluation_window or in the year before it:
- other laws or regulations affecting the same industry;
- prices, fees, fares, levies, caps or taxes set by government in that industry or CPI class;
- large firm entries or exits;
- major subsidies or programmes.
Use official or reputable sources only (government, regulator, ABS, ACCC, peer-reviewed research). Write each change in other_changes_in_window as "YYYY-MM-DD — what changed — source URL", separated by " | ". record_confounders lists the ones we already know: repeat one only if you can add a date and source. If you find none, write "none found" and say what you searched in reviewer_notes. Save the CSV and list the three changes you think most likely to affect the results, with reasons.
```

## Step 5. Answer the open questions (paste once)

```text
Answer these specific questions from official sources, writing each answer, its source URL and a short quote into reviewer_notes of the row named.
1. vic-taxi-licensing-2014: Did Melbourne public transport fares change on 1 January 2015 (travel across zones 1 and 2 capped at the zone 1 fare; free trams in the CBD)? Give the exact start date and the fare change, from Public Transport Victoria, the Victorian Fares and Ticketing Manual, the Victoria Government Gazette or a Victorian Government media release. Also list any taxi fare determinations in Victoria between July 2014 and June 2015.
2. nsw-fuel-price-reporting-2016: On what date did reporting prices to FuelCheck become mandatory for all NSW service stations? Our record uses the registration deadline, 14 July 2016.
3. qld-fuel-price-reporting-2018: When did mandatory reporting start, and was it a trial? Give the start and end dates of any trial.
4. tas-fuel-price-reporting-2020 and sa-fuel-price-reporting-2021: confirm the date retailers first had to report prices, and whether there was a phase-in.
5. The five e-conveyancing-mandate rows: for each state, the date paper lodgment stopped being accepted for the transactions the mandate covered, and which transactions were covered first.
Save the CSV.
```

## Step 6. Check the work before handing it back (paste once)

```text
Before I hand this back, check your own work:
1. List every row where date_verdict, industries_verdict or confidence is blank, and fill them (unsure is acceptable).
2. For every row with agrees or differs, confirm check_source_url is an official source and check_quote contains the date.
3. Re-open five sources at random and confirm the quotes are exact. Correct any that are not, and tell me which.
4. Compare with the original CSV and confirm no column other than the review columns has changed, and no rows were added or removed.
5. Save the result as evaluated_records_review_completed.csv in this folder: same columns, same order, UTF-8.
Then give me a short summary: counts of agrees, differs and unsure for dates and for industries, the rows I should look at myself, and anything you could not check.
```

## Step 7. Hand it back to Claude Code

1. Upload `evaluated_records_review_completed.csv` to the repository at `docs/review/` on branch `claude/sharp-bell-4dsvcz`: on GitHub, *Add file → Upload files*. Or attach it in a Claude Code session.
2. Tell Claude Code: **"Apply the completed record review in docs/review/evaluated_records_review_completed.csv."**

Claude Code then:
1. Validates the file:
   ```
   uv run python scripts/review_sheet.py --check ../docs/review/evaluated_records_review_completed.csv
   ```
   This rejects changed columns, values outside the allowed lists, missing sources or quotes, and unexplained differences.
2. Updates each record's dates, sources and review status, and re-runs the effective-date check.
3. Lists every evaluation whose inputs changed. Those are re-run as registered follow-up evaluations (a new evaluation, not an overwrite), with the confounders you found written into their plans before any results are seen.

## Optional. Compare with published research (Cowork's own role)

```text
For the evaluations in due_diligence.md section 1 (fuel price reporting, e-conveyancing, retail trading hours, childcare NQF, heavy vehicle national law, taxi and ride-share reforms, legal profession uniform law, container deposits, retail energy deregulation), find published evaluations of the same or closely similar Australian reforms: peer-reviewed papers, Productivity Commission, ACCC, state regulator or Treasury reports. For each, give the full citation and a URL you opened, the outcome measured, the estimated effect with its units, and how it compares with ours (direction and size). Do not report any number you did not read in the source. Put the result in a new file, literature_comparison.md.
```
