# Confounder scan for the Phase 5 evaluations

**Date:** 18 October 2026. **Status:** not pre-registered. It was run after the registered results were seen, so it adds caveats and changes no verdict. Item 2 of the [due-diligence plan](due_diligence.md).

**Code:** `alicia/analyses/phase5/confounders.py`, a post-hoc stage of both Phase 5 specifications. **Output:** `analyses/phase5/{reevaluations,new_families}/confounders.json`. Each evaluation file carries a one-line summary in its caveats.

## 1. What the scan does

1. **Register overlap.** It uses no outcome data, so it can run before unblinding.
   - **Looks for:** other register records that commenced from a year before an evaluation's window to its end, in a treated state, a comparison state, or nationally. A record counts if it touches the same ANZSIC class, group, subdivision or division as the outcome, or names the same CPI class.
   - **Grades:**
     - *High:* a close match (same class or group, or the same CPI class) in a treated state.
     - *Medium:* a looser match in a treated state, or a close match in a comparison state, which moves the comparison instead.
     - *Low:* national changes and division-level matches. National changes hit every state, so period effects absorb them unless exposure differs. These are listed in the JSON only.
2. **Timing.** It uses outcome data.
   - **Series:** for each cohort and treated state, the treated series' gap against the comparison states. Business counts are also netted against each state's other industries, as the saturated model does. Prices are already relative to All groups.
   - **Test:** each period-to-period step is divided by the spread of pre-reform steps. A step of 3 or more spreads outside the reform period (or the one after) is flagged.
   - **Limits:** it shows *when* a series moved, not why. Annual business counts give few pre-reform steps, so the test is weak there and impossible with fewer than three.

The register holds only the 171 changes recorded so far. Cowork's desk search (guide step 4) covers what the register lacks: fare and fee changes, large firm entries and exits, subsidies.

## 2. What it found

| Evaluation | Register overlaps (high, medium) | Timing | Bearing on the result |
|---|---|---|---|
| Victorian taxi licensing | Heavy Vehicle National Law, Feb 2014 (the year before; Victoria and most comparison states alike) | Melbourne fares: largest step 2015-Q1 (−11.9 × usual), none at the reform | Confirms the earlier post-unblinding check: the fares fall is not the taxi reform. Entry and exits show no large move |
| Legal Profession Uniform Law | **NSW e-conveyancing mandate, May 2018: same class (legal services), treated state, last year of the window** | Victorian exits: largest step 2017-18 (−3.0) | The last window year is contaminated in NSW. The step 3 window variant drops it |
| Retail energy deregulation | **National Energy Customer Framework, adopted in SA on the same day, NSW the year before, Queensland the year before**; ACT and Tasmania adopted 2012; Tasmania full retail contestability 2014 | NSW and Queensland: largest steps 3 years after the reform | Two policies moved together in both groups. Consistent with the failed pre-trend test (not identified) |
| Heavy Vehicle National Law | Taxi and ride-share reforms in every treated state, 2014–2017 (same subdivision, road transport; they affect taxis, not freight) | NSW entries: largest step 2015-16 (+3.5), the year NSW legalised ride-share; Victorian exits 2015-16 (−3.6) | Taxis are one class among about 430 in each state's comparison, so the effect is small but worth a variant excluding taxis. Verdict unchanged |
| Perth trading hours | Comparison-state changes in the same retail classes: NSW Boxing Day trading (2015), Queensland trading hours (2017), container deposit schemes (NT 2012, NSW 2017, ACT 2018) | Not testable (2 pre-reform years) | These move the comparison in the later window years. The step 3 window variants show whether the result depends on them |
| NT container deposits | Comparison-state alcohol laws naming the beer class (NSW lockout 2014, Queensland 2016) | Darwin beer: largest step 2013-Q2 (−4.1) | Already not identified |
| Ride-share legalisation | None above low | Fares: Brisbane −5.0 in 2017-Q1; Sydney and Canberra +3.8 and +3.5 in 2015-Q1, before the reform. Entries: large steps at the reform with opposite signs (NSW −4.5, Victoria +5.4) | Public transport fare changes are a candidate for the price steps (to check, as in Melbourne). Already not identified |
| Fuel price reporting | None above low | Prices: Tasmania −4.1 at its reform quarter (2020-Q3, during COVID); SA +4.5 at its reform quarter (2021-Q1); NSW +3.6 in 2019-Q2 | The two largest moves are at the reform but in opposite directions, and the TAS one falls in COVID. They may explain why the estimators disagree; step 3 drops each state in turn |
| E-conveyancing | Engineer and building-practitioner registration (NSW, Victoria, 2021; same subdivision, different class) | No large move | Little concern |
| Childcare NQF | None | No large move | Clean |

