# Framework traceability

**Status:** Phases 1 and 2 implemented (6 October 2026).
- The **Code** column points to the implementation in `src/engine/`.
- The **Test** column gives test IDs, which appear in the test titles under `tests/engine/`, `tests/ui/` and `e2e/`.
- `npm run trace` checks that every cited test, warning and code reference exists.

## 1. Source documents

| Short name | Document | Version and identity |
|---|---|---|
| **RBM** (the spec) | *Regulatory Burden Measurement Framework*, Office of Impact Analysis (OIA), PM&C | July 2026, 15 pp. SHA-256 `646848f9…0c74ac8`. Identical to the copy on the OIA website as of 6 Oct 2026 (see `data/SOURCES.md`). |
| **IAF-PG** (context) | *Australian Government Impact Analysis Framework: Practical Guide for Agencies*, OIA | July 2026, 25 pp. In effect from 1 July 2026. |
| **OIA-calc** (context) | *Regulatory Burden Estimate calculator* (.xlsx), OIA | "Version July 2026". |

- **Page references.** "p. N" means the printed page number of the RBM. The printed numbers match the PDF page index (the cover is p. 1).
- **Precedence.** The RBM is the specification. The IAF-PG and OIA-calc are cited only where they settle an RBM ambiguity, or where they change how the RBM applies in practice (section 5).

**Column key**

- **Code** is the module (and function) under `src/engine/`.
- **Test** is the test ID (W-xx for warnings) used in the titles of `tests/engine/*.test.ts`.

## 2. Rules, defaults, formulas and exclusions

### 2.1 Purpose and cost categories

| ID | Rule | RBM | Code | Test |
|---|---|---|---|---|
| R-01 | New policies, and changes to existing ones, must quantify the increase *or decrease* in costs imposed on businesses, community organisations and individuals. | p. 1 | `aggregate.ts` (signed Δ) | T-RBE-01, T-RBE-04 |
| R-02 | Regulatory costs are compliance costs (administrative + substantive compliance) plus delay costs. | pp. 1–2 | `schema.ts` (`category` enum) | T-SCH-01 |
| R-03 | **Administrative costs** are incurred primarily to *demonstrate* compliance. They include time and associated travel or queuing, and the costs of: making, keeping and providing records; notifying government; conducting tests; making applications; and the *time* to pay taxes, fees, charges and levies (not the amount paid). | p. 2 | `scope.ts` (category help, screener) | T-SCOPE-03 |
| R-04 | **Substantive compliance costs** are incurred to *deliver the outcome*: training; buying and maintaining plant and equipment; providing information to third parties; operating costs (e.g. energy); professional services (legal, tax, accounting); permits bought through non-government market mechanisms. | pp. 2–3 | `scope.ts` | T-SCOPE-03 |
| R-05 | Government subsidies paid to help comply are **subtracted** from the compliance cost. | p. 3 | `reform.ts#finaliseItem` | T-COST-05 |
| R-06 | **Delay costs** are expenses and loss of income from (a) an *application delay*, the entity's time to complete an application that prevents it beginning its intended operations, or (b) an *approval delay*, the regulator's time to decide, including assessment. | pp. 2–3 | `costing.ts#delayCost` | T-DEL-01..05 |

### 2.2 Exclusions (never in the RBE; may be analysed qualitatively in the IA, p. 3)

| ID | Excluded | RBM | Code | Test |
|---|---|---|---|---|
| R-07 | Opportunity costs (the value of opportunities forgone), **unless they relate to a delay**. | p. 3 | `scope.ts` | T-SCOPE-03 |
| R-08 | Business-as-usual (BAU) costs: anything above which burden is measured, i.e. what a *normally efficient business* would pay without the regulation. Footnote 1 defines a normally efficient business as one that "handles its regulatory tasks no better or worse than another". Example: an airport perimeter fence that airports build anyway. | p. 3 (fn 1), p. 6 | `reform.ts#doAnywayShares` | T-COST-04, T-REF-04..06 |
| R-09 | Non-compliance and enforcement costs: fines, legal fees, court and tribunal costs; costs arising when entities fail to comply and must act to restore compliance; government processes put in place to *enforce* compliance. | pp. 3–4 | `scope.ts`, `aggregate.ts` | T-SCOPE-01..03 |
| R-10 | Regulatory impacts of court and tribunal administration (court rules, practice directions made by the court or tribunal). | p. 4 | `scope.ts` | T-SCOPE-03 |
| R-11 | Indirect costs, including changes to market structure and **competition impacts**. | p. 4 | `scope.ts` | T-SCOPE-03 |
| R-12 | Direct financial costs payable to government: administrative charges, licence and permit fees, levies, mandatory insurance premiums *where remitted to government*. **Taxes** are also excluded. | p. 4 | `scope.ts`, `validate.ts` (W-01) | T-SCOPE-03, W-01 |
| R-13 | Costs of international obligations that are a prerequisite for taking part in international markets (e.g. airworthiness directives). This covers *performing* the obligated activity only. *Demonstrating* compliance to a Commonwealth regulator stays in scope. | p. 4 | `scope.ts` | T-SCOPE-03 |
| R-14 | Government-to-government policy imposed on Commonwealth, state/territory, local or foreign government agencies and their employees (as part of their employment). **Exceptions, which stay in scope:** Government Business Enterprises, public universities, and businesses owned by foreign governments. | pp. 4–5 | `scope.ts`, `validate.ts` (W-13) | W-13 |
| R-15 | Not every cost must be quantified, but administrative, substantive compliance and delay costs that can be practically estimated should be. Costs to government belong elsewhere in the IA. | p. 11 | `scope.ts` (help text) | — |

