# Rules and changes: sorting the register's reforms

*15 November 2026. Draft by Claude Code on the legislation branch, for the owner to check. Phase 2 of the [re-evaluation plan](plan_levers_reevaluation.md), under the owner's decisions 1 and 2 of 15 November 2026. Sorted by judgement from each item's own summary in the register; no law was reread for it. The same rows are in [`levers_rules_and_changes.csv`](levers_rules_and_changes.csv).*

## What this is for

Framework version 2.0 lists rules, each with its changes under it. Today 47 reforms count as rules, and 127 of the 144 changes link to no rule. This sorts all 191 reforms, so that each change can name its rule in the dedicated field the owner chose (decision 2), and each reform that tightened an existing restriction can sit under that restriction as a standing rule (decision 1).

Nothing here changes the site yet. The field belongs to the website session (requested in [`notes_for_other_branches.md`](notes_for_other_branches.md)). Until it exists, a reform with negative marks that is in force still counts as a rule. So the standing rules below are not added yet: added now, each would be counted twice.

## Summary

| Today | Sorted as | Items | What happens |
|---|---|---|---|
| Rule | Created its restriction | 25 | Stays a rule. Its marks are already against no rule |
| Rule | Changed a rule in the register | 10 | Becomes that rule's change |
| Rule | Tightened a rule not in the register | 12 | The standing rule is added as an existing setting, marked against the same market without it. The reform becomes its change, marked against what it replaced |
| Change | Changed a rule in the register | 66 | Names that rule |
| Change | Changed a rule not in the register | 45 | The rule is added if its marks are negative |
| Change | Removed a rule outright | 5 | Stays in the history |
| Change | Changed nothing that weighs on productivity | 25 | Stands alone: a rule marked positive, a funding program, competition law |
| Change | Not yet in force | 3 | Named when it starts |

### Requirements attached now (decision 3)

Three requirements quote the same law as a reform that stays a rule, but did not name it, so each rule was listed twice. They now name the item and are shown inside it:

- `cth-electricity-retail-code` inside the Default Market Offer (`cth-default-market-offer-2019`);
- `cth-sustainability-reporting` inside climate reporting (`cth-sustainability-reporting-2025`);
- `nsw-professional-engineer-registration` inside the NSW design and building practitioners scheme (`nsw-design-building-practitioners-2021`).

### Found on the way

- **Rules left out of the impact classes.** A requirement that names a change is shown inside it, and changes are not classed. So 8 requirements with negative marks are not in the impact classes: the primary duty under each state's model work health and safety law (7) and aged care provider registration. Under the dedicated field, each becomes a rule in its own row and the reform its change.
- **Coverage gaps in requirements.** Several standing rules exist as requirements in one state only. For example, education and care service approval is drafted for NSW only, and rail operator accreditation for NSW only. The rows below name them; drafting them belongs with the state batches ([`plan_states.md`](plan_states.md)).
- **A quote to recheck.** `cth-rba-interchange-standards` quotes a 0.300% credit card cap. The 2026 reform lowered domestic interchange caps, so the quote may be out of date (phase 3).

## Standing rules to add for the reforms that tightened them

| Rule to add (proposed id) | Reforms that become its changes |
|---|---|
| `act-new-home-building-standards` | `act-ncc-2022-2024` |
| `cth-small-amount-credit-cost-caps` | `cth-small-amount-credit-caps-2013` |
| `cth-vape-pharmacy-supply` | `cth-vaping-reforms-2024` |
| `nsw-new-home-building-standards` | `nsw-ncc-2022-2023` |
| `nt-new-home-building-standards` | `nt-ncc-2022-2023` |
| `qld-new-home-building-standards` | `qld-ncc-2022-2024` |
| `qld-pharmacy-ownership` | `qld-pharmacy-business-ownership-2025` |
| `qld-liquor-trading-hours` | `qld-tafv-2016` |
| `sa-new-home-building-standards` | `sa-ncc-2022-2024` |
| `tas-new-home-building-standards` | `tas-ncc-2022-2024` |
| `vic-new-home-building-standards` | `vic-ncc-2022-2024` |
| `wa-new-home-building-standards` | `wa-ncc-2022-2025` |

## Rules to add for changes, if their marks are negative

Many of these are requirements a state places on businesses: they belong with the state batches. Those that cap numbers or need a licence before trading score highest, so they come first.

