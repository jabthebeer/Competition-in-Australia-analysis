# Pre-analysis plan: Perth 9pm weeknight trading (2010), re-evaluated with new data

**Registered:** 18 October 2026, before any post-reform outcome for WA was estimated from the data used here.

**Design-stage evidence:** `alicia/analyses/wa_weeknight_2010/design.json`, written by `design_review.py`. That script hides WA's outcomes from the first excluded period on, in code, before anything is computed.

**Earlier evaluation:** [`pap_wa_trading_hours.md`](pap_wa_trading_hours.md) and [`results_wa_trading_hours.md`](results_wa_trading_hours.md) (15 October 2026).

- That evaluation pooled the 2010 and 2012 steps of the reform.
- It used CABEE entry and exit rates by state; its results are known.
- This plan treats the **weeknight step alone**, with three outcomes that the earlier evaluation did not use.

Changes after unblinding go in §11, and results from changed analyses are labelled "not pre-registered".

---

## 1. Record and hypothesis

- **Record:** `wa-trading-hours-weeknight-2010`. The *Retail Trading Hours Amendment Act 2010* let general retail shops in the Perth metropolitan area open until 9pm on weeknights from **1 November 2010**.
- **Hypothesis:** the change **enhanced** competition in general retail. The record's rationale is that smaller and new retailers can compete on convenience.
- **Alternative:** longer hours favour large chains, which can staff them. Small retailers lose ground.
- **What each outcome can show:**
  - **Turnover:** whether general retailers in WA sold more.
  - **Hours worked:** whether they worked more hours.
  - **Business counts by place:** whether the number of retail businesses in metropolitan Perth changed relative to regional WA, where the rules did not change. This is the outcome closest to competition. Business counts are an imperfect proxy for it.

## 2. Timing

| | Dates |
|---|---|
| Reform | 9pm weeknight trading from 1 Nov 2010, Perth metropolitan area |
| Also in 2010 | Special trading precincts with Sunday trading: Joondalup (8 Jul 2010), Armadale and Midland (23 Sep 2010). The periods they touch are excluded, not used as pre-periods |
| Next step | Sunday trading from 26 Aug 2012. Every post-period ends before it |

## 3. Designs

All three designs are a difference-in-differences with one treated unit and two-way fixed effects (unit and period). The effect is the average post-period difference.

**A. Retail turnover (primary).**

| | Specification |
|---|---|
| Source | ABS Retail Trade, seasonally adjusted, monthly |
| Outcome | 100 × log turnover of supermarkets and grocery stores (Retail Trade subgroup 01), clothing (4251) and department stores (4260): the general retail shops the reform covered |
| Units | WA and the comparison states with a complete series from 1992: NSW, Victoria, Queensland, ACT. Tasmania and the NT lack department-store or clothing series. SA is excluded (Adelaide CBD trading change in Apr 2012) |
| Window | Pre: Jul 2008 to Jun 2010 (24 months). Excluded: Jul to Oct 2010. Post: Nov 2010 to Jul 2012 (21 months) |
| Event study | Three-month bins; reference is the last pre bin (Apr to Jun 2010) |

**B. Hours worked (descriptive only; see §6).**

| | Specification |
|---|---|
| Source | ABS Labour Force EQ06, mid-quarter months |
| Outcome | 100 × log hours actually worked by people whose main job is in groups 411 (supermarket and grocery), 425 (clothing, footwear, personal accessories) and 426 (department stores) |
| Units | WA and NSW, Victoria, Queensland, the states whose group estimates rest on enough respondents |
| Window | Pre: Aug 2004 to May 2010 (24 quarters). Excluded: Aug 2010. Post: Nov 2010 to May 2012 (7 quarters) |
| Secondary | Employed persons, same groups |

**C. Retail businesses by place (primary).**

