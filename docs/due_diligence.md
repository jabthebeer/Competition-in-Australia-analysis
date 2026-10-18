# Due diligence on the evaluation results

**Date:** 18 October 2026. **Covers:** the 12 current evaluations (34 laws); the 8 archived ones are superseded. **For:** Cowork and the owner. It lists what has been checked, what has not, and what must happen before the results are relied on.

**Verdict: provisional.** The method is sound and reproducible. The inputs (the laws' dates and industries) have not been checked by a person, and several robustness checks are still outstanding. Treat every result as provisional until items 1–3 below are done.

## 1. The evaluations covered

| Evaluation | Laws | Result now |
|---|---|---|
| Fuel price reporting (NSW 2016 to SA 2021) | 5 | No detectable effect on fuel prices (−2.8%, p = 0.20); grade Weak |
| Mandatory e-conveyancing (2018–2023) | 5 | No detectable effect on legal services entry; Weak |
| Perth retail trading hours (2010, 2012), Phase 5 | 2 | No detectable effect; Moderate |
| Perth weeknight trading (2010), new data | 1 | No detectable effect; Moderate |
| Childcare NQF (2012), Phase 5 | 2 | No detectable effect; Moderate |
| Childcare NQF, WA's delay | 2 | No detectable effect; Moderate |
| Heavy Vehicle National Law (2014) | 6 | No detectable effect; Moderate |
| Victorian taxi licensing (2014) | 1 | No detectable effect on entry; Weak. The fares fall is confounded |
| Legal Profession Uniform Law (2015) | 2 | No detectable effect; Moderate |
| Ride-share legalisation (2015–2018) | 7 | Not identified |
| NT container deposits (2012) | 1 | Not identified |
| Retail energy price deregulation (2013–2016) | 3 | Not identified |

The Perth and childcare records are each used by two evaluations, so the laws column sums to 37 for 34 distinct records.

Full results: [`results_phase5.md`](results_phase5.md). Regression tables: [`econometric_tables.md`](econometric_tables.md).

## 2. What has been checked

| Check | Status | Where |
|---|---|---|
| Design fixed before results: specification and plan committed, blinded dry run, one registered run | Done for every current evaluation | `alicia/specs/`, `pap_*.md`; the runner refuses the estimate stage otherwise |
| Estimator chosen blind, by power on placebos, not by results | Done for the 10 Phase 5 evaluations; the other two fixed their designs in their own plans | [`power_study.md`](power_study.md) |
| Inference against placebo industries (or CPI classes), with a pre-reform trend test | Done | Each evaluation; the regression tables |
| Every output reproduces byte for byte from the raw data and scripts | Done | `alicia spec run <id>`; [`specification_runner.md`](specification_runner.md) |
| Regression-table estimates re-fitted and matched to the registered run | Done (25 of 25 outcomes) | `alicia/analyses/phase5/*/table_stats.json` |
| Automated tests | 171 passing | `alicia/tests/` |
| Laws' dates confirmed against official registers | **7 of 34** | `regulation-register/reports/effective_dates_2026-10-18.json` |
| Laws reviewed by a person (dates, states, industries, direction) | **0 of 34** | Every record is `draft` |

## 3. Open items

| # | Gap | Why it matters | Who | How | Done when |
|---|---|---|---|---|---|
| 1 | **Laws not checked by a person.** 27 of 34 dates unconfirmed (NSW and SA registers block automated checks; other records lack register identifiers). Industries are desk-research judgements | A wrong date, state or industry pushes results towards "no effect" | Owner with Cowork | [`cowork_review_guide.md`](cowork_review_guide.md) and the review sheet [`review/evaluated_records_review.csv`](review/evaluated_records_review.csv) | Every row has a verdict with an official source; Claude Code has applied it; changed cases are re-run as registered follow-ups |
| 2 | **No search for other changes in the same window before results were seen.** The Melbourne fares confounder was found only afterwards | A coinciding change can create or hide an effect | Claude Code (data scan), Cowork (desk search, guide step 4) | [`confounder_scan.md`](confounder_scan.md): other register records in the same states and industries, and when each treated series actually moved | Each evaluation has a listed set of concurrent changes. Future specifications include the scan before unblinding |
| 3 | **Robustness checks not run for Phase 5.** Leave-one-state-out, other windows, unweighted, sensitivity to pre-trends; the estimator disagreements not explained | Shows whether a result depends on one state, one year or one estimator | Claude Code | [`robustness_phase5.md`](robustness_phase5.md) (not pre-registered) | Each evaluation reports its robustness table; disagreements explained or flagged |
| 4 | **No independent verification of the code.** The R cross-check required by CLAUDE.md is deferred; R is not installed in the cloud environment | Catches estimator bugs a single implementation cannot | Claude Code, after the owner adds R to the environment's setup script | fixest and synthdid cross-checks on reference cases; a code review of `evaluate/` and `analyses/phase5/` | Python and R agree within tolerance on each estimator |
| 5 | **Inference limits.** 40 placebos give coarse p-values (smallest 0.024). Placebo industries may be quieter than the treated ones. Multiple testing is adjusted only within each specification; secondary outcomes are not adjusted | p-values can be too small or too large | Claude Code | Programme-wide false discovery rate; report the own-industry placebo p-value beside every result | Adjusted q-values across all evaluations |
| 6 | **Power.** Most designs detect only 3–7 entries per 100 businesses, or 6–9% on prices; plausible effects are 1–3 | "No detectable effect" is not "no effect" | Claude Code (pooling), owner (data) | Pooled estimates across similar reforms; direct outcome data (station-level fuel prices, PEXA, NCVER, NDIS, AER) | Each family has a pooled estimate or a stated reason |
| 7 | **One unverified fact in a result.** The January 2015 Melbourne fare changes come from commentary, not Public Transport Victoria | It is the stated cause of the confounded fares result | Cowork | Guide step 5, question 1 | Official source recorded |

## 4. Known issues by evaluation

- **Fuel price reporting:**
  - NSW's date is the registration deadline, not a confirmed reporting start. Queensland's 2018 scheme may have begun as a trial.
  - Synthetic DiD (+4.8%) and generalised synthetic control (+22%) disagree with the registered estimate (−2.8%).
  - COVID falls in the Tasmanian and SA windows.
- **E-conveyancing:** conveyancing is a small part of legal services, so any effect is diluted. Synthetic DiD disagrees (−3.0).
- **Victorian taxi licensing:** only one post-reform year. Unlicensed UberX arrived in 2014. The fares fall dates to 2015-Q1, not the reform (see item 7).
- **Childcare NQF:**
  - Exits are −1.9 per 100 with two-way fixed effects but +3.2 with saturated fixed effects: the sign depends on the estimator.
  - Prices: +4.4% with synthetic DiD; the saturated check disagrees.
- **Legal Profession Uniform Law:** unusual against its own industry in placebo states (p = 0.048), but not against placebo industries (p = 0.47).
- **Ride-share, NT container deposits, energy deregulation:** not identified (pre-trends fail). They need different data, not more estimation.

## 5. When the results can be relied on

1. Every law used has a person-checked date, states and industries, with official sources (item 1).
2. Every evaluation lists its concurrent changes and says which could matter (item 2).
3. Every result reports a robustness table, and no conclusion rests on one state, one year or one estimator without saying so (item 3).
4. Any evaluation whose inputs changed after items 1–2 has been re-run as a registered follow-up evaluation.

Items 4–6 strengthen the results but do not block reporting them, provided their limits are stated.
