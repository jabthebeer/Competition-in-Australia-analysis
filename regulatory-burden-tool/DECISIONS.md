# Decision log

Every assumption, interpretation of an ambiguous rule, and design choice is recorded here, with a one-line rationale.

- **Status values:** *Proposed* (awaiting approval) · *Approved* · *Rejected* · *Superseded*.
- **Cross-references:** IDs in brackets point to `docs/framework_traceability.md` (A-, P-, N- items) or `docs/phase0_proposal.md` (F- items).

## Interpretations of the framework

| # | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| 1 | 2026-10-06 | Delay: measure all times from the start of the application. Effective delay = max(0, application + approval − ready). Cost = effective delay × (net income forgone + additional expenses, default $0). Units are days, weeks or months [A-01] | Reproduces the p. 10 example. The RBM defines delay as "expenses *and* loss of income", and OIA's calculator says "standby expenses + lost income" | Proposed |
| 2 | 2026-10-06 | Read "lost sales" (p. 10) as lost *net* income [A-01] | The next paragraph of the RBM values delay as "loss of net income"; revenue would overstate the loss | Proposed |
| 3 | 2026-10-06 | Engine uses $91.54 exactly. Overridden components derive a rate rounded to the cent [A-02] | This is the published figure, used in OIA's own calculator, and it matches the prompt's expected dollar values | Proposed |
| 4 | 2026-10-06 | One *voluntary share* per obligation (BAU share and retention unified), applied as a per-entity floor measured against current activity [A-03] | Avoids double counting, and handles reductions that fall below what firms do anyway | Proposed: **decision needed** |
| 5 | 2026-10-06 | Overlap: Σ Δ_t over all T years ÷ T, with year 1 = commencement. Whole years in Phase 1 [A-04] | RBM p. 6 (varying costs ÷ duration); savings lost in the overlap are never made up | Proposed |
| 6 | 2026-10-06 | Sunk = past one-off costs only. Future replacements, renewals, maintenance and new-entrant start-up are avoidable. Locked-in contracts are unavoidable until expiry [A-05] | Only future costs can change against BAU | Proposed: **decision needed** |
| 7 | 2026-10-06 | Subsidies are capped at the cost of the obligation they offset (net ≥ 0); any excess is an excluded transfer [A-06] | RBM p. 3 subtracts subsidies from a compliance cost; it doesn't treat them as negative burden | Proposed |
| 8 | 2026-10-06 | Range inputs → midpoint of each input for the point estimate. The output-range midpoint is shown in the sensitivity view [A-07, P-04] | Matches the prompt; the RBM's midpoint rule applies to ranges presented as the estimate | Proposed: **decision needed** |
| 9 | 2026-10-06 | RBE display: 1 dp, half away from zero, brackets for negatives, exact zero printed `$0`, totals from unrounded values [A-08, P-07] | Matches the RBM p. 11 example | Proposed |
| 10 | 2026-10-06 | Delay stays a separate category despite the p. 10 sentence about reclassification [A-09] | The sentence is unclear, and the RBE table has no category split | Proposed |
| 11 | 2026-10-06 | "Every *k* years" requires a first-occurrence year (default 1) [A-10] | The anchor changes the occurrence count when *k* doesn't divide T | Proposed |
| 12 | 2026-10-06 | Duration 1–10 years; ≠ 10 needs a justification; > 10 needs recorded OIA agreement [A-11] | The RBM only contemplates shorter periods | Proposed |
| 13 | 2026-10-06 | Sole traders are businesses. Employees meeting requirements in their own time are individuals at the leisure rate [A-12] | RBM p. 9: the leisure rate is for time "not in the course of their employment" | Proposed |
| 14 | 2026-10-06 | Volunteers are valued at the $41 leisure rate, flagged "seek OIA advice" [A-13] | The work rate is defined for employees | Proposed: **decision needed** |
| 15 | 2026-10-06 | GBEs and foreign-government-owned businesses → Business. Public universities → user must choose [A-14] | The RBM is silent on which group | Proposed: **decision needed** |
| 16 | 2026-10-06 | Mandatory payments to non-government bodies (private certifiers, scheme memberships, private insurance) are in-scope purchase costs [A-15] | The exclusion covers only charges payable or remitted to government | Proposed |
| 17 | 2026-10-06 | Purchase costs are entered excluding GST [A-16] | Taxes are out of scope | Proposed |
| 18 | 2026-10-06 | Default cohorts use ABS employment bands (< 20, 20–199, 200+), to be verified in Phase 3; users can redefine them [A-17] | The RBM names cohorts but doesn't define them | Proposed |
| 19 | 2026-10-06 | State/territory items count only in inter-jurisdictional proposals [A-18] | RBM p. 6 scope of netting | Proposed |
| 20 | 2026-10-06 | Separate fields and labels for "expected compliance rate" and "compliance vs enforcement" [A-19] | They are two different concepts that share a word | Proposed |
| 21 | 2026-10-06 | Delay costs are allowed for individuals waiting on an approval to start income-earning work, flagged for OIA advice [A-20] | Consistent with "loss of income incurred by an entity" | Proposed |
| 22 | 2026-10-06 | Transition costs are start-up costs of the reformed regime, placed in the commencement year [A-21] | RBM p. 8 | Proposed |

