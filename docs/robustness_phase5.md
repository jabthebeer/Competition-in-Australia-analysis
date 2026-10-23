# Robustness and diagnostics for the Phase 5 evaluations

**Date:** 18–19 October 2026. **Status:** not pre-registered. Run after the registered results were seen, it can show a result is fragile; it cannot turn a variant into a finding. Item 3 of the [due-diligence plan](due_diligence.md).

**Code:** `alicia/analyses/phase5/robustness.py`, a post-hoc stage of both Phase 5 specifications. **Output:** `analyses/phase5/{reevaluations,new_families}/robustness.json`. Each evaluation page has a second regression table, "robustness (not pre-registered)", and one key-insight line.

## 1. What was run

For each of the 25 feasible outcomes, the registered estimator was re-run on variants of the registered panel:
- **Leave one state out:** each treated or comparison state.
- **Window:** the first exposed year (four quarters for prices), and the last year dropped.
- **Pre-period:** from four years (business counts) or five years (prices) before first exposure.
- **Unweighted cells** (business counts).
- **Other CABEE vintages** (each year from the mean of the releases it is not final in).

**Inference:** each variant is judged against its own no-effect distribution, the same 40 placebo groups re-estimated on the variant with treated cells hidden, as at the design stage. The as-registered variant reproduces `estimate.json` (estimate and p exactly; placebo spread within rounding), which checks the machinery.

**Diagnostics:**
- **Pre-trend sensitivity:** Rambachan–Roth relative-magnitudes breakdown on the saturated event study.
- **Synthetic DiD:** weights and pre-period fit, wherever it is the registered or a check layer.
- **Programme-wide q-values:** across all 25 outcomes and across the 10 primaries.

## 2. Headline

- **"No detectable effect" holds everywhere it was found.** No identified primary outcome reaches p < 0.05 in any of its 9–13 variants. Signs are stable for the uniform law (13 of 13 negative), fuel prices (10 of 10 negative), e-conveyancing (12 of 13) and Perth trading hours (9 of 10).
- **Nothing survives programme-wide adjustment.** With Benjamini–Hochberg across all 25 outcomes, the smallest q-value is 0.28. Across the 10 primaries it is 0.24.
- **The secondary "leads" are fragile:**
  - Childcare exits (p = 0.049) are significant in only 4 of 9 variants. Significance disappears without NSW, Tasmania or Victoria, unweighted, or on other data vintages.
  - Victorian taxi exits (p = 0.049, pre-trend failed) lose significance without NSW or WA, with a shorter pre-period, or unweighted.
- **Two results are robust but not effects:**
  - Melbourne fares stay significant in 8 of 8 variants. The confounder scan dates the fall to the January 2015 public transport fare change, which no variant can remove.
  - Electricity prices after deregulation stay significant in 8 of 10 variants. But the pre-trend test failed, and the breakdown value is 0.05: a post-reform departure from parallel trends one-twentieth the size of the largest pre-reform change would explain it.
- **One point estimate is fragile.** The Heavy Vehicle National Law entry estimate is +0.3 as registered but −3.7 without WA, one of only two comparison states. The record already lists the WA mining downturn as a confounder. The conclusion (no detectable effect) holds; the point estimate should not be quoted alone.

## 3. Primary outcomes across variants

