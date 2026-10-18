# Forward plan: macroeconomic controls and a full regression framework for ALICIA

Methods note, 18 October 2026, for the owner and Cowork. It builds on [`impact_evaluation_design.md`](impact_evaluation_design.md) (designs D1–D4, inference, pooling) and the three evaluations run so far.

**Goal:** each register record gets a regression-based causal estimate that accounts for state growth, industry growth and macroeconomic demand. The estimate should be precise enough to be useful, and every step stays pre-registered and reproducible.

---

## 1. Diagnosis: what the current tool already does, and what is missing

The concern is right in part. The evaluations so far are not significant mainly because of **power**:

- one treated state;
- short clean windows;
- noisy small cells, e.g. WA quarterly LFS figures for one industry group swing by up to 30 log points.

Omitted macro trends are a second factor. The current designs already remove some macro variation, but not all of it:

| Macro factor | How the current designs handle it | Gap |
|---|---|---|
| National cycle (GDP, interest rates, GFC, COVID, national subsidies) | Period fixed effects in every design | None for common shocks |
| State-wide demand and growth (e.g. the WA mining boom) | Triple differences against other industries in the same state; placebo industries in the same state | **Partly missing.** The weeknight turnover design dropped its within-state comparison to gain precision, and a robustness check moved the result by ~20 points |
| National industry growth (e.g. childcare expanding everywhere) | Comparison with the same industry in other states | Covered where other states are untreated. Missing where every state is treated (e.g. after WA joined the NQF) |
| State-specific industry cycles (e.g. WA construction and mining-linked retail) | Not modelled | **Missing** |
| Different sensitivity to common shocks (WA reacts more to commodity prices) | Not modelled; it only widens the placebo spread | **Missing.** This is where macro controls can buy the most precision |

Adding these factors does two things:

- **Removes bias** from state-specific shocks that coincide with a reform.
- **Shrinks the no-effect spread,** so smaller effects become detectable.

It will not by itself make results significant. The aim is credible and precise estimates, whatever their sign or size. A tool tuned to find significance would not be credible (§7).

## 2. Target econometric framework

All reforms go through one regression framework, with the unit being **state (or region) × industry × period**. Four layers, used as far as each reform's data allow.

### 2.1 Saturated fixed effects (the default)

y_{s,i,t} = α_{s,i} + δ_{i,t} + γ_{s,t} + β · D_{s,i,t} + ε_{s,i,t}

| Term | What it absorbs |
|---|---|
| α_{s,i} (state × industry) | Permanent differences in each industry's level by state |
| δ_{i,t} (industry × period) | **National industry growth and industry-specific demand**: everything common to an industry across states in a period |
| γ_{s,t} (state × period) | **State macro conditions**: demand, growth, the mining boom, state budgets. Everything common to all industries in a state in a period |
| D_{s,i,t} | 1 for treated industries in treated states after the reform |

- **Identification:** what is left is how the treated industry in the treated state moved, relative to its own industry elsewhere and to other industries in its own state. This is the regression form of design D2, and it nets out exactly the factors in the owner's note.
- **Requirements:** several industries per state and several states per industry. CABEE, the LFS, Retail Trade and the register panels all have that structure.

### 2.2 Measured controls where fixed effects cannot be saturated

Some outcomes cover only one industry (e.g. a price index), and some designs have few states. There, γ_{s,t} and δ_{i,t} are replaced by measured variables:

- **State demand and growth:**
  - state final demand growth (quarterly);
  - gross state product growth (annual);
  - state employment growth and unemployment rate (monthly);
  - population growth;
  - dwelling approvals (a leading demand indicator).
- **Industry demand and growth:**
  - national industry gross value added or turnover growth;
  - household consumption by purpose (for consumer-facing industries).
- **Exposure-weighted shocks** (shift-share controls):
  - national commodity prices × each state's mining share of output (WA, QLD);
  - national industry growth × each state's pre-period industry mix.

  These give each state its own predicted demand path from national movements and fixed pre-period weights.

### 2.3 Different sensitivity to common shocks (factor models)

