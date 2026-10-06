# Regulatory burden tool (working title)

An **unofficial** aid for estimating the regulatory burden of policy proposals under the Office of Impact Analysis (OIA) *Regulatory Burden Measurement Framework* (July 2026). Its core use case is **reform**: replacing an existing regulation with a less burdensome version, obligation by obligation.

> **Disclaimer.** This is not an Australian Government tool. It isn't endorsed by PM&C or OIA. Users remain responsible for their estimates, and should contact OIA for formal advice.

## Status

| Phase | Scope | Status |
|---|---|---|
| 0 | Specification: traceability, ambiguities, data model, test list | **Draft. Awaiting approval.** |
| 1 | Calculation engine (pure TypeScript), tests, CLI | Not started |
| 2 | Core web app (MVP), built around reform mode | Not started |
| 3 | Framework completeness: screener, warnings, cohorts, delay, overlap, assumptions register, option comparison | Not started |
| 4 | Reporting (docx, xlsx, CSV, print) and sensitivity | Not started |
| 5 | Validation against published Impact Analyses; accessibility audit; user guide | Not started |

## Documents

- `docs/framework_traceability.md`: every framework rule, its page reference, planned code location and test, plus ambiguities and proposed interpretations.
- `docs/phase0_proposal.md`: engine data model, Phase 1 test list, feasibility issues.
- `docs/oia_calculator_review.md`: review of OIA's official calculator workbook.
- `docs/scope_expansion.md`: planning note on the proposed CCA stocktake, cost–benefit module and business dynamism module.
- `DECISIONS.md`: assumption and interpretation log.
- `data/SOURCES.md`: every external source, with URL, release, access date and hash.

## Roadmap: future expansion (not part of this project)

Each of these would be added as a separate module that reads the engine output and never alters the RBE calculation.

**Proposed staged expansion** (see `docs/scope_expansion.md`; not yet approved):

- **S1: CCA consumer-law stocktake.** RBM costings of existing obligations, using the engine's "outright repeal" option.
- **S2: Cost–benefit module.** OIA CBA guidance (7% real; 3% and 10% sensitivity), with break-even analysis where benefits can't be sourced. This absorbs the net benefit panel below.
- **S3: Business dynamism and competition module.** Entry and exit effects using ABS entry/exit data and elasticities from this repository's econometric work. This absorbs the competition note and the data helper below.

**Original future-expansion items:**

- **Indicative net benefit panel:** quantified benefits, discounted per current OIA cost–benefit guidance.
- **Competition impacts note:** a qualitative checklist based on the OECD Competition Assessment Toolkit.
- **Reference data helper:** ABS *Counts of Australian Businesses*, to help fill in entity counts.
