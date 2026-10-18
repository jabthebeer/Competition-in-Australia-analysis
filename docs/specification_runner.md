# Methods note: specification files and the runner (forward plan Phase 4)

**Date:** 18 October 2026. **Status:** started. The four existing analyses are written as specifications, their code reads its design constants from them, and their outputs reproduce byte for byte (section 5). New evaluations (Phase 5) will be written as specifications first.

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
| `high-evaluability-batch` | design, estimate, evaluation | 9 (7 evaluation files) | **Identical** (baseline run with the specification-driven code); runner run: see below |

Every evaluation file in `regulation-register/evaluations/` is reproduced byte for byte from its specification.

## 6. Limits and next steps

- **Bespoke scripts remain.** The estimators and outputs are still each analysis's own scripts; the runner drives them but does not yet build designs from the specification alone. Phase 5 specifications should use the shared estimators (`evaluate/panel.py`, `synth.py`, `cs.py`) through a generic stage, so that a new evaluation needs only a JSON file and a plan.
- **Estimator comparison not yet produced.** The forward plan (§5.3) asks every evaluation to show the estimate without controls, with fixed effects, with measured controls and with factor models side by side. That is a stage to add for Phase 5.
- **Not every constant has moved.** Labels, chart markers and output wording stay in the builder scripts.
