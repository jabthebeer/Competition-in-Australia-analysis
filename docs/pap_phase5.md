# Pre-analysis plan: Phase 5 re-evaluations and the first new-family evaluations

**Registered:** 18 October 2026. Written after the blinded design stage and before any treated post-reform outcome was computed for these designs.

**Specifications:**
- `alicia/specs/phase5-reevaluations.json`: eight re-evaluations.
- `alicia/specs/phase5-new-families.json`: two new families.

These files hold every case's records, outcomes, classes or CPI class, cohorts, windows, registered estimator layer, check layers and placebo pools. They are the registered design; this plan explains them.

**Code:**
- `alicia/analyses/phase5/run.py` (design, dry run, estimate);
- `evaluations.py` (register files).

**Stages:** `alicia spec run <id>` runs the four stages. The registered estimate runs only after the design outputs are committed.

**Forward plan:** Phase 5 ([`forward_plan_macro_controls.md`](forward_plan_macro_controls.md) §6); layer choices from the blinded power study ([`power_study.md`](power_study.md) §4).

## 1. What is evaluated

| Evaluation | Records | Outcomes (registered layer) | Follows and supersedes |
|---|---|---|---|
| Perth retail trading hours (2010, 2012) | WA weeknight 2010, WA Sunday 2012 | Entry (saturated), exit (synthetic DiD) | `wa-trading-hours-2010-2012` |
| National Quality Framework (2012) | Commonwealth and WA NQF | Entry (synthetic DiD), exit (two-way), child care prices (synthetic DiD) | `childcare-nqf-2012` |
| Heavy Vehicle National Law (2014) | Six adopting jurisdictions | Entry, exit (saturated) | `heavy-vehicle-national-law-2014` |
| Victorian taxi licences (2014) | Victoria | Entry, exit, urban transport fares (saturated) | `vic-taxi-licensing-2014` |
| Legal Profession Uniform Law (2015) | NSW, Victoria | Entry, exit (saturated) | `legal-profession-uniform-law-2015` |
| Ride-share legalisation (2015–2018) | Seven jurisdictions | Entry, exit (saturated), fares (synthetic DiD) | `rideshare-legalisation-2015-2018` |
| NT container deposits (2012) | NT | Soft drink prices (primary), beer prices (saturated) | `nt-container-deposits-2012` |
| Retail energy deregulation (2013–2016) | SA, NSW, SEQ | Electricity prices (saturated) | `retail-energy-deregulation-2013-2016` |
| **New:** fuel price reporting (2016–2021) | NSW, NT, QLD, TAS, SA | Automotive fuel prices (primary), fuel retailer entry and exit (saturated) | — |
| **New:** e-conveyancing (2018–2023) | NSW, WA, VIC, SA, QLD | Legal services entry (primary) and exit (saturated) | — |

**Not re-evaluated here:**
- **Perth weeknight trading with new data** (`wa-trading-hours-weeknight-2010-new-data`).
- **The NQF in WA with monthly data** (`childcare-nqf-wa-delay-2012`).

These already use the new data with designs (places within WA; the on-off stagger) that the layers here do not replace. They stay current alongside the re-evaluations.

**Archiving:** each re-evaluation names the evaluation it replaces (`supersedes`). The menu then shows the earlier one as archived, below the new results.

## 2. Disclosure

- **Re-evaluations.** The earlier evaluations' estimates were known when these specifications were written. To limit the scope for choosing a design by its result:
  - The windows, cohorts, classes, comparison states and grade caps are those of the earlier registered designs, unchanged.
  - The estimator layer for each outcome is the one the blinded power study chose (§4 there), where no reform's effect was estimated.
  - Where the study's best layers were within 10% of each other (equal within its sampling error), the simpler or more consistent layer was registered:
    - HVNL exits: saturated (3.0 against 2.8 for synthetic DiD), so one layer covers both outcomes;
    - NT drink prices: saturated (22.0 against 21.3);
    - Victorian taxi fares: saturated (8.3, tied with synthetic DiD).
  - For Perth trading hours the study's layers come from the weeknight window (2010-11 and 2011-12), applied here to the earlier evaluation's longer window (to 2017-18).
- **New families.** No outcome of the treated states after adoption has been computed for fuel price reporting or e-conveyancing in any earlier analysis. The power study hid them.

## 3. Data

- **Business counts:** CABEE entries and exits by ANZSIC class × state × financial year, all 15 releases stitched (latest vintage, to 2024-25).
  - The earlier batch used the vintage registered at the time (to 2019-20). The re-evaluations use the latest counts over the same windows. That is the "new data" for these outcomes.
- **Prices:** ABS CPI 17th series, every expenditure class by capital city, 2001-Q1 to 2025-Q3. The price is 100 × log(class / All groups).

## 4. Estimation

**Layers** (all run; one registered per outcome):
- two-way;
- cell + state × year;
- saturated (class × period and state × period effects);
- two-way with measured state controls;
- imputation;
- synthetic DiD;
- generalised synthetic control.

Definitions are in `power_study.md` §2.

**Registered estimate:** the registered layer's coefficient on the treated classes in treated states over each cohort's window, net of the mean of the same layer's placebo estimates.

**No-effect distribution:** the same layer applied to up to 40 placebo industry groups (size-matched, outside the treated divisions; the batch's rule) or 40 CPI classes outside the related subgroups, at the reform's states and dates, with treated cells hidden.
- p-value: share of centred placebo estimates at least as large in absolute value.
- 90% interval: the estimate minus the 95th and 5th percentiles of the centred placebos.
- MDE: 2.8 × their standard deviation.

**Robustness (registered):**
- the check layers named for each outcome;
- the registered layer under placebo states and fake dates (p-values reported where there are 10 or more draws).

**Year by year:** the event-study form of the saturated model, with years before −5 and after +5 pooled at the ends and k = −1 omitted. Coefficients are net of the placebo mean, with 90% placebo bands.

**Multiple testing:** Benjamini–Hochberg q-values across the primary outcomes within each specification.

## 5. Decision rule and grade (as the high-evaluability batch)

**Feasibility:** at least 100 treated businesses in the base year and 19 placebo groups (business counts). Otherwise the outcome is not identified.

**Pre-trend check:** if any pre-reform year (k ≤ −2) of the primary outcome's treated coefficient, net of the placebo mean, lies outside its 95% placebo band, the evaluation is **not identified**.
- This was checked at the design stage on the pre-reform rows. They are visible with treated post-periods hidden, so the check was known before unblinding.
- With four pre-reform years tested, about one design in six fails by chance. The rule is kept as registered for the batch.

**Verdict:**
- An effect is **detected** if the primary p < 0.05, q < 0.10, and every check layer has the same sign.
- With an enhancing hypothesis, more entry and lower prices **support** it; the opposite **contradicts** it. Weakening is the mirror image.
- Mixed hypotheses (fuel reporting, e-conveyancing, container deposits) report **increase** or **decrease**.
- Otherwise **inconclusive** (no detectable effect).

**Grade:**
- Weak if any check layer falls outside the registered 90% interval.
- Strong if there are two or more cohorts, three or more treated states, an MDE of 5 or less (per 100 or log points), and the checks agree.
- Moderate otherwise.
- Grade caps set before the earlier batch carry over: Victorian taxis, ride-share and energy deregulation are capped at Weak.

## 6. Design stage (blinded)

To be filled in from `design.json` before unblinding (section 6 of the committed plan).

## 7. Changes after registration

None yet. Any change after unblinding will be listed here and labelled "not pre-registered".
