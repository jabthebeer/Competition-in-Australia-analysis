# Register of regulatory changes

Candidate Commonwealth, state and territory changes whose effects on competition could be evaluated with public data. One JSON file per change per jurisdiction in `records/`, validated against `schema/change-record.schema.json` (generated from `alicia/src/alicia/register/schema.py`).

Browse it with the menu explorer (`uv run alicia explorer` in `alicia/`) or the command line (`uv run alicia menu`).

> **Status (15 October 2026):** 69 records, all `draft`. They were compiled by AI-assisted desk research from the sources each record cites and have not yet been checked by a person. The `direction` of each change is a hypothesis to be tested.

## What a record holds

| Field | Meaning |
|---|---|
| `id`, `family` | `jurisdiction-topic-year`; `family` groups the same reform across jurisdictions (staggered adoption) |
| `instruments` | Acts, regulations or codes, with register URL or ID and role (principal, amending, regulation, code, other) |
| `dates` | Announced, assent or made, and commencements. **Every date has a source URL.** One commencement may be marked `primary`: the date the competition-relevant change took effect (otherwise the earliest is used) |
| `direction`, `direction_rationale`, `direction_sources` | Hypothesised effect on competition: enhancing, weakening, mixed or unclear |
| `channels` | OIA competition-guidance categories (July 2026): barriers; number or type of businesses; ability or incentive to compete; prices or market share; consumer choice |
| `industries` | ANZSIC 2006 codes (validated against the ABS list), each direct or indirect |
| `comparison`, `confounders`, `price_series` | How a comparison group could be formed; threats; matching CPI expenditure classes |
| `verified`, `review` | Whether dates were verified against official sources; whether a person has reviewed the record |

## Coding protocol

1. **One record per jurisdiction.** A national scheme adopted by states on different dates gets one record per state, sharing a `family`.
2. **Sources for every date.** Prefer the legislation register, then the gazette, then official government or regulator pages. A secondary source (news, law firm) sets `verified.dates = false` and is explained in `verified.notes`.
3. **Primary commencement.** When provisions commence on several dates, mark the one that changes competition conditions as `primary`, and say why in `review.notes`.
4. **Industries.** List only industries the change directly regulates as `direct`. Use the most specific ANZSIC level that fits (class, then group).
5. **Direction.** State the mechanism in one or two sentences and cite the basis (Productivity Commission, ACCC, OECD, research).
6. **Check dates.** Run `uv run alicia dates <id>`. Resolve or explain any "differs" status or assent mismatch.
7. **Review.** A person who has checked the record sets `review` to `{"status": "reviewed", "by": "<name>", "on": "<date>"}`. `uv run alicia validate` must pass.

## Evaluations

A record's `direction` is a hypothesis. What an evaluation found is kept separately, in `evaluations/<id>.json`, validated against `schema/evaluation.schema.json` (generated from `alicia/src/alicia/register/evaluation.py`). One evaluation can cover several records, for example two steps of one reform.

| Field | Meaning |
|---|---|
| `records`, `family` | The register records the evaluation covers (each must exist; one evaluation per record) |
| `verdict`, `finding_label`, `grade`, `grade_reason` | The pre-registered decision rule's verdict (supports enhancing, supports weakening, inconclusive), a short label for the menu, and the credibility grade (Strong, Moderate, Weak, Not identified) |
| `headline`, `category_summaries` | Plain-English result, and one line each for competition, prices, and productivity and pay |
| `outcomes` | Each estimate with its unit, 90% interval, the range the estimator gives where there was no reform (placebos), p-value, smallest detectable effect, finding, role and whether it was pre-registered |
| `event_studies` | Year-by-year estimates with their placebo bands, for the charts |
| `caveats`, `documents` | Limits to read alongside the result; the plan, results and code in this repository |

**Evaluation files are generated, never typed by hand.** Each case's `alicia/analyses/<case>/evaluation.py` writes the file from the analysis outputs, and `alicia/tests/test_evaluation.py` checks the numbers against them. The menu explorer reads these files to show the **Evaluated** filter and the **Results** view.

## Reports

`reports/effective_dates_<date>.json` is the output of `alicia dates --all --json` on that date: each record's effective date, timing, register status and issues, with what each register returned. Federal Register content in these reports is CC BY 4.0: "Sourced from the Federal Register of Legislation" at each entry's `retrieved_at` date.

Latest run (15 October 2026):

| Status | Records | Meaning |
|---|---|---|
| confirmed | 19 | A register date matches the effective date |
| differs | 1 | The register's commencement dates don't include the effective date. Default market offer: the instrument commenced on 5 April 2019, while the price caps applied from 1 July 2019 |
| unconfirmed | 48 | Nothing readable to check against (NSW and SA registers block automated requests; other records lack a register link) |
| not-commenced | 1 | |