| Rule to add (proposed id) | Changes |
|---|---|
| act-residential-transfer-duty (setting) | `act-commercial-conveyance-duty-2018`, `act-conveyance-duty-phase-out-2012` |
| act-ctp-insurer-licence (requirement) | `act-ctp-scheme-2020` |
| act-heavy-vehicle-national-law (requirement) | `act-heavy-vehicle-national-law-2014` |
| act-energy-retailer-authorisation (requirement) | `act-necf-2012` |
| act-pharmacist-prescribing-limits (setting) | `act-pharmacist-uti-2023` |
| act-point-to-point-licensing (requirement) | `act-rideshare-2015` |
| cth-card-surcharging-standard (requirement) | `cth-card-surcharging-2016` |
| food safety supervisor requirement in each state and territory (8 requirements) | `cth-food-safety-tools-2023` |
| cth-insolvent-trading-duty (requirement) | `cth-insolvency-safe-harbour-2017` |
| cth-merger-notification (requirement) | `cth-merger-reform-2026` |
| cth-offshore-safety-case (requirement) | `cth-nopsema-2012` |
| cth-whs-primary-duty (requirement) | `cth-whs-2012` |
| nsw-ctp-insurer-licence (requirement) | `nsw-ctp-scheme-2017` |
| nsw-heavy-vehicle-national-law (requirement) | `nsw-heavy-vehicle-national-law-2014` |
| nsw-energy-retailer-authorisation (requirement) | `nsw-necf-2013` |
| nsw-pharmacist-prescribing-limits (setting) | `nsw-pharmacist-uti-2023` |
| nt-pharmacist-prescribing-limits (setting) | `nt-pharmacist-uti-2024` |
| nt-point-to-point-licensing (requirement) | `nt-rideshare-2017` |
| qld-point-to-point-licensing (requirement) | `qld-booked-hire-licences-2017`, `qld-rideshare-2016` |
| qld-heavy-vehicle-national-law (requirement) | `qld-heavy-vehicle-national-law-2014` |
| qld-energy-retailer-authorisation (requirement) | `qld-necf-2015` |
| qld-pharmacist-prescribing-limits (setting) | `qld-pharmacist-uti-2020` |
| sa-ctp-insurer-licence (requirement) | `sa-ctp-price-competition-2019` |
| sa-heavy-vehicle-national-law (requirement) | `sa-heavy-vehicle-national-law-2014` |
| sa-energy-retailer-authorisation (requirement) | `sa-necf-2013` |
| sa-pharmacist-prescribing-limits (setting) | `sa-pharmacist-uti-2024` |
| sa-point-to-point-licensing (requirement) | `sa-rideshare-2016`, `sa-taxi-licence-reform-2025` |
| tas-gaming-machine-entitlements (setting) | `tas-future-gaming-market-2023` |
| tas-heavy-vehicle-national-law (requirement) | `tas-heavy-vehicle-national-law-2014` |
| tas-energy-retailer-authorisation (requirement) | `tas-necf-2012` |
| tas-pharmacist-prescribing-limits (setting) | `tas-pharmacist-uti-2024` |
| tas-point-to-point-licensing (requirement) | `tas-rideshare-2016` |
| vic-commercial-industrial-property-tax (setting) | `vic-commercial-industrial-property-tax-2024` |
| vic-gaming-machine-entitlements (setting) | `vic-gaming-venue-operator-2012` |
| vic-heavy-vehicle-national-law (requirement) | `vic-heavy-vehicle-national-law-2014` |
| vic-pharmacist-prescribing-limits (setting) | `vic-pharmacist-uti-2023` |
| vic-rail-operator-accreditation (requirement) | `vic-rail-safety-regulator-2019` |
| vic-point-to-point-licensing (requirement) | `vic-rideshare-2017` |
| wa-education-care-service-approval (requirement) | `wa-nqf-childcare-2012` |
| wa-point-to-point-licensing (requirement) | `wa-on-demand-transport-2019` |
| wa-pharmacist-prescribing-limits (setting) | `wa-pharmacist-uti-2023` |
| wa-rail-operator-accreditation (requirement) | `wa-rail-safety-national-law-2024` |

## The 47 reforms that count as rules

