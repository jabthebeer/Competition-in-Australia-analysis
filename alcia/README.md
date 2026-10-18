# ALCIA: Analysis of Legislation Impact on Competition in Australia

A public-data toolkit for evaluating how Australian legislation and regulation affect competition (the Python package and command are `alcia`; it was called `regimpact` until 18 October 2026). It is part of the econometric foundation scoped in [`docs/econometric_foundation_scoping.md`](../docs/econometric_foundation_scoping.md). The evaluation design it serves is [`docs/impact_evaluation_design.md`](../docs/impact_evaluation_design.md).

> Unofficial research tooling. Not an Australian Government product.

## Status (15 October 2026)

| Part | What it does | Status |
|---|---|---|
| Register of changes | One validated record per regulatory change per jurisdiction, in [`regulation-register/`](../regulation-register/) | 69 draft records, none reviewed yet |
| Effective-date gatherer | Reads assent, commencement and version dates from the legislation registers and checks each record's effective date against them | Commonwealth, Qld, Tas, ACT, WA and NT automated; Victoria version dates only; NSW and SA blocked (sourced dates only) |
| Timing | Maps a commencement onto financial years and quarters, with the partly exposed first period | Done |
| Evaluability screen | Rates each change high, medium or low for public-data evaluation, with reasons | Done (rules stated in `menu/screen.py`) |
| Menu explorer | One interactive HTML page: search and filters (including **Evaluated**), list, adoption timeline, record details, and a **Results** view with each evaluation's verdict, grade, estimated effects and year-by-year charts | Done |
| Evaluation results | One validated file per evaluation in [`regulation-register/evaluations/`](../regulation-register/evaluations/), written from the analysis outputs by each analysis's builder script and checked against them by the tests | 8 evaluations covering 24 records |
| Outcome panels | CABEE entry and exit by ANZSIC class, state and size (2007-08 to 2019-20, 10 releases stitched); CPI by capital city (ABS Data API); state retail output and pay per worker | Done for the first case |
| Estimators | Two-way fixed effects, event study, blinding, comparison-state and industry placebos, planted-effect simulations (`evaluate/did.py`) | Done for single-treated-state designs; staggered estimators not started |
| First case | Perth trading-hours deregulation (2010, 2012): blinded robustness review, pre-analysis plan and results ([review](../docs/robustness_review_wa_trading_hours.md), [plan](../docs/pap_wa_trading_hours.md), [results](../docs/results_wa_trading_hours.md)) | Done: no detectable effect on entry or exit; grade Moderate |
| High-evaluability batch | The other 16 high-rated records as seven reforms, one plan, stacked difference-in-differences ([plan](../docs/pap_high_evaluability.md), [results](../docs/results_high_evaluability.md)) | Done: no detectable effects; three not identified |

## Setup