States react differently to the same national shock: WA to iron ore, Tasmania to tourism. A fixed effect cannot capture that; a factor structure λ_s′F_t can. Three ways to estimate it:

- **Interactive fixed effects / generalised synthetic control** (Bai 2009; Xu 2017). Estimate the common factors from untreated units, then each treated unit's loadings from its pre-period.
- **Synthetic difference-in-differences** (Arkhangelsky et al. 2021) and **augmented synthetic control** (Ben-Michael, Feller & Rothstein 2021). These weight comparison units and pre-periods to match the treated unit's pre-reform path. Measured controls (§2.2) can enter as covariates.
- **Matrix completion** (Athey et al. 2021), as a check.

This is the most promising route to precision for single-state reforms, because it uses the long monthly and quarterly histories now in the pipeline.

### 2.4 Staggered and heterogeneous effects, and pooling

- **Several states adopting at different times (D1):**
  - Callaway & Sant'Anna (2021), with covariates through the doubly robust estimator of Sant'Anna & Zhao (2020);
  - the imputation estimator of Borusyak, Jaravel & Spiess (2024). It fits the full fixed-effect model (§2.1) on untreated cells only, then imputes counterfactuals. This is the natural way to combine saturated fixed effects with staggered timing.
- **Pooling across reforms** in the same family (mutual recognition, ride-sharing, container deposits, trading hours): stacked estimation and a hierarchical or meta-analytic summary, as in design-doc §5 "Pooling". This is the largest remaining power gain.

### 2.5 Inference

- **Wild cluster bootstrap with few treated clusters** (Roodman et al. 2019; MacKinnon & Webb 2018).
- **Randomization inference** across placebo industries, states and dates. This is the current approach and stays the default for single-state designs.
- **Conformal inference for synthetic-control-type estimators** (Chernozhukov, Wüthrich & Zhu 2021).
- **Sensitivity to violations of parallel trends** (Rambachan & Roth 2023). This replaces ad hoc detrending with a stated bound.

## 3. Rules for controls (the "bad control" problem)

A control that the reform itself changes absorbs part of the effect. Example: retail growth in WA after a retail trading-hours change.

1. **Never control for the outcome industry's own post-reform growth in the treated state.** Fixed effects and controls are built from other industries, other states or pre-period weights.
2. **Measured controls are state-level aggregates excluding the treated industry,** e.g. state final demand minus treated-industry spending where it can be separated.
3. **Prefer exposure-weighted national shocks** (§2.2): they are not caused by a state reform.
4. **Each plan states its control set before unblinding.** It also reports the estimate without controls, and with fixed effects only, so the effect of adding controls is visible. Reference: Cinelli, Forney & Pearl, "A crash course in good and bad controls".

## 4. Data to add

All are public. Access and licences are to be confirmed in Phase 1, and the ABS Data API dataflow names checked against the live list.

| Control | Source | Frequency, geography | Use |
|---|---|---|---|
| State final demand (household consumption, investment, government) | ABS 5206, Australian National Accounts | Quarterly, state | State demand control; deflator |
| Gross state product; gross value added by industry × state | ABS 5220, State Accounts | Annual, state × division | State growth; industry mix weights; mining share |
| Employment, unemployment rate, hours (total) | ABS 6202, Labour Force | Monthly, state (and SA4) | State labour-market conditions |
| Estimated resident population | ABS 3101 | Quarterly, state; annual SA2 | Demand scaling; per-capita outcomes |
| Wage Price Index | ABS 6345 | Quarterly, state | Cost conditions |
| Building approvals | ABS 8731 | Monthly, state and SA2 | Local demand, leading indicator |
| Household consumption by purpose | ABS 5206 | Quarterly, national | Industry-specific demand (for δ_{i,t} when it cannot be saturated) |
| Industry gross value added (chain volume) | ABS 5206 / 5204 | Quarterly or annual, national by division | National industry growth |
| Commodity price index | RBA statistical table I2 | Monthly, national | Exposure-weighted shock (× state mining share) |
| Business income, wages, sales by industry | ABS 5676 (Business Indicators); 8155 (Australian Industry) | Quarterly or annual, national by industry | Industry cycle; margins |
| Regional population, income | ABS Data by Region (already connected) | Annual, SA2 and LGA | Local controls for geographic designs |