- **Source:** ABS CABEE, businesses by division × SA2 (ASGS 2011) at 30 June. Two archived releases are chained at June 2011: June 2009–2011 from the Jun 2007–Jun 2011 release, and June 2012 moved by its change since June 2011 within the Jun 2009–Jun 2013 release.
- **Places:**
  - Metropolitan Perth = SA4s 503–507.
  - Mandurah (SA4 502) is in Greater Perth but outside the trading-hours metropolitan area, so it is excluded.
  - Rest of WA = all other WA SA4s.
  - In each comparison state, the capital city vs the rest of the state. The comparison states are NSW, Victoria, Queensland, Tasmania and the NT; the ACT has no rest of territory.
- **Outcome:** for division X in state s,
  y = [100 × log(businesses in the capital) − 100 × log(businesses in the rest of the state)] for X, minus the same gap for all other divisions together.
  The other divisions exclude retail (G), accommodation and food services (H), and X itself.
  The real estimate is X = retail (G), s = WA. It is a triple difference: retail vs other industries × Perth vs regional WA × after vs before, set against the same contrast in other states.
- **Periods:**
  - Pre: 30 June 2009 and 2010.
  - Post: 30 June 2011 (8 months after the reform) and 30 June 2012 (20 months).
  - June 2013 is not used, because Sunday trading began in Aug 2012.
- **Event study:** k = −2, −1 (reference, June 2010), 0, 1.

## 4. Inference

With one treated state, conventional standard errors are not credible. Each outcome is judged against a **no-effect distribution**: the same estimator applied where there was no reform.

- **A and B:**
  - every unit at every fake event date from January 1995 whose whole window ends before the real excluded period (Jun 2010 for A, May 2010 for B), with the other units as comparisons;
  - plus each comparison state at the real date, with WA left out.
- **C:** every other division (not G or H) in every state as if it were treated, plus retail in each comparison state, with WA left out. Only cells of a size like WA retail count: at least 1,000 businesses in both the capital and the rest of the state at June 2010 (WA retail: 10,284 and 3,271).

From each distribution:

| Quantity | Definition |
|---|---|
| p-value | Share of no-effect estimates at least as large in absolute value as the real one, counting the real one |
| 90% interval | Estimate minus the 95th and 5th percentiles of the distribution (Conley–Taber) |
| Smallest detectable effect | 2.80 × the distribution's standard deviation (80% power, 5% two-sided) |
| Event-study bands | 5th to 95th percentile of the same event-study coefficients across the distribution |

## 5. Power (from the design stage, outcomes hidden)

| Design | No-effect estimates | SD | Smallest detectable effect | Comparison states at the real date |
|---|---|---|---|---|
| **A** turnover | 834 | 3.46 | **9.7** log points (~10%) | NSW −1.4, VIC −2.0, QLD +0.1, ACT +3.3 |
| B hours | 227 | 6.89 | 19.3 | NSW −0.1, VIC +6.7, QLD −6.5 |
| B employment | 227 | 5.73 | 16.1 | — |
| **C** retail businesses | 59 | 3.61 | **10.1** log points | NSW +2.7, QLD −1.9, TAS +2.8, VIC +0.3 |

Effects smaller than these cannot be told apart from what happens without a reform. A null result rules out only effects at least this large.

## 6. Diagnostics at the design stage, and what they decided

- **A:** WA's own fake-date test passes. At the latest fake date (Oct 2008) the estimate is −3.5, p = 0.29 among the no-effect estimates. One of seven pre-period event-study bins lies outside the 90% band.
- **B: fails.** WA's latest fake-date estimate is +15.6, p = 0.02, and WA's pre-period event-study coefficients swing between −22 and +32. Under the rule adopted after the first case (decision E-31: a failed fake-date test at the design stage is binding), hours and employment are reported as **descriptive only**, with no finding.
- **C:** with two pre-periods there is no fake-date test. WA's pre-period event-study coefficient (June 2009 vs 2010) is 0.0, inside the placebo band (−14.2 to +6.5).

## 7. Choices made at the design stage on hidden outcomes (full list)

