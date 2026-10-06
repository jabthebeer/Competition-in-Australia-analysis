# Phase 0 proposal: engine data model, Phase 1 test list, feasibility

**Status:** Approved by the project owner on 6 October 2026, with the changes recorded in `DECISIONS.md`. The implemented schema in `src/engine/schema.ts` is authoritative where it differs from this sketch.

Interpretation IDs (A-xx, N-xx, P-xx) refer to `docs/framework_traceability.md`.

## 1. Engine data model

### 1.1 Design principles

- **One model for every proposal type.** A proposal holds options. An option holds obligations. Each obligation has a `current` side and a `reformed` side, and either side may be `null`.

  | Proposal type | `current` | `reformed` |
  |---|---|---|
  | New regulation | `null` everywhere | populated |
  | Outright repeal | populated | `null` everywhere |
  | Reform (the default) | populated | populated |

  The proposal type is only a UI preset.
- **The engine is a pure function.** `computeProposal(proposal, parameters) → ProposalResult`. There is no I/O, no clock and no randomness.
- **The RBE can't be contaminated.** The schema has no fields for benefits, discount rates, inflation or excluded cost types, and it rejects unknown keys. Excluded items are carried in a separate `excluded` list that the RBE never reads.
- **Exact money arithmetic.**
  - Inputs are JSON numbers, converted via `new Decimal(String(n))`.
  - All arithmetic uses `decimal.js` at 40 significant digits.
  - Outputs are exact decimal strings. Rounding happens only when values are displayed or exported.
  - Integer cents won't work, because annualising (÷ 3, ÷ 7) and the do-anyway ratio (A-03) produce non-terminating values.
- **Point estimates from ranges.** Any numeric input can be a `Quantity`: a number, or a `{ low, high }` range. The point estimate is the midpoint (A-07). The range is kept for sensitivity analysis only.
- **Defaults are visible and overrides are audited.** Every default comes from `parameters.ts`. Every non-default rate, duration or classification needs an `Override { justification, source }`, which feeds the assumptions register.

### 1.2 Schema sketch

TypeScript shown for readability. It will be implemented as `zod` schemas in `src/engine/schema.ts`.

