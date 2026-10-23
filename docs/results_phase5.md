# Results: Phase 5 re-evaluations and the first new-family evaluations

**Run:** 18 October 2026, 21:04 UTC. Each specification ran once, after its blinded design and dry-run outputs were committed. The plan is [`pap_phase5.md`](pap_phase5.md).

**Specifications:** `alicia/specs/phase5-reevaluations.json` and `phase5-new-families.json`.

**Numbers:** `alicia/analyses/phase5/{reevaluations,new_families}/estimate.json`. The one post-unblinding check is in `reevaluations/posthoc.json`.

**Evaluation files:** `regulation-register/evaluations/` (10 new). Eight are re-evaluations: each *supersedes* an earlier evaluation, which is now archived (§6).

Tables come from `uv run python analyses/phase5/evaluations.py --spec <id> --table`. Full regression tables for each evaluation (every estimator, observations, fixed effects, notes) are in [`econometric_tables.md`](econometric_tables.md), with a LaTeX version in `econometric_tables.tex`. Estimates are per 100 businesses a year for entry and exit, and 100 × log points relative to the CPI for prices. MDE is the smallest effect detectable with 80% power at the 5% level.

## 1. Headline

- **No registered primary outcome shows a detectable effect.**
  - Seven designs are identified and inconclusive.
  - Three are not identified: their pre-reform paths already fail the placebo check, as the blinded design stage showed (plan §6.3).
- **The new designs are more precise.**
  - For the five identified re-evaluations, the primary outcome's MDE falls by 18–53%: for example, the heavy vehicle law from 9.4 to 4.4 per 100, and childcare from 9.8 to 6.0.
  - Their 90% intervals all lie within −4.3 to +3.5 entries per 100 (average entry rates are 12–16). Effects smaller than the MDEs (3.5–6.0) cannot be ruled out.
  - No conclusion changed.
- **Fuel price reporting (new, rated high):** the registered estimate is −2.8% (90% interval −7.3 to +0.4; p = 0.20). Synthetic DiD gives +4.8, outside that interval, so the grade is **Weak**. These data cannot detect a price effect smaller than about 7%.
- **E-conveyancing (new, rated medium):** legal services entry −0.6 per 100 (p = 0.54; MDE 2.9). Synthetic DiD gives −3.0, outside the interval, so the grade is Weak.
- **The one significant secondary price result is confounded.**
  - Melbourne's urban transport fares are 10.6% lower in the Victorian taxi window (p = 0.024).
  - A check made after unblinding puts the whole fall in 2015-Q1, the quarter public transport fare changes were reported to start, not when the taxi reform began (§5).

## 2. New families

| Evaluation | Outcome | Layer | Estimate | 90% interval | p | q | MDE | Pre-trend check | Verdict | Grade |
|---|---|---|---|---|---|---|---|---|---|---|
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | Automotive fuel: prices relative to the CPI (primary) | Saturated fixed effects | −2.8 | −7.3 to +0.4 | 0.20 | 0.39 | 6.7 | pass | No detectable effect | Weak |
|  | Business entry rate (secondary) | Saturated fixed effects | −0.2 | −1.4 to +0.8 | 0.85 | n/a | 2.2 | fail |  | |
|  | Business exit rate (secondary) | Saturated fixed effects | −1.0 | −2.1 to +0.1 | 0.15 | n/a | 2.2 | pass |  | |
| Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023) | Business entry rate (primary) | Saturated fixed effects | −0.6 | −2.3 to +0.6 | 0.54 | 0.54 | 2.9 | pass | No detectable effect | Weak |
|  | Business exit rate (secondary) | Saturated fixed effects | +0.0 | −1.1 to +0.7 | 0.88 | n/a | 1.8 | pass |  | |

**Every estimator, primary outcomes:**

