# Power study (forward plan Phase 3): how much each layer shrinks the no-effect spread

**Runs:** 18 October 2026, blinded. First run: business entry and exit, placebo industries. Second run (completing Phase 3): placebo states, fake dates and both; CPI prices; the new families from the [gap scan](legislation_gap_scan.md). The first run's numbers are reproduced exactly by the second.

**Code:** `alicia/analyses/power_study/run.py` (business counts), `prices.py` (CPI), `tables.py` (the tables below, generated from the outputs). **Numbers:** `power.json` and `power_prices.json` in the same folder (every placebo estimate is stored).

**Blinding:**
- Before anything is computed, every row for a reform's treated industries (or CPI class) in its treated states from the first exposed period on is deleted, and treated states after their window. A check in the code enforces this.
- No reform's effect was estimated.

## 1. Key findings (non-technical)

1. **State-wide conditions are not what limits precision.**
   - For business entry and exit, and for prices alike, adding state × period effects or measured state controls (demand, unemployment, population, commodity exposure) changes the smallest detectable effect by 1.5% or less.
2. **Industry-wide (or product-wide) movements are.**
   - For business counts, comparing each industry with the same industry elsewhere (industry × year effects) cuts the smallest detectable effect by 28–77% for most reforms.
   - For prices it is essential. Without class × quarter effects, a CPI class's own national swings swamp everything: smallest detectable effects of 35–70% of the relative price. With them, 6.5–10% against placebo classes for most reforms (17–22% for the NT drinks and child care classes).
   - Tested on the reform's own class at fake dates, the saturated price model's total error is 0.2–2.8 log points for most designs, so effects of about 1–8% are detectable.
3. **Testing the treated industry itself gives a mixed check on the placebo-industry results.**
   - For the legal profession law and e-conveyancing, the treated class at fake dates or in other states is quieter than the placebo industries suggested.
   - For Victorian taxis and the CTP reforms it is noisier. With placebo states, the saturated model gains little over the simple model for taxis (error 2.4 against 2.6 per 100).
   - These checks have few draws (5–20), so they are a guide, not a ranking.
4. **They also expose bias that placebo industries cannot.**
   - Several price designs show a systematic error at fake dates: the reform's class already drifted in the treated cities before the reform.
   - **East-coast gas** (+11 log points with the saturated model): east-coast gas prices diverged from WA and the NT before the 2022 cap, so the comparison fails as it stands.
   - **Electricity** (+10 for retail price deregulation; +1.6 for the energy customer framework).
   - The fixed-effect layers remove most such bias for business counts (e.g. CTP placebo states: two-way +9.8, saturated −1.5).
5. **Among the new families, fuel price reporting has the most precise design.**
   - The saturated price model at fake dates has a root mean square error of 0.7 log points: an effect of about 2% on fuel prices relative to other prices would be detectable.
   - Fuel retailers' entry and exit can be measured to about 2 per 100.
   - E-conveyancing (legal services, 2.9 and 1.8 per 100) and the 2022 building code (2.7 and 1.6) are next for business counts, but their outcomes are diluted or their windows short (see the [evaluability ratings](evaluability_new_families.md)).
6. **Four reforms cannot be studied with business counts by class and state:**
   - NT container deposits (12 businesses in the treated group);
   - retail energy deregulation and the energy customer framework (59);
   - the NT takeaway liquor moratorium (6).

   The energy reforms remain measurable with CPI electricity prices.

## 2. Design

| Item | Choice |
|---|---|
| Business outcome | Entry and exit rates per 100 businesses at the start of the financial year (CABEE), ANZSIC class × state × year; cells weighted by businesses. Evaluated reforms use their registered vintage; new families use CABEE to 2024-25 |
| Price outcome | 100 × log(CPI class / All groups), capital city × quarter, 2001-Q1 to 2025-Q3 (ABS CPI 17th series); every eligible class in the panel |
| Placebo families | **Industries** (or CPI classes): up to 40 size-matched class groups outside the treated divisions (or CPI classes outside related subgroups), at the reform's states and dates. **States**: the reform's own classes in states that never adopted it (up to 20 assignments). **Fake dates**: the reform's own classes and states moved back whole years, window cut before real exposure. **States and dates**: both (up to 20) |
| Measure | Placebo industries: smallest detectable effect (MDE), 80% power, 5% two-sided = 2.8 × standard deviation of placebo estimates. Own-class families: mean (systematic error) and root mean square (total error) of the placebo estimates, because draws that share the treated class's trend can be biased without being spread out |

**Layers compared** (*c* class, *s* state or city, *t* year or quarter; D = 1 for treated classes in treated states after adoption):

| Layer | Model |
|---|---|
| Two-way | y_{cst} = α_{cs} + λ_t + β·D_{cst} + ε |
| + state × year | y_{cst} = α_{cs} + γ_{st} + β·D_{cst} + ε |
| Saturated | y_{cst} = α_{cs} + δ_{ct} + γ_{st} + β·D_{cst} + ε |
| Measured controls | Two-way + state final demand growth, unemployment rate, population growth, mining share × commodity prices |
| Imputation | Saturated effects fitted on untreated cells only; effect = actual − imputed (Borusyak, Jaravel and Spiess) |
| Synthetic DiD | The treated group's series against all untreated cells, with unit and time weights (Arkhangelsky et al.) |
| Generalised synthetic control | Interactive fixed effects; factors from untreated cells, chosen by cross-validation (Xu) |

