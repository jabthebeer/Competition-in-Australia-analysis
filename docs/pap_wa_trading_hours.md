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

No analysis has been changed.

**Clarifications made before unblinding (15 October 2026).** These settle points the plan left open.
- They are fixed in `alcia/analyses/wa_trading_hours/estimate.py`.
- That script was checked in a dry run with the treated outcomes hidden (`estimate_blind.json`).
- The dry run reproduced the design review's placebo draws exactly: 472 groups for entries and 451 for exits, with the same mean and SD.
- They were committed before the unblinded run.

| # | Point | Clarification |
|---|---|---|
| C1 | "Same sign under the comparison-state placebo" (§9) | The sign of the plain treated-group DiD, δ_T: the estimate that the comparison-state placebo evaluates. Its rank p-value is also computed for δ_T |
| C2 | "Overlap vintage" (§8.1) | The CABEE cubes give one second vintage, for 2010-11 to 2016-17 only, from the following release. Those years are replaced; the others keep their own-release values. The placebo groups use the same vintage. "No reversal" means the net estimate keeps its sign |
| C3 | Placebo draws (§3) | One random stream, seed 20261015. The first 1,000 draws are for entries and the next 1,000 for exits, as in the design review. Robustness variants reuse these groups. The divisions H and S pool (§8.5) uses a fresh stream with the same seed |
| C4 | Broadened treated set (§8.4) | All classes in subdivisions 41 and 42 except 4123 (28 classes). It reuses the primary placebo groups, which are size-matched to the primary treated group. A larger pooled group is less noisy, so its p-value is conservative |
| C5 | Interpretation rule (§7) | "Inconclusive" when the 90% interval contains 0 and also reaches +5 or −5 per 100 |
| C6 | Grade (§9 and evaluation design §8) | **Not identified** if either pre-period event coefficient (net of the placebo mean) lies outside its 95% placebo band. **Weak** if any §8.1–8.5 variant moves the estimate outside the primary 90% interval. Otherwise **Moderate** |
| C7 | Event study and sensitivity (§5.3, §8.6) | The plain event study is reported, and alongside it the same coefficients net of the placebo-group mean for each year, which matches the primary estimator. The sensitivity bounds are the relative-magnitudes breakdown of Rambachan and Roth (2023), point-identified version, plus a linear pre-trend extrapolation |
| C8 | Additional output, labelled "not pre-registered" | The 95% interval (the evaluation design's reporting standard); the comparison-state rank of the net estimate; real pay per worker deflated by each capital's CPI (descriptive) |

**After unblinding (15 October 2026).**
- **Run once.** The registered analysis was run once; results are in [`results_wa_trading_hours.md`](results_wa_trading_hours.md).
- **No registered analysis was changed.**
- **Added and labelled "not pre-registered":**
  - a food-price estimate with each city's pre-reform trend removed (`posthoc.py`);
  - balanced-panel means without NT;
  - a back-of-envelope scaling for the Perth-only reach of the reform;
  - a grade for food prices.

**Paths (18 October 2026).** File paths and the tool name were updated for the ALCIA rename (`econ/` became `alcia/`; `regimpact` became `alcia`). The content is unchanged.
