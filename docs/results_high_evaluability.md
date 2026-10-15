# Results: the high-evaluability batch

**Status:** 15 October 2026. Registered analysis, unblinded once after the plan and design stage were committed (`4daadb9`).

**Files:**
- Plan: [`pap_high_evaluability.md`](pap_high_evaluability.md)
- Code: `econ/analyses/high_evaluability/run.py`
- Results: `estimate.json`
- Register evaluation files: `regulation-register/evaluations/`
- Also browsable in the menu explorer (Evaluated filter, Results tab)

---

## 1. Headline

**None of the seven reforms shows a detectable effect on how many businesses entered or left the affected industry.**

| Status | Reforms |
|---|---|
| Evaluated for entry and exit | Four: childcare quality framework, Heavy Vehicle National Law, Victorian taxi licences, Legal Profession Uniform Law |
| Not identified | Three: NT container deposits and retail energy deregulation (too few businesses in the data); ride-share legalisation (the states had already diverged before it) |

**What the evaluated reforms show:**
- **Point estimates are small and none is significant.** Every Benjamini–Hochberg q-value is 0.83 or higher.
- **Where the intervals are narrow enough, they rule out large rises in entry.** This assumes the treated states would otherwise have tracked the comparison states, after netting out unaffected industries. For example, a rise of more than about 1 per 100 a year is ruled out for:
  - road freight under the Heavy Vehicle National Law;
  - legal services under the Uniform Law;
  - Victorian taxis in the first year.

**Prices.** No reliable price effect. Two price estimates cleared conventional thresholds, and both have other explanations:
- **Electricity (+17%):** continues a decade-long pre-existing rise. With each city's trend removed it is −0.6%.
- **Melbourne urban transport fares (−11%):** coincides with public transport fare changes from January 2015.

**Productivity and pay.** Not measurable with public division-level data. Placebo spreads are 5 to 24 log points.

## 2. Summary

Effects are per 100 businesses a year, net of unaffected industries in the same states, with 90% intervals.

| Reform | Hypothesis | Entry | Exit | Verdict | Grade |
|---|---|---|---|---|---|
| NT container deposits (2012) | mixed | not evaluable (12 businesses) | not evaluable | Not identified | Not identified |
| Childcare quality framework: first year (2012) | weakening | −0.3 (−5.9 to +4.3), p = 0.93 | +3.1 (−1.4 to +6.9), p = 0.24 | Inconclusive (wide) | Moderate |
| Retail energy deregulation (2013–16) | enhancing | not evaluable (59 businesses) | not evaluable | Not identified | Not identified |
| Heavy Vehicle National Law (2014) | enhancing | −2.2 (−5.9 to +0.9), p = 0.33 | −1.5 (−3.8 to +0.8), p = 0.31 | Inconclusive (wide) | Moderate |
| Victorian taxi licences (2014, first year) | enhancing | −1.4 (−3.4 to +0.9), p = 0.32 | −1.4 (−3.6 to +0.8), p = 0.32 | Inconclusive | Weak (cap: UberX, one year) |
| Legal Profession Uniform Law (2015) | enhancing | −1.6 (−5.8 to +1.2), p = 0.53 | −0.2 (−1.8 to +1.0), p = 0.85 | Inconclusive (wide) | Moderate |
| Ride-share legalisation (2015–18) | enhancing | +0.2 (−3.2 to +4.3), not headlined | −2.1 (−4.8 to +0.7), not headlined | Not identified | Not identified (pre-trend) |

The verification checks are in §6. The robustness variants for every evaluated reform stay inside its main 90% interval:

| Reform | Entry estimates across variants |
|---|---|
| Childcare | −3.1 to +0.5 |
| Heavy vehicles | −4.5 to −0.1 |
| Taxis | −1.8 to −0.5 |
| Legal profession | −1.8 to +0.4 |

## 3. Reform by reform

**NT container deposits.**
- *Entry and exit:* the treated industries (soft drinks, beer, materials recovery) had 12 NT businesses in 2010-11, below the plan's minimum of 100.
- *Soft-drink prices:* Darwin prices rose 8.7% relative to other capitals and other CPI classes (p = 0.12). But the year-by-year path shows them rising for a decade before the scheme. With each city's trend removed: +1.4% (p = 0.74).
- *Beer:* +4.3% (p = 0.41).
- *Size of the test:* a 10-cent deposit is a few per cent of a drink's price, well below the smallest effect these data can detect (19%).

**Childcare quality framework.**
- *What could be compared:* the framework started in January 2012 everywhere except WA, which started in August 2012. Only 2011-12 can be compared.
- *Result:* entry in the states with the framework moved by −0.3 per 100 relative to WA, and exits by +3.1. Neither is distinguishable from zero.
- *Limit:* with one comparison state, only first-year effects above about 10 per 100 were detectable.
- *Prices (descriptive):* childcare fees −4.3% (detrended +4.8%).

**Retail energy deregulation.**
- *Entry and exit:* the three states had 59 electricity retailers. CABEE counts each retailer in its head-office state, so business counts cannot show where retailers compete.
- *Electricity prices:* the registered estimate is +17.0% (90% interval +12.0 to +23.0, p = 0.01). That is opposite to the hypothesis, but it continues a rise relative to the regulated states that began more than a decade before deregulation, probably network charges. The registered detrended check gives −0.6% (p = 0.86).
- *Grade:* the price result is graded Not identified. That grade is a judgement made after unblinding.

