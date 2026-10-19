# Methods note: specification files and the runner (forward plan Phase 4)

**Date:** 18 October 2026. **Status:** done. The four earlier analyses are written as specifications, their code reads its design constants from them, and their outputs reproduce byte for byte (section 5). The Phase 5 evaluations were written as specifications first and run by one generic engine (section 3).

**Code:** `alicia/src/alicia/runner/` (`spec.py`, the format; `run.py`, the runner). **Specifications:** `alicia/specs/<id>.json`. **Tests:** `alicia/tests/test_runner.py`.

## 1. What a specification holds

One JSON file per evaluation design, validated on load (pydantic, like register records):

| Field | Holds |
|---|---|
| `id`, `title`, `analysis`, `plan`, `registered_on`, `follows` | Identity; the analysis folder; the pre-analysis plan; the earlier evaluation it revisits |
| `records`, `evaluations`, `hypothesis` | Register records covered; evaluation files written; the direction tested |
| `outcomes` | Per outcome: role (primary, secondary, descriptive), source panel, measure, frequency, unit, industries, cohorts or event window, estimator, controls, placebo pools, pre-registered or not |
| `stages` | Ordered stages: design (blinded), dry run (blinded), registered estimate, post-hoc or derived outputs, evaluation file. Each names its script, arguments and the files it writes |
| `parameters` | The analysis's own design constants (states, classes, seeds, windows, size rules) |
| `cases` | For a batch: one entry per reform (classes, cohorts, price specification, grade cap) |

The analysis modules read `parameters`, `outcomes` and `cases` from the file, so the specification is the single place a design is written down. Before this change the same constants lived in each analysis's `spec.py`, `cases.py` or script header.

## 2. The runner

```
alicia spec list                       # specifications and their stages
alicia spec show <id>                  # the full specification
alicia spec check <id>                 # its records and evaluation files exist
alicia spec run <id> [--stage NAME]    # run stages in order; report each output as identical, changed or created
```

- Each stage runs as a separate process from `alicia/`, exactly as the analysis documents it.
- Before a stage runs, the runner records each output's SHA-256; afterwards it reports the output as identical, changed or created. `REPRODUCED` means every output is byte-identical.
- **Pre-registration guard.** The registered estimate stage runs only if every design and dry-run output is committed and unmodified. A design therefore cannot change after its estimate has been seen without the change showing in the history. `--allow-uncommitted-design` overrides this for checks only.

## 3. The specifications so far

| Specification | Analysis | Stages | Evaluation files |
|---|---|---|---|
| `wa-trading-hours-2010-2012` | `wa_trading_hours` | design, dry run, estimate, post-hoc (not pre-registered), evaluation | 1 |
| `high-evaluability-batch` | `high_evaluability` | design (blinded), estimate, evaluation | 7 |
| `wa-trading-hours-weeknight-2010-new-data` | `wa_weeknight_2010` | design, dry run, estimate, evaluation | 1 |
| `childcare-nqf-wa-delay-2012` | `childcare_nqf_wa` | design, dry run, estimate, paths, evaluation | 1 |
| `phase5-reevaluations` | `phase5` | design (blinded), dry run, estimate, post-hoc, confounder scan and robustness (not pre-registered), table-stats, evaluation | 8 |
| `phase5-new-families` | `phase5` | design (blinded), dry run, estimate, confounder scan and robustness (not pre-registered), table-stats, evaluation | 2 |

**New specifications** should add the confounder scan as a blind design-stage output (`confounders.py --spec <id> --blind`, writing `confounders_blind.json`), so that concurrent changes are listed in the plan before the registered run ([`confounder_scan.md`](confounder_scan.md) §3).

**The Phase 5 specifications are generic.** Their `cases` hold everything a design needs: records, cohorts, classes or CPI class, windows, the registered layer, check layers, placebo pools and grade caps. `analyses/phase5/run.py` builds every design from those cases alone, with no per-reform code. A new evaluation needs only a case in a specification and a plan.

Each re-evaluation case names the earlier evaluation it `follows` and `supersedes`. The evaluation stage writes those fields, so the earlier file is archived without being changed.

## 4. Reproduction check (18 October 2026)

1. **Baseline.** Before any constant moved, every stage of the four analyses was re-run in order (17 stages) and the outputs compared with the committed files with `git status`: all byte-identical. The batch's case table and constants had already moved to its specification when its stages ran, so for the batch this run is also the check of the change.
2. **Equal objects.** For each analysis, every constant read from the specification was compared with the value it replaced, including its type (e.g. a tuple stays a tuple, a set stays a set): all equal.
3. **Runner.** Each specification was then run end to end with `alicia spec run <id>`, with the code reading its constants from the file.

## 5. Results

| Specification | Stages run | Outputs | Result |
|---|---|---|---|
| `wa-trading-hours-2010-2012` | design, dry run, estimate, post-hoc, evaluation | 5 | **Identical** |
| `wa-trading-hours-weeknight-2010-new-data` | design, dry run, estimate, evaluation | 4 | **Identical** |
| `childcare-nqf-wa-delay-2012` | design, dry run, estimate, paths, evaluation | 5 | **Identical** |
| `high-evaluability-batch` | design, estimate, evaluation | 9 (7 evaluation files) | **Identical** |

Every evaluation file in `regulation-register/evaluations/` is reproduced byte for byte from its specification.

## 6. Limits and next steps

- **Bespoke scripts remain for the four earlier analyses.** Phase 5 uses the generic engine; the earlier analyses keep their own scripts so that their outputs still reproduce byte for byte.
- **Estimator comparison.** Phase 5 evaluation files carry every layer side by side (`estimators`): two-way, cell and state × year, saturated, measured controls, imputation, synthetic DiD and generalised synthetic control, with the registered layer marked (forward plan §5.3). Matrix completion and sensitivity bounds are not yet in the comparison.
- **Not every constant has moved.** Labels, chart markers and output wording stay in the builder scripts.