```ts
type Quantity = number | { low: number; high: number };          // range → midpoint
interface Source   { description: string; url?: string; vintage?: string; accessed?: string }
interface Override { justification: string; source: Source }

// ---------- File envelope (versioned; old files are migrated on load) ----------
interface ProposalFile {
  schemaVersion: 1;
  savedAt?: string;                 // set on export; the engine never reads the clock
  proposal: Proposal;
}

// ---------- Proposal ----------
interface Proposal {
  id: string;
  title: string;
  description?: string;
  proposalType: "reform" | "new" | "repeal";            // UI preset only
  durationYears: number;                                // 1–10, default 10 (A-11)
  durationOverride?: Override;                          // required if ≠ 10
  jurisdiction: "commonwealthOnly" | "interJurisdictional";   // R-33 (A-18)
  baseline: "statusQuo" | "noInstrument";               // N-01: toggle approved; both always computed
  parameterVintage: string;                             // e.g. "RBM-2026-07"; must match parameters.ts
  rates: RateTable;
  populations: Population[];
  options: Option[];
}

interface RateTable {                                   // proposal-wide; sides refer to rates by id
  work:    { hourly: number; base: number; multiplier: number; override?: Override };   // 91.54 = 52.31 × 1.75 (A-02)
  leisure: { hourly: number; override?: Override };                                     // 41
  custom:  { id: string; label: string; kind: "work" | "leisure"; hourly: number; override: Override }[];
}

interface Population {                                  // who is affected, and how many
  id: string;
  label: string;                                        // e.g. "Small importers"
  group: "business" | "communityOrg" | "individual";
  cohort: "small" | "medium" | "large" | "all";         // R-32 (A-17)
  count: Quantity;                                      // denominator for per-entity results
  industry?: string;                                    // ANZSIC code; links to ABS entry/exit data (scope expansion, #42)
  source?: Source;
  flags?: {
    nonResident?: boolean;                              // R-53 → W-04
    g2gException?: "gbe" | "publicUniversity" | "foreignGovOwned";   // R-14 (A-14)
  };
}

// ---------- Option ----------
interface Option {
  id: string;
  name: string;                                         // "Outright repeal", "Light version A", …
  isStatusQuo?: boolean;
  timing: { reformStartYear: number; overlapYears: number };   // defaults 1 and 0 (A-04)
  obligations: Obligation[];
  transitions: Obligation[];                            // reformed-only switching costs (A-21)
}

// ---------- Obligation: the unit of comparison ----------
interface Obligation {
  id: string;
  name: string;
  group: "business" | "communityOrg" | "individual";
  category: "administrative" | "substantive" | "delay";
  jurisdiction: "commonwealth" | "stateTerritory";
  legalReference?: { instrument: string; provision?: string };   // e.g. "CCA Sch 2 (ACL)", "s 131" (#42)
  scope: {                                              // Appendix 3 (A-19)
    classification: "compliance" | "enforcement" | "split";   // default "compliance" (R-57)
    complianceShare?: number;                           // required for "split"
    override?: Override;                                // required to depart from the default (R-59)
  };
  doAnywayShare: Quantity;                              // A-03: share of today's activity businesses would do anyway; default 0
  doAnywaySource?: Source;
  tags: Tag[];                                          // "commonIndustryPractice" | "outsourcedService" | "governmentFee" | "tax" | …
  levers: Lever[];                                      // descriptive: "lessFrequent" | "simplerForm" | "threshold" | …
  current: Side | null;
  reformed: Side | null;
  timingOverride?: { reformStartYear?: number; overlapYears?: number };   // e.g. locked-in contracts (A-05)
}

interface Side {
  costType: "labour" | "purchase" | "delay";
  timing: Timing;
  status?: "future" | "alreadyIncurred";                // current side only; alreadyIncurred = sunk (A-05)
  lines: Line[];                                        // one per population/cohort this side applies to
}

type Timing =
  | { type: "oneOff";      year: number }                          // default year 1 = start-up
  | { type: "ongoing";     startYear: number; endYear?: number }   // constant
  | { type: "everyKYears"; k: number; firstYear: number }          // A-10
  | { type: "schedule";    factors: number[] };                    // share of the annual cost in each year 1..T

interface Line {
  populationId: string;
  entities?: Quantity;                                  // default = population count; 0 = exempt
  complianceRate: Quantity;                             // expected compliance rate, default 1 (X-07)
  labour?:   { hours: Quantity; timesPerYear: Quantity; staff?: Quantity; rateId: string };
  purchase?: { unitCost: Quantity; timesPerYear: Quantity };
  delay?:    { unit: "days" | "weeks" | "months";       // A-01
               applicationDelay: Quantity; approvalDelay: Quantity; readyAfter: Quantity;
               netIncomePerUnit: Quantity; extraExpensesPerUnit?: Quantity;
               waitingOnGovernment: boolean };          // W-03
  subsidy?:  { perEntityPerActiveYear: Quantity; source: Source };   // A-06
  note?: string;
}
```

### 1.3 Calculation pipeline

This runs for each option, obligation, side and line.

1. **Point values.** Resolve every `Quantity` to its point value.
2. **Gross cost in an active year** (R-39 to R-41, A-01):

   | Cost type | Formula |
   |---|---|
   | Labour | hours × rate × timesPerYear × entities × complianceRate × staff (staff = 1 for individuals) |
   | Purchase | unitCost × timesPerYear × entities × complianceRate |
   | Delay | entities × complianceRate × effectiveDelay × (netIncome + extraExpenses) |