**Heavy Vehicle National Law.**
- *Result:* road freight entry in the six adopting jurisdictions changed by −2.2 per 100 a year relative to WA and the NT; exits by −1.5. Neither is distinguishable from zero.
- *What is ruled out:* a rise in entry of more than about 0.9 per 100 a year, if road freight would otherwise have tracked WA and the NT.
- *Most sensitive variant:* dropping WA as a comparison gives −4.5.
- *Productivity (descriptive):* transport output per worker fell 26% relative to WA and the NT. That is far more than a freight law could plausibly cause, and most likely reflects the resources boom there.

**Victorian taxi licences.**
- *Result:* in 2014-15, the one usable year, entry changed by −1.4 per 100 relative to other states, and exits by −1.4. Neither is distinguishable from zero.
- *What is ruled out:* a first-year rise above about 0.9 per 100.
- *Grade:* Weak, because unlicensed UberX arrived in Melbourne the same year.
- *Fares (descriptive):* Melbourne urban transport fares fell 10.7% relative to other capitals. Urban transport fares are mostly public transport, and Melbourne's CBD Free Tram Zone started on 1 January 2015, so this is almost certainly not a taxi effect.

**Legal Profession Uniform Law.**
- *Result:* legal services entry in NSW and Victoria changed by −1.6 per 100 a year over three years; exits by −0.2. Neither is distinguishable from zero.
- *What is ruled out:*
  - exit changes beyond about 1.8 per 100;
  - entry rises above about 1.2 per 100.
- *What it may have missed:* the law mainly lowers costs for firms practising in both states, which counts by main state cannot see directly.

**Ride-share legalisation.**
- *Why not identified:* taxi and road-transport entry in the legalising states was 6 to 17 per 100 above the comparison states in the years before legalisation, so the design fails its pre-reform check.
- *Confounders:*
  - ride-sharing ran before it was legal in most capitals;
  - drivers had to register for GST from August 2015 wherever it ran.
- *Estimates* are reported for transparency but not headlined.

## 4. Productivity and pay (descriptive)

Division-level real output and real pay per employed person, net of the other 17 divisions in the same states (log points):

| Reform | Division | Output per worker | Real pay per worker |
|---|---|---|---|
| NT container deposits | Manufacturing | +26.0 (p = 0.28) | −16.9 (p = 0.39) |
| Childcare framework | Health care and social assistance | +9.3 (p = 0.67) | +11.5 (p = 0.56) |
| Energy deregulation | Electricity, gas, water and waste | +12.5 (p = 0.22) | +15.6 (p = 0.22) |
| Heavy Vehicle National Law | Transport, postal and warehousing | −26.2 (p = 0.11) | −23.3 (p = 0.11) |
| Victorian taxis | Transport, postal and warehousing | −9.2 (p = 0.39) | −8.6 (p = 0.28) |
| Legal Profession Uniform Law | Professional, scientific and technical | −8.1 (p = 0.06) | −11.5 (p = 0.17) |
| Ride-share | Transport, postal and warehousing | −11.3 (p = 0.16) | −10.4 (p = 0.11) |

Each reformed industry is a small part of its division, and divisions swing by tens of per cent across states for unrelated reasons. These figures do not measure the reforms' productivity effects.

## 5. What this means for the programme

1. **"High" on the screen overstated what public data can do.** Three of the seven reforms failed on data or diagnostics before any result was seen. The screen should add three things:
   - a minimum treated business count in CABEE;
   - a flag for industries whose businesses are counted at a head office rather than where they compete;
   - the real end of the class-by-state entry and exit data (2019-20, not 2024-25).
2. **One to six treated states detect only large effects.** The smallest detectable effects were 4 to 10 per 100. That is enough to rule out large rises in entry, but not to find modest effects.
   - *Exploratory pattern (not pre-registered):* all three evaluated "enhancing" reforms (heavy vehicles, taxis, legal profession) have negative entry estimates. Three of three has a two-sided sign-test p of 0.25, so this is not evidence of anything yet. Pooling more reforms would sharpen it.
3. **Prices need trend checks by default.** That has now been confirmed three times (Perth food, Darwin soft drinks, electricity). Decision E-31 already registers it.
4. **Productivity effects need firm-level or finer industry data.** Options are the BLADE TableBuilder, or ABS industry hours by state.

## 6. Verification, deviations and disclosures

- **Verification.** Independent code (pandas plus normal equations, no `regimpact` estimators) reproduces two cases exactly:
  - the legal profession and heavy vehicle plain estimates;
  - their placebo counts, net estimates and p-values.
- **No registered analysis was changed.**
- **Readings made after unblinding** (also listed in the plan's §11):
  - the energy price grade;
  - the explanation of the Melbourne fare fall;
  - the trend reading of Darwin soft-drink prices;
  - the resources-boom reading of transport productivity;
  - the sign-test observation.
- **Register status.** All records remain drafts; only dates were checked against registers.