## 3. Results

Business counts in points per 100 businesses; prices in log points × 100 (about percent). **Bold**: smallest MDE in the row. "Registered design": the batch's design-stage spread (stacked DiD net of placebo industries or classes). "Mean / RMS": mean and root mean square of placebo estimates; families with fewer than 5 draws are not shown.

### 3.1 Business entries: evaluated reforms

| Reform | Mean rate | Registered design | Two-way | + state × year | Saturated | Controls | Imputation | Synthetic DiD | Gen. synth. |
|---|---|---|---|---|---|---|---|---|---|
| National Quality Framework for childcare (2012): the WA stagger | 13.8 | 9.8 | 10.1 | 10.1 | 10.9 | 10.1 | 10.9 | **6.0** | 10.6 |
| Heavy Vehicle National Law (2014) | 13.6 | 9.4 | 8.3 | 8.3 | **4.4** | 8.3 | 4.4 | 8.7 | 10.0 |
| As-of-right taxi licences in Victoria (2014) | 13.0 | 4.2 | 9.1 | 9.2 | **3.5** | 9.2 | **3.5** | 9.2 | 9.2 |
| Legal Profession Uniform Law (NSW and Victoria, 2015) | 13.6 | 7.0 | 19.8 | 19.8 | **4.5** | 19.8 | 4.5 | 18.1 | 19.3 |
| Ride-share legalisation (2015 to 2018) | 13.4 | 6.0 | 6.7 | 6.7 | 4.3 | 6.7 | 4.7 | **4.1** | 4.3 |
| Perth weeknight trading (November 2010) | 14.0 | — | 7.3 | 7.4 | **5.2** | 7.3 | 5.5 | 6.5 | 7.5 |
| Automatic mutual recognition of occupational registrations (2021-22) | 16.3 | — | 4.7 | 4.8 | 4.3 | 4.7 | **2.5** | 4.5 | 4.9 |

### 3.2 Business entries: new families

| Reform | Mean rate | Two-way | + state × year | Saturated | Controls | Imputation | Synthetic DiD | Gen. synth. |
|---|---|---|---|---|---|---|---|---|
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | 14.5 | 4.9 | 4.9 | **2.2** | 4.9 | 11.0 | 3.2 | 5.5 |
| Pharmacists treat uncomplicated UTIs (QLD 2020, NSW 2023, five more 2023-24) | 15.4 | 4.2 | 4.2 | **2.9** | 4.2 | 11.1 | 3.3 | 5.6 |
| Small bar licence (NSW, July 2013) | 13.5 | 15.1 | 15.1 | 4.8 | 15.1 | **4.8** | 14.2 | 15.3 |
| Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023) | 14.6 | 11.4 | 11.5 | **2.9** | 11.4 | 3.3 | 10.3 | 26.6 |
| 2022 building code adoption (NSW, VIC, QLD, ACT, NT 2023-24; SA, TAS, WA 2024-25) | 16.1 | 4.5 | 4.5 | **2.7** | 4.5 | 2.8 | 3.0 | 5.7 |
| Contestable VET entitlements (VIC 2009, SA 2012, QLD 2013) | 13.2 | 10.9 | 11.0 | **3.6** | 10.9 | 4.5 | 11.2 | 10.8 |
| NDIS Quality and Safeguards Commission (NSW, SA 2018; five more 2019; WA 2020) | 13.8 | 3.4 | 3.4 | 4.3 | 3.4 | 5.0 | **3.1** | 4.2 |
| CTP insurance reforms (NSW 2017; SA price competition 2019; ACT 2020) | 14.3 | 6.2 | 6.2 | **4.8** | 6.1 | 5.0 | 5.1 | 11.8 |
| Commercial property stamp duty cut or abolished (SA from December 2015; ACT June 2018) | 13.7 | 11.8 | 11.7 | 5.3 | 11.7 | **5.3** | 9.4 | 9.7 |
| Victorian gaming venue-operator model (August 2012) | 13.2 | 13.5 | 13.5 | **5.2** | 13.5 | 5.4 | 11.2 | 12.7 |
| Victorian freeze on late-night liquor licences lifted (July 2023) | 16.2 | 9.0 | 9.0 | 7.3 | 9.0 | 7.3 | **6.8** | 9.2 |

### 3.3 Business entries: placebo families

