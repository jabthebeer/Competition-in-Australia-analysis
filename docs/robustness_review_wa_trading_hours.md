# Robustness review: Perth trading-hours deregulation (design stage, blinded)

**Status:** 15 October 2026. Design-stage review, run before any effect is estimated.

**What was used:** comparison states, WA's pre-reform years, and WA industries the reform did not touch.

**What was not used:** WA's post-reform outcomes for affected retail, and Perth prices after the reform. One exception is disclosed in §5.

**Files:**
- Code: `econ/analyses/wa_trading_hours/design_review.py`
- Results: `econ/analyses/wa_trading_hours/design_review.json`
- Pre-analysis plan: [`pap_wa_trading_hours.md`](pap_wa_trading_hours.md)

---

## 1. Verdict

The case is a sound demonstration. Public data can test it for **business entry and exit**, but **only large effects are detectable**.

| Outcome | Can public data test it? | Why |
|---|---|---|
| **Entry rate** (primary) | **Yes, for large effects** | 80% power needs about **6 entries per 100 businesses** (WA's pre-reform rate was 16). A 3-per-100 effect has 20% power |
| **Exit rate** | **Yes, for large effects** | 80% power at about **4 per 100** (pre-reform rate 15) |
| **Real food prices** (Perth vs other capitals) | Weakly | Smallest detectable effect about **3%** relative to the CPI. Comparison-city inference cannot go below p = 0.14 |
| Clothing prices | No | Perth clothing prices drift by about 9 log points in the pre-reform placebo test |
| **Retail productivity** | **No** | State-level retail output per worker is too noisy: smallest detectable effect 20–36%. Hours are also not available by state and industry before 2011-12, and longer trading hours change hours per worker. Descriptive only |
| Industry real wages | No | Same data limits as productivity. Secondary and descriptive only |

**Three design changes came out of the review**, and are now fixed in the pre-analysis plan:

1. **Net out a WA-wide shock.** Unaffected WA industries show entry falling by about 1.6 per 100 relative to other states after 2010-11, probably the mining cycle. A plain WA-versus-other-states comparison would blame the reform for it. The primary estimate subtracts the average of 472 size-matched placebo industry groups.
2. **Use industry placebos for inference.** With six comparison states, the smallest possible p-value is 0.14, so conventional significance is impossible. Ranking the retail result against 472 placebo industry groups allows p-values down to about 0.002.
3. **Drop 2018-19 from the main window.** It is the only year where the ABS accounting identity fails (a vintage break). The window is 2007-08 to 2017-18, which also keeps the analysis clear of COVID.

---

## 2. Why this case

The criteria are: before COVID, a clear mechanism, a narrow but well-populated industry, a credible comparison, and price and productivity measures. The leading candidates from the menu:

| Candidate | For | Against | Decision |
|---|---|---|---|
| **WA trading hours (2010, 2012)** | Discrete, register-confirmed dates; one state changed while the others' rules were stable; 7 post-reform years before COVID; the reform touches most of retail, so division-level data are not swamped by unaffected industries; CPI food and clothing by capital city | One treated state; short pre-period (3 years) for business data; WA's mining cycle | **Chosen** |
| Ride-sharing (2015–19) | Large shock; staggered across states | Ride-sharing ran before it was legal, so the legal date is not the economic date; GST registration of drivers created business-count artefacts | Not as the first case; a candidate "big shock" check later |
| Mutual recognition (2021–22) | Staggered; Queensland never joined | COVID overlaps the whole rollout | Deferred, as you asked |
| Victorian taxi licensing (2014) | Removed a cap on licence numbers | Uber arrived in Melbourne the same year | Confounded |
| NT minimum unit price (2018) | Clean price test (Darwin alcohol CPI) | Price channel only; 5 clean quarters before COVID | A possible second, "weakening", demonstration |
| Energy price deregulation (2009–16) | Staggered; CPI electricity by city | Network costs and the carbon price move the same prices | Too confounded |

The dates were checked against the WA register's history of the *Retail Trading Hours Act 1987* (law_a696):

| Step | Assent | Took effect | Source |
|---|---|---|---|
| Special trading precincts | Jul–Sep 2010 | Joondalup 8 Jul 2010; Armadale and Midland 23 Sep 2010 | WA register |
| 9pm weeknight trading | 1 Oct 2010 | **1 Nov 2010** | Gazette 22 Oct 2010 p 5207 |
| Sunday and public-holiday trading | 3 Jul 2012 | **26 Aug 2012** | Gazette 17 Aug 2012 p 3899 |

So deregulation began in **2010-11**: the first exposed financial year, with 66% of the year after 1 November 2010. The pre-period is 2007-08 to 2009-10.

---

## 3. Results, check by check

The checklist is §9 of [`impact_evaluation_design.md`](impact_evaluation_design.md). "Per 100" means entries (or exits) per 100 businesses operating at the start of the financial year.

| # | Check | Result | Verdict |
|---|---|---|---|
| RB-01 | **Pre-trends** (treated group, WA vs comparison states, relative to 2009-10) | 2007-08: −2.1; 2008-09: −1.0 per 100. Within the comparison-state spread (SD 1.7), but WA's retail entry was rising relative to other states before the reform. Only 3 pre-years, including the GFC | **Weak evidence either way.** The event-study path will be reported; HonestDiD-style bounds are pre-registered |
| RB-02 | **Placebo industries** (472 random size-matched groups of 3 unaffected WA classes) | Mean −1.58 per 100 (a WA-wide shock); SD 2.0 | **Changed the design**: the primary estimate is net of this mean |
| RB-03 | **Alternative comparison groups** | Dropping Queensland (2017 change) raises the smallest detectable effect from 4.7 to 5.3 per 100 | Pre-registered as a sensitivity |
| RB-04 | **Estimator** | One treated state at one date, so two-way fixed effects carry no negative-weighting problem. Unbiased in simulation (below) | OK |
| RB-05 | **Vintage revisions** (same year, adjacent ABS releases) | Treated group: mean absolute revision 0.86 per 100 (max 5.0); comparison group 0.62 | **Material**: about half the placebo SD. The main series uses each year's own release; the overlap vintage is a sensitivity |
| RB-06 | **Effective-date variants** | Announcement (30 Sep 2010), precincts and weeknights all fall in 2010-11, so they share one first-exposed year. Sundays (2012-13) show up as a second step in the event study | Pre-registered |
| RB-07 | **COVID** | Window ends 2017-18 | **Avoided** |
| RB-08 | **Small cells** | WA department stores average 19 businesses and 1 entry a year, all perturbed by the ABS. Supermarkets (712) and clothing (1,050) carry the treated group | Department stores stay in the pooled group but are never reported alone |
| RB-09 | **Inference** | Comparison-state placebos: smallest p = 0.14. Industry placebos: smallest p = 0.002 | **Changed the design**: industry-placebo ranks are primary; state placebos are reported alongside |
| RB-10 | **Power** (before estimating) | Entries: smallest detectable effect 5.6 per 100 (industry placebos), 4.7 (state placebos). Exits: 4.1 and 4.0 | Recorded in the plan with an interpretation rule: a null with a wide interval is "inconclusive", not "no effect" |
| RB-11 | **Multiple testing** | One primary outcome (entry rate); exits and prices secondary | Pre-registered |
| RB-12 | **Leave-one-state-out** | Implemented as the drop-Queensland variant; all others pre-registered | Pending estimation |
| RB-13 | **Specification curve** | Choices listed in the plan (vintage, window, treated set, comparison pool, state set) | Pending estimation |
| RB-14 | **Results-chain consistency** | Entry → prices: food CPI is testable but weak; productivity is not testable | The chain will be reported as partial |
| RB-15 | **Simulation recovery** (planting known effects in comparison states) | Mean bias +0.26 per 100, mean absolute error 1.3. The planted state ranks most extreme in 17% of runs at 0 or 1, 33% at 2, 50% at 3, 100% at 5 | **Estimator works**; only large effects stand out |

**Triple difference against three hand-picked comparison industries** (cafes and restaurants, takeaway food, fuel retailing): smaller smallest-detectable effect (3.0 per 100), but an erratic pre-period (−5.5 per 100 in 2007-08, driven by fuel retailing's small counts). It is kept as a secondary design. The industry-placebo approach replaces it as primary because it compares retail with hundreds of unaffected industries, not three.

---

## 4. Prices and productivity in detail

**Food prices.** The outcome is Perth's *Food and non-alcoholic beverages* index relative to its *All groups* CPI, compared with other capitals, quarterly from 2000 to 2019.
- Placebo SD across comparison cities: 1.1 log points, so the smallest detectable effect is about 3.2%.
- A fake reform dated 2006-Q1 in the pre-period gives −2.0, within noise.
- A trading-hours effect on grocery prices of a few percent is plausible but at the edge of detection.

**Clothing prices.** Placebo SD 2.4, and a fake reform in 2006 gives −8.6. Perth's relative clothing prices already moved a lot before the reform. Not credible as evidence; descriptive only.

**Retail productivity** (real value added per employed person, division G):
- Comparison-state placebo SD 12.9 log points (smallest detectable effect 36%). With NSW, Victoria, Queensland and Tasmania only: SD 7.2 (20%).
- Fake reforms in 2004-05 and 2006-07 give +6.5 and +5.0: WA's relative productivity swings that much without any reform.
- The measure is per person, not per hour. Longer trading hours shift work towards part-time shifts, which lowers output per person even if output per hour is unchanged.

Productivity is therefore reported as descriptive only. Measuring the productivity effect of this reform needs hours by state and industry (not published before 2011-12) or firm-level data.

---

## 5. Disclosures

- **Blinding breach (productivity).** WA's division-level retail output per worker for 2005–2019 was displayed once while validating the data on 15 October 2026, before this review. Productivity is not graded as evidence in any case (§4), but any productivity figure for this case is reported as "not blind".
- **Everything else is blind.** The review code sets WA's affected-retail outcomes from 2010-11, and Perth CPI from 2010-Q4, to missing before any estimator runs. No output reports them.
- **Records.** The two WA records remain drafts. Their dates are now confirmed against the register. Open question: whether liquor stores were covered (their hours fall under liquor licensing law). Liquor retailing (4123) is excluded from the treated group pending that check.

---

## 6. What this means for the wider programme

1. **One treated state is the binding constraint.** Even a clean case can only detect large effects. Every future pilot should prefer reform families adopted by several states, which give more treated units and finer inference.
2. **Industry placebos are the key tool for single-state cases.** They net out state-wide shocks and allow real p-values. They are now part of `regimpact.evaluate`.
3. **Productivity effects need better data than state-by-division publications.** Options are hours by state and industry (from 2011-12), the BLADE TableBuilder's per-business sales and wages, or a case large enough to move a whole division.
4. **Vintage choice matters.** Revisions between ABS releases are about half the noise level. Every result should be shown on both vintages.

---

## 7. Next step

Unblinding: run the pre-registered estimation in [`pap_wa_trading_hours.md`](pap_wa_trading_hours.md), with the plan committed first so the record shows it came before the results.