**What it changes:**
- **No verdict changes.** Every evaluation now records its concurrent changes as a caveat.
- **Robustness:** three findings feed the robustness stage (item 3):
  - drop NSW 2017-18 from the uniform law;
  - drop each state from fuel;
  - drop the later window years from Perth trading hours.
- **Questions for Cowork** (guide step 4):
  - public transport fare changes in Brisbane (early 2017) and Sydney and Canberra (early 2015);
  - what moved fuel prices in Adelaide in 2021-Q1 and Hobart in 2020-Q3.

## 3. Using it before unblinding

New specifications should run the scan blind, at the design stage:

```
uv run python analyses/phase5/confounders.py --spec <id> --blind
```

This writes `confounders_blind.json`. The timing part then covers only pre-reform periods, so it shows pre-reform jumps without revealing any result. The plan should list each high- or medium-relevance overlap and say how the design handles it before the registered run.

## 4. Full tables

### Mandatory fuel price reporting (NSW 2016, NT 2017, QLD 2018, TAS 2020, SA 2021)

No other register change of high or medium relevance in or just before the window.

Plus 4 of low relevance (national, or a division-level match), listed in confounders.json.

| Outcome | State | Reform period | Step there (× pre-reform spread) | Largest step (period, × spread) | Verdict |
|---|---|---|---|---|---|
| price-automotive-fuel | NSW | 2016-Q3 | 2016-Q3: -1.6, 2016-Q4: +0.1 | 2019-Q2: +3.6 | largest move after the reform period |
| price-automotive-fuel | NT | 2017-Q4 | 2017-Q4: +0.3, 2018-Q1: +1.5 | 2020-Q2: +2.6 | no large move |
| price-automotive-fuel | QLD | 2018-Q4 | 2018-Q4: -2.1, 2019-Q1: +0.7 | 2019-Q2: +2.2 | no large move |
| price-automotive-fuel | TAS | 2020-Q3 | 2020-Q3: -4.1, 2020-Q4: -0.2 | 2020-Q3: -4.1 | largest move at the reform |
| price-automotive-fuel | SA | 2021-Q1 | 2021-Q1: +4.5, 2021-Q2: -2.0 | 2021-Q1: +4.5 | largest move at the reform |
| entries | NSW | 2016-17 | 2016-17: +2.1, 2017-18: -1.1 | 2016-17: +2.1 | no large move |
| entries | NT | 2017-18 | 2017-18: +0.4, 2018-19: +0.8 | 2019-20: -1.8 | no large move |
| entries | QLD | 2018-19 | 2018-19: -1.5, 2019-20: -0.2 | 2018-19: -1.5 | no large move |
| entries | TAS | 2020-21 | 2020-21: -0.8, 2021-22: +0.8 | 2018-19: -1.6 | no large move |
| entries | SA | 2020-21 | 2020-21: -0.9, 2021-22: +0.7 | 2022-23: -3.1 | largest move after the reform period |
| exits | NSW | 2016-17 | 2016-17: -0.9, 2017-18: +1.1 | 2014-15: -1.4 | no large move |
| exits | NT | 2017-18 | 2017-18: +0.3, 2018-19: +0.2 | 2017-18: +0.3 | no large move |
| exits | QLD | 2018-19 | 2018-19: -1.5, 2019-20: +2.2 | 2019-20: +2.2 | no large move |
| exits | TAS | 2020-21 | 2020-21: +0.4, 2021-22: -0.1 | 2019-20: -2.1 | no large move |
| exits | SA | 2020-21 | 2020-21: +0.4, 2021-22: -2.8 | 2022-23: +3.2 | largest move after the reform period |