| Reform | Family | Draws | Two-way | Saturated | Imputation | Synthetic DiD | Smallest RMS |
|---|---|---|---|---|---|---|---|
| National Quality Framework for childcare (2012): the WA stagger | Placebo industries | 40 | +0.2 / 3.6 | +0.3 / 3.9 | +0.3 / 3.9 | +0.6 / 2.2 | Synthetic DiD |
| Heavy Vehicle National Law (2014) | Placebo industries | 40 | +0.2 / 3.0 | +0.1 / 1.6 | +0.1 / 1.6 | +0.9 / 3.2 | Saturated |
| As-of-right taxi licences in Victoria (2014) | Placebo industries | 40 | +0.3 / 3.2 | -0.4 / 1.3 | -0.4 / 1.3 | +0.7 / 3.3 | Saturated |
|  | Placebo states | 7 | +1.3 / 2.6 | +0.6 / 2.4 | +0.6 / 2.4 | +2.1 / 2.8 | Saturated |
|  | Fake dates | 5 | -2.3 / 4.0 | -1.5 / 1.8 | -1.5 / 1.8 | -0.9 / 3.9 | Saturated |
| Legal Profession Uniform Law (NSW and Victoria, 2015) | Placebo industries | 39 | +1.8 / 7.2 | +0.2 / 1.6 | +0.2 / 1.6 | +2.3 / 6.8 | Saturated |
|  | Placebo states | 15 | -1.1 / 1.2 | +0.1 / 0.6 | +0.1 / 0.6 | -0.2 / 0.7 | + state × year |
|  | Fake dates | 6 | +1.6 / 1.8 | -0.2 / 0.6 | -0.2 / 0.6 | +1.6 / 1.8 | Saturated |
| Ride-share legalisation (2015 to 2018) | Placebo industries | 40 | +0.3 / 2.4 | +0.3 / 1.6 | +0.3 / 1.7 | +0.7 / 1.6 | Gen. synth. |
|  | Fake dates | 6 | +3.8 / 7.3 | +0.3 / 2.0 | +0.7 / 2.1 | +4.0 / 6.3 | Saturated |
| Perth weeknight trading (November 2010) | Placebo industries | 40 | -0.2 / 2.6 | +0.1 / 1.9 | +0.1 / 1.9 | -0.0 / 2.3 | Saturated |
| Automatic mutual recognition of occupational registrations (2021-22) | Placebo industries | 24 | -0.3 / 1.7 | +0.3 / 1.5 | +0.4 / 1.0 | +0.3 / 1.6 | Imputation |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | Placebo industries | 40 | -1.2 / 2.1 | -0.1 / 0.8 | -0.7 / 3.9 | -0.6 / 1.3 | Saturated |
|  | Fake dates | 5 | +0.9 / 1.3 | +0.2 / 0.8 | -0.5 / 1.0 | +1.3 / 1.5 | Saturated |
| Pharmacists treat uncomplicated UTIs (QLD 2020, NSW 2023, five more 2023-24) | Placebo industries | 40 | -0.5 / 1.5 | +0.2 / 1.0 | -0.2 / 3.9 | -0.2 / 1.2 | Saturated |
| Small bar licence (NSW, July 2013) | Placebo industries | 40 | +0.1 / 5.3 | -0.4 / 1.7 | -0.4 / 1.7 | +0.8 / 5.1 | Saturated |
|  | Placebo states | 5 | +0.3 / 2.9 | -0.5 / 2.2 | -0.5 / 2.2 | +2.2 / 2.8 | Saturated |
| Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023) | Placebo industries | 40 | +1.1 / 4.2 | -0.1 / 1.0 | -0.2 / 1.2 | +1.4 / 3.9 | Saturated |
|  | Fake dates | 6 | -0.8 / 1.1 | -0.0 / 0.2 | -0.1 / 0.3 | -0.3 / 0.6 | Saturated |
| 2022 building code adoption (NSW, VIC, QLD, ACT, NT 2023-24; SA, TAS, WA 2024-25) | Placebo industries | 40 | +0.3 / 1.6 | +0.3 / 1.0 | +0.3 / 1.1 | +0.8 / 1.3 | Saturated |
|  | Fake dates | 6 | -0.7 / 2.5 | +0.2 / 1.4 | +0.1 / 1.4 | -0.4 / 2.5 | Imputation |
| Contestable VET entitlements (VIC 2009, SA 2012, QLD 2013) | Placebo industries | 40 | +0.5 / 3.9 | +0.1 / 1.3 | +0.2 / 1.6 | +0.9 / 4.0 | Saturated |
| NDIS Quality and Safeguards Commission (NSW, SA 2018; five more 2019; WA 2020) | Placebo industries | 40 | +0.1 / 1.2 | -0.2 / 1.5 | -0.3 / 1.8 | -0.1 / 1.1 | Synthetic DiD |
| CTP insurance reforms (NSW 2017; SA price competition 2019; ACT 2020) | Placebo industries | 40 | -0.9 / 2.4 | -0.4 / 1.8 | -0.5 / 1.8 | -0.0 / 1.8 | Saturated |
|  | Placebo states | 20 | +9.8 / 15.2 | -1.5 / 7.1 | -3.9 / 9.6 | +29.5 / 33.0 | Saturated |
|  | Fake dates | 6 | -0.8 / 1.3 | +0.4 / 0.8 | +0.6 / 1.0 | -0.5 / 1.1 | Saturated |
| Commercial property stamp duty cut or abolished (SA from December 2015; ACT June 2018) | Placebo industries | 37 | +0.0 / 4.1 | -0.5 / 1.9 | -0.5 / 1.9 | +0.7 / 3.4 | Imputation |
|  | Placebo states | 20 | -0.7 / 1.2 | -0.3 / 0.7 | -0.3 / 0.7 | -0.6 / 1.1 | Imputation |
| Victorian gaming venue-operator model (August 2012) | Placebo industries | 40 | +0.3 / 4.8 | +0.5 / 1.9 | +0.5 / 2.0 | +0.8 / 4.0 | Saturated |
|  | Placebo states | 7 | +2.0 / 2.7 | +0.1 / 1.6 | +0.1 / 1.7 | +2.9 / 3.7 | Saturated |
| Victorian freeze on late-night liquor licences lifted (July 2023) | Placebo industries | 40 | -0.4 / 3.2 | +0.3 / 2.6 | +0.3 / 2.6 | +0.3 / 2.4 | Synthetic DiD |
|  | Placebo states | 7 | -0.2 / 2.4 | +0.9 / 2.4 | +0.9 / 2.4 | +0.5 / 2.0 | Synthetic DiD |
|  | Fake dates | 6 | -1.0 / 1.4 | -0.8 / 2.0 | -0.8 / 2.0 | -1.1 / 1.3 | Gen. synth. |