### 2.3 Relevant population

| ID | Rule | RBM | Code | Test |
|---|---|---|---|---|
| R-16 | The population is businesses, community organisations and individuals. An *individual* is subject to Australian law, has activities that impact Australia, and interacts with the Australian Government or is affected by its policy. All activities of individuals count, whether income-generating (e.g. occupational licensing) or not (e.g. visas, passports). | p. 5 | `schema.ts` (`group`) | T-SCH-01 |
| R-17 | Businesses and community organisations operating, or seeking to operate, in Australia regardless of ownership. This includes foreign businesses exporting to or investing in Australia (e.g. foreign investment applications), and Australian entities operating overseas to the extent Australian policy affects them. | p. 5 | `schema.ts` (population flags) | W-02 |

### 2.4 Reporting: the RBE table

| ID | Rule | RBM | Code | Test |
|---|---|---|---|---|
| R-18 | An RBE table must be produced **for every viable option**. | p. 5 | `aggregate.ts#aggregateOption` | T-RBE-07 |
| R-19 | Table format. Caption "Average annual regulatory costs (from business as usual)". Header: "Change in costs ($ million) \| Business \| Community organisations \| Individuals \| Total change in costs". One row: "Total, by sector". | p. 5, p. 11 | `aggregate.ts`, `src/export/` | T-RBE-01 |
| R-20 | Use a single point estimate of the most likely scenario. Where an estimate is presented as a range, OIA uses its midpoint. | p. 11 | `schema.ts` (`Quantity`), `costing.ts#point` | T-COST-06 (see A-07) |
| R-21 | Reductions are entered as **negatives**. Worked example: a $400,000 a year saving for business reads `($0.4)`, `$0`, `$0`, `($0.4)`. Zero cells are printed as `$0`. | p. 11 | `format.ts#rbeTable` | T-RBE-01, T-RBE-06 |
| R-22 | Estimates in addenda to an IA also count towards the annual impact. *(Process rule; out of tool scope. Noted only.)* | p. 11 | — | — |
| R-23 | The RBE report must be completed and included in the IA. | p. 10 | `src/export/` (Phase 4) | — |

### 2.5 Annualisation and timing

| ID | Rule | RBM | Code | Test |
|---|---|---|---|---|
| R-24 | Present costs as average annual impacts. | p. 6 | `annualise.ts` | T-ANN-01..06 |
| R-25 | Default duration is **10 years**. Use a shorter period if the policy ends sooner, e.g. a 3-year grant programme or a 4-year budget measure. | p. 6, p. 11 | `schema.ts` (`durationYears`), `validate.ts` | T-ANN-06, W-16 |
| R-26 | **Real terms** (constant prices): no inflation, and the same wage rate in every year. | p. 6 | `annualise.ts` (no escalation inputs exist) | T-ANN-07 |
| R-27 | **No discounting** in the RBE. (Discounting belongs to a full cost–benefit analysis.) | p. 6 | `annualise.ts`; strict schema rejects `discountRate` | T-ANN-07 |
| R-28 | Costs that don't vary over time: the first-year change can be treated as the average. | p. 6 | `annualise.ts` (the general profile rule gives the same result) | T-ANN-02 |
| R-29 | Costs that vary over time: total over the duration ÷ duration. Example: a cost every two years over 10 years → sum the 10 years, then ÷ 10. | p. 6, p. 8 | `annualise.ts` | T-ANN-03..05 |
| R-30 | One-off and start-up costs: ÷ duration. | p. 6, p. 8 | `annualise.ts` | T-ANN-01 |
| R-31 | Start-up costs are incurred in the **first year**, and tend to be one-off purchase costs. Ongoing costs recur from year to year and are constant or variable. | p. 8 | `schema.ts` (`Timing`) | T-ANN-01 |
| R-32 | Consider disaggregating into small, medium and large cohorts where effects vary significantly. | pp. 7–8 | `schema.ts` (`Population.cohort`), `aggregate.ts#aggregateOption` | T-RBE-09, T-REF-09 |

### 2.6 Inter-jurisdictional reforms