Already listed in the records: crude oil and terminal gate price movements, temporary halving of fuel excise (30 Mar to 28 Sep 2022), COVID-19 demand collapse 2020 (`nsw-fuel-price-reporting-2016`); crude oil and terminal gate price movements, temporary halving of fuel excise (30 Mar to 28 Sep 2022), COVID-19 demand collapse 2020 (`nt-fuel-price-reporting-2017`); crude oil and terminal gate price movements, temporary halving of fuel excise (30 Mar to 28 Sep 2022), COVID-19 demand collapse 2020 (`qld-fuel-price-reporting-2018`); crude oil and terminal gate price movements, temporary halving of fuel excise (30 Mar to 28 Sep 2022), COVID-19 demand collapse 2020 (`tas-fuel-price-reporting-2020`); crude oil and terminal gate price movements, temporary halving of fuel excise (30 Mar to 28 Sep 2022), COVID-19 demand collapse 2020 (`sa-fuel-price-reporting-2021`)

### Mandatory electronic conveyancing (NSW 2018, WA 2018, VIC 2019, SA 2020, QLD 2023)

| Relevance | Other change | Where | Date | Relation | Timing | Outcomes |
|---|---|---|---|---|---|---|
| medium | Design and Building Practitioners Act registration scheme (NSW) (`nsw-design-building-practitioners-2021`) | treated state (NSW) | 2021-07-01 | same subdivision | in window | entries, exits |
| medium | Professional engineers registration scheme (Victoria) (`vic-engineers-registration-2021`) | treated state (VIC) | 2021-07-01 | same subdivision | in window | entries, exits |

Plus 3 of low relevance (national, or a division-level match), listed in confounders.json.

| Outcome | State | Reform period | Step there (× pre-reform spread) | Largest step (period, × spread) | Verdict |
|---|---|---|---|---|---|
| entries | NSW | 2017-18 | 2017-18: +0.2, 2018-19: +1.2 | 2015-16: -2.2 | no large move |
| entries | WA | 2018-19 | 2018-19: -0.6, 2019-20: -1.4 | 2019-20: -1.4 | no large move |
| entries | VIC | 2019-20 | 2019-20: -0.6, 2020-21: -0.4 | 2021-22: -2.0 | no large move |
| entries | SA | 2020-21 | 2020-21: -1.2, 2021-22: -0.2 | 2018-19: +1.4 | no large move |
| entries | QLD | 2022-23 | 2022-23: -0.3, 2023-24: -0.0 | 2024-25: -0.6 | no large move |
| exits | NSW | 2017-18 | 2017-18: -0.9, 2018-19: +1.0 | 2016-17: +1.1 | no large move |
| exits | WA | 2018-19 | 2018-19: -0.5, 2019-20: +1.3 | 2021-22: -1.8 | no large move |
| exits | VIC | 2019-20 | 2019-20: +0.9, 2020-21: -0.8 | 2017-18: -1.8 | no large move |
| exits | SA | 2020-21 | 2020-21: -0.3, 2021-22: -0.8 | 2019-20: -0.9 | no large move |
| exits | QLD | 2022-23 | 2022-23: +0.3, 2023-24: -0.6 | 2020-21: -0.6 | no large move |

Already listed in the records: housing market swings and interest rate changes, COVID-19 property market 2020-21 (`nsw-e-conveyancing-mandate-2018`); housing market swings and interest rate changes, COVID-19 property market 2020-21 (`wa-e-conveyancing-mandate-2018`); housing market swings and interest rate changes, COVID-19 property market 2020-21 (`vic-e-conveyancing-mandate-2019`); housing market swings and interest rate changes, COVID-19 property market 2020-21 (`sa-e-conveyancing-mandate-2020`); housing market swings and interest rate changes, COVID-19 property market 2020-21 (`qld-e-conveyancing-mandate-2023`)

### Perth retail trading hours (2010 weeknights, 2012 Sundays): re-evaluation with saturated effects

| Relevance | Other change | Where | Date | Relation | Timing | Outcomes |
|---|---|---|---|---|---|---|
| medium | Container deposit scheme (Northern Territory) (`nt-cds-2012`) | comparison state (NT) | 2012-01-03 | same class | in window | entries, exits |
| medium | Statewide Boxing Day trading (NSW) (`nsw-boxing-day-2015`) | comparison state (NSW) | 2015-11-19 | same class | in window | entries, exits |
| medium | Standardised and extended trading hours (Queensland) (`qld-trading-hours-2017`) | comparison state (QLD) | 2017-08-31 | same class | in window | entries, exits |
| medium | Return and Earn container deposit scheme (NSW) (`nsw-cds-2017`) | comparison state (NSW) | 2017-12-01 | same class | in window | entries, exits |
| medium | Container deposit scheme (ACT) (`act-cds-2018`) | comparison state (ACT) | 2018-06-30 | same class | in window | entries, exits |