### 3.4 Business exits: evaluated reforms

| Reform | Mean rate | Registered design | Two-way | + state × year | Saturated | Controls | Imputation | Synthetic DiD | Gen. synth. |
|---|---|---|---|---|---|---|---|---|---|
| National Quality Framework for childcare (2012): the WA stagger | 13.6 | 8.1 | **2.2** | 2.3 | 4.8 | 2.2 | 4.9 | 2.5 | 2.5 |
| Heavy Vehicle National Law (2014) | 12.9 | 9.9 | 3.1 | 3.1 | 3.0 | 3.1 | 3.0 | **2.8** | 3.1 |
| As-of-right taxi licences in Victoria (2014) | 13.2 | 3.7 | 2.6 | 2.6 | **2.4** | 2.6 | **2.4** | 2.5 | 2.6 |
| Legal Profession Uniform Law (NSW and Victoria, 2015) | 12.9 | 2.6 | 3.6 | 3.6 | **1.6** | 3.6 | 1.6 | 3.1 | 3.4 |
| Ride-share legalisation (2015 to 2018) | 13.0 | 5.7 | 3.2 | 3.2 | **2.2** | 3.2 | 2.4 | 2.7 | 3.3 |
| Perth weeknight trading (November 2010) | 13.8 | — | 3.4 | 3.4 | 4.5 | 3.4 | 4.3 | **3.0** | 3.5 |
| Automatic mutual recognition of occupational registrations (2021-22) | 13.1 | — | 1.8 | 1.8 | 1.3 | 1.8 | 1.7 | 2.0 | **0.9** |

### 3.5 Business exits: new families

| Reform | Mean rate | Two-way | + state × year | Saturated | Controls | Imputation | Synthetic DiD | Gen. synth. |
|---|---|---|---|---|---|---|---|---|
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | 12.7 | 4.6 | 4.6 | **2.2** | 4.6 | 2.3 | 4.3 | 4.2 |
| Pharmacists treat uncomplicated UTIs (QLD 2020, NSW 2023, five more 2023-24) | 12.5 | 2.9 | 2.9 | **2.1** | 2.9 | 25.6 | 2.7 | 4.2 |
| Small bar licence (NSW, July 2013) | 13.1 | 4.7 | 4.7 | 3.6 | 4.7 | **3.6** | 3.8 | 4.3 |
| Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023) | 12.6 | 5.8 | 5.9 | **1.8** | 5.8 | 2.4 | 6.3 | 6.8 |
| 2022 building code adoption (NSW, VIC, QLD, ACT, NT 2023-24; SA, TAS, WA 2024-25) | 12.9 | 2.0 | 2.0 | **1.6** | 2.0 | 1.6 | 1.7 | 2.0 |
| Contestable VET entitlements (VIC 2009, SA 2012, QLD 2013) | 13.5 | 3.8 | 3.8 | **3.2** | 3.8 | 3.4 | 4.3 | 4.2 |
| NDIS Quality and Safeguards Commission (NSW, SA 2018; five more 2019; WA 2020) | 12.4 | 4.5 | 4.5 | **3.0** | 4.5 | 3.5 | 4.2 | 8.8 |
| CTP insurance reforms (NSW 2017; SA price competition 2019; ACT 2020) | 12.5 | 5.7 | 5.7 | **4.1** | 5.7 | 4.2 | 5.3 | 6.6 |
| Commercial property stamp duty cut or abolished (SA from December 2015; ACT June 2018) | 12.6 | 2.8 | 2.9 | **2.4** | 2.8 | 2.4 | 2.6 | 3.2 |
| Victorian gaming venue-operator model (August 2012) | 13.1 | 2.3 | 2.3 | 2.7 | 2.3 | 2.6 | **2.0** | 2.1 |
| Victorian freeze on late-night liquor licences lifted (July 2023) | 13.0 | 2.9 | 2.9 | 3.0 | 2.9 | 3.0 | **2.8** | 3.0 |

