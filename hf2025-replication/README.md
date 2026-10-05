# Replicating and extending Hambur & Freestone (2025)

This project replicates and extends Hambur, J. and Freestone, O. (2025), "How Costly are Mark-ups in Australia? The Effect of Declining Competition on Misallocation and Productivity", RBA RDP 2025-05. That paper calibrates the Edmond, Midrigan & Xu (2023, *JPE*) heterogeneous-firm GE model to ABS BLADE data for the mid-2000s and mid-2010s.

We have no BLADE access. The plan is to:

1. reproduce the model results from the paper's published targets;
2. test how sensitive they are;
3. rebuild calibration targets from public data, and extend the analysis to the latest year.

Replication results (from the paper's own targets) and extension results (from public-data targets) are always labelled separately.

## Status

| Phase | Status |
|---|---|
| Start: read the papers, summarise the model, propose a Phase 1 plan | Done. H&F and EMX read; H&F's replication code found and inspected (`notes/model_summary.md` §4). Revised plan: `notes/phase1_plan.md`. **Awaiting approval.** |
| 1. Reproduce model results | Not started. Smoke test: H&F's code runs in GNU Octave 8.4 |
| 2. Sensitivity and channel decomposition | Not started |
| 3. Public-data targets, 2004 to latest | Not started. Raw ABS/ATO data fetched (`data/raw/SOURCES.md`). Annual-report agent pilot done (`notes/annual_report_pilot_results.md`) |
| 4. Extension to the present | Not started |

## Layout

```
literature/       Source papers (only openly licensed ones are committed)
notes/            Model summary, plans
DECISIONS.md      Assumption and deviation log
data/raw/         Untouched downloads + SOURCES.md
data/processed/   Cleaned data
src/model/        EMX model: Kimball monopolistic competition and Cournot oligopoly
src/targets/      Builds calibration targets from data
src/analysis/     Calibration, counterfactuals, sensitivity
tests/            Unit tests
output/           tables/, figures/, report.md
```

## How to run

The full pipeline is not yet available; the single entry point will be `make all`. What exists now:

```
uv venv .venv --python 3.11 && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python src/fetch_raw.py      # downloads raw inputs, logs them in data/raw/MANIFEST.csv
sudo apt-get install --no-install-recommends octave   # GNU Octave 8.4 (Ubuntu 24.04)
```