Every alternative tried is recorded here with its smallest detectable effect (MDE). None used WA's post-reform outcomes.

**A, turnover:**

- Started as a triple difference against cafes, restaurants and takeaway, with a 60-month pre-period and fake dates from 1987. The MDE was 38: the food-service series are volatile, and differential trends accumulate over a long pre-period.
- Variants tried (MDE): turnover of the treated subgroups alone (16 → 9.7 with a 24-month pre-period and fake dates from 1995); minus the rest of retail and food services (15.3); supermarkets minus specialised food (54.6); triple difference against food services (31.4).
- **Chosen:** treated subgroups alone, 24-month pre-period, fake dates from 1995 (the period of the modern retail series).
- All other variants are reported as secondary (§8).
- Cost of dropping the food-service difference: the main estimate does not net out WA-wide demand shocks such as the mining boom. The no-effect distribution includes WA's own history of such shocks since 1995. The variant net of other retail and food services is reported alongside.

**B, hours:** comparison states limited to the three large states (MDE 19.3, vs 25.2 with all six). Its fake-date test failed (§6).

**C, places:**

- First tried with ABN cancellations of businesses whose names indicate retail. Too few: in WA, about 62 retail-named exits a year in Perth and 18 in the rest of the state (2005–2009 average). Dropped.
- Replaced with CABEE business counts by SA2.
- The size floor of 1,000 businesses per area was set after seeing that tiny cells dominate the placebo spread: SD 15.9 without it, 3.6 with it. Dropping the floor is reported as a sensitivity.

## 8. Secondary results and sensitivities (all reported, whatever they show; none changes the finding)

| Design | Secondary results and sensitivities |
|---|---|
| A | Each treated subgroup alone; net of other retail and food services; triple difference against food services; supermarkets minus specialised food (a market-share measure); detrended (each unit's pre-period linear trend removed); no-effect distribution using all fake dates from 1987 |
| B | Hours; employment; hours minus food services (all descriptive) |
| C | Small businesses only (fewer than 20 employees); Mandurah counted in Perth; WA outback left out; no size floor |

## 9. Findings, verdict and grade

**Finding for each primary outcome:**

| p-value | Finding |
|---|---|
| p < 0.10 | Increase or decrease, by sign |
| Otherwise | No detectable effect, with the interval and the smallest detectable effect stated |

- The two primaries are A and C. Benjamini–Hochberg q-values across them are reported next to the p-values; findings use p.
- **Verdict** (competition, from C):

| C result | Verdict |
|---|---|
| Increase, p < 0.10 | Supports the enhancing hypothesis (more retail businesses in Perth relative to regional WA) |
| Decrease, p < 0.10 | Contradicts it |
| Otherwise | Inconclusive |

- Turnover (A) is reported under "productivity and pay" as a measure of activity; it does not set the verdict.
- **Grade:** capped at **Moderate**, because there is one treated state.
  - Moderate if A's and C's design-stage diagnostics pass (they do, §6).
  - Weak if the main estimate falls outside the range of the robustness checks in §8 in a way that changes the finding.

## 10. Data, code and order of work

- **Panels:** `data/processed/abs_retail`, `abs_lfs` and `abs_cabee_local`. Sources are in `data/SOURCES.md`.
- **Code:** `alicia/analyses/wa_weeknight_2010/`:
  - `spec.py` (designs);
  - `design_review.py` (blinded);
  - `estimate.py` (registered run; `--blind` dry run first, which must reproduce the design-stage no-effect distributions);
  - `evaluation.py` (writes the register's evaluation file from `estimate.json`).
- **Disclosure:** while the data pipeline was being built, only national or all-state totals of these panels were printed. No WA retail outcome after 2010 was looked at.

## 11. Changes after registration

None yet.

**Paths (18 October 2026, second rename).** File paths and the tool name were updated when ALCIA became ALICIA (`alcia/` became `alicia/`; the package and command `alcia` became `alicia`). The content is unchanged.