### 3.6 Business exits: placebo families

| Reform | Family | Draws | Two-way | Saturated | Imputation | Synthetic DiD | Smallest RMS |
|---|---|---|---|---|---|---|---|
| National Quality Framework for childcare (2012): the WA stagger | Placebo industries | 40 | +0.3 / 0.9 | +0.8 / 1.9 | +0.8 / 1.9 | +0.6 / 1.1 | Two-way |
| Heavy Vehicle National Law (2014) | Placebo industries | 40 | +0.0 / 1.1 | -0.0 / 1.0 | -0.0 / 1.0 | +0.0 / 1.0 | Synthetic DiD |
| As-of-right taxi licences in Victoria (2014) | Placebo industries | 40 | +0.1 / 0.9 | -0.1 / 0.8 | -0.1 / 0.8 | +0.2 / 0.9 | Saturated |
|  | Placebo states | 7 | -0.6 / 1.7 | -0.6 / 1.9 | -0.6 / 1.9 | -0.2 / 1.6 | Synthetic DiD |
|  | Fake dates | 5 | -0.5 / 1.6 | -1.0 / 1.2 | -1.0 / 1.2 | -0.3 / 1.6 | Saturated |
| Legal Profession Uniform Law (NSW and Victoria, 2015) | Placebo industries | 39 | +0.0 / 1.3 | +0.0 / 0.6 | +0.0 / 0.6 | +0.0 / 1.1 | Saturated |
|  | Placebo states | 15 | +0.4 / 1.0 | -0.2 / 1.3 | -0.2 / 1.3 | +0.2 / 1.0 | Controls |
|  | Fake dates | 6 | +0.3 / 0.5 | -0.4 / 0.4 | -0.4 / 0.4 | +0.4 / 0.5 | Saturated |
| Ride-share legalisation (2015 to 2018) | Placebo industries | 40 | -0.3 / 1.2 | -0.3 / 0.8 | -0.2 / 0.9 | -0.4 / 1.0 | Saturated |
|  | Fake dates | 6 | +0.1 / 0.4 | -0.1 / 0.7 | -0.0 / 1.0 | +0.2 / 0.5 | Controls |
| Perth weeknight trading (November 2010) | Placebo industries | 40 | -0.3 / 1.2 | -0.8 / 1.8 | -0.8 / 1.7 | +0.1 / 1.1 | Synthetic DiD |
| Automatic mutual recognition of occupational registrations (2021-22) | Placebo industries | 24 | +0.0 / 0.6 | +0.2 / 0.5 | +0.2 / 0.6 | +0.2 / 0.7 | Gen. synth. |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | Placebo industries | 40 | -0.8 / 1.8 | +0.1 / 0.8 | +0.1 / 0.8 | -0.3 / 1.5 | Saturated |
|  | Fake dates | 5 | +1.0 / 1.1 | +0.1 / 0.4 | +0.2 / 0.3 | +1.2 / 1.2 | Imputation |
| Pharmacists treat uncomplicated UTIs (QLD 2020, NSW 2023, five more 2023-24) | Placebo industries | 40 | -0.5 / 1.1 | +0.2 / 0.8 | -1.5 / 9.1 | -0.1 / 0.9 | Saturated |
| Small bar licence (NSW, July 2013) | Placebo industries | 40 | +0.1 / 1.7 | +0.0 / 1.3 | +0.0 / 1.3 | +0.0 / 1.3 | Imputation |
|  | Placebo states | 5 | +0.5 / 2.2 | +0.3 / 2.3 | +0.3 / 2.3 | +0.5 / 2.0 | Synthetic DiD |
| Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023) | Placebo industries | 40 | +0.3 / 2.1 | +0.1 / 0.6 | +0.1 / 0.8 | +0.6 / 2.3 | Saturated |
|  | Fake dates | 6 | +0.1 / 0.2 | -0.1 / 0.1 | -0.1 / 0.2 | +0.4 / 0.4 | Saturated |
| 2022 building code adoption (NSW, VIC, QLD, ACT, NT 2023-24; SA, TAS, WA 2024-25) | Placebo industries | 40 | -0.6 / 0.9 | -0.2 / 0.6 | -0.2 / 0.6 | -0.6 / 0.8 | Imputation |
|  | Fake dates | 6 | +0.4 / 0.6 | +0.1 / 0.5 | +0.0 / 0.5 | +0.8 / 0.9 | Imputation |
| Contestable VET entitlements (VIC 2009, SA 2012, QLD 2013) | Placebo industries | 40 | +0.7 / 1.5 | +0.1 / 1.1 | +0.0 / 1.2 | +0.9 / 1.8 | Saturated |
| NDIS Quality and Safeguards Commission (NSW, SA 2018; five more 2019; WA 2020) | Placebo industries | 40 | -0.7 / 1.7 | +0.1 / 1.1 | +0.1 / 1.2 | -0.4 / 1.5 | Saturated |
| CTP insurance reforms (NSW 2017; SA price competition 2019; ACT 2020) | Placebo industries | 40 | -0.6 / 2.1 | -0.1 / 1.4 | -0.1 / 1.5 | -0.3 / 1.9 | Saturated |
|  | Placebo states | 20 | +1.0 / 4.5 | +0.3 / 3.5 | -0.6 / 4.7 | +2.9 / 9.8 | Saturated |
|  | Fake dates | 6 | -0.5 / 0.9 | -0.7 / 1.5 | -0.6 / 1.4 | +0.4 / 1.5 | + state × year |
| Commercial property stamp duty cut or abolished (SA from December 2015; ACT June 2018) | Placebo industries | 37 | -0.0 / 1.0 | -0.0 / 0.9 | -0.0 / 0.9 | +0.0 / 0.9 | Saturated |
|  | Placebo states | 20 | +0.4 / 0.6 | -0.1 / 0.4 | -0.1 / 0.4 | +0.5 / 0.6 | Saturated |
| Victorian gaming venue-operator model (August 2012) | Placebo industries | 40 | +0.3 / 0.9 | +0.2 / 1.0 | +0.2 / 0.9 | +0.2 / 0.7 | Synthetic DiD |
|  | Placebo states | 7 | +0.2 / 1.0 | +0.0 / 1.0 | +0.1 / 1.0 | -0.1 / 0.6 | Synthetic DiD |
| Victorian freeze on late-night liquor licences lifted (July 2023) | Placebo industries | 40 | +0.2 / 1.0 | -0.2 / 1.1 | -0.2 / 1.1 | +0.1 / 1.0 | Synthetic DiD |
|  | Placebo states | 7 | -1.3 / 2.2 | -0.8 / 2.1 | -0.8 / 2.1 | -1.3 / 2.3 | Saturated |
|  | Fake dates | 6 | -1.8 / 2.0 | -1.6 / 1.7 | -1.6 / 1.7 | -1.3 / 1.6 | Gen. synth. |

