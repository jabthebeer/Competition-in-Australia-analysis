# Results: the National Quality Framework for childcare and WA's seven-month delay

**Run:** 18 October 2026, once, after the plan [`pap_childcare_nqf_wa.md`](pap_childcare_nqf_wa.md) was committed (commit "Register the NQF-in-WA evaluation").

- **Before the run:** a blinded dry run reproduced the design-stage no-effect distributions.
- **Numbers:** `alicia/analyses/childcare_nqf_wa/estimate.json`.
- **Display paths:** `paths.json`.
- **Evaluation file:** `regulation-register/evaluations/childcare-nqf-wa-delay-2012.json`. It *follows* `childcare-nqf-2012`.

## 1. Headline

The framework started in January 2012 everywhere except WA, which followed in August 2012. That delay shows **no detectable early effect** on childcare business exits or entries, or on child care prices.

- **Exits:** childcare's share of named-business exits moved **+0.35 percentage points** (90% interval −0.87 to +1.12) on a WA base of 1.5%.
- **Prices:** child care prices relative to all prices moved **+0.3%** (−2.9 to +5.6).
- **Power:** only large effects could have been detected. For exits, a doubling of childcare's share; for prices, about 8%.

**Verdict:** inconclusive. **Grade:** Moderate.

## 2. Registered results (on-off design, pooled estimate)

| Outcome | Role | Estimate | 90% interval | p | No-effect range (5–95%) | Smallest detectable effect | Finding |
|---|---|---|---|---|---|---|---|
| Childcare share of named-business ABN cancellations (points) | Primary (competition) | **+0.35** | −0.87 to +1.12 | 0.68 | −0.77 to +1.22 (40) | 1.9 | No detectable effect |
| Child care CPI relative to all groups, Perth vs other capitals (%) | Primary (prices) | **+0.3** | −2.9 to +5.6 | 0.84 | −5.3 to +3.2 (97) | 8.0 | No detectable effect |
| Childcare share of new ABNs, survivors (points) | Secondary | +0.44 | −0.30 to +1.38 | 0.49 | −0.94 to +0.74 (38) | 1.7 | No detectable effect |
| Hours worked, group 871 (%) | Descriptive | −12.3 | −39.3 to +16.6 | 0.52 | | 55 | — |
| Employed persons, group 871 (%) | Descriptive | −27.0 | −65.3 to −1.1 | 0.18 | | 55 | — |

- Benjamini–Hochberg q-values across the two primaries: 0.84 for both.
- The employment interval excludes zero while p = 0.18 because its no-effect estimates are lopsided (5th to 95th percentile −26 to +38). Like hours, it is descriptive only.

## 3. The on–off pattern

Each outcome splits into three parts:

- **Early:** the other jurisdictions in January–July 2012, against WA.
- **Late:** WA's change when it adopted.
- **Gap after against before:** should be near zero.

| Outcome | Early | Late | Gap after against before | Detrended (pooled) |
|---|---|---|---|---|
| Exits share | +0.34 (p 0.68) | +0.37 (p 0.63) | +0.03 | +0.85 (p 0.32) |
| Prices | +0.6 (p 0.83) | −0.7 (p 0.63) | −1.3 | −0.4 (p 0.78) |
| Entries share | +0.37 | +0.64 | +0.27 | +0.31 |

- **Exits:** the gap opened in January and closed in August, the pattern an immediate framework effect would produce. It moved by about half the no-effect spread, so it cannot be told apart from noise.
- **Prices:** neither half moved. The pooled 90% interval rules out price effects above about +5.6% relative to other prices.

## 4. Comparison with the first evaluation

The batch evaluation (`childcare-nqf-2012`) used annual CABEE rates for 2011-12. It found:

- **Entry:** −0.3 per 100 (−5.9 to +4.3).
- **Exit:** +3.1 per 100 (−1.4 to +6.9).

Neither was distinguishable from zero. This evaluation uses monthly and quarterly data with the exact adoption dates, and it agrees: no detectable early effect.

Its descriptive early-2012 price estimate was −4.3. That figure came from different windows and was netted against other CPI classes. The early estimand here is +0.6. Both are inside their no-effect ranges.

## 5. Limits

- **Early effects only.** The ratio and qualification phase-ins of 2014 and 2016 applied everywhere and are not identified by WA's delay.
- **Small industry in the ABN data.** Childcare is about 1.5% of named-business exits, so only very large changes are detectable. Industry is inferred from names; the childcare rule is 82–91% precise on City of Melbourne names.
- **Entries are survivors.** They count only ABNs still active in October 2026.
- **LFS group estimates are too noisy** for WA over a seven-month window.
- **Better data exist but could not be reached:** Department of Education quarterly reports on approved services, usage and fees by state (education.gov.au refused the connection). They are the natural next source for any childcare regulation.

## 6. Deviations and disclosures

- **No deviations from the plan.**
- **Prices not fully blind:** see plan §7.
- **Display only:** `paths.py` computes the gap paths and placebo bands shown in the web viewer. It is not part of the registered inference and was written after the run.
- **Post-hoc check (not pre-registered).** The monthly chart shows one outlier: December 2010, a pre-period month when childcare was 15.6% of WA's few named exits (usually about 0.6%). Dropping that month from every series moves the pooled exits estimate to +0.45 (p = 0.51; 90% interval −0.62 to +1.23). The finding is unchanged.