| Layer | Fuel prices: estimate (p; MDE) | E-conveyancing entry: estimate (p; MDE) |
|---|---|---|
| Two-way fixed effects | +1.7 (0.90; 38.6) | −3.0 (0.37; 11.4) |
| Cell and state × year effects | +1.7 (0.90; 38.9) | −3.0 (0.34; 11.5) |
| Two-way with measured state controls | +1.7 (0.90; 38.7) | −3.1 (0.34; 11.4) |
| **Saturated fixed effects (registered)** | **−2.8 (0.20; 6.7)** | **−0.6 (0.54; 2.9)** |
| Imputation (Borusyak, Jaravel and Spiess) | −3.0 (0.29; 7.2) | −0.6 (0.54; 3.3) |
| Synthetic DiD | +4.8 (0.13; 8.6) | −3.0 (0.32; 10.3) |
| Generalised synthetic control | +22.0 (0.025; 12.1) | −1.7 (0.61; 26.6) |

**Reading:**
- **Fuel.** The two layers that take out each CPI class's national quarter-by-quarter movement agree on about −3%: saturated fixed effects and imputation. The layers without class × quarter effects have MDEs near 39%, so they say nothing.
  - Synthetic DiD and the generalised synthetic control point the other way. The generalised synthetic control's +22% is far outside every other layer and was not a registered check.
  - The registered rule therefore grades the result Weak. A fall of a few per cent is consistent with the preferred layers but not established.
- **E-conveyancing.** All layers are negative. Only the saturated and imputation layers are precise enough to matter, and neither is significant.
- **Not tested here:** conveyancing is a small part of legal services, so a real effect on conveyancers would be diluted (evaluability note, §2). PEXA or IPART data would test it directly.

## 3. Re-evaluations

| Evaluation | Outcome | Layer | Estimate | 90% interval | p | q | MDE | Pre-trend check | Verdict | Grade |
|---|---|---|---|---|---|---|---|---|---|---|
| Perth retail trading hours (2010 weeknights, 2012 Sundays) | Business entry rate (primary) | Saturated fixed effects | +1.0 | −1.9 to +3.5 | 0.49 | 0.78 | 4.6 | pass | No detectable effect | Moderate |
|  | Business exit rate (secondary) | Synthetic DiD | +1.3 | −0.2 to +2.6 | 0.22 | n/a | 3.0 | pass |  | |
| National Quality Framework for childcare (2012) | Business entry rate (primary) | Synthetic DiD | −0.3 | −2.3 to +2.4 | 0.85 | 0.85 | 6.0 | pass | No detectable effect | Moderate |
|  | Business exit rate (secondary) | Two-way fixed effects | −1.9 | −3.1 to −0.5 | 0.049 | n/a | 2.2 | pass |  | |
|  | Child care: prices relative to the CPI (secondary) | Synthetic DiD | +4.4 | +2.5 to +6.7 | 0.075 | n/a | 5.0 | pass |  | |
| Heavy Vehicle National Law (2014) | Business entry rate (primary) | Saturated fixed effects | +0.3 | −1.7 to +2.8 | 0.85 | 0.85 | 4.4 | pass | No detectable effect | Moderate |
|  | Business exit rate (secondary) | Saturated fixed effects | −0.7 | −2.2 to +0.9 | 0.59 | n/a | 3.0 | pass |  | |
| As-of-right taxi licences in Victoria (2014) | Business entry rate (primary) | Saturated fixed effects | −0.4 | −2.6 to +1.8 | 0.68 | 0.85 | 3.5 | pass | No detectable effect | Weak |
|  | Business exit rate (secondary) | Saturated fixed effects | −1.9 | −3.2 to −0.8 | 0.049 | n/a | 2.4 | fail |  | |
|  | Urban transport fares: prices relative to the CPI (secondary) | Saturated fixed effects | −10.6 | −14.8 to −7.6 | 0.024 | n/a | 8.3 | pass |  | |
| Legal Profession Uniform Law (2015) | Business entry rate (primary) | Saturated fixed effects | −1.3 | −4.3 to +0.8 | 0.47 | 0.78 | 4.5 | pass | No detectable effect | Moderate |
|  | Business exit rate (secondary) | Saturated fixed effects | −0.4 | −1.3 to +0.5 | 0.45 | n/a | 1.6 | pass |  | |
| Ride-share legalisation (2015 to 2018) | Business entry rate (primary) | Saturated fixed effects | −2.2 | −4.6 to −0.5 | 0.17 | 0.52 | 4.3 | fail | Not identified | Not identified |
|  | Business exit rate (secondary) | Saturated fixed effects | −0.3 | −1.5 to +0.8 | 0.59 | n/a | 2.2 | pass |  | |
|  | Urban transport fares: prices relative to the CPI (secondary) | Synthetic DiD | −0.3 | −3.0 to +2.5 | 0.85 | n/a | 5.0 | pass |  | |
| Northern Territory container deposit scheme (2012) | Waters, soft drinks and juices: prices relative to the CPI (primary) | Saturated fixed effects | +7.6 | −0.2 to +19.1 | 0.20 | 0.52 | 22.0 | fail | Not identified | Not identified |
|  | Beer: prices relative to the CPI (secondary) | Saturated fixed effects | +4.8 | −3.0 to +16.3 | 0.44 | n/a | 22.0 | pass |  | |
| Retail energy price deregulation (SA 2013, NSW 2014, SEQ 2016) | Electricity: prices relative to the CPI (primary) | Saturated fixed effects | +9.4 | +5.0 to +15.1 | 0.024 | 0.20 | 9.1 | fail | Not identified | Not identified |