### 3.7 Not feasible with CABEE classes

| Reform | Reason |
|---|---|
| Northern Territory container deposit scheme (2012) | treated group has 12 businesses in the base year (rule: 100); only 0 placebo groups (rule: 19) |
| Retail energy price deregulation (SA 2013, NSW 2014, south-east Queensland 2016) | treated group has 59 businesses in the base year (rule: 100) |
| National Energy Customer Framework adoption (ACT, TAS 2012; SA 2013; NSW 2013; QLD 2015) | treated group has 59 businesses in the base year (rule: 100) |
| NT moratorium on new takeaway liquor licences (October 2017) | treated group has 6 businesses in the base year (rule: 100); only 10 placebo groups (rule: 19) |

### 3.8 Prices

| Reform | CPI class | Registered design | Two-way | + state × year | Saturated | Controls | Imputation | Synthetic DiD | Gen. synth. |
|---|---|---|---|---|---|---|---|---|---|
| Northern Territory container deposit scheme (2012) | Waters, soft drinks and juices | 18.6 | 46.2 | 46.7 | 22.0 | 46.3 | 22.0 | **21.3** | 28.8 |
| Northern Territory container deposit scheme (2012) | Beer | 18.6 | 46.2 | 46.7 | 22.0 | 46.3 | 22.0 | **21.3** | 28.7 |
| National Quality Framework for childcare (2012): the WA stagger | Child care | 18.4 | 25.6 | 25.6 | 17.1 | 25.6 | 17.1 | **5.0** | 21.6 |
| Retail energy price deregulation (SA 2013, NSW 2014, south-east Queensland 2016) | Electricity | 9.5 | 48.5 | 48.9 | **9.1** | 48.6 | 9.6 | 12.7 | 26.3 |
| As-of-right taxi licences in Victoria (2014) | Urban transport fares | 11.3 | 35.8 | 36.1 | 8.3 | 35.8 | 8.3 | **8.3** | 12.1 |
| Ride-share legalisation (2015 to 2018) | Urban transport fares | 8.6 | 36.2 | 36.4 | 8.2 | 36.2 | 8.3 | **5.0** | 9.8 |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | Automotive fuel | — | 38.6 | 38.9 | **6.7** | 38.7 | 7.2 | 8.6 | 12.1 |
| National Energy Customer Framework adoption (ACT, TAS 2012; SA 2013; NSW 2013; QLD 2015) | Electricity | — | 40.9 | 41.2 | **7.4** | 41.0 | 8.0 | 11.5 | 17.7 |
| CTP insurance reforms (NSW 2017; SA price competition 2019; ACT 2020) | Insurance | — | 70.0 | 70.7 | 7.8 | 70.1 | 8.0 | **4.7** | 9.9 |
| Pharmacists treat uncomplicated UTIs (QLD 2020, NSW 2023, five more 2023-24) | Medical and hospital services | — | 39.1 | 39.4 | **7.1** | 39.1 | 7.7 | 8.4 | 12.9 |
| Pharmacists treat uncomplicated UTIs (QLD 2020, NSW 2023, five more 2023-24) | Pharmaceutical products | — | 39.1 | 39.4 | **7.1** | 39.1 | 7.7 | 8.4 | 12.9 |
| 2022 building code adoption (staggered 2023-2025) | New dwelling purchase by owner-occupiers | — | 45.3 | 45.6 | 6.5 | 45.3 | **6.5** | 9.6 | 15.7 |
| East-coast gas price cap (December 2022) and Gas Market Code (July 2023) | Gas and other household fuels | — | 46.5 | 46.6 | **9.6** | 46.5 | **9.6** | 10.3 | 26.1 |