| ID | Rule | RBM | Code | Test |
|---|---|---|---|---|
| R-33 | Applies to national reforms that change Commonwealth legislation or practices, or that result from direct Commonwealth incentives or conditions. This includes decisions of National Cabinet, ministerial councils and intergovernmental standard-setting bodies with Commonwealth involvement. | p. 6 | `schema.ts` (`jurisdiction`), `validate.ts` | T-RBE-03 |
| R-34 | Net the costs imposed or removed by the Commonwealth *and* by states and territories. Example: −$10m + $2m = **−$8m** a year. | p. 6 | `aggregate.ts#aggregateOption` | T-RBE-02 |

### 2.7 Method and costing formulas

| ID | Rule | RBM | Code | Test |
|---|---|---|---|---|
| R-35 | Start from the obligations, and from how stakeholders operate in the *current* regulatory or non-regulatory environment. This identifies BAU costs. | p. 7 | `reform.ts` (current regime) | T-REF-* |
| R-36 | Use the best available data. Where none exists, assumptions must be **reasonable and defensible**. | p. 7 | `schema.ts` (`Source`, `Override`), assumptions register | W-05 |
| R-37 | Three steps: (1) nature of costs (start-up or ongoing, constant or variable, by size); (2) cost the three classes; (3) summarise in the RBE table. | p. 7 | UI wizard (Phase 2) | — |
| R-38 | Administrative costs are normally labour costs; substantive compliance costs are normally purchase costs. | p. 8 | `schema.ts` (defaults), `validate.ts` | W-01, W-02 |
| R-39 | **Labour, businesses and community organisations:** (Time required × Labour cost) × (Times performed × Number of entities × Number of staff). *Time required* is internal hours per staff member per occurrence. *Labour cost* is the hourly wage plus non-wage on-costs (payroll tax, superannuation) and overheads (rent, telephone, IT). *Times performed* is per year per staff member (twice a month = 24). *Number of entities* takes account of the expected compliance rate. *Number of staff* is staff per entity who perform the activity. | pp. 8–9 | `costing.ts#labourCost` | T-COST-01 |
| R-40 | **Labour, individuals:** (Time required × Labour cost) × (Times performed × Number of individuals). The rate is for time outside paid employment (leisure). Use the default unless there is strong evidence for another. Times performed is per year per individual; the number of individuals takes account of the compliance rate. | p. 9 | `costing.ts#labourCost` | T-COST-02 |
| R-41 | **Purchase:** Purchase cost × (Times performed × Number of entities). The purchase cost is a product or external service *not otherwise bought* (e.g. a safety guard). | p. 9 | `costing.ts#purchaseCost` | T-COST-03 |
| R-42 | **Delay costs** count only while an entity is **waiting on government action to commence trading**. Worked example: a 6-month approval for an entity ready on the day of lodgement = 6 months of lost sales; ready 4 months after lodgement = **2 months**. | p. 10 | `costing.ts#effectiveDelay` | T-DEL-01 |
| R-43 | Delays involving land or capital: the purchase of a required machine is a *substantive compliance* cost. The machine sitting idle because of an application delay is a *delay* cost, valued as the **loss of net income** from not using it. Consider the BAU case. | p. 10 | `scope.ts` (help), `costing.ts#delayCost` | T-DEL-03 |
| R-44 | If a proposal is likely to impose delay costs, **contact OIA** for further guidance. | p. 10 | UI flag "seek OIA advice" | — |
| R-45 | "Often, once the policy is implemented, delay costs could be considered as administrative costs, compliance costs, or both." | p. 10 | — (see A-09) | — |

### 2.8 Labour rates (Appendix 2)

| ID | Rule | RBM | Code | Test |
|---|---|---|---|---|
| R-46 | Work-related labour is valued at the hourly cost to the business or community organisation of the relevant staff. | p. 12 | `parameters.ts` | T-PAR-01 |
| R-47 | **Outsourced** labour-related services (accountancy, legal) are **purchase costs**, not labour. | p. 12 | `validate.ts` (W-02) | W-02 |
| R-48 | Default work rate: $52.31/hour × 1.75 = **$91.54/hour**. The $52.31 is "based on average weekly earnings, but adjusted to include income tax". Source (fn 3–4): ABS *Employee Earnings and Hours*, released January 2024, Data Cube 6, full-time non-managerial employees paid at the adult rate; ATO Simple Tax Calculator, 2024–25 rates. The 1.75 multiplier covers on-costs (payroll tax, superannuation) and overheads (rent, telephone, electricity, IT). | p. 12 | `parameters.ts` | T-PAR-01 |
| R-49 | Use the default rate where policy cuts across sectors, or where better rates are unknown or would add undue complexity. | p. 12 | `parameters.ts` (help) | — |
| R-50 | Use a different rate or multiplier where strong evidence shows it is more accurate (e.g. known on-costs; a single sector such as mining or medical practitioners). | p. 12 | `schema.ts` (`Override`) | W-05 |
| R-51 | Default non-work (leisure) rate: **$41/hour**, based on average weekly earnings including overtime, after tax. | p. 13 | `parameters.ts` | T-PAR-02 |
| R-52 | For people outside the labour force (unemployed people, pensioners), where strong evidence supports a different rate, **discuss with OIA**. | p. 13 | UI help, `validate.ts` | — |
| R-53 | The $41 rate is only for individuals **residing in Australia**. For non-residents, use a rate based on the average hourly rate in their country. | p. 13 (fn 5) | `validate.ts` (W-04) | W-04 |
| R-54 | Rates are generally updated every two years. The next update is scheduled for **February 2028**, "though this is yet to be confirmed". | p. 12 (fn 2) | `parameters.ts` (metadata) | T-PAR-03 |

