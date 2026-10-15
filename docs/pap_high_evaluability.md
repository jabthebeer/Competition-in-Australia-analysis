# Pre-analysis plan: the high-evaluability batch

**Registered:** 15 October 2026, before any post-reform outcome of a treated state was estimated. The design stage (§9) ran with those outcomes hidden.

**What this covers:** the 16 register records rated "high" for evaluability that had not been evaluated yet (the two Perth trading-hours records were evaluated earlier: [`results_wa_trading_hours.md`](results_wa_trading_hours.md)). They form seven reforms, each evaluated once. Where a reform was adopted in other states too, those adoptions are part of the same evaluation.

**Code:** `econ/analyses/high_evaluability/cases.py` (the case table in §8, as code) and `run.py` (`--blind` for the design stage). The same code runs both stages. Changes after registration go in §11 and are labelled "not pre-registered".

---

## 1. Questions

For each reform, did it change how many businesses entered or left the affected industry, in the direction the register hypothesises? Secondary: did it change prices where a matching CPI class exists? Descriptive: industry output and real pay per worker.

## 2. Outcomes

| Role | Outcome | Source |
|---|---|---|
| **Primary** | Entry rate: entries per 100 businesses operating at the start of the financial year, treated classes pooled | ABS CABEE, class × state, own-release vintage |
| Secondary | Exit rate (same definition) | CABEE |
| Secondary or descriptive (see §8) | 100 × log(CPI class / All groups), by capital city, quarterly 2001-Q1 to 2019-Q4 | ABS CPI, 17th series |
| Descriptive | Industry-division real value added per employed person; real compensation per employed person (deflated by each capital's CPI), 2000-01 onwards | State Accounts, Labour Force |

Business-count windows start in 2007-08 (2009-10 for NT) and end no later than 2017-18. That end avoids the 2018-19 vintage break and COVID; 2018-19 is used only as a robustness check.

## 3. Timing

**First exposed financial year:** the year containing the effective date, unless that date is 30 June, in which case the next year. Quarters follow the same rule.

**Clean controls:** each group of states adopting together (a *cohort*) is compared only with states not treated at any time up to the last year used for that cohort.

## 4. Estimator

**Stacked difference-in-differences.** For each cohort:
1. Take the cohort's states and its clean controls.
2. Estimate a two-way fixed-effects difference-in-differences (state and year effects) over the cohort's window.
3. Average the cohort estimates, weighted by the number of treated states.

With one cohort this is ordinary difference-in-differences. Stacking avoids comparing treated states with already-treated ones. `regimpact.evaluate.stacked` implements it, and tests on simulated data show it recovers known effects that grow over time.

**Net of a state-group shock.** The same estimator is applied to *placebo industry groups*: the same states and dates, but industries the reform did not touch. The primary estimate is the treated estimate minus the placebo mean. This removes shocks common to all industries in the treated states, as in the Perth case.

**Placebo groups:**
- **Eligible classes:** 4-digit classes outside the treated classes' divisions, with at least 50 businesses in the treated states in the base year (the year before the first exposed year).
- **Group size:** the same number of classes as the treated group. A one-class group enumerates every eligible class; larger groups use 1,000 random draws (seed 20261015).
- **Size matching:** a group's base-year size must be between 0.5 and 2 times the treated group's. If fewer than 19 groups qualify, the band widens to 0.25–4 times, then 0.1–10 times.
- **Completeness:** a group is used only if every treated state has every year of the window.

**Feasibility rules.** A reform's entry and exit are not evaluated, and are graded "Not identified" with no estimate headlined, if:
- the treated group has fewer than 100 businesses in the base year; or
- fewer than 19 placebo groups qualify.

## 5. Inference

- **p-value:** the two-sided rank of the net estimate among the centred placebo-group estimates.
- **Intervals:** 90% (and 95%, for reporting) from the placebo quantiles.
- **Smallest detectable effect:** 2.8 × the placebo SD.
- **Multiple testing:** Benjamini–Hochberg q-values across the batch's primary (entry) outcomes.

## 6. Year by year, diagnostics and robustness

- **Event study:** stacked event-time coefficients relative to the year before exposure, net of the placebo mean for each year, with 90% and 95% placebo bands.
- **Pre-trend diagnostic:** every pre-reform coefficient must lie inside its 95% placebo band.
- **Robustness**, each re-estimated with its own placebo distribution:
  1. the other ABS vintage;
  2. employing businesses only (non-employing removed);
  3. leave each control state out;
  4. leave each treated state out (when there are several);
  5. add 2018-19 (heavy vehicles, legal profession and energy only: no control is treated by then).

## 7. Decisions and grades

**Decision rule (primary outcome):**

| Verdict | Conditions |
|---|---|
| **Supports** the hypothesis | The net estimate has the hypothesised sign, p < 0.05, BH q < 0.10, the plain (un-netted) estimate has the same sign, and the other vintage keeps the sign |
| **Contradicts** it | The same conditions with the opposite sign |
| "Detects an increase / decrease" | For "mixed" hypotheses, under the same conditions |
| **Inconclusive** | Otherwise. Reported with the estimate and interval. "Inconclusive" when the 90% interval contains 0 and reaches ±5 per 100 |

**Grade:**

| Grade | Rule |
|---|---|
| **Not identified** | A feasibility rule fails, or a pre-reform coefficient lies outside its 95% band |
| **Weak** | Any robustness variant falls outside the primary 90% interval, or the case has a grade cap set in advance (§8) |
| **Strong** | At least two cohorts and three treated states, all checks passed, smallest detectable effect at most 5 per 100 |
| **Moderate** | Otherwise |

**Prices** are judged against placebo CPI classes: every class outside the related subgroups listed in §8. A detrended estimate is registered as a robustness check, with each city's pre-reform linear trend removed (decision E-31). **Productivity and pay** are judged against the other industry divisions, and are descriptive only.

## 8. Cases

| Case | Records | Treated classes | Cohorts (first exposed year) → controls | Division | Prices | Grade cap |
|---|---|---|---|---|---|---|
| NT container deposits | `nt-cds-2012` | 1211 soft drinks, 1212 beer, 2922 materials recovery | NT 2011-12, last 2016-17 → NSW, VIC, QLD, WA, TAS, ACT (SA excluded: scheme since 1977) | C | Soft drinks and beer, Darwin, from 2012-Q1 (secondary; expected up) | none |
| Childcare quality framework | `cth-nqf-childcare-2012`, `wa-nqf-childcare-2012` | 8710 child care | All but WA 2011-12 (first year only) → WA (adopted Aug 2012) | Q | Child care, from 2012-Q1 to 2012-Q2 (descriptive) | none |
| Retail energy price deregulation | `sa-…-2013`, `nsw-…-2014`, `qld-seq-…-2016` | 2640 electricity retailing | SA 2012-13, NSW 2014-15, QLD 2016-17 → TAS, ACT, WA, NT | D | Electricity, to 2019-Q2 before the default market offer (secondary; expected down) | Weak: business counts locate retailers at head office; state network charges |
| Heavy Vehicle National Law | six records (ACT, NSW, QLD, SA, TAS, VIC) | 4610 road freight | Six jurisdictions 2013-14 → WA, NT | I | none | none |
| Victorian taxi licences | `vic-taxi-licensing-2014` | 4623 taxi and other road transport | VIC 2014-15 only → all other states | I | Urban transport fares (descriptive) | Weak: unlicensed UberX from 2014; one usable year |
| Legal Profession Uniform Law | `nsw-…-2015`, `vic-…-2015` | 6931 legal services | NSW and VIC 2015-16 → QLD, SA, WA, TAS, ACT, NT | M | none | none |
| Ride-share legalisation | seven records (ACT, NSW, SA, QLD, TAS, VIC, NT) | 4623 taxi and other road transport | ACT and NSW 2015-16 (to 2016-17); SA, QLD, TAS 2016-17; VIC and NT 2017-18 → states not yet legal (VIC, NT, WA; then WA) | I | Urban transport fares (descriptive) | Weak: ride-share ran before it was legal; driver GST registration from Aug 2015 |

## 9. Design stage (blinded): what it found

Run on 15 October 2026 with every treated state's outcomes hidden from its first exposed period (`design.json`). The table shows what the rules decide before unblinding.

| Case | Treated businesses (base year) | Placebo groups | Smallest detectable effect: entry / exit (per 100) | Pre-reform check | Consequence |
|---|---|---|---|---|---|
| NT container deposits | **12** | 0 | n/a | n/a | **Entry and exit not evaluable** (feasibility rules). Prices: smallest detectable effect 18.6% against placebo classes |
| Childcare quality framework | 7,223 | 74 | 9.8 / 8.1 | passes | Evaluated. One control state, so only very large effects are detectable |
| Retail energy deregulation | **59** | 54 | n/a | n/a | **Entry and exit not evaluable**. Electricity prices: smallest detectable effect 9.5% |
| Heavy Vehicle National Law | 44,908 | 41 (band widened to 0.25–4×) | 9.4 / 9.9 | passes (largest pre-reform gap 6.9) | Evaluated |
| Victorian taxi licences | 3,931 | 43 | 4.2 / 3.7 | passes | Evaluated (capped at Weak) |
| Legal Profession Uniform Law | 13,060 | 39 | 7.0 / 2.6 | passes | Evaluated |
| Ride-share legalisation | 14,500 | 43 | 6.0 / 5.7 | **fails**: pre-reform coefficients 6 to 17 per 100 above the reference year | **Not identified**. Estimates are reported but not headlined |

**Productivity and pay.** Across the other 17 divisions, the placebo SD is 5 to 24 log points, so the smallest detectable effects are 14% to 66%. This confirms these outcomes are descriptive only.

**No design changes followed.** The rules above were applied as written.

## 10. Disclosures

- **No treated outcome was seen.** No post-reform outcome of a treated state, for any treated class, price class or division in this batch, was displayed before this plan was committed.
- **Earlier aggregates.** The Perth case's placebo industries were random WA classes, and could have included some of these classes. Only their aggregate mean and spread were reported.
- **Register status.** Every record in the batch is a draft.

## 11. Changes after registration

None yet.
