# Pre-analysis plan: the National Quality Framework for childcare and WA's seven-month delay

**Registered:** 18 October 2026, before the WA outcomes used here were estimated, with one disclosed exception (§7).

**Design-stage evidence:** `alicia/analyses/childcare_nqf_wa/design.json`, written by `design_review.py`. That script hides WA's childcare outcomes from January 2012 on, in code, before anything is computed.

**Earlier evaluation:** `childcare-nqf-2012` ([`results_high_evaluability.md`](results_high_evaluability.md)).

- That evaluation used annual CABEE entry and exit rates for 2011-12.
- This plan uses monthly and quarterly data and a different method (§3).

Changes after unblinding go in §10, and results from changed analyses are labelled "not pre-registered".

---

## 1. Records and hypothesis

- **Records:** `wa-nqf-childcare-2012` and `cth-nqf-childcare-2012` (family `childcare-nqf`).
- **The framework:** national quality standards, ratings, and phased staff ratio and qualification requirements. It started on **1 January 2012** in every jurisdiction except WA, and in WA on **1 August 2012**.
- **Hypothesis (from the records):** the framework **weakened** competition. Compliance and staffing costs deter small providers and favour larger operators. The expected direction is:
  - childcare exits up;
  - entries down;
  - prices up.
- **Alternative:** quality ratings give parents information, which may sharpen competition.

## 2. What can be identified

Every jurisdiction adopted the same law, so a long-run comparison is impossible. What WA's delay does allow:

- **On (Jan–Jul 2012):** WA is a clean comparison, not yet treated. A gap between WA and the rest should open in January 2012.
- **Off:** the gap should close when WA adopts in August 2012, if the effect is immediate and lasting.

The evaluation therefore measures the framework's **early effect**, over its first year and a half. Later phase-ins are not measured: qualifications in 2014, and further ratios in 2016.

## 3. Method: the on-off difference-in-differences (`alicia.evaluate.stagger`)

**The gap.** For each outcome, D_t = WA minus the other seven jurisdictions pooled.

- The gap's pre-period mean for each season (quarter of the year) is removed.
- Windows:

| Window | Quarterly outcomes | Monthly outcomes |
|---|---|---|
| Pre | 2009-Q1 to 2011-Q4 | Jan 2009 to Dec 2011 |
| On | 2012-Q1 to 2012-Q2 | Jan to Jul 2012 |
| Off | 2012-Q3 to 2013-Q2 | Aug 2012 to Jul 2013 |

**Three estimates, in units of the outcome:**

| Estimate | Formula | Meaning | Assumption |
|---|---|---|---|
| **Pooled** (primary) | mean of D over pre and off, minus mean over on | One effect, measured from the gap opening and closing | Effect immediate, lasting and equal |
| **Early** | pre − on | Effect on the other jurisdictions in their first seven months, against WA | None beyond parallel trends: clean comparison |
| **Late** | off − on | WA's own change when it adopted | Others' effect did not build up after July 2012 |
| On–off check | off − pre | Should be near zero | |

## 4. Outcomes

| Role | Outcome | Source | Placebos for inference |
|---|---|---|---|
| **Primary (competition)** | Childcare-named businesses' share of named-business ABN cancellations (%). Named businesses outside education (P) and health and social assistance (Q) form the denominator | ABN Bulk Extract (14 Oct 2026), industry inferred from names (childcare rule 82–91% precise on City of Melbourne names) | 32 named industries with 10–150 WA cancellations a year (2009–2011) |
| **Primary (prices)** | 100 × log(Child care CPI / All groups CPI), Perth vs the other seven capitals (mean) | ABS CPI 17th series | 84 CPI classes outside *Domestic and household services* |
| Secondary | Early and late estimates of both primaries; detrended versions (pre-period linear trend in the gap removed; required for prices by decision E-31) | | |
| Secondary | Childcare-named share of ABNs active since each month (entries, survivors only) | ABN | 30 named industries |
| Descriptive | Hours worked and employed persons, ANZSIC group 871 | LFS EQ06 | 65 groups with 4,000–25,000 WA workers |

**Fake dates.** Childcare itself at fake dates is added to every no-effect distribution: the same windows shifted back 2 or more whole years, whole window before 2012.

## 5. Inference and power (design stage, WA hidden)

| Outcome | WA pre-period level | No-effect estimates | SD (pooled) | Smallest detectable effect (pooled) | WA fake-date test (latest, 2 years earlier) |
|---|---|---|---|---|---|
| Exits share | 1.55% | 40 | 0.68 | **1.9 points**: only a doubling or more is detectable | +1.21, p = 0.10 (pass, at the threshold) |
| Prices | — | 97 | 2.85 | **8.0 log points** (detrended: 5.0) | −0.69, p = 0.73 (pass) |
| Entries share | 2.04% | 38 | 0.59 | 1.7 points | +0.05, p = 0.95 |
| Hours | — | 88 | 19.7 | 55: not usable | +7.9, p = 0.65 |

- **p-value:** share of no-effect estimates at least as large in absolute value.
- **90% interval:** the estimate minus the 95th and 5th percentiles of the no-effect estimates.
- **Benjamini–Hochberg q-values** are reported across the two primaries.

## 6. Findings, verdict and grade

**Finding for each primary outcome:**

| p-value | Finding |
|---|---|
| p < 0.10 | Increase or decrease |
| Otherwise | No detectable effect, with the smallest detectable effect stated |

**Verdict** (competition, from exits):

| Exits | Verdict |
|---|---|
| Significantly up | Supports the weakening hypothesis |
| Significantly down | Contradicts it |
| Otherwise | Inconclusive |

**Grade:**

- Capped at **Moderate**: one late jurisdiction, short windows.
- **Weak** if, for a primary outcome, the detrended variant reaches p < 0.10 with the opposite sign to a significant main estimate, or a significant main estimate's early and late parts have opposite signs.
- Design checks: hours and employment are descriptive only because their spread makes them uninformative. The exits fake-date test sits at the threshold, and this is reported.

## 7. Disclosure: prices are not fully blind

The earlier batch evaluation (15 Oct 2026) reported a descriptive estimate of Perth child-care prices relative to the other capitals for 2012-Q1 and Q2: **−4.3** log points (detrended **+4.8**). That is close to this plan's **early** estimand.

- The **pooled** and **late** estimands, and every other outcome here, were not estimated before.
- Prices are kept as a primary because they are the only outcome precise enough to detect a plausible effect. They do not set the verdict.

## 8. Choices made at the design stage on hidden outcomes

- **LFS hours and employment** are descriptive: WA's quarterly industry-group estimates swing by up to 30 log points.
- **Administrative childcare data** were looked for: approved services and fees by state, quarterly, from the Department of Education. They were not reachable (education.gov.au refused the connection; nothing on data.gov.au). Manual download is recommended for future work.
- **Comparison jurisdictions** are pooled into one "others" series, so small-state noise does not dominate.

## 9. Data and code

- **Panels:** `data/processed/abr_abn`, `abs_lfs`; CPI from the ABS Data API (cached).
- **Code:** `alicia/analyses/childcare_nqf_wa/`:
  - `spec.py`;
  - `design_review.py`;
  - `estimate.py` (`--blind` dry run first, which must reproduce the design-stage distributions);
  - `evaluation.py`;
  - `registration.json` (hashes before the unblinded run).

## 10. Changes after registration

None yet.

**Paths (18 October 2026, second rename).** File paths and the tool name were updated when ALCIA became ALICIA (`alcia/` became `alicia/`; the package and command `alcia` became `alicia`). The content is unchanged.