3. **Year profile.** G_t for t = 1…T, from `Timing` (R-29 to R-31).
4. **Do-anyway adjustment** (A-03). Multiply by (1 − b_side), where b is the do-anyway share on the reference side and min(1, do-anyway level ÷ average gross per entity) on the other.
5. **Enforcement share.** Multiply by `complianceShare`. The removed share goes to `excluded` (R-55 to R-60).
6. **Subsidy.** Subtract it, capping so the duration total stays ≥ 0. Any excess goes to `excluded` (A-06).
7. **Sunk and out-of-scope items.** `alreadyIncurred`, out-of-scope tags, and state items in a Commonwealth-only proposal are diverted to `excluded`.
8. **Scenario masks** (A-04). Δ_t = reformed_t × in-force_reformed(t) − current_t × (1 − in-force_current(t)). With baseline `noInstrument`, the current side is treated as absent (N-01).
9. **Annualise.** Average annual Δ = Σ_t Δ_t ÷ T. The duration total is Σ_t Δ_t (N-02).
10. **Aggregate** to the RBE table, gross increases and reductions, breakdowns, per-entity results, the jurisdiction split and the waterfall.

### 1.4 Output API

Future modules attach here without touching the RBE.

```ts
function computeProposal(p: Proposal, params = PARAMETERS): ProposalResult;

interface ProposalResult {
  engineVersion: string; parameterVintage: string; schemaVersion: 1;
  options: OptionResult[];
  warnings: Warning[];          // { code: "W-01".., severity, optionId?, obligationId?, message, ref: "RBM p. 4" }
  assumptions: AssumptionRow[]; // every non-default input with its justification and source
}

interface OptionResult {
  optionId: string;
  rbe: { business: Dec; communityOrg: Dec; individual: Dec; total: Dec };  // average annual Δ, $ (exact strings)
  durationTotal: Dec;                                    // N-02: 10-year total (approved)
  alternativeBaseline: { rbe: OptionResult["rbe"]; durationTotal: Dec };  // the baseline not selected, shown as context
  verdict: { kind: "increase" | "reduction" | "none"; amount: Dec };
  gross: { increases: Dec; reductions: Dec };
  context: { currentAnnual: Dec; reformedAnnual: Dec; transitionAnnual: Dec; shareRemoved: Dec | null };  // labelled "context, not RBE"
  waterfall: { step: "current" | "removed" | "reduced" | "increased" | "new" | "transition" | "reformed"; value: Dec }[];
  deltaByYear: Dec[];                                    // Δ_t, t = 1..T
  breakdowns: Record<"group" | "category" | "cohort" | "timing" | "jurisdiction" | "obligation", Record<string, Dec>>;
  perEntity: { populationId: string; current: Dec; reformed: Dec; change: Dec; cliffFlag?: boolean }[];
  jurisdictionSplit: { commonwealth: Dec; stateTerritory: Dec };
  items: ItemResult[];                                   // full audit trail: inputs used, formula, profile, annualised value
  excluded: ExcludedItem[];                              // enforcement share, out of scope, sunk, excess subsidy — each with reason and RBM ref
}
```

**Future expansion.** A benefits panel, competition note or ABS data helper would be separate modules, e.g. `src/extensions/benefits/`. Each would take `(Proposal, ProposalResult)` read-only and return its own result type. None of them can write to `rbe`, and the RBE function never imports them.

### 1.5 Example file (illustrative, synthetic data)

This is the prompt's illustrative quarterly-to-annual reform, expressed in the schema.