### 2.9 Compliance and enforcement (Appendix 3)

| ID | Rule | RBM | Code | Test |
|---|---|---|---|---|
| R-55 | In general, all compliance costs (administrative and substantive) are in scope, and all enforcement costs are excluded. | p. 14 | `aggregate.ts` | T-SCOPE-01 |
| R-56 | Classify the *activity*, not the "mutual obligation" label. The question is whether the activity is compliance or enforcement, judged by the government's objective. | p. 14 | `scope.ts` (screener) | — |
| R-57 | Voluntary, administrative and regulatory interactions are reasonably assumed to be compliance. This is the **default position**: all their administrative, substantive and delay costs are costed. | pp. 14–15 | `schema.ts` (default `compliance`) | T-SCOPE-01 |
| R-58 | Processes put in place by government to *enforce* compliance, or to influence or direct behaviour, are outside the RBM. | p. 15 | `scope.ts` | T-SCOPE-01 |
| R-59 | To depart from the default, agencies must **clearly demonstrate** that a proposal is an enforcement action. | p. 15 | `validate.ts` (justification required) | W-14 |
| R-60 | A mix may be costed as 100% compliance or 100% enforcement without demonstrating the split. A split may be estimated if accurate data is readily available. | p. 15 | `schema.ts` (`scope.complianceShare`) | T-SCOPE-02 |

### 2.10 Tool rules that implement, rather than quote, the framework

These come from the prompt. They are listed so that each traces back to the framework rule it implements.

| ID | Tool rule | Derives from | Code | Test |
|---|---|---|---|---|
| X-01 | Reform = reformed-regime cost − current-regime cost, obligation by obligation, plus transition costs. | R-01, R-08, R-35 (change from BAU) | `reform.ts` | T-REF-01..03 |
| X-02 | Do-anyway share: only the avoided part of a removed or reduced obligation is a saving. | R-08 (BAU) | `reform.ts#doAnywayShares` | T-REF-04..06 |
| X-03 | Transition costs (familiarisation, systems, retraining, advice) are one-off costs annualised over the duration. | R-30, R-31 (start-up costs) | `reform.ts` | T-REF-01 |
| X-04 | Overlap/dual running: current obligations keep running for a set period after commencement. | R-29 (varying costs) | `reform.ts#applyMasks` | T-REF-07, T-REF-08 |
| X-05 | Sunk costs are not savings. | R-08 and R-01 (only *changes* in future costs vs BAU) | `reform.ts` | T-REF-10 |
| X-06 | Same labour rate on both sides unless a justified change is made. | R-26 (constant prices), R-36 | `reform.ts`, `validate.ts` (W-06) | T-REF-11 |
| X-07 | Expected compliance rate is an explicit input (default 100%). | R-39, R-40 | `costing.ts` | T-COST-04 |
| X-08 | Baseline toggle: current settings vs no instrument (sunsetting remake); both always computed. | N-01 | `reform.ts#applyMasks`, `aggregate.ts#aggregateOption` | T-REF-14, W-21 |
| X-09 | 10-year total and IA threshold 1 indicator. | N-02, N-03 | `aggregate.ts#aggregateOption` | T-RBE-10 |
| X-10 | Users edit only what changes: copy-on-reform and a field-level diff. | Brief §6 | `reform.ts#copyCurrentToReformed`, `reform.ts#reformDiff` | T-REF-12 |
| X-11 | Extensions read results and can't change the RBE. | Brief ground rules; DECISIONS #44 | `extensions.ts#runExtensions` | T-EXT-01 |
| X-12 | Tidy export with ABS-aligned identifiers, for econometric work. | DECISIONS #44, #50 | `tidy.ts#toTidyRows` | T-TIDY-01 |
| X-13 | Exact decimal arithmetic; versioned, strict schema; pure, deterministic engine. | Brief technical stack | `decimal.ts`, `schema.ts`, `migrate.ts#loadProposalFile` | T-NUM-01, T-SCH-01..03 |
| X-14 | Provenance labels on inputs; unconfirmed model estimates mark results as a draft. | R-36 (reasonable, defensible assumptions); DECISIONS #58-#59 | `schema.ts#ProvenanceSchema`, `validate.ts#unconfirmedEstimates` | T-PROV-01, W-22 |
| X-15 | Pasted drafts (saved files or AI replies) are validated before loading. | DECISIONS #60 | `migrate.ts#importDraft` | T-DRAFT-01, T-E2E-06 |
| X-16 | One shared current regime; each reformed version follows it except for the fields the reform changes. | Brief §6 ("users only edit what changes") | `src/ui/model.ts#rebaseReformed`, `src/ui/model.ts#updateCurrentObligation` | T-UI-01..08 |
| X-17 | The web app shows the RBE table in the framework's layout for every option, with the net verdict, gross figures, context, waterfall and breakdowns. | R-18 to R-21, R-34; brief §5-6 | `src/ui/pages/ResultsPage.tsx#RbeTable`, `src/ui/components/Charts.tsx#WaterfallChart` | T-E2E-01..05 |
| X-18 | Privacy by design: no network requests (enforced by a Content-Security-Policy), data kept in the browser or exported files. | Brief ground rules; DECISIONS #37 | `src/ui/persistence.ts#saveProposal` | T-E2E-06, T-E2E-07 |
| X-19 | Accessibility: WCAG 2.2 A/AA checked with axe on every page. | Brief technical stack | `src/ui/components/fields.tsx#QuantityField` | T-E2E-08 |

