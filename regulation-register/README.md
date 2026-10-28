# Register of productivity-impacting factors

Commonwealth, state and territory reforms, existing regulatory settings and non-legislative barriers that affect productivity and competition in Australia, each marked against the [productivity impact framework](../docs/productivity_framework.md). One JSON file per item per jurisdiction in `records/`, validated against `schema/change-record.schema.json` (generated from `alicia/src/alicia/register/schema.py`).

Browse it with the legislation menu (`uv run alicia explorer` in `alicia/`, or the website) or the command line (`uv run alicia menu`).

> **Status (28 October 2026):** 234 records, all `draft`: 173 reforms, 54 existing settings and 7 non-legislative barriers. Every record has a framework assessment (28 October 2026). The reforms were first chosen because they could be evaluated with public data (102 added on 18 October from the [legislation gap scan](../docs/legislation_gap_scan.md)); the settings and barriers were added after the [framework review](../docs/register_review_framework.md). Records not yet in force have no commencement. Everything was compiled by AI-assisted desk research from the sources each record cites and has not yet been checked by a person. The `direction` and the assessment are judgements about likely effects, not findings.

## What a record holds

| Field | Meaning |
|---|---|
| `id`, `family` | `jurisdiction-topic-year` (the year may be left out for a setting or barrier); `family` groups the same reform or setting across jurisdictions |
| `kind` | `reform` (a change: in force, passed or proposed), `setting` (a law, regulation or government policy already in place) or `barrier` (not a law or policy: market structure, conduct or practice) |
| `instruments` | Acts, regulations, codes or policies, with register URL or ID and role (principal, amending, regulation, code, other). Required for reforms and settings; a barrier may have none |
| `dates` | Announced, assent or made, and commencements. **Every date has a source URL.** One commencement may be marked `primary`: the date the competition-relevant change took effect (otherwise the earliest is used) |
| `direction`, `direction_rationale`, `direction_sources` | Hypothesised effect on competition: enhancing, weakening, mixed or unclear |
| `channels` | OIA competition-guidance categories (July 2026): barriers; number or type of businesses; ability or incentive to compete; prices or market share; consumer choice |
| `industries` | ANZSIC 2006 codes (validated against the ABS list), each direct or indirect. May be empty only for an item assessed as economy-wide |
| `comparison`, `confounders`, `price_series` | For the archived econometric evaluations: how a comparison group could be formed; threats; matching CPI expenditure classes. Optional |
| `verified`, `review` | Whether dates were verified against official sources; whether a person has reviewed the record |
| `assessment` | The framework assessment: a plain-English `summary`; `marks`, each a driver, a mark from −2 to +2 (never 0: unmarked drivers are 0) and a reason; the `main_driver` (a driver with the largest mark, either way); `reach`; `confidence` and an optional note; extra `evidence` URLs; the `framework` version and `assessed_on` date. The overall mark is the sum of the marks |

## Coding protocol

1. **One record per jurisdiction.** A national scheme adopted by states on different dates gets one record per state, sharing a `family`.
2. **Sources for every date.** Prefer the legislation register, then the gazette, then official government or regulator pages. A secondary source (news, law firm) sets `verified.dates = false` and is explained in `verified.notes`.
3. **Primary commencement.** When provisions commence on several dates, mark the one that changes competition conditions as `primary`, and say why in `review.notes`.
4. **Industries.** List only industries the change directly regulates as `direct`. Use the most specific ANZSIC level that fits (class, then group).
5. **Direction.** State the mechanism in one or two sentences and cite the basis (Productivity Commission, ACCC, OECD, research).
6. **Assessment.** Mark the item against the [framework](../docs/productivity_framework.md): only drivers with a material effect, each with a one-line reason; follow its overlap rules; mark a reform against what it replaced and a setting or barrier against the market without it. Rate reach and confidence, and write a two- or three-sentence summary a non-specialist can follow.
7. **Check dates.** Run `uv run alicia dates <id>`. Resolve or explain any "differs" status or assent mismatch.
8. **Review.** A person who has checked the record sets `review` to `{"status": "reviewed", "by": "<name>", "on": "<date>"}`. `uv run alicia validate` must pass.

## Evaluations

> **Archived (28 October 2026).** The evaluation programme was paused on 22 October 2026; the evaluations stay in this folder and on the website's econometric archive, unchanged.

A record's `direction` is a hypothesis. What an evaluation found is kept separately, in `evaluations/<id>.json`, validated against `schema/evaluation.schema.json` (generated from `alicia/src/alicia/register/evaluation.py`). One evaluation can cover several records, for example two steps of one reform.

| Field | Meaning |
|---|---|
| `records`, `family` | The register records the evaluation covers (each must exist; one evaluation per record) |
| `verdict`, `finding_label`, `grade`, `grade_reason` | The pre-registered decision rule's verdict (supports enhancing, supports weakening, inconclusive), a short label for the menu, and the credibility grade (Strong, Moderate, Weak, Not identified) |
| `headline`, `category_summaries` | Plain-English result, and one line each for competition, prices, and productivity and pay |
| `outcomes` | Each estimate with its unit, 90% interval, the range the estimator gives where there was no reform (placebos), p-value, smallest detectable effect, finding, role and whether it was pre-registered |
| `event_studies` | Year-by-year estimates with their placebo bands, for the charts |
| `caveats`, `documents` | Limits to read alongside the result; the plan, results and code in this repository |

**Evaluation files are generated, never typed by hand.** Each case's `alicia/analyses/<case>/evaluation.py` writes the file from the analysis outputs, and `alicia/tests/test_evaluation.py` checks the numbers against them. The econometric archive page reads these files to show the **Evaluated** filter and the **Results** view; the legislation menu links each evaluated record to its archived evaluation.

## Reports

`reports/effective_dates_<date>.json` is the output of `alicia dates --all --json` on that date: each record's effective date, timing, register status and issues, with what each register returned. Federal Register content in these reports is CC BY 4.0: "Sourced from the Federal Register of Legislation" at each entry's `retrieved_at` date.

Latest run (18 October 2026, `effective_dates_2026-10-18.json`, 171 records):

| Status | Records | Meaning |
|---|---|---|
| confirmed | 38 | A register date matches the effective date |
| differs | 7 | The register's commencement dates don't include the effective date. In each case the rule applied later than the instrument commenced, and the record explains it: default market offer (caps from 1 July 2019), card surcharging standard, open banking phasing, major bank levy, R&D Tax Incentive income years, Same Job Same Pay orders, super performance test results |
| unconfirmed | 123 | Nothing readable to check against: NSW and SA registers block automated requests, and many new records are programs, protocols or guidelines with no register entry |
| not-commenced | 3 | No commencement: the non-compete ban and the National Competition Policy (pre-registration candidates), and Queensland's non-adoption of automatic mutual recognition |