Requires Python 3.11 or later and [uv](https://docs.astral.sh/uv/).

```bash
cd alcia
uv sync
uv run pytest              # offline tests (84)
uv run ruff check src tests scripts analyses
uv run python analyses/wa_trading_hours/design_review.py   # blinded design review (downloads ABS data on first run)
uv run python analyses/wa_trading_hours/estimate.py        # registered estimation (--blind for the dry run)
uv run python analyses/wa_trading_hours/posthoc.py         # checks added after unblinding (not pre-registered)
uv run python analyses/wa_trading_hours/figure.py          # event-study figure for the results
uv run python analyses/wa_trading_hours/evaluation.py      # write the register's evaluation file from the outputs
uv run python analyses/high_evaluability/run.py --blind    # batch design stage (outcomes hidden); without --blind: the registered run
uv run python analyses/high_evaluability/evaluations.py    # batch evaluation files
```

## Commands

```bash
uv run alcia validate                    # check every register record (schema, ANZSIC codes and names, CPI classes) and evaluation
uv run alcia menu                        # list changes with their evaluability rating
uv run alcia menu --jurisdiction nsw --direction weakening
uv run alcia menu --industry 4623        # ANZSIC code or prefix
uv run alcia show nsw-rideshare-2015     # one record in full, with its screen
uv run alcia families                    # multi-jurisdiction reforms in date order
uv run alcia dates cth-uct-penalties-2023      # effective date, checked against the register
uv run alcia dates --all --json > ../regulation-register/reports/effective_dates_YYYY-MM-DD.json
uv run alcia dates --all --offline       # sourced dates and timing only, no network
uv run alcia explorer -o menu.html --dates ../regulation-register/reports/effective_dates_2026-10-15.json
uv run alcia explorer -o menu.html --standalone   # full HTML document for opening locally
```

`alcia dates` reports, for each change:

- the effective date (the record's primary commencement);
- the first exposed and first full financial year, with the share of the first year exposed;
- the first full quarter;
- a status:
  - **confirmed**: a register date matches;
  - **differs**: the register states commencement dates and none matches;
  - **unconfirmed**: nothing readable to compare;
  - **not-commenced**;
- every issue found, for example an assent date that disagrees with the register.

## How effective dates are read

| Register | Method | Notes |
|---|---|---|
| Commonwealth (legislation.gov.au) | REST API: title record (assent or making date, registration, repeal); the s 2 commencement table in the as-made Word document; for an amending law, the start of each compilation of the principal law that cites it | An amending Act's effective date is read per schedule, from the principal's compilations |
| Queensland | As-made XML; for a principal Act, its legislative-history XML | Amending Acts are checked through their principal Act |
| Tasmania | Amendment commencement table (JSON) searched by title | |
| ACT | Landing page: notified date and commencement table | 10-second spacing (robots.txt) |
| WA | Act page (assent) and "History of this Act" table | Commencement free text parsed per segment |
| NT | As-assented page | Needs the as-assented link in the record |
| Victoria | In-force version dates | Assent and commencement are in documents the site asks robots not to fetch |
| NSW, SA | Not read | Both block automated requests; records rely on sourced dates |

Requests carry a descriptive User-Agent, are spaced per host, are retried on timeouts and server errors, and are cached in `alcia/.cache/` for seven days (not committed). See [`SOURCES.md`](SOURCES.md) for licences and attribution.

## Layout

```
alcia/
  src/alcia/
    register/      schema.py (record model), catalogue.py (load, filter, families), evaluation.py (results model)
    legislation/   frl.py (Commonwealth), states.py (states and territories), gather.py (reconcile),
                   adapters.py (routing), http.py (polite fetching), cache.py, text.py (dates, Word tables)
    menu/          screen.py (evaluability), explorer.py + templates/explorer.html (the page)
    outcomes/      cabee.py (entries and exits), abs_series.py (ABS workbooks, CPI Data API), productivity.py
    evaluate/      did.py (single-treated-unit DiD, placebos, simulations), stacked.py (several or staggered treated units)
    timing.py      financial years and quarters
    anzsic.py, cpi.py, data/   bundled ABS classifications (CC BY 4.0)
    cli.py
  analyses/        one folder per case: design review code and results (wa_trading_hours/)
  data/processed/  CABEE panel built by `outcomes.cabee.build()` (CC BY 4.0, ABS; manifest has release URLs and SHA-256)
  scripts/         regenerate bundled data; record test fixtures; import desk-research drafts; export the schema
  tests/           offline tests; fixtures are real register responses
```

## Ground rules

- **No invented data.** Every date in a record has a source URL. Test records are labelled illustrative.
- **Draft until reviewed.** Records from desk research stay `draft` until a person has checked them.
- **Hypotheses, not findings.** The direction (enhancing or weakening) is what the evaluation tests.
- **Public data only.** No BLADE microdata, and no confidential proposals in the register.

Decisions are logged in [`DECISIONS.md`](DECISIONS.md).
