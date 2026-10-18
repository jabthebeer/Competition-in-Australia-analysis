# Power study (forward plan Phase 3): how much each layer shrinks the no-effect spread

**Run:** 18 October 2026, blinded. **Code:** `alicia/analyses/power_study/run.py`. **Numbers:** `alicia/analyses/power_study/power.json` (every placebo estimate is stored).

**Blinding:**
- Before anything is computed, every row for a reform's treated industries in its treated states, from the first exposed year on, is deleted. A check in the code enforces this.
- No reform's effect was estimated.

## 1. Key findings (non-technical)

1. **State-wide economic conditions were not what kept the earlier results imprecise.**
   - Adding state × year effects, or measured state demand, unemployment, population and commodity controls, changed the smallest detectable effect by 1.5% or less for every reform.
   - For business entry and exit, a state's boom or slump moves all its industries' rates together only a little.
2. **Industry-wide cycles were.**
   - Comparing each industry with the same industry in other states (industry × year effects) cut the smallest detectable effect on entry rates by:
     - 28% (Perth weeknight trading);
     - 47% (Heavy Vehicle National Law);
     - 62% (Victorian taxi licences);
     - 77% (Legal Profession Uniform Law).
   - It beat the registered batch design for four of the five batch reforms it can be compared with.
3. **Where there is only one comparison state, synthetic DiD does best.** For the childcare framework (WA was the only comparison), synthetic DiD cut the entry-rate MDE from about 10 to 6 points; industry × year effects made it worse.
4. **Even the best design detects only large effects.** The best entry-rate MDEs are 2.5 to 6 points, against average rates of 13 to 16 entries per 100 businesses: roughly 15% to 45% of the rate. Smaller changes in business entry and exit cannot be detected with state-level CABEE counts.
5. **Two reforms cannot be studied this way.** The NT container deposit scheme and retail energy deregulation have treated groups too small at class × state level: 12 and 59 businesses, against a rule of 100.

## 2. Design

| Item | Choice |
|---|---|
| Outcome | Business entry and exit rates per 100 businesses at the start of the financial year (CABEE), ANZSIC class × state × year; cells weighted by businesses |
| Reforms | The seven high-evaluability reforms (registered CABEE vintage, to 2019-20); Perth weeknight trading (2010-11 to 2011-12); automatic mutual recognition (2021-22 and 2022-23, CABEE to 2024-25) |
| No-effect distribution | Placebo industries: the batch's size-matched class groups outside the treated divisions (up to 40), given the reform's treated states and dates. The same placebos for every layer |
| Measure | Smallest detectable effect (MDE), 80% power, 5% two-sided = 2.8 × standard deviation of placebo estimates. With 40 placebos each MDE has a sampling error of about ±11% |

**Layers compared** (*c* class, *s* state, *t* year; D = 1 for treated classes in treated states after adoption):

| Layer | Model |
|---|---|
| Two-way | y_{cst} = α_{cs} + λ_t + β·D_{cst} + ε |
| + state × year | y_{cst} = α_{cs} + γ_{st} + β·D_{cst} + ε |
| Saturated | y_{cst} = α_{cs} + δ_{ct} + γ_{st} + β·D_{cst} + ε |
| Measured controls | Two-way + state final demand growth, unemployment rate, population growth, mining share × commodity prices |
| Imputation | Saturated effects fitted on untreated cells only; effect = actual − imputed (Borusyak, Jaravel and Spiess) |
| Synthetic DiD | The treated group's rate against all untreated cells, with unit and time weights (Arkhangelsky et al.) |
| Generalised synthetic control | Interactive fixed effects; factors from untreated cells, chosen by cross-validation (Xu) |

## 3. Results: smallest detectable effect (points per 100 businesses)

**Entry rate:**