Plus 9 of low relevance (national, or a division-level match), listed in confounders.json.

| Outcome | State | Reform period | Step there (× pre-reform spread) | Largest step (period, × spread) | Verdict |
|---|---|---|---|---|---|
| entries | WA | 2010-11 | — | — | fewer than 3 pre-reform steps |
| exits | WA | 2010-11 | — | — | fewer than 3 pre-reform steps |

Already listed in the records: growth of online retail, mining boom/bust in WA, COVID-19 2020-21 (`wa-trading-hours-weeknight-2010`); growth of online retail, mining boom/bust in WA, COVID-19 2020-21 (`wa-trading-hours-sunday-2012`)

### National Quality Framework for childcare (2012): re-evaluation with synthetic DiD

No other register change of high or medium relevance in or just before the window.

| Outcome | State | Reform period | Step there (× pre-reform spread) | Largest step (period, × spread) | Verdict |
|---|---|---|---|---|---|
| entries | NSW | 2011-12 | 2011-12: +0.5 | 2011-12: +0.5 | no large move |
| entries | VIC | 2011-12 | 2011-12: +1.0 | 2011-12: +1.0 | no large move |
| entries | QLD | 2011-12 | 2011-12: -0.6 | 2009-10: +1.6 | no large move |
| entries | SA | 2011-12 | 2011-12: +0.8 | 2010-11: -1.0 | no large move |
| entries | TAS | 2011-12 | 2011-12: -0.3 | 2010-11: +1.5 | no large move |
| entries | ACT | 2011-12 | 2011-12: +0.5 | 2010-11: -1.8 | no large move |
| entries | NT | 2011-12 | — | — | fewer than 3 pre-reform steps |
| exits | NSW | 2011-12 | 2011-12: +1.0 | 2009-10: +1.0 | no large move |
| exits | VIC | 2011-12 | 2011-12: +0.7 | 2009-10: -0.8 | no large move |
| exits | QLD | 2011-12 | 2011-12: +1.7 | 2011-12: +1.7 | no large move |
| exits | SA | 2011-12 | 2011-12: +1.2 | 2011-12: +1.2 | no large move |
| exits | TAS | 2011-12 | 2011-12: +0.5 | 2009-10: +0.7 | no large move |
| exits | ACT | 2011-12 | 2011-12: +0.7 | 2011-12: +0.7 | no large move |
| exits | NT | 2011-12 | — | — | fewer than 3 pre-reform steps |
| price-child-care | NSW | 2012-Q1 | 2012-Q1: +0.4, 2012-Q2: -0.3 | 2011-Q3: -2.0 | no large move |
| price-child-care | VIC | 2012-Q1 | 2012-Q1: +2.2, 2012-Q2: -0.2 | 2012-Q1: +2.2 | no large move |
| price-child-care | QLD | 2012-Q1 | 2012-Q1: +0.7, 2012-Q2: -0.1 | 2011-Q3: -2.2 | no large move |
| price-child-care | SA | 2012-Q1 | 2012-Q1: +1.7, 2012-Q2: +0.4 | 2012-Q1: +1.7 | no large move |
| price-child-care | TAS | 2012-Q1 | 2012-Q1: +0.6, 2012-Q2: +0.1 | 2011-Q1: +1.2 | no large move |
| price-child-care | ACT | 2012-Q1 | 2012-Q1: +2.6, 2012-Q2: +1.0 | 2012-Q1: +2.6 | no large move |
| price-child-care | NT | 2012-Q1 | 2012-Q1: +0.8, 2012-Q2: +1.1 | 2011-Q3: -2.4 | no large move |

Already listed in the records: Child Care Benefit/Rebate changes 2008-2018, Child Care Subsidy from 2 Jul 2018 (`cth-nqf-childcare-2012`); mining boom labour shortages in WA, Child Care Subsidy from 2 Jul 2018 (`wa-nqf-childcare-2012`)

