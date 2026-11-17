# Quoting the coded rules: phase 3

*15 November 2026. Claude Code on the legislation branch, for the owner and the website session. Phase 3 of the [re-evaluation plan](plan_levers_reevaluation.md), under decisions 3 and 4. The same rows are in [`levers_quoted_rules.csv`](levers_quoted_rules.csv). Drafts from AI-assisted desk research, not yet checked by a person.*

Batch 1 (15 November 2026) covered the 56 Severe and Major rules; batch 2 (16 November 2026) the 46 Minor rules.

## Batch 1: Severe and Major rules

### What was done

Each register rule coded in `rule-coding.json` should rest on the law's own words. For each of the 56 Severe and Major coded rules, a requirement quoting the operating provision is attached to the item (its `records` names the item), so the quote sits with the rule. The item's own coding stays in `rule-coding.json`; where the law reads differently, the difference goes to the website session as a list (decision 4).

| Result | Rules |
|---|---|
| Already had a quoted requirement that fits: checked against the coding | 16 |
| Has one that quotes a different Act (the 8 occupational licensing items): the state builder licence fits, proposed below | 8 |
| An existing quoted requirement attached (foreign investment notification) | 1 |
| A new quoted requirement drafted and attached | 19 (plus a second for the Default Market Offer, quoting its price cap); Queensland outside automatic mutual recognition added on 17 November 2026 |
| Found no longer in force | 1 (the NT minimum price on alcohol, repealed from 1 March 2025) |
| Not quoted: blocked (Victoria) | 6 |
| Not quoted: a policy with no law | 2 (the four pillars policy; WA domestic gas reservation) |
| Not quoted yet | 1 (Queensland's 2am liquor limit, deferred to its standing rule in phase 2) |
| Not quoted as rules: phase 2 makes them changes of rules already quoted | 2 (coastal trading 2012; the 2018 pharmacy location rules) |
| **Total** | **56** |

All 42 quotes in the 19 new requirements were found word for word in their sources by the repository's quote checker (run on the new requirements only: the full run stops at a Fair Work awards page that refuses this environment's requests, an existing source).

Also:

- **Links.** 27 instruments on register items gained a link to the official register, copied from the attached requirement's law, so those items now reach the "Law named" evidence step.
- **Gaps.** The new requirement families are drafted only where an item was coded. The other states are logged in `requirement-gaps.json` (25 entries): Victoria as blocked, the rest as not searched.
- **No double listing.** Foreign investment notification was a rule of its own and inside no item. It now sits inside foreign investment screening, the item for the same Act, so the rule is ranked once.

### New requirements