```json
{
  "schemaVersion": 1,
  "proposal": {
    "id": "illustrative-reform", "title": "ILLUSTRATIVE: quarterly report becomes annual",
    "proposalType": "reform", "durationYears": 10, "jurisdiction": "commonwealthOnly",
    "baseline": "statusQuo", "parameterVintage": "RBM-2026-07",
    "rates": { "work": { "hourly": 91.54, "base": 52.31, "multiplier": 1.75 }, "leisure": { "hourly": 41 }, "custom": [] },
    "populations": [{ "id": "biz", "label": "Regulated businesses (synthetic)", "group": "business", "cohort": "all", "count": 10000 }],
    "options": [{
      "id": "opt-a", "name": "Annual reporting", "timing": { "reformStartYear": 1, "overlapYears": 0 },
      "obligations": [{
        "id": "report", "name": "Periodic report", "group": "business", "category": "administrative",
        "jurisdiction": "commonwealth", "scope": { "classification": "compliance" }, "doAnywayShare": 0,
        "tags": [], "levers": ["lessFrequent", "simplerForm"],
        "current":  { "costType": "labour", "timing": { "type": "ongoing", "startYear": 1 },
                      "lines": [{ "populationId": "biz", "complianceRate": 1,
                                  "labour": { "hours": 4, "timesPerYear": 4, "staff": 1, "rateId": "work" } }] },
        "reformed": { "costType": "labour", "timing": { "type": "ongoing", "startYear": 1 },
                      "lines": [{ "populationId": "biz", "complianceRate": 1,
                                  "labour": { "hours": 2, "timesPerYear": 1, "staff": 1, "rateId": "work" } }] }
      }],
      "transitions": [{
        "id": "familiarise", "name": "Familiarisation with new rules", "group": "business", "category": "administrative",
        "jurisdiction": "commonwealth", "scope": { "classification": "compliance" }, "doAnywayShare": 0,
        "tags": [], "levers": [], "current": null,
        "reformed": { "costType": "labour", "timing": { "type": "oneOff", "year": 1 },
                      "lines": [{ "populationId": "biz", "complianceRate": 1,
                                  "labour": { "hours": 1, "timesPerYear": 1, "staff": 1, "rateId": "work" } }] }
      }]
    }]
  }
}
```

Expected result: Δ = 1,830,800 − 14,646,400 + 915,400 ÷ 10 = **−12,724,060 a year**, which prints as RBE **($12.7)**.

## 2. Proposed Phase 1 file layout

```
regulatory-burden-tool/
  package.json, tsconfig.json, vitest.config.ts
  src/engine/
    parameters.ts   schema.ts   annualise.ts   costing.ts   reform.ts
    aggregate.ts    validate.ts scope.ts (exclusion catalogue and screener questions, as data)
    format.ts (RBE number formatting)   index.ts (public API)
  src/cli/rbe.ts    # npm run rbe -- examples/illustrative-reform.json
  examples/         # illustrative, synthetic proposal files only
  tests/engine/
```

`scope.ts` and `format.ts` are additions to the suggested structure, logged in `DECISIONS.md`.

## 3. Phase 1 test list

- All monetary inputs below are **illustrative or synthetic** unless marked *RBM* (a framework worked example) or *OIA-calc* (OIA's own training examples, with OIA's stated answers).
- "RBE" strings are the formatted cells: Business | Community organisations | Individuals | Total.

**Implementation note (Phase 1).** Every test below is implemented under the same ID in `tests/engine/`. Five tests were added:

- T-SCOPE-01b: the time to pay a fee stays in scope;
- T-SCH-03: structural errors are reported;
- T-EXT-01: extensions can't change the RBE;
- T-TIDY-01: the tidy export;
- an overall check that every warning has a reference.

The suite has 79 tests in total. Run `npm run check`.

### Parameters and rates

| ID | Test | Expected |
|---|---|---|
| T-PAR-01 | Default work rate (*RBM* p. 12) | `91.54` exactly; display string "52.31 × 1.75 = 91.5425 → $91.54"; an overridden base or multiplier derives a rate rounded to the cent |
| T-PAR-02 | Default leisure rate (*RBM* p. 13) | `41` |
| T-PAR-03 | Parameter metadata | Each rate has a source, vintage and next-update note ("February 2028, unconfirmed"). A proposal with a mismatched `parameterVintage` raises a warning. |

### Costing formulas

