# Results: Perth trading-hours deregulation, retail entry and exit

**Status:** 15 October 2026. This is the registered analysis, unblinded once, after the plan and its clarifications were committed (commit `2bb895b`).

**Files:**
- Plan: [`pap_wa_trading_hours.md`](pap_wa_trading_hours.md)
- Design-stage review: [`robustness_review_wa_trading_hours.md`](robustness_review_wa_trading_hours.md)
- Code: `econ/analyses/wa_trading_hours/estimate.py`
- Results: `estimate.json`
- Checks that were not pre-registered: `posthoc.py` and `posthoc.json`

---

## 1. Headline

> Perth's move to 9pm weeknight trading (November 2010) and Sunday trading (August 2012) had **no detectable effect** on how many general retail businesses started or closed in WA.
>
> - **Entries:** **+0.8 per 100 businesses a year** (90% interval −2.4 to +3.7). The rate before the reform was 16.
> - **Exits:** **−0.1 per 100** (90% interval −2.4 to +2.5). The rate before the reform was 15.
>
> **Grade: Moderate.** There is one treated state and three pre-reform years, so parallel trends cannot be checked well.

**Verdict on the register's hypothesis ("enhancing"):** **inconclusive**, under the plan's decision rule (§9). The data neither support nor refute it. The record keeps its hypothesis.

**What the data rule out, and what they don't:**
- **If parallel trends hold:** WA retail would have tracked the other states once the WA-wide shock is netted out. In that case the data rule out:
  - a rise in entry of more than about **3.7 per 100**, almost a quarter of the normal rate;
  - a change in exits of more than about **2.5 per 100**.
- **If they don't hold:** the three pre-reform years are too short and noisy to test the assumption. A post-reform drift as large as the pre-reform year-to-year swings would be enough to flip the sign (§4).
- **What these data cannot see at all:** consumer convenience, sales shifting between large and small stores, and hours worked.

**Prices and productivity:**
- **Food prices:** Perth's food prices did fall about 2% relative to other capitals. But they had been falling at a similar pace since 2000, and the fall slowed after the reform (§6).
- **Productivity and pay:** too noisy to say anything (§7).

## 2. Registered results

| Outcome | Role | Estimate | 90% interval | p, industry placebos | p, comparison states |
|---|---|---|---|---|---|
| **Entry rate** (per 100), net of the WA-wide shock | **Primary** | **+0.78** | −2.40 to +3.75 | 0.62 | 0.71 (plain DiD) |
| Entry rate, plain WA-vs-states DiD (δ_T) | Part of the primary | −0.80 | | | 0.71 |
| Entry rate, triple difference against cafes, takeaway and fuel | Secondary | −0.72 | | | 0.57 |
| **Exit rate** (per 100), net | Secondary | **−0.07** | −2.44 to +2.50 | 0.95 | 1.00 (plain DiD) |
| Exit rate, plain DiD | Part of the secondary | +0.09 | | | 1.00 |
| Exit rate, triple difference | Secondary | +1.19 | | | 0.57 |
| **Food prices** relative to the CPI, Perth vs other capitals (log points) | Secondary | **−2.22** | | | 0.14 (the smallest possible) |