### Heavy Vehicle National Law (2014): re-evaluation with saturated effects

| Relevance | Other change | Where | Date | Relation | Timing | Outcomes |
|---|---|---|---|---|---|---|
| medium | As-of-right taxi licences at a set annual fee (Victoria) (`vic-taxi-licensing-2014`) | treated state (VIC) | 2014-06-30 | same subdivision | in window | entries, exits |
| medium | Ride-sharing legalised and taxi fees cut (ACT) (`act-rideshare-2015`) | treated state (ACT) | 2015-10-30 | same subdivision | in window | entries, exits |
| medium | Ride-sharing legalised; point-to-point transport reform (NSW) (`nsw-rideshare-2015`) | treated state (NSW) | 2015-12-18 | same subdivision | in window | entries, exits |
| medium | Ride-sharing legalised with taxi reform package (SA) (`sa-rideshare-2016`) | treated state (SA) | 2016-07-01 | same subdivision | in window | entries, exits |
| medium | Ride-booking legalised (Queensland) (`qld-rideshare-2016`) | treated state (QLD) | 2016-09-05 | same subdivision | in window | entries, exits |
| medium | Ride-sourcing clarified as legal (Tasmania) (`tas-rideshare-2016`) | treated state (TAS) | 2016-09-06 | same subdivision | in window | entries, exits |
| medium | Commercial passenger vehicle reform legalising ride-share (Victoria) (`vic-rideshare-2017`) | treated state (VIC) | 2017-08-23 | same subdivision | in window | entries, exits |
| medium | Booked hire licences and booking entities (Queensland) (`qld-booked-hire-licences-2017`) | treated state (QLD) | 2017-10-01 | same subdivision | in window | entries, exits |

Plus 2 of low relevance (national, or a division-level match), listed in confounders.json.

| Outcome | State | Reform period | Step there (× pre-reform spread) | Largest step (period, × spread) | Verdict |
|---|---|---|---|---|---|
| entries | NSW | 2013-14 | 2013-14: +2.0, 2014-15: -2.4 | 2015-16: +3.5 | largest move after the reform period |
| entries | VIC | 2013-14 | 2013-14: +1.6, 2014-15: -1.2 | 2015-16: +3.0 | no large move |
| entries | QLD | 2013-14 | 2013-14: +1.1, 2014-15: -3.0 | 2014-15: -3.0 | largest move at the reform |
| entries | SA | 2013-14 | 2013-14: +1.3, 2014-15: -1.2 | 2015-16: +1.8 | no large move |
| entries | TAS | 2013-14 | 2013-14: -0.0, 2014-15: -0.4 | 2011-12: -1.2 | no large move |
| entries | ACT | 2013-14 | 2013-14: +1.1, 2014-15: -2.0 | 2014-15: -2.0 | no large move |
| exits | NSW | 2013-14 | 2013-14: -0.7, 2014-15: +0.5 | 2015-16: -0.7 | no large move |
| exits | VIC | 2013-14 | 2013-14: -1.3, 2014-15: +1.5 | 2015-16: -3.6 | largest move after the reform period |
| exits | QLD | 2013-14 | 2013-14: -0.8, 2014-15: -0.1 | 2016-17: -2.0 | no large move |
| exits | SA | 2013-14 | 2013-14: -0.2, 2014-15: +0.5 | 2015-16: -1.4 | no large move |
| exits | TAS | 2013-14 | 2013-14: +0.5, 2014-15: +0.2 | 2015-16: -3.0 | no large move |
| exits | ACT | 2013-14 | 2013-14: -0.4, 2014-15: +0.2 | 2012-13: +1.5 | no large move |

Already listed in the records: mining downturn 2013-16 (WA, QLD), chain-of-responsibility amendments 1 Oct 2018, fuel price falls 2014-15 (`act-heavy-vehicle-national-law-2014`); mining downturn 2013-16 (WA, QLD), chain-of-responsibility amendments 1 Oct 2018, fuel price falls 2014-15 (`nsw-heavy-vehicle-national-law-2014`); mining downturn 2013-16 (WA, QLD), chain-of-responsibility amendments 1 Oct 2018, fuel price falls 2014-15 (`qld-heavy-vehicle-national-law-2014`); mining downturn 2013-16 (WA, QLD), chain-of-responsibility amendments 1 Oct 2018, fuel price falls 2014-15 (`sa-heavy-vehicle-national-law-2014`); mining downturn 2013-16 (WA, QLD), chain-of-responsibility amendments 1 Oct 2018, fuel price falls 2014-15 (`tas-heavy-vehicle-national-law-2014`); mining downturn 2013-16 (WA, QLD), chain-of-responsibility amendments 1 Oct 2018, fuel price falls 2014-15 (`vic-heavy-vehicle-national-law-2014`)