| Evaluation | Primary outcome | Registered estimate | p | Variants with the same sign | Variants with p < 0.05 | Range | Variant furthest from the registered estimate | Pre-trend breakdown M̄ |
|---|---|---|---|---|---|---|---|---|
| Perth retail trading hours (2010 weeknights, 2012 Sundays) | entries | +0.98 | 0.49 | 9 of 10 | 0 of 10 | −0.37 to +1.30 | Unweighted cells | 0.215 |
| National Quality Framework for childcare (2012) | entries | −0.28 | 0.85 | 8 of 9 | 0 of 9 | −0.85 to +0.27 | Other CABEE vintages | 0.26 |
| Heavy Vehicle National Law (2014) | entries | +0.27 | 0.85 | 10 of 13 | 0 of 13 | −3.67 to +0.56 | Without WA | 0.367 |
| As-of-right taxi licences in Victoria (2014) | entries | −0.36 | 0.68 | 8 of 10 | 0 of 10 | −1.45 to +0.52 | Unweighted cells | 0.091 |
| Legal Profession Uniform Law (2015) | entries | −1.26 | 0.47 | 13 of 13 | 0 of 13 | −1.63 to −1.04 | Unweighted cells | 0.636 |
| Ride-share legalisation (2015 to 2018) | entries | −2.24 | 0.17 | 9 of 11 | 1 of 11 | −4.48 to +2.82 | Unweighted cells | 0.674 |
| Northern Territory container deposit scheme (2012) | price-soft-drinks | +7.62 | 0.20 | 9 of 9 | 0 of 9 | +6.06 to +7.91 | Pre-period from 2007-Q1 | 0.163 |
| Retail energy price deregulation (SA 2013, NSW 2014, SEQ 2016) | price-electricity | +9.43 | 0.024 | 10 of 10 | 8 of 10 | +6.38 to +11.59 | Without TAS | 0.051 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | price-automotive-fuel | −2.85 | 0.20 | 10 of 10 | 0 of 10 | −3.57 to −2.06 | Without TAS | 0.393 |
| Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023) | entries | −0.58 | 0.54 | 12 of 13 | 0 of 13 | −1.28 to +0.03 | Without NSW | 0.24 |

**Breakdown values:** every one is below 1. A post-reform departure from parallel trends no larger than the largest change already seen before the reform could produce or hide each estimate. For results that are already "no detectable effect", that is expected. For electricity (0.05) it confirms the design-stage verdict, not identified.

## 4. Programme-wide multiple testing

Benjamini–Hochberg q-values across all Phase 5 outcomes, and across the primary outcomes only. Only outcomes with p < 0.10 are shown:

| Evaluation | Outcome | Role | Pre-trend check | p | q (all 25) | q (10 primaries) |
|---|---|---|---|---|---|---|
| As-of-right taxi licences in Victoria (2014) | price-urban-transport-fares | secondary | pass | 0.024 | 0.28 | — |
| Retail energy price deregulation (SA 2013, NSW 2014, SEQ 2016) | price-electricity | primary | fail | 0.024 | 0.28 | 0.24 |
| National Quality Framework for childcare (2012) | exits | secondary | pass | 0.049 | 0.28 | — |
| As-of-right taxi licences in Victoria (2014) | exits | secondary | fail | 0.049 | 0.28 | — |
| National Quality Framework for childcare (2012) | price-child-care | secondary | pass | 0.075 | 0.34 | — |

No outcome is below q = 0.10. The registered decision rule already required q < 0.10 within each specification. Across the programme, the only outcomes with p < 0.05 are a confounded fares fall, a non-identified electricity rise and two fragile exit results.

## 5. Why the estimators disagree

The two evaluations graded Weak (fuel, e-conveyancing) disagree because synthetic DiD uses a different comparison. Its weights show which:

- **E-conveyancing:**
  - Synthetic DiD spreads its weight almost evenly: 630–1,010 effective control cells out of 910–1,340, depending on the cohort.
  - That is close to an equal-weighted comparison with every other cell. It has no class × year effects, so it keeps the national movement in legal services' entry rate.
  - Its plain estimates (−0.9 to −3.4 by cohort) sit with the two-way estimate (−3.0). The saturated estimate, which removes legal services' national movement, is −0.6.
  - The disagreement is a national trend in legal services, not the reform.
- **Fuel prices:**
  - Synthetic DiD puts 42–78% of its weight on automotive fuel in Melbourne and Canberra, the cities that never reported (3–10 effective controls).
  - Its plain estimates by cohort are +2.3 (NSW), +1.3 (NT), −2.3 (Queensland), +0.6 (Tasmania) and +15.3 (SA).
  - The positive average comes from the SA 2021 cohort. The confounder scan finds a jump of 4.5 times the usual quarterly move in Adelaide's fuel gap in 2021-Q1.
  - The saturated estimate is stable: −2.1 to −3.6 in all 10 variants, none significant.
