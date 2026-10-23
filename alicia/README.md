# ALICIA: Australian Legislation Impact on Competition Industry Analysis

A public-data toolkit for evaluating how Australian legislation and regulation affect competition (the Python package and command are `alicia`; it was called `regimpact`, then `alcia` (ALCIA), until 18 October 2026). It is part of the econometric foundation scoped in [`docs/econometric_foundation_scoping.md`](../docs/econometric_foundation_scoping.md). The evaluation design it serves is [`docs/impact_evaluation_design.md`](../docs/impact_evaluation_design.md).

> Unofficial research tooling. Not an Australian Government product.

## Status (22 October 2026)

**Change of direction (22 October 2026, E-75).** Retrospective evaluation is paused. The register and its hypotheses stay and become part of the product. The next build is a **Policy costing** tab on the website: a regulatory burden costing under the OIA framework, and a productivity and competition costing that turns a policy brief into productivity and GDP effects by channel, with ranges and sources ([plan](../docs/forward_plan_policy_costing.md)). Parked: a literature review for each register record ([P-1](../docs/parked_items.md)). Plan approved 22 October 2026 (E-77). **P0–P3 done**:<br>• the policy brief schema;<br>• the Policy costing tab on the website;<br>• the costing parameters (`alicia costing-params`, 16 sources, refreshed daily; [data dictionary](../docs/costing_parameters.md));<br>• the evidence library.

The table below is the state of the retrospective work when it was paused.