### 3.9 Prices: placebo families

| Reform | CPI class | Family | Draws | Two-way | Saturated | Imputation | Synthetic DiD | Smallest RMS |
|---|---|---|---|---|---|---|---|---|
| Northern Territory container deposit scheme (2012) | Waters, soft drinks and juices | Placebo classes | 40 | -0.9 / 16.3 | -0.4 / 7.8 | -0.4 / 7.8 | +0.8 / 7.5 | Synthetic DiD |
|  |  | Placebo states | 6 | +4.1 / 4.3 | -0.0 / 1.1 | -0.0 / 1.1 | -2.7 / 2.9 | Saturated |
|  |  | Fake dates | 5 | +10.5 / 10.5 | +5.3 / 5.3 | +5.3 / 5.3 | +4.0 / 5.3 | Gen. synth. |
| Northern Territory container deposit scheme (2012) | Beer | Placebo classes | 40 | -0.9 / 16.3 | -0.4 / 7.8 | -0.4 / 7.8 | +0.7 / 7.5 | Synthetic DiD |
|  |  | Placebo states | 6 | +10.6 / 10.9 | +0.0 / 3.1 | +0.0 / 3.1 | +2.6 / 2.9 | Gen. synth. |
|  |  | Fake dates | 5 | +7.4 / 7.5 | +2.4 / 3.0 | +2.4 / 3.0 | +3.8 / 4.5 | Saturated |
| National Quality Framework for childcare (2012): the WA stagger | Child care | Placebo classes | 40 | +1.1 / 9.1 | -0.3 / 6.0 | -0.3 / 6.0 | +0.2 / 1.8 | Synthetic DiD |
|  |  | Fake dates | 5 | -17.9 / 24.7 | -2.2 / 3.3 | -2.2 / 3.3 | +2.5 / 3.9 | Saturated |
| Retail energy price deregulation (SA 2013, NSW 2014, south-east Queensland 2016) | Electricity | Placebo classes | 40 | +2.6 / 17.3 | +0.1 / 3.2 | +0.1 / 3.4 | -0.2 / 4.5 | Saturated |
|  |  | Placebo states | 20 | +26.6 / 26.7 | -5.1 / 7.2 | -4.1 / 7.6 | -9.9 / 11.8 | Saturated |
|  |  | Fake dates | 6 | +38.3 / 38.5 | +10.4 / 11.0 | +10.2 / 10.9 | +15.9 / 17.8 | Imputation |
| As-of-right taxi licences in Victoria (2014) | Urban transport fares | Placebo classes | 40 | +1.0 / 12.6 | -0.3 / 2.9 | -0.3 / 2.9 | -0.1 / 2.9 | Synthetic DiD |
|  |  | Placebo states | 7 | +9.8 / 11.4 | +0.0 / 6.8 | +0.0 / 6.8 | +0.3 / 2.4 | Synthetic DiD |
|  |  | Fake dates | 7 | +3.8 / 4.8 | -2.1 / 2.5 | -2.1 / 2.5 | +0.7 / 1.7 | Synthetic DiD |
| Ride-share legalisation (2015 to 2018) | Urban transport fares | Placebo classes | 40 | +0.6 / 12.8 | +0.1 / 2.9 | +0.1 / 2.9 | -0.5 / 1.8 | Synthetic DiD |
|  |  | Fake dates | 8 | +4.9 / 5.5 | -1.2 / 2.2 | -0.1 / 1.7 | +0.2 / 1.1 | Synthetic DiD |
| Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021) | Automotive fuel | Placebo classes | 40 | -1.2 / 13.7 | +0.6 / 2.4 | +0.6 / 2.6 | -0.3 / 3.1 | Saturated |
|  |  | Fake dates | 9 | -3.9 / 5.5 | +0.1 / 0.7 | +0.1 / 0.6 | -1.4 / 1.9 | Imputation |
| National Energy Customer Framework adoption (ACT, TAS 2012; SA 2013; NSW 2013; QLD 2015) | Electricity | Placebo classes | 40 | +2.8 / 14.7 | -0.2 / 2.6 | -0.2 / 2.8 | -0.3 / 4.0 | Saturated |
|  |  | Fake dates | 5 | +30.0 / 30.3 | +1.6 / 2.8 | +0.7 / 2.4 | +13.7 / 14.4 | Imputation |
| CTP insurance reforms (NSW 2017; SA price competition 2019; ACT 2020) | Insurance | Placebo classes | 40 | -0.3 / 24.7 | +0.2 / 2.8 | +0.2 / 2.8 | +0.5 / 1.7 | Synthetic DiD |
|  |  | Placebo states | 20 | +20.1 / 20.2 | +0.4 / 2.2 | +0.0 / 2.3 | +0.5 / 1.4 | Synthetic DiD |
|  |  | Fake dates | 10 | +15.7 / 15.9 | -1.0 / 1.9 | -1.3 / 2.1 | +1.4 / 2.9 | Saturated |
| Pharmacists treat uncomplicated UTIs (QLD 2020, NSW 2023, five more 2023-24) | Medical and hospital services | Placebo classes | 40 | -0.2 / 13.8 | +0.1 / 2.5 | +0.1 / 2.7 | -0.1 / 2.9 | Saturated |
|  |  | Fake dates | 13 | +21.0 / 22.5 | +0.0 / 0.2 | -0.0 / 0.3 | +2.4 / 2.9 | Saturated |
| Pharmacists treat uncomplicated UTIs (QLD 2020, NSW 2023, five more 2023-24) | Pharmaceutical products | Placebo classes | 40 | +0.1 / 13.8 | +0.1 / 2.5 | +0.1 / 2.7 | -0.1 / 3.0 | Saturated |
|  |  | Fake dates | 13 | -3.7 / 4.2 | -0.4 / 0.7 | -0.5 / 0.8 | -1.4 / 1.8 | Saturated |
| 2022 building code adoption (staggered 2023-2025) | New dwelling purchase by owner-occupiers | Placebo classes | 40 | +2.3 / 16.1 | -0.2 / 2.3 | -0.2 / 2.3 | +0.3 / 3.4 | Saturated |
|  |  | Fake dates | 11 | +5.3 / 7.4 | +0.6 / 1.3 | +0.6 / 1.2 | +1.1 / 1.9 | Imputation |
| East-coast gas price cap (December 2022) and Gas Market Code (July 2023) | Gas and other household fuels | Placebo classes | 40 | +2.5 / 16.6 | -0.6 / 3.4 | -0.6 / 3.4 | +0.5 / 3.6 | Saturated |
|  |  | Fake dates | 10 | +13.4 / 13.8 | +11.2 / 11.4 | +11.2 / 11.4 | +0.7 / 3.7 | Synthetic DiD |