| Rule | Requirement | Provision | Threshold | Maximum penalty |
|---|---|---|---|---|
| `cth-vaping-reforms-2024` | `cth-vape-supply-pharmacy-only` | s 41QB(1), (10) |  | Offence: imprisonment for 7 years or 5,000 penalty units, or both; civil penalty up to 70,000 penalty units for a body corporate (s 41QB(1), (3)) |
| `cth-book-parallel-import-restrictions` | `cth-book-import-licence` | ss 37(1), 44A(2) |  | Civil remedies for infringement (damages, account of profits); no fixed maximum in these sections |
| `cth-small-amount-credit-caps-2013` | `cth-small-amount-credit-cost-caps` | Sch 1 s 31A(2)-(3) | Establishment fee at most 20%, monthly fee at most 4% of the adjusted credit amount | Not stated in s 31A |
| `cth-default-market-offer-2019` | `cth-default-market-offer-cap` | s 10(2) |  | Civil penalty: 300 penalty units (s 10(2)) |
| `qld-pharmacy-business-ownership-2025` | `qld-pharmacy-ownership-restriction` | ss 15(1), 16 | A person may hold an interest in no more than a set number of pharmacy businesses (s 17) | 200 penalty units (ss 15(1), 16) |
| `qld-planning-zoning` | `qld-development-approval` | s 163(1) |  | 4,500 penalty units; 17,000 on a heritage place (s 163(1)) |
| `tas-pharmacy-ownership` | `tas-pharmacy-ownership-restriction` | s 62(1) | A limit on the number of pharmacies a person may hold an interest in (s 65) | 200 penalty units, and 20 a day for a continuing offence (s 62(1)) |
| `tas-planning-zoning` | `tas-development-approval` | s 51(1) |  | Not stated in s 51(1) |
| `wa-pharmacy-ownership` | `wa-pharmacy-ownership-restriction` | s 54(1) |  | $5,000 for an individual, $10,000 for a body corporate (s 54) |
| `wa-planning-zoning` | `wa-development-approval` | s 218(a)-(b) |  | The general penalty in s 223 (not quoted) |
| `nsw-planning-zoning` | `nsw-development-approval` | s 4.2(1) |  | Tier 1 monetary penalty (s 4.2(1)) |
| `nsw-pharmacy-ownership` | `nsw-pharmacy-ownership-restriction` | Sch 5F cl 5(1) |  | 100 penalty units (Sch 5F cl 5(1)) |
| `sa-planning-zoning` | `sa-development-approval` | s 215(1) |  | $120,000, with a default penalty of $500 (s 215(1)) |
| `sa-pharmacy-ownership` | `sa-pharmacy-ownership-restriction` | s 51(1a) |  | $50,000 or imprisonment for 6 months (s 51(1a)) |
| `act-planning-zoning` | `act-development-approval` | s 403(1) |  | 2,000 penalty units for an individual, 2,500 for a corporation (s 403(1)) |
| `nt-planning-zoning` | `nt-development-approval` | s 75B(1) |  | 500 penalty units for the offence in s 75B(2) (not quoted) |
| `nt-takeaway-liquor-moratorium-2017` | `nt-takeaway-authority-moratorium` | s 84(3)-(4); reg 98A | Until after 28 February 2027 (reg 98A) | None stated: the bar is on issuing authorities |
| `nt-fuel-price-commitment-2026` | `nt-fuel-next-day-price` | new reg 5(1)-(3) |  | Not stated in reg 5 |
| `nsw-stra-2021` | `nsw-short-term-rental-night-cap` | s 112(1) | 180 days in a 365-day period in prescribed areas; 60 days in parts of Byron Shire (s 112(1)) | None stated in s 112 |

### Coding corrections for the website session (decision 4)

`rule-coding.json` is the website session's file, so these are proposals, not edits. Each comes from the law's own words in the attached requirement.

#### Corrections that change a rule's class

| Rule | Coded | Proposed | Why | Class |
|---|---|---|---|---|
| `cth-sustainability-reporting-2025` | reporting, growth, all | bound: some | Climate reporting binds only entities above the size thresholds (attached `cth-sustainability-reporting`) | Major (wide) to Minor: a rule binding only some businesses is never wide |
| `cth-gas-market-code-2023` | price-control, operating, all | bound: some | The Code binds only suppliers of regulated gas (attached `cth-gas-market-code`) | Score 5 to 4: Major (narrow) to Minor |
| `cth-small-amount-credit-caps-2013` | price-control, operating, all | bound: some | The caps bind only lenders offering small amount credit contracts, not every non-depository financier (Sch 1 s 31A) | Score 5 to 4: Major (narrow) to Minor |
| `nt-alcohol-minimum-unit-price-2018` | price-control, operating, all | remove | Repealed from 1 March 2025; the item now records the repeal | Leaves the classes (Major, narrow) |

#### Corrections that keep the class

| Rule | Coded | Proposed | Why |
|---|---|---|---|
| The 7 planning items (`act`, `nsw`, `nt`, `qld`, `sa`, `tas`, `wa-planning-zoning`) | approval, entry, all | bound: some | Approval is needed only for development the planning scheme says needs it. Score 7 to 6 |
| `cth-vaping-reforms-2024` | cap, entry, all | bound: some | The ban binds only businesses that would supply vapes. Score 8 to 7 |
| `cth-pharmacy-location-rules` | cap, entry, all | bound: some | PBS approval binds pharmacies seeking it. Score 8 to 7 |
| `cth-sydney-airport-curfew-cap` | cap, operating, all | bound: some | Binds operators at Sydney Airport only. Score 6 to 5 |
| `vic-ohs-not-harmonised` | standard, operating, all | when: growth | The duty is an employer's, so it bites at the first employee. Score 3 to 4 |
| `nsw-design-building-practitioners-2021` | licence (item) and registration (requirement) | check | Registration is needed to do the work; 'licence' may fit both |

