# Econometric results tables

Generated from `regulation-register/evaluations/` by `alicia tables`. Do not edit by hand: change the analysis's builder script and regenerate. The same tables, in LaTeX (booktabs and threeparttable), are in `econometric_tables.tex`.

One table per evaluation, newest first. Columns are estimators or registered specifications; each panel is one outcome. Every number comes from the analysis's registered outputs.

## As-of-right taxi licences in Victoria (2014): re-evaluation with saturated effects

`vic-taxi-licensing-2014-phase5` · evaluated 18 October 2026

**Table 1. As-of-right taxi licences in Victoria (2014): re-evaluation with saturated effects**

| | (1)<br>Two-way FE | (2)<br>State × period FE | (3)<br>Saturated FE | (4)<br>Two-way + controls | (5)<br>Imputation | (6)<br>Synthetic DiD | (7)<br>Generalised SC |
|---|---:|---:|---:|---:|---:|---:|---:|
| | *Fixed effects* |  |  |  |  | *Synthetic comparison* |  |
| ***Panel A. Business entry rate, per 100 businesses a year (primary outcome; 1 treated cell)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 0.22 | 0.22 | −0.36† | 0.21 | −0.36 | 0.67 | 1.99 |
|  | (3.27) | (3.28) | (1.24) | (3.27) | (1.24) | (3.27) | (3.27) |
|  | [0.951] | [0.951] | [0.683] | [0.951] | [0.683] | [0.658] | [0.293] |
| Observations | 25,082 | 25,082 | 25,082 | 25,082 | 25,082 | 18,976 | 18,976 |
| Units (cells) | 3,370 | 3,370 | 3,370 | 3,370 | 3,370 | 2,372 | 2,372 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 9.15 | 9.20 | 3.48 | 9.15 | 3.48 | 9.15 | 9.16 |
| Pre-reform mean, treated | 11.20 | 11.20 | 11.20 | 11.20 | 11.20 | 11.20 | 11.20 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| BH q-value |  |  | 0.854 |  |  |  |  |
| ***Panel B. Business exit rate, per 100 businesses a year (secondary outcome; 1 treated cell)*** |  |  |  |  |  |  |  |
| Reform × post (β) | −1.81 | −1.80 | −1.91\*\*† | −1.80 | −1.91\*\* | −1.21 | −1.72 |
|  | (0.94) | (0.94) | (0.84) | (0.94) | (0.84) | (0.88) | (0.94) |
|  | [0.122] | [0.122] | [0.049] | [0.122] | [0.049] | [0.171] | [0.146] |
| Observations | 25,082 | 25,082 | 25,082 | 25,082 | 25,082 | 18,976 | 18,976 |
| Units (cells) | 3,370 | 3,370 | 3,370 | 3,370 | 3,370 | 2,372 | 2,372 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 2.63 | 2.64 | 2.37 | 2.63 | 2.37 | 2.47 | 2.65 |
| Pre-reform mean, treated | 15.51 | 15.51 | 15.51 | 15.51 | 15.51 | 15.51 | 15.51 |
| Pre-trend test (k ≤ −2) |  |  | Fail |  |  |  |  |
| ***Panel C. Urban transport fares: prices relative to the CPI, 100 × log points (secondary outcome; 1 treated cell)*** |  |  |  |  |  |  |  |
| Reform × post (β) | −1.57 | −1.57 | −10.56\*\*† | −1.57 | −10.56\*\* | −9.18\*\* | −8.60\* |
|  | (12.76) | (12.89) | (2.95) | (12.77) | (2.95) | (2.94) | (4.32) |
|  | [0.902] | [0.902] | [0.024] | [0.902] | [0.024] | [0.025] | [0.075] |
| Observations | 29,024 | 29,024 | 29,024 | 29,024 | 29,024 | 28,560 | 28,560 |
| Units (cells) | 696 | 696 | 696 | 696 | 696 | 680 | 680 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 39 | 39 |
| MDE (80% power) | 35.76 | 36.13 | 8.26 | 35.78 | 8.26 | 8.25 | 12.09 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| ***Specification*** |  |  |  |  |  |  |  |
| Cell FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Period FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Class × period FE | No | No | Yes | No | Yes | No | No |
| State × period FE | No | Yes | Yes | No | Yes | No | No |
| Measured state controls | No | No | No | Yes | No | No | No |
| Synthetic weights | No | No | No | No | No | Yes | No |
| Interactive FE (factors) | No | No | No | No | No | No | Yes |

*Notes:* Panels A and B: entries and exits per 100 businesses operating at the start of the financial year, ANZSIC class × state, weighted by those businesses; 2007-08 to 2014-15 (8 periods), 431 classes, 8 states. Panel C: 100 × log of the CPI class relative to All groups, CPI class × capital city × quarter, unweighted; 2005-Q1 to 2015-Q2 (42 periods), 87 classes, 8 cities. Each column applies one estimator to the same panel. β is the average effect on the reform's classes in treated states (cities) over the window, net of the mean of the same estimator across the placebo groups. Columns (6) and (7) compare the treated group's average with reweighted untreated cells over each cohort's window; their observations and units are summed over cohorts. The placebo standard deviation is the spread of the same estimator across up to 40 placebo industry groups (or CPI classes) given the reform's states and dates: the randomization-inference analogue of a standard error. p-values rank the estimate among the centred placebo estimates; with 40 placebos the smallest attainable is about 0.024, so *** cannot occur. Clustered standard errors are not reported: with seven or eight states they are unreliable, and the registered inference uses placebos. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Placebo groups: placebo industry groups (business outcomes) or CPI classes (prices). Pre-trend test: every event-study coefficient with k ≤ −2 (saturated model, net of the placebo mean) lies inside its 95% placebo band; a failure means the outcome is not identified. BH q-value: Benjamini–Hochberg across the specification's primary outcomes. Source: alicia/analyses/phase5/reevaluations/estimate.json (registered run, 18 October 2026) and table_stats.json (samples, re-fitted to check every estimate reproduces). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


## Heavy Vehicle National Law (2014): re-evaluation with saturated effects

`heavy-vehicle-national-law-2014-phase5` · evaluated 18 October 2026

**Table 2. Heavy Vehicle National Law (2014): re-evaluation with saturated effects**

