# Methods note: panel estimators and macroeconomic controls

**Date:** 18 October 2026. **Status:** forward plan Phases 1 and 2 built and tested. No reform has been re-estimated with them yet; that is Phase 5, under new pre-registered plans.

**Code:** `alicia/src/alicia/evaluate/panel.py`, `synth.py`, `cs.py`, `honest.py`, `covariates.py`; controls in `alicia/src/alicia/pipeline/controls.py` and `abs_state_accounts.py`. **Plan:** [`forward_plan_macro_controls.md`](forward_plan_macro_controls.md).

## 1. Model

y_{s,i,t} = α_{s,i} + δ_{i,t} + γ_{s,t} + β·D_{s,i,t} + X′c + ε

| Term | Absorbs |
|---|---|
| α_{s,i} | Cell levels |
| δ_{i,t} | National industry cycles and demand |
| γ_{s,t} | State macro conditions (demand, mining boom, budgets) |
| X | Measured controls, where the fixed effects cannot be saturated |

**Identifying assumption:** without the reform, the treated industry in the treated state would have moved like the same industry elsewhere plus the treated state's other industries (triple-difference parallel trends). It fails if the reform shifts activity to other industries in the same state (spillovers bias β toward the total effect minus the spillover) or if a shock hits only the treated industry in the treated state.

## 2. Estimators and inference

| Tool | Use | Key limits |
|---|---|---|
| `feols` (alternating projections) | Any number of fixed effects; clustered (CR1) errors | Clustered errors are unreliable with fewer than about 10 clusters, or few treated ones |
| `wild_cluster_bootstrap` (restricted, Webb weights) | Several treated states | Not valid with one or two treated clusters (MacKinnon and Webb 2017) |
| `imputation` (Borusyak, Jaravel and Spiess 2024) | Staggered adoption, effects that change over time | Needs untreated observations for every fixed-effect group of a treated observation; others are reported as not identified |
| `placebo_null` | Randomization inference over placebo states, industries and dates; the default for single-state reforms | Exchangeability of the placebo units; spread depends on the placebo pool |
| `shift_share`, `covariates.state_covariates` | Exposure-weighted and measured controls | Bad-control rule: state aggregates include the treated industry; each plan must justify them |
| `synth.sdid` (also `method="sc"`, `"did"`) | Synthetic DiD (Arkhangelsky et al. 2021), synthetic control and DiD on one footing, following the synthdid reference code | One adoption date (run per cohort and average) |
| `synth.gsynth` | Generalised synthetic control / interactive fixed effects (Xu 2017): factors from never-treated units, loadings from each treated unit's pre-period, factors chosen by cross-validation | Needs more pre-periods than factors plus one; staggered adoption allowed |
| `synth.mc_nnm` | Matrix completion with unit and time effects (Athey et al. 2021), as a check | Slow; penalty by cross-validation on control cells |
| `synth.conformal_pvalue`, `conformal_interval` | Permutation inference for one treated unit (Chernozhukov, Wüthrich and Zhu 2021), with DiD or synthetic-control fits | p-values move in steps of 1/T; needs stationary residuals |
| `cs.att_gt` | Callaway–Sant'Anna group-time effects; doubly robust with covariates (Sant'Anna and Zhao 2020); never-treated or not-yet-treated comparisons; simple, dynamic and group aggregates | Balanced panels; covariates fixed within units; the cluster bootstrap needs many clusters |
| `honest.relative_magnitudes`, `smoothness`, `breakdown` | Bounds on effects when parallel trends may fail (Rambachan and Roth 2023), and the allowance at which zero enters | Identified sets exact; confidence intervals approximate (the R package HonestDiD is the reference) |

## 3. Simulation checks (tests in `alicia/tests/test_panel.py`)

| Check | Result |
|---|---|
| Fixed-effect absorption against an explicit dummy regression, unbalanced panel | Coefficients and CR1 errors equal to 1e-7 |
| Treated state booms after adoption; industry cycles (true effect 2.0, 20 panels) | Saturated: mean 2.01. Cell + period effects only: mean 3.95 |
| Staggered adoption, effects growing 0.5 a period, every cell eventually treated (8 panels; true average 3.25) | Imputation: mean 3.23. Static two-way regression: mean 1.47 |
| Imputation with a control correlated with treatment | Control coefficient within 0.1 of 1; effect within 0.3 |
| Wild cluster bootstrap under no effect (40 panels, 10 clusters, 5 treated) | 6 of 40 rejections at 10% (4 expected; the test allows up to 9) |
| Placebo randomization inference, single treated cell | Detects a large planted effect; the Conley–Taber interval covers it |
| One treated unit with a high loading on a factor that rises after adoption (true effect 2.0, 12 panels; `test_synth.py`) | DiD 4.34; synthetic control 2.19; synthetic DiD 2.45; generalised synthetic control 2.10; matrix completion 2.69 (4 panels) |
| Factor count chosen by cross-validation, one-factor design | One factor in 6 of 8 panels |
| Conformal test under no effect (40 panels) | 2 rejections at 10% (4 expected) |
| Callaway–Sant'Anna, adoption more likely where outcomes trend up with a covariate (true effect 2.0 two periods after adoption; `test_cs.py`) | Without covariates 3.02; doubly robust with the covariate 1.99 |
| Sensitivity bounds (`test_honest.py`) | Closed-form identified sets checked against hand calculations |

**Reference case** (`analysis/crosscheck/`, synthetic: 8 states × 10 industries × 30 periods, 4 states adopting in 2 industries at staggered dates, state boom after adoption):

| Estimator | Estimate | True average effect |
|---|---|---|
| Saturated fixed effects, static | 2.08 (clustered SE 0.27; bootstrap p = 0.002) | 2.27 |
| Imputation, saturated fixed effects | 2.42 | 2.27 |
| Cell + period effects, static | 5.54 (SE 0.96) | 2.27 |
| Imputation, cell + period effects | 5.71 | 2.27 |

The last two rows show the problem the owner raised: without state × period effects, the state boom is credited to the reform.

## 4. R cross-check

`analysis/crosscheck_panel_estimators.R` re-estimates the reference case with fixest, didimputation, fwildclusterboot, synthdid, gsynth and did and compares each number with `panel_reference_python.json` (tolerance 1e-6; bootstrap p-values within 0.01). **Not yet run:** R is not installed in the build environment. To run: `Rscript analysis/crosscheck_panel_estimators.R` from the repository root.

## 5. Controls available (Phase 1)

| Panel | Series | Frequency, geography |
|---|---|---|
| `abs_state_accounts/industry_state_fy` | GVA by division (volume, current), factor income, GSP, GSP per person, real income | FY1989-90 to 2024-25, states and Australia |
| `controls/state_quarter` | State final demand and components; household consumption by purpose; ERP; WPI | Quarterly, states |
| `controls/state_month` | Labour Force; building approvals | Monthly, states (approvals also capital city / rest of state) |
| `controls/industry_quarter` | National GVA by division and sub-industry; Business Indicators | Quarterly, Australia |
| `controls/national_month` | RBA commodity prices | Monthly |

## 6. Still to do

- **Phase 2:** an R run of the cross-check (deferred by the owner).
- **Phase 3:** blinded power study: how much each layer shrinks the no-effect spread for each evaluable reform (in progress).
- **Phase 4:** a specification runner that reproduces the three existing analyses exactly.
