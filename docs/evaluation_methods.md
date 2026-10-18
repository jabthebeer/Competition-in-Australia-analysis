# Evaluations: key insights and methods

Generated from `regulation-register/evaluations/` by `alicia methods`. Do not edit by hand: change the analysis's builder script and regenerate.

## National Quality Framework for childcare (2012): the WA stagger

`childcare-nqf-2012` · evaluated 15 October 2026 · grade Moderate

In 2011-12, the framework's first year, childcare business entry in the states that had it changed by −0.3 per 100 relative to WA, which started seven months later (90% interval −5.9 to +4.3); exits by +3.1 (90% interval −1.4 to +6.9). Neither is distinguishable from zero.

**Key insights**

- The question: did the National Quality Framework for childcare change how many childcare businesses opened or closed in its first year (2011-12)?
- The comparison: the seven jurisdictions that started in January 2012 against WA, which started seven months later. Changes shared by every industry in the same states (a state's boom or slump) were removed by subtracting the same comparison for industries the reform did not touch.
- What we found: no detectable change. Openings moved −0.3 per 100 businesses (90% interval −5.9 to +4.3) and closures +3.1 (−1.4 to +6.9).
- How precise: only changes larger than about 10 openings per 100 businesses a year could have been detected, so a modest effect cannot be ruled out.
- What it means: a first-year check against one comparison state, not the long-run effect of the later staff ratio and qualification phases. The follow-up evaluation with monthly data agrees.

**What we did**

1. Took the treated industries (8710 Child Care Services) and the adopting states and dates from the register records; cohorts: NSW, VIC, QLD, SA, TAS, ACT, NT in 2011-12 against WA. Comparison states are those not yet treated in each cohort's window.
2. Built yearly entry and exit rates from ABS Counts of Australian Businesses (registered release vintage), 2007-08 on, pooling the treated classes in each state.
3. Drew placebo groups of the same number of classes from outside the treated division, matched on size (7223 businesses in the treated states in 2010-11); 75 qualified.
4. Design stage with every treated outcome hidden: checked the feasibility rules (at least 100 treated businesses and 19 placebo groups) and the power, then committed the plan (docs/pap_high_evaluability.md).
5. Estimated the stacked difference-in-differences for the treated group and every placebo group, and subtracted the placebo mean.
6. Checked each pre-reform year against its 95% placebo band, and ran the registered robustness variants (the other ABS vintage, employing businesses only, leaving each state out).
7. Applied the plan's decision and grading rules, with Benjamini–Hochberg q-values across the batch.
8. Prices: the same estimator on each city's CPI class relative to its all-groups index, against placebo CPI classes, with a registered variant that removes each city's pre-reform linear trend.

**Econometric model**

Stacked difference-in-differences with clean comparison states, net of the same estimate for unaffected industries in the same states (a triple difference), with inference from placebo industries.

*For each cohort c (states adopting together), over its window*

> y<sub>s,t</sub> = α<sub>s</sub> + λ<sub>t</sub> + β<sub>c</sub> · D<sub>s,t</sub> + ε<sub>s,t</sub>,   s ∈ treated<sub>c</sub> ∪ comparison<sub>c</sub>

*Stacked across cohorts*

> β̂ = Σ<sub>c</sub> n<sub>c</sub> β̂<sub>c</sub> / Σ<sub>c</sub> n<sub>c</sub>

*Reported estimate: net of unaffected industries*

> β̂<sup>net</sup> = β̂ − (1/P) Σ<sub>p=1</sub><sup>P</sup> β̂<sub>p</sub>

*Prices (capital cities, quarterly; same estimator, net of other CPI classes)*

> y<sub>k,q</sub> = 100 × ln(P<sup>class</sup><sub>k,q</sub> / P<sup>all groups</sup><sub>k,q</sub>)

*Output and pay per worker (descriptive; net of other divisions)*

> y<sub>s,t</sub> = 100 × ln(GVA per worker<sub>s,t</sub>) for the treated industry's division

| Symbol | Meaning |
|---|---|
| y<sub>s,t</sub> | Entries (or exits) per 100 businesses operating at the start of financial year t in state s, for the treated ANZSIC classes pooled (8710 Child Care Services) |
| α<sub>s</sub>, λ<sub>t</sub> | State and year fixed effects |
| D<sub>s,t</sub> | 1 for an adopting state from its first exposed financial year on, else 0 |
| n<sub>c</sub> | Number of treated states in cohort c |
| β̂<sub>p</sub> | The same stacked estimate for placebo group p: classes outside the treated division, matched on size, in the same states and years |
| P | Number of placebo groups: 75 qualified on size, 74 with every year of the window |
| P<sup>class</sup><sub>k,q</sub> | CPI for the expenditure class in capital city k, quarter q |

- **Estimand:** The average change in the treated industries' entry (or exit) rate in the adopting states over the exposed years, relative to the comparison states, beyond the change for unaffected industries in the same states (ACT, NSW, NT, QLD, SA, TAS, VIC).
- **Identifying assumption:** Without the reform, the treated industries' rate in the adopting states would have moved as in the comparison states once state-wide changes shared with unaffected industries are removed (triple-difference parallel trends). Checked with the pre-reform event-study coefficients.
- **Inference:** No conventional standard errors (few treated states). p-value: two-sided rank of β̂<sup>net</sup> among the P centred placebo estimates. 90% interval: β̂<sup>net</sup> minus the 95th and 5th percentiles of the centred placebos (Conley and Taber 2011). Smallest detectable effect: 2.8 × their standard deviation.

## Heavy Vehicle National Law (2014)

`heavy-vehicle-national-law-2014` · evaluated 15 October 2026 · grade Moderate

Road freight business entry in the six jurisdictions that adopted the Heavy Vehicle National Law changed by −2.2 per 100 a year relative to WA and the NT, net of other industries (90% interval −5.9 to +0.9); exits by −1.5 (90% interval −3.8 to +0.8). Neither is distinguishable from zero.

**Key insights**

- The question: did one national law for heavy vehicles (February 2014) change how many road freight businesses started or closed?
- The comparison: the six jurisdictions that adopted it against WA and the Northern Territory, which did not, from 2007-08 to 2017-18. Changes shared by every industry in the same states (a state's boom or slump) were removed by subtracting the same comparison for industries the reform did not touch.
- What we found: no detectable change. Openings moved −2.2 per 100 businesses a year (90% interval −5.9 to +0.9) and closures −1.5 (−3.8 to +0.8).
- How precise: a rise in openings of more than about 0.9 per 100 a year is ruled out; a fall cannot be ruled out.
- What it means: no sign that the law drew in new freight firms. The comparison rests on WA and the NT, which rode the resources boom.

**What we did**

1. Took the treated industries (4610 Road Freight Transport) and the adopting states and dates from the register records; cohorts: NSW, VIC, QLD, SA, TAS, ACT from 2013-14 to 2017-18 against WA, NT. Comparison states are those not yet treated in each cohort's window.
2. Built yearly entry and exit rates from ABS Counts of Australian Businesses (registered release vintage), 2007-08 on, pooling the treated classes in each state.
3. Drew placebo groups of the same number of classes from outside the treated division, matched on size (44908 businesses in the treated states in 2012-13); 41 qualified.
4. Design stage with every treated outcome hidden: checked the feasibility rules (at least 100 treated businesses and 19 placebo groups) and the power, then committed the plan (docs/pap_high_evaluability.md).
5. Estimated the stacked difference-in-differences for the treated group and every placebo group, and subtracted the placebo mean.
6. Checked each pre-reform year against its 95% placebo band, and ran the registered robustness variants (the other ABS vintage, employing businesses only, leaving each state out, adding 2018-19).
7. Applied the plan's decision and grading rules, with Benjamini–Hochberg q-values across the batch.

**Econometric model**

Stacked difference-in-differences with clean comparison states, net of the same estimate for unaffected industries in the same states (a triple difference), with inference from placebo industries.

*For each cohort c (states adopting together), over its window*

> y<sub>s,t</sub> = α<sub>s</sub> + λ<sub>t</sub> + β<sub>c</sub> · D<sub>s,t</sub> + ε<sub>s,t</sub>,   s ∈ treated<sub>c</sub> ∪ comparison<sub>c</sub>

*Stacked across cohorts*

> β̂ = Σ<sub>c</sub> n<sub>c</sub> β̂<sub>c</sub> / Σ<sub>c</sub> n<sub>c</sub>

*Reported estimate: net of unaffected industries*

> β̂<sup>net</sup> = β̂ − (1/P) Σ<sub>p=1</sub><sup>P</sup> β̂<sub>p</sub>

*Output and pay per worker (descriptive; net of other divisions)*

> y<sub>s,t</sub> = 100 × ln(GVA per worker<sub>s,t</sub>) for the treated industry's division

| Symbol | Meaning |
|---|---|
| y<sub>s,t</sub> | Entries (or exits) per 100 businesses operating at the start of financial year t in state s, for the treated ANZSIC classes pooled (4610 Road Freight Transport) |
| α<sub>s</sub>, λ<sub>t</sub> | State and year fixed effects |
| D<sub>s,t</sub> | 1 for an adopting state from its first exposed financial year on, else 0 |
| n<sub>c</sub> | Number of treated states in cohort c |
| β̂<sub>p</sub> | The same stacked estimate for placebo group p: classes outside the treated division, matched on size, in the same states and years |
| P | Number of placebo groups: 41 qualified on size, 41 with every year of the window |

- **Estimand:** The average change in the treated industries' entry (or exit) rate in the adopting states over the exposed years, relative to the comparison states, beyond the change for unaffected industries in the same states (ACT, NSW, QLD, SA, TAS, VIC).
- **Identifying assumption:** Without the reform, the treated industries' rate in the adopting states would have moved as in the comparison states once state-wide changes shared with unaffected industries are removed (triple-difference parallel trends). Checked with the pre-reform event-study coefficients.
- **Inference:** No conventional standard errors (few treated states). p-value: two-sided rank of β̂<sup>net</sup> among the P centred placebo estimates. 90% interval: β̂<sup>net</sup> minus the 95th and 5th percentiles of the centred placebos (Conley and Taber 2011). Smallest detectable effect: 2.8 × their standard deviation.

## Legal Profession Uniform Law (NSW and Victoria, 2015)

`legal-profession-uniform-law-2015` · evaluated 15 October 2026 · grade Moderate

Legal services business entry in NSW and Victoria changed by −1.6 per 100 a year in the three years after the Uniform Law, relative to other states and net of other industries (90% interval −5.8 to +1.2); exits by −0.2 (90% interval −1.8 to +1.0). Neither is distinguishable from zero.

**Key insights**

- The question: did the Legal Profession Uniform Law (NSW and Victoria, July 2015) change how many legal practices started or closed?
- The comparison: NSW and Victoria against the six jurisdictions that had not adopted it, over the three years after. Changes shared by every industry in the same states (a state's boom or slump) were removed by subtracting the same comparison for industries the reform did not touch.
- What we found: no detectable change. Openings moved −1.6 per 100 businesses a year (90% interval −5.8 to +1.2) and closures −0.2 (−1.8 to +1.0).
- How precise: changes in closures beyond about 2 per 100 are ruled out, as is a rise in openings of more than about 1.2.
- What it means: the law mainly cuts costs for firms working in both states, which counts of businesses by main state cannot see directly.

**What we did**

1. Took the treated industries (6931 Legal Services) and the adopting states and dates from the register records; cohorts: NSW, VIC from 2015-16 to 2017-18 against QLD, SA, WA, TAS, ACT, NT. Comparison states are those not yet treated in each cohort's window.
2. Built yearly entry and exit rates from ABS Counts of Australian Businesses (registered release vintage), 2007-08 on, pooling the treated classes in each state.
3. Drew placebo groups of the same number of classes from outside the treated division, matched on size (13060 businesses in the treated states in 2014-15); 39 qualified.
4. Design stage with every treated outcome hidden: checked the feasibility rules (at least 100 treated businesses and 19 placebo groups) and the power, then committed the plan (docs/pap_high_evaluability.md).
5. Estimated the stacked difference-in-differences for the treated group and every placebo group, and subtracted the placebo mean.
6. Checked each pre-reform year against its 95% placebo band, and ran the registered robustness variants (the other ABS vintage, employing businesses only, leaving each state out, adding 2018-19).
7. Applied the plan's decision and grading rules, with Benjamini–Hochberg q-values across the batch.

**Econometric model**

Stacked difference-in-differences with clean comparison states, net of the same estimate for unaffected industries in the same states (a triple difference), with inference from placebo industries.

*For each cohort c (states adopting together), over its window*

> y<sub>s,t</sub> = α<sub>s</sub> + λ<sub>t</sub> + β<sub>c</sub> · D<sub>s,t</sub> + ε<sub>s,t</sub>,   s ∈ treated<sub>c</sub> ∪ comparison<sub>c</sub>

*Stacked across cohorts*

> β̂ = Σ<sub>c</sub> n<sub>c</sub> β̂<sub>c</sub> / Σ<sub>c</sub> n<sub>c</sub>

*Reported estimate: net of unaffected industries*

> β̂<sup>net</sup> = β̂ − (1/P) Σ<sub>p=1</sub><sup>P</sup> β̂<sub>p</sub>

*Output and pay per worker (descriptive; net of other divisions)*

> y<sub>s,t</sub> = 100 × ln(GVA per worker<sub>s,t</sub>) for the treated industry's division

| Symbol | Meaning |
|---|---|
| y<sub>s,t</sub> | Entries (or exits) per 100 businesses operating at the start of financial year t in state s, for the treated ANZSIC classes pooled (6931 Legal Services) |
| α<sub>s</sub>, λ<sub>t</sub> | State and year fixed effects |
| D<sub>s,t</sub> | 1 for an adopting state from its first exposed financial year on, else 0 |
| n<sub>c</sub> | Number of treated states in cohort c |
| β̂<sub>p</sub> | The same stacked estimate for placebo group p: classes outside the treated division, matched on size, in the same states and years |
| P | Number of placebo groups: 39 qualified on size, 39 with every year of the window |

- **Estimand:** The average change in the treated industries' entry (or exit) rate in the adopting states over the exposed years, relative to the comparison states, beyond the change for unaffected industries in the same states (NSW, VIC).
- **Identifying assumption:** Without the reform, the treated industries' rate in the adopting states would have moved as in the comparison states once state-wide changes shared with unaffected industries are removed (triple-difference parallel trends). Checked with the pre-reform event-study coefficients.
- **Inference:** No conventional standard errors (few treated states). p-value: two-sided rank of β̂<sup>net</sup> among the P centred placebo estimates. 90% interval: β̂<sup>net</sup> minus the 95th and 5th percentiles of the centred placebos (Conley and Taber 2011). Smallest detectable effect: 2.8 × their standard deviation.

## Northern Territory container deposit scheme (2012)

`nt-container-deposits-2012` · evaluated 15 October 2026 · grade Not identified

Too few NT businesses make beverages or recover materials (12 in 2010-11) to measure entry or exit. Darwin soft-drink prices rose +8.7% relative to other capitals (p = 0.12), but they were already rising before the scheme; with each city's trend removed the change is +1.4%.

**Key insights**

- The question: did the Northern Territory's container deposit scheme (January 2012) change the number of drink makers and recyclers, or drink prices?
- Business numbers could not be measured: only 12 NT businesses were in the affected industries, too few for any change to show.
- Darwin soft-drink prices rose +8.7% relative to other capitals and beer +4.3%, but soft-drink prices were already rising before the scheme; taking out each city's earlier trend leaves +1.4%.
- These price data can only detect changes of about 19% or more, while a 10-cent deposit is a few per cent of a drink's price.
- Bottom line: the scheme's effect cannot be measured with these public data.

**What we did**

1. Took the treated industries (1211 Soft Drink, Cordial and Syrup Manufacturing, 1212 Beer Manufacturing, 2922 Waste Remediation and Materials Recovery Services) and the adopting states and dates from the register records; cohorts: NT from 2011-12 to 2016-17 against NSW, VIC, QLD, WA, TAS, ACT. Comparison states are those not yet treated in each cohort's window.
2. Built yearly entry and exit rates from ABS Counts of Australian Businesses (registered release vintage), 2007-08 on, pooling the treated classes in each state.
3. Drew placebo groups of the same number of classes from outside the treated division, matched on size (12 businesses in the treated states in 2010-11); 0 qualified.
4. Design stage with every treated outcome hidden: checked the feasibility rules (at least 100 treated businesses and 19 placebo groups) and the power, then committed the plan (docs/pap_high_evaluability.md).
5. Estimated the stacked difference-in-differences for the treated group and every placebo group, and subtracted the placebo mean.
6. Checked each pre-reform year against its 95% placebo band, and ran the registered robustness variants (the other ABS vintage, employing businesses only, leaving each state out).
7. Applied the plan's decision and grading rules, with Benjamini–Hochberg q-values across the batch.
8. Prices: the same estimator on each city's CPI class relative to its all-groups index, against placebo CPI classes, with a registered variant that removes each city's pre-reform linear trend.

**Econometric model**

Stacked difference-in-differences with clean comparison states, net of the same estimate for unaffected industries in the same states (a triple difference), with inference from placebo industries.

*For each cohort c (states adopting together), over its window*

> y<sub>s,t</sub> = α<sub>s</sub> + λ<sub>t</sub> + β<sub>c</sub> · D<sub>s,t</sub> + ε<sub>s,t</sub>,   s ∈ treated<sub>c</sub> ∪ comparison<sub>c</sub>

*Stacked across cohorts*

> β̂ = Σ<sub>c</sub> n<sub>c</sub> β̂<sub>c</sub> / Σ<sub>c</sub> n<sub>c</sub>

*Reported estimate: net of unaffected industries*

> β̂<sup>net</sup> = β̂ − (1/P) Σ<sub>p=1</sub><sup>P</sup> β̂<sub>p</sub>

*Prices (capital cities, quarterly; same estimator, net of other CPI classes)*

> y<sub>k,q</sub> = 100 × ln(P<sup>class</sup><sub>k,q</sub> / P<sup>all groups</sup><sub>k,q</sub>)

*Output and pay per worker (descriptive; net of other divisions)*

> y<sub>s,t</sub> = 100 × ln(GVA per worker<sub>s,t</sub>) for the treated industry's division

| Symbol | Meaning |
|---|---|
| y<sub>s,t</sub> | Entries (or exits) per 100 businesses operating at the start of financial year t in state s, for the treated ANZSIC classes pooled (1211 Soft Drink, Cordial and Syrup Manufacturing, 1212 Beer Manufacturing, 2922 Waste Remediation and Materials Recovery Services) |
| α<sub>s</sub>, λ<sub>t</sub> | State and year fixed effects |
| D<sub>s,t</sub> | 1 for an adopting state from its first exposed financial year on, else 0 |
| n<sub>c</sub> | Number of treated states in cohort c |
| β̂<sub>p</sub> | The same stacked estimate for placebo group p: classes outside the treated division, matched on size, in the same states and years |
| P | Number of placebo groups: 0 qualified on size |
| P<sup>class</sup><sub>k,q</sub> | CPI for the expenditure class in capital city k, quarter q |

- **Estimand:** The average change in the treated industries' entry (or exit) rate in the adopting states over the exposed years, relative to the comparison states, beyond the change for unaffected industries in the same states (NT).
- **Identifying assumption:** Without the reform, the treated industries' rate in the adopting states would have moved as in the comparison states once state-wide changes shared with unaffected industries are removed (triple-difference parallel trends). Checked with the pre-reform event-study coefficients.
- **Inference:** No conventional standard errors (few treated states). p-value: two-sided rank of β̂<sup>net</sup> among the P centred placebo estimates. 90% interval: β̂<sup>net</sup> minus the 95th and 5th percentiles of the centred placebos (Conley and Taber 2011). Smallest detectable effect: 2.8 × their standard deviation.

## Retail energy price deregulation (SA 2013, NSW 2014, south-east Queensland 2016)

`retail-energy-deregulation-2013-2016` · evaluated 15 October 2026 · grade Not identified

Business counts cannot measure this reform: the three states had 59 electricity retailers in the base year, each counted in its head-office state. Electricity prices in the deregulating states rose +17.0% relative to the regulated states (p = 0.01), but they had been rising faster for more than a decade before; with each city's trend removed the change is −0.6% (p = 0.86).

**Key insights**

- The question: did removing retail electricity price caps (SA 2013, NSW 2014, south-east Queensland 2016) bring in new retailers or lower prices?
- Business numbers could not be measured: the three states had 59 electricity retailers, each counted in its head-office state rather than where it sells.
- Electricity prices in the deregulating states rose +17.0% relative to states that kept price caps, but they had been rising faster for more than a decade before (mostly network charges); taking out each city's earlier trend leaves −0.6%, close to zero.
- Bottom line: no effect of deregulation can be identified in these data. Retailer margins or offer-level prices would be needed.

**What we did**

1. Took the treated industries (2640 On Selling Electricity and Electricity Market Operation) and the adopting states and dates from the register records; cohorts: SA from 2012-13 to 2017-18 against TAS, ACT, WA, NT; NSW from 2014-15 to 2017-18 against TAS, ACT, WA, NT; QLD from 2016-17 to 2017-18 against TAS, ACT, WA, NT. Comparison states are those not yet treated in each cohort's window.
2. Built yearly entry and exit rates from ABS Counts of Australian Businesses (registered release vintage), 2007-08 on, pooling the treated classes in each state.
3. Drew placebo groups of the same number of classes from outside the treated division, matched on size (59 businesses in the treated states in 2011-12); 54 qualified.
4. Design stage with every treated outcome hidden: checked the feasibility rules (at least 100 treated businesses and 19 placebo groups) and the power, then committed the plan (docs/pap_high_evaluability.md).
5. Estimated the stacked difference-in-differences for the treated group and every placebo group, and subtracted the placebo mean.
6. Checked each pre-reform year against its 95% placebo band, and ran the registered robustness variants (the other ABS vintage, employing businesses only, leaving each state out, adding 2018-19).
7. Applied the plan's decision and grading rules, with Benjamini–Hochberg q-values across the batch.
8. Prices: the same estimator on each city's CPI class relative to its all-groups index, against placebo CPI classes, with a registered variant that removes each city's pre-reform linear trend.

**Econometric model**

Stacked difference-in-differences with clean comparison states, net of the same estimate for unaffected industries in the same states (a triple difference), with inference from placebo industries.

*For each cohort c (states adopting together), over its window*

> y<sub>s,t</sub> = α<sub>s</sub> + λ<sub>t</sub> + β<sub>c</sub> · D<sub>s,t</sub> + ε<sub>s,t</sub>,   s ∈ treated<sub>c</sub> ∪ comparison<sub>c</sub>

*Stacked across cohorts*

> β̂ = Σ<sub>c</sub> n<sub>c</sub> β̂<sub>c</sub> / Σ<sub>c</sub> n<sub>c</sub>

*Reported estimate: net of unaffected industries*

> β̂<sup>net</sup> = β̂ − (1/P) Σ<sub>p=1</sub><sup>P</sup> β̂<sub>p</sub>

*Prices (capital cities, quarterly; same estimator, net of other CPI classes)*

> y<sub>k,q</sub> = 100 × ln(P<sup>class</sup><sub>k,q</sub> / P<sup>all groups</sup><sub>k,q</sub>)

*Output and pay per worker (descriptive; net of other divisions)*

> y<sub>s,t</sub> = 100 × ln(GVA per worker<sub>s,t</sub>) for the treated industry's division

| Symbol | Meaning |
|---|---|
| y<sub>s,t</sub> | Entries (or exits) per 100 businesses operating at the start of financial year t in state s, for the treated ANZSIC classes pooled (2640 On Selling Electricity and Electricity Market Operation) |
| α<sub>s</sub>, λ<sub>t</sub> | State and year fixed effects |
| D<sub>s,t</sub> | 1 for an adopting state from its first exposed financial year on, else 0 |
| n<sub>c</sub> | Number of treated states in cohort c |
| β̂<sub>p</sub> | The same stacked estimate for placebo group p: classes outside the treated division, matched on size, in the same states and years |
| P | Number of placebo groups: 54 qualified on size |
| P<sup>class</sup><sub>k,q</sub> | CPI for the expenditure class in capital city k, quarter q |

- **Estimand:** The average change in the treated industries' entry (or exit) rate in the adopting states over the exposed years, relative to the comparison states, beyond the change for unaffected industries in the same states (NSW, QLD, SA).
- **Identifying assumption:** Without the reform, the treated industries' rate in the adopting states would have moved as in the comparison states once state-wide changes shared with unaffected industries are removed (triple-difference parallel trends). Checked with the pre-reform event-study coefficients.
- **Inference:** No conventional standard errors (few treated states). p-value: two-sided rank of β̂<sup>net</sup> among the P centred placebo estimates. 90% interval: β̂<sup>net</sup> minus the 95th and 5th percentiles of the centred placebos (Conley and Taber 2011). Smallest detectable effect: 2.8 × their standard deviation.

## Ride-share legalisation (2015 to 2018)

`rideshare-legalisation-2015-2018` · evaluated 15 October 2026 · grade Not identified

Not identified. Taxi and road-transport entry in the legalising states was already far above the comparison states in the years before legalisation, so the comparison fails its pre-reform check. Ride-sharing also ran before it was legal, and drivers had to register for GST from August 2015 wherever it ran.

**Key insights**

- The question: did legalising ride-sharing (2015 to 2018) change how many taxi and road passenger businesses started or closed?
- The comparison: each group of states that legalised together against states that had not yet.
- What we found: no answer is possible. Openings in the legalising states were already far above the comparison states before legalisation, so the comparison fails its pre-reform check.
- Why: ride-sharing ran before it was legal in most cities, and every driver had to register for GST from August 2015, so the legal dates are not when the market changed.
- What it means: a different design is needed, such as the dates ride-sharing actually arrived in each city.

**What we did**

1. Took the treated industries (4623 Taxi and Other Road Transport) and the adopting states and dates from the register records; cohorts: ACT, NSW from 2015-16 to 2016-17 against VIC, NT, WA; SA, QLD, TAS in 2016-17 against VIC, NT, WA; VIC, NT in 2017-18 against WA. Comparison states are those not yet treated in each cohort's window.
2. Built yearly entry and exit rates from ABS Counts of Australian Businesses (registered release vintage), 2007-08 on, pooling the treated classes in each state.
3. Drew placebo groups of the same number of classes from outside the treated division, matched on size (14500 businesses in the treated states in 2014-15); 43 qualified.
4. Design stage with every treated outcome hidden: checked the feasibility rules (at least 100 treated businesses and 19 placebo groups) and the power, then committed the plan (docs/pap_high_evaluability.md).
5. Estimated the stacked difference-in-differences for the treated group and every placebo group, and subtracted the placebo mean.
6. Checked each pre-reform year against its 95% placebo band, and ran the registered robustness variants (the other ABS vintage, employing businesses only, leaving each state out).
7. Applied the plan's decision and grading rules, with Benjamini–Hochberg q-values across the batch.
8. Prices: the same estimator on each city's CPI class relative to its all-groups index, against placebo CPI classes, with a registered variant that removes each city's pre-reform linear trend.

**Econometric model**

Stacked difference-in-differences with clean comparison states, net of the same estimate for unaffected industries in the same states (a triple difference), with inference from placebo industries.

*For each cohort c (states adopting together), over its window*

> y<sub>s,t</sub> = α<sub>s</sub> + λ<sub>t</sub> + β<sub>c</sub> · D<sub>s,t</sub> + ε<sub>s,t</sub>,   s ∈ treated<sub>c</sub> ∪ comparison<sub>c</sub>

*Stacked across cohorts*

> β̂ = Σ<sub>c</sub> n<sub>c</sub> β̂<sub>c</sub> / Σ<sub>c</sub> n<sub>c</sub>

*Reported estimate: net of unaffected industries*

> β̂<sup>net</sup> = β̂ − (1/P) Σ<sub>p=1</sub><sup>P</sup> β̂<sub>p</sub>

*Prices (capital cities, quarterly; same estimator, net of other CPI classes)*

> y<sub>k,q</sub> = 100 × ln(P<sup>class</sup><sub>k,q</sub> / P<sup>all groups</sup><sub>k,q</sub>)

*Output and pay per worker (descriptive; net of other divisions)*

> y<sub>s,t</sub> = 100 × ln(GVA per worker<sub>s,t</sub>) for the treated industry's division

| Symbol | Meaning |
|---|---|
| y<sub>s,t</sub> | Entries (or exits) per 100 businesses operating at the start of financial year t in state s, for the treated ANZSIC classes pooled (4623 Taxi and Other Road Transport) |
| α<sub>s</sub>, λ<sub>t</sub> | State and year fixed effects |
| D<sub>s,t</sub> | 1 for an adopting state from its first exposed financial year on, else 0 |
| n<sub>c</sub> | Number of treated states in cohort c |
| β̂<sub>p</sub> | The same stacked estimate for placebo group p: classes outside the treated division, matched on size, in the same states and years |
| P | Number of placebo groups: 43 qualified on size, 43 with every year of the window |
| P<sup>class</sup><sub>k,q</sub> | CPI for the expenditure class in capital city k, quarter q |

- **Estimand:** The average change in the treated industries' entry (or exit) rate in the adopting states over the exposed years, relative to the comparison states, beyond the change for unaffected industries in the same states (ACT, NSW, NT, QLD, SA, TAS, VIC).
- **Identifying assumption:** Without the reform, the treated industries' rate in the adopting states would have moved as in the comparison states once state-wide changes shared with unaffected industries are removed (triple-difference parallel trends). Checked with the pre-reform event-study coefficients.
- **Inference:** No conventional standard errors (few treated states). p-value: two-sided rank of β̂<sup>net</sup> among the P centred placebo estimates. 90% interval: β̂<sup>net</sup> minus the 95th and 5th percentiles of the centred placebos (Conley and Taber 2011). Smallest detectable effect: 2.8 × their standard deviation.

## As-of-right taxi licences in Victoria (2014)

`vic-taxi-licensing-2014` · evaluated 15 October 2026 · grade Weak

In 2014-15, the first year of as-of-right taxi licences, entry into Victorian taxi and road transport changed by −1.4 per 100 relative to other states (90% interval −3.4 to +0.9); exits by −1.4. Neither is distinguishable from zero. Unlicensed UberX arrived in Melbourne the same year.

**Key insights**

- The question: did as-of-right taxi licences in Victoria (2014) change how many taxi and road transport businesses started or closed?
- The comparison: Victoria against all other states in 2014-15, the one year before ride-sharing and driver GST rules changed the market. Changes shared by every industry in the same states (a state's boom or slump) were removed by subtracting the same comparison for industries the reform did not touch.
- What we found: no detectable change. Openings moved −1.4 per 100 businesses (90% interval −3.4 to +0.9) and closures −1.4 (−3.6 to +0.8).
- How precise: a rise in openings of more than about 0.9 per 100 is ruled out.
- What it means: graded Weak. Unlicensed UberX arrived in Melbourne in the same year, and only one year can be used.

**What we did**

1. Took the treated industries (4623 Taxi and Other Road Transport) and the adopting states and dates from the register records; cohorts: VIC in 2014-15 against NSW, QLD, SA, WA, TAS, ACT, NT. Comparison states are those not yet treated in each cohort's window.
2. Built yearly entry and exit rates from ABS Counts of Australian Businesses (registered release vintage), 2007-08 on, pooling the treated classes in each state.
3. Drew placebo groups of the same number of classes from outside the treated division, matched on size (3931 businesses in the treated states in 2013-14); 43 qualified.
4. Design stage with every treated outcome hidden: checked the feasibility rules (at least 100 treated businesses and 19 placebo groups) and the power, then committed the plan (docs/pap_high_evaluability.md).
5. Estimated the stacked difference-in-differences for the treated group and every placebo group, and subtracted the placebo mean.
6. Checked each pre-reform year against its 95% placebo band, and ran the registered robustness variants (the other ABS vintage, employing businesses only, leaving each state out).
7. Applied the plan's decision and grading rules, with Benjamini–Hochberg q-values across the batch.
8. Prices: the same estimator on each city's CPI class relative to its all-groups index, against placebo CPI classes, with a registered variant that removes each city's pre-reform linear trend.

**Econometric model**

Stacked difference-in-differences with clean comparison states, net of the same estimate for unaffected industries in the same states (a triple difference), with inference from placebo industries.

*For each cohort c (states adopting together), over its window*

> y<sub>s,t</sub> = α<sub>s</sub> + λ<sub>t</sub> + β<sub>c</sub> · D<sub>s,t</sub> + ε<sub>s,t</sub>,   s ∈ treated<sub>c</sub> ∪ comparison<sub>c</sub>

*Stacked across cohorts*

> β̂ = Σ<sub>c</sub> n<sub>c</sub> β̂<sub>c</sub> / Σ<sub>c</sub> n<sub>c</sub>

*Reported estimate: net of unaffected industries*

> β̂<sup>net</sup> = β̂ − (1/P) Σ<sub>p=1</sub><sup>P</sup> β̂<sub>p</sub>

*Prices (capital cities, quarterly; same estimator, net of other CPI classes)*

> y<sub>k,q</sub> = 100 × ln(P<sup>class</sup><sub>k,q</sub> / P<sup>all groups</sup><sub>k,q</sub>)

*Output and pay per worker (descriptive; net of other divisions)*

> y<sub>s,t</sub> = 100 × ln(GVA per worker<sub>s,t</sub>) for the treated industry's division

| Symbol | Meaning |
|---|---|
| y<sub>s,t</sub> | Entries (or exits) per 100 businesses operating at the start of financial year t in state s, for the treated ANZSIC classes pooled (4623 Taxi and Other Road Transport) |
| α<sub>s</sub>, λ<sub>t</sub> | State and year fixed effects |
| D<sub>s,t</sub> | 1 for an adopting state from its first exposed financial year on, else 0 |
| n<sub>c</sub> | Number of treated states in cohort c |
| β̂<sub>p</sub> | The same stacked estimate for placebo group p: classes outside the treated division, matched on size, in the same states and years |
| P | Number of placebo groups: 43 qualified on size, 43 with every year of the window |
| P<sup>class</sup><sub>k,q</sub> | CPI for the expenditure class in capital city k, quarter q |

- **Estimand:** The average change in the treated industries' entry (or exit) rate in the adopting states over the exposed years, relative to the comparison states, beyond the change for unaffected industries in the same states (VIC).
- **Identifying assumption:** Without the reform, the treated industries' rate in the adopting states would have moved as in the comparison states once state-wide changes shared with unaffected industries are removed (triple-difference parallel trends). Checked with the pre-reform event-study coefficients.
- **Inference:** No conventional standard errors (few treated states). p-value: two-sided rank of β̂<sup>net</sup> among the P centred placebo estimates. 90% interval: β̂<sup>net</sup> minus the 95th and 5th percentiles of the centred placebos (Conley and Taber 2011). Smallest detectable effect: 2.8 × their standard deviation.

## Perth retail trading-hours deregulation (2010 and 2012)

`wa-trading-hours-2010-2012` · evaluated 15 October 2026 · grade Moderate

Perth's move to 9pm weeknight trading (November 2010) and Sunday trading (August 2012) had no detectable effect on how many general retail businesses started or closed. Entry changed by +0.8 per 100 businesses a year (90% interval −2.4 to +3.7), exit by −0.1 (−2.4 to +2.5).

**Key insights**

- The question: did letting Perth's general retail shops trade until 9pm on weeknights (November 2010) and on Sundays (August 2012) change how many supermarkets, clothing and department stores started or closed?
- The comparison: WA against six other states and territories, 2007-08 to 2017-18. Anything that moved all WA industries together, such as the mining boom, was removed by subtracting the same comparison for 472 groups of industries the reform did not touch.
- What we found: no detectable change. Business openings moved +0.8 per 100 businesses a year (90% interval −2.4 to +3.7) and closures −0.1 (−2.4 to +2.5).
- How precise: only changes larger than about 5.6 openings per 100 businesses a year could have been detected. Food prices in Perth fell relative to other capitals, but they were already falling before the reform.
- What it means: no sign that longer hours brought in or pushed out shops in large numbers. Counts cannot show whether sales shifted from small shops to large chains; the follow-up evaluation of the weeknight step with new data agrees.

**What we did**

1. Took the reform dates from the WA register and the treated classes from the register records.
2. Built yearly entry and exit rates from ABS Counts of Australian Businesses, stitched from successive releases, 2007-08 to 2017-18 (before COVID); SA left out because Adelaide changed its hours in 2012.
3. Ran a design-stage review with WA's post-reform outcomes hidden, chose the estimator and placebo pool, measured power, and committed the plan (docs/pap_wa_trading_hours.md).
4. Estimated the WA-versus-comparison difference-in-differences for general retail and for 472 placebo groups, and subtracted the placebo mean.
5. Estimated the year-by-year path and its sensitivity to departures from parallel trends.
6. Ran the registered robustness checks: the other ABS vintage, adding 2018-19, leaving out comparison states, a broader treated set, a consumer-facing placebo pool, and a triple difference against cafes, takeaway food and fuel retailing.
7. Prices: Perth's food CPI relative to its all-groups CPI against other capitals; a check that removes each city's pre-reform trend was added after unblinding and is labelled as such.

**Econometric model**

Difference-in-differences with one treated state and state and year fixed effects, net of the same estimate for placebo industry groups in the same states (a triple difference). Inference from the placebo distribution.

*Treated industries, WA against comparison states*

> y<sub>s,t</sub> = α<sub>s</sub> + λ<sub>t</sub> + δ<sub>T</sub> · D<sub>s,t</sub> + ε<sub>s,t</sub>

*Reported estimate: net of unaffected WA industries*

> δ̂ = δ̂<sub>T</sub> − (1/P) Σ<sub>p=1</sub><sup>P</sup> δ̂<sub>p</sub>

*Year by year (event study)*

> y<sub>s,t</sub> = α<sub>s</sub> + λ<sub>t</sub> + Σ<sub>k≠−1</sub> θ<sub>k</sub> · 1[s = WA, t − 2010-11 = k] + ε<sub>s,t</sub>

*Food prices (capital cities, quarterly)*

> 100 × ln(P<sup>food</sup><sub>k,q</sub> / P<sup>all</sup><sub>k,q</sub>) = α<sub>k</sub> + λ<sub>q</sub> + δ · D<sub>k,q</sub> + ε<sub>k,q</sub>

| Symbol | Meaning |
|---|---|
| y<sub>s,t</sub> | Entries (or exits) per 100 businesses at the start of financial year t in state s, classes 4110 Supermarket and Grocery Stores, 4251 Clothing Retailing and 4260 Department Stores pooled |
| α<sub>s</sub>, λ<sub>t</sub> | State and year fixed effects |
| D<sub>s,t</sub> | 1 for WA from 2010-11 (the first year with weeknight trading) on |
| δ̂<sub>p</sub> | The same estimate for placebo group p: three ANZSIC classes outside retail with a WA size between half and twice the treated group's |
| P | Number of placebo groups (472) |
| θ<sub>k</sub> | Effect k years from 2010-11, relative to 2009-10 |
| P<sup>food</sup><sub>k,q</sub> | CPI for food and non-alcoholic beverages in city k, quarter q |

- **Estimand:** The average change in the entry (or exit) rate of WA general retail after the reforms, relative to the same industries in comparison states, beyond the change for unaffected WA industries.
- **Identifying assumption:** Without the reforms, WA general retail would have moved like general retail in the comparison states once WA-wide changes shared with other industries are removed. Three pre-reform years allow only a weak check; sensitivity bounds (relative magnitudes) show how large a departure would overturn the sign.
- **Inference:** No conventional standard errors (one treated state). p-value: two-sided rank among the centred placebo-group estimates; 90% interval from their quantiles (Conley and Taber 2011); smallest detectable effect 2.8 × their standard deviation. A comparison-state placebo rank is also reported (smallest possible p 0.14).

## National Quality Framework for childcare (2012): re-evaluation with synthetic DiD

`childcare-nqf-2012-phase5` · evaluated 18 October 2026 · grade Moderate

No detectable effect: business entry rate −0.3 per 100 businesses a year (p = 0.85), synthetic DiD, grade Moderate.

**Key insights**

- The question: did the National Quality Framework for childcare change how many childcare businesses opened or closed in its first year (2011-12)?
- The comparison: The framework started in January 2012 everywhere except WA (August 2012): 2011-12 childcare entry and exit in the seven early jurisdictions against WA, with synthetic DiD weights.
- What we found: no detectable change. Business entry rate: −0.3 per 100 businesses a year (90% interval −2.3 to +2.4; p = 0.85).
- Other outcomes: business exit rate −1.9 (p = 0.049); child care: prices relative to the CPI +4.4 (p = 0.075). Secondary outcomes are outside the registered decision rule and not adjusted for testing several outcomes, so a p-value below 0.05 among them is a lead, not a finding.
- How precise: only changes larger than about 6.0 per 100 businesses a year could have been detected.
- Compared with the earlier evaluation (2026-10-15, now archived): it found no detectable effect (business entry rate −0.3 per 100 businesses a year). The conclusion is unchanged; the smallest detectable effect is now 6.0, down from 9.8. This evaluation uses the estimator chosen in the blinded power study and the latest data.
- What it means: no effect is detectable with public state-level data; an effect smaller than the detectable size cannot be ruled out.

**What we did**

1. Registered the layer, outcomes, windows and placebo pools in the specification before any treated post-reform outcome was computed.
2. Design stage: hid treated cells from first exposure, computed every layer's placebo distribution, the own-class placebos and the pre-reform event-study check.
3. Committed the design and plan, ran a blinded dry run, then one registered run with treated cells restored.
4. Judged the registered layer's estimate against its placebo distribution; reported every other layer side by side.

**Econometric model**

Synthetic DiD on ANZSIC classes by state and financial year, the layer chosen for this reform in the blinded power study, with every other layer reported side by side.

*Synthetic DiD*

> τ̂ = arg min over (μ, α, β, τ) of Σ<sub>i,t</sub> (y<sub>it</sub> − μ − α<sub>i</sub> − β<sub>t</sub> − D<sub>it</sub>·τ)<sup>2</sup> · ω̂<sub>i</sub> · λ̂<sub>t</sub>

*Year by year*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + Σ<sub>k≠−1</sub> β<sub>k</sub>·1[t − T<sub>s</sub> = k]·T<sub>cs</sub> + ε<sub>cst</sub>

| Symbol | Meaning |
|---|---|
| y<sub>cst</sub> | Entries (or exits) per 100 businesses operating at the start of year t, class c, state s |
| D<sub>cst</sub> | 1 for the reform's class in a treated state (or city) from its first exposed period to the end of its window |
| ω̂<sub>i</sub> | weights on comparison cells, chosen so their pre-reform path matches the treated group's |
| λ̂<sub>t</sub> | weights on pre-reform periods, chosen to resemble the post-reform periods |

- **Estimand:** The average change in the outcome for the reform's classes in treated states over the window, beyond the same classes elsewhere and the treated states' other classes, net of the mean placebo estimate.
- **Identifying assumption:** Without the reform, the treated classes in treated states would have moved like the same classes elsewhere plus their states' other classes (parallel trends in the saturated model; for synthetic DiD, like the weighted comparison cells).
- **Inference:** The same estimator applied to up to 40 placebo industry groups (or CPI classes) at the reform's states and dates gives the no-effect distribution: the p-value is the share of centred placebo estimates at least as large; the 90% interval subtracts their 5th and 95th percentiles. Benjamini-Hochberg q-values across the specification's primary outcomes. Placebo states and fake dates check the reform's own classes.

## National Quality Framework for childcare (2012): WA's seven-month delay, monthly data

`childcare-nqf-wa-delay-2012` · evaluated 18 October 2026 · grade Moderate

WA's seven-month delay in adopting the National Quality Framework shows no detectable early effect. Childcare's share of business exits moved +0.35 percentage points (90% interval −0.87 to +1.12) on a base of 1.5%, and child care prices +0.3% (−2.9 to +5.6) relative to other prices. Only large effects could have been detected.

**Key insights**

- The question: did the National Quality Framework for childcare (staff ratios, qualifications, quality ratings) push childcare businesses out or raise prices soon after it started?
- The natural experiment: every other jurisdiction started in January 2012, but WA only in August 2012. If the framework mattered straight away, the gap between WA and the rest should open in January and close again in August.
- What we found: no detectable early effect. Childcare's share of business closures moved +0.35 percentage points (90% interval −0.87 to +1.12) on a base of 1.5%, and child care prices +0.3% (−2.9 to +5.6).
- How precise: only very large effects could have been seen: about 1.9 points on closures (roughly a doubling of childcare's share) or about 8% on prices.
- What it means: no sign of an immediate shake-out or price jump. The later staff ratio and qualification phases (2014, 2016) are not covered, and Department of Education data on services and fees would allow a sharper test.

**What we did**

1. Built monthly counts of ABN cancellations and registrations by industry inferred from business names (childcare rule checked on City of Melbourne names), quarterly CPI by capital and Labour Force employment and hours.
2. Design-stage review with WA's childcare outcomes from January 2012 hidden in code; chose the windows, placebo pools and outcome roles, and committed the plan (docs/pap_childcare_nqf_wa.md).
3. Ran a blinded dry run that reproduced the design-stage no-effect distributions, then one unblinded run.
4. Estimated the pooled, early and late effects, the after-against-before check and detrended variants for each outcome.
5. Applied the plan's findings, verdict and grading rules. A check dropping one outlying month (December 2010) was added after unblinding and is labelled as such.

**Econometric model**

On-off difference-in-differences for a rule that starts late in one jurisdiction: the gap between the late adopter and the rest is compared across three windows (before, others only, all). Inference from placebo industries and fake dates.

*The gap, each month (or quarter)*

> G<sub>t</sub> = y<sup>WA</sup><sub>t</sub> − ȳ<sup>others</sup><sub>t</sub> − s̄<sub>season(t)</sub>

*Pooled effect (primary)*

> δ̂ = mean<sub>t ∈ pre ∪ off</sub>(G<sub>t</sub>) − mean<sub>t ∈ on</sub>(G<sub>t</sub>)

*Early effect and late effect (secondary)*

> δ̂<sub>early</sub> = mean<sub>pre</sub>(G<sub>t</sub>) − mean<sub>on</sub>(G<sub>t</sub>);   δ̂<sub>late</sub> = mean<sub>off</sub>(G<sub>t</sub>) − mean<sub>on</sub>(G<sub>t</sub>)

| Symbol | Meaning |
|---|---|
| y<sub>t</sub> | Exits: childcare-named businesses' share of named-business ABN cancellations (%), monthly. Prices: 100 × ln(child care CPI / all-groups CPI), quarterly, Perth against the mean of the other capitals |
| ȳ<sup>others</sup><sub>t</sub> | The other seven jurisdictions pooled |
| s̄<sub>season(t)</sub> | The gap's pre-period mean for the same month or quarter of the year |
| pre | January 2009 to December 2011; quarterly outcomes 2009-Q1 to 2011-Q4 (no one treated) |
| on | January to July 2012; quarterly 2012-Q1 and Q2 (all but WA treated) |
| off | August 2012 to July 2013; quarterly 2012-Q3 to 2013-Q2 (all treated) |

- **Estimand:** The framework's immediate effect on the outcome, measured by how the WA-minus-others gap moves when the others adopt (on) relative to when nobody (pre) or everybody (off) has it. The early part needs only parallel trends; the pooled estimate also assumes the effect is immediate and lasting.
- **Identifying assumption:** Without the framework, the WA-minus-others gap would have kept its usual seasonal pattern through 2012-13. The on-off pattern guards against a WA-specific shock, which would not switch off in August 2012.
- **Inference:** No conventional standard errors (one late jurisdiction). No-effect distribution: the same estimator for 32 named industries over the same windows plus childcare at 8 fake dates two or more years earlier (exits). p-value: two-sided rank; 90% interval: estimate minus the 95th and 5th percentiles (Conley and Taber 2011); smallest detectable effect: 2.8 × standard deviation; Benjamini–Hochberg q-values across the two primaries.

## Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023)

`e-conveyancing-2018-2023` · evaluated 18 October 2026 · grade Weak

No detectable effect: business entry rate −0.6 per 100 businesses a year (p = 0.54), saturated fixed effects, grade Weak.

**Key insights**

- The question: did requiring property settlements to be lodged electronically (NSW 2018 to Queensland 2023) change how many legal and conveyancing practices opened or closed?
- The comparison: Staggered: legal services entry and exit in each mandating state against the ACT, Tasmania and the NT (never mandated) and Queensland until 2022-23, with class x year and state x year effects.
- What we found: no detectable change. Business entry rate: −0.6 per 100 businesses a year (90% interval −2.3 to +0.6; p = 0.54).
- The estimators disagree: synthetic DiD gives −3.0, outside the registered layer's 90% interval, so the grade is Weak.
- Other outcomes: business exit rate +0.0 (p = 0.88).
- How precise: only changes larger than about 2.9 per 100 businesses a year could have been detected.
- What it means: no effect is detectable with public state-level data; an effect smaller than the detectable size cannot be ruled out.

**What we did**

1. Registered the layer, outcomes, windows and placebo pools in the specification before any treated post-reform outcome was computed.
2. Design stage: hid treated cells from first exposure, computed every layer's placebo distribution, the own-class placebos and the pre-reform event-study check.
3. Committed the design and plan, ran a blinded dry run, then one registered run with treated cells restored.
4. Judged the registered layer's estimate against its placebo distribution; reported every other layer side by side.

**Econometric model**

Saturated fixed effects on ANZSIC classes by state and financial year, the layer chosen for this reform in the blinded power study, with every other layer reported side by side.

*Saturated fixed effects*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + β·D<sub>cst</sub> + ε<sub>cst</sub>

*Year by year*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + Σ<sub>k≠−1</sub> β<sub>k</sub>·1[t − T<sub>s</sub> = k]·T<sub>cs</sub> + ε<sub>cst</sub>

| Symbol | Meaning |
|---|---|
| y<sub>cst</sub> | Entries (or exits) per 100 businesses operating at the start of year t, class c, state s |
| D<sub>cst</sub> | 1 for the reform's class in a treated state (or city) from its first exposed period to the end of its window |
| α<sub>cs</sub> | a level for each class in each state |
| δ<sub>ct</sub> | each class's national movement in each period (industry cycles, product-wide price swings) |
| γ<sub>st</sub> | each state's movement in each period (state booms and slumps) |

- **Estimand:** The average change in the outcome for the reform's classes in treated states over the window, beyond the same classes elsewhere and the treated states' other classes, net of the mean placebo estimate.
- **Identifying assumption:** Without the reform, the treated classes in treated states would have moved like the same classes elsewhere plus their states' other classes (parallel trends in the saturated model; for synthetic DiD, like the weighted comparison cells).
- **Inference:** The same estimator applied to up to 40 placebo industry groups (or CPI classes) at the reform's states and dates gives the no-effect distribution: the p-value is the share of centred placebo estimates at least as large; the 90% interval subtracts their 5th and 95th percentiles. Benjamini-Hochberg q-values across the specification's primary outcomes. Placebo states and fake dates check the reform's own classes.

## Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021)

`fuel-price-reporting-2016-2021` · evaluated 18 October 2026 · grade Weak

No detectable effect: automotive fuel: prices relative to the CPI −2.8% (log points) (p = 0.20), saturated fixed effects, grade Weak.

**Key insights**

- The question: did making fuel retailers report their prices in real time for publication (NSW 2016, NT 2017, Queensland 2018, Tasmania 2020, SA 2021) change fuel prices, or the number of fuel retailers?
- The comparison: Staggered: each state's capital-city fuel price relative to the CPI against capitals not yet reporting (Melbourne and Canberra throughout; Hobart and Adelaide until they adopted), with class x quarter and city x quarter effects; fuel retailers' entry and exit the same way. WA, always reporting, is left out.
- What we found: no detectable change. Automotive fuel: prices relative to the CPI: −2.8% relative to other prices (90% interval −7.3 to +0.4; p = 0.20).
- The estimators disagree: synthetic DiD gives +4.8, outside the registered layer's 90% interval, so the grade is Weak.
- Other outcomes: business entry rate −0.2 (p = 0.85; not identified: a pre-reform year lies outside its placebo band); business exit rate −1.0 (p = 0.15).
- How precise: only changes larger than about 6.7% relative to other prices could have been detected.
- What it means: no effect is detectable with public state-level data; an effect smaller than the detectable size cannot be ruled out.

**What we did**

1. Registered the layer, outcomes, windows and placebo pools in the specification before any treated post-reform outcome was computed.
2. Design stage: hid treated cells from first exposure, computed every layer's placebo distribution, the own-class placebos and the pre-reform event-study check.
3. Committed the design and plan, ran a blinded dry run, then one registered run with treated cells restored.
4. Judged the registered layer's estimate against its placebo distribution; reported every other layer side by side.

**Econometric model**

Saturated fixed effects on CPI classes by capital city and quarter, the layer chosen for this reform in the blinded power study, with every other layer reported side by side.

*Saturated fixed effects*

> y<sub>cjq</sub> = α<sub>cj</sub> + δ<sub>cq</sub> + γ<sub>jq</sub> + β·D<sub>cjq</sub> + ε<sub>cjq</sub>

*Year by year*

> y<sub>cjq</sub> = α<sub>cj</sub> + δ<sub>cq</sub> + γ<sub>jq</sub> + Σ<sub>k≠−1</sub> β<sub>k</sub>·1[q − T<sub>j</sub> = k]·T<sub>cj</sub> + ε<sub>cjq</sub>

| Symbol | Meaning |
|---|---|
| y<sub>cjq</sub> | 100 × log of the CPI class relative to All groups in city j, quarter q |
| D<sub>cjq</sub> | 1 for the reform's class in a treated state (or city) from its first exposed period to the end of its window |
| α<sub>cj</sub> | a level for each class in each state |
| δ<sub>cq</sub> | each class's national movement in each period (industry cycles, product-wide price swings) |
| γ<sub>jq</sub> | each state's movement in each period (state booms and slumps) |

- **Estimand:** The average change in the outcome for the reform's classes in treated states over the window, beyond the same classes elsewhere and the treated states' other classes, net of the mean placebo estimate.
- **Identifying assumption:** Without the reform, the treated classes in treated states would have moved like the same classes elsewhere plus their states' other classes (parallel trends in the saturated model; for synthetic DiD, like the weighted comparison cells).
- **Inference:** The same estimator applied to up to 40 placebo industry groups (or CPI classes) at the reform's states and dates gives the no-effect distribution: the p-value is the share of centred placebo estimates at least as large; the 90% interval subtracts their 5th and 95th percentiles. Benjamini-Hochberg q-values across the specification's primary outcomes. Placebo states and fake dates check the reform's own classes.

## Heavy Vehicle National Law (2014): re-evaluation with saturated effects

`heavy-vehicle-national-law-2014-phase5` · evaluated 18 October 2026 · grade Moderate

No detectable effect: business entry rate +0.3 per 100 businesses a year (p = 0.85), saturated fixed effects, grade Moderate.

**Key insights**

- The question: did one national law for heavy vehicles (February 2014) change how many road freight businesses started or closed?
- The comparison: Road freight in the six adopting jurisdictions against WA and the NT, 2013-14 to 2017-18, with class x year and state x year effects.
- What we found: no detectable change. Business entry rate: +0.3 per 100 businesses a year (90% interval −1.7 to +2.8; p = 0.85).
- Other outcomes: business exit rate −0.7 (p = 0.59).
- How precise: only changes larger than about 4.4 per 100 businesses a year could have been detected.
- Compared with the earlier evaluation (2026-10-15, now archived): it found no detectable effect (business entry rate −2.2 per 100 businesses a year). The conclusion is unchanged; the smallest detectable effect is now 4.4, down from 9.4. This evaluation uses the estimator chosen in the blinded power study and the latest data.
- What it means: no effect is detectable with public state-level data; an effect smaller than the detectable size cannot be ruled out.

**What we did**

1. Registered the layer, outcomes, windows and placebo pools in the specification before any treated post-reform outcome was computed.
2. Design stage: hid treated cells from first exposure, computed every layer's placebo distribution, the own-class placebos and the pre-reform event-study check.
3. Committed the design and plan, ran a blinded dry run, then one registered run with treated cells restored.
4. Judged the registered layer's estimate against its placebo distribution; reported every other layer side by side.

**Econometric model**

Saturated fixed effects on ANZSIC classes by state and financial year, the layer chosen for this reform in the blinded power study, with every other layer reported side by side.

*Saturated fixed effects*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + β·D<sub>cst</sub> + ε<sub>cst</sub>

*Year by year*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + Σ<sub>k≠−1</sub> β<sub>k</sub>·1[t − T<sub>s</sub> = k]·T<sub>cs</sub> + ε<sub>cst</sub>

| Symbol | Meaning |
|---|---|
| y<sub>cst</sub> | Entries (or exits) per 100 businesses operating at the start of year t, class c, state s |
| D<sub>cst</sub> | 1 for the reform's class in a treated state (or city) from its first exposed period to the end of its window |
| α<sub>cs</sub> | a level for each class in each state |
| δ<sub>ct</sub> | each class's national movement in each period (industry cycles, product-wide price swings) |
| γ<sub>st</sub> | each state's movement in each period (state booms and slumps) |

- **Estimand:** The average change in the outcome for the reform's classes in treated states over the window, beyond the same classes elsewhere and the treated states' other classes, net of the mean placebo estimate.
- **Identifying assumption:** Without the reform, the treated classes in treated states would have moved like the same classes elsewhere plus their states' other classes (parallel trends in the saturated model; for synthetic DiD, like the weighted comparison cells).
- **Inference:** The same estimator applied to up to 40 placebo industry groups (or CPI classes) at the reform's states and dates gives the no-effect distribution: the p-value is the share of centred placebo estimates at least as large; the 90% interval subtracts their 5th and 95th percentiles. Benjamini-Hochberg q-values across the specification's primary outcomes. Placebo states and fake dates check the reform's own classes.

## Legal Profession Uniform Law (2015): re-evaluation with saturated effects

`legal-profession-uniform-law-2015-phase5` · evaluated 18 October 2026 · grade Moderate

No detectable effect: business entry rate −1.3 per 100 businesses a year (p = 0.47), saturated fixed effects, grade Moderate.

**Key insights**

- The question: did the Legal Profession Uniform Law (NSW and Victoria, July 2015) change how many legal practices opened or closed?
- The comparison: Legal services in NSW and Victoria against the other jurisdictions, 2015-16 to 2017-18, with class x year and state x year effects.
- What we found: no detectable change. Business entry rate: −1.3 per 100 businesses a year (90% interval −4.3 to +0.8; p = 0.47).
- Other outcomes: business exit rate −0.4 (p = 0.45).
- How precise: only changes larger than about 4.5 per 100 businesses a year could have been detected.
- Compared with the earlier evaluation (2026-10-15, now archived): it found no detectable effect (business entry rate −1.6 per 100 businesses a year). The conclusion is unchanged; the smallest detectable effect is now 4.5, down from 7.0. This evaluation uses the estimator chosen in the blinded power study and the latest data.
- What it means: no effect is detectable with public state-level data; an effect smaller than the detectable size cannot be ruled out.

**What we did**

1. Registered the layer, outcomes, windows and placebo pools in the specification before any treated post-reform outcome was computed.
2. Design stage: hid treated cells from first exposure, computed every layer's placebo distribution, the own-class placebos and the pre-reform event-study check.
3. Committed the design and plan, ran a blinded dry run, then one registered run with treated cells restored.
4. Judged the registered layer's estimate against its placebo distribution; reported every other layer side by side.

**Econometric model**

Saturated fixed effects on ANZSIC classes by state and financial year, the layer chosen for this reform in the blinded power study, with every other layer reported side by side.

*Saturated fixed effects*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + β·D<sub>cst</sub> + ε<sub>cst</sub>

*Year by year*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + Σ<sub>k≠−1</sub> β<sub>k</sub>·1[t − T<sub>s</sub> = k]·T<sub>cs</sub> + ε<sub>cst</sub>

| Symbol | Meaning |
|---|---|
| y<sub>cst</sub> | Entries (or exits) per 100 businesses operating at the start of year t, class c, state s |
| D<sub>cst</sub> | 1 for the reform's class in a treated state (or city) from its first exposed period to the end of its window |
| α<sub>cs</sub> | a level for each class in each state |
| δ<sub>ct</sub> | each class's national movement in each period (industry cycles, product-wide price swings) |
| γ<sub>st</sub> | each state's movement in each period (state booms and slumps) |

- **Estimand:** The average change in the outcome for the reform's classes in treated states over the window, beyond the same classes elsewhere and the treated states' other classes, net of the mean placebo estimate.
- **Identifying assumption:** Without the reform, the treated classes in treated states would have moved like the same classes elsewhere plus their states' other classes (parallel trends in the saturated model; for synthetic DiD, like the weighted comparison cells).
- **Inference:** The same estimator applied to up to 40 placebo industry groups (or CPI classes) at the reform's states and dates gives the no-effect distribution: the p-value is the share of centred placebo estimates at least as large; the 90% interval subtracts their 5th and 95th percentiles. Benjamini-Hochberg q-values across the specification's primary outcomes. Placebo states and fake dates check the reform's own classes.

## Northern Territory container deposit scheme (2012): re-evaluation with drink prices

`nt-container-deposits-2012-phase5` · evaluated 18 October 2026 · grade Not identified

Not identified: waters, soft drinks and juices: prices relative to the CPI +7.6% (log points) (p = 0.20), saturated fixed effects.

**Key insights**

- The question: did the Northern Territory's container deposit scheme (January 2012) change drink prices in Darwin?
- The comparison: Darwin drink prices relative to the CPI against the capitals of states without a scheme (Adelaide excluded), 2012-Q1 to 2017-Q3, with class x quarter and city x quarter effects. Business counts are too few to use.
- What we found: the effect cannot be identified: a pre-reform year of the primary outcome lies outside its 95% placebo band, so the treated group was already moving apart before the reform. The registered layer's estimate (+7.6% relative to other prices) is not an effect.
- Other outcomes: beer: prices relative to the CPI +4.8 (p = 0.44).
- How precise: only changes larger than about 22.0% relative to other prices could have been detected.
- Compared with the earlier evaluation (2026-10-15, now archived): it found that the effect could not be identified (waters, soft drinks and juices: prices relative to the CPI +8.7% (log points)). The conclusion is unchanged. This evaluation uses the estimator chosen in the blinded power study and the latest data.
- What it means: these data cannot separate the reform from what was already happening.

**What we did**

1. Registered the layer, outcomes, windows and placebo pools in the specification before any treated post-reform outcome was computed.
2. Design stage: hid treated cells from first exposure, computed every layer's placebo distribution, the own-class placebos and the pre-reform event-study check.
3. Committed the design and plan, ran a blinded dry run, then one registered run with treated cells restored.
4. Judged the registered layer's estimate against its placebo distribution; reported every other layer side by side.

**Econometric model**

Saturated fixed effects on CPI classes by capital city and quarter, the layer chosen for this reform in the blinded power study, with every other layer reported side by side.

*Saturated fixed effects*

> y<sub>cjq</sub> = α<sub>cj</sub> + δ<sub>cq</sub> + γ<sub>jq</sub> + β·D<sub>cjq</sub> + ε<sub>cjq</sub>

*Year by year*

> y<sub>cjq</sub> = α<sub>cj</sub> + δ<sub>cq</sub> + γ<sub>jq</sub> + Σ<sub>k≠−1</sub> β<sub>k</sub>·1[q − T<sub>j</sub> = k]·T<sub>cj</sub> + ε<sub>cjq</sub>

| Symbol | Meaning |
|---|---|
| y<sub>cjq</sub> | 100 × log of the CPI class relative to All groups in city j, quarter q |
| D<sub>cjq</sub> | 1 for the reform's class in a treated state (or city) from its first exposed period to the end of its window |
| α<sub>cj</sub> | a level for each class in each state |
| δ<sub>cq</sub> | each class's national movement in each period (industry cycles, product-wide price swings) |
| γ<sub>jq</sub> | each state's movement in each period (state booms and slumps) |

- **Estimand:** The average change in the outcome for the reform's classes in treated states over the window, beyond the same classes elsewhere and the treated states' other classes, net of the mean placebo estimate.
- **Identifying assumption:** Without the reform, the treated classes in treated states would have moved like the same classes elsewhere plus their states' other classes (parallel trends in the saturated model; for synthetic DiD, like the weighted comparison cells).
- **Inference:** The same estimator applied to up to 40 placebo industry groups (or CPI classes) at the reform's states and dates gives the no-effect distribution: the p-value is the share of centred placebo estimates at least as large; the 90% interval subtracts their 5th and 95th percentiles. Benjamini-Hochberg q-values across the specification's primary outcomes. Placebo states and fake dates check the reform's own classes.

## Retail energy price deregulation (SA 2013, NSW 2014, SEQ 2016): re-evaluation with electricity prices

`retail-energy-deregulation-2013-2016-phase5` · evaluated 18 October 2026 · grade Not identified

Not identified: electricity: prices relative to the CPI +9.4% (log points) (p = 0.024), saturated fixed effects.

**Key insights**

- The question: did removing retail electricity price caps (SA 2013, NSW 2014, south-east Queensland 2016) lower electricity prices?
- The comparison: Electricity prices relative to the CPI in each deregulating capital against capitals whose prices stayed regulated (Hobart, Canberra, Perth, Darwin), with class x quarter and city x quarter effects. Retailer counts are too few to use.
- What we found: the effect cannot be identified: a pre-reform year of the primary outcome lies outside its 95% placebo band, so the treated group was already moving apart before the reform. The registered layer's estimate (+9.4% relative to other prices) is not an effect.
- How precise: only changes larger than about 9.1% relative to other prices could have been detected.
- Compared with the earlier evaluation (2026-10-15, now archived): it found that the effect could not be identified (electricity: prices relative to the CPI +17.0% (log points)). The conclusion is unchanged; the smallest detectable effect is now 9.1, down from 9.5. This evaluation uses the estimator chosen in the blinded power study and the latest data.
- What it means: these data cannot separate the reform from what was already happening.

**What we did**

1. Registered the layer, outcomes, windows and placebo pools in the specification before any treated post-reform outcome was computed.
2. Design stage: hid treated cells from first exposure, computed every layer's placebo distribution, the own-class placebos and the pre-reform event-study check.
3. Committed the design and plan, ran a blinded dry run, then one registered run with treated cells restored.
4. Judged the registered layer's estimate against its placebo distribution; reported every other layer side by side.

**Econometric model**

Saturated fixed effects on CPI classes by capital city and quarter, the layer chosen for this reform in the blinded power study, with every other layer reported side by side.

*Saturated fixed effects*

> y<sub>cjq</sub> = α<sub>cj</sub> + δ<sub>cq</sub> + γ<sub>jq</sub> + β·D<sub>cjq</sub> + ε<sub>cjq</sub>

*Year by year*

> y<sub>cjq</sub> = α<sub>cj</sub> + δ<sub>cq</sub> + γ<sub>jq</sub> + Σ<sub>k≠−1</sub> β<sub>k</sub>·1[q − T<sub>j</sub> = k]·T<sub>cj</sub> + ε<sub>cjq</sub>

| Symbol | Meaning |
|---|---|
| y<sub>cjq</sub> | 100 × log of the CPI class relative to All groups in city j, quarter q |
| D<sub>cjq</sub> | 1 for the reform's class in a treated state (or city) from its first exposed period to the end of its window |
| α<sub>cj</sub> | a level for each class in each state |
| δ<sub>cq</sub> | each class's national movement in each period (industry cycles, product-wide price swings) |
| γ<sub>jq</sub> | each state's movement in each period (state booms and slumps) |

- **Estimand:** The average change in the outcome for the reform's classes in treated states over the window, beyond the same classes elsewhere and the treated states' other classes, net of the mean placebo estimate.
- **Identifying assumption:** Without the reform, the treated classes in treated states would have moved like the same classes elsewhere plus their states' other classes (parallel trends in the saturated model; for synthetic DiD, like the weighted comparison cells).
- **Inference:** The same estimator applied to up to 40 placebo industry groups (or CPI classes) at the reform's states and dates gives the no-effect distribution: the p-value is the share of centred placebo estimates at least as large; the 90% interval subtracts their 5th and 95th percentiles. Benjamini-Hochberg q-values across the specification's primary outcomes. Placebo states and fake dates check the reform's own classes.

## Ride-share legalisation (2015 to 2018): re-evaluation with saturated effects

`rideshare-legalisation-2015-2018-phase5` · evaluated 18 October 2026 · grade Not identified

Not identified: business entry rate −2.2 per 100 businesses a year (p = 0.17), saturated fixed effects.

**Key insights**

- The question: did legalising ride-sharing (2015 to 2018) change how many taxi and ride businesses started or closed, or fares?
- The comparison: Staggered: each group of states that legalised in the same year against states that had not yet, with class x year and state x year effects.
- What we found: the effect cannot be identified: a pre-reform year of the primary outcome lies outside its 95% placebo band, so the treated group was already moving apart before the reform. The registered layer's estimate (−2.2 per 100 businesses a year) is not an effect.
- Other outcomes: business exit rate −0.3 (p = 0.59); urban transport fares: prices relative to the CPI −0.3 (p = 0.85).
- How precise: only changes larger than about 4.3 per 100 businesses a year could have been detected.
- Compared with the earlier evaluation (2026-10-15, now archived): it found that the effect could not be identified (business entry rate +0.2 per 100 businesses a year). The conclusion is unchanged; the smallest detectable effect is now 4.3, down from 6.0. This evaluation uses the estimator chosen in the blinded power study and the latest data.
- What it means: these data cannot separate the reform from what was already happening.

**What we did**

1. Registered the layer, outcomes, windows and placebo pools in the specification before any treated post-reform outcome was computed.
2. Design stage: hid treated cells from first exposure, computed every layer's placebo distribution, the own-class placebos and the pre-reform event-study check.
3. Committed the design and plan, ran a blinded dry run, then one registered run with treated cells restored.
4. Judged the registered layer's estimate against its placebo distribution; reported every other layer side by side.

**Econometric model**

Saturated fixed effects on ANZSIC classes by state and financial year, the layer chosen for this reform in the blinded power study, with every other layer reported side by side.

*Saturated fixed effects*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + β·D<sub>cst</sub> + ε<sub>cst</sub>

*Year by year*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + Σ<sub>k≠−1</sub> β<sub>k</sub>·1[t − T<sub>s</sub> = k]·T<sub>cs</sub> + ε<sub>cst</sub>

| Symbol | Meaning |
|---|---|
| y<sub>cst</sub> | Entries (or exits) per 100 businesses operating at the start of year t, class c, state s |
| D<sub>cst</sub> | 1 for the reform's class in a treated state (or city) from its first exposed period to the end of its window |
| α<sub>cs</sub> | a level for each class in each state |
| δ<sub>ct</sub> | each class's national movement in each period (industry cycles, product-wide price swings) |
| γ<sub>st</sub> | each state's movement in each period (state booms and slumps) |

- **Estimand:** The average change in the outcome for the reform's classes in treated states over the window, beyond the same classes elsewhere and the treated states' other classes, net of the mean placebo estimate.
- **Identifying assumption:** Without the reform, the treated classes in treated states would have moved like the same classes elsewhere plus their states' other classes (parallel trends in the saturated model; for synthetic DiD, like the weighted comparison cells).
- **Inference:** The same estimator applied to up to 40 placebo industry groups (or CPI classes) at the reform's states and dates gives the no-effect distribution: the p-value is the share of centred placebo estimates at least as large; the 90% interval subtracts their 5th and 95th percentiles. Benjamini-Hochberg q-values across the specification's primary outcomes. Placebo states and fake dates check the reform's own classes.

## As-of-right taxi licences in Victoria (2014): re-evaluation with saturated effects

`vic-taxi-licensing-2014-phase5` · evaluated 18 October 2026 · grade Weak

No detectable effect: business entry rate −0.4 per 100 businesses a year (p = 0.68), saturated fixed effects, grade Weak.

**Key insights**

- The question: did Victoria's as-of-right taxi licences (2014) bring new taxi businesses in, or lower fares?
- The comparison: Victorian taxis against taxis in the other states, 2014-15 only (before ride-share legalisation), with class x year and state x year effects.
- What we found: no detectable change. Business entry rate: −0.4 per 100 businesses a year (90% interval −2.6 to +1.8; p = 0.68).
- Other outcomes: business exit rate −1.9 (p = 0.049; not identified: a pre-reform year lies outside its placebo band); urban transport fares: prices relative to the CPI −10.6 (p = 0.024). Secondary outcomes are outside the registered decision rule and not adjusted for testing several outcomes, so a p-value below 0.05 among them is a lead, not a finding.
- How precise: only changes larger than about 3.5 per 100 businesses a year could have been detected.
- After unblinding (not pre-registered): the fall in Melbourne's urban transport fares came all at once in 2015-Q1 (−19.1 points in one quarter, about 12 times the usual quarterly move), not when the taxi reform started (2014-Q3: +0.1). January 2015 is when public transport fare changes were reported to start (zone 1+2 travel capped at the zone 1 fare; free CBD trams). The CPI class covers public transport fares as well as taxi fares, and a one-quarter step of this size looks like a fare-schedule change, not taxi competition building up; the fares result should not be read as an effect of the taxi reform.
- Compared with the earlier evaluation (2026-10-15, now archived): it found no detectable effect (business entry rate −1.4 per 100 businesses a year). The conclusion is unchanged; the smallest detectable effect is now 3.5, down from 4.2. This evaluation uses the estimator chosen in the blinded power study and the latest data.
- What it means: no effect is detectable with public state-level data; an effect smaller than the detectable size cannot be ruled out.

**What we did**

1. Registered the layer, outcomes, windows and placebo pools in the specification before any treated post-reform outcome was computed.
2. Design stage: hid treated cells from first exposure, computed every layer's placebo distribution, the own-class placebos and the pre-reform event-study check.
3. Committed the design and plan, ran a blinded dry run, then one registered run with treated cells restored.
4. Judged the registered layer's estimate against its placebo distribution; reported every other layer side by side.

**Econometric model**

Saturated fixed effects on ANZSIC classes by state and financial year, the layer chosen for this reform in the blinded power study, with every other layer reported side by side.

*Saturated fixed effects*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + β·D<sub>cst</sub> + ε<sub>cst</sub>

*Year by year*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + Σ<sub>k≠−1</sub> β<sub>k</sub>·1[t − T<sub>s</sub> = k]·T<sub>cs</sub> + ε<sub>cst</sub>

| Symbol | Meaning |
|---|---|
| y<sub>cst</sub> | Entries (or exits) per 100 businesses operating at the start of year t, class c, state s |
| D<sub>cst</sub> | 1 for the reform's class in a treated state (or city) from its first exposed period to the end of its window |
| α<sub>cs</sub> | a level for each class in each state |
| δ<sub>ct</sub> | each class's national movement in each period (industry cycles, product-wide price swings) |
| γ<sub>st</sub> | each state's movement in each period (state booms and slumps) |

- **Estimand:** The average change in the outcome for the reform's classes in treated states over the window, beyond the same classes elsewhere and the treated states' other classes, net of the mean placebo estimate.
- **Identifying assumption:** Without the reform, the treated classes in treated states would have moved like the same classes elsewhere plus their states' other classes (parallel trends in the saturated model; for synthetic DiD, like the weighted comparison cells).
- **Inference:** The same estimator applied to up to 40 placebo industry groups (or CPI classes) at the reform's states and dates gives the no-effect distribution: the p-value is the share of centred placebo estimates at least as large; the 90% interval subtracts their 5th and 95th percentiles. Benjamini-Hochberg q-values across the specification's primary outcomes. Placebo states and fake dates check the reform's own classes.

## Perth retail trading hours (2010 weeknights, 2012 Sundays): re-evaluation with saturated effects

`wa-trading-hours-2010-2012-phase5` · evaluated 18 October 2026 · grade Moderate

No detectable effect: business entry rate +1.0 per 100 businesses a year (p = 0.49), saturated fixed effects, grade Moderate.

**Key insights**

- The question: did longer shop trading hours in Perth (weeknights from November 2010, Sundays from August 2012) change how many general retail businesses opened or closed?
- The comparison: WA general retail classes against the same classes in NSW, Victoria, Queensland, Tasmania, the ACT and the NT (SA excluded), 2010-11 to 2017-18, with class x year and state x year effects.
- What we found: no detectable change. Business entry rate: +1.0 per 100 businesses a year (90% interval −1.9 to +3.5; p = 0.49).
- Other outcomes: business exit rate +1.3 (p = 0.22).
- How precise: only changes larger than about 4.6 per 100 businesses a year could have been detected.
- Compared with the earlier evaluation (2026-10-15, now archived): it found no detectable effect (business entry rate +0.8 per 100 businesses a year). The conclusion is unchanged; the smallest detectable effect is now 4.6, down from 5.6. This evaluation uses the estimator chosen in the blinded power study and the latest data.
- What it means: no effect is detectable with public state-level data; an effect smaller than the detectable size cannot be ruled out.

**What we did**

1. Registered the layer, outcomes, windows and placebo pools in the specification before any treated post-reform outcome was computed.
2. Design stage: hid treated cells from first exposure, computed every layer's placebo distribution, the own-class placebos and the pre-reform event-study check.
3. Committed the design and plan, ran a blinded dry run, then one registered run with treated cells restored.
4. Judged the registered layer's estimate against its placebo distribution; reported every other layer side by side.

**Econometric model**

Saturated fixed effects on ANZSIC classes by state and financial year, the layer chosen for this reform in the blinded power study, with every other layer reported side by side.

*Saturated fixed effects*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + β·D<sub>cst</sub> + ε<sub>cst</sub>

*Year by year*

> y<sub>cst</sub> = α<sub>cs</sub> + δ<sub>ct</sub> + γ<sub>st</sub> + Σ<sub>k≠−1</sub> β<sub>k</sub>·1[t − T<sub>s</sub> = k]·T<sub>cs</sub> + ε<sub>cst</sub>

| Symbol | Meaning |
|---|---|
| y<sub>cst</sub> | Entries (or exits) per 100 businesses operating at the start of year t, class c, state s |
| D<sub>cst</sub> | 1 for the reform's class in a treated state (or city) from its first exposed period to the end of its window |
| α<sub>cs</sub> | a level for each class in each state |
| δ<sub>ct</sub> | each class's national movement in each period (industry cycles, product-wide price swings) |
| γ<sub>st</sub> | each state's movement in each period (state booms and slumps) |

- **Estimand:** The average change in the outcome for the reform's classes in treated states over the window, beyond the same classes elsewhere and the treated states' other classes, net of the mean placebo estimate.
- **Identifying assumption:** Without the reform, the treated classes in treated states would have moved like the same classes elsewhere plus their states' other classes (parallel trends in the saturated model; for synthetic DiD, like the weighted comparison cells).
- **Inference:** The same estimator applied to up to 40 placebo industry groups (or CPI classes) at the reform's states and dates gives the no-effect distribution: the p-value is the share of centred placebo estimates at least as large; the 90% interval subtracts their 5th and 95th percentiles. Benjamini-Hochberg q-values across the specification's primary outcomes. Placebo states and fake dates check the reform's own classes.

## Perth 9pm weeknight trading (2010), re-evaluated with new data

`wa-trading-hours-weeknight-2010-new-data` · evaluated 18 October 2026 · grade Moderate

Letting Perth's general retail shops open until 9pm on weeknights (November 2010) made no detectable difference to the number of retail businesses in Perth compared with regional WA (−1.8 log points, 90% interval −5.8 to +4.2) or to the turnover of supermarkets, clothing and department stores (+2.0%, −4.4 to +7.2). Effects of about 10% or more in either can be ruled out; smaller ones cannot.

**Key insights**

- The question: did letting Perth's general retail shops open until 9pm on weeknights (from 1 November 2010) change the number of retail businesses or how much the shops sold?
- The comparisons: retail business numbers in metropolitan Perth against regional WA, net of other industries and set against the same city-versus-country gap in other states; and monthly sales of the shops covered (supermarkets, clothing and department stores) in WA against NSW, Victoria, Queensland and the ACT.
- What we found: no detectable change. Perth's retail business count moved −1.8% relative to regional WA (90% interval −5.8 to +4.2); the shops' sales moved +2.0% (−4.4 to +7.2).
- How precise: changes of about 10% or more in either could have been detected; smaller ones could not.
- What it means: the business-count result is robust. The sales result is not: removing each state's earlier trend pushes it up, and netting out cafes and restaurants pushes it down, so the sign depends on the comparison. Hours worked were too noisy to use.

**What we did**

1. Added three data sources the first evaluation did not use: CABEE business counts by SA2 (two archived releases), ABS Retail Trade monthly turnover and Labour Force hours by industry group.
2. Design-stage review with WA's post-reform outcomes hidden in code: chose the comparison states, windows and placebo pools, and measured power (docs/pap_wa_weeknight_2010.md).
3. Wrote the plan; a blinded dry run reproduced the design-stage no-effect distributions; plan and code were registered by SHA-256 before one unblinded run.
4. Estimated each design and its year-by-year path, then every registered robustness check (small businesses only, Mandurah in Perth, WA outback left out, no size floor, each state's trend removed, triple differences against food services and the rest of retail, each store type alone).
5. Applied the plan's findings, verdict and grading rules.

**Econometric model**

Difference-in-differences with one treated unit and two-way fixed effects, for each of three data sources. Inference from no-effect distributions (fake dates, comparison states and placebo industries), not from standard errors.

*C. Retail businesses by place (primary): the outcome for division x in state s*

> g<sub>x,s,t</sub> = [100 ln B<sup>cap</sup><sub>x,s,t</sub> − 100 ln B<sup>rest</sup><sub>x,s,t</sub>] − [100 ln B<sup>cap</sup><sub>o,s,t</sub> − 100 ln B<sup>rest</sup><sub>o,s,t</sub>]

*C. Estimator (units u = division × state; treated unit: retail in WA)*

> g<sub>u,t</sub> = α<sub>u</sub> + λ<sub>t</sub> + δ<sub>C</sub> · D<sub>u,t</sub> + ε<sub>u,t</sub>

*A. Turnover of the shops covered (primary), monthly*

> 100 ln R<sub>s,m</sub> = α<sub>s</sub> + λ<sub>m</sub> + δ<sub>A</sub> · D<sub>s,m</sub> + ε<sub>s,m</sub>

*B. Hours worked (descriptive), mid-quarter months*

> 100 ln H<sub>s,q</sub> = α<sub>s</sub> + λ<sub>q</sub> + δ<sub>B</sub> · D<sub>s,q</sub> + ε<sub>s,q</sub>

| Symbol | Meaning |
|---|---|
| B<sup>cap</sup><sub>x,s,t</sub>, B<sup>rest</sup><sub>x,s,t</sub> | Businesses in division x at 30 June of year t in the capital (for WA, metropolitan Perth, SA4s 503–507) and in the rest of the state (CABEE by SA2, two releases chained at June 2011) |
| o | All other divisions together, excluding retail (G), accommodation and food (H) and x |
| D | 1 for the treated unit after the reform: June 2011 and 2012 for C; November 2010 to July 2012 for A (July to October 2010 left out); November 2010 to May 2012 for B |
| R<sub>s,m</sub> | Seasonally adjusted turnover of supermarkets and grocery stores, clothing and department stores in state s, month m (ABS Retail Trade) |
| H<sub>s,q</sub> | Hours actually worked in ANZSIC groups 411, 425 and 426 (Labour Force EQ06) |
| α, λ | Unit and period fixed effects |

- **Estimand:** C: the change in metropolitan Perth's retail business count relative to regional WA, beyond the same change for other industries and for capitals in other states (log points, about %). A: the change in WA turnover of the shops covered relative to comparison states (log points).
- **Identifying assumption:** C: without the reform, Perth's retail count relative to regional WA would have moved like other industries' and like retail's city-versus-country gap in other states (a triple difference). A: WA turnover of these shops would have moved like the comparison states'. Both passed the design-stage fake-date checks; B failed its check and is descriptive only.
- **Inference:** No conventional standard errors (one treated state). A and B: estimates at every fake date from January 1995 whose window ends before the reform, plus each comparison state at the real date (834 estimates for A). C: every other division in every state as if treated, plus retail in each comparison state, cells of at least 1,000 businesses (59 estimates). p-value: two-sided rank; 90% interval: estimate minus the 95th and 5th percentiles (Conley and Taber 2011); smallest detectable effect: 2.8 × standard deviation; Benjamini–Hochberg q-values across the two primaries.