| Part | What it does | Status |
|---|---|---|
| Register of changes | One validated record per regulatory change per jurisdiction, in [`regulation-register/`](../regulation-register/) | 171 draft records (102 added from the [gap scan](../docs/legislation_gap_scan.md)), none reviewed yet |
| Effective-date gatherer | Reads assent, commencement and version dates from the legislation registers and checks each record's effective date against them | Commonwealth, Qld, Tas, ACT, WA and NT automated; Victoria version dates only; NSW and SA blocked (sourced dates only) |
| Timing | Maps a commencement onto financial years and quarters, with the partly exposed first period | Done |
| Evaluability screen | Rates each change high, medium or low for public-data evaluation, with reasons | Done (rules stated in `menu/screen.py`) |
| Menu explorer | One interactive HTML page: search and filters (including **Evaluated**), list, adoption timeline, record details, and a **Results** view. Each evaluation opens with plain-language **key insights**, then **in depth**: what was done, the econometric model (equations, terms, estimand, identifying assumption, inference), estimated effects and year-by-year charts. Each evaluation also has its own full-width page (`evaluation-<id>.html`), opened by double-clicking it or from its "Open as a page" link | Done |
| Evaluation results | One validated file per evaluation in [`regulation-register/evaluations/`](../regulation-register/evaluations/), written from the analysis outputs by each analysis's builder script and checked against them by the tests | 20 evaluations covering 34 records: 12 current, 8 archived (superseded by the Phase 5 re-evaluations, kept and shown in a folded section). The menu lists evaluations newest first. Every current evaluation has regression tables in the academic layout, on its page and in [`econometric_tables.md`](../docs/econometric_tables.md) and [`.tex`](../docs/econometric_tables.tex) (`alicia tables`) |
| Outcome panels | CABEE entry and exit by ANZSIC class, state and size (2007-08 to 2024-25, 15 releases stitched); CPI by capital city (ABS Data API); state retail output and pay per worker | Done |
| Data pipeline | Connectors that write one common panel format, sorted by ANZSIC code and place: Retail Trade (monthly, class or subgroup × state), Labour Force EQ06 (employment and hours, group × state, quarterly), Data by Region (division × SA2 and LGA), ABN Bulk Extract and ASIC registers (monthly, postcode, industry inferred from names), City of Melbourne CLUE (class × small area), postcode-to-ASGS concordance; a coverage catalogue that matches every record to the finest data available ([feasibility note](../docs/data_pipeline_feasibility.md)) | Built; Internet Vacancy Index is a parser for hand-downloaded files (site not reachable here) |
| Estimators | Two-way fixed effects, event study, blinding, comparison-state and industry placebos, planted-effect simulations (`evaluate/did.py`); stacked difference-in-differences for several or staggered treated states (`evaluate/stacked.py`); the on-off design for one late jurisdiction (`evaluate/stagger.py`) | Done |
| Macroeconomic controls (forward plan Phase 1) | State Accounts GVA by division × state (FY1990–2025); state final demand and household consumption; Labour Force; population; Wage Price Index; building approvals; national GVA by division; Business Indicators; RBA commodity prices. Written to `data/processed/controls/` and kept out of the outcome catalogue (`pipeline/controls.py`, `pipeline/abs_state_accounts.py`) | Done |
| Panel estimators (forward plan Phase 2) | Saturated state × industry, industry × period and state × period fixed effects; clustered errors; restricted wild cluster bootstrap; imputation (Borusyak, Jaravel and Spiess); Callaway–Sant'Anna (doubly robust); synthetic DiD and synthetic control; generalised synthetic control; matrix completion; conformal and placebo randomization inference; Rambachan–Roth sensitivity bounds; shift-share and measured controls (`evaluate/panel.py`, `synth.py`, `cs.py`, `honest.py`, `covariates.py`; [methods note](../docs/methods_panel_estimators.md)) | Built and tested on simulations; R cross-check written, not yet run (deferred) |
| Power study (forward plan Phase 3) | Blinded: for each evaluable reform, including the new families, the no-effect spread and smallest detectable effect of each estimator layer on business entry and exit rates (`run.py`) and on CPI prices by capital city (`prices.py`), under four placebo families: industries (or CPI classes), states, fake dates, and both (`analyses/power_study/`; [results](../docs/power_study.md)) | Done |
| Specification runner (forward plan Phase 4) | One JSON specification per evaluation in `specs/` (records, outcomes, cohorts or windows, estimators, placebo pools, stages, design constants), read by the analysis code; `alicia spec run` re-runs the stages and checks every output is byte-identical; the registered estimate runs only after the design is committed (`src/alicia/runner/`; [note](../docs/specification_runner.md)) | Done: the four earlier analyses and the two Phase 5 specifications |
| Website | `alicia site` builds the legislation menu plus **State and industry growth** (GSP; GVA, employment and business entry and exit by division × state) and **Economic conditions** (the control series). With `--costing`, it adds the **Policy costing** tab built from `regulatory-burden-tool/` (`npm run build:site`) | Done; published by the Pages workflow on merge to main and daily, after refreshing the costing data from the publishers' latest releases |
| First case | Perth trading-hours deregulation (2010, 2012): blinded robustness review, pre-analysis plan and results ([review](../docs/robustness_review_wa_trading_hours.md), [plan](../docs/pap_wa_trading_hours.md), [results](../docs/results_wa_trading_hours.md)) | Done: no detectable effect on entry or exit; grade Moderate |
| High-evaluability batch | The other 16 high-rated records as seven reforms, one plan, stacked difference-in-differences ([plan](../docs/pap_high_evaluability.md), [results](../docs/results_high_evaluability.md)) | Done: no detectable effects; three not identified |
| Perth weeknight re-evaluation | The 2010 weeknight step alone, with business counts by place (Perth vs regional WA), monthly turnover and hours ([plan](../docs/pap_wa_weeknight_2010.md), [results](../docs/results_wa_weeknight_2010.md)) | Done: no detectable effect; grade Moderate |
| Phase 5 re-evaluations and new families | One engine for every case in a specification (`analyses/phase5/`): the eight earlier evaluations re-run with the power study's layers and the latest data, and the first evaluations of fuel price reporting and e-conveyancing. Every estimator layer reported side by side; each re-evaluation supersedes and archives its earlier evaluation ([plan](../docs/pap_phase5.md), [results](../docs/results_phase5.md)) | Done: no detectable primary effects; three not identified; precision up 18–53%; a significant Victorian fares fall traced, after unblinding, to January 2015 public transport fare changes. Checked after unblinding (not pre-registered): a confounder scan and robustness variants ([scan](../docs/confounder_scan.md), [robustness](../docs/robustness_phase5.md)); the due-diligence plan is in [`due_diligence.md`](../docs/due_diligence.md) |
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
uv run python analyses/power_study/run.py                   # Phase 3 power study, business counts (blinded; about an hour)
uv run python analyses/power_study/prices.py                # Phase 3 power study, CPI prices (blinded)
uv run alicia spec list                   # evaluation specifications (specs/*.json)
uv run alicia spec run wa-trading-hours-weeknight-2010-new-data   # re-run every stage; check outputs are byte-identical
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
    runner/        spec.py (specification format), run.py (runs stages, checks outputs, pre-registration guard)
    timing.py      financial years and quarters
    anzsic.py, cpi.py, data/   bundled ABS classifications (CC BY 4.0)
    cli.py
  specs/           one JSON specification per evaluation (read by the analysis code and the runner)
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
