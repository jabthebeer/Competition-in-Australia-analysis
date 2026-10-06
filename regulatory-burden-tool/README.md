# Regulatory burden tool (working title)

An **unofficial** aid for estimating the regulatory burden of policy proposals under the Office of Impact Analysis (OIA) *Regulatory Burden Measurement Framework* (July 2026). Its core use case is **reform**: replacing an existing regulation with a less burdensome version, obligation by obligation.

> **Disclaimer.** This is not an Australian Government tool. It isn't endorsed by PM&C or OIA. Users remain responsible for their estimates, and should contact OIA for formal advice.

## Status

| Phase | Scope | Status |
|---|---|---|
| 0 | Specification: traceability, ambiguities, data model, test list | Approved 6 Oct 2026 |
| 1 | Calculation engine (pure TypeScript), tests, CLI | **Complete. Awaiting review.** |
| 2 | Core web app (MVP), built around reform mode | Not started |
| 3 | Framework completeness: screener UI, warnings UI, assumptions register UI, option comparison | Not started (the engine already supports these) |
| 4 | Reporting (docx, xlsx, CSV, print) and sensitivity | Not started |
| 5 | Validation against published Impact Analyses; accessibility audit; user guide | Not started |

## Running it

Requires Node 20 or later.

```bash
npm install
npm test                 # unit tests (Vitest)
npm run typecheck        # TypeScript
npm run trace            # checks the traceability document against the code and tests
npm run check            # all three

# Print the RBE table for a proposal file (illustrative example included):
npm run rbe -- examples/illustrative-reform.json
npm run rbe -- examples/illustrative-reform.json --precision dollars   # or 2, 3
npm run rbe -- examples/illustrative-reform.json --json                # full results
npm run rbe -- examples/illustrative-reform.json --tidy out/tidy.csv   # analysis-ready data + dictionary
```

Proposal files may be Cabinet-in-confidence. `.gitignore` keeps `*.rbm.json` and `*.proposal.json` out of the repository; only the synthetic files in `examples/` are tracked.

## The engine (`src/engine/`)

The engine is pure TypeScript, with no UI, I/O, clock or randomness. The same input always gives the same output.

| Module | Role |
|---|---|
| `parameters.ts` | Default rates ($91.54 work, $41 non-work and volunteer), size bands, thresholds. **Updating rates is a one-file change.** |
| `schema.ts`, `migrate.ts` | Versioned, strict `zod` schema (Proposal → Option → Obligation {current, reformed} → Line); loading of older files |
| `costing.ts`, `annualise.ts` | Labour, purchase and delay formulas; year-by-year profiles and averages |
| `reform.ts` | Current-vs-reformed comparison: do-anyway share, exclusions, enforcement split, subsidies, overlap, baseline toggle, copy-on-reform and diff |
| `aggregate.ts` | RBE table, verdict, gross figures, context, waterfall, breakdowns, per-entity results and cliffs, 10-year total, IA threshold 1 indicator |
| `validate.ts`, `scope.ts` | 21 non-blocking warnings, the assumptions register, the exclusion catalogue and the scope screener questions |
| `format.ts` | The framework's RBE table layout and number formats (brackets for negatives, `$0` for zero) |
| `tidy.ts`, `extensions.ts` | Analysis-ready export with ABS-aligned identifiers, and the read-only interface for future modules |

**Arithmetic.** All money arithmetic uses `decimal.js`, and results are exact decimal strings, so totals carry no floating-point residue. Rounding happens only when values are displayed.

### Building on it (competition costings and econometrics)

The tool does no econometrics itself (DECISIONS #44). Two hooks make that work easy to add:

- **Tidy export** (`toTidyRows`, `tidyCsv`, `tidyDictionaryCsv`)
  - One row per option × obligation side × population × year.
  - Merge keys: ANZSIC 2006 industry code, ABS employment-size band, cohort, legal reference.
  - Ready to join with ABS *Counts of Australian Businesses, including Entries and Exits*.
- **Extensions** (`runExtensions`)
  - A future module, e.g. one applying entry/exit elasticities estimated in this repository's econometric work, receives frozen copies of the proposal, results and tidy rows.
  - It returns its own output. It can't change the RBE.

## Documents

- `docs/framework_traceability.md`: every framework rule, with its page reference, code location and test; ambiguities and the approved interpretations.
- `docs/phase0_proposal.md`: data model, Phase 1 test list, feasibility issues.
- `docs/oia_calculator_review.md`: review of OIA's official calculator workbook.
- `docs/scope_expansion.md`: planning note on the CCA stocktake, cost–benefit and business dynamism modules.
- `DECISIONS.md`: assumption, interpretation and design log.
- `data/SOURCES.md`: every external source, with URL, release, access date and hash.

## Roadmap: future expansion (not part of this project)

Each of these would be added as a separate module that reads the engine output and never alters the RBE calculation.

**Proposed staged expansion** (see `docs/scope_expansion.md`):

- **S1: CCA consumer-law stocktake.** RBM costings of existing obligations, using the engine's "outright repeal" option.
- **S2: Cost–benefit module.** OIA CBA guidance (7% real; 3% and 10% sensitivity), with break-even analysis where benefits can't be sourced. This absorbs the net benefit panel below.
- **S3: Competition costings and business dynamism.** Entry and exit effects using ABS entry/exit data and elasticities from this repository's econometric work, via the extension interface. This absorbs the competition note and the data helper below.

**Original future-expansion items:**

- **Indicative net benefit panel:** quantified benefits, discounted per current OIA cost–benefit guidance.
- **Competition impacts note:** a qualitative checklist based on the OECD Competition Assessment Toolkit.
- **Reference data helper:** ABS *Counts of Australian Businesses*, to help fill in entity counts.