| ID | Test | Expected |
|---|---|---|
| T-COST-01 | Labour, business (prompt example): 2 h × $91.54 × 24 × 1,000 × 1 staff | $4,393,920.00 → `$4.4 \| $0 \| $0 \| $4.4` |
| T-COST-02 | Labour, individuals: 0.5 h × $41 × 2 × 100,000 (no staff factor) | $4,100,000 → Individuals `$4.1` |
| T-COST-03 | Purchase: $250 × 2 × 4,000 entities (no staff factor) | $2,000,000 |
| T-COST-04 | Compliance rate and BAU share on a new obligation: gross $1,000,000; *v* = 20%; compliance 80% | $800,000 with *v* only; $640,000 with both |
| T-COST-05 | Subsidy (A-06): cost $100,000 with a $30,000 subsidy; then with a $150,000 subsidy | $70,000; then $0, warning W-12, and $50,000 listed as an excluded transfer |
| T-COST-06 | Range → midpoint: T-COST-01 with hours `{low: 1, high: 3}` | identical to T-COST-01 |

### Delay costs

| ID | Test | Expected |
|---|---|---|
| T-DEL-01 | *RBM* p. 10: approval 6 months, application 0, ready at 4 months; then ready at 0 | effective delay 2 months; 6 months |
| T-DEL-02 | Application 1 + approval 6 − ready 4; then ready at 8 | 3 months; 0 (floored) |
| T-DEL-03 | 10 entities/year × 2 months × $50,000 net income/month; then plus $5,000/month extra expenses | $1,000,000/yr; $1,100,000/yr |
| T-DEL-04 | Faster-approval reform: 100 applications/yr, approval 6 → 3 months, ready at 0, $10,000/month | Δ −$3,000,000/yr → `($3.0)` |
| T-DEL-05 | *OIA-calc* Example C: 9 applications/yr, 35 → 19 days, $13,800/day | Δ −$1,987,200/yr → `($2.0)`; duration total −$19,872,000. OIA states $19.87m unsigned; under the RBM a reduction is negative (p. 11). |

### Annualisation

| ID | Test | Expected |
|---|---|---|
| T-ANN-01 | One-off $1,000,000 in year 1 | $100,000/yr over 10 years; $250,000/yr over 4 years |
| T-ANN-02 | Constant ongoing cost | annualised = year-1 cost |
| T-ANN-03 | Every 2 years over 10 (*RBM* p. 8), first year 1 or 2 | 5 occurrences ÷ 10 in both cases |
| T-ANN-04 | Every 3 years over 10 (A-10) | first year 1 → 4 occurrences (years 1, 4, 7, 10); first year 4 → 3 |
| T-ANN-05 | Explicit schedule `[1, 1, 0.5, 0, …]` | Σ factors × annual cost ÷ T |
| T-ANN-06 | 3-year duration | profile truncated at year 3; one-off ÷ 3 |
| T-ANN-07 | Real terms, no discounting | A file containing `discountRate`, `inflation` or `benefits` fails schema validation. Results never depend on the year except through timing. |
| T-ANN-08 | *OIA-calc* Examples A, B, D, checked against OIA's *stated* answers. A uses a $150/h override with a justification. | A: $3,630,000 over 10 yrs → `$0.4`. B: $9,611,700 → `$1.0`. D: $54,208,200 → `$5.4` |

### RBE table and aggregation