| Reform | Marks | Sorted as | Rule | Attach | Basis |
|---|---|---|---|---|---|
| `act-cds-2018` | -1 | Created its restriction |  |  | Created the state's container refund scheme. |
| `act-ncc-2022-2024` | -1 | Tightened a rule not in the register | `act-new-home-building-standards` |  | Raised the energy efficiency standards, or added livable housing, in the building code ACT already applied to new homes. Standing rule to add: the building code's energy and accessibility standards for new homes (ACT). |
| `act-ndis-commission-2019` | -1 | Changed a rule in the register | `cth-ndis-registered-provider` |  | Moved provider registration in the state to the NDIS Commission; the rule is the Commonwealth registration. |
| `cth-childcare-fee-growth-cap-2024` | -1 | Created its restriction |  |  | Created a fee growth limit for services that opt in. |
| `cth-coastal-trading-2012` | -3 | Changed a rule in the register | `cth-coastal-trading-licence` |  | Replaced the permit system with the licences the requirement covers. |
| `cth-default-market-offer-2019` | -1 | Created its restriction |  | `cth-electricity-retail-code` | Re-regulated standing offers after deregulation. The requirement on advertised prices is the same Code: attach it. |
| `cth-gas-market-code-2023` | -3 | Created its restriction |  | `cth-gas-market-code` | Created the price cap and Code; requirement already attached. |
| `cth-multi-employer-bargaining-2023` | -2 | Created its restriction |  |  | Created the supported and single-interest streams. A narrow low-paid stream existed from 2009: a judgement, to confirm. |
| `cth-pharmacy-location-rules-2018` | -2 | Changed a rule in the register | `cth-pharmacy-location-rules` |  | Removed the sunset on location rules the register already holds. |
| `cth-right-to-disconnect-2024` | -1 | Created its restriction |  |  | Created a new employee right. |
| `cth-same-job-same-pay-2023` | -2 | Created its restriction |  |  | Created labour-hire pay orders. |
| `cth-small-amount-credit-caps-2013` | -1 | Tightened a rule not in the register | `cth-small-amount-credit-cost-caps` |  | Replaced state caps with national ones. Standing rule to add: the cost caps on small amount credit contracts. |
| `cth-sustainability-reporting-2025` | -1 | Created its restriction |  | `cth-sustainability-reporting` | Created climate reporting. The requirement is the same law: attach it. |
| `cth-vaping-reforms-2024` | -2 | Tightened a rule not in the register | `cth-vape-pharmacy-supply` |  | Tightened the prescription model for nicotine vapes. Standing rule to add: vapes supplied only through pharmacies. |
| `nsw-cds-2017` | -1 | Created its restriction |  |  | Created the state's container refund scheme. |
| `nsw-design-building-practitioners-2021` | -2 | Created its restriction |  | `nsw-professional-engineer-registration` | Created the registration scheme. The engineer registration requirement is the same Act: attach it. |
| `nsw-ncc-2022-2023` | -2 | Tightened a rule not in the register | `nsw-new-home-building-standards` |  | Raised the energy efficiency standards, or added livable housing, in the building code NSW already applied to new homes. Standing rule to add: the building code's energy and accessibility standards for new homes (NSW). |
| `nsw-ndis-commission-2018` | -1 | Changed a rule in the register | `cth-ndis-registered-provider` |  | Moved provider registration in the state to the NDIS Commission; the rule is the Commonwealth registration. |
| `nsw-stra-2021` | -2 | Created its restriction |  |  | Created the code, register and night cap. |
| `nt-alcohol-minimum-unit-price-2018` | -2 | Created its restriction |  |  | Created a floor price as a licence condition. |
| `nt-cds-2012` | -1 | Created its restriction |  |  | Created the state's container refund scheme. |
| `nt-fuel-price-commitment-2026` | -2 | Created its restriction |  |  | Added a price commitment to the reporting scheme, whose marks add to zero. |
| `nt-ncc-2022-2023` | -2 | Tightened a rule not in the register | `nt-new-home-building-standards` |  | Raised the energy efficiency standards, or added livable housing, in the building code NT already applied to new homes. Standing rule to add: the building code's energy and accessibility standards for new homes (NT). |
| `nt-ndis-commission-2019` | -1 | Changed a rule in the register | `cth-ndis-registered-provider` |  | Moved provider registration in the state to the NDIS Commission; the rule is the Commonwealth registration. |
| `nt-takeaway-liquor-moratorium-2017` | -2 | Created its restriction |  |  | Created the moratorium. Check that it is still in force: the record notes later extensions were not checked. |
| `qld-cds-2018` | -1 | Created its restriction |  |  | Created the state's container refund scheme. |
| `qld-ncc-2022-2024` | -1 | Tightened a rule not in the register | `qld-new-home-building-standards` |  | Raised the energy efficiency standards, or added livable housing, in the building code Qld already applied to new homes. Standing rule to add: the building code's energy and accessibility standards for new homes (Qld). |
| `qld-ndis-commission-2019` | -1 | Changed a rule in the register | `cth-ndis-registered-provider` |  | Moved provider registration in the state to the NDIS Commission; the rule is the Commonwealth registration. |
| `qld-pharmacy-business-ownership-2025` | -2 | Tightened a rule not in the register | `qld-pharmacy-ownership` |  | Replaced Queensland's earlier ownership rules with a licensing regime. Standing rule to add: pharmacy ownership restrictions (Qld), as for the other states. Confirm the earlier law. |
| `qld-tafv-2016` | -1 | Tightened a rule not in the register | `qld-liquor-trading-hours` |  | Cut the latest trading time that licences already limited. Standing rule to add: liquor trading hours limits (Qld). |
| `sa-ncc-2022-2024` | -1 | Tightened a rule not in the register | `sa-new-home-building-standards` |  | Raised the energy efficiency standards, or added livable housing, in the building code SA already applied to new homes. Standing rule to add: the building code's energy and accessibility standards for new homes (SA). |
| `sa-ndis-commission-2018` | -1 | Changed a rule in the register | `cth-ndis-registered-provider` |  | Moved provider registration in the state to the NDIS Commission; the rule is the Commonwealth registration. |
| `tas-cds-2025` | -1 | Created its restriction |  |  | Created the state's container refund scheme. |
| `tas-ncc-2022-2024` | -2 | Tightened a rule not in the register | `tas-new-home-building-standards` |  | Raised the energy efficiency standards, or added livable housing, in the building code Tas already applied to new homes. Standing rule to add: the building code's energy and accessibility standards for new homes (Tas). |
| `tas-ndis-commission-2019` | -1 | Changed a rule in the register | `cth-ndis-registered-provider` |  | Moved provider registration in the state to the NDIS Commission; the rule is the Commonwealth registration. |
| `vic-cds-2023` | -1 | Created its restriction |  |  | Created the state's container refund scheme. |
| `vic-default-offer-2019` | -1 | Created its restriction |  |  | Re-regulated standing offers after deregulation. |
| `vic-engineers-registration-2021` | -2 | Created its restriction |  |  | Created the registration scheme. |
| `vic-fuel-price-commitment-2026` | -2 | Created its restriction |  |  | Added a price commitment to the reporting scheme, whose marks add to zero. |
| `vic-ncc-2022-2024` | -1 | Tightened a rule not in the register | `vic-new-home-building-standards` |  | Raised the energy efficiency standards, or added livable housing, in the building code Vic already applied to new homes. Standing rule to add: the building code's energy and accessibility standards for new homes (Vic). |
| `vic-ndis-commission-2019` | -1 | Changed a rule in the register | `cth-ndis-registered-provider` |  | Moved provider registration in the state to the NDIS Commission; the rule is the Commonwealth registration. |
| `vic-port-of-melbourne-lease-2016` | -1 | Created its restriction |  |  | Granted the operator's rights under the lease. The port was a public monopoly before: a judgement, to confirm. |
| `vic-short-stay-levy-2025` | -1 | Created its restriction |  |  | Created the levy. |
| `wa-cds-2020` | -1 | Created its restriction |  |  | Created the state's container refund scheme. |
| `wa-ncc-2022-2025` | -2 | Tightened a rule not in the register | `wa-new-home-building-standards` |  | Raised the energy efficiency standards, or added livable housing, in the building code WA already applied to new homes. Standing rule to add: the building code's energy and accessibility standards for new homes (WA). |
| `wa-ndis-commission-2020` | -1 | Changed a rule in the register | `cth-ndis-registered-provider` |  | Moved provider registration in the state to the NDIS Commission; the rule is the Commonwealth registration. |
| `wa-stra-register-2025` | -2 | Created its restriction |  |  | Created the register. |