### As-of-right taxi licences in Victoria (2014): re-evaluation with saturated effects

| Relevance | Other change | Where | Date | Relation | Timing | Outcomes |
|---|---|---|---|---|---|---|
| high | Heavy Vehicle National Law commences (Victoria) (`vic-heavy-vehicle-national-law-2014`) | treated state (VIC) | 2014-02-10 | same group | in the year before | entries, exits |
| medium | Heavy Vehicle National Law commences (ACT) (`act-heavy-vehicle-national-law-2014`) | comparison state (ACT) | 2014-02-10 | same group | in the year before | entries, exits |
| medium | Heavy Vehicle National Law commences (New South Wales) (`nsw-heavy-vehicle-national-law-2014`) | comparison state (NSW) | 2014-02-10 | same group | in the year before | entries, exits |
| medium | Heavy Vehicle National Law commences (Queensland) (`qld-heavy-vehicle-national-law-2014`) | comparison state (QLD) | 2014-02-10 | same group | in the year before | entries, exits |
| medium | Heavy Vehicle National Law commences (South Australia) (`sa-heavy-vehicle-national-law-2014`) | comparison state (SA) | 2014-02-10 | same group | in the year before | entries, exits |
| medium | Heavy Vehicle National Law commences (Tasmania) (`tas-heavy-vehicle-national-law-2014`) | comparison state (TAS) | 2014-02-10 | same group | in the year before | entries, exits |

Plus 1 of low relevance (national, or a division-level match), listed in confounders.json.

| Outcome | State | Reform period | Step there (× pre-reform spread) | Largest step (period, × spread) | Verdict |
|---|---|---|---|---|---|
| entries | VIC | 2014-15 | 2014-15: -0.4 | 2012-13: -0.4 | no large move |
| exits | VIC | 2014-15 | 2014-15: -1.0 | 2014-15: -1.0 | no large move |
| price-urban-transport-fares | VIC | 2014-Q3 | 2014-Q3: +0.1, 2014-Q4: +0.5 | 2015-Q1: -11.9 | largest move after the reform period |

Already listed in the records: Uber entry into Melbourne (unlawful UberX from 2014), maximum fare re-determination 19 May 2014 (`vic-taxi-licensing-2014`)

### Legal Profession Uniform Law (2015): re-evaluation with saturated effects

| Relevance | Other change | Where | Date | Relation | Timing | Outcomes |
|---|---|---|---|---|---|---|
| high | Mandatory electronic conveyancing (New South Wales) (`nsw-e-conveyancing-mandate-2018`) | treated state (NSW) | 2018-05-01 | same class | in window | entries, exits |

Plus 1 of low relevance (national, or a division-level match), listed in confounders.json.

| Outcome | State | Reform period | Step there (× pre-reform spread) | Largest step (period, × spread) | Verdict |
|---|---|---|---|---|---|
| entries | NSW | 2015-16 | 2015-16: -2.9, 2016-17: -0.8 | 2015-16: -2.9 | no large move |
| entries | VIC | 2015-16 | 2015-16: -0.5, 2016-17: +0.6 | 2017-18: -0.8 | no large move |
| exits | NSW | 2015-16 | 2015-16: -0.2, 2016-17: +1.3 | 2014-15: -1.9 | no large move |
| exits | VIC | 2015-16 | 2015-16: +0.6, 2016-17: +1.7 | 2017-18: -3.0 | largest move after the reform period |

Already listed in the records: COVID-19 2020-21, growth of legal tech and incorporated legal practices (`nsw-legal-profession-uniform-law-2015`); COVID-19 2020-21, growth of legal tech and incorporated legal practices (`vic-legal-profession-uniform-law-2015`)

### Ride-share legalisation (2015 to 2018): re-evaluation with saturated effects