q-values are Benjamini–Hochberg across each specification's primary outcomes. Secondary outcomes are outside the decision rule and are not adjusted.

### 3.1 Against the archived evaluations

| Re-evaluation | Outcome | Earlier (archived): estimate, p, MDE, verdict | Phase 5: estimate, p, MDE, verdict | Grade (earlier → now) |
|---|---|---|---|---|
| Perth retail trading hours (2010, 2012) | Business entry rate | +0.8, p = 0.62, 5.6, no detectable effect | +1.0, p = 0.49, 4.6, no detectable effect | Moderate → Moderate |
| National Quality Framework for childcare (2012) | Business entry rate | −0.3, p = 0.93, 9.8, no detectable effect | −0.3, p = 0.85, 6.0, no detectable effect | Moderate → Moderate |
| Heavy Vehicle National Law (2014) | Business entry rate | −2.2, p = 0.33, 9.4, no detectable effect | +0.3, p = 0.85, 4.4, no detectable effect | Moderate → Moderate |
| As-of-right taxi licences in Victoria (2014) | Business entry rate | −1.4, p = 0.32, 4.2, no detectable effect | −0.4, p = 0.68, 3.5, no detectable effect | Weak → Weak |
| Legal Profession Uniform Law (2015) | Business entry rate | −1.6, p = 0.53, 7.0, no detectable effect | −1.3, p = 0.47, 4.5, no detectable effect | Moderate → Moderate |
| Ride-share legalisation (2015 to 2018) | Business entry rate | +0.2, p = 0.86, 6.0, not identified | −2.2, p = 0.17, 4.3, not identified | Not identified → Not identified |
| NT container deposit scheme (2012) | Waters, soft drinks and juices: prices relative to the CPI | +8.7, p = 0.12, 18.6, not identified | +7.6, p = 0.20, 22.0, not identified | Not identified → Not identified |
| Retail energy price deregulation (2013–2016) | Electricity: prices relative to the CPI | +17.0, p = 0.012, 9.5, not identified | +9.4, p = 0.024, 9.1, not identified | Not identified → Not identified |

**Reading:**
- Every verdict and grade is unchanged.
- The gain is precision, from the layer the blinded power study chose for each reform and the latest CABEE vintage. The MDE falls for every business-count re-evaluation; NT drinks get worse (18.6 to 22.0).
- The earlier estimate lies inside the new 90% interval for five of the eight. It lies outside for:
  - heavy vehicles (−2.2, now +0.3);
  - ride-share (+0.2, now −2.2; not identified either way);
  - electricity (+17.0, now +9.4; not identified either way).

