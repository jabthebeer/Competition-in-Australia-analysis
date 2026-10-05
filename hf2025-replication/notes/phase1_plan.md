# Phase 1 implementation plan (proposal, awaiting approval)

Goal: reproduce H&F (2025) model results from the paper's own published targets, and validate them against Tables 2, 4, 5, 8–11, B2–B3, B5–B6 and B9.

## 0. Inputs still required

| Input | Why | Status |
|---|---|---|
| EMX (2023) paper and online appendix (*JPE*, or NBER WP 24800) | Model details listed in `model_summary.md` §4 | **Blocked** by network policy |
| EMX replication package (*JPE* Harvard Dataverse, or Chris Edmond's site) | Reference implementation | **Blocked** |
| RBA RDP 2025-05 replication files (a "read me" page appears to exist on rba.gov.au) | Possibly H&F's adapted code, the best reference | **Blocked**; contents unknown |

Either upload these files or allowlist the hosts (see `../data/raw/SOURCES.md`). Nothing below starts until at least the EMX paper and appendix are available.

## 1. Engine: which code computes the results

I'll follow the user's language rule (Python preferred; Octave for MATLAB code; port only if Octave fails):

- **Path A, code obtained** (preferred):
  - run the MATLAB code unmodified in GNU Octave 8.4 (installable from the Ubuntu archive, which is reachable);
  - drive it from Python through a thin wrapper (parameters in, CSV out, via `octave-cli`);
  - log any Octave compatibility shims in DECISIONS.md;
  - all sensitivity and extension runs reuse this engine with different inputs.
- **Path B, code not obtained, or Octave cannot run it:**
  - implement the model in Python (`src/model/`) from the EMX paper and H&F Section 3;
  - if Path A also exists, require the Python port to match the Octave output to 1e-6 relative error on every reported statistic before using it.

## 2. Numerical method for the Python implementation (Path B, and for the tests)

### 2.1 Kimball static block

- **Change of variables.** Integrate over the Pareto CDF, $u = 1 - x^{-\xi} \in [0,1)$, so that "top 5% of firms" is simply $u \ge 0.95$ and the fat tail becomes a finite interval.
- **Quadrature.** Composite Gauss–Legendre on $[0,0.95]$ and $[0.95,1)$, with geometric refinement towards $u \to 1$. Accuracy is verified by doubling the number of nodes until every reported statistic changes by less than 1e-9 in relative terms.
- **Firm allocation.** For each node, solve the firm first-order condition for $q(x)$ with a vectorised safeguarded Newton–bisection. The equation is monotone in $q$, and the solution is bracketed in $(0,\bar\sigma^{\bar\sigma/\varepsilon})$.
- **Planner allocation.** Same method with $\mu\equiv1$.
- **Calibration.** Solve for $(\xi, \bar\sigma)$ from the two moments with `scipy.optimize.root` (hybrid Powell), using transformed unknowns $\log(\xi-1)$ and $\log(\bar\sigma-1)$. Moment tolerance 1e-10.
- **Robustness check.** Run a multi-start from a 5×5 grid to confirm the solution is unique within the plausible region.

### 2.2 General-equilibrium steady state

- Given the static block, the steady state reduces to a small system: $K/L$ from $R=1/\beta-1+\delta$, labour supply, free entry and the materials first-order condition.
- Solve it with `scipy.optimize.root`, residual tolerance 1e-12.
- Solve the planner and uniform-subsidy steady states the same way. Normalisations of $\varphi$ and $\kappa$ will follow EMX.

### 2.3 Cournot oligopoly

- Simulate $S$ sectors, each with $n$ firms (fixed at 3,440 / 3,884, or drawn as in EMX), with Pareto($\xi$) productivities.
- Fix the seed (`numpy.random.default_rng(20250805)`) and use **common random numbers** across parameter evaluations, so the objective is smooth.
- Within each sector, solve for the Cournot equilibrium by fixed-point iteration on sales shares (eqs 19–20 with CES within sector), with a damped update and tolerance 1e-12.
- Calibrate $(\xi,\eta,\gamma)$ by minimum distance on the four Table 8 moments, using the EMX weighting if documented. Otherwise use the identity matrix on percentage deviations, and log that choice.
- Choose $S$ so that simulation error on each moment is below 0.1 ppt, checked by re-running with five seeds.

## 3. Validation (deliverable: `output/report.md` §1)

| Paper table | Statistic | Pass criterion |
|---|---|---|
| Table 2 | $\xi$, $\bar\sigma$ (4 calibrations) | ≤ 2% relative error. If missed, diagnose (definition of the top-5% share, choke cut-off, rounding of targets) before moving on |
| Table 4 | GO / VA / VA($\mu$=1) losses, 2 weightings × 2 periods, plus changes | Report absolute and relative differences. Goal ≤ 2% relative on levels |
| Table 5 | Model markup percentiles (cost-weighted run) | Report differences. Also confirms the weighting convention |
| Table 11 / B9 | Output, consumption, hours, welfare gains; uniform subsidy | Report differences |
| Tables 9–10 | Oligopoly parameters and losses | ≤ 2% on parameters. Report what the model implies for the inconsistent Table 10 VA (no input) column |
| B2–B3, B5–B6 | Robustness variants | Report differences. Test the B1/B4 swapped-rows hypothesis and the B3 copy-paste hypothesis |

Every discrepancy goes in a numbered list in the report, with a diagnosis or "unexplained".

**Rounding sensitivity.** The targets are published to two decimal places (markups) or whole percentages (shares). For each calibration I'll also re-solve at the edges of the rounding interval (e.g. $M\in[1.175,1.185]$, top-5% $\in[0.675,0.685]$) and report the implied range of $\xi$, $\bar\sigma$ and the losses. This shows whether a ~2% mismatch can be explained by rounding alone.

## 4. Unit tests (`tests/`, pytest)

1. **CES limit.** Superelasticity → 0 (e.g. 1e-6) gives a misallocation loss of ≈ 0 (< 1e-6). Markups are then uniform at $\bar\sigma/(\bar\sigma-1)$.
2. **Planner dominance.**
   - Planner $Z \ge$ market $Z$ across a grid of $(\xi,\bar\sigma,\varepsilon/\bar\sigma)$.
   - First-best steady-state welfare ≥ market steady-state welfare.
3. **Harmonic-mean identities on a toy example.** With 3–5 discrete firms in 2 sectors, eq. (10) $z(s)$ and $Z$ computed as harmonic sales-weighted means equal output divided by input-bundle use. Also eqs (11–12) and (13–14).
4. **Klenow–Willis algebra:**
   - $\Upsilon'$ is the derivative of $\Upsilon$ (finite differences);
   - $\Upsilon(1)=1$;
   - $\sigma(q)=\bar\sigma q^{-\varepsilon/\bar\sigma}$;
   - the (A2) slope recovered from simulated firms equals $\varepsilon/\bar\sigma$.
5. **Cournot identities.** Eq. (21) holds exactly in simulated sectors. With $\gamma=\eta$, markups are uniform.
6. **Model weighting identity.** Cost-weighted mean markup = harmonic sales-weighted markup inside the model.
7. **Calibration round-trip.** Simulate moments at known parameters, re-calibrate, and recover the parameters to 1e-6.

## 5. Reproducibility

- **Entry point:** `make all` → `phase1` (the `phase2`–`phase4` targets are added later). Each target writes `output/tables/*.csv` and regenerates `output/report.md` sections from them, so no numbers are pasted by hand.
- **Pinned dependencies:** `requirements.txt` with exact versions (numpy, scipy, pandas, matplotlib, pytest; `oct2py` only if needed). Octave version recorded in the report.
- **Paper benchmarks:** transcribed once into `data/paper/hf2025_published.csv`, with table and page references, and checked against the PDF text by a test.
- **Seeds:** fixed seeds for all simulations; the seed list is recorded in the report.

## 6. Rough effort and risks

- Static Kimball block plus calibration: small once EMX details are confirmed.
- GE block: moderate. Most of the risk is in matching EMX normalisations and the welfare definition.
- Oligopoly: the largest piece, with about 3,500 firms per sector × thousands of sectors. Vectorised numpy should handle tens of millions of firm draws per evaluation, but calibration may take minutes to hours.
- **Main risk.** Without EMX code, conventions such as the loss metric, choke cut-off, percentile weighting and oligopoly design may have to be inferred by matching H&F's published numbers. Any such inference will be logged in DECISIONS.md as an inference, not a fact.