#### Proposed attachment

Each state's occupational licensing item has the state's security licence attached, which quotes a different Act. The state's builder licence quotes the item's own licensing law and agrees with its coding (licence, entry), and it is also ranked as a rule of its own, so the rule is counted twice. Attaching the 8 builder licences to the 8 items fixes both, but `tests/test_explorer.py` keeps builder licences as one group (`req-builder-licence`). The test belongs to the website session, so the attachment waits for its decision.

#### For the schema

Requirements have no kind for a cap (or exclusive right, ban or ownership limit) or a price control, the two kinds that score highest for register items. The attached requirements for pharmacy ownership, Australia Post, the Default Market Offer, the gas price code, the Sydney Airport cap, vapes, the NSW night cap, the NT moratorium and the NT fuel commitment therefore carry 'licence' or 'other'. Adding `cap` and `price-control` to requirement kinds would let them carry the same kind as the coding.

### Found on the way

- **The NT minimum price on alcohol has been repealed** (1 March 2025). It was listed as a Major (narrow) rule in force.
- **The NT takeaway liquor moratorium is still in force.** The Liquor Act 2019 (s 84(3)) carries it on, and the regulations extend it to 28 February 2027. Section 84(2) also bars any grocery store liquor authority: a second cap, not yet in the register.
- **The Default Market Offer item lists class 2700 (gas supply)**, but the Code covers electricity only. The Victorian Default Offer item does the same. Recheck both in phase 5.
- **Victoria is blocked.** Its register refuses automated requests. Saved copies of 6 laws would unblock it: the Pharmacy Regulation Act 2010, Planning and Environment Act 1987, Professional Engineers Registration Act 2019, the Port of Melbourne lease Act 2016, the fuel price regulations (S.R. No. 152/2025) and the Victorian Default Offer order.

## Batch 2: Minor rules

| Result | Rules |
|---|---|
| A new quoted requirement drafted and attached | 23 (transfer and insurance duty in 6 states; container deposit schemes in 6; the right to disconnect, labour hire pay orders, multi-employer bargaining and dumping duty; the WA short-term rental register) |
| An existing quoted requirement attached | 1 (customs duty, under import tariffs) |
| Not quoted: blocked (Victoria) | 4 (insurance duty, transfer duty, container deposits, short stay levy) |
| Not quoted: no law | 2 (the childcare fee growth cap, a grant condition; mandatory standards that differ from international ones, a pattern across many instruments) |
| Not quoted as rules: phase 2 makes them changes of a rule already quoted | 8 (the NDIS Commission transfers, under `cth-ndis-registered-provider`) |
| Deferred to the standing rules phase 2 adds | 8 (the 2022 building code adoptions; Victoria is also blocked) |
| **Total** | **46** |

All 46 quotes in the 23 new requirements were found word for word by the quote checker. 17 more instruments on register items gained an official register link (44 across both batches), and gaps are logged for the states each new family does not yet cover: Victoria as blocked, the ACT's conveyance duty as to draft, the rest as not searched.

### New requirements