| Reform | Mean rate | Registered design | Two-way | + state × year | Saturated | Controls | Imputation | Synthetic DiD | Gen. synth. |
|---|---|---|---|---|---|---|---|---|---|
| Childcare NQF (2012) | 13.8 | 9.8 | 10.1 | 10.1 | 10.9 | 10.1 | 10.9 | **6.0** | 10.6 |
| Heavy Vehicle National Law (2014) | 13.6 | 9.4 | 8.3 | 8.3 | **4.4** | 8.3 | 4.4 | 8.7 | 10.0 |
| Victorian taxi licences (2014) | 13.0 | 4.2 | 9.1 | 9.2 | **3.5** | 9.2 | 3.5 | 9.2 | 9.2 |
| Legal Profession Uniform Law (2015) | 13.6 | 7.0 | 19.8 | 19.8 | **4.5** | 19.8 | 4.5 | 18.1 | 19.3 |
| Ride-share legalisation (2015–18) | 13.5 | 6.0 | 6.7 | 6.7 | 4.3 | 6.7 | 4.7 | **4.1** | 4.3 |
| Perth weeknight trading (2010) | 14.0 | — | 7.3 | 7.4 | **5.2** | 7.3 | 5.5 | 6.5 | 7.5 |
| Automatic mutual recognition (2021–22)* | 16.3 | — | 4.7 | 4.8 | 4.3 | 4.7 | **2.5** | 4.5 | 4.9 |

**Exit rate:**

| Reform | Mean rate | Registered design | Two-way | + state × year | Saturated | Controls | Imputation | Synthetic DiD | Gen. synth. |
|---|---|---|---|---|---|---|---|---|---|
| Childcare NQF (2012) | 13.6 | 8.1 | **2.2** | 2.3 | 4.8 | 2.2 | 4.9 | 2.5 | 2.5 |
| Heavy Vehicle National Law (2014) | 12.9 | 9.9 | 3.1 | 3.1 | 3.0 | 3.1 | 3.0 | **2.8** | 3.1 |
| Victorian taxi licences (2014) | 13.2 | 3.7 | 2.6 | 2.6 | **2.4** | 2.6 | 2.4 | 2.5 | 2.6 |
| Legal Profession Uniform Law (2015) | 13.0 | 2.6 | 3.6 | 3.6 | **1.6** | 3.6 | 1.6 | 3.1 | 3.4 |
| Ride-share legalisation (2015–18) | 13.0 | 5.7 | 3.2 | 3.2 | **2.2** | 3.2 | 2.4 | 2.7 | 3.3 |
| Perth weeknight trading (2010) | 13.8 | — | 3.4 | 3.4 | 4.5 | 3.4 | 4.3 | **3.0** | 3.5 |
| Automatic mutual recognition (2021–22)* | 13.1 | — | 1.8 | 1.8 | 1.3 | 1.8 | 1.7 | 2.0 | **0.9** |

- **Bold** marks the smallest MDE in each row.
- \*Automatic mutual recognition has only 24 placebo groups and one never-treated state (Queensland), and its window includes COVID years.
- "Registered design" is the batch's design-stage spread (stacked DiD net of placebo industries, `analyses/high_evaluability/design.json`; 39–74 placebos).
- Placebo means are near zero for every layer: the largest is 2.3 points, for synthetic DiD on the uniform law's entries. Most of the spread is noise, not systematic bias.

## 4. Use in Phase 5 (design choice, before any re-estimation)

| Reform | Proposed primary layer | Why |
|---|---|---|
| Heavy Vehicle National Law; Victorian taxi licences; Legal Profession Uniform Law | Saturated fixed effects | Largest reductions; single adoption date |
| Ride-share legalisation | Imputation (saturated) | Staggered adoption: imputation is robust to effects that change over time. It costs about 0.4 points of MDE against the static saturated model |
| Childcare NQF | Synthetic DiD | One comparison state; industry × year effects add WA's noise |
| Perth weeknight trading | Saturated for entries; synthetic DiD for exits | Layer ranking differs by outcome. Choose one per outcome in the plan, with reasons |
| Automatic mutual recognition | Imputation; generalised synthetic control as a check | Staggered. Few placebos, COVID years. Needs more placebo groups (classes outside the trades) before a plan is fixed |
| NT container deposits; retail energy deregulation | Not with CABEE classes | Treated groups too small. Prices or other data needed |

These are design-stage choices, made without seeing any treated post-reform outcome. Each Phase 5 plan should still state its layer before unblinding (forward plan §7).

## 5. Limits

- **Placebo industries only.**
  - Fake dates for the treated industries themselves, and placebo states, are not yet included. Single-state designs especially should add them.
  - The MDE ranking can change with the placebo family.
- **Only business entry and exit are tested.** Measured controls may matter more for single-series outcomes such as prices, where industry × year effects are not available. That is the next test.
- **Small differences are noise.** MDEs within about 10% of each other should be treated as equal (sampling error of the standard deviation with 40 placebos).
- **Smaller pools for two reforms.** Automatic mutual recognition (24 placebos) and the uniform law (39) have smaller pools.
