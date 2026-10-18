# ALICIA: Australian Legislation Impact on Competition Industry Analysis

A public-data toolkit for evaluating how Australian legislation and regulation affect competition (the Python package and command are `alicia`; it was called `regimpact`, then `alcia` (ALCIA), until 18 October 2026). It is part of the econometric foundation scoped in [`docs/econometric_foundation_scoping.md`](../docs/econometric_foundation_scoping.md). The evaluation design it serves is [`docs/impact_evaluation_design.md`](../docs/impact_evaluation_design.md).

> Unofficial research tooling. Not an Australian Government product.

## Status (18 October 2026)

| Part | What it does | Status |
|---|---|---|
| Register of changes | One validated record per regulatory change per jurisdiction, in [`regulation-register/`](../regulation-register/) | 69 draft records, none reviewed yet |
| Effective-date gatherer | Reads assent, commencement and version dates from the legislation registers and checks each record's effective date against them | Commonwealth, Qld, Tas, ACT, WA and NT automated; Victoria version dates only; NSW and SA blocked (sourced dates only) |
| Timing | Maps a commencement onto financial years and quarters, with the partly exposed first period | Done |
| Evaluability screen | Rates each change high, medium or low for public-data evaluation, with reasons | Done (rules stated in `menu/screen.py`) |
| Menu explorer | One interactive HTML page: search and filters (including **Evaluated**), list, adoption timeline, record details, and a **Results** view. Each evaluation opens with plain-language **key insights**, then **in depth**: what was done, the econometric model (equations, terms, estimand, identifying assumption, inference), estimated effects and year-by-year charts | Done |
| Evaluation results | One validated file per evaluation in [`regulation-register/evaluations/`](../regulation-register/evaluations/), written from the analysis outputs by each analysis's builder script and checked against them by the tests | 10 evaluations covering 24 records (the Perth weeknight change and the childcare NQF re-evaluated with new data) |
| Outcome panels | CABEE entry and exit by ANZSIC class, state and size (2007-08 to 2024-25, 15 releases stitched); CPI by capital city (ABS Data API); state retail output and pay per worker | Done |
| Data pipeline | Connectors that write one common panel format, sorted by ANZSIC code and place: Retail Trade (monthly, class or subgroup × state), Labour Force EQ06 (employment and hours, group × state, quarterly), Data by Region (division × SA2 and LGA), ABN Bulk Extract and ASIC registers (monthly, postcode, industry inferred from names), City of Melbourne CLUE (class × small area), postcode-to-ASGS concordance; a coverage catalogue that matches every record to the finest data available ([feasibility note](../docs/data_pipeline_feasibility.md)) | Built; Internet Vacancy Index is a parser for hand-downloaded files (site not reachable here) |
| Estimators | Two-way fixed effects, event study, blinding, comparison-state and industry placebos, planted-effect simulations (`evaluate/did.py`); stacked difference-in-differences for several or staggered treated states (`evaluate/stacked.py`); the on-off design for one late jurisdiction (`evaluate/stagger.py`) | Done |
| Macroeconomic controls (forward plan Phase 1) | State Accounts GVA by division × state (FY1990–2025); state final demand and household consumption; Labour Force; population; Wage Price Index; building approvals; national GVA by division; Business Indicators; RBA commodity prices. Written to `data/processed/controls/` and kept out of the outcome catalogue (`pipeline/controls.py`, `pipeline/abs_state_accounts.py`) | Done |
| Panel estimators (forward plan Phase 2) | Saturated state × industry, industry × period and state × period fixed effects; clustered errors; restricted wild cluster bootstrap; imputation (Borusyak, Jaravel and Spiess); Callaway–Sant'Anna (doubly robust); synthetic DiD and synthetic control; generalised synthetic control; matrix completion; conformal and placebo randomization inference; Rambachan–Roth sensitivity bounds; shift-share and measured controls (`evaluate/panel.py`, `synth.py`, `cs.py`, `honest.py`, `covariates.py`; [methods note](../docs/methods_panel_estimators.md)) | Built and tested on simulations; R cross-check written, not yet run (deferred) |
| Power study (forward plan Phase 3) | Blinded: for each evaluable reform, the no-effect spread and smallest detectable effect of each estimator layer on business entry and exit rates, from the same placebo industries (`analyses/power_study/`; [results](../docs/power_study.md)) | First run done: industry × year effects cut the no-effect spread by 28–77% for most reforms; state controls barely change it |
| Website | `alicia site` builds the legislation menu plus **State and industry growth** (GSP; GVA, employment and business entry and exit by division × state) and **Economic conditions** (the control series) | Done; published by the Pages workflow on merge to main |
| First case | Perth trading-hours deregulation (2010, 2012): blinded robustness review, pre-analysis plan and results ([review](../docs/robustness_review_wa_trading_hours.md), [plan](../docs/pap_wa_trading_hours.md), [results](../docs/results_wa_trading_hours.md)) | Done: no detectable effect on entry or exit; grade Moderate |
| High-evaluability batch | The other 16 high-rated records as seven reforms, one plan, stacked difference-in-differences ([plan](../docs/pap_high_evaluability.md), [results](../docs/results_high_evaluability.md)) | Done: no detectable effects; three not identified |
| Perth weeknight re-evaluation | The 2010 weeknight step alone, with business counts by place (Perth vs regional WA), monthly turnover and hours ([plan](../docs/pap_wa_weeknight_2010.md), [results](../docs/results_wa_weeknight_2010.md)) | Done: no detectable effect; grade Moderate |
| NQF in WA | The National Quality Framework around WA's seven-month delay, with the on-off design (`evaluate/stagger.py`): monthly childcare exits and entries (ABN), child care prices (CPI), employment ([plan](../docs/pap_childcare_nqf_wa.md), [results](../docs/results_childcare_nqf_wa.md)) | Done: no detectable early effect; grade Moderate |