## 4. What the estimator layers show

This is the first set of evaluations to report every layer side by side. The full tables are in each evaluation file (`estimators`) and on its page ("Every estimator side by side").

1. **Two-way fixed effects are not enough here.** For most outcomes the saturated layer's MDE is much smaller:
   - entry rates: by up to 4.4 times (legal services: 19.8 against 4.5);
   - prices: by up to 5.8 times (fuel: 38.6 against 6.7).

   The exceptions are the one-year childcare design, where two-way is as tight or tighter, and exits, where the two are often close. The power study's layer choice reflects this: two-way is registered for childcare exits.
2. **Two-way estimates can be badly biased where the saturated design passes or fails visibly.** Ride-share entry:
   - two-way: +33.2 per 100 (p = 0.024);
   - synthetic DiD: +25.5;
   - saturated: −2.2.

   The design stage had already failed this outcome's pre-trend check. A study using two-way effects alone would have reported a large, "significant" increase.
3. **Saturated and imputation layers agree closely** except for ride-share entry (−2.2 against −0.9), the most staggered design. Imputation fits the same saturated effects on untreated cells only, so it is robust to effects that vary across cohorts. Where the two differ, timing matters.
4. **Synthetic DiD disagrees most often.** It is the check layer outside the registered interval in both grades the check rule set to Weak (fuel, e-conveyancing). It reweights comparison cells to match pre-reform paths, so it uses a different comparison. Where the two disagree, the result depends on the comparison chosen.

## 5. Post-unblinding check (not pre-registered): Victorian fares