- **Childcare prices:** synthetic DiD puts 0.91 of its weight on child care in Perth, so its comparison is Perth alone.
- **Ride-share entry:** for the Victoria and NT cohort, synthetic DiD puts 0.48 of its weight on taxis in WA (3.7 effective controls). Plain estimates of +25 to +31 by cohort reflect the national surge in taxi-class ABNs as ride-share drivers registered. The design is not identified.

| Evaluation | Outcome | Cohort | Control cells | Effective controls | Pre-fit ratio | Largest weights | Estimate |
|---|---|---|---|---|---|---|---|
| Perth retail trading hours (2010 weeknights, 2012 Sundays) | entries | WA 2010-11 | 2064 | 1933.4 | 0.007 | 4320:ACT (0.001), 2640:QLD (0.001), 6322:ACT (0.001) | −0.72 |
| Perth retail trading hours (2010 weeknights, 2012 Sundays) | exits | WA 2010-11 | 2064 | 2011.8 | 0.009 | 2313:WA (0.001), 2611:NSW (0.001), 8520:TAS (0.001) | +1.26 |
| National Quality Framework for childcare (2012) | entries | NSW/VIC/QLD/SA/TAS/ACT/NT 2011-12 | 2414 | 2268.6 | 0.002 | 8212:ACT (0.003), 5291:SA (0.003), 0804:SA (0.002) | +0.32 |
| National Quality Framework for childcare (2012) | exits | NSW/VIC/QLD/SA/TAS/ACT/NT 2011-12 | 2414 | 949.8 | 0.004 | 4122:ACT (0.006), 1172:SA (0.005), 4820:SA (0.005) | −0.09 |
| National Quality Framework for childcare (2012) | price-child-care | NSW/VIC/QLD/SA/TAS/ACT/NT 2012-Q1 | 657 | 1.2 | 0.142 | 115498:WA (0.913), 40098:WA (0.073), 114121:NSW (0.013) | +4.54 |
| Heavy Vehicle National Law (2014) | entries | NSW/VIC/QLD/SA/TAS/ACT 2013-14 | 2395 | 1856.7 | 0.017 | 5420:ACT (0.002), 0600:VIC (0.001), 6230:TAS (0.001) | +2.32 |
| Heavy Vehicle National Law (2014) | exits | NSW/VIC/QLD/SA/TAS/ACT 2013-14 | 2395 | 2324.2 | 0.006 | 1821:WA (0.001), 2812:QLD (0.001), 2619:VIC (0.001) | +0.44 |
| As-of-right taxi licences in Victoria (2014) | entries | VIC 2014-15 | 2371 | 827.6 | 0.01 | 2611:WA (0.006), 1212:SA (0.005), 3921:ACT (0.005) | +1.37 |
| As-of-right taxi licences in Victoria (2014) | exits | VIC 2014-15 | 2371 | 1490.1 | 0.008 | 7720:SA (0.003), 3921:ACT (0.003), 2412:ACT (0.002) | −1.04 |
| As-of-right taxi licences in Victoria (2014) | price-urban-transport-fares | VIC 2014-Q3 | 679 | 68.9 | 0.271 | 40083:NT (0.048), 97557:SA (0.033), 115497:TAS (0.027) | −9.33 |
| Legal Profession Uniform Law (2015) | entries | NSW/VIC 2015-16 | 2362 | 1519.7 | 0.031 | 5420:QLD (0.003), 9111:ACT (0.002), 2393:VIC (0.002) | −0.68 |
| Legal Profession Uniform Law (2015) | exits | NSW/VIC 2015-16 | 2362 | 2135.8 | 0.014 | 1212:SA (0.001), 1920:QLD (0.001), 2210:WA (0.001) | +0.32 |
| Ride-share legalisation (2015 to 2018) | entries | ACT/NSW 2015-16 | 1379 | 789.1 | 0.044 | 2393:VIC (0.004), 9111:ACT (0.004), 9411:ACT (0.004) | +25.05 |
| Ride-share legalisation (2015 to 2018) | entries | SA/QLD/TAS 2016-17 | 1782 | 99.0 | 0.04 | 9003:SA (0.03), 7540:QLD (0.025), 6411:TAS (0.023) | +30.60 |
| Ride-share legalisation (2015 to 2018) | entries | VIC/NT 2017-18 | 803 | 3.7 | 0.214 | 4623:WA (0.475), 5299:WA (0.129), 2449:WA (0.114) | +25.23 |
| Ride-share legalisation (2015 to 2018) | price-urban-transport-fares | ACT/NSW 2015-Q4 | 421 | 151.2 | 0.275 | 97558:NT (0.023), 40055:NT (0.022), 40083:NT (0.017) | +0.59 |
| Ride-share legalisation (2015 to 2018) | price-urban-transport-fares | SA/QLD/TAS 2016-Q3 | 505 | 84.1 | 0.09 | 115524:WA (0.035), 40055:VIC (0.03), 40101:TAS (0.026) | −3.89 |
| Ride-share legalisation (2015 to 2018) | price-urban-transport-fares | VIC 2017-Q3 | 169 | 12.3 | 0.461 | 40046:VIC (0.151), 40005:VIC (0.113), 40055:VIC (0.102) | +1.20 |
| Ride-share legalisation (2015 to 2018) | price-urban-transport-fares | NT 2018-Q1 | 169 | 16.3 | 0.229 | 40083:NT (0.198), 97558:NT (0.074), 115497:NT (0.061) | +0.85 |
| Northern Territory container deposit scheme (2012) | price-soft-drinks | NT 2012-Q1 | 566 | 96.3 | 0.181 | 97558:ACT (0.027), 115495:WA (0.025), 30014:WA (0.019) | −2.38 |
| Northern Territory container deposit scheme (2012) | price-beer | NT 2012-Q1 | 566 | 154.8 | 0.125 | 115524:WA (0.021), 40055:WA (0.02), 40055:VIC (0.018) | −1.04 |
| Retail energy price deregulation (SA 2013, NSW 2014, SEQ 2016) | price-electricity | SA 2013-Q1 | 414 | 6.9 | 0.394 | 40055:TAS (0.314), 40055:WA (0.122), 40072:ACT (0.075) | −6.67 |
| Retail energy price deregulation (SA 2013, NSW 2014, SEQ 2016) | price-electricity | NSW 2014-Q3 | 414 | 4.6 | 0.361 | 40055:TAS (0.339), 40055:WA (0.238), 40090:TAS (0.152) | −11.83 |
| Retail energy price deregulation (SA 2013, NSW 2014, SEQ 2016) | price-electricity | QLD 2016-Q3 | 414 | 6.0 | 0.25 | 40090:TAS (0.238), 40090:WA (0.235), 40055:NT (0.156) | −15.05 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | price-automotive-fuel | NSW 2016-Q3 | 402 | 3.9 | 0.259 | 40081:VIC (0.368), 40081:ACT (0.339), 40055:TAS (0.05) | +2.26 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | price-automotive-fuel | NT 2017-Q4 | 402 | 3.2 | 0.281 | 40081:ACT (0.389), 40081:VIC (0.385), 40086:VIC (0.106) | +1.31 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | price-automotive-fuel | QLD 2018-Q4 | 402 | 3.2 | 0.235 | 40081:VIC (0.41), 40081:ACT (0.368), 40008:QLD (0.049) | −2.29 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | price-automotive-fuel | TAS 2020-Q3 | 242 | 8.6 | 0.421 | 40081:VIC (0.229), 40081:ACT (0.225), 40086:VIC (0.058) | +0.59 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | price-automotive-fuel | SA 2021-Q1 | 242 | 10.1 | 0.436 | 40081:VIC (0.214), 40081:ACT (0.204), 40055:ACT (0.043) | +15.33 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | entries | NSW 2016-17 | 1542 | 969.8 | 0.023 | 5420:ACT (0.003), 2391:VIC (0.003), 5420:NSW (0.003) | −1.68 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | entries | NT 2017-18 | 1247 | 62.3 | 0.158 | 1132:VIC (0.045), 1133:SA (0.036), 5801:VIC (0.034) | +2.27 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | entries | QLD 2018-19 | 1529 | 503.0 | 0.053 | 2591:ACT (0.009), 8021:QLD (0.007), 6230:TAS (0.007) | −0.22 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | entries | TAS/SA 2020-21 | 1117 | 147.8 | 0.129 | 6632:TAS (0.017), 5102:TAS (0.017), 0700:SA (0.016) | +1.18 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | exits | NSW 2016-17 | 1542 | 1215.9 | 0.023 | 5420:ACT (0.003), 4123:ACT (0.003), 1012:TAS (0.002) | +1.83 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | exits | NT 2017-18 | 1247 | 76.4 | 0.088 | 3606:TAS (0.026), 9209:TAS (0.024), 0171:TAS (0.024) | +2.79 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | exits | QLD 2018-19 | 1529 | 753.5 | 0.02 | 1212:SA (0.007), 6322:ACT (0.006), 4273:ACT (0.005) | +0.88 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | exits | TAS/SA 2020-21 | 1117 | 285.3 | 0.079 | 6322:VIC (0.017), 6999:TAS (0.013), 3731:TAS (0.012) | +0.65 |
| Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023) | entries | NSW 2017-18 | 1336 | 1008.5 | 0.045 | 1012:NT (0.003), 4214:ACT (0.003), 5420:QLD (0.003) | −1.29 |
| Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023) | entries | WA 2018-19 | 1283 | 1000.3 | 0.036 | 4214:ACT (0.003), 4229:TAS (0.003), 5420:QLD (0.003) | −3.39 |
| Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023) | entries | VIC 2019-20 | 1329 | 939.0 | 0.04 | 1012:NT (0.003), 9411:ACT (0.003), 5420:QLD (0.003) | −1.86 |
| Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023) | entries | SA 2020-21 | 1253 | 790.2 | 0.047 | 6322:QLD (0.007), 1012:NT (0.005), 0700:SA (0.003) | −2.93 |
| Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023) | entries | QLD 2022-23 | 908 | 627.8 | 0.083 | 1012:NT (0.005), 9111:ACT (0.004), 7312:NT (0.004) | −0.93 |

The pre-fit ratio is the spread of the treated-minus-weighted-controls gap before the reform, over the spread of the treated series. With few pre-reform years, a close fit is easy, so for business counts it says little. Estimates are plain, before the placebo mean is netted out.

## 6. What changes

- **No verdict or grade changes.** Robustness is not pre-registered.
- **Evaluation pages:** each carries the robustness table and one key-insight line for its primary outcome. The table shows which secondary leads are fragile, such as childcare exits, significant in 4 of 9 variants.
- **Before quoting a point estimate:** check its robustness row. The heavy vehicle law estimate depends on WA. The fuel and e-conveyancing disagreements are explained above and do not change "no detectable effect".

## 7. Limits

- **Pre-trend bounds** use an approximate interval (`evaluate/honest.py`). The reference implementation (R HonestDiD) is not yet run (due-diligence item 4).
- **Leave-one-out with few states** changes the comparison a lot. A state's removal moving the estimate shows dependence, not which state is right.
- **The vintage variant** replaces each year with the mean of its other releases. It tests revisions, not a single alternative vintage.
- **Not covered:** variants for the two older designs (Perth weeknight, NQF in WA). Their registered robustness checks are already in their regression tables.