**Outside this list but worth seeking:**

- Department of Education childcare service and fee data, and the Internet Vacancy Index. Both need manual download.
- ATO taxation statistics by fine industry.

**Storage:** a new controls panel in the common format.

- State × period controls go in `data/processed/controls/state_quarter.parquet`.
- National industry series go in `industry_quarter.parquet`.
- Builders `alicia.pipeline.controls_*` record each source in `data/SOURCES.md`.

## 5. Library and workflow changes

**1. `alicia.evaluate.panel`: one estimation interface.**

- Builds the state × industry × period panel from any outcome panel, plus controls.
- Estimators:
  - saturated fixed effects (§2.1);
  - measured controls (§2.2);
  - imputation and Callaway–Sant'Anna for staggered timing (§2.4);
  - synthetic difference-in-differences and generalised synthetic control (§2.3).
- Inference by wild cluster bootstrap and randomization (§2.5).
- **Candidate implementations,** to be vetted for maintenance before adoption:
  - Python: pyfixest (high-dimensional fixed effects, event studies, wild bootstrap).
  - R references for cross-checking: fixest, did, didimputation, synthdid, fect/gsynth, HonestDiD, fwildclusterboot.
- Every estimator is tested on simulated panels with planted effects and planted state-specific shocks, as the current tests do.

**2. A specification file per evaluation.** A data class or YAML file, replacing hand-written `spec.py` modules, with:

- records and dates;
- treated units and industries;
- outcomes;
- control set;
- estimators;
- windows;
- placebo pools.

One runner produces the design review (blinded), the registered estimate and the evaluation file. The three existing analyses become the first specifications, and the runner must reproduce their numbers exactly before anything new is run.

**3. Comparison of estimates in every evaluation.** Main estimate:

- without controls;
- with fixed effects;
- with measured controls;
- with factor models.

All are shown side by side in the results file and the web viewer, with the pre-registered one marked.

**4. Cross-checks in R.** CLAUDE.md makes R the project default. For each new estimator, one R script in `analysis/` reproduces a reference case with fixest, did or synthdid, and the Python result must match to tolerance.

## 6. Phases

| Phase | Work | Done when |
|---|---|---|
| **0. Decisions** (owner) | Approve the framework (§2), control rules (§3), the Python-with-R-cross-check approach, and the order of reforms | Decision log entries |
| **1. Controls data** | Connectors for the controls in §4; controls panel; sources recorded | Panels built and tested; coverage for 2000–2025 by state |
| **2. Estimator library** | `evaluate.panel` with the estimators in §2 and inference in §2.5; simulation tests (planted effects with and without state shocks); R cross-checks | Each estimator recovers planted effects within tolerance and matches R on a reference case |
| **3. Power study (blinded)** | For each evaluable reform, how much each layer shrinks the no-effect spread, with treated post-periods hidden | A table of smallest detectable effects by reform and estimator, used to choose designs |
| **4. Specification runner** | Specification format; runner; the three existing analyses reproduced exactly | Byte-identical evaluation files for the existing three |
| **5. Re-evaluations** | Re-run the evaluated reforms under the new framework, each as a pre-registered follow-up (`follows`), never overwriting earlier results | Plans committed before runs; results and evaluation files published |
| **6. All evaluable records** | Extend to every record the screen rates medium or high; pooled family estimates | Every such record has an evaluation or a stated reason it cannot be identified |
| **7. Reporting** | Viewer shows controls, estimator comparison and sensitivity bounds; a short methods page | Owner sign-off |

**Order of reforms in Phase 5–6.** Families with several adopting states first, where power is highest:

1. automatic mutual recognition (2021–22);
2. ride-sharing legalisation (2015–18);
3. container deposit schemes;
4. trading hours (WA 2010 and 2012, SA, QLD, NSW Boxing Day).