| | (1)<br>Two-way FE | (2)<br>State × period FE | (3)<br>Saturated FE | (4)<br>Two-way + controls | (5)<br>Imputation | (6)<br>Synthetic DiD | (7)<br>Generalised SC |
|---|---:|---:|---:|---:|---:|---:|---:|
| | *Fixed effects* |  |  |  |  | *Synthetic comparison* |  |
| ***Panel A. Business entry rate, per 100 businesses a year (primary outcome; 6 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 1.75 | 1.77 | 0.27† | 1.77 | 0.28 | 1.46 | 2.26 |
|  | (2.98) | (2.98) | (1.57) | (2.98) | (1.58) | (3.10) | (3.56) |
|  | [0.366] | [0.317] | [0.854] | [0.317] | [0.854] | [0.415] | [0.390] |
| Observations | 34,985 | 34,985 | 34,985 | 34,985 | 34,985 | 26,356 | 26,356 |
| Units (cells) | 3,406 | 3,406 | 3,406 | 3,406 | 3,406 | 2,396 | 2,396 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 8.34 | 8.34 | 4.40 | 8.34 | 4.42 | 8.67 | 9.96 |
| Pre-reform mean, treated | 11.95 | 11.95 | 11.95 | 11.95 | 11.95 | 11.95 | 11.95 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| BH q-value |  |  | 0.854 |  |  |  |  |
| ***Panel B. Business exit rate, per 100 businesses a year (secondary outcome; 6 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 0.56 | 0.56 | −0.67† | 0.56 | −0.68 | 0.42 | 0.56 |
|  | (1.11) | (1.11) | (1.05) | (1.11) | (1.05) | (1.00) | (1.11) |
|  | [0.634] | [0.634] | [0.585] | [0.634] | [0.585] | [0.658] | [0.610] |
| Observations | 34,985 | 34,985 | 34,985 | 34,985 | 34,985 | 26,356 | 26,356 |
| Units (cells) | 3,406 | 3,406 | 3,406 | 3,406 | 3,406 | 2,396 | 2,396 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 3.10 | 3.11 | 2.96 | 3.11 | 2.96 | 2.79 | 3.11 |
| Pre-reform mean, treated | 14.45 | 14.45 | 14.45 | 14.45 | 14.45 | 14.45 | 14.45 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| ***Specification*** |  |  |  |  |  |  |  |
| Cell FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Period FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Class × period FE | No | No | Yes | No | Yes | No | No |
| State × period FE | No | Yes | Yes | No | Yes | No | No |
| Measured state controls | No | No | No | Yes | No | No | No |
| Synthetic weights | No | No | No | No | No | Yes | No |
| Interactive FE (factors) | No | No | No | No | No | No | Yes |

*Notes:* Panels A and B: entries and exits per 100 businesses operating at the start of the financial year, ANZSIC class × state, weighted by those businesses; 2007-08 to 2017-18 (11 periods), 434 classes, 8 states. Each column applies one estimator to the same panel. β is the average effect on the reform's classes in treated states (cities) over the window, net of the mean of the same estimator across the placebo groups. Columns (6) and (7) compare the treated group's average with reweighted untreated cells over each cohort's window; their observations and units are summed over cohorts. The placebo standard deviation is the spread of the same estimator across up to 40 placebo industry groups (or CPI classes) given the reform's states and dates: the randomization-inference analogue of a standard error. p-values rank the estimate among the centred placebo estimates; with 40 placebos the smallest attainable is about 0.024, so *** cannot occur. Clustered standard errors are not reported: with seven or eight states they are unreliable, and the registered inference uses placebos. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Placebo groups: placebo industry groups (business outcomes) or CPI classes (prices). Pre-trend test: every event-study coefficient with k ≤ −2 (saturated model, net of the placebo mean) lies inside its 95% placebo band; a failure means the outcome is not identified. BH q-value: Benjamini–Hochberg across the specification's primary outcomes. Source: alicia/analyses/phase5/reevaluations/estimate.json (registered run, 18 October 2026) and table_stats.json (samples, re-fitted to check every estimate reproduces). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


## Legal Profession Uniform Law (2015): re-evaluation with saturated effects

`legal-profession-uniform-law-2015-phase5` · evaluated 18 October 2026

**Table 3. Legal Profession Uniform Law (2015): re-evaluation with saturated effects**

| | (1)<br>Two-way FE | (2)<br>State × period FE | (3)<br>Saturated FE | (4)<br>Two-way + controls | (5)<br>Imputation | (6)<br>Synthetic DiD | (7)<br>Generalised SC |
|---|---:|---:|---:|---:|---:|---:|---:|
| | *Fixed effects* |  |  |  |  | *Synthetic comparison* |  |
| ***Panel A. Business entry rate, per 100 businesses a year (primary outcome; 2 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | −2.75 | −2.77 | −1.26† | −2.77 | −1.26 | −2.94 | −3.64 |
|  | (7.06) | (7.08) | (1.60) | (7.06) | (1.61) | (6.45) | (6.89) |
|  | [0.325] | [0.325] | [0.475] | [0.325] | [0.475] | [0.250] | [0.200] |
| Observations | 34,784 | 34,784 | 34,784 | 34,784 | 34,784 | 25,993 | 25,993 |
| Units (cells) | 3,382 | 3,382 | 3,382 | 3,382 | 3,382 | 2,363 | 2,363 |
| Placebo groups | 39 | 39 | 39 | 39 | 39 | 39 | 39 |
| MDE (80% power) | 19.77 | 19.83 | 4.49 | 19.79 | 4.50 | 18.07 | 19.30 |
| Pre-reform mean, treated | 8.87 | 8.87 | 8.87 | 8.87 | 8.87 | 8.87 | 8.87 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| BH q-value |  |  | 0.780 |  |  |  |  |
| ***Panel B. Business exit rate, per 100 businesses a year (secondary outcome; 2 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 0.43 | 0.44 | −0.43† | 0.43 | −0.43 | 0.29 | 0.44 |
|  | (1.27) | (1.28) | (0.56) | (1.28) | (0.56) | (1.10) | (1.22) |
|  | [0.675] | [0.675] | [0.450] | [0.675] | [0.450] | [0.800] | [0.725] |
| Observations | 34,784 | 34,784 | 34,784 | 34,784 | 34,784 | 25,993 | 25,993 |
| Units (cells) | 3,382 | 3,382 | 3,382 | 3,382 | 3,382 | 2,363 | 2,363 |
| Placebo groups | 39 | 39 | 39 | 39 | 39 | 39 | 39 |
| MDE (80% power) | 3.57 | 3.59 | 1.56 | 3.58 | 1.56 | 3.07 | 3.40 |
| Pre-reform mean, treated | 7.91 | 7.91 | 7.91 | 7.91 | 7.91 | 7.91 | 7.91 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| ***Specification*** |  |  |  |  |  |  |  |
| Cell FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Period FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Class × period FE | No | No | Yes | No | Yes | No | No |
| State × period FE | No | Yes | Yes | No | Yes | No | No |
| Measured state controls | No | No | No | Yes | No | No | No |
| Synthetic weights | No | No | No | No | No | Yes | No |
| Interactive FE (factors) | No | No | No | No | No | No | Yes |

*Notes:* Panels A and B: entries and exits per 100 businesses operating at the start of the financial year, ANZSIC class × state, weighted by those businesses; 2007-08 to 2017-18 (11 periods), 431 classes, 8 states. Each column applies one estimator to the same panel. β is the average effect on the reform's classes in treated states (cities) over the window, net of the mean of the same estimator across the placebo groups. Columns (6) and (7) compare the treated group's average with reweighted untreated cells over each cohort's window; their observations and units are summed over cohorts. The placebo standard deviation is the spread of the same estimator across up to 40 placebo industry groups (or CPI classes) given the reform's states and dates: the randomization-inference analogue of a standard error. p-values rank the estimate among the centred placebo estimates; with 40 placebos the smallest attainable is about 0.024, so *** cannot occur. Clustered standard errors are not reported: with seven or eight states they are unreliable, and the registered inference uses placebos. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Placebo groups: placebo industry groups (business outcomes) or CPI classes (prices). Pre-trend test: every event-study coefficient with k ≤ −2 (saturated model, net of the placebo mean) lies inside its 95% placebo band; a failure means the outcome is not identified. BH q-value: Benjamini–Hochberg across the specification's primary outcomes. Source: alicia/analyses/phase5/reevaluations/estimate.json (registered run, 18 October 2026) and table_stats.json (samples, re-fitted to check every estimate reproduces). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


## National Quality Framework for childcare (2012): re-evaluation with synthetic DiD

`childcare-nqf-2012-phase5` · evaluated 18 October 2026

**Table 4. National Quality Framework for childcare (2012): re-evaluation with synthetic DiD**

| | (1)<br>Two-way FE | (2)<br>State × period FE | (3)<br>Saturated FE | (4)<br>Two-way + controls | (5)<br>Imputation | (6)<br>Synthetic DiD | (7)<br>Generalised SC |
|---|---:|---:|---:|---:|---:|---:|---:|
| | *Fixed effects* |  |  |  |  | *Synthetic comparison* |  |
| ***Panel A. Business entry rate, per 100 businesses a year (primary outcome; 7 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | −0.35 | −0.30 | 0.65 | −0.27 | 0.63 | −0.28† | −0.28 |
|  | (3.60) | (3.61) | (3.90) | (3.60) | (3.90) | (2.13) | (3.79) |
|  | [0.805] | [0.854] | [0.854] | [0.854] | [0.854] | [0.854] | [0.854] |
| Observations | 15,572 | 15,572 | 15,572 | 15,572 | 15,572 | 12,075 | 12,075 |
| Units (cells) | 3,389 | 3,389 | 3,389 | 3,389 | 3,389 | 2,415 | 2,415 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 10.10 | 10.11 | 10.92 | 10.10 | 10.91 | 5.97 | 10.63 |
| Pre-reform mean, treated | 15.59 | 15.59 | 15.59 | 15.59 | 15.59 | 15.59 | 15.59 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| BH q-value |  |  |  |  |  | 0.854 |  |
| ***Panel B. Business exit rate, per 100 businesses a year (secondary outcome; 7 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | −1.95\*\*† | −1.96\*\* | 3.22\* | −1.96\*\* | 3.22\* | −0.70 | −1.89\*\* |
|  | (0.80) | (0.80) | (1.73) | (0.80) | (1.73) | (0.90) | (0.87) |
|  | [0.049] | [0.049] | [0.073] | [0.049] | [0.073] | [0.366] | [0.049] |
| Observations | 15,572 | 15,572 | 15,572 | 15,572 | 15,572 | 12,075 | 12,075 |
| Units (cells) | 3,389 | 3,389 | 3,389 | 3,389 | 3,389 | 2,415 | 2,415 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 2.24 | 2.25 | 4.84 | 2.25 | 4.86 | 2.52 | 2.45 |
| Pre-reform mean, treated | 14.89 | 14.89 | 14.89 | 14.89 | 14.89 | 14.89 | 14.89 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| ***Panel C. Child care: prices relative to the CPI, 100 × log points (secondary outcome; 7 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | −4.67 | −4.67 | −0.71 | −4.67 | −0.71 | 4.38\*† | 20.69\* |
|  | (9.14) | (9.15) | (6.11) | (9.14) | (6.11) | (1.78) | (7.70) |
|  | [0.658] | [0.683] | [0.732] | [0.658] | [0.732] | [0.075] | [0.050] |
| Observations | 20,192 | 20,192 | 20,192 | 20,192 | 20,192 | 19,740 | 19,740 |
| Units (cells) | 680 | 680 | 680 | 680 | 680 | 658 | 658 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 39 | 39 |
| MDE (80% power) | 25.61 | 25.64 | 17.12 | 25.61 | 17.12 | 5.00 | 21.57 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| ***Specification*** |  |  |  |  |  |  |  |
| Cell FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Period FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Class × period FE | No | No | Yes | No | Yes | No | No |
| State × period FE | No | Yes | Yes | No | Yes | No | No |
| Measured state controls | No | No | No | Yes | No | No | No |
| Synthetic weights | No | No | No | No | No | Yes | No |
| Interactive FE (factors) | No | No | No | No | No | No | Yes |

*Notes:* Panels A and B: entries and exits per 100 businesses operating at the start of the financial year, ANZSIC class × state, weighted by those businesses; 2007-08 to 2011-12 (5 periods), 437 classes, 8 states. Panel C: 100 × log of the CPI class relative to All groups, CPI class × capital city × quarter, unweighted; 2005-Q1 to 2012-Q2 (30 periods), 85 classes, 8 cities. Each column applies one estimator to the same panel. β is the average effect on the reform's classes in treated states (cities) over the window, net of the mean of the same estimator across the placebo groups. Columns (6) and (7) compare the treated group's average with reweighted untreated cells over each cohort's window; their observations and units are summed over cohorts. The placebo standard deviation is the spread of the same estimator across up to 40 placebo industry groups (or CPI classes) given the reform's states and dates: the randomization-inference analogue of a standard error. p-values rank the estimate among the centred placebo estimates; with 40 placebos the smallest attainable is about 0.024, so *** cannot occur. Clustered standard errors are not reported: with seven or eight states they are unreliable, and the registered inference uses placebos. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Placebo groups: placebo industry groups (business outcomes) or CPI classes (prices). Pre-trend test: every event-study coefficient with k ≤ −2 (saturated model, net of the placebo mean) lies inside its 95% placebo band; a failure means the outcome is not identified. BH q-value: Benjamini–Hochberg across the specification's primary outcomes. Source: alicia/analyses/phase5/reevaluations/estimate.json (registered run, 18 October 2026) and table_stats.json (samples, re-fitted to check every estimate reproduces). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


## Northern Territory container deposit scheme (2012): re-evaluation with drink prices

`nt-container-deposits-2012-phase5` · evaluated 18 October 2026

**Table 5. Northern Territory container deposit scheme (2012): re-evaluation with drink prices**

| | (1)<br>Two-way FE | (2)<br>State × period FE | (3)<br>Saturated FE | (4)<br>Two-way + controls | (5)<br>Imputation | (6)<br>Synthetic DiD | (7)<br>Generalised SC |
|---|---:|---:|---:|---:|---:|---:|---:|
| | *Fixed effects* |  |  |  |  | *Synthetic comparison* |  |
| ***Panel A. Waters, soft drinks and juices: prices relative to the CPI, 100 × log points (primary outcome; 1 treated cell)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 10.72 | 10.74 | 7.62† | 10.74 | 7.62 | −3.13 | −0.79 |
|  | (16.48) | (16.66) | (7.85) | (16.52) | (7.85) | (7.59) | (10.30) |
|  | [0.512] | [0.537] | [0.195] | [0.512] | [0.195] | [0.650] | [0.975] |
| Observations | 29,449 | 29,449 | 29,449 | 29,449 | 29,449 | 28,917 | 28,917 |
| Units (cells) | 581 | 581 | 581 | 581 | 581 | 567 | 567 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 39 | 39 |
| MDE (80% power) | 46.18 | 46.68 | 21.98 | 46.30 | 21.98 | 21.26 | 28.85 |
| Pre-trend test (k ≤ −2) |  |  | Fail |  |  |  |  |
| BH q-value |  |  | 0.520 |  |  |  |  |
| ***Panel B. Beer: prices relative to the CPI, 100 × log points (secondary outcome; 1 treated cell)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 14.46 | 14.47 | 4.82† | 14.47 | 4.82 | −1.76 | −7.81 |
|  | (16.48) | (16.66) | (7.85) | (16.52) | (7.85) | (7.60) | (10.24) |
|  | [0.390] | [0.390] | [0.439] | [0.390] | [0.439] | [0.800] | [0.350] |
| Observations | 29,449 | 29,449 | 29,449 | 29,449 | 29,449 | 28,917 | 28,917 |
| Units (cells) | 581 | 581 | 581 | 581 | 581 | 567 | 567 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 39 | 39 |
| MDE (80% power) | 46.18 | 46.68 | 21.98 | 46.30 | 21.98 | 21.28 | 28.69 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| ***Specification*** |  |  |  |  |  |  |  |
| Cell FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Period FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Class × period FE | No | No | Yes | No | Yes | No | No |
| State × period FE | No | Yes | Yes | No | Yes | No | No |
| Measured state controls | No | No | No | Yes | No | No | No |
| Synthetic weights | No | No | No | No | No | Yes | No |
| Interactive FE (factors) | No | No | No | No | No | No | Yes |

*Notes:* Panels A and B: 100 × log of the CPI class relative to All groups, CPI class × capital city × quarter, unweighted; 2005-Q1 to 2017-Q3 (51 periods), 83 classes, 7 cities. Each column applies one estimator to the same panel. β is the average effect on the reform's classes in treated states (cities) over the window, net of the mean of the same estimator across the placebo groups. Columns (6) and (7) compare the treated group's average with reweighted untreated cells over each cohort's window; their observations and units are summed over cohorts. The placebo standard deviation is the spread of the same estimator across up to 40 placebo industry groups (or CPI classes) given the reform's states and dates: the randomization-inference analogue of a standard error. p-values rank the estimate among the centred placebo estimates; with 40 placebos the smallest attainable is about 0.024, so *** cannot occur. Clustered standard errors are not reported: with seven or eight states they are unreliable, and the registered inference uses placebos. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Placebo groups: placebo industry groups (business outcomes) or CPI classes (prices). Pre-trend test: every event-study coefficient with k ≤ −2 (saturated model, net of the placebo mean) lies inside its 95% placebo band; a failure means the outcome is not identified. BH q-value: Benjamini–Hochberg across the specification's primary outcomes. Source: alicia/analyses/phase5/reevaluations/estimate.json (registered run, 18 October 2026) and table_stats.json (samples, re-fitted to check every estimate reproduces). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


## Perth retail trading hours (2010 weeknights, 2012 Sundays): re-evaluation with saturated effects

`wa-trading-hours-2010-2012-phase5` · evaluated 18 October 2026

**Table 6. Perth retail trading hours (2010 weeknights, 2012 Sundays): re-evaluation with saturated effects**

| | (1)<br>Two-way FE | (2)<br>State × period FE | (3)<br>Saturated FE | (4)<br>Two-way + controls | (5)<br>Imputation | (6)<br>Synthetic DiD | (7)<br>Generalised SC |
|---|---:|---:|---:|---:|---:|---:|---:|
| | *Fixed effects* |  |  |  |  | *Synthetic comparison* |  |
| ***Panel A. Business entry rate, per 100 businesses a year (primary outcome; 3 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | −0.20 | −0.23 | 0.98† | −0.23 | 0.98 | −0.68 | −1.93 |
|  | (3.21) | (3.28) | (1.65) | (3.25) | (1.64) | (3.00) | (5.13) |
|  | [0.878] | [0.854] | [0.488] | [0.854] | [0.463] | [0.756] | [0.512] |
| Observations | 30,096 | 30,096 | 30,096 | 30,096 | 30,096 | 22,715 | 22,715 |
| Units (cells) | 2,954 | 2,954 | 2,954 | 2,954 | 2,954 | 2,065 | 2,065 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 9.00 | 9.18 | 4.62 | 9.10 | 4.60 | 8.40 | 14.39 |
| Pre-reform mean, treated | 16.07 | 16.07 | 16.07 | 16.07 | 16.07 | 16.07 | 16.07 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| BH q-value |  |  | 0.780 |  |  |  |  |
| ***Panel B. Business exit rate, per 100 businesses a year (secondary outcome; 3 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 1.50 | 1.50 | 0.01 | 1.50 | −0.03 | 1.30† | 1.56 |
|  | (1.31) | (1.32) | (1.52) | (1.31) | (1.50) | (1.07) | (1.31) |
|  | [0.244] | [0.244] | [1.000] | [0.244] | [0.951] | [0.220] | [0.244] |
| Observations | 30,096 | 30,096 | 30,096 | 30,096 | 30,096 | 22,715 | 22,715 |
| Units (cells) | 2,954 | 2,954 | 2,954 | 2,954 | 2,954 | 2,065 | 2,065 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 3.67 | 3.71 | 4.25 | 3.68 | 4.21 | 3.00 | 3.68 |
| Pre-reform mean, treated | 15.08 | 15.08 | 15.08 | 15.08 | 15.08 | 15.08 | 15.08 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| ***Specification*** |  |  |  |  |  |  |  |
| Cell FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Period FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Class × period FE | No | No | Yes | No | Yes | No | No |
| State × period FE | No | Yes | Yes | No | Yes | No | No |
| Measured state controls | No | No | No | Yes | No | No | No |
| Synthetic weights | No | No | No | No | No | Yes | No |
| Interactive FE (factors) | No | No | No | No | No | No | Yes |

*Notes:* Panels A and B: entries and exits per 100 businesses operating at the start of the financial year, ANZSIC class × state, weighted by those businesses; 2007-08 to 2017-18 (11 periods), 431 classes, 7 states. Each column applies one estimator to the same panel. β is the average effect on the reform's classes in treated states (cities) over the window, net of the mean of the same estimator across the placebo groups. Columns (6) and (7) compare the treated group's average with reweighted untreated cells over each cohort's window; their observations and units are summed over cohorts. The placebo standard deviation is the spread of the same estimator across up to 40 placebo industry groups (or CPI classes) given the reform's states and dates: the randomization-inference analogue of a standard error. p-values rank the estimate among the centred placebo estimates; with 40 placebos the smallest attainable is about 0.024, so *** cannot occur. Clustered standard errors are not reported: with seven or eight states they are unreliable, and the registered inference uses placebos. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Placebo groups: placebo industry groups (business outcomes) or CPI classes (prices). Pre-trend test: every event-study coefficient with k ≤ −2 (saturated model, net of the placebo mean) lies inside its 95% placebo band; a failure means the outcome is not identified. BH q-value: Benjamini–Hochberg across the specification's primary outcomes. Source: alicia/analyses/phase5/reevaluations/estimate.json (registered run, 18 October 2026) and table_stats.json (samples, re-fitted to check every estimate reproduces). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


## Retail energy price deregulation (SA 2013, NSW 2014, SEQ 2016): re-evaluation with electricity prices

`retail-energy-deregulation-2013-2016-phase5` · evaluated 18 October 2026

**Table 7. Retail energy price deregulation (SA 2013, NSW 2014, SEQ 2016): re-evaluation with electricity prices**

| | (1)<br>Two-way FE | (2)<br>State × period FE | (3)<br>Saturated FE | (4)<br>Two-way + controls | (5)<br>Imputation | (6)<br>Synthetic DiD | (7)<br>Generalised SC |
|---|---:|---:|---:|---:|---:|---:|---:|
| | *Fixed effects* |  |  |  |  | *Synthetic comparison* |  |
| ***Panel A. Electricity: prices relative to the CPI, 100 × log points (primary outcome; 3 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 35.65\*\* | 35.62\*\* | 9.43\*\*† | 35.64\*\* | 10.35\*\* | −9.97 | −12.50 |
|  | (17.33) | (17.47) | (3.24) | (17.34) | (3.42) | (4.54) | (9.38) |
|  | [0.049] | [0.049] | [0.024] | [0.049] | [0.024] | [0.125] | [0.100] |
| Observations | 34,328 | 34,328 | 34,328 | 34,328 | 34,328 | 72,210 | 72,210 |
| Units (cells) | 595 | 595 | 595 | 595 | 595 | 1,245 | 1,245 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 39 | 39 |
| MDE (80% power) | 48.55 | 48.94 | 9.08 | 48.56 | 9.58 | 12.71 | 26.29 |
| Pre-trend test (k ≤ −2) |  |  | Fail |  |  |  |  |
| BH q-value |  |  | 0.195 |  |  |  |  |
| ***Specification*** |  |  |  |  |  |  |  |
| Cell FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Period FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Class × period FE | No | No | Yes | No | Yes | No | No |
| State × period FE | No | Yes | Yes | No | Yes | No | No |
| Measured state controls | No | No | No | Yes | No | No | No |
| Synthetic weights | No | No | No | No | No | Yes | No |
| Interactive FE (factors) | No | No | No | No | No | No | Yes |

*Notes:* Panel A: 100 × log of the CPI class relative to All groups, CPI class × capital city × quarter, unweighted; 2005-Q1 to 2019-Q2 (58 periods), 85 classes, 7 cities. Each column applies one estimator to the same panel. β is the average effect on the reform's classes in treated states (cities) over the window, net of the mean of the same estimator across the placebo groups. Columns (6) and (7) compare the treated group's average with reweighted untreated cells over each cohort's window; their observations and units are summed over cohorts. The placebo standard deviation is the spread of the same estimator across up to 40 placebo industry groups (or CPI classes) given the reform's states and dates: the randomization-inference analogue of a standard error. p-values rank the estimate among the centred placebo estimates; with 40 placebos the smallest attainable is about 0.024, so *** cannot occur. Clustered standard errors are not reported: with seven or eight states they are unreliable, and the registered inference uses placebos. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Placebo groups: placebo industry groups (business outcomes) or CPI classes (prices). Pre-trend test: every event-study coefficient with k ≤ −2 (saturated model, net of the placebo mean) lies inside its 95% placebo band; a failure means the outcome is not identified. BH q-value: Benjamini–Hochberg across the specification's primary outcomes. Source: alicia/analyses/phase5/reevaluations/estimate.json (registered run, 18 October 2026) and table_stats.json (samples, re-fitted to check every estimate reproduces). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


## Ride-share legalisation (2015 to 2018): re-evaluation with saturated effects

`rideshare-legalisation-2015-2018-phase5` · evaluated 18 October 2026

**Table 8. Ride-share legalisation (2015 to 2018): re-evaluation with saturated effects**

| | (1)<br>Two-way FE | (2)<br>State × period FE | (3)<br>Saturated FE | (4)<br>Two-way + controls | (5)<br>Imputation | (6)<br>Synthetic DiD | (7)<br>Generalised SC |
|---|---:|---:|---:|---:|---:|---:|---:|
| | *Fixed effects* |  |  |  |  | *Synthetic comparison* |  |
| ***Panel A. Business entry rate, per 100 businesses a year (primary outcome; 7 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 33.16\*\* | 33.10\*\* | −2.24† | 33.12\*\* | −0.87 | 25.47\*\* | 26.99\*\* |
|  | (2.39) | (2.40) | (1.54) | (2.40) | (1.68) | (1.47) | (1.53) |
|  | [0.024] | [0.024] | [0.171] | [0.024] | [0.561] | [0.024] | [0.024] |
| Observations | 32,749 | 32,749 | 32,749 | 32,749 | 32,749 | 40,474 | 40,474 |
| Units (cells) | 3,382 | 3,382 | 3,382 | 3,382 | 3,382 | 3,967 | 3,967 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 6.70 | 6.73 | 4.32 | 6.72 | 4.72 | 4.12 | 4.29 |
| Pre-reform mean, treated | 12.44 | 12.44 | 12.44 | 12.44 | 12.44 | 12.44 | 12.44 |
| Pre-trend test (k ≤ −2) |  |  | Fail |  |  |  |  |
| BH q-value |  |  | 0.520 |  |  |  |  |
| ***Panel B. Business exit rate, per 100 businesses a year (secondary outcome; 7 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 3.73\*\* | 3.72\*\* | −0.33† | 3.73\*\* | −0.48 | 3.22\*\* | 3.13\*\* |
|  | (1.14) | (1.15) | (0.78) | (1.14) | (0.84) | (0.96) | (1.17) |
|  | [0.024] | [0.024] | [0.585] | [0.024] | [0.488] | [0.024] | [0.024] |
| Observations | 32,749 | 32,749 | 32,749 | 32,749 | 32,749 | 40,474 | 40,474 |
| Units (cells) | 3,382 | 3,382 | 3,382 | 3,382 | 3,382 | 3,967 | 3,967 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 3.20 | 3.21 | 2.17 | 3.20 | 2.35 | 2.69 | 3.29 |
| Pre-reform mean, treated | 13.74 | 13.74 | 13.74 | 13.74 | 13.74 | 13.74 | 13.74 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| ***Panel C. Urban transport fares: prices relative to the CPI, 100 × log points (secondary outcome; 7 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 5.18 | 5.18 | −1.56 | 5.19 | −1.02 | −0.28† | −0.12 |
|  | (12.93) | (13.00) | (2.91) | (12.94) | (2.96) | (1.77) | (3.51) |
|  | [0.732] | [0.756] | [0.488] | [0.732] | [0.634] | [0.850] | [0.950] |
| Observations | 36,158 | 36,158 | 36,158 | 36,158 | 36,158 | 65,440 | 65,440 |
| Units (cells) | 696 | 696 | 696 | 696 | 696 | 1,268 | 1,268 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 39 | 39 |
| MDE (80% power) | 36.23 | 36.42 | 8.15 | 36.25 | 8.28 | 4.97 | 9.82 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| ***Specification*** |  |  |  |  |  |  |  |
| Cell FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Period FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Class × period FE | No | No | Yes | No | Yes | No | No |
| State × period FE | No | Yes | Yes | No | Yes | No | No |
| Measured state controls | No | No | No | Yes | No | No | No |
| Synthetic weights | No | No | No | No | No | Yes | No |
| Interactive FE (factors) | No | No | No | No | No | No | Yes |

*Notes:* Panels A and B: entries and exits per 100 businesses operating at the start of the financial year, ANZSIC class × state, weighted by those businesses; 2007-08 to 2017-18 (11 periods), 431 classes, 8 states. Panel C: 100 × log of the CPI class relative to All groups, CPI class × capital city × quarter, unweighted; 2005-Q1 to 2018-Q4 (56 periods), 87 classes, 8 cities. Each column applies one estimator to the same panel. β is the average effect on the reform's classes in treated states (cities) over the window, net of the mean of the same estimator across the placebo groups. Columns (6) and (7) compare the treated group's average with reweighted untreated cells over each cohort's window; their observations and units are summed over cohorts. The placebo standard deviation is the spread of the same estimator across up to 40 placebo industry groups (or CPI classes) given the reform's states and dates: the randomization-inference analogue of a standard error. p-values rank the estimate among the centred placebo estimates; with 40 placebos the smallest attainable is about 0.024, so *** cannot occur. Clustered standard errors are not reported: with seven or eight states they are unreliable, and the registered inference uses placebos. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Placebo groups: placebo industry groups (business outcomes) or CPI classes (prices). Pre-trend test: every event-study coefficient with k ≤ −2 (saturated model, net of the placebo mean) lies inside its 95% placebo band; a failure means the outcome is not identified. BH q-value: Benjamini–Hochberg across the specification's primary outcomes. Source: alicia/analyses/phase5/reevaluations/estimate.json (registered run, 18 October 2026) and table_stats.json (samples, re-fitted to check every estimate reproduces). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


## Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023)

`e-conveyancing-2018-2023` · evaluated 18 October 2026

**Table 9. Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023)**

| | (1)<br>Two-way FE | (2)<br>State × period FE | (3)<br>Saturated FE | (4)<br>Two-way + controls | (5)<br>Imputation | (6)<br>Synthetic DiD | (7)<br>Generalised SC |
|---|---:|---:|---:|---:|---:|---:|---:|
| | *Fixed effects* |  |  |  |  | *Synthetic comparison* |  |
| ***Panel A. Business entry rate, per 100 businesses a year (primary outcome; 5 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | −3.00 | −3.03 | −0.58† | −3.05 | −0.62 | −2.95 | −1.72 |
|  | (4.08) | (4.09) | (1.03) | (4.08) | (1.19) | (3.67) | (9.51) |
|  | [0.366] | [0.342] | [0.537] | [0.342] | [0.537] | [0.317] | [0.610] |
| Observations | 46,506 | 46,506 | 46,506 | 46,506 | 46,506 | 82,209 | 82,209 |
| Units (cells) | 3,404 | 3,404 | 3,404 | 3,404 | 3,404 | 6,114 | 6,114 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 11.43 | 11.46 | 2.89 | 11.44 | 3.33 | 10.28 | 26.65 |
| Pre-reform mean, treated | 9.62 | 9.62 | 9.62 | 9.62 | 9.62 | 9.62 | 9.62 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| BH q-value |  |  | 0.537 |  |  |  |  |
| ***Panel B. Business exit rate, per 100 businesses a year (secondary outcome; 5 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 0.02 | −0.01 | 0.05† | 0.01 | −0.00 | −0.02 | −0.68 |
|  | (2.09) | (2.10) | (0.63) | (2.09) | (0.85) | (2.23) | (2.41) |
|  | [1.000] | [1.000] | [0.878] | [1.000] | [1.000] | [0.976] | [0.658] |
| Observations | 46,506 | 46,506 | 46,506 | 46,506 | 46,506 | 82,209 | 82,209 |
| Units (cells) | 3,404 | 3,404 | 3,404 | 3,404 | 3,404 | 6,114 | 6,114 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 5.85 | 5.87 | 1.76 | 5.85 | 2.38 | 6.25 | 6.76 |
| Pre-reform mean, treated | 7.82 | 7.82 | 7.82 | 7.82 | 7.82 | 7.82 | 7.82 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| ***Specification*** |  |  |  |  |  |  |  |
| Cell FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Period FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Class × period FE | No | No | Yes | No | Yes | No | No |
| State × period FE | No | Yes | Yes | No | Yes | No | No |
| Measured state controls | No | No | No | Yes | No | No | No |
| Synthetic weights | No | No | No | No | No | Yes | No |
| Interactive FE (factors) | No | No | No | No | No | No | Yes |

*Notes:* Panels A and B: entries and exits per 100 businesses operating at the start of the financial year, ANZSIC class × state, weighted by those businesses; 2009-10 to 2024-25 (16 periods), 431 classes, 8 states. Each column applies one estimator to the same panel. β is the average effect on the reform's classes in treated states (cities) over the window, net of the mean of the same estimator across the placebo groups. Columns (6) and (7) compare the treated group's average with reweighted untreated cells over each cohort's window; their observations and units are summed over cohorts. The placebo standard deviation is the spread of the same estimator across up to 40 placebo industry groups (or CPI classes) given the reform's states and dates: the randomization-inference analogue of a standard error. p-values rank the estimate among the centred placebo estimates; with 40 placebos the smallest attainable is about 0.024, so *** cannot occur. Clustered standard errors are not reported: with seven or eight states they are unreliable, and the registered inference uses placebos. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Placebo groups: placebo industry groups (business outcomes) or CPI classes (prices). Pre-trend test: every event-study coefficient with k ≤ −2 (saturated model, net of the placebo mean) lies inside its 95% placebo band; a failure means the outcome is not identified. BH q-value: Benjamini–Hochberg across the specification's primary outcomes. Source: alicia/analyses/phase5/new_families/estimate.json (registered run, 18 October 2026) and table_stats.json (samples, re-fitted to check every estimate reproduces). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


## Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021)

`fuel-price-reporting-2016-2021` · evaluated 18 October 2026

**Table 10. Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021)**

| | (1)<br>Two-way FE | (2)<br>State × period FE | (3)<br>Saturated FE | (4)<br>Two-way + controls | (5)<br>Imputation | (6)<br>Synthetic DiD | (7)<br>Generalised SC |
|---|---:|---:|---:|---:|---:|---:|---:|
| | *Fixed effects* |  |  |  |  | *Synthetic comparison* |  |
| ***Panel A. Automotive fuel: prices relative to the CPI, 100 × log points (primary outcome; 5 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 1.65 | 1.67 | −2.85† | 1.65 | −2.98 | 4.80 | 21.98\*\* |
|  | (13.79) | (13.90) | (2.39) | (13.81) | (2.56) | (3.08) | (4.30) |
|  | [0.902] | [0.902] | [0.195] | [0.902] | [0.293] | [0.125] | [0.025] |
| Observations | 42,480 | 42,480 | 42,480 | 42,480 | 42,480 | 114,810 | 114,810 |
| Units (cells) | 581 | 581 | 581 | 581 | 581 | 1,695 | 1,695 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 39 | 39 |
| MDE (80% power) | 38.65 | 38.93 | 6.70 | 38.68 | 7.16 | 8.64 | 12.05 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| BH q-value |  |  | 0.390 |  |  |  |  |
| ***Panel B. Business entry rate, per 100 businesses a year (secondary outcome; 5 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 0.52 | 0.51 | −0.24† | 0.51 | −0.02 | −0.20 | −0.69 |
|  | (1.74) | (1.74) | (0.78) | (1.74) | (3.92) | (1.14) | (1.96) |
|  | [0.634] | [0.634] | [0.854] | [0.634] | [1.000] | [0.829] | [0.537] |
| Observations | 38,060 | 38,060 | 38,060 | 38,060 | 38,060 | 65,419 | 65,419 |
| Units (cells) | 2,901 | 2,901 | 2,901 | 2,901 | 2,901 | 5,439 | 5,439 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 4.87 | 4.88 | 2.19 | 4.88 | 10.98 | 3.19 | 5.49 |
| Pre-reform mean, treated | 11.49 | 11.49 | 11.49 | 11.49 | 11.49 | 11.49 | 11.49 |
| Pre-trend test (k ≤ −2) |  |  | Fail |  |  |  |  |
| ***Panel C. Business exit rate, per 100 businesses a year (secondary outcome; 5 treated cells)*** |  |  |  |  |  |  |  |
| Reform × post (β) | 2.05 | 2.03 | −1.04† | 2.04 | −0.97 | 1.74 | 1.81\* |
|  | (1.64) | (1.64) | (0.80) | (1.64) | (0.83) | (1.53) | (1.51) |
|  | [0.122] | [0.122] | [0.146] | [0.122] | [0.220] | [0.122] | [0.098] |
| Observations | 38,060 | 38,060 | 38,060 | 38,060 | 38,060 | 65,419 | 65,419 |
| Units (cells) | 2,901 | 2,901 | 2,901 | 2,901 | 2,901 | 5,439 | 5,439 |
| Placebo groups | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 4.59 | 4.59 | 2.23 | 4.60 | 2.32 | 4.29 | 4.24 |
| Pre-reform mean, treated | 11.76 | 11.76 | 11.76 | 11.76 | 11.76 | 11.76 | 11.76 |
| Pre-trend test (k ≤ −2) |  |  | Pass |  |  |  |  |
| ***Specification*** |  |  |  |  |  |  |  |
| Cell FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Period FE | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Class × period FE | No | No | Yes | No | Yes | No | No |
| State × period FE | No | Yes | Yes | No | Yes | No | No |
| Measured state controls | No | No | No | Yes | No | No | No |
| Synthetic weights | No | No | No | No | No | Yes | No |
| Interactive FE (factors) | No | No | No | No | No | No | Yes |

*Notes:* Panel A: 100 × log of the CPI class relative to All groups, CPI class × capital city × quarter, unweighted; 2005-Q1 to 2025-Q2 (82 periods), 83 classes, 7 cities. Panels B and C: entries and exits per 100 businesses operating at the start of the financial year, ANZSIC class × state, weighted by those businesses; 2009-10 to 2024-25 (16 periods), 421 classes, 7 states. Each column applies one estimator to the same panel. β is the average effect on the reform's classes in treated states (cities) over the window, net of the mean of the same estimator across the placebo groups. Columns (6) and (7) compare the treated group's average with reweighted untreated cells over each cohort's window; their observations and units are summed over cohorts. The placebo standard deviation is the spread of the same estimator across up to 40 placebo industry groups (or CPI classes) given the reform's states and dates: the randomization-inference analogue of a standard error. p-values rank the estimate among the centred placebo estimates; with 40 placebos the smallest attainable is about 0.024, so *** cannot occur. Clustered standard errors are not reported: with seven or eight states they are unreliable, and the registered inference uses placebos. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Placebo groups: placebo industry groups (business outcomes) or CPI classes (prices). Pre-trend test: every event-study coefficient with k ≤ −2 (saturated model, net of the placebo mean) lies inside its 95% placebo band; a failure means the outcome is not identified. BH q-value: Benjamini–Hochberg across the specification's primary outcomes. Source: alicia/analyses/phase5/new_families/estimate.json (registered run, 18 October 2026) and table_stats.json (samples, re-fitted to check every estimate reproduces). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


## National Quality Framework for childcare (2012): WA's seven-month delay, monthly data

`childcare-nqf-wa-delay-2012` · evaluated 18 October 2026

**Table 11. National Quality Framework for childcare (2012): WA's seven-month delay: on-off estimates**

| | (1)<br>Pooled | (2)<br>Early | (3)<br>Late | (4)<br>Pooled | (5)<br>Early | (6)<br>Late |
|---|---:|---:|---:|---:|---:|---:|
| | *Registered (seasonal means removed)* |  |  | *Pre-trend also removed* |  |  |
| ***Panel A. Childcare share of business exits, percentage points (primary outcome; 36 / 7 / 12 months before / on / off)*** |  |  |  |  |  |  |
| Framework × WA timing (β) | 0.35† | 0.34 | 0.37 | 0.85 | 1.12 | 0.03 |
|  | (0.68) | (0.71) | (0.93) | (0.81) | (0.97) | (0.94) |
|  | [0.683] | [0.683] | [0.634] | [0.317] | [0.268] | [0.976] |
| No-effect estimates | 40 | 40 | 40 | 40 | 40 | 40 |
| MDE (80% power) | 1.91 | 1.99 | 2.61 | 2.28 | 2.71 | 2.63 |
| Gap after WA adopted vs pre-2012 | 0.03 |  |  | −1.10 |  |  |
| WA share before 2012, % | 1.55 | 1.55 | 1.55 | 1.55 | 1.55 | 1.55 |
| BH q-value | 0.837 |  |  |  |  |  |
| ***Panel B. Child care prices relative to all prices, 100 × log points (primary outcome; 12 / 2 / 4 quarters before / on / off)*** |  |  |  |  |  |  |
| Framework × WA timing (β) | 0.29† | 0.62 | −0.72 | −0.42 | −0.48 | −0.24 |
|  | (2.85) | (3.51) | (2.14) | (1.78) | (2.18) | (2.85) |
|  | [0.837] | [0.827] | [0.633] | [0.775] | [0.837] | [0.857] |
| No-effect estimates | 97 | 97 | 97 | 97 | 97 | 97 |
| MDE (80% power) | 8.00 | 9.83 | 6.01 | 5.00 | 6.10 | 7.97 |
| Gap after WA adopted vs pre-2012 | −1.34 |  |  | 0.24 |  |  |
| BH q-value | 0.837 |  |  |  |  |  |
| ***Panel C. Childcare share of new ABNs, percentage points (secondary outcome; 36 / 7 / 12 months before / on / off)*** |  |  |  |  |  |  |
| Framework × WA timing (β) | 0.44† | 0.37 | 0.64 | 0.31 | 0.17 | 0.74 |
|  | (0.59) | (0.65) | (0.68) | (0.75) | (0.93) | (0.69) |
|  | [0.487] | [0.564] | [0.333] | [0.692] | [0.795] | [0.308] |
| No-effect estimates | 38 | 38 | 38 | 38 | 38 | 38 |
| MDE (80% power) | 1.66 | 1.82 | 1.90 | 2.09 | 2.60 | 1.93 |
| Gap after WA adopted vs pre-2012 | 0.27 |  |  | 0.57 |  |  |
| WA share before 2012, % | 2.04 | 2.04 | 2.04 | 2.04 | 2.04 | 2.04 |
| ***Specification*** |  |  |  |  |  |  |
| Seasonal means removed | Yes | Yes | Yes | Yes | Yes | Yes |
| Linear pre-trend removed | No | No | No | Yes | Yes | Yes |

*Notes:* Panels A and C: businesses whose names say childcare, as a share of all named businesses' ABN cancellations (A) or of new ABNs still active in October 2026 (C), monthly from January 2009 to July 2013. Panel B: the child care CPI relative to All groups, Perth against the other capitals, quarterly from 2009-Q1 to 2013-Q2. On-off difference-in-differences (alicia.evaluate.stagger) on the gap between WA and the mean of the other seven jurisdictions, less its pre-2012 mean for each season. The framework started in January 2012 everywhere but WA, which followed in August 2012 (2012-Q3 in quarterly data). Pooled: one effect from the gap opening and closing. Early: the other jurisdictions in January to July 2012 against WA, not yet treated. Late: WA's change when it adopted, against the others (assumes their effect did not build up). The gap row shows whether the gap returned to its pre-2012 level once both had adopted. The placebo standard deviation is the spread of the no-effect estimates: the same estimator for placebo industries (CPI classes, Labour Force groups) over the same windows and for childcare at fake dates before 2012. p-values rank the estimate among them. BH q-value: Benjamini-Hochberg across the two primary outcomes. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Source: alicia/analyses/childcare_nqf_wa/estimate.json (registered run, 18 October 2026) and design.json (windows, pre-2012 levels). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


**Table 12. National Quality Framework for childcare (2012): WA's seven-month delay: hours and employment (descriptive)**

| | (1)<br>Pooled | (2)<br>Early | (3)<br>Late | (4)<br>Pooled | (5)<br>Early | (6)<br>Late |
|---|---:|---:|---:|---:|---:|---:|
| | *Registered (seasonal means removed)* |  |  | *Pre-trend also removed* |  |  |
| ***Panel A. Hours worked in child care, 100 × log points (descriptive; 12 / 2 / 4 quarters before / on / off)*** |  |  |  |  |  |  |
| Framework × WA timing (β) | −12.28 | −12.14 | −12.71 | −10.40 | −9.21 | −13.97 |
|  | (19.73) | (21.39) | (22.02) | (21.88) | (26.33) | (23.41) |
|  | [0.517] | [0.551] | [0.562] | [0.596] | [0.730] | [0.573] |
| No-effect estimates | 88 | 88 | 88 | 88 | 88 | 88 |
| MDE (80% power) | 55.26 | 59.91 | 61.69 | 61.31 | 73.75 | 65.60 |
| Gap after WA adopted vs pre-2012 | −0.57 |  |  | −4.76 |  |  |
| ***Panel B. Employment in child care, 100 × log points (descriptive; 12 / 2 / 4 quarters before / on / off)*** |  |  |  |  |  |  |
| Framework × WA timing (β) | −27.05 | −29.15 | −20.75 | −24.18 | −24.68 | −22.66 |
|  | (19.73) | (20.67) | (21.96) | (22.22) | (25.62) | (22.33) |
|  | [0.180] | [0.202] | [0.360] | [0.258] | [0.292] | [0.281] |
| No-effect estimates | 88 | 88 | 88 | 88 | 88 | 88 |
| MDE (80% power) | 55.27 | 57.91 | 61.53 | 62.24 | 71.78 | 62.55 |
| Gap after WA adopted vs pre-2012 | 8.40 |  |  | 2.02 |  |  |
| ***Specification*** |  |  |  |  |  |  |
| Seasonal means removed | Yes | Yes | Yes | Yes | Yes | Yes |
| Linear pre-trend removed | No | No | No | Yes | Yes | Yes |

*Notes:* Labour Force industry group 871 (child care services), WA against the other jurisdictions, quarterly from 2009-Q1 to 2013-Q2. Registered as descriptive: WA's quarterly estimates for one group are too noisy to test. On-off difference-in-differences (alicia.evaluate.stagger) on the gap between WA and the mean of the other seven jurisdictions, less its pre-2012 mean for each season. The framework started in January 2012 everywhere but WA, which followed in August 2012 (2012-Q3 in quarterly data). Pooled: one effect from the gap opening and closing. Early: the other jurisdictions in January to July 2012 against WA, not yet treated. Late: WA's change when it adopted, against the others (assumes their effect did not build up). The gap row shows whether the gap returned to its pre-2012 level once both had adopted. The placebo standard deviation is the spread of the no-effect estimates: the same estimator for placebo industries (CPI classes, Labour Force groups) over the same windows and for childcare at fake dates before 2012. p-values rank the estimate among them. BH q-value: Benjamini-Hochberg across the two primary outcomes. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Source: alicia/analyses/childcare_nqf_wa/estimate.json (registered run, 18 October 2026) and design.json (windows, pre-2012 levels). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


## Perth 9pm weeknight trading (2010), re-evaluated with new data

`wa-trading-hours-weeknight-2010-new-data` · evaluated 18 October 2026

**Table 13. Perth 9pm weeknight trading (2010): retail businesses in metropolitan Perth relative to regional WA**

| | (1)<br>Registered | (2)<br>Small businesses only | (3)<br>Mandurah in Perth | (4)<br>WA outback left out | (5)<br>No size floor on placebos |
|---|---:|---:|---:|---:|---:|
| | *Main* | *Registered robustness checks* |  |  |  |
| ***Retail businesses, Perth minus regional WA, net of other industries (100 × log points; primary outcome)*** |  |  |  |  |  |
| WA × post (β) | −1.75† | −1.19 | −2.10 | −1.55 | −1.75 |
|  | (3.61) | (3.77) | (3.60) | (3.75) | (15.86) |
|  | [0.700] | [0.767] | [0.600] | [0.690] | [0.787] |
| Observations (units × years) | 24 (6 × 4) | 24 (6 × 4) | 24 (6 × 4) | 24 (6 × 4) | 24 (6 × 4) |
| No-effect estimates | 59 | 59 | 59 | 57 | 107 |
| MDE (80% power) | 10.12 | 10.57 | 10.09 | 10.50 | 44.44 |
| Perth retail businesses, June 2010 | 10,284 | 9,299 | 10,793 | 10,284 | 10,284 |
| Regional WA retail businesses, June 2010 | 3,271 | 2,966 | 3,271 | 2,184 | 3,271 |
| BH q-value | 0.700 |  |  |  |  |
| ***Specification*** |  |  |  |  |  |
| Unit and year fixed effects | Yes | Yes | Yes | Yes | Yes |
| Other industries netted out | Yes | Yes | Yes | Yes | Yes |

*Notes:* Each unit is a state's capital-minus-rest gap in log retail businesses (ANZSIC division G), less the same gap for other industries (CABEE by SA4). WA is treated (metropolitan Perth: SA4s 503-507); NSW, Victoria, Queensland, Tasmania and the NT are comparisons. Counts at 30 June 2009 and 2010 (before) and 2011 and 2012 (after); two-way fixed effects on unit and year. Columns: (2) non-employing businesses and those with fewer than 20 employees; (3) Mandurah (SA4 502) counted in Perth; (4) the WA outback (SA4s 508, 510, 511) left out of regional WA; (5) placebo cells of any size (otherwise at least 1,000 businesses in both parts at June 2010). The placebo standard deviation is the spread of the same estimator for other industries in every state and for retail in the comparison states; p-values rank the estimate among those placebo estimates. BH q-value: Benjamini-Hochberg across the two primary outcomes. MDE: the smallest effect detectable with 80% power at the 5% level (2.8 × the placebo standard deviation). Source: alicia/analyses/wa_weeknight_2010/estimate.json (registered run, 18 October 2026). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


**Table 14. Perth 9pm weeknight trading (2010): turnover of supermarkets, clothing and department stores, WA against other states**

| | (1)<br>Registered | (2)<br>Pre-trend removed | (3)<br>All fake dates | (4)<br>Net of other retail and food | (5)<br>Net of food services | (6)<br>Supermarkets | (7)<br>Clothing | (8)<br>Department stores | (9)<br>Supermarkets vs specialised food |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| | *Main* | *Registered robustness checks* |  |  |  | *By store type* |  |  | *Composition* |
| ***Turnover, 100 × log points (primary outcome; column 9 a secondary outcome)*** |  |  |  |  |  |  |  |  |  |
| WA × post (β) | 2.04† | 7.87\* | 2.04 | −6.10 | −19.28\* | 2.88 | −5.38 | 1.04 | 10.55 |
|  | (3.46) | (4.21) | (4.33) | (5.45) | (11.22) | (4.27) | (14.80) | (4.33) | (19.48) |
|  | [0.497] | [0.060] | [0.599] | [0.230] | [0.085] | [0.366] | [0.731] | [0.817] | [0.548] |
| Observations (states × months) | 225 (5 × 45) | 225 (5 × 45) | 225 (5 × 45) | 225 (5 × 45) | 225 (5 × 45) | 225 (5 × 45) | 225 (5 × 45) | 225 (5 × 45) | 225 (5 × 45) |
| No-effect estimates | 834 | 834 | 1459 | 760 | 834 | 834 | 834 | 834 | 760 |
| MDE (80% power) | 9.70 | 11.78 | 12.14 | 15.28 | 31.43 | 11.97 | 41.46 | 12.13 | 54.59 |
| BH q-value | 0.700 |  |  |  |  |  |  |  |  |
| ***Specification*** |  |  |  |  |  |  |  |  |  |
| State and month fixed effects | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Linear pre-trend removed | No | Yes | No | No | No | No | No | No | No |
| Fake dates used | From 1995 | From 1995 | All | From 1995 | From 1995 | From 1995 | From 1995 | From 1995 | From 1995 |

*Notes:* 100 × log monthly turnover (ABS Retail Trade, seasonally adjusted), WA against NSW, Victoria, Queensland and the ACT: July 2008 to June 2010 before, November 2010 to July 2012 after, July to October 2010 left out. Treated stores: supermarkets and grocery stores, clothing retailing and department stores. Columns: (2) each state's linear pre-reform trend removed; (3) every fake date in the data in the no-effect set; (4) less other retail and cafes, restaurants and takeaway; (5) less cafes, restaurants and takeaway only (triple difference); (6)-(8) one store type; (9) supermarkets relative to other specialised food retailing. The placebo standard deviation is the spread of the same estimator at fake dates for every state and for each comparison state at the real date; p-values rank the estimate among them. Source: alicia/analyses/wa_weeknight_2010/estimate.json (registered run, 18 October 2026). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.


**Table 15. Perth 9pm weeknight trading (2010): hours worked and employment in the same stores (descriptive)**

| | (1)<br>Hours worked | (2)<br>Employment | (3)<br>Hours net of food services | (4)<br>Hours, pre-trend removed |
|---|---:|---:|---:|---:|
| ***Hours and employment, 100 × log points (descriptive: failed the design-stage check)*** |  |  |  |  |
| WA × post (β) | 1.61 | −1.52 | −0.21 | −8.69 |
|  | (6.89) | (5.73) | (9.61) | (7.45) |
|  | [0.847] | [0.789] | [0.983] | [0.237] |
| Observations (states × quarters) | 124 (4 × 31) | 124 (4 × 31) | 124 (4 × 31) | 124 (4 × 31) |
| No-effect estimates | 227 | 227 | 227 | 227 |
| MDE (80% power) | 19.32 | 16.06 | 26.91 | 20.86 |
| ***Specification*** |  |  |  |  |
| State and quarter fixed effects | Yes | Yes | Yes | Yes |
| Linear pre-trend removed | No | No | No | Yes |

*Notes:* Labour Force (EQ06), supermarkets, clothing and department stores (groups 411, 425, 426), WA against NSW, Victoria and Queensland, quarterly: 24 quarters before (August 2004 to May 2010), August 2010 left out, 7 after (November 2010 to May 2012). Column (3) less cafes, restaurants and takeaway (group 451). Descriptive only: WA failed the fake-date test at the design stage, so none of these columns supports a finding. The placebo standard deviation is the spread of the same estimator at fake dates for every state and for each comparison state at the real date. Source: alicia/analyses/wa_weeknight_2010/estimate.json (registered run, 18 October 2026). Placebo standard deviation in parentheses; two-sided p-values in brackets. * p < 0.10, ** p < 0.05, *** p < 0.01. † The registered (pre-specified) estimator for that outcome.