## 3. Ambiguities and proposed interpretations

**Status (6 October 2026):** all items below were approved by the project owner, as recorded in `DECISIONS.md`.

### A-01 Delay-cost formula **[approved]**

The RBM gives a definition (pp. 2–3), one worked example (p. 10), and an instruction to contact OIA. Four gaps:

1. **Reference point for "ready".** The p. 10 example measures readiness from *lodgement*, but an application delay happens *before* lodgement. The prompt's `application + approval − ready` formula is only coherent if all three are measured from the same start point.
2. **"Lost sales" vs "loss of net income".** p. 10 uses both terms. Revenue overstates the loss, because the entity also avoids the costs of operating.
3. **"Expenses".** The definition (p. 3) is "expenses *and* loss of income". The prompt's formula counts net income only. OIA's own calculator describes delay costs as "standby expenses + lost income".
4. **Units.** The RBM example uses months. OIA-calc and its Example C use days.

**Proposed rule:**

- Measure everything from **t = 0, when the entity starts preparing its application** (or lodgement, if there is no application delay).
- **Effective delay** = max(0, application delay + approval delay − time until the entity would otherwise be ready to operate).
- **Delay cost per affected entity** = effective delay × (net income forgone per unit of time + additional expenses per unit of time caused by the delay). Additional expenses default to $0. Help text warns against double counting with net income.
- **Delay cost per year** = entities experiencing the delay per year × cost per entity.
- Units: days, weeks or months, chosen per activity. The income rate is entered in the same unit, so no conversion is needed.
- "Lost sales" in the example is read as lost *net* income, consistent with "loss of net income" in the next paragraph.
- "Commence trading" includes an existing business starting a new product or activity (the p. 10 example is selling a product).
- Always show a "seek OIA advice" flag (R-44).

**Check:** application 0 + approval 6 − ready 4 = **2 months** ✓; ready at 0 = 6 months ✓.

### A-02 Work-rate rounding

52.31 × 1.75 = 91.5425. The RBM publishes **$91.54**, and OIA-calc uses 91.54 as its default (cell C9).

**Proposed rule:**

- The engine uses **91.54 exactly**. 52.31 and 1.75 are stored for display ("52.31 × 1.75 = 91.5425, published as $91.54").
- If a user overrides the base wage or the multiplier, the derived rate is rounded to the cent, half-up, mirroring the published figure.
- This choice matters for exact dollars. The labour example is $4,393,920 with 91.54, but $4,394,040 with 91.5425. Both round to $4.4m.

### A-03 The "do-anyway share" (compliance rate, BAU and voluntary retention) **[approved 6 Oct 2026]**

**Plain-language definition.** The *do-anyway share* is the share of an activity that businesses would keep doing even if the rule didn't exist, for their own reasons (e.g. records they need anyway). The tool only counts cost **above** that level. This is the framework's business-as-usual rule (RBM pp. 3, 6). Exported tables use the framework's term "business-as-usual".

**Why one input, not two.** The prompt had a "BAU share" (§2) and a "voluntary retention share" (§6). Both measure what businesses do without the rule, so applying both to one obligation would subtract the same thing twice. One input avoids that. A literal "(cut) × (1 − retention)" rule would also get partial reductions wrong.

**The rule, in four points:**

- The do-anyway share is set once per obligation, as a share of *today's* activity per business. For a brand-new obligation, it is a share of the new activity.
- **Do-anyway level** = do-anyway share × today's cost per business.
- Each version (current and reformed) costs a business only what it requires *above* the do-anyway level, and never less than zero.
- This works per cohort, so exemptions are handled correctly. The expected compliance rate separately scales how many businesses incur the cost.

Worked illustration (synthetic): today's cost is $1,000 per business per year and the do-anyway share is 25%, so the do-anyway level is $250.

| Reform | Saving counted | A literal "(cut) × (1 − share)" rule would give |
|---|---|---|
| Removed outright | $750 | $750 |
| Reduced to $500 (above the do-anyway level) | **$500**: the rule still binds above what firms do anyway | $375 (understated) |
| Reduced to $100 (below the do-anyway level) | **$750**: firms still spend $250 by choice | $675 (overstated) |