| ID | Test | Expected |
|---|---|---|
| T-RBE-01 | *RBM* p. 11 deregulatory example: −$400,000/yr, business | `($0.4) \| $0 \| $0 \| ($0.4)` exactly, under the caption and header from R-19 |
| T-RBE-02 | *RBM* p. 6 inter-jurisdictional: Commonwealth −$10m, states +$2m | Total `($8.0)`; split Commonwealth `($10.0)`, State/territory `$2.0` |
| T-RBE-03 | A state item in a Commonwealth-only proposal | excluded from the RBE; warning W-15 |
| T-RBE-04 | Mixed signs: Business +$3m, Individuals −$5m | Total `($2.0)`; gross increases `$3.0`, gross reductions `($5.0)` |
| T-RBE-05 | Verdict strings | "Net increase in regulatory burden of $X million a year" / "Net reduction of $X million a year" / "No net change" |
| T-RBE-06 | Formatting (A-08): 3 × $40,000 in different groups; ±$50,000; 2 dp; exact dollars | Cells `$0.0`, Total `$0.1`, plus a rounding note; `$0.1` / `($0.1)`; `$4.39`; `$4,393,920` |
| T-RBE-07 | Several options, including the status quo | one RBE table per option; status quo is all `$0`; comparison rows line up |
| T-RBE-08 | Breakdowns (by group, category, cohort, timing, jurisdiction, obligation) | each reconciles exactly to the total |
| T-RBE-09 | Per-entity change by cohort | Δ ÷ population count, per cohort |
| T-RBE-10 | 10-year total (N-02, approved) | Σ Δ_t; equals 10 × average annual when T = 10; T-REF-01 gives −$127,240,600 |

### Reform comparison

| ID | Test | Expected |
|---|---|---|
| T-REF-01 | Illustrative reform (§1.5) | current $14,646,400; reformed $1,830,800; transition $915,400 → $91,540/yr. Net **−$12,724,060** → `($12.7)`. Context: 87.5% of current burden removed (86.875% net of transition). |
| T-REF-02 | Identity: reformed = deep copy of current | Δ_t = 0 in every year and every breakdown |
| T-REF-03 | Empty current regime | identical to a standalone new-regulation costing (T-COST-01) |
| T-REF-04 | Removal with retention (A-03): $1,000,000/yr removed, *v* = 25% | Δ −$750,000 (−$1,000,000 when *v* = 0) |
| T-REF-05 | Reduction above the do-anyway level: $1,000/entity → $500, *v* = 25% | saving $500/entity |
| T-REF-06 | Reduction below the do-anyway level: $1,000 → $100, *v* = 25% | saving capped at $750/entity |
| T-REF-07 | 1-year overlap (A-04) on T-REF-01 | year-1 Δ = +$1,830,800 (reformed only); years 2–10 −$12,815,600; average **−$11,259,420** → `($11.3)` |
| T-REF-08 | 1-year deferred commencement on T-REF-01 | year-1 Δ = 0; average −$11,442,500 → `($11.4)` |
| T-REF-09 | Small-business exemption. Cohorts (synthetic): small 8,000, medium 1,500, large 500. Quarterly report at $1,464.64/entity/yr; small cohort set to 0 entities | Δ −$11,717,120 → `($11.7)`; per-entity change: small −$1,464.64, medium $0, large $0; cliff flag on medium |
| T-REF-10 | Sunk costs (A-05) | `alreadyIncurred` one-off excluded and listed, warning W-08; a future equipment replacement every 5 years from year 3 is counted as avoidable |
| T-REF-11 | Rate consistency | reformed side defaults to the current rate; a changed rate without justification raises W-06; with justification, no warning |
| T-REF-12 | Copy-on-reform diff | the diff lists only the changed fields (e.g. `hours`, `timesPerYear`) |
| T-REF-13 | Waterfall | current − removed − reduced + increased + new = reformed; + transition = net change; reconciles to the RBE total |
| T-REF-14 | Baseline toggle (N-01, approved) on T-REF-01 | "Current settings": RBE `($12.7)`. "No instrument": RBE = reformed regime + transition vs nothing = $1,830,800 + $91,540 = $1,922,340 → `$1.9`. The non-selected figure appears as context. |

### Scope and exclusions

