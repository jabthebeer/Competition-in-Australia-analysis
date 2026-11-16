# Scoping: the cost of licences

*16 November 2026. Scoping only: nothing has been built. Owner request: "scope out potential impact of licensing from a cost perspective, can this be phased into the plan?" Drafted by Claude Code on the legislation branch for the owner and Cowork. Figures marked "register" were counted from the repository on 16 November 2026. Sources marked "search results" were read only in web search summaries, not in the original documents.*

**Decided by the owner, 16 November 2026 (DECISIONS E-173):**

- **In scope:** compliance cost only, meaning fees and direct staff time (hours at the labour rate), for a business entering and at each renewal.
- **Out of scope:** the cost of licensing to the whole economy. Section 4 is kept as background only, and nothing from it will be built or attached.
- **The other recommendations stand,** except one: scaling goes ahead from the law and regulators' published fees before ABLIS.

**Built so far:** see [`licence_costs.md`](licence_costs.md) (the costs) and `regulation-register/licence-costs.json` (the sourced inputs).

## 1. The question

Framework version 2.0 says how hard a licence bites (its severity: a licence needed before trading scores 4 + 2 + 1 = 7 of 8) and how many businesses it reaches. It does not say what a licence costs. The plan for the policy tool already names fees and waiting times as severity attributes waiting on ABLIS ([`plan_policy_tool.md`](plan_policy_tool.md), section 4). This note scopes a fuller answer: what each licence costs the business that holds it, and what licensing costs the economy.

Two kinds of cost need different methods.

| Cost | What it is | How it can be measured | Fits the plan's principles? |
|---|---|---|---|
| **Compliance cost** | What a business pays to get and keep the licence: fees, time to apply, waiting, training, insurance, renewal | Counted from the law and regulators' published figures, with the Office of Impact Analysis's method | Yes: facts anyone can check |
| **Economic cost** | What licensing does to entry, prices, wages and productivity | Estimated by others (the RBA, the OECD, the Productivity Commission) | Only as "What others found": the plan does not estimate (E-161, principle 6) |

## 2. What the register holds now (register)

| Measure | Count |
|---|---|
| Requirements of kind "licence" | 233 of 671 |
| Licence families | 77, of which 27 are in 4 or more jurisdictions |
| Licences, approvals and registrations needed before trading starts | 202 |
| Licence families in all 8 states and territories | builder, plumbing, security, liquor, high-risk work, asbestos removal, driving instructor, health practitioner registration |
| Coded register rules that are licences | 12 (the 8 occupational licensing items, coastal trading, the NSW and Victorian practitioner and engineer schemes, Queensland outside automatic mutual recognition) |

No requirement records a fee, a processing time, a renewal period or a qualification. The schema has no field for them.

## 3. Compliance cost: the method

### The Office of Impact Analysis's method

The *Regulatory Burden Measurement Framework* (Office of Impact Analysis, July 2026) is the Australian Government's method for costing regulation. The repository already implements it in the archived calculator in `regulatory-burden-tool/` (a tested TypeScript engine with a command line). Three of its rules matter here:

- **Labour time** is valued at $91.54 an hour for work time ($52.31 × 1.75 for on-costs) and $41 for non-work time (RBM pp. 12–13; `regulatory-burden-tool/src/engine/parameters.ts`).
- **Delay** is costed as the income forgone while waiting on government (the engine's delay cost type: application and approval delay, net income per day).
- **Government fees, levies, charges and taxes are excluded** from the burden estimate, as transfers to government; the time it takes to pay them stays in (RBM p. 4; the calculator's warning W-01 and test T-SCOPE-01).

So a licence's cost is reported in two parts: its **burden** under the framework, and its **fees**, shown beside it as a cash cost to the business that is also revenue to government.

### Cost elements for each licence

| Element | Measured as | Where it comes from |
|---|---|---|
| Application fee | Dollars | Fee regulations or determinations under the licensing Act (quotable from the law); regulators' fee pages; ABLIS when the key arrives |
| Annual or renewal fee | Dollars and period | As above; the renewal period is usually in the Act or regulations |
| Time to apply | Hours, at $91.54 | Regulators' guidance; a standard assumption where none is published (stated as an assumption) |
| Waiting time | Days, costed as delay | Regulators' published service standards (for example, Consumer Affairs Victoria publishes licensing processing times); annual reports |
| Qualification or experience | Hours of training and course fees, or years of experience | The licensing law (the qualification it names); course fees from providers; costed as labour and purchases |
| Insurance, bonds and continuing training | Dollars a year; hours a year | The licensing law and regulations |

### From one licence to a total

- **Per business:** first-year cost (entry) and yearly cost after that (renewal), in the framework's terms and with fees beside them.
- **Total:** cost per licence × number of licence holders. Holder counts come from regulators' annual reports. Where none is published, ABS business counts give an upper bound, as the levers page already uses ([`plan_policy_tool.md`](plan_policy_tool.md), section 4).
- **Ranges:** low and high values where a fee varies by class of licence or a time is assumed.

## 4. Economic cost: what others found (out of scope, owner 16 November 2026)

These are other people's estimates, to be shown under "What others found", not computed by the tool.

| Source | What it found | Status |
|---|---|---|
| Bowman, Hambur and Markovski (2024), *Examining the Macroeconomic Costs of Occupational Entry Regulations*, RBA Research Discussion Paper 2024-06 | A one-unit rise in its index of occupational entry regulation is associated with a 1.1 percentage point lower business entry rate and a 0.5 point lower exit rate. Cutting regulation to the OECD's least stringent could offset about a fifth of the fall in entry by employing businesses. The authors call the method a back-of-the-envelope, partial equilibrium approach | Read from the RBA's web version |
| Bambalaite, Nicoletti and von Rueden (2020), OECD Economics Department Working Paper 1605 | Labour productivity 1.6% higher for each unit cut in the OECD occupational entry index (range 0.05 to 3.27), from firms in 11 licensed services in 11 EU countries | Already in the calculator's evidence library (`c8.licensing.bnvr2020`), with its locator |
| Productivity Commission (2024), *National Competition Policy: modelling proposed reforms* | Models a 0.5-unit cut in licensing stringency (scenario L2) | Already in the calculator's evidence library (`c8.pc-stringency-cut.pc2024`). The GDP figure reported for it (about 0.4%) is from search results |
| Productivity Commission (2025), *National Competition Policy analysis 2025*, interim report | Labour mobility for high-risk licensed occupations worth up to $846 million a year; a national electrical licence worth up to $51–62 million a year | Search results only; the final report (due 31 October 2025) was not read |
| Productivity Commission (2015 and 2017) | About one in five workers were licensed in 2011 (as cited by the RBA paper). A figure of up to $15 billion a year in costs to consumers is attributed to a 2017 PC paper | The first is quoted in the RBA paper; the second is from a news report only and is not used |

## 5. Phases

Phase 8 in the [re-evaluation plan](plan_levers_reevaluation.md). Each step ends in a pull request, as the other phases do.

| # | Step | Who | Scope |
|---|---|---|---|
| 8.1 | Settle the method | Owner | The decisions in section 6 |
| 8.2 | Fields for cost facts | Website session | On requirements: fees (amount, period, as at, source), processing time (days, source), renewal period, qualification (what, hours or years, source). Optional, like the threshold fields |
| 8.3 | Pilot: fees and renewal from the law | This branch | 3 families × 8 jurisdictions (recommended: builder, plumbing and liquor licences, 24 requirements). Fees quoted from the fee regulations; renewal periods and qualifications from the Act |
| 8.4 | Pilot: waiting times and holder counts | This branch | Regulators' service standards and annual reports, as web-page sources; gaps logged where none is published |
| 8.5 | Cost each pilot licence | This branch | Each licence as an input file for the calculator's engine (`npm run rbe`), which already implements the framework and its tests; fees reported beside the burden figure |
| 8.6 | Show it | Website session | A licence's cost on Legislative levers, the Industry lens and Register data, beside its severity and impact class |
| 8.7 | Scale up | This branch | All 233 licence requirements, once the ABLIS key gives fees at scale; then approvals and registrations |
| 8.8 | What others found | This branch | The economic estimates in section 4, attached to the licensing items, quoted from the originals |

Steps 8.3 and 8.4 can start before 8.2, keeping the figures in a staging table, as phase 2 did.

## 6. Decisions for the owner

| # | Question | Recommended |
|---|---|---|
| 1 | Which pilot families? | Builder, plumbing and liquor licences: in all 8 jurisdictions, with fees in regulations, qualifications in the law, and a link to the mutual recognition reforms |
| 2 | Cost with the Office of Impact Analysis's method, through the existing calculator? | Yes. It is the Government's own method, already built and tested here |
| 3 | Should costs change severity, or stand beside it? | Beside it at first. Fee points can join severity once fees cover most licences |
| 4 | Economic costs: "What others found" only, or revive the archived Policy costing tab to estimate them? | "What others found" only, as principle 6 of the policy-tool plan says |
| 5 | Wait for ABLIS before scaling up? | Yes for the scale-up (step 8.7); the pilot does not need it. **Owner, 16 November 2026: no; keep scaling from the law and regulators before applying for ABLIS** |

## 7. Limits

- **Fees change every year.** Most are indexed and set in regulations or gazettes, so each figure needs its "as at" date.
- **Waiting times are patchy.** Few regulators publish them, and those that do publish averages.
- **Qualification costs are the hardest part.** Course fees vary by provider and state subsidy, and experience requirements have no price. The pilot will show whether they can be costed or only described.
- **Holder counts** are not published for every licence. Business counts are an upper bound, since one business may hold several licences or none.
- **Compliance cost is not the whole cost.** A licence that keeps rivals out costs most through less entry and higher prices, which the tool does not estimate. Section 4 records what others found.
