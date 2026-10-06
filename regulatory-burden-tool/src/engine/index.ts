// Public API of the calculation engine. The engine is pure TypeScript with no UI
// or I/O dependencies, so it can be tested and reused independently.
export { computeProposal, ENGINE_VERSION } from "./compute";
export { PARAMETERS, deriveWorkRate } from "./parameters";
export * from "./schema";
export { loadProposalFile, parseProposal, toProposalFile, ProposalValidationError, MIGRATIONS } from "./migrate";
export { timingFactors, annualAverage, activeYears } from "./annualise";
export { point, labourCost, purchaseCost, effectiveDelay, delayCost } from "./costing";
export { copyCurrentToReformed, reformDiff } from "./reform";
export { EXCLUSIONS, SCREENER, screen } from "./scope";
export { WARNING_CATALOGUE } from "./validate";
export { formatMoney, formatShare, rbeTable, rbeHeaders, rbeTableMarkdown, verdictText, RBE_CAPTION, RBE_ROW_LABEL, type Precision, type RbeTableView } from "./format";
export { runExtensions, type EngineExtension, type ExtensionContext, type ExtensionOutcome } from "./extensions";
export { toTidyRows, tidyCsv, tidyDictionaryCsv, TIDY_COLUMNS } from "./tidy";
export type * from "./types";
