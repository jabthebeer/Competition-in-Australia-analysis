# Quoting the coded rules: phase 3, batch 1 (Severe and Major)

*15 November 2026. Claude Code on the legislation branch, for the owner and the website session. Phase 3 of the [re-evaluation plan](plan_levers_reevaluation.md), under decisions 3 and 4. The same rows are in [`levers_quoted_rules.csv`](levers_quoted_rules.csv). Drafts from AI-assisted desk research, not yet checked by a person.*

## What was done

Each register rule coded in `rule-coding.json` should rest on the law's own words. For each of the 56 Severe and Major coded rules, a requirement quoting the operating provision is attached to the item (its `records` names the item), so the quote sits with the rule. The item's own coding stays in `rule-coding.json`; where the law reads differently, the difference goes to the website session as a list (decision 4).

| Result | Rules |
|---|---|
| Already had a quoted requirement that fits: checked against the coding | 16 |
| Has one that quotes a different Act (the 8 occupational licensing items): the state builder licence fits, proposed below | 8 |
| An existing quoted requirement attached (foreign investment notification) | 1 |
| A new quoted requirement drafted and attached | 18 (plus a second for the Default Market Offer, quoting its price cap) |
| Found no longer in force | 1 (the NT minimum price on alcohol, repealed from 1 March 2025) |
| Not quoted: blocked (Victoria) | 6 |
| Not quoted: a policy with no law | 2 (the four pillars policy; WA domestic gas reservation) |
| Not quoted yet | 2 (Queensland outside automatic mutual recognition; Queensland's 2am liquor limit, deferred to its standing rule in phase 2) |
| Not quoted as rules: phase 2 makes them changes of rules already quoted | 2 (coastal trading 2012; the 2018 pharmacy location rules) |
| **Total** | **56** |

All 42 quotes in the 19 new requirements were found word for word in their sources by the repository's quote checker (run on the new requirements only: the full run stops at a Fair Work awards page that refuses this environment's requests, an existing source).

Also:

- **Links.** 27 instruments on register items gained a link to the official register, copied from the attached requirement's law, so those items now reach the "Law named" evidence step.
- **Gaps.** The new requirement families are drafted only where an item was coded. The other states are logged in `requirement-gaps.json` (25 entries): Victoria as blocked, the rest as not searched.
- **No double listing.** Foreign investment notification was a rule of its own and inside no item. It now sits inside foreign investment screening, the item for the same Act, so the rule is ranked once.

## New requirements

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

## Coding corrections for the website session (decision 4)

`rule-coding.json` is the website session's file, so these are proposals, not edits. Each comes from the law's own words in the attached requirement.

### Corrections that change a rule's class

| Rule | Coded | Proposed | Why | Class |
|---|---|---|---|---|
| `cth-sustainability-reporting-2025` | reporting, growth, all | bound: some | Climate reporting binds only entities above the size thresholds (attached `cth-sustainability-reporting`) | Major (wide) to Minor: a rule binding only some businesses is never wide |
| `cth-gas-market-code-2023` | price-control, operating, all | bound: some | The Code binds only suppliers of regulated gas (attached `cth-gas-market-code`) | Score 5 to 4: Major (narrow) to Minor |
| `cth-small-amount-credit-caps-2013` | price-control, operating, all | bound: some | The caps bind only lenders offering small amount credit contracts, not every non-depository financier (Sch 1 s 31A) | Score 5 to 4: Major (narrow) to Minor |
| `nt-alcohol-minimum-unit-price-2018` | price-control, operating, all | remove | Repealed from 1 March 2025; the item now records the repeal | Leaves the classes (Major, narrow) |

### Corrections that keep the class

| Rule | Coded | Proposed | Why |
|---|---|---|---|
| The 7 planning items (`act`, `nsw`, `nt`, `qld`, `sa`, `tas`, `wa-planning-zoning`) | approval, entry, all | bound: some | Approval is needed only for development the planning scheme says needs it. Score 7 to 6 |
| `cth-vaping-reforms-2024` | cap, entry, all | bound: some | The ban binds only businesses that would supply vapes. Score 8 to 7 |
| `cth-pharmacy-location-rules` | cap, entry, all | bound: some | PBS approval binds pharmacies seeking it. Score 8 to 7 |
| `cth-sydney-airport-curfew-cap` | cap, operating, all | bound: some | Binds operators at Sydney Airport only. Score 6 to 5 |
| `vic-ohs-not-harmonised` | standard, operating, all | when: growth | The duty is an employer's, so it bites at the first employee. Score 3 to 4 |
| `nsw-design-building-practitioners-2021` | licence (item) and registration (requirement) | check | Registration is needed to do the work; 'licence' may fit both |

### Proposed attachment

Each state's occupational licensing item has the state's security licence attached, which quotes a different Act. The state's builder licence quotes the item's own licensing law and agrees with its coding (licence, entry), and it is also ranked as a rule of its own, so the rule is counted twice. Attaching the 8 builder licences to the 8 items fixes both, but `tests/test_explorer.py` keeps builder licences as one group (`req-builder-licence`). The test belongs to the website session, so the attachment waits for its decision.

### For the schema

Requirements have no kind for a cap (or exclusive right, ban or ownership limit) or a price control, the two kinds that score highest for register items. The attached requirements for pharmacy ownership, Australia Post, the Default Market Offer, the gas price code, the Sydney Airport cap, vapes, the NSW night cap, the NT moratorium and the NT fuel commitment therefore carry 'licence' or 'other'. Adding `cap` and `price-control` to requirement kinds would let them carry the same kind as the coding.

## Found on the way

- **The NT minimum price on alcohol has been repealed** (1 March 2025). It was listed as a Major (narrow) rule in force.
- **The NT takeaway liquor moratorium is still in force.** The Liquor Act 2019 (s 84(3)) carries it on, and the regulations extend it to 28 February 2027. Section 84(2) also bars any grocery store liquor authority: a second cap, not yet in the register.
- **The Default Market Offer item lists class 2700 (gas supply)**, but the Code covers electricity only. The Victorian Default Offer item does the same. Recheck both in phase 5.
- **Victoria is blocked.** Its register refuses automated requests. Saved copies of 6 laws would unblock it: the Pharmacy Regulation Act 2010, Planning and Environment Act 1987, Professional Engineers Registration Act 2019, the Port of Melbourne lease Act 2016, the fuel price regulations (S.R. No. 152/2025) and the Victorian Default Offer order.

## Limits

- **NSW and SA** are quoted from the Open Australian Legal Corpus copy (10 March 2025 and later versions), which is not itself official. Each says so.
- **Marks** on the new requirements are copied from their items, so the two agree. They are not a fresh judgement.
- **Reach** follows the item's industries; phase 5 narrows it.
- **Administration** (who licenses, inspects and enforces) is not yet coded on the new requirements.