No other register change of high or medium relevance in or just before the window.

Plus 1 of low relevance (national, or a division-level match), listed in confounders.json.

| Outcome | State | Reform period | Step there (× pre-reform spread) | Largest step (period, × spread) | Verdict |
|---|---|---|---|---|---|
| entries | ACT | 2015-16 | 2015-16: -0.3, 2016-17: -3.9 | 2016-17: -3.9 | largest move at the reform |
| entries | NSW | 2015-16 | 2015-16: -4.5, 2016-17: +1.0 | 2015-16: -4.5 | largest move at the reform |
| entries | SA | 2016-17 | 2016-17: +1.9 | 2015-16: -2.8 | no large move |
| entries | QLD | 2016-17 | 2016-17: +0.7 | 2015-16: -2.1 | no large move |
| entries | TAS | 2016-17 | 2016-17: -0.4 | 2015-16: -2.6 | no large move |
| entries | VIC | 2017-18 | 2017-18: +5.4 | 2017-18: +5.4 | largest move at the reform |
| entries | NT | 2017-18 | 2017-18: +1.6 | 2015-16: -2.6 | no large move |
| exits | ACT | 2015-16 | 2015-16: +0.4, 2016-17: -1.2 | 2014-15: -1.6 | no large move |
| exits | NSW | 2015-16 | 2015-16: -0.9, 2016-17: +0.6 | 2015-16: -0.9 | no large move |
| exits | SA | 2016-17 | 2016-17: -2.4 | 2016-17: -2.4 | no large move |
| exits | QLD | 2016-17 | 2016-17: +0.6 | 2016-17: +0.6 | no large move |
| exits | TAS | 2016-17 | 2016-17: -1.1 | 2016-17: -1.1 | no large move |
| exits | VIC | 2017-18 | 2017-18: +1.8 | 2017-18: +1.8 | no large move |
| exits | NT | 2017-18 | 2017-18: -0.6 | 2015-16: -1.3 | no large move |
| price-urban-transport-fares | ACT | 2015-Q4 | 2015-Q4: +0.9, 2016-Q1: -0.1 | 2015-Q1: +3.5 | largest move before the reform |
| price-urban-transport-fares | NSW | 2015-Q4 | 2015-Q4: -0.4, 2016-Q1: -0.6 | 2015-Q1: +3.8 | largest move before the reform |
| price-urban-transport-fares | SA | 2016-Q3 | 2016-Q3: -0.0, 2016-Q4: +0.0 | 2017-Q1: -0.7 | no large move |
| price-urban-transport-fares | QLD | 2016-Q3 | 2016-Q3: -0.3, 2016-Q4: -0.0 | 2017-Q1: -5.0 | largest move after the reform period |
| price-urban-transport-fares | TAS | 2016-Q3 | 2016-Q3: -0.4, 2016-Q4: -0.2 | 2016-Q1: +1.1 | no large move |
| price-urban-transport-fares | VIC | 2017-Q3 | 2017-Q3: -1.0, 2017-Q4: -0.1 | 2017-Q3: -1.0 | no large move |
| price-urban-transport-fares | NT | 2018-Q1 | 2018-Q1: +0.4, 2018-Q2: -0.1 | 2017-Q3: -1.4 | no large move |

Already listed in the records: COVID-19 travel collapse 2020-21, taxi licence compensation and per-trip levies, ABN registration by gig drivers inflates business counts (`act-rideshare-2015`); COVID-19 travel collapse 2020-21, taxi licence compensation and per-trip levies, ABN registration by gig drivers inflates business counts (`nsw-rideshare-2015`); COVID-19 travel collapse 2020-21, taxi licence compensation and per-trip levies, ABN registration by gig drivers inflates business counts (`sa-rideshare-2016`); COVID-19 travel collapse 2020-21, taxi licence compensation and per-trip levies, ABN registration by gig drivers inflates business counts (`qld-rideshare-2016`); COVID-19 travel collapse 2020-21, taxi licence compensation and per-trip levies, ABN registration by gig drivers inflates business counts (`tas-rideshare-2016`); COVID-19 travel collapse 2020-21, taxi licence compensation and per-trip levies, ABN registration by gig drivers inflates business counts, $2 (later $1) per-trip levy from 2018 (`vic-rideshare-2017`); COVID-19 travel collapse 2020-21, taxi licence compensation and per-trip levies, ABN registration by gig drivers inflates business counts (`nt-rideshare-2017`)