| ID | Test | Expected |
|---|---|---|
| T-SCOPE-01 | Property test: adding any excluded item (enforcement, government fee, tax, fine, indirect/competition, court administration, international-obligation performance, non-exception G2G, sunk) to any proposal | RBE unchanged; the item appears in `excluded` with its RBM reference |
| T-SCOPE-02 | Compliance/enforcement split 60/40 (R-60) | 60% counted, 40% excluded |
| T-SCOPE-03 | Screener answers map to the correct in-scope/out-of-scope result and RBM page | table-driven test over `scope.ts` |

### Numbers, schema and CLI

| ID | Test | Expected |
|---|---|---|
| T-NUM-01 | Exact arithmetic | 10 × $0.10 = $1.00 exactly; components sum exactly to totals; $1,000,000 ÷ 3 years gives consistent displays and a consistent sum |
| T-SCH-01 | Versioned file | v1 round-trip (export → import is identical); unknown version rejected with a clear message; the migration registry is exercised with a synthetic v0 fixture |
| T-SCH-02 | Determinism | the same input gives byte-identical output |
| T-CLI-01 | CLI | `npm run rbe -- examples/illustrative-reform.json` prints the framework-format table showing `($12.7)` |

### Validation warnings

Each warning has at least one firing test and one non-firing test.

| ID | Warning | RBM |
|---|---|---|
| W-01 | Fee, levy, charge or tax entered as a purchase cost | p. 4 |
| W-02 | Outsourced professional service entered as labour | p. 12 |
| W-03 | Delay cost where the entity isn't waiting on government to commence | p. 10 |
| W-04 | Leisure rate applied to non-resident individuals | p. 13 fn 5 |
| W-05 | Default rate overridden without a justification or source | p. 12 |
| W-06 | Labour rate differs between the current and reformed sides | p. 6 |
| W-07 | Do-anyway share of 0% on an item tagged "common industry practice" | p. 3 |
| W-08 | Current-side one-off not confirmed as future or already incurred (sunk) | — (A-05) |
| W-09 | Reform with no transition costs ("Will entities need time to learn the new rules?") | p. 8 |
| W-10 | Exemption threshold creates a cliff effect | p. 8 |
| W-11 | Implausible inputs: times per year > 365 per staff member; staff above the cohort ceiling; hours per occurrence > 24 | p. 7 |
| W-12 | Subsidy larger than the cost it offsets | p. 3 |
| W-13 | G2G obligation not on a GBE, public university or foreign-government-owned business | pp. 4–5 |
| W-14 | Enforcement classification without a demonstrating justification; or an item tagged "enforcement" but classified as compliance | p. 15 |
| W-15 | State/territory item in a Commonwealth-only proposal | p. 6 |
| W-16 | Duration ≠ 10 years without a justification | p. 6 |
| W-17 | Any delay cost entered: "seek OIA advice" (information only) | p. 10 |

## 4. Feasibility issues

### F-01 OIA already publishes an official calculator (high impact on positioning)

OIA released a *Regulatory Burden Estimate calculator* (.xlsx, "Version July 2026") alongside this RBM. The new IA Practical Guide (p. 7) points agencies to it. This tool will be compared with it, so it must:

- clearly add value beyond it. It can: the official calculator has no reform mode, no split by stakeholder group, no cohorts, no exclusion screener, no assumptions trail, and only one entity count for all items;
- explain any differences in its results.

### F-02 The official calculator has formula defects (verified)

I filled OIA's own four training examples into the workbook and recalculated it in LibreOffice (full details in `docs/oia_calculator_review.md`). Examples B and D match; B only by coincidence. It doesn't reproduce the other two of OIA's own answers:

| OIA example | OIA's stated answer | Workbook output |
|---|---|---|
| Example A | $3.63m | $3.267m |
| Example C | $19.87m | $0.125m |

There are four main causes:

- Year 1 omits recurring costs.
- Both delay formulas are mis-specified.
- Set-up labour ignores staff per entity.
- The period-of-analysis input is ignored.