## The 144 changes

| Change | Marks | Sorted as | Rule | Basis |
|---|---|---|---|---|
| `act-amr-2021` | 2 | Changed a rule in the register | act-occupational-licensing | Deemed interstate licences valid: a change to occupational licensing. |
| `act-health-practitioner-national-law-2010` | 3 | Changed a rule in the register | act-health-practitioner-registration | Made the national registration the requirement covers. |
| `act-whs-2012` | 2 | Changed a rule in the register | act-whs-primary-duty | Adopted the model law the requirement quotes. The requirement sits inside this change today, so it is left out of the impact classes. |
| `cth-aged-care-act-2025` | 1 | Changed a rule in the register | cth-aged-care-provider-registration | Made the registration the requirement covers. The requirement sits inside this change today, so it is left out of the impact classes. |
| `cth-biosecurity-act-2016` | 1 | Changed a rule in the register | cth-biosecurity-import-conditions | Replaced the law the requirement quotes. |
| `cth-card-surcharge-removal-2026` | 0 | Changed a rule in the register | cth-rba-interchange-standards; cth-card-surcharging-standard (to add) | Lowered the interchange caps and banned surcharges on the main cards. Check the requirement's quoted cap is current. |
| `cth-cdr-open-banking-2020` | 1 | Changed a rule in the register | cth-cdr-data-holder | Made the data-sharing rule the requirement covers. |
| `cth-company-tax-turnover-2016` | 0 | Changed a rule in the register | cth-income-tax | Changed the company tax rate. |
| `cth-dairy-code-2020` | 0 | Changed a rule in the register | cth-dairy-code | Made the Code the requirement covers. |
| `cth-dcv-national-system-2013` | 2 | Changed a rule in the register | cth-dcv-certificate-of-operation | Made the national certificate the requirement covers. |
| `cth-epbc-reform-2025` | 0 | Changed a rule in the register | cth-epbc-approval | Reforms the approval the requirement covers. |
| `cth-food-grocery-code-2025` | 0 | Changed a rule in the register | cth-food-grocery-code | Made the Code the requirement covers. |
| `cth-franchising-code-2025` | 0 | Changed a rule in the register | cth-franchising-code | Remade the Code the requirement covers. |
| `cth-horticulture-code-2017` | 0 | Changed a rule in the register | cth-horticulture-code | Made the Code the requirement covers. |
| `cth-industrial-chemicals-2020` | 1 | Changed a rule in the register | cth-industrial-chemical-introducer-registration | Made the registration the requirement covers. |
| `cth-instant-asset-write-off-2015` | 1 | Changed a rule in the register | cth-income-tax | Changed how income tax treats assets. |
| `cth-major-bank-levy-2017` | 0 | Changed a rule in the register | cth-major-bank-levy | Made the levy the requirement covers. |
| `cth-nqf-childcare-2012` | 0 | Changed a rule in the register | nsw-education-care-service-approval | Made the national approval the NSW requirement covers. The same requirement is not yet drafted for the other states. |
| `cth-petroleum-retail-repeal-2007` | 1 | Changed a rule in the register | cth-oil-code-terminal-gate-prices | Repealed the site limits and made the Oilcode the requirement covers. |
| `cth-rd-tax-incentive-2011` | 1 | Changed a rule in the register | cth-income-tax | A concession within income tax. |
| `cth-rd-tax-incentive-2021` | 1 | Changed a rule in the register | cth-income-tax | A concession within income tax. |
| `cth-sugar-code-2017` | 1 | Changed a rule in the register | cth-sugar-code-supply-contracts | Made the Code the requirement covers. |
| `cth-sydney-airport-slots-2025` | 1 | Changed a rule in the register | cth-sydney-airport-curfew-cap | Changed slot rules at the capped airport. |
| `cth-water-act-2008` | 0 | Changed a rule in the register | cth-water-market-rules | Made the market rules the requirement covers. |
| `nsw-amr-2021` | 2 | Changed a rule in the register | nsw-occupational-licensing | Deemed interstate licences valid: a change to occupational licensing. |
| `nsw-boxing-day-2015` | 1 | Changed a rule in the register | nsw-retail-trading-hours | Loosened trading hours. |
| `nsw-employment-zones-2023` | 2 | Changed a rule in the register | nsw-planning-zoning | Simplified zoning. |
| `nsw-energy-price-deregulation-2014` | 2 | Changed a rule in the register | cth-default-market-offer-2019 | Removed regulated prices; the Default Market Offer re-regulated them in 2019. |
| `nsw-health-practitioner-national-law-2010` | 3 | Changed a rule in the register | nsw-health-practitioner-registration | Made the national registration the requirement covers. |
| `nsw-legal-profession-uniform-law-2015` | 2 | Changed a rule in the register | nsw-occupational-licensing | Changed the licensing of lawyers. |
| `nsw-lockout-repeal-cbd-2020` | 1 | Changed a rule in the register | nsw-liquor-licence | Removed the lockout in the CBD; the 2014 lockout is no longer in force. |
| `nsw-lockout-repeal-kings-cross-2021` | 1 | Changed a rule in the register | nsw-liquor-licence | Removed the last lockout. |
| `nsw-rail-safety-national-law-2013` | 2 | Changed a rule in the register | nsw-rail-operator-accreditation | Made the national accreditation the requirement covers. |
| `nsw-rideshare-2015` | 3 | Changed a rule in the register | nsw-taxi-booking-service-authorisation | Legalised ride-share under the authorisation the requirement covers. |
| `nsw-small-bar-licence-2013` | 1 | Changed a rule in the register | nsw-liquor-licence | Added a licence type. |
| `nsw-transport-oriented-development-2024` | 2 | Changed a rule in the register | nsw-planning-zoning | Loosened zoning near stations. |
| `nsw-whs-2012` | 2 | Changed a rule in the register | nsw-whs-primary-duty | Adopted the model law the requirement quotes. The requirement sits inside this change today, so it is left out of the impact classes. |
| `nt-amr-2021` | 2 | Changed a rule in the register | nt-occupational-licensing | Deemed interstate licences valid: a change to occupational licensing. |
| `nt-health-practitioner-national-law-2010` | 3 | Changed a rule in the register | nt-health-practitioner-registration | Made the national registration the requirement covers. |
| `nt-whs-2012` | 2 | Changed a rule in the register | nt-whs-primary-duty | Adopted the model law the requirement quotes. The requirement sits inside this change today, so it is left out of the impact classes. |
| `qld-health-practitioner-national-law-2010` | 3 | Changed a rule in the register | qld-health-practitioner-registration | Made the national registration the requirement covers. |
| `qld-seq-energy-price-deregulation-2016` | 2 | Changed a rule in the register | cth-default-market-offer-2019 | As above, for south-east Queensland. |
| `qld-trading-hours-2017` | 2 | Changed a rule in the register | qld-retail-trading-hours | Set the trading hours the requirement covers. |
| `qld-whs-2012` | 2 | Changed a rule in the register | qld-whs-primary-duty | Adopted the model law the requirement quotes. The requirement sits inside this change today, so it is left out of the impact classes. |
| `sa-amr-2021` | 2 | Changed a rule in the register | sa-occupational-licensing | Deemed interstate licences valid: a change to occupational licensing. |
| `sa-energy-price-deregulation-2013` | 2 | Changed a rule in the register | cth-default-market-offer-2019 | As above, for South Australia. |
| `sa-health-practitioner-national-law-2010` | 3 | Changed a rule in the register | sa-health-practitioner-registration | Made the national registration the requirement covers. |
| `sa-trading-hours-2012` | 1 | Changed a rule in the register | sa-retail-trading-hours | Loosened trading hours. |
| `sa-trading-hours-2022` | 1 | Changed a rule in the register | sa-retail-trading-hours | Loosened trading hours. |
| `sa-whs-2013` | 2 | Changed a rule in the register | sa-whs-primary-duty | Adopted the model law the requirement quotes. The requirement sits inside this change today, so it is left out of the impact classes. |
| `tas-amr-2021` | 2 | Changed a rule in the register | tas-occupational-licensing | Deemed interstate licences valid: a change to occupational licensing. |
| `tas-health-practitioner-national-law-2010` | 3 | Changed a rule in the register | tas-health-practitioner-registration | Made the national registration the requirement covers. |
| `tas-whs-2013` | 2 | Changed a rule in the register | tas-whs-primary-duty | Adopted the model law the requirement quotes. The requirement sits inside this change today, so it is left out of the impact classes. |
| `vic-amr-2021` | 2 | Changed a rule in the register | vic-occupational-licensing | Deemed interstate licences valid: a change to occupational licensing. |
| `vic-business-insurance-duty-phase-out-2024` | 1 | Changed a rule in the register | vic-insurance-duty | Phases out the duty the setting covers. |
| `vic-energy-price-deregulation-2009` | 2 | Changed a rule in the register | vic-default-offer-2019 | Removed regulated prices; the Victorian Default Offer re-regulated them in 2019. |
| `vic-health-practitioner-national-law-2010` | 3 | Changed a rule in the register | vic-health-practitioner-registration | Made the national registration the requirement covers. |
| `vic-late-night-liquor-freeze-lifted-2023` | 2 | Changed a rule in the register | vic-liquor-licence | Ended a freeze on new late-night licences. |
| `vic-legal-profession-uniform-law-2015` | 2 | Changed a rule in the register | vic-occupational-licensing | Changed the licensing of lawyers. |
| `wa-amr-2022` | 2 | Changed a rule in the register | wa-occupational-licensing | Deemed interstate licences valid: a change to occupational licensing. |
| `wa-health-practitioner-national-law-2010` | 3 | Changed a rule in the register | wa-health-practitioner-registration | Made the national registration the requirement covers. |
| `wa-legal-profession-uniform-law-2022` | 2 | Changed a rule in the register | wa-occupational-licensing | Changed the licensing of lawyers. |
| `wa-small-bar-licence-2007` | 1 | Changed a rule in the register | wa-liquor-licence | Added a licence type. |
| `wa-trading-hours-sunday-2012` | 1 | Changed a rule in the register | wa-retail-trading-hours | Loosened trading hours. |
| `wa-trading-hours-weeknight-2010` | 1 | Changed a rule in the register | wa-retail-trading-hours | Loosened trading hours. |
| `wa-whs-2022` | 2 | Changed a rule in the register | wa-whs-primary-duty | Adopted the model law the requirement quotes. The requirement sits inside this change today, so it is left out of the impact classes. |
| `act-commercial-conveyance-duty-2018` | 3 | Changed a rule not in the register | act-residential-transfer-duty (setting) | Cut conveyance duty on commercial property. Rule to add: the ACT's conveyance duty, as for the other states. |
| `act-conveyance-duty-phase-out-2012` | 3 | Changed a rule not in the register | act-residential-transfer-duty (setting) | Began phasing out conveyance duty. Rule to add: the ACT's conveyance duty, which still applies at lower rates. |
| `act-ctp-scheme-2020` | 1 | Changed a rule not in the register | act-ctp-insurer-licence (requirement) | Rule to add: licensing and premium rules for CTP insurers (ACT). |
| `act-heavy-vehicle-national-law-2014` | 2 | Changed a rule not in the register | act-heavy-vehicle-national-law (requirement) | Applied the national law. Rule to add: heavy vehicle access permits and mass, dimension and fatigue rules (ACT). |
| `act-necf-2012` | 2 | Changed a rule not in the register | act-energy-retailer-authorisation (requirement) | Applied the National Energy Retail Law. Rule to add: hold a retailer authorisation from the AER (ACT). |
| `act-pharmacist-uti-2023` | 2 | Changed a rule not in the register | act-pharmacist-prescribing-limits (setting) | Widened what pharmacists may treat. Rule to add, if its marks are negative: the limits on who may prescribe in the state's medicines and poisons law (ACT). |
| `act-rideshare-2015` | 4 | Changed a rule not in the register | act-point-to-point-licensing (requirement) | Legalised ride-share. Rule to add: the state's licences for taxi, hire and booking services (ACT). |
| `cth-card-surcharging-2016` | 2 | Changed a rule not in the register | cth-card-surcharging-standard (requirement) | Limited surcharges to the cost of acceptance. Rule to add, if its marks are negative: the RBA's surcharging rules. |
| `cth-food-safety-tools-2023` | 0 | Changed a rule not in the register | food safety supervisor requirement in each state and territory (8 requirements) | Rule to add, if its marks are negative: a certified food safety supervisor and trained food handlers (Standard 3.2.2A). |
| `cth-insolvency-safe-harbour-2017` | 1 | Changed a rule not in the register | cth-insolvent-trading-duty (requirement) | Rule to add, if its marks are negative: directors' duty to prevent insolvent trading (Corporations Act s 588G). |
| `cth-merger-reform-2026` | 1 | Changed a rule not in the register | cth-merger-notification (requirement) | Made notification mandatory from 1 January 2026. Rule to add: notify the ACCC of acquisitions above the thresholds. |
| `cth-nopsema-2012` | 1 | Changed a rule not in the register | cth-offshore-safety-case (requirement) | Rule to add, if its marks are negative: an accepted safety case and environment plan. |
| `cth-whs-2012` | 2 | Changed a rule not in the register | cth-whs-primary-duty (requirement) | Rule to add: the primary duty under the Commonwealth Act (Commonwealth and self-insured employers). |
| `nsw-ctp-scheme-2017` | 0 | Changed a rule not in the register | nsw-ctp-insurer-licence (requirement) | Rule to add: licensing and premium rules for CTP insurers (NSW). |
| `nsw-heavy-vehicle-national-law-2014` | 2 | Changed a rule not in the register | nsw-heavy-vehicle-national-law (requirement) | Applied the national law. Rule to add: heavy vehicle access permits and mass, dimension and fatigue rules (NSW). |
| `nsw-necf-2013` | 2 | Changed a rule not in the register | nsw-energy-retailer-authorisation (requirement) | Applied the National Energy Retail Law. Rule to add: hold a retailer authorisation from the AER (NSW). |
| `nsw-pharmacist-uti-2023` | 2 | Changed a rule not in the register | nsw-pharmacist-prescribing-limits (setting) | Widened what pharmacists may treat. Rule to add, if its marks are negative: the limits on who may prescribe in the state's medicines and poisons law (NSW). |
| `nt-pharmacist-uti-2024` | 2 | Changed a rule not in the register | nt-pharmacist-prescribing-limits (setting) | Widened what pharmacists may treat. Rule to add, if its marks are negative: the limits on who may prescribe in the state's medicines and poisons law (NT). |
| `nt-rideshare-2017` | 3 | Changed a rule not in the register | nt-point-to-point-licensing (requirement) | Legalised ride-share. Rule to add: the state's licences for taxi, hire and booking services (NT). |
| `qld-booked-hire-licences-2017` | 2 | Changed a rule not in the register | qld-point-to-point-licensing (requirement) | Rule to add: Queensland's booked hire licences. |
| `qld-heavy-vehicle-national-law-2014` | 2 | Changed a rule not in the register | qld-heavy-vehicle-national-law (requirement) | Applied the national law. Rule to add: heavy vehicle access permits and mass, dimension and fatigue rules (Qld). |
| `qld-necf-2015` | 2 | Changed a rule not in the register | qld-energy-retailer-authorisation (requirement) | Applied the National Energy Retail Law. Rule to add: hold a retailer authorisation from the AER (Qld). |
| `qld-pharmacist-uti-2020` | 2 | Changed a rule not in the register | qld-pharmacist-prescribing-limits (setting) | Widened what pharmacists may treat. Rule to add, if its marks are negative: the limits on who may prescribe in the state's medicines and poisons law (Qld). |
| `qld-rideshare-2016` | 4 | Changed a rule not in the register | qld-point-to-point-licensing (requirement) | Legalised ride-share. Rule to add: the state's licences for taxi, hire and booking services (Qld). |
| `sa-ctp-price-competition-2019` | 3 | Changed a rule not in the register | sa-ctp-insurer-licence (requirement) | Rule to add: licensing of CTP insurers (SA). |
| `sa-heavy-vehicle-national-law-2014` | 2 | Changed a rule not in the register | sa-heavy-vehicle-national-law (requirement) | Applied the national law. Rule to add: heavy vehicle access permits and mass, dimension and fatigue rules (SA). |
| `sa-necf-2013` | 2 | Changed a rule not in the register | sa-energy-retailer-authorisation (requirement) | Applied the National Energy Retail Law. Rule to add: hold a retailer authorisation from the AER (SA). |
| `sa-pharmacist-uti-2024` | 2 | Changed a rule not in the register | sa-pharmacist-prescribing-limits (setting) | Widened what pharmacists may treat. Rule to add, if its marks are negative: the limits on who may prescribe in the state's medicines and poisons law (SA). |
| `sa-rideshare-2016` | 3 | Changed a rule not in the register | sa-point-to-point-licensing (requirement) | Legalised ride-share. Rule to add: the state's licences for taxi, hire and booking services (SA). |
| `sa-taxi-licence-reform-2025` | 3 | Changed a rule not in the register | sa-point-to-point-licensing (requirement) | Replaced perpetual taxi licences with annual ones. Rule to add: South Australia's taxi licences. |
| `tas-future-gaming-market-2023` | 1 | Changed a rule not in the register | tas-gaming-machine-entitlements (setting) | Ended the monopoly on gaming machines outside casinos. Rule to add: the state's licences and caps on gaming machines (a cap, so a high score). |
| `tas-heavy-vehicle-national-law-2014` | 2 | Changed a rule not in the register | tas-heavy-vehicle-national-law (requirement) | Applied the national law. Rule to add: heavy vehicle access permits and mass, dimension and fatigue rules (Tas). |
| `tas-necf-2012` | 2 | Changed a rule not in the register | tas-energy-retailer-authorisation (requirement) | Applied the National Energy Retail Law. Rule to add: hold a retailer authorisation from the AER (Tas). |
| `tas-pharmacist-uti-2024` | 2 | Changed a rule not in the register | tas-pharmacist-prescribing-limits (setting) | Widened what pharmacists may treat. Rule to add, if its marks are negative: the limits on who may prescribe in the state's medicines and poisons law (Tas). |
| `tas-rideshare-2016` | 3 | Changed a rule not in the register | tas-point-to-point-licensing (requirement) | Legalised ride-share. Rule to add: the state's licences for taxi, hire and booking services (Tas). |
| `vic-commercial-industrial-property-tax-2024` | 3 | Changed a rule not in the register | vic-commercial-industrial-property-tax (setting) | Replaced duty with an annual tax on entry. Rule to add: Victoria's commercial and industrial property tax. |
| `vic-gaming-venue-operator-2012` | 1 | Changed a rule not in the register | vic-gaming-machine-entitlements (setting) | Replaced the operator duopoly with venue entitlements. Rule to add: the state's entitlements and caps on gaming machines (a cap, so a high score). |
| `vic-heavy-vehicle-national-law-2014` | 2 | Changed a rule not in the register | vic-heavy-vehicle-national-law (requirement) | Applied the national law. Rule to add: heavy vehicle access permits and mass, dimension and fatigue rules (Vic). |
| `vic-pharmacist-uti-2023` | 2 | Changed a rule not in the register | vic-pharmacist-prescribing-limits (setting) | Widened what pharmacists may treat. Rule to add, if its marks are negative: the limits on who may prescribe in the state's medicines and poisons law (Vic). |
| `vic-rail-safety-regulator-2019` | 2 | Changed a rule not in the register | vic-rail-operator-accreditation (requirement) | Rule to add: rail operator accreditation (Vic). |
| `vic-rideshare-2017` | 3 | Changed a rule not in the register | vic-point-to-point-licensing (requirement) | Legalised ride-share. Rule to add: the state's licences for taxi, hire and booking services (Vic). |
| `wa-nqf-childcare-2012` | 0 | Changed a rule not in the register | wa-education-care-service-approval (requirement) | Rule to add: approval as a provider of an education and care service (WA). |
| `wa-on-demand-transport-2019` | 3 | Changed a rule not in the register | wa-point-to-point-licensing (requirement) | Legalised ride-share. Rule to add: the state's licences for taxi, hire and booking services (WA). |
| `wa-pharmacist-uti-2023` | 2 | Changed a rule not in the register | wa-pharmacist-prescribing-limits (setting) | Widened what pharmacists may treat. Rule to add, if its marks are negative: the limits on who may prescribe in the state's medicines and poisons law (WA). |
| `wa-rail-safety-national-law-2024` | 2 | Changed a rule not in the register | wa-rail-operator-accreditation (requirement) | Rule to add: rail operator accreditation (WA). |
| `act-insurance-duty-abolition-2016` | 1 | Removed a rule |  | Abolished insurance duty. |
| `cth-wheat-export-deregulation-2008` | 2 | Removed a rule |  | Ended the single desk. |
| `qld-electricity-frc-2007` | 3 | Removed a rule |  | Ended the retailers' exclusive franchise areas. |
| `sa-commercial-stamp-duty-2015` | 3 | Removed a rule |  | Abolished duty on non-residential transfers. |
| `tas-electricity-frc-2014` | 3 | Removed a rule |  | Ended the retailer's monopoly on small customers. |
| `cth-60-day-dispensing-2023` | 1 | Stands alone |  | Changed PBS supply quantities, not the location rules its family links it to today. |
| `cth-concerted-practices-2017` | 1 | Stands alone |  | Changed competition law, which is not a restriction on entry or conduct the framework counts against productivity. |
| `cth-misuse-market-power-2017` | 2 | Stands alone |  | Changed competition law, as above. |
| `cth-motor-vehicle-repair-information-2022` | 2 | Stands alone |  | A rule marked positive: it opens repair to independent repairers. |
| `cth-small-business-restructuring-2021` | 2 | Stands alone |  | Created an optional process; it places no obligation on businesses. |
| `cth-super-performance-test-2021` | 1 | Stands alone |  | A rule marked positive. |
| `cth-uct-penalties-2023` | 1 | Stands alone |  | Consumer protection marked positive. |
| `cth-uct-small-business-2016` | 1 | Stands alone |  | Consumer protection marked positive. |
| `nsw-e-conveyancing-mandate-2018` | 1 | Stands alone |  | Made electronic lodgment compulsory; marked positive, so no rule weighs on productivity. |
| `nsw-fuel-price-reporting-2016` | 0 | Stands alone |  | Made a price reporting rule whose marks add to zero. |
| `nsw-smart-and-skilled-2015` | 2 | Stands alone |  | A funding program, not a rule on businesses. |
| `nt-fuel-price-reporting-2017` | 0 | Stands alone |  | Made a price reporting rule whose marks add to zero. |
| `nt-port-of-darwin-lease-2015` | 0 | Stands alone |  | A lease whose marks add to zero. |
| `qld-certificate-3-guarantee-2013` | 2 | Stands alone |  | A funding program, not a rule on businesses. |
| `qld-e-conveyancing-mandate-2023` | 1 | Stands alone |  | Made electronic lodgment compulsory; marked positive, so no rule weighs on productivity. |
| `qld-fuel-price-reporting-2018` | 0 | Stands alone |  | Made a price reporting rule whose marks add to zero. |
| `qld-port-of-brisbane-lease-2010` | 0 | Stands alone |  | A lease whose marks add to zero. |
| `sa-e-conveyancing-mandate-2020` | 1 | Stands alone |  | Made electronic lodgment compulsory; marked positive, so no rule weighs on productivity. |
| `sa-fuel-price-reporting-2021` | 0 | Stands alone |  | Made a price reporting rule whose marks add to zero. |
| `sa-skills-for-all-2012` | 1 | Stands alone |  | A funding program, not a rule on businesses. |
| `tas-fuel-price-reporting-2020` | 0 | Stands alone |  | Made a price reporting rule whose marks add to zero. |
| `vic-e-conveyancing-mandate-2019` | 1 | Stands alone |  | Made electronic lodgment compulsory; marked positive, so no rule weighs on productivity. |
| `vic-fuel-price-reporting-2025` | 0 | Stands alone |  | Made a price reporting rule whose marks add to zero. |
| `vic-training-guarantee-2009` | 1 | Stands alone |  | A funding program, not a rule on businesses. |
| `wa-e-conveyancing-mandate-2018` | 1 | Stands alone |  | Made electronic lodgment compulsory; marked positive, so no rule weighs on productivity. |
| `cth-live-sheep-export-ban-2028` | -1 | Not yet in force |  | A ban from 1 May 2028; it becomes a rule when it starts. |
| `cth-national-competition-policy-2024` | 4 | Not yet in force |  | An agreement; its reforms have no commencement dates. |
| `cth-non-compete-ban-2027` | 3 | Not yet in force | cth-non-compete-clause-prevalence | Announced for 2027; already linked to the barrier it would change. |

## Limits

- **Judgement.** Whether a reform created or tightened a restriction, and which rule a change touched, are judgements from the register's own summaries. Three are flagged to confirm: multi-employer bargaining, the Port of Melbourne lease and Queensland's earlier pharmacy ownership law.
- **Not yet marked.** The rules to add have no marks yet. A rule for a change is added only if its marks, against the same market without it, are negative.
- **Proposed ids.** The ids of rules to add are proposals and may change when the items are drafted.