Policy illustration (synthetic): a quarterly report takes 4 × 4 h = 16 h a year per business. Businesses would prepare a 4 h annual summary anyway, so the do-anyway share is 25%. The reform requires one 2 h annual report. That is less than businesses already do, so the reformed version adds no burden. The saving is 16 − 4 = **12 h** per business, not the 16 − 2 = 14 h a naive comparison gives.

**Implementation.** Each version's yearly profile is scaled by an effective business-as-usual share. This is the do-anyway share on the reference version, and min(1, do-anyway level ÷ that version's average cost per business) on the other. Lumpy profiles (e.g. every 3 years) therefore never show negative years. Code: `src/engine/reform.ts` (`doAnywayShares`).

### A-04 Annualising overlap and dual running **[approved]**

**Proposed rule:**

- Year 1 is the reform's first year in effect, *including* any overlap.
- In the reform scenario, current obligations stay in force until the overlap ends; in the BAU scenario they apply in all years. So for each year *t*:

  Δ_t = reformed_t × [reformed in force at *t*] − current_t × [current *not* in force at *t*]

- The average is **Σ Δ_t over all T years ÷ T**. Savings lost in the overlap are not made up later.
- **Deferred commencement** (phase-in without dual running) is a separate setting. It gives Δ_t = 0 until the reform starts.
- **Timing convention (implementation):** current-side timing years are calendar years of the analysis window. Reformed-side and transition timing years count from the reformed regime's start. So "one-off in year 1" on the reformed side means the first year the reform applies, and deferring the reform shifts its start-up and transition costs with it.
- Transition costs go in the reform's commencement year.
- **Granularity:** whole years in Phase 1. Overlap in months, with pro-rated ongoing costs, is a possible later refinement.

**Check:** a 1-year overlap gives year-1 Δ = reformed cost only, and savings start in year 2 ✓.

### A-05 Which current-regime costs are sunk? **[approved]**

**Proposed rule:** only costs the entity would incur *in the future* under the current regime can be saved.

| Treatment | Costs |
|---|---|
| **Sunk** (excluded) | Past start-up and one-off costs: systems built, initial training, equipment already bought, initial registrations. |
| **Avoidable** (counted) | Future replacements of existing equipment at end of life (modelled as "every *k* years" from the next replacement year). Maintenance, operating, licence-renewal and periodic audit costs. Start-up costs for **future new entrants**: an annual flow, modelled as an ongoing cost, *not* sunk. |
| **Unavoidable until expiry** | Costs locked in by non-cancellable contracts entered to comply (e.g. a multi-year software licence). Modelled as an obligation-specific overlap. |
| **Not a saving in the RBM** | Resale value of equipment no longer needed (an asset value, not a compliance cost). |

- Current-side one-off items carry a `status: future | alreadyIncurred` field. `alreadyIncurred` is excluded and listed with the reason.
- Activity that firms keep doing out of habit or embedded systems is covered by the do-anyway share (A-03), not treated as sunk cost.

### A-06 Can subsidies push net cost below zero?

**Proposed rule: no.**

- A subsidy offsets only the compliance cost of the obligation (and cohort) it is tied to.
- The offset is capped so that the obligation's net cost on that side, summed over the duration, is ≥ 0. Any excess is a transfer, which is outside the RBM. It is listed in the excluded items and triggers warning W-12.
- Subsidies apply to administrative and substantive costs only, after the BAU adjustment.
- *Removing* a subsidy in a reform raises net compliance cost, which correctly shows as an increase (R-05).
- Net *changes* (Δ) can of course be negative.

### A-07 Ranges: midpoint of the inputs, or of the estimate? **[approved: input midpoints]**

When an input is uncertain, users can enter a range (e.g. "1 to 3 hours"), but the RBE needs one number. There are two ways to get it:

- **Input midpoints** (what the tool does): take the middle of each input range, then calculate.
- **Output midpoint:** calculate everything at the low end and at the high end, then take halfway between the two results.

Illustration (synthetic): a report takes 1–3 hours, 1,000–3,000 businesses do it, and the rate is $100/hour.

| | 1,000 businesses | 3,000 businesses |
|---|---|---|
| **1 hour** | $100,000 | $300,000 |
| **3 hours** | $300,000 | $900,000 |

- **Input midpoints:** 2 h × 2,000 × $100 = **$400,000**. This equals the average of all four cells.
- **Output midpoint:** ($100,000 + $900,000) ÷ 2 = **$500,000**. It uses only the two corners and ignores the mixed cases, so the single "everything high" case pulls it up.
- **When it matters.** The two methods agree when only one input is a range. They diverge when two or more ranged inputs are multiplied. The gap is (width of range A × width of range B) ÷ 4, here (2 × 2,000) ÷ 4 × $100 = $100,000.
- **Why input midpoints.** With independent, symmetric ranges they give the *expected* cost (E[XY] = E[X]·E[Y]), which is the "most likely scenario" the RBM asks for (p. 11). OIA's midpoint rule (p. 11) covers an agency handing OIA a range instead of a number. The tool always produces one number, so that rule isn't triggered.
- **Sensitivity.** The low and high results, and their midpoint, are shown as supplementary information in the Phase 4 sensitivity view.