| Rule | Requirement | Provision | Maximum penalty |
|---|---|---|---|
| `nsw-residential-transfer-duty` | `nsw-transfer-duty` | s 13 |  |
| `nsw-insurance-duty` | `nsw-insurance-duty-payment` | s 235 |  |
| `qld-residential-transfer-duty` | `qld-transfer-duty` | s 17 |  |
| `qld-insurance-duty` | `qld-insurance-duty-payment` | s 357(1)-(2) |  |
| `tas-residential-transfer-duty` | `tas-transfer-duty` | s 11 |  |
| `tas-insurance-duty` | `tas-insurance-duty-payment` | s 167 |  |
| `wa-residential-transfer-duty` | `wa-transfer-duty` | s 20 |  |
| `wa-insurance-duty` | `wa-insurance-duty-payment` | s 213 |  |
| `sa-residential-transfer-duty` | `sa-transfer-duty` | s 5(2) |  |
| `sa-insurance-duty` | `sa-insurance-duty-payment` | s 34(1) |  |
| `nt-residential-transfer-duty` | `nt-transfer-duty` | s 52A(a) |  |
| `nt-insurance-duty` | `nt-insurance-duty-payment` | s 85(1) (registration of insurers) | 50 penalty units for an unregistered NT insurer (s 85(1)) |
| `nsw-cds-2017` | `nsw-container-refund-supply-arrangement` | s 38(1) |  |
| `act-cds-2018` | `act-container-refund-supply-arrangement` | s 64W(1) |  |
| `qld-cds-2018` | `qld-container-refund-supply-arrangement` | s 99P(1) |  |
| `nt-cds-2012` | `nt-container-refund-supply-arrangement` | s 13(4) |  |
| `tas-cds-2025` | `tas-container-refund-supply-arrangement` | s 11(2) |  |
| `wa-cds-2020` | `wa-container-refund-supply-arrangement` | s 47E(2) |  |
| `cth-right-to-disconnect-2024` | `cth-right-to-disconnect` | s 333M(1) | Civil remedy provisions of the Act (not quoted) |
| `cth-same-job-same-pay-2023` | `cth-labour-hire-protected-rate` | s 306F(2) | A civil remedy provision (s 306F(2), note) |
| `cth-multi-employer-bargaining-2023` | `cth-multi-employer-bargaining` | s 242(1) |  |
| `cth-anti-dumping-system` | `cth-dumping-duty` | s 269TG(1) |  |
| `wa-stra-register-2025` | `wa-short-term-rental-registration` | s 9 | A fine of $20,000 (s 9) |

### Coding corrections for the website session

| Rule | Coded | Proposed | Why | Class |
|---|---|---|---|---|
| The 7 container deposit schemes (`act`, `nsw`, `nt`, `qld`, `tas`, `vic`, `wa-cds-*`) | tax-or-levy, operating, all | registration, entry | The law bars a first supplier from supplying drinks in eligible containers until it has a supply arrangement with the scheme coordinator and an approved container; the contributions follow from the arrangement. Score 3 to 5 | Minor to Major (narrow) |
| `cth-right-to-disconnect-2024` | standard, growth, all | none | Agrees. The item names divisions K and M, but the right binds every employer: recheck the reach in phase 5 | None |

The container deposit change is a judgement about which part of the rule bites first, so it is offered for the website session to decide, not as a plain error.

### Found on the way

- **Container deposit items** list retailers and recyclers as well as drink makers. The supply rule binds only the first supplier (the maker or importer), so the new requirements reach drink manufacturing (classes 1211, 1212 and 1214). Recheck the items' industries in phase 5.
- **Insurance duty in the NT** is quoted through the duty to register as an insurer before writing dutiable policies (s 85(1)); the provision imposing the duty itself was not found by the searches here.
- **The ACT has no transfer duty item.** It still charges conveyance duty at falling rates; phase 2 adds it.

## Limits

- **NSW and SA** are quoted from the Open Australian Legal Corpus copy (10 March 2025 and later versions), which is not itself official. Each says so.
- **Marks** on the new requirements are copied from their items, so the two agree. They are not a fresh judgement.
- **Reach** follows the item's industries (except the container deposit requirements, which follow the law); phase 5 narrows it.
- **Administration** (who licenses, inspects and enforces) is not yet coded on the new requirements.

## Leftover quoted after batching resumed (17 November 2026)

- **Queensland outside automatic mutual recognition** (`qld-amr-not-adopted`): requirement `qld-mutual-recognition-notice`. A worker licensed in another state lodges a notice with the Queensland authority before working there (Mutual Recognition Act 1992 (Cth) s 19(1)); the 2021 amendments that brought in automatic deemed registration do not apply to a "pre-adoption State" (ss 4, 5(3), 42C(3)). The coding agrees (licence, before trading, binds some businesses). Once the notice is lodged the worker is taken to be registered while the authority decides (s 25), which softens the hurdle.
  - **Still in force:** neither Act names Queensland, so its status is read from the definition and the Queensland Act, which adopts no 2021 amendment. A 2024 Queensland regulation (SL 2024 No. 244) approves only the change to the Administrative Review Tribunal.
  - **Gaps:** the other 7 jurisdictions are logged as not searched. They are in automatic mutual recognition, but occupations exempted from it (for example, WA electricians under a 2025 declaration) still use the s 19 notice.
  - All 9 quotes were found in their sources.
