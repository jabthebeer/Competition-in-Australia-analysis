# Results: Perth 9pm weeknight trading (2010), re-evaluated with new data

**Run:** 18 October 2026, once, after the plan [`pap_wa_weeknight_2010.md`](pap_wa_weeknight_2010.md) was fixed.

- **Before the run:** a dry run with WA's post-reform outcomes hidden reproduced the design-stage no-effect distributions. The plan and code hashes were recorded in `alicia/analyses/wa_weeknight_2010/registration.json`.
- **Numbers:** `alicia/analyses/wa_weeknight_2010/estimate.json`.
- **Evaluation file:** `regulation-register/evaluations/wa-trading-hours-weeknight-2010-new-data.json`. It *follows* the first evaluation (`wa-trading-hours-2010-2012`).

## 1. Headline

Letting Perth's general retail shops open until 9pm on weeknights from 1 November 2010 made **no detectable difference** to either:

- the **number of retail businesses** in metropolitan Perth compared with regional WA;
- the **turnover** of supermarkets, clothing and department stores in WA compared with other states.

Effects of about 10% or more in either can be ruled out. Smaller effects cannot. The business-count result is robust. The turnover result depends on the comparison (§3).

- **Verdict:** inconclusive.
- **Grade:** Moderate. One treated state caps the grade; the design checks pass.

## 2. Registered results

| Outcome | Role | Estimate | 90% interval | p | No-effect range (5–95%) | Smallest detectable effect | Finding |
|---|---|---|---|---|---|---|---|
| Retail businesses, Perth vs regional WA, net of other industries (log points ×100) | Primary (competition) | **−1.8** | −5.8 to +4.2 | 0.70 | −6.0 to +4.1 (59 placebo industries and states) | 10.1 | No detectable effect |
| Turnover of supermarkets, clothing, department stores, WA vs NSW, Vic, Qld, ACT (%) | Primary (activity) | **+2.0** | −4.4 to +7.2 | 0.50 | −5.2 to +6.4 (834 fake-date and comparison-state estimates) | 9.7 | No detectable effect |
| Hours worked in the same stores, WA vs NSW, Vic, Qld (%) | Descriptive (failed design check) | +1.6 | −10.9 to +12.0 | 0.85 | −10.4 to +12.6 | 19.3 | — |

Benjamini–Hochberg q-values across the two primaries are 0.70 for both.

**Sizes:**

- Metropolitan Perth had 10,284 retail businesses at June 2010 and the rest of WA 3,271. By June 2012 these were 10,094 and 3,142.
- The stores in the turnover outcome sold about $974m a month in WA in 2009-10.

## 3. Robustness (plan §8, all as registered)

**Business counts (all close to the main estimate, none significant):**

| Variant | Estimate | p |
|---|---|---|
| Small businesses only (fewer than 20 employees) | −1.2 | 0.77 |
| Mandurah counted in Perth | −2.1 | 0.60 |
| WA outback left out | −1.6 | 0.69 |
| No size floor on placebo cells | −1.8 | 0.79 (smallest detectable effect 44) |

**Turnover (depends on the comparison):**

| Variant | Estimate | p | Smallest detectable effect |
|---|---|---|---|
| Main (registered) | +2.0 | 0.50 | 9.7 |
| Each state's pre-reform trend removed | **+7.9** | **0.06** | 11.8 |
| Net of cafes, restaurants and takeaway | **−19.3** | **0.085** | 31.4 |
| Net of all other retail and food services | −6.1 | 0.23 | 15.3 |
| Supermarkets alone | +2.9 | 0.37 | 12.0 |
| Department stores alone | +1.0 | 0.82 | 12.1 |
| Clothing alone | −5.4 | 0.73 | 41.5 |
| Supermarkets relative to specialised food stores | +10.6 | 0.55 | 54.6 |
| Fake dates from 1987 rather than 1995 | +2.0 | 0.60 | 12.1 |

Two registered checks reach p < 0.10 **in opposite directions**:

- **Detrended (+7.9):** extrapolates a decline in WA's relative turnover during 2008–09. That decline had levelled off by 2010 (event study below).
- **Net of food services (−19.3):** WA's cafes and restaurants grew unusually fast during the mining boom.

Neither is the registered estimate. Under the plan's grading rule the grade stays Moderate. Read the turnover finding as "no effect established; the sign depends on what WA is compared with". The evidence does not show an absence of effect.

## 4. Year by year

**Retail businesses, Perth vs regional WA, relative to other industries** (reference June 2010; 90% band across placebo industries and states):

| 30 June | 2009 | 2010 | 2011 | 2012 |
|---|---|---|---|---|
| Estimate | 0.0 | 0 (ref.) | −1.8 | −1.7 |
| No-effect band | −14.2 to +6.5 | | −8.8 to +4.5 | −10.2 to +7.9 |

**Turnover**, three-month bins (reference Apr–Jun 2010):

- **Before the reform:** from +6.7 (Jul–Sep 2008) down to about −1.8 (2009), then back to 0.
- **After the reform:** +0.3 (Nov 2010–Jan 2011) rising to about +3 to +3.7 through 2011–12.
- Every post-reform bin is inside its no-effect band.

## 5. What is new compared with the first evaluation

The first evaluation ([`results_wa_trading_hours.md`](results_wa_trading_hours.md)) pooled the 2010 and 2012 steps and used state-level CABEE entry and exit rates. It found no detectable effect on entry or exit.

This re-evaluation isolates the **weeknight step** and adds three new kinds of evidence:

- **A within-state geographic contrast:** Perth vs regional WA, using SA2-level business counts. This nets out WA-wide shocks such as the mining boom.
- **Monthly turnover** of the store types covered.
- **Hours worked** (not usable: WA's series failed its pre-reform check).

The two evaluations agree: no detectable effect on business numbers.

## 6. Limits

- **One treated state** (and one treated metropolitan area). Inference rests on placebo distributions, and effects below about 10% are not detectable.
- **Business counts are stocks at 30 June.** They proxy competition, but not prices or market shares. They stop at June 2012 because Sunday trading began in August 2012.
- **Two CABEE releases are chained at June 2011,** which adds vintage noise. The placebo industries are subject to the same noise.
- **The turnover outcome does not net out WA-specific demand.** Its variants show the sign is not robust.
- **Exits inferred from business names (ABN register) were not usable for 2010:** there are too few named retail exits, about 18 a year in regional WA.

## 7. Deviations and disclosures

- **No deviations from the plan.**
- **Event-study period labels:** added in the evaluation file for readability (`evaluation.py`), with no change to any number.
- **Order of work:**
  - design review (blinded);
  - plan;
  - dry run (blinded, reproduced the design-stage distributions);
  - hashes recorded;
  - one unblinded run.
- **Not yet committed:** the owner asked to hold commits. The hash record lets the order be checked when it is committed.
