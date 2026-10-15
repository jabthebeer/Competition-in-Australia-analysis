# Pre-analysis plan: Perth trading-hours deregulation and retail entry and exit

**Registered:** 15 October 2026, before any post-reform outcome for affected WA retail was estimated. The one disclosed exception is the productivity series; see the robustness review §5.

**Design-stage evidence:** [`robustness_review_wa_trading_hours.md`](robustness_review_wa_trading_hours.md).

Changes to this plan after unblinding must be listed in §10, with reasons. Results from changed analyses are labelled "not pre-registered".

---

## 1. Records and hypothesis

- **Register records:** `wa-trading-hours-weeknight-2010` and `wa-trading-hours-sunday-2012` (family `retail-trading-hours`).
- **Hypothesis:** the reform **enhanced** competition in general retail.
  - **Channels** (OIA categories): ability or incentives to compete; consumer choice.
  - **Expected direction:** entry rate up. The effect on exit is ambiguous, since more competition may push weaker incumbents out. Food prices relative to the CPI down.
- **Alternative to take seriously:** longer hours favour large chains that can staff them. Small-store exits rise and net entry falls, which would read as competition between businesses weakening even as consumer choice improves.

## 2. Timing

- **First exposed financial year: 2010-11** (fy 2011). Special trading precincts took effect from July and September 2010, and 9pm weeknight trading from **1 Nov 2010**.
- **Second step:** Sunday trading from **26 Aug 2012**, first exposed in 2012-13.
- **Window:** 2007-08 to 2017-18. Pre-period 2007-08 to 2009-10 (3 years); post-period 2010-11 to 2017-18 (8 years).
- **Reference year** for the event study: 2009-10.

## 3. Units

- **Treated:** WA × pooled ANZSIC classes **4110** Supermarket and Grocery Stores, **4251** Clothing Retailing and **4260** Department Stores. Rates are pooled: total entries ÷ total businesses at the start of the year.
- **Comparison states:** NSW, Victoria, Queensland, Tasmania, ACT and NT. SA is excluded because the Adelaide CBD trading-hours change took effect in April 2012.
- **Placebo industries:** random groups of 3 ANZSIC classes outside division G, with at least 50 WA businesses each in 2009-10, and total WA size between half and twice the treated group. 1,000 draws, seed 20261015; draws where WA lacks a year are discarded.

## 4. Outcomes

| Role | Outcome | Source |
|---|---|---|
| **Primary** | Entry rate, entries per 100 businesses operating at the start of the year | CABEE, own-release vintage |
| Secondary | Exit rate (same definition) | CABEE |
| Secondary | 100 × log(Perth *Food and non-alcoholic beverages* / *All groups*) vs other capitals, quarterly 2000-Q1 to 2019-Q4, post from 2010-Q4 | ABS CPI (17th series) |
| Descriptive only | Retail output per worker (division G); clothing relative prices; compensation per worker | State Accounts, LFS, CPI |

## 5. Estimators

1. **Treated-group difference-in-differences:** WA vs comparison states, two-way fixed effects (state and year). This gives δ_T.
2. **Primary estimate:** **δ = δ_T − mean(δ_placebo)**, where δ_placebo applies the same estimator to each placebo industry group. This nets out WA-wide shocks to all industries.
3. **Event study:** annual coefficients relative to 2009-10, for the dynamics. The expected pattern is a step in 2010-11 and 2011-12 (weeknights), then a further step from 2012-13 (Sundays).
4. **Triple difference** against cafes and restaurants (4511), takeaway food (4512) and fuel retailing (4000). Secondary.
5. **Prices:** WA vs comparison capitals, two-way fixed effects (city and quarter).

## 6. Inference

- **Primary:** two-sided rank p-value of (δ_T − mean placebo) within the centred placebo-industry distribution. Smallest possible p is about 0.002.
- **Also reported:**
  - the comparison-state placebo rank (smallest possible p is 0.14);
  - a 90% interval from the placebo-industry quantiles.
- **No conventional standard errors.** With one treated state they are not credible.

## 7. Power (from the design stage)

| Outcome | Smallest effect detectable with 80% power | Power for a 3-per-100 effect |
|---|---|---|
| Entry rate | ~5.6 per 100 (industry placebos) | 20% |
| Exit rate | ~4.1 per 100 | 56% |
| Food relative price | ~3.2% | not applicable |

**Interpretation rule:** if the 90% interval includes both 0 and ±5 per 100, the result is **"inconclusive"**, not "no effect".

## 8. Robustness (all reported, whatever they show)

1. **Vintage:** the overlap-vintage series in place of the own-release series.
2. **Window:** add 2018-19, which has the identity break.
3. **Comparison states:** drop Queensland; drop NT and ACT; leave each state out in turn.
4. **Treated set:** broaden to all classes in subdivisions 41 and 42 except 4123 Liquor Retailing.
5. **Placebo pool:** restrict to consumer-facing classes (divisions H and S).
6. **Event-study pre-coefficients and sensitivity bounds:** how large a violation of parallel trends would overturn the sign.
7. **Results chain:** do entry and food prices move in the predicted directions together?

## 9. Decision rule and grading

- **Supports "enhancing":** δ > 0 on entries with p < 0.05 (primary inference), the same sign under the comparison-state placebo and the triple difference, and no reversal in the vintage sensitivity.
- **Supports "weakening":** the mirror image.
- **Otherwise:** "inconclusive", with the magnitude and interval reported.
- **Grading** follows §8 of the evaluation design. Because there is one treated state with 3 pre-years, the best achievable grade is **Moderate**.

## 10. Changes after registration

None yet.