## Setup

Requires Python 3.11 or later and [uv](https://docs.astral.sh/uv/).

```bash
cd alicia
uv sync
uv run pytest              # offline tests (116)
uv run ruff check src tests scripts analyses
uv run python analyses/wa_trading_hours/design_review.py   # blinded design review (downloads ABS data on first run)
uv run python analyses/wa_trading_hours/estimate.py        # registered estimation (--blind for the dry run)
uv run python analyses/wa_trading_hours/posthoc.py         # checks added after unblinding (not pre-registered)
uv run python analyses/wa_trading_hours/figure.py          # event-study figure for the results
uv run python analyses/wa_trading_hours/evaluation.py      # write the register's evaluation file from the outputs
uv run python analyses/high_evaluability/run.py --blind    # batch design stage (outcomes hidden); without --blind: the registered run
uv run python analyses/high_evaluability/evaluations.py    # batch evaluation files
uv run python analyses/wa_weeknight_2010/design_review.py # weeknight re-evaluation: blinded design stage
uv run python analyses/wa_weeknight_2010/estimate.py      # registered run (--blind for the dry run)
uv run python analyses/wa_weeknight_2010/evaluation.py    # its evaluation file
uv run python analyses/childcare_nqf_wa/design_review.py  # NQF in WA: blinded design stage
uv run python analyses/childcare_nqf_wa/estimate.py       # registered run (--blind for the dry run)
uv run python analyses/childcare_nqf_wa/paths.py          # display paths, then evaluation.py
```

## Commands

```bash
uv run alicia validate                    # check every register record (schema, ANZSIC codes and names, CPI classes) and evaluation
uv run alicia menu                        # list changes with their evaluability rating
uv run alicia menu --jurisdiction nsw --direction weakening
uv run alicia menu --industry 4623        # ANZSIC code or prefix
uv run alicia show nsw-rideshare-2015     # one record in full, with its screen
uv run alicia families                    # multi-jurisdiction reforms in date order
uv run alicia dates cth-uct-penalties-2023      # effective date, checked against the register
uv run alicia dates --all --json > ../regulation-register/reports/effective_dates_YYYY-MM-DD.json
uv run alicia dates --all --offline       # sourced dates and timing only, no network
uv run alicia explorer -o menu.html --dates ../regulation-register/reports/effective_dates_2026-10-15.json
uv run alicia explorer -o menu.html --standalone   # full HTML document for opening locally
uv run alicia site -o ../site --dates ../regulation-register/reports/effective_dates_2026-10-15.json   # menu + growth + conditions pages
uv run alicia methods -o ../docs/evaluation_methods.md   # key insights and methods of every evaluation, as Markdown
uv run alicia pipeline build              # build every outcome panel (downloads ~1.5 GB on first run, mostly the ABN extract)
uv run alicia pipeline build abs_lfs asic  # or named sources; see BUILDERS in cli.py
uv run alicia pipeline build abs_state_accounts controls   # State Accounts and the macroeconomic controls
uv run python analyses/panel_crosscheck/write_reference.py # reference panel for analysis/crosscheck_panel_estimators.R
uv run python analyses/power_study/run.py                   # Phase 3 power study (blinded; about 20 minutes)
uv run alicia pipeline catalogue          # re-summarise the panels in data/processed/catalogue.json
uv run alicia data nsw-lockout-2014       # which panels can measure a change, at what industry level and place
```

`alicia dates` reports, for each change:

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

Requests carry a descriptive User-Agent, are spaced per host, are retried on timeouts and server errors, and are cached in `alicia/.cache/` for seven days (not committed). See [`SOURCES.md`](SOURCES.md) for licences and attribution.

## Layout

```
alicia/
  src/alicia/
    register/      schema.py (record model), catalogue.py (load, filter, families), evaluation.py (results model)
    legislation/   frl.py (Commonwealth), states.py (states and territories), gather.py (reconcile),
                   adapters.py (routing), http.py (polite fetching), cache.py, text.py (dates, Word tables)
    menu/          screen.py (evaluability), explorer.py + templates/explorer.html (the menu page),
                   growth.py + templates/growth.html, conditions.html, site.css, charts.js (summary pages, `alicia site`)
    outcomes/      cabee.py (entries and exits), abs_series.py (ABS workbooks, CPI Data API), productivity.py
    pipeline/      schema.py (common panel format), store.py (raw, processed, manifests), coverage.py (catalogue and
                   matching to records), sources.py (registry), one module per connector (abs_cabee, abs_retail,
                   abs_lfs, abs_regional, geo, abr_abn, asic, clue, jsa_ivi, abs_state_accounts), controls.py
                   (macroeconomic controls), names.py (industry from names), concord.py (Retail Trade groupings),
                   abs_api.py (ABS Data API client), abs_tsw.py (ABS time series workbooks)
    evaluate/      did.py (single-treated-unit DiD, placebos, simulations), stacked.py (several or staggered treated units),
                   stagger.py (one late jurisdiction: the on-off design), panel.py (saturated fixed effects, wild
                   cluster bootstrap, imputation, randomization inference), covariates.py (measured state controls)
    timing.py      financial years and quarters
    anzsic.py, cpi.py, data/   bundled ABS classifications (CC BY 4.0)
    cli.py
  analyses/        one folder per case: design review code and results (wa_trading_hours/); panel_crosscheck/ writes
                   the reference panel for the R cross-check; power_study/ (Phase 3, blinded)
  (panels are written to ../data/processed/<source>/, raw downloads to ../data/raw/<source>/, manifests to ../data/manifests/)
  scripts/         regenerate bundled data; record test fixtures; import desk-research drafts; export the schema
  tests/           offline tests; fixtures are real register responses
```

## Ground rules

- **No invented data.** Every date in a record has a source URL. Test records are labelled illustrative.
- **Draft until reviewed.** Records from desk research stay `draft` until a person has checked them.
- **Hypotheses, not findings.** The direction (enhancing or weakening) is what the evaluation tests.
- **Public data only.** No BLADE microdata, and no confidential proposals in the register.

Decisions are logged in [`DECISIONS.md`](DECISIONS.md).
