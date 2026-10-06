# Phase 1 implementation plan (revised 2026-10-05; awaiting approval)

Goal: reproduce H&F (2025) model results from the paper's own targets, and validate them against Tables 2, 4, 5, 7–11, B2–B3 and B5–B9.

**What changed since the first draft:** H&F's own model code is public. It is an edited copy of the EMX MATLAB code, together with their unrounded input moments, in the RBA supplementary zip. It runs in GNU Octave 8.4: one calibration-objective evaluation takes about 0.7 s, and the only change needed was wrapping the `fsolve` calls. So Phase 1 becomes **"run the authors' code, faithfully and reproducibly, then audit it"**, not a re-implementation. That is Path A of the first draft.

## 1. Engine

- **Source.** `data/raw/hf2025_supplementary/*.zip` (RBA, CC BY 4.0) is never edited. `make phase1` extracts it to `build/hf_model/` and applies **one patch file**, `src/model/octave_compat.patch`. Every hunk is listed and justified in DECISIONS.md.
- **Expected patch hunks (Octave or environment only; no economics changes):**
  1. Octave's `fsolve` does not accept the legacy extra-argument syntax, so `fsolve('findequilibrium', x0, options, args…)` becomes `fsolve(@(X) findequilibrium(X, args…), x0, options)`.
  2. Windows absolute paths are replaced with repo-relative paths.
  3. `xlsread('Inputs for model.xlsx', …)` is replaced by reading CSVs that a Python script exports once from that workbook, with values unchanged (`data/processed/hf_inputs_*.csv`).
  4. `writematrix` becomes `csvwrite` into `output/hf_model/`.
  5. Plotting and `groot` calls are removed or guarded, because Octave runs without a display.
  6. MATLAB-only `string`, `categorical` and `table` display code is replaced by `fprintf`.
- **Not needed for any table we reproduce:** Dynare (transitions are excluded, as in H&F) and the CompEcon `.mex` files (the `.m` versions are used).
- **Orchestration:** a thin Python wrapper (`src/analysis/run_hf.py`) calls `octave-cli`, collects the CSV outputs, and builds comparison tables.
- **Python re-implementation:** none for the main engine, per the language rule ("port only if Octave fails"). Independent Python code is limited to the unit-test identities and the comparison tables.

## 2. Runs

| Step | Script (H&F) | Reproduces | Notes |
|---|---|---|---|
| 1a | `Benchmark/start_calibration_main.m` as written (Nelder–Mead, MaxFunEvals 200) | Tables 2, B2, B5 | Faithful replication of their procedure |
| 1b | Same objective, solved to convergence: root-find the two free moments (markup, top-5% share), since $B/Y$ is matched exactly through $\phi$; tolerance 1e-10; multi-start | Tables 2, B2, B5, converged | Tests whether 1a converged. Explains the smoke-test miss for mid-2010s harmonic ($\xi$ = 4.04 gives top-5% = 0.638 vs 0.696) |
| 2 | `Benchmark/start_aggr.m`, report T3, using the 1a and the 1b parameters | Tables 4, 5, B3, B6 | Losses $= (1 - Z/Z^\ast)\times100$ |
| 3 | `start_aggr.m` T4 + `start_planner.m` (`efficient`) | Table 11; Table B9 first-best rows | Steady-state comparisons only |
| 4 | Uniform subsidy (`start_subsidy`) | Table B9 subsidy rows | **No `start_subsidy.m` exists in H&F's Benchmark folder.** Try EMX's `Benchmark/start_subsidy.asv`, then the Cournot version adapted. Report which one reproduces B9, or that none does |
| 5 | `start_calibration_div.m`, `start_div.m` | Tables 7, B7, B8 | Division-level results |
| 6 | `Cournot/start_calibration_agg.m`, `Cournot/start_olig.m` | Tables 9, 10 | Monte Carlo with `rng(0)`, Poisson firms per sector (mean about 3,440 / 3,884), weights 100 on markup and 10 on the regression. EMX report up to 12 h runtimes. **Timing test first**: if a full run is impractical, reduce the number of sectors and report simulation error across seeds |

## 3. Validation (output/report.md §1)

- Side-by-side tables for paper vs replication 1a vs replication 1b, with absolute and relative differences.
- Pass criterion for the calibrated parameters: ≤ 2% relative error. Anything above that is diagnosed.
- Every discrepancy goes in a numbered list. Already known:
  1. Table 10's value added (no input) column;
  2. Table B3's harmonic change rows;
  3. Table B1's garbled targets;
  4. Table B4's copied targets;
  5. Table B2's corner solution ($\xi = 2$);
  6. the text's "1.12" vs the table's 1.16;
  7. Table 2's mid-2010s harmonic parameters.

## 4. Unit tests (pytest; they call the Octave engine, plus independent Python algebra)

1. **CES limit.** Superelasticity $10^{-6}$ gives a misallocation loss below $10^{-6}$ and uniform markups at $\bar\sigma/(\bar\sigma-1)$.
2. **Planner dominance.** On a grid of $(\xi,\bar\sigma,\varepsilon/\bar\sigma)$:
   - static: $Z^\ast \ge Z$;
   - steady state: first-best welfare ≥ market welfare.
3. **Harmonic identities (toy example).** With 3–5 discrete firms in 2 sectors, eq. (10) harmonic means equal $Y/X$. Eqs (11)–(14) hold.
4. **Klenow–Willis algebra:**
   - $\Upsilon' = d\Upsilon/dq$;
   - $\Upsilon(1)=1$;
   - $\sigma(q) = \bar\sigma q^{-\varepsilon/\bar\sigma}$;
   - the (A2) regression slope on model firms equals $\varepsilon/\bar\sigma$ (the code reports this as `bhat`).
5. **Model weighting identity.** Inside the model, cost-weighted mean markup = harmonic sales-weighted markup.
6. **Cournot identities.** Eq. (21) holds exactly in a simulated sector. With $\gamma=\eta$, markups are uniform.
7. **Patch guard.** Applying `octave_compat.patch` changes no line that contains arithmetic. This is checked by a diff filter.

## 5. Reproducibility

- `make all` runs `fetch` (`src/fetch_raw.py`), then `phase1`, then `test`.
- Pinned `requirements.txt` (the Python venv already uses numpy 2.4.6, scipy 1.17.1, pandas 3.0.6).
- The Octave version is logged in the output.
- Raw downloads are recorded in `data/raw/MANIFEST.csv` with sha256 hashes.

## 6. Effort and risk

- Steps 1–3 and 5 are minutes of compute.
- Step 6 (oligopoly) is the long pole: hours of compute, so it runs in the background.
- Main risk: missing pieces of H&F's code (step 4's subsidy script, and output files the read-me references but the zip does not contain).