## 4. Use in Phase 5 (design choice, before any re-estimation)

| Reform or family | Proposed primary layer | Why |
|---|---|---|
| Heavy Vehicle National Law; Victorian taxi licences; Legal Profession Uniform Law | Saturated fixed effects | Largest reductions; single adoption date. For taxis, report the placebo-state spread too: the own-class check is noisier than placebo industries suggest |
| Ride-share legalisation | Saturated, with imputation as a check | Staggered; imputation is robust to effects that change over time but loses about 0.4 points |
| Childcare NQF | Synthetic DiD | One comparison state; industry × year effects add WA's noise |
| Perth weeknight trading | Saturated for entries; synthetic DiD for exits | Layer ranking differs by outcome |
| Automatic mutual recognition | Imputation; generalised synthetic control as a check | Staggered; few placebos; COVID years |
| Fuel price reporting (new) | Saturated price model (class × quarter, city × quarter); saturated for fuel retailer entry and exit | Smallest error in every family; no systematic error at fake dates |
| E-conveyancing, 2022 building code, VET entitlements, NDIS Commission, CTP (new) | Saturated (business counts); for CTP prices, synthetic DiD | Smallest RMS in most families. Imputation is unstable in late staggered cohorts, where few untreated cells remain to fit the class × year effects (one fuel placebo gave −24) |
| Energy customer framework; retail energy deregulation | Saturated price model with a pre-trend check | Business counts infeasible; electricity prices show pre-reform drift at fake dates |
| East-coast gas interventions | Not with this comparison | WA and NT gas prices do not track the east coast before 2022 (fake-date error +11) |

These are design-stage choices, made without seeing any treated post-reform outcome. Each Phase 5 plan should still state its layer before unblinding (forward plan §7).

## 5. Limits

- **Few own-class draws.** Placebo states and fake dates give 5–20 draws; their spreads have sampling errors of 15–30%. They are used to detect bias and gross differences, not to rank close layers.
- **Fake dates use earlier years.** CABEE starts in 2007-08 (NT 2009-10), so fake dates for early reforms are few or none (e.g. none for the childcare framework or VET entitlements).
- **Placebo states need states that never adopted.** Staggered families that every state adopted (pharmacist prescribing, the 2022 building code, the NDIS Commission) have no placebo states.
- **Prices are city averages.** A capital-city CPI class mixes the reform's effect with everything else in the class (e.g. CTP inside Insurance, GP fees inside Medical and hospital services).
- **Small differences are noise.** MDEs within about 10% of each other should be treated as equal (sampling error of the standard deviation with 40 placebos).