**Why:** the registered result (−10.6%, p = 0.024) covers 2014-Q3 to 2015-Q2. The annual event-study bin cannot separate the quarters. Public transport fare changes were reported to start on 1 January 2015: travel across zones 1 and 2 capped at the zone 1 fare, and free trams in the CBD. Source: commentary written before the change ([danielbowen.com, 11 August 2014](https://danielbowen.com/2014/08/11/myki-fare-reform/)). **These changes were not checked against PTV's fare tables.**

**Check:** Melbourne's urban transport fares relative to the CPI, minus the mean of the other seven capitals. The gap is measured from its mean over 2013-Q3 to 2014-Q2. Script: `alicia/analyses/phase5/posthoc.py` (a post-hoc stage of the specification).

| Quarter | 2014-Q2 | 2014-Q3 | 2014-Q4 | 2015-Q1 | 2015-Q3 | 2015-Q4 | 2016-Q4 |
|---|---|---|---|---|---|---|---|
| Gap (log points × 100) | −0.1 | −0.1 | +0.7 | −18.4 | −19.2 | −19.4 | −20.0 |

**What it shows:**
- The gap does not move when the taxi reform starts: +0.1 in 2014-Q3.
- It falls 19.1 points in 2015-Q1, about 12 times the standard deviation of quarterly moves from 2005 to 2014. It stays down.
- Over the registered window the raw gap averages −9.1: two quarters near zero and two near −18.5. The registered estimate (−10.6) is the saturated-model version of that average.

**Reading:**
- The fares result is almost certainly the January 2015 fare changes, not taxi competition. The CPI class covers public transport as well as taxi fares.
- It is recorded in the evaluation as a confounded secondary result, labelled post-unblinding. The verdict, which rests on taxi entry, is unchanged.

## 6. Leads, not findings

These are secondary outcomes, or checks that are not part of the decision rule. Each needs its own registered test before it is relied on.

- **Childcare exits after the NQF: −1.9 per 100 (two-way, p = 0.049).**
  - The synthetic DiD check agrees in sign (−0.7) but is not significant.
  - The saturated and imputation layers give +3.2.
  - The earlier evaluation found +3.1 (p = 0.24).
  - Conclusion: the sign depends on the comparison.
- **Childcare prices: +4.4% (synthetic DiD, p = 0.075).** The saturated check (−0.7) lies outside its interval.
- **Legal Profession Uniform Law entry: −1.3 per 100.** It is unusual against the reform's own class in placebo states at fake dates (p = 0.048, 20 draws), but not against placebo industries (p = 0.47).

**After unblinding:** robustness checks, not pre-registered, show both exit leads are fragile ([`robustness_phase5.md`](robustness_phase5.md)):
- childcare exits are significant in 4 of 9 variants;
- Victorian taxi exits lose significance without NSW or WA.

No Phase 5 outcome survives a programme-wide false-discovery adjustment: the smallest q-value is 0.28.

## 7. Limits

- **Identification:**
  - Parallel trends hold conditional on class × period and state × period effects. For synthetic DiD, the condition is relative to the weighted comparison cells.
  - Three designs fail the pre-trend check, so their estimates are descriptive only.
- **Aggregation:** state-level business counts and capital-city CPI classes. They cannot show firm-level entry, prices or markups.
  - Conveyancing is diluted within legal services.
  - Fuel prices are capital-city averages.
- **Inference:**
  - Rank p-values against 40 placebo industry groups (or CPI classes): the smallest attainable p is about 0.024.
  - The 90% interval comes from placebo quantiles, so it can exclude zero when the two-sided rank p is above 0.10 if the placebo distribution is skewed (ride-share entry). The decision uses the p-value.
- **Disclosure:**
  - The re-evaluation specifications were written knowing the earlier results.
  - The layers, outcomes and windows were fixed by the blinded power study and design stage before any treated post-reform outcome was computed.
- **Records:** the new-family records (fuel, e-conveyancing) are drafts. Their dates and industries have not been checked by a person. NSW's fuel reporting date is the registration deadline (unconfirmed).
- **COVID** falls in the Tasmanian and South Australian fuel windows and in the later e-conveyancing cohorts.

## 8. What was archived

Each re-evaluation supersedes one earlier evaluation. The archived evaluations stay in the register and on the website, in a folded "Archived evaluations" section with a banner linking to the newer one, and are never the current evaluation of a record:

| Archived | Superseded by |
|---|---|
| `wa-trading-hours-2010-2012` | `wa-trading-hours-2010-2012-phase5` |
| `childcare-nqf-2012` | `childcare-nqf-2012-phase5` |
| `heavy-vehicle-national-law-2014` | `heavy-vehicle-national-law-2014-phase5` |
| `vic-taxi-licensing-2014` | `vic-taxi-licensing-2014-phase5` |
| `legal-profession-uniform-law-2015` | `legal-profession-uniform-law-2015-phase5` |
| `rideshare-legalisation-2015-2018` | `rideshare-legalisation-2015-2018-phase5` |
| `nt-container-deposits-2012` | `nt-container-deposits-2012-phase5` |
| `retail-energy-deregulation-2013-2016` | `retail-energy-deregulation-2013-2016-phase5` |

**Not archived:** `wa-trading-hours-weeknight-2010-new-data` (Perth vs regional WA business counts, and turnover) and `childcare-nqf-wa-delay-2012` (the WA delay design). They use other data and comparisons that Phase 5 did not repeat, so they stay current alongside the new evaluations, listed after them.

## 9. Checks after the registered run (not pre-registered)

- **Confounder scan** ([`confounder_scan.md`](confounder_scan.md)): other register changes near each reform, and when each treated series moved. Main findings:
  - it confirms the Melbourne fares jump is in 2015-Q1;
  - NSW e-conveyancing falls in the uniform law's last window year;
  - the energy customer framework moved with energy deregulation.
- **Robustness and diagnostics** ([`robustness_phase5.md`](robustness_phase5.md)):
  - No identified primary result becomes significant in any of its variants.
  - Nothing survives programme-wide multiple testing.
  - The two Weak grades come from synthetic DiD using a different comparison: the national legal-services trend (e-conveyancing), and the SA 2021 cohort (fuel).
  - The heavy vehicle law's point estimate depends on WA as a comparison.