## Differences between the prompt and the RBM (the RBM wins)

| # | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| 23 | 2026-10-06 | Describe the $52.31 as the RBM does: "adjusted to include income tax", sourced to ABS EEH, Jan 2024 [P-01] | The prompt says "AWE-based, after tax", which doesn't match the RBM text or footnote | Proposed |
| 24 | 2026-10-06 | Record the Feb 2028 rate update as "unconfirmed" [P-02] | RBM p. 12, fn 2 | Proposed |
| 25 | 2026-10-06 | Allow purchase costs for individuals [P-06] | Individuals' compliance costs are in scope (pp. 1, 5) | Proposed |

## Effects of the new IA Framework (1 July 2026)

| # | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| 26 | 2026-10-06 | Add a `baseline` setting: `statusQuo` (default) or `noInstrument` (remaking a sunsetting instrument) [N-01, F-03] | IAF-PG pp. 21–22 | Proposed: **decision needed** |
| 27 | 2026-10-06 | Report a duration total ("$X over 10 years") alongside the RBE [N-02] | Required by the Dashboard IA template | Proposed: **decision needed** |
| 28 | 2026-10-06 | Show an IA threshold 1 indicator, using the absolute value [N-03] | IAF-PG p. 7; it's unclear whether reductions trigger the threshold | Proposed: **decision needed** |
| 29 | 2026-10-06 | Make the `.xlsx` export formula-driven [N-04] | Agencies are told to share their "regulatory burden workbook" with OIA (IAF-PG p. 20) | Proposed |
| 30 | 2026-10-06 | Use OIA calculator examples as tests against OIA's *stated* answers only [N-05] | The workbook has verified formula defects (`docs/oia_calculator_review.md`) | Proposed |

## Design choices

| # | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| 31 | 2026-10-06 | Build in the `regulatory-burden-tool/` subfolder of this repository [F-05] | Matches the suggested structure; the session is scoped to this repository; it can be split out later | Proposed |
| 32 | 2026-10-06 | Don't commit the framework PDF; record its URL and SHA-256 instead [F-06] | Public repository; redistribution licence not checked | Proposed |
| 33 | 2026-10-06 | Use `decimal.js` (40 significant digits), not integer cents | Annualisation and the floor ratio produce non-terminating values | Proposed |
| 34 | 2026-10-06 | Use a strict zod schema with `schemaVersion` and a migration registry; unknown keys are rejected | Stops benefits or discounting fields leaking into the RBE; old files still load | Proposed |
| 35 | 2026-10-06 | Add `scope.ts` (exclusion catalogue and screener as data) and `format.ts` to the engine | Keeps screener logic pure and testable | Proposed |
| 36 | 2026-10-06 | Use ExcelJS for `.xlsx` (lazy-loaded) instead of SheetJS from npm [F-08] | The npm `xlsx` package is stale, with unpatched advisories | Proposed |
| 37 | 2026-10-06 | Add a strict CSP (`connect-src 'none'`), an auto-save toggle, "clear all data", and a single-file offline build [F-07] | Enforces "no network calls"; supports agency hosting and offline use | Proposed |
| 38 | 2026-10-06 | Waterfall has an "increased" step for modified obligations whose cost rises | The prompt's waterfall only lists removed, reduced and new | Proposed |
| 39 | 2026-10-06 | The proposal type (reform / new / repeal) is only a UI preset; the engine treats all three the same | One model, fewer code paths | Proposed |