### A-08 Display and rounding of the RBE table

**Proposed rule:**

- Figures are in $ million to 1 decimal place, rounded half away from zero. Negatives are shown in brackets.
- An exact zero is printed `$0`, as in p. 11. A non-zero value that rounds to 0.0 prints `$0.0` or `($0.0)`, with a footnote.
- Totals are computed from unrounded values. A note appears when the rounded columns don't add up.
- The net verdict uses the exact value. When the change is under $50,000 it is stated in dollars.

### A-09 "Delay costs could be considered as administrative costs, compliance costs, or both" (p. 10)

**Proposed rule:** keep delay as its own category in the RBE breakdowns. The sentence is unclear, and the RBE table doesn't split by category anyway. Logged for OIA advice.

### A-10 Anchoring of "every *k* years"

Over 10 years, "every 2 years" gives 5 occurrences whichever year it starts in. But "every 3 years" gives 4 occurrences from year 1 (years 1, 4, 7, 10) and 3 from year 4. OIA-calc's Example B uses an initial course in year 1, then refreshers in years 4, 7 and 10.

**Proposed rule:** "every *k* years" requires a **first occurrence year** (default 1), and the year-by-year profile is always shown.

### A-11 Duration

The RBM only contemplates shorter periods (p. 6).

**Proposed rule:**

- Durations of 1–10 years are allowed. Anything other than 10 requires a justification.
- Durations over 10 years are blocked unless the user records OIA agreement. *(Alternative: allow them with a warning.)*

### A-12 Individuals doing work-related tasks; sole traders

**Proposed rule:**

- Sole traders and the self-employed are **businesses**, at the work rate.
- An employee meeting an occupational requirement *in their own time* is an **individual**, at the leisure rate (p. 9: "not in the course of their employment").
- If the employer pays for that time, the cost falls on the **business**, at the work rate.

### A-13 Volunteers in community organisations **[approved: $41 RBM leisure rate]**

The RBM's work rate is defined for employees (p. 9), so it doesn't fit volunteers.

**Decision (6 Oct 2026, second round):** volunteer time is valued at the RBM non-work rate of **$41/h**. Paid staff stay at the work rate. Replacement cost (with a justification) is the accepted override for skilled tasks. This replaces the earlier "half the full-time rate" choice.

**Alternatives considered:**

| Approach | Rate | Traces to RBM? | When it fits |
|---|---|---|---|
| RBM leisure rate | $41/h | Yes. p. 9 values time "not in the course of their employment"; p. 13 | The volunteer's own time is the cost (the RBM's own concept). **Recommended default.** |
| Replacement cost | Market wage for the task + on-costs, e.g. a bookkeeper | Partly (R-50: a more accurate rate, with evidence) | Skilled tasks (treasurer, accounts) where the organisation would otherwise pay someone |
| Half the work rate | $45.77/h | No (a user policy choice) | Pragmatic; within 12% of $41 |

The volunteer rate is stored separately in `parameters.ts` (`rates.volunteer`), so it can be changed in one place.

### A-14 Which stakeholder group for the R-14 exceptions? **[resolved]**

- GBEs and foreign-government-owned businesses go in **Business**.
- Public universities get no special handling (user decision, 6 Oct 2026). The user picks the group, as for any other entity.

### A-15 Mandatory payments to *non-government* bodies

The R-12 exclusion covers charges "payable to government" and insurance premiums "where remitted to government". This leaves some mandatory payments unclear.

**Proposed rule:** these are in scope as **purchase costs**:

- fees to private certifiers or accredited bodies;
- industry scheme memberships required by regulation;
- mandatory insurance bought from private insurers.

The screener explains why.

### A-16 GST on purchase costs

**Proposed rule:** enter purchase costs excluding GST, because taxes are out of scope (R-12). The help text explains this.

### A-17 Size cohorts

The RBM names small, medium and large cohorts (p. 8) but doesn't define them.

**Proposed rule:**

- Default to ABS employment-size bands: small < 20 employees, medium 20–199, large 200+. To be verified against the ABS source and recorded in `data/SOURCES.md` in Phase 3.
- Users can redefine the bands, for example by turnover.
- The bands drive the "staff larger than the cohort allows" warning.

### A-18 State/territory costs in a Commonwealth-only proposal

**Proposed rule:** activities sourced to a state or territory count only when the proposal is flagged inter-jurisdictional under R-33. Otherwise they are excluded and warning W-15 is raised.

### A-19 Two different meanings of "compliance"

The *expected compliance rate* (the share of entities that comply, R-39) is different from the *compliance vs enforcement* classification (Appendix 3).

**Proposed rule:** use distinct UI labels and separate fields. An enforcement-classified share is removed by construction, so it can never reach the RBE.

### A-20 Delay costs for individuals

R-42 frames delay as waiting "to commence trading". However, an individual waiting on an approval before starting income-earning work (e.g. an occupational licence) also loses income.