### Northern Territory container deposit scheme (2012): re-evaluation with drink prices

| Relevance | Other change | Where | Date | Relation | Timing | Outcomes |
|---|---|---|---|---|---|---|
| medium | Sydney CBD and Kings Cross lockout and last-drinks laws (NSW) (`nsw-lockout-2014`) | comparison state (NSW) | 2014-02-24 | names the same CPI class | in window | price-beer |
| medium | Tackling Alcohol-Fuelled Violence: 2am statewide trading cap (Queensland) (`qld-tafv-2016`) | comparison state (QLD) | 2016-07-01 | names the same CPI class | in window | price-beer |

| Outcome | State | Reform period | Step there (× pre-reform spread) | Largest step (period, × spread) | Verdict |
|---|---|---|---|---|---|
| price-soft-drinks | NT | 2012-Q1 | 2012-Q1: -1.5, 2012-Q2: +0.2 | 2013-Q1: -2.3 | no large move |
| price-beer | NT | 2012-Q1 | 2012-Q1: +3.7, 2012-Q2: -1.3 | 2013-Q2: -4.1 | largest move after the reform period |

Already listed in the records: plastic bag bans in the same period, COVID-19 2020-21, beverage excise and alcohol tax changes, 2013 Federal Court challenge (Mutual Recognition Act) (`nt-cds-2012`)

### Retail energy price deregulation (SA 2013, NSW 2014, SEQ 2016): re-evaluation with electricity prices

| Relevance | Other change | Where | Date | Relation | Timing | Outcomes |
|---|---|---|---|---|---|---|
| high | National Energy Customer Framework adopted (South Australia) (`sa-necf-2013`) | treated state (SA) | 2013-02-01 | names the same CPI class | in window | price-electricity |
| high | National Energy Customer Framework adopted (New South Wales) (`nsw-necf-2013`) | treated state (NSW) | 2013-07-01 | names the same CPI class | in the year before | price-electricity |
| high | National Energy Customer Framework adopted (Queensland) (`qld-necf-2015`) | treated state (QLD) | 2015-07-01 | names the same CPI class | in the year before | price-electricity |
| medium | National Energy Customer Framework adopted (ACT) (`act-necf-2012`) | comparison state (ACT) | 2012-07-01 | names the same CPI class | in the year before | price-electricity |
| medium | National Energy Customer Framework adopted (Tasmania) (`tas-necf-2012`) | comparison state (TAS) | 2012-07-01 | names the same CPI class | in the year before | price-electricity |
| medium | Full retail contestability for small electricity customers (Tasmania) (`tas-electricity-frc-2014`) | comparison state (TAS) | 2014-07-01 | names the same CPI class | in window | price-electricity |

| Outcome | State | Reform period | Step there (× pre-reform spread) | Largest step (period, × spread) | Verdict |
|---|---|---|---|---|---|
| price-electricity | SA | 2013-Q1 | 2013-Q1: -0.2, 2013-Q2: -1.1 | 2017-Q3: +2.3 | no large move |
| price-electricity | NSW | 2014-Q3 | 2014-Q3: -0.4, 2014-Q4: -0.0 | 2017-Q3: +3.3 | largest move after the reform period |
| price-electricity | QLD | 2016-Q3 | 2016-Q3: -0.0, 2016-Q4: -0.0 | 2018-Q3: -3.2 | largest move after the reform period |

Already listed in the records: network (poles and wires) price increases 2009-15, carbon price 1 Jul 2012-30 Jun 2014, wholesale price spike 2016-17, solar feed-in tariff schemes, NECF adoption on the same day (`sa-energy-price-deregulation-2013`); network (poles and wires) price increases 2009-15, carbon price 1 Jul 2012-30 Jun 2014, wholesale price spike 2016-17, solar feed-in tariff schemes, carbon tax repeal 1 Jul 2014 (same date) (`nsw-energy-price-deregulation-2014`); network (poles and wires) price increases 2009-15, carbon price 1 Jul 2012-30 Jun 2014, wholesale price spike 2016-17, solar feed-in tariff schemes (`qld-seq-energy-price-deregulation-2016`)