The single-state cases come after.

### Progress (18 October 2026)

| Phase | State |
|---|---|
| 0. Decisions | Done (E-55) |
| 1. Controls data | Done (E-56): State Accounts, state final demand, Labour Force, ERP, WPI, building approvals, national GVA by division, Business Indicators, RBA commodity prices; sources in `data/SOURCES.md` |
| 2. Estimator library | Done in Python (E-58, E-59): saturated fixed effects, wild cluster bootstrap, imputation, randomization inference, shift-share and measured controls, synthetic DiD and synthetic control, generalised synthetic control, matrix completion, conformal inference, Callaway–Sant'Anna, sensitivity bounds; simulation tests ([methods note](methods_panel_estimators.md)). The R run of the cross-check is deferred by the owner |
| 3. Power study | Done (E-60, E-65; [results](power_study.md)): business entry and exit and CPI prices; placebo industries, placebo states, fake dates and both; the new families from the gap scan |
| 4. Specification runner | Started (E-67; [note](specification_runner.md)): the four existing analyses are JSON specifications read by their code, and reproduce byte for byte through `alicia spec run`. Still to do: a generic estimation stage and the side-by-side estimator comparison (§5.3) |
| 5–7 | Not started |

The website also shows the controls and state and industry growth (E-57).

## 7. Guardrails

- **Pre-registration stays.** Control sets and estimators are fixed at the blinded design stage. Choosing among them by looking at results would turn the comparison of estimates into a search for significance.
- **Report every specification run**, labelled pre-registered or not.
- **State honestly what controls cannot fix:**
  - one treated state still gives limited inference;
  - survey noise in small cells does not shrink with controls;
  - firm-level questions (markups, reallocation) still need BLADE or ATO microdata, which the project has ruled out (decision E-02).

## 8. Decisions needed from the owner

1. Approve the four-layer framework, with saturated fixed effects as the default and factor models for single-state reforms.
2. Approve the control rules in §3, especially excluding treated-industry growth.
3. Estimation core: Python (pyfixest and peers) with R cross-checks, or move the estimation core to R (fixest, did, synthdid, fect) and keep Python for the data pipeline.
4. Reform order for Phases 5–6 (§6).
5. Whether to seek the manually downloaded sources: Department of Education childcare data, the Internet Vacancy Index, ATO industry statistics.

## References

- Arkhangelsky, Athey, Hirshberg, Imbens & Wager (2021), "Synthetic difference-in-differences", *American Economic Review*.
- Athey, Bayati, Doudchenko, Imbens & Khosravi (2021), "Matrix completion methods for causal panel data models", *JASA*.
- Bai (2009), "Panel data models with interactive fixed effects", *Econometrica*.
- Ben-Michael, Feller & Rothstein (2021), "The augmented synthetic control method", *JASA*.
- Borusyak, Jaravel & Spiess (2024), "Revisiting event-study designs: robust and efficient estimation", *Review of Economic Studies*.
- Callaway & Sant'Anna (2021), "Difference-in-differences with multiple time periods", *Journal of Econometrics*.
- Chernozhukov, Wüthrich & Zhu (2021), "An exact and robust conformal inference method for counterfactual and synthetic controls", *JASA*.
- Cinelli, Forney & Pearl, "A crash course in good and bad controls", *Sociological Methods & Research*.
- Goldsmith-Pinkham, Sorkin & Swift (2020), "Bartik instruments: what, when, why, and how", *American Economic Review*.
- MacKinnon & Webb (2018), "The wild bootstrap for few (treated) clusters", *Econometrics Journal*.
- Rambachan & Roth (2023), "A more credible approach to parallel trends", *Review of Economic Studies*.
- Roodman, MacKinnon, Nielsen & Webb (2019), "Fast and wild: bootstrap inference in Stata using boottest", *Stata Journal*.
- Sant'Anna & Zhao (2020), "Doubly robust difference-in-differences estimators", *Journal of Econometrics*.
- Xu (2017), "Generalized synthetic control method", *Political Analysis*.