**Proposed rule:** allow delay costs for individuals in that case only, with a "seek OIA advice" flag.

### A-21 Transition costs aren't named in the RBM

Familiarisation, systems changes and retraining are the *start-up costs* (p. 8) of the reformed regime.

**Proposed rule:** they are in scope. Each item takes the category of its nature: familiarisation is usually administrative/labour; systems are usually substantive/purchase. They go in the commencement year, including any preparation done during a pre-commencement lead time.

## 4. Differences between the prompt and the RBM (the RBM wins)

All of these are logged in `DECISIONS.md`.

| ID | Prompt says | RBM says | Resolution |
|---|---|---|---|
| P-01 | $52.31 is "AWE-based, after tax adjustment". | "Based on average weekly earnings, but adjusted to *include* income tax". The footnote cites ABS *Employee Earnings and Hours* (Jan 2024, Data Cube 6), not the AWE series. | Record the RBM wording and source in `parameters.ts`. No numeric effect. |
| P-02 | Next rate update "scheduled February 2028". | "Scheduled for February 2028 … though this is yet to be confirmed." | Record as unconfirmed. |
| P-03 | Delay cost = entities × effective delay × net income forgone. | Delay costs are "expenses *and* loss of income" (p. 3). | Add an optional "additional expenses during the delay" input (A-01). |
| P-04 | Midpoint of each *input* range. | OIA uses the midpoint of *estimates* presented as ranges. | Keep input midpoints and show the output-range midpoint in the sensitivity view (A-07). |
| P-05 | One-off costs default to year 1, but may be put in another year. | Start-up costs are incurred in the first year (p. 8). | No conflict: a later one-off is a "varying cost" (p. 6) and annualises the same way. Label year-1 one-offs "start-up". |
| P-06 | Purchase formula for businesses and community organisations. | Same, but individuals' compliance costs are in scope (pp. 1, 5). | Allow purchase costs for individuals too (e.g. a required safety device). |
| P-07 | "1 decimal place" format. | The p. 11 example prints exact zero as `$0`, not `$0.0`. | Follow the RBM for zero cells (A-08). |
| P-08 | Separate BAU share and retention inputs. | A single BAU concept (pp. 3, 6). | Unify them as the do-anyway share (A-03). |

## 5. Things outside the RBM PDF that change how it applies

The new Impact Analysis Framework came into effect on 1 July 2026. The OIA web page for the RBM notes that the PDF's references to the previous IA framework (e.g. "Impact Analysis Equivalent", "certification letter") "are no longer current".

| ID | Source | What it says | Effect on this tool |
|---|---|---|---|
| N-01 | IAF-PG pp. 21–22 | Remaking a **sunsetting legislative instrument**, "as is" or with amendments, is assessed "relative to the status quo of there being no instrument in place". Burden changes from remaking an instrument are not included in the Estimated Annual Impact on Regulatory Burden. | **Material to the core use case.** If the reform is delivered by remaking a sunsetting instrument, the official RBE baseline is *no regulation*, not the current regime. The reformed regime is costed as new; the saving against today's regime becomes context only. **Approved (6 Oct 2026):** a baseline toggle, "current settings" vs "no instrument". Both figures are always computed. The toggle chooses which one fills the RBE table, and the other is shown as context. The screener sets the default from how the change will be legally made, and the tool warns if the toggle contradicts that answer. Proposed interpretation: under "no instrument", the reformed regime's ongoing costs plus its transition costs are counted. Set-up costs already sunk under the current regime are not re-counted as if firms started from scratch. Flagged "seek OIA advice". |
| N-02 | Dashboard IA template; IAF-PG p. 11 | The Dashboard IA reports regulatory burden as "$X over 10 years". The final RBE is "a point estimate of the average annual change in regulatory burden over 10 years (without discounting)". | **Approved (6 Oct 2026):** report a 10-year total alongside the RBE table. Where the duration is under 10 years, the total covers the policy's life; average = total ÷ duration (p. 6). |
| N-03 | IAF-PG p. 7; Preliminary Analysis checklist | IA threshold 1: a change in burden of **$20 million or more in total over 10 years**. The checklist's per-entity test is Y1 = $20m ÷ number of entities. | Show a threshold indicator ("likely meets IA threshold 1; confirm with OIA") and a per-entity comparison. It is unclear whether the threshold applies to reductions; proposed: use the absolute value. **[decision needed]** |
| N-04 | IAF-PG p. 20 | Agencies should retain the final "regulatory burden workbook" and share it with OIA. | The `.xlsx` export (Phase 4) should be a formula-driven workbook OIA can audit, not just values. |
| N-05 | OIA-calc | OIA's official calculator uses 91.54. It describes delay costs as "standby expenses + lost income", and gives four illustrative examples with stated answers. It also has formula defects (see `docs/oia_calculator_review.md`). | Settles A-02 and supports A-01. Its *stated* example answers become extra illustrative tests. Its *computed* outputs are not a validation benchmark. |