**Implication:** Phase 5 validation should use published IAs and OIA's *stated* answers, not this workbook's outputs. Whether to report the defects to OIA is your call.

### F-03 New IA Framework: remaking a sunsetting instrument changes the baseline (high impact on the core use case)

From 1 July 2026, remaking a sunsetting legislative instrument, "as is or with amendments", is assessed against *no instrument* (IAF-PG pp. 21–22).

- For reforms delivered that way, the official RBE is the full cost of the remade (reformed) regime: an *increase* against nothing, not a saving against today.
- The current-vs-reformed comparison is still valuable, but only as context.
- Reforms to Acts, or to instruments not being remade, keep the status-quo baseline.

**Proposal:** a `baseline` switch, with the screener asking how the reform will be made (N-01). This needs your decision.

### F-04 Outputs the new IA process needs that the prompt doesn't list

- **A "$X over 10 years" figure** for the Dashboard IA (N-02).
- **An IA threshold 1 indicator** ($20m over 10 years; N-03).
- **A formula-driven `.xlsx` workbook,** because agencies are told to retain the "regulatory burden workbook" and share it with OIA (N-04). This favours ExcelJS (see F-08).

All three are small additions. I recommend them for Phases 2 and 4.

### F-05 Repository fit

The repository is **public**, and its README describes an econometrics programme.

- Building in a `regulatory-burden-tool/` subfolder works (it matches the suggested structure), and GitHub Pages is free for public repositories.
- Saved proposals must never be committed. A `.gitignore` rule will keep proposal files out of the repo except `examples/`.
- If the tool grows, it can be split into its own repository later with its history intact (`git subtree split`).
- This session can only reach this repository, so I'll build in the subfolder unless you say otherwise.

### F-06 The framework PDF

The PDF carries the Commonwealth Coat of Arms and the OIA logo on page 1, and I haven't checked its licence for redistribution. Rather than committing it to a public repository, I've recorded its URL and SHA-256 hash, so page references are anchored to an exact version. Tell me if you want it committed.

### F-07 Cabinet-in-confidence handling

Running entirely client-side reduces risk but doesn't remove agency obligations. Two problems:

- Whether a public web page may be used with security-classified material is a matter for each agency's security policy (under the Protective Security Policy Framework).
- `localStorage` is unencrypted and persists on shared machines.

Recommendations:

- a strict Content-Security-Policy (`connect-src 'none'`), with an e2e test that no network request is made;
- an auto-save on/off switch and a "clear all data" button;
- a **single-file offline build** (one `.html`) that agencies can host internally or open from a network drive. Vite's default module build doesn't run from `file://`.

### F-08 Excel export library

The `xlsx` (SheetJS) package on npm is stuck at 0.18.5, which has unpatched security advisories; current SheetJS versions are only published on SheetJS's own CDN. **Proposal:** use ExcelJS (MIT licence, on npm, supports formulas and styles), loaded only when exporting so it doesn't slow the first page load.

### F-09 Phase 5 data availability (medium–high risk)

- Most published IAs predate July 2026, so they use older default rates; reproductions will need justified rate overrides.
- Many report only aggregate RBE tables.
- Finding 3–5 IAs with line-item detail, including at least two reforms, may take some searching.

The OIA website is reachable from this environment, and its sitemap lists published IAs (e.g. one on reducing the second-tier financial reporting burden is a likely reform candidate). I suggest building a shortlist early.

### F-10 Environment

The cloud container is ephemeral, so I'll commit and push at every phase checkpoint. The tools needed are all present:

- Node 22;
- Chromium (Playwright build 1194). I'll pin `@playwright/test` to match, or use `executablePath`;
- LibreOffice, so Phase 4 exports can be checked by opening and rendering the generated `.docx` and `.xlsx`.

### F-11 Effort and timeline

The engineering fits comfortably in the project plan's timeline. The binding constraints are review turnaround and the interpretive decisions in A-01 to A-21 and N-01 to N-03, not technical risk.
