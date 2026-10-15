// Engine output types. Money values are exact decimal strings (dollars).
// Future modules (benefits, competition costings) read these results through
// the extension interface and never write to them (DECISIONS #44).
import type { ExclusionReason } from "./scope";
import type { Cohort, CostType, Group } from "./schema";

export type Money = string;

export type WarningCode =
  | "W-01" | "W-02" | "W-03" | "W-04" | "W-05" | "W-06" | "W-07" | "W-08" | "W-09" | "W-10"
  | "W-11" | "W-12" | "W-13" | "W-14" | "W-15" | "W-16" | "W-17" | "W-18" | "W-19" | "W-20" | "W-21" | "W-22";

export interface Warning {
  code: WarningCode;
  severity: "warning" | "info";
  message: string;
  ref: string;
  optionId?: string;
  obligationId?: string;
  populationId?: string;
}

export interface RbeRow {
  business: Money;
  communityOrg: Money;
  individual: Money;
  total: Money;
}

export type ItemSide = "current" | "reformed";
export type ItemKind = "obligation" | "transition";

/** One obligation side × population line: the full audit trail of a calculation. */
export interface ItemResult {
  optionId: string;
  obligationId: string;
  obligationName: string;
  kind: ItemKind;
  side: ItemSide;
  populationId: string;
  group: Group;
  cohort: Cohort;
  employmentBand?: string;
  industry?: string;
  entityType: string;
  category: "administrative" | "substantive" | "delay";
  costType: CostType;
  timingType: string;
  jurisdiction: "commonwealth" | "stateTerritory";
  legalInstrument?: string;
  legalProvision?: string;
  formula: string;
  inputs: Record<string, string>;
  /** Entities × expected compliance rate. */
  effectiveEntities: Money;
  activeYearCost: Money;
  /** Effective business-as-usual share applied (A-03). */
  doAnywayShareApplied: string;
  /** Year-by-year profiles over the analysis window (index 0 = year 1). */
  grossByYear: Money[];
  doAnywayByYear: Money[];
  enforcementExcludedByYear: Money[];
  subsidyByYear: Money[];
  /** In-scope regime cost: steady-state (current unmasked; reformed unshifted). */
  netByYear: Money[];
  /** Contribution to the change in burden under the selected baseline. */
  deltaByYear: Money[];
  /** Contribution under the other baseline. */
  deltaByYearAlternative: Money[];
  deltaAnnual: Money;
  excluded?: ExclusionReason;
}

export interface ExcludedItem {
  optionId: string;
  obligationId: string;
  obligationName: string;
  side: ItemSide;
  populationId?: string;
  reason: ExclusionReason;
  label: string;
  explanation: string;
  ref: string;
  /** Average annual amount kept out of the RBE. */
  annualAmount: Money;
}

export interface BaselineResult {
  baseline: "statusQuo" | "noInstrument";
  rbe: RbeRow;
  tenYearTotal: Money;
  deltaByYear: Money[];
}

export interface PerEntityResult {
  populationId: string;
  label: string;
  group: Group;
  cohort: Cohort;
  count: Money;
  currentAnnualPerEntity: Money;
  reformedAnnualPerEntity: Money;
  changePerEntity: Money;
  cliffFlag: boolean;
}

export type WaterfallStep = "current" | "removed" | "reduced" | "increased" | "new" | "transition" | "end";

export interface OptionResult {
  optionId: string;
  optionName: string;
  isStatusQuo: boolean;
  baseline: "statusQuo" | "noInstrument";
  /** Average annual change in regulatory costs, $ (the RBE table), under the selected baseline. */
  rbe: RbeRow;
  /** Sum of the change over the analysis period (the Dashboard IA's "$X over 10 years"; N-02). */
  tenYearTotal: Money;
  deltaByYear: Money[];
  alternativeBaseline: BaselineResult;
  verdict: { kind: "increase" | "reduction" | "none"; amount: Money };
  gross: { increases: Money; reductions: Money };
  context: {
    currentAnnual: Money;
    reformedAnnual: Money;
    transitionAnnual: Money;
    shareRemoved: string | null;
    shareRemovedNetOfTransition: string | null;
  };
  waterfall: { step: WaterfallStep; label: string; value: Money }[];
  breakdowns: {
    group: Record<string, Money>;
    category: Record<string, Money>;
    cohort: Record<string, Money>;
    timing: Record<string, Money>;
    jurisdiction: Record<string, Money>;
    obligation: Record<string, Money>;
  };
  jurisdictionSplit: { commonwealth: Money; stateTerritory: Money };
  perEntity: PerEntityResult[];
  iaThreshold1: { tenYearTotal: Money; threshold: Money; likelyMet: boolean; note: string };
  items: ItemResult[];
  excluded: ExcludedItem[];
}

export interface AssumptionRow {
  item: string;
  value: string;
  defaultValue?: string;
  justification?: string;
  source?: string;
  ref?: string;
}

/** An input that came from a language-model draft and hasn't been confirmed or sourced yet. */
export interface UnconfirmedEstimate {
  kind: "population" | "obligation";
  id: string;
  label: string;
  optionId?: string;
  path: string;
  note?: string;
}

export interface ProposalResult {
  engineVersion: string;
  schemaVersion: number;
  parameterVintage: string;
  proposalId: string;
  title: string;
  durationYears: number;
  baseline: "statusQuo" | "noInstrument";
  options: OptionResult[];
  warnings: Warning[];
  assumptions: AssumptionRow[];
  /** Results are a draft while any of these remain (DECISIONS #59). */
  unconfirmedEstimates: UnconfirmedEstimate[];
}