**Further detail:**
- **95% intervals** (the evaluation design's reporting standard; not pre-registered):
  - entries −3.5 to +5.1;
  - exits −2.9 to +2.8.
- **Smallest effects detectable with 80% power**, from the design stage:
  - entries 5.6;
  - exits 4.1;
  - food prices 3.2%.
- **Interpretation rule (§7):** neither 90% interval reaches ±5. These are therefore bounded nulls rather than the wide, "inconclusive" kind. That reading still depends on parallel trends (§4).

**Decision rule (§9), checked condition by condition.** It needs all of the following; only the vintage condition holds:
- p below 0.05;
- the same sign in the plain DiD;
- the same sign in the triple difference;
- no reversal under the other vintage.

## 3. How the estimate is built: the WA-wide shock

| | Before (2007-08 to 2009-10) | After (2010-11 to 2017-18) | Change |
|---|---|---|---|
| WA general retail, entries per 100 | 16.1 | 13.4 | −2.6 |
| Comparison states (excluding NT, which lacks 2007-08 and 2008-09) | 16.2 | 14.2 | −2.1 |
| Difference | | | **−0.6** (−0.8 with NT, using fixed effects) |

**The plain comparison suggests WA retail entry fell slightly relative to other states.** But WA's other industries fell too.
- Across 472 random groups of unaffected WA industries, entry fell by **1.6 per 100** relative to the same industries elsewhere. This is most likely the end of the mining investment boom.
- Netting that out gives **+0.8**.
- Without the industry placebos, the plain comparison would have read as a small decline caused by the reform.

## 4. Year by year

![Event study: entries and exits per 100 businesses, WA general retail relative to comparison states, net of the placebo-industry mean, with 90% placebo bands](figures/wa_trading_hours_event_study.svg)

| Financial year | 2007-08 | 2008-09 | 2009-10 | 2010-11 | 2011-12 | 2012-13 | 2013-14 | 2014-15 | 2015-16 | 2016-17 | 2017-18 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Entries, net | −4.2 | −2.1 | 0 (ref.) | −1.2 | −1.5 | −1.7 | −1.2 | −1.3 | −2.6 | −1.0 | −0.1 |
| Exits, net | +1.6 | +1.7 | 0 (ref.) | +0.1 | +2.3 | +1.3 | +1.6 | +1.2 | +0.8 | −0.9 | +1.6 |

**What the chart shows:**
- **No step at either reform.** Entry did not jump when weeknight trading began, or when Sunday trading began (2012-13: −1.7, against −1.5 the year before).
- **Every year after the reform lies well inside its placebo band.**

**Pre-period:**
- **Entries** rose into 2009-10 relative to WA's other industries. In 2009-10, WA retail entry was 18.4 per 100 against 16.8 elsewhere.
- **Both pre-period coefficients are inside their 95% bands**, so the plan's diagnostic passes.
- **The reference year matters.** Measured against 2009-10 alone, every post-reform year is lower. Measured against the three-year pre-reform average, entry is higher. That is why the event-study points sit below zero while the headline estimate is positive.

**How fragile is the sign?** (plan §8.6)
- **Relative-magnitudes breakdown** (Rambachan and Roth 2023): **0.14 for entries and 0.13 for exits.** A post-reform departure from parallel trends of only about one-seventh of the largest pre-reform year-to-year swing would flip the sign. If trend violations can be as large as the pre-period swings, the average post-reform effect could be anywhere from about −11 to +8 per 100.
- **Linear pre-trend extrapolation:** continuing the 2007-08 to 2009-10 rise would imply an entry effect of −10.8. Three points spanning the global financial crisis are not a credible trend either.

The honest reading is that the pre-period is too short and noisy to tell a trend from noise. The bounds in §1 hold only under parallel trends.

## 5. Robustness (plan §8)

| Variant | Entries, net | 90% interval | p | Exits, net | p |
|---|---|---|---|---|---|
| **Primary** | **+0.78** | −2.40 to +3.75 | 0.62 | **−0.07** | 0.95 |
| 1. Other ABS vintage (2010-11 to 2016-17 replaced) | +0.64 | −2.78 to +3.60 | 0.66 | −0.03 | 0.99 |
| 2. Add 2018-19 (identity-break year) | +1.16 | −2.04 to +4.15 | 0.45 | +0.13 | 0.93 |
| 3. Leave out NSW | +0.59 | −2.90 to +3.64 | 0.71 | +0.05 | 0.98 |
| 3. Leave out Victoria | +0.46 | −3.18 to +3.89 | 0.77 | +0.08 | 0.94 |
| 3. Leave out Queensland | +0.96 | −2.61 to +4.18 | 0.56 | +0.07 | 0.96 |
| 3. Leave out Tasmania | +0.72 | −2.86 to +4.05 | 0.64 | −0.19 | 0.90 |
| 3. Leave out ACT | +0.78 | −2.14 to +3.68 | 0.64 | −0.33 | 0.77 |
| 3. Leave out NT | +1.13 | −1.82 to +3.87 | 0.45 | −0.07 | 0.96 |
| 3. Drop NT and ACT | +1.25 | −1.31 to +3.87 | 0.40 | −0.46 | 0.72 |
| 4. All store-based retail (subdivisions 41–42, 28 classes, less liquor) | −0.16 | −3.34 to +2.81 | 0.92 | −0.72 | 0.62 |
| 5. Placebo pool: consumer-facing services only (divisions H and S) | +0.29 | −2.78 to +4.10 | 0.77 | +0.11 | 0.95 |

**Results across the variants:**
- **Stable estimates.** Every variant stays inside the primary 90% interval, and none comes near significance.
- **Signs.** Entries: 10 of 11 variants positive. Exits: centred on zero.
- **This meets the plan's rule for "Moderate"** (clarification C6).

## 6. Food prices

The registered estimate is **−2.2 log points**, with p = 0.14. Perth is the most extreme of the 7 capitals. That is in the hypothesised direction and at the smallest p-value this design allows.

**It is a trend, not a reform effect.** These checks were run after unblinding and are not pre-registered:
- **Before the reform:** Perth's food prices relative to its CPI had been falling against other capitals since 2000, at about **0.29 log points a year**.
- **After the reform:** they fell more slowly, about **0.18 a year**.
- **Removing each city's own pre-reform trend** turns the estimate into **+0.7** (p = 0.71).
- **The design-stage test agrees:** a fake reform dated 2006 gave −2.0, about the same as the registered estimate.

**Reading:** no evidence that the reform changed food prices.

**Grade: Not identified** (it fails the trend diagnostic). This grade is a judgement made after unblinding; the plan set no grading rule for prices.

**Clothing prices** (descriptive): −2.0 log points, p = 0.43. Perth's relative clothing prices swing by more than 10 log points over the period, so this says nothing.

## 7. Productivity and pay (descriptive only)

| Outcome | Estimate (log points) | Comparison-state placebo SD | p |
|---|---|---|---|
| Retail real value added per employed person, 1989-90 to 2017-18 (**not blind**: see the review, §5) | −0.3 | 12.9 | 1.00 |
| Retail real compensation per employed person, 2000-01 to 2017-18 | −8.9 | 15.1 | 0.86 |

Both estimates are far inside the noise. These outcomes cannot be measured at state level with public data (robustness review §4).

## 8. Results chain (plan §8.7)

The plan asked whether entry and food prices move together in the hypothesised direction.
- **Mechanically, they do:** entry +0.8 and food prices −2.2.
- **Neither is distinguishable from zero, or from the pre-existing trend.**
- **So the chain does not support the hypothesis.**

## 9. Interpretation and limits

- **The data dilute a Perth-only reform.** The reform applied to metropolitan Perth, but CABEE is by state. About four-fifths of WA's population lives in Greater Perth. If the effect were confined to Perth, the upper bound for Perth alone would be about 4.7 per 100 rather than 3.7. (Back-of-envelope; not pre-registered.)
- **The likely effects are ones these data do not measure.**
  - Longer hours mainly change *when* people shop, and *which* stores capture the sales.
  - The plan's alternative hypothesis is that large chains gain and small shops lose. It predicts offsetting entry and exit by business size, which the totals here can hide.
  - CABEE has employment-size bands, so this can be tested. But it was not pre-registered, so it would be exploratory.
- **One treated state is the binding limit.** Inference ranks WA against unaffected industries, so a sharp answer would need a much larger effect than this reform appears to have had.

## 10. What this means for the programme

1. **The pipeline works end to end:**
   - a register record with verified dates;
   - an evaluability screen;
   - a blinded design review;
   - a committed plan with its clarifications;
   - a dry run;
   - one unblinded run;
   - a graded result.

   Every step is in the repository history, in order.
2. **Industry placebos earned their place.** They changed the sign of the plain comparison and gave real p-values.
3. **Single-state reforms give bounds, not findings.** The next case should be a reform adopted by several states at different times (design D1), which is where public data can say more.
4. **Price designs need a pre-trend check registered up front.** The food-price estimate looked like a result until the pre-existing trend was removed. Future plans should register a detrended price estimate as a robustness check. The design-stage fake-date test already flagged the trend; it should have been made binding.

## 11. Deviations and disclosures

- **No registered analysis was changed.**
  - Clarifications C1–C8 were committed before unblinding, in commit `2bb895b`.
  - A dry run on hidden data reproduced the design review's placebo draws exactly: 472 and 451 groups, with the same mean and SD.
  - The analysis was then run once.
- **Not pre-registered:**
  - the detrended food-price check;
  - the balanced-panel means in §3;
  - the Perth dilution scaling in §9;
  - the food-price grade.
- **The estimator was checked by recomputing it independently.** A from-scratch least-squares fit reproduces δ_T = −0.798. On the balanced panel without NT, the simple difference of means equals the fixed-effects estimate (−0.601).
- **Productivity is not blind.** WA retail output per worker was displayed once before the design review.
- **Records stay drafts.** The two WA register records remain `draft`. Their notes now point here. Their direction field is unchanged, because it is a hypothesis and this result does not settle it.
