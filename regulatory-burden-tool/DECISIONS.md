# Decision log

Every assumption, interpretation of an ambiguous rule, and design choice is recorded here, with a one-line rationale.

- **Status values:** *Proposed* (awaiting approval) · *Approved* · *Rejected* · *Superseded*.
- **Cross-references:** IDs in brackets point to `docs/framework_traceability.md` (A-, P-, N- items) or `docs/phase0_proposal.md` (F- items).

## Interpretations of the framework

| # | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| 1 | 2026-10-06 | Delay: measure all times from the start of the application. Effective delay = max(0, application + approval − ready). Cost = effective delay × (net income forgone + additional expenses, default $0). Units are days, weeks or months [A-01] | Reproduces the p. 10 example. The RBM defines delay as "expenses *and* loss of income", and OIA's calculator says "standby expenses + lost income" | Approved |
| 2 | 2026-10-06 | Read "lost sales" (p. 10) as lost *net* income [A-01] | The next paragraph of the RBM values delay as "loss of net income"; revenue would overstate the loss | Approved |
| 3 | 2026-10-06 | Engine uses $91.54 exactly. Overridden components derive a rate rounded to the cent [A-02] | This is the published figure, used in OIA's own calculator, and it matches the prompt's expected dollar values | Approved |
| 4 | 2026-10-06 | One **do-anyway share** per obligation (BAU share and retention unified): businesses bear only the cost above the do-anyway level (share × today's cost per business), applied per cohort [A-03] | Avoids double counting, and handles reductions that fall below what firms do anyway. Renamed from "voluntary share" at the user's request | Approved |
| 5 | 2026-10-06 | Overlap: Σ Δ_t over all T years ÷ T, with year 1 = commencement. Whole years in Phase 1 [A-04] | RBM p. 6 (varying costs ÷ duration); savings lost in the overlap are never made up | Approved |
| 6 | 2026-10-06 | Sunk = past one-off costs only. Future replacements, renewals, maintenance and new-entrant start-up are avoidable. Locked-in contracts are unavoidable until expiry [A-05] | Only future costs can change against BAU | Approved |
| 7 | 2026-10-06 | Subsidies are capped at the cost of the obligation they offset (net ≥ 0); any excess is an excluded transfer [A-06] | RBM p. 3 subtracts subsidies from a compliance cost; it doesn't treat them as negative burden | Approved |
| 8 | 2026-10-06 | Range inputs → midpoint of each input for the point estimate. The output-range midpoint is shown in the sensitivity view [A-07, P-04] | Matches the prompt; the RBM's midpoint rule applies to ranges presented as the estimate | Approved |
| 9 | 2026-10-06 | RBE display: 1 dp, half away from zero, brackets for negatives, exact zero printed `$0`, totals from unrounded values [A-08, P-07] | Matches the RBM p. 11 example | Approved |
| 10 | 2026-10-06 | Delay stays a separate category despite the p. 10 sentence about reclassification [A-09] | The sentence is unclear, and the RBE table has no category split | Approved |
| 11 | 2026-10-06 | "Every *k* years" requires a first-occurrence year (default 1) [A-10] | The anchor changes the occurrence count when *k* doesn't divide T | Approved |
| 12 | 2026-10-06 | Duration 1–10 years; ≠ 10 needs a justification; > 10 needs recorded OIA agreement [A-11] | The RBM only contemplates shorter periods | Approved |
| 13 | 2026-10-06 | Sole traders are businesses. Employees meeting requirements in their own time are individuals at the leisure rate [A-12] | RBM p. 9: the leisure rate is for time "not in the course of their employment" | Approved |
| 14 | 2026-10-06 | Volunteers are valued at the $41 leisure rate, flagged "seek OIA advice" [A-13] | The work rate is defined for employees | Superseded by #40 |
| 15 | 2026-10-06 | GBEs and foreign-government-owned businesses → Business. Public universities get no special handling; the user picks the group [A-14] | The RBM is silent; user decision 6 Oct 2026 | Approved |
| 16 | 2026-10-06 | Mandatory payments to non-government bodies (private certifiers, scheme memberships, private insurance) are in-scope purchase costs [A-15] | The exclusion covers only charges payable or remitted to government | Approved |
| 17 | 2026-10-06 | Purchase costs are entered excluding GST [A-16] | Taxes are out of scope | Approved |
| 18 | 2026-10-06 | Default cohorts use ABS employment bands (< 20, 20–199, 200+), to be verified in Phase 3; users can redefine them [A-17] | The RBM names cohorts but doesn't define them | Approved |
| 19 | 2026-10-06 | State/territory items count only in inter-jurisdictional proposals [A-18] | RBM p. 6 scope of netting | Approved |
| 20 | 2026-10-06 | Separate fields and labels for "expected compliance rate" and "compliance vs enforcement" [A-19] | They are two different concepts that share a word | Approved |
| 21 | 2026-10-06 | Delay costs are allowed for individuals waiting on an approval to start income-earning work, flagged for OIA advice [A-20] | Consistent with "loss of income incurred by an entity" | Approved |
| 22 | 2026-10-06 | Transition costs are start-up costs of the reformed regime, placed in the commencement year [A-21] | RBM p. 8 | Approved |

## Differences between the prompt and the RBM (the RBM wins)

| # | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| 23 | 2026-10-06 | Describe the $52.31 as the RBM does: "adjusted to include income tax", sourced to ABS EEH, Jan 2024 [P-01] | The prompt says "AWE-based, after tax", which doesn't match the RBM text or footnote | Approved |
| 24 | 2026-10-06 | Record the Feb 2028 rate update as "unconfirmed" [P-02] | RBM p. 12, fn 2 | Approved |
| 25 | 2026-10-06 | Allow purchase costs for individuals [P-06] | Individuals' compliance costs are in scope (pp. 1, 5) | Approved |

## Effects of the new IA Framework (1 July 2026)

| # | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| 26 | 2026-10-06 | Baseline toggle: "current settings" or "no instrument" (remaking a sunsetting instrument). Both are always computed; the toggle picks which fills the RBE table; the screener sets the default and warns on a mismatch [N-01, F-03] | IAF-PG pp. 21–22; user approved 6 Oct 2026 | Approved |
| 27 | 2026-10-06 | Report a 10-year total ("$X over 10 years") alongside the RBE; for shorter policies, the total over the policy's life [N-02] | Required by the Dashboard IA template; user approved 6 Oct 2026 | Approved |
| 28 | 2026-10-06 | Show an IA threshold 1 indicator, using the absolute value [N-03] | IAF-PG p. 7; it's unclear whether reductions trigger the threshold | Approved |
| 29 | 2026-10-06 | Make the `.xlsx` export formula-driven [N-04] | Agencies are told to share their "regulatory burden workbook" with OIA (IAF-PG p. 20) | Approved |
| 30 | 2026-10-06 | Use OIA calculator examples as tests against OIA's *stated* answers only [N-05] | The workbook has verified formula defects (`docs/oia_calculator_review.md`) | Approved |

## Design choices

| # | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| 31 | 2026-10-06 | Build in the `regulatory-burden-tool/` subfolder of this repository [F-05] | Matches the suggested structure; the session is scoped to this repository; it can be split out later | Approved |
| 32 | 2026-10-06 | Don't commit the framework PDF; record its URL and SHA-256 instead [F-06] | Public repository; redistribution licence not checked | Approved |
| 33 | 2026-10-06 | Use `decimal.js` (40 significant digits), not integer cents | Annualisation and the floor ratio produce non-terminating values | Approved |
| 34 | 2026-10-06 | Use a strict zod schema with `schemaVersion` and a migration registry; unknown keys are rejected | Stops benefits or discounting fields leaking into the RBE; old files still load | Approved |
| 35 | 2026-10-06 | Add `scope.ts` (exclusion catalogue and screener as data) and `format.ts` to the engine | Keeps screener logic pure and testable | Approved |
| 36 | 2026-10-06 | Use ExcelJS for `.xlsx` (lazy-loaded) instead of SheetJS from npm [F-08] | The npm `xlsx` package is stale, with unpatched advisories | Approved |
| 37 | 2026-10-06 | Add a strict CSP (`connect-src 'none'`), an auto-save toggle, "clear all data", and a single-file offline build [F-07] | Enforces "no network calls"; supports agency hosting and offline use | Approved |
| 38 | 2026-10-06 | Waterfall has an "increased" step for modified obligations whose cost rises | The prompt's waterfall only lists removed, reduced and new | Approved |
| 39 | 2026-10-06 | The proposal type (reform / new / repeal) is only a UI preset; the engine treats all three the same | One model, fewer code paths | Approved |

## Decisions and proposals of 6 October 2026 (second round)

| # | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| 40 | 2026-10-06 | ~~Volunteer time at half the full-time labour rate~~ [A-13] | Replaced by #43 | Superseded by #43 |
| 41 | 2026-10-06 | Scope expansion (ACL/CCA stocktake, cost–benefit module, business dynamism and competition module) planned as stages after Phase 5, each a separate module that never alters the RBE (`docs/scope_expansion.md`) | User request; keeps the RBE pure and the core tool on schedule | Superseded by #44 |
| 42 | 2026-10-06 | Add optional `legalReference` (Act or instrument, provision) to Obligation and `industry` (ANZSIC code) to Population in schema v1 | Lets the stocktake aggregate by provision, and the dynamism module link to ABS industry data, without a later schema migration | Approved |

## Third round (6 October 2026): approvals and Phase 1 implementation decisions

| # | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| 43 | 2026-10-06 | Volunteer time is valued at the RBM non-work rate, **$41/h** (`rates.volunteer`); replacement cost is an override, with justification, for skilled tasks [A-13] | User decision; traceable to RBM pp. 9, 13 | Approved |
| 44 | 2026-10-06 | Expansion approach: the tool is built so competition costings can be added as **extensions**, and its outputs feed econometric work easily. The tool itself does no econometrics. Phase 1 delivers a read-only extension interface, a tidy long-format export with a data dictionary, and ABS-aligned industry and size identifiers. The CCA scope question (A/B/C) is deferred until that work starts | User decision (item 4) | Approved |
| 45 | 2026-10-06 | Current-side timing years are calendar years of the analysis window; reformed-side and transition timing years count from the reformed regime's start [A-04] | Deferring a reform then moves its start-up and transition costs with it, without editing every obligation | Approved (implementation) |
| 46 | 2026-10-06 | Out-of-scope tags exclude automatically, with an explanatory warning: a government fee or tax on a *purchase* side; a fine or non-compliance cost; indirect effects; court administration; performing an international obligation; opportunity cost not caused by a delay. A government fee on a *labour* side (time to pay) stays in scope | Excluded cost types can never reach the RBE, yet the user isn't blocked (RBM pp. 2–4) | Approved (implementation) |
| 47 | 2026-10-06 | A delay line where the entity isn't waiting on government to commence is excluded, with warning W-03 | RBM p. 10: delay costs only apply in that case; otherwise it is an excluded opportunity cost (p. 3) | Approved (implementation) |
| 48 | 2026-10-06 | Gross increases and reductions are measured at obligation × population level; transitions are increases | Shows offsetting effects without netting within an obligation's cohorts | Approved (implementation) |
| 49 | 2026-10-06 | Context figures (current and reformed regime cost, share removed) use steady-state profiles: unmasked current, unshifted reformed. The waterfall starts at current-regime cost and adds the masked changes, so its end equals current + net change | Context describes the regimes; the waterfall reconciles exactly to the RBE | Approved (implementation) |
| 50 | 2026-10-06 | Population sizes may carry an ABS employment band (non-employing, 1–4, 5–19, 20–199, 200+), which must be consistent with the cohort: small = non-employing to 19, medium = 20–199, large = 200+ | Matches ABS *Counts of Australian Businesses* bands (release of 18 Aug 2026), so exports merge with ABS entry/exit data | Approved (implementation) |
| 51 | 2026-10-06 | Labour for individuals ignores staff (the RBM formula has none); a staff value other than 1 raises W-11 | RBM p. 9 | Approved (implementation) |
| 52 | 2026-10-06 | The proposal may record `remakesSunsettingInstrument`; W-21 warns if the baseline toggle contradicts it | Supports the approved baseline toggle (#26) ahead of the Phase 3 screener | Approved (implementation) |
| 53 | 2026-10-06 | Toolchain: TypeScript 7.0, Vitest 5, zod 4.6, decimal.js 10.6, tsx (latest stable on 6 Oct 2026); Node ≥ 20 | Current versions; the engine needs only zod and decimal.js at runtime | Approved (implementation) |
| 54 | 2026-10-06 | `npm run trace` fails if the traceability document cites a test, warning or code symbol that doesn't exist | Keeps the rule → page → code → test mapping honest as the code changes | Approved (implementation) |
| 55 | 2026-10-06 | Subsidies are capped over the whole analysis period, not year by year | A subsidy timed differently from the cost it offsets (e.g. paid up front) shouldn't be lost | Approved (implementation) |
| 56 | 2026-10-06 | The cliff flag fires when a cohort's cost falls to zero (exempt) while the next larger cohort of the same group and industry gets no per-entity relief | Simple, transparent test of a threshold cliff (brief section 6) | Approved (implementation) |
| 57 | 2026-10-06 | Plausibility check on staff per entity uses the cohort's upper employment bound (small 19, medium 199) | The only defined bounds; non-blocking warning only | Approved (implementation) |

## Phase 2 (6 October 2026): web app

| # | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| 58 | 2026-10-06 | Inputs can carry a provenance label (`default`, `entered`, `description`, `modelEstimate`, `sourced`), stored as a map keyed by field path on each population and obligation; a missing entry means "entered by the user" | Prepares the copy-and-paste AI drafting (Phase 2b) without changing any numbers; keys reuse the diff paths | Approved |
| 59 | 2026-10-06 | Unconfirmed model estimates **watermark** results (draft banner, W-22, assumptions register) rather than block them | User left the choice open; non-blocking matches every other warning in the tool | Approved (default; revisit in Phase 4 exports) |
| 60 | 2026-10-06 | `importDraft` accepts a saved file, a bare proposal, or an AI reply with the JSON in a code fence, and returns problems as a list | One checked path for files and pasted drafts | Approved |
| 61 | 2026-10-06 | Only the copy-and-paste route to an AI tool; no direct connection | User decision | Approved |
| 62 | 2026-10-06 | The UI keeps one shared current regime across options. Each reformed version follows it, except for the fields the reform changed (`rebaseReformed`); a changed cost type or timing pattern stays as the reform set it | Brief §6: "users only edit what changes" | Approved (implementation) |
| 63 | 2026-10-06 | Titles, group labels, option and obligation names may be blank (the UI shows a fallback) | Found by the end-to-end tests: a blank name blocked all results, and forced defaults made text fields jump while typing | Approved (implementation) |
| 64 | 2026-10-06 | Changing the proposal type resets the default options only while nothing has been entered | e.g. choosing "Remove outright" should give an "Outright repeal" option | Approved (implementation) |
| 65 | 2026-10-06 | IDs are restricted to letters, digits, hyphens and underscores | IDs appear inside field paths (provenance, diffs) | Approved (implementation) |
| 66 | 2026-10-06 | The Content-Security-Policy is added to the production build only; end-to-end tests run against the build | The dev server needs a WebSocket for hot reload | Approved (implementation) |
| 67 | 2026-10-06 | Charts use a diverging pair, blue `#2a78d6` for reductions and red `#e34948` for increases, with neutral `#52514e` for regime totals. Validated on the white chart surface: colour-blind ΔE ≥ 10.4, normal-vision ΔE ≥ 26.6, all ≥ 3:1 contrast. Each chart has a legend, tooltip and table view. The app is light-theme only for now | Dataviz method: the job is polarity, so a diverging pair; status colours (green/red "good/bad") avoided | Approved (implementation) |
| 68 | 2026-10-06 | The results page (with the charting library) loads only when first opened | Halves the first download (≈ 460 kB before compression instead of ≈ 840 kB) | Approved (implementation) |
| 69 | 2026-10-06 | `@playwright/test` is pinned to 1.56.1, with a `playwright-core` override | Matches the preinstalled Chromium build; avoids a browser download | Approved (implementation) |
| 70 | 2026-10-06 | The single-file offline build (DECISIONS #37) moves to Phase 4 | Inlined scripts need CSP hashes, best done alongside the export work | Approved (deferral) |
| 71 | 2026-10-06 | Hash-based routing; focus moves to the page heading on navigation; a skip link | Works from any static host or folder; screen-reader friendly | Approved (implementation) |
| 72 | 2026-10-07 | Confirmations happen on the page (a "Yes, …" / "Cancel" pair) instead of `window.confirm` | Browser dialogs are blocked in embedded viewers and are awkward with screen readers | Approved (implementation) |
| 73 | 2026-10-07 | Page links are plain tokens (`#results`); the older `#/results` form still works | Some hosts pass only a plain `#token` through to the page | Approved (implementation) |
| 74 | 2026-10-07 | Save and load adds "Copy this proposal as text", falling back to a selected text box if the clipboard is refused; pasted text loads through the same checked path as files | A way to keep work where downloads are blocked | Approved (implementation) |
| 75 | 2026-10-07 | First visit (nothing entered) offers the illustrative example, labelled synthetic | Quicker to explore; the example stays clearly illustrative | Approved (implementation) |
| 76 | 2026-10-07 | `npm run build:artifact` makes a one-file hosted test copy: opens on the example, carries a "test copy, illustrative or public information only" notice, hides the download button, and omits the app's CSP meta (the host applies its own). The normal build is unchanged | Lets reviewers try the tool without installing anything, without weakening the privacy rules for real use | Approved (implementation) |
