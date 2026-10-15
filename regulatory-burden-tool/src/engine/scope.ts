// What counts and what doesn't (RBM pp. 2-5, 10, 14-15), held as data so the
// screener (Phase 3) and the engine share one source.
import type { CostType, Tag } from "./schema";

export type ExclusionReason =
  | "sunk"
  | "directFinancialCost"
  | "nonCompliance"
  | "enforcement"
  | "courtAdministration"
  | "indirect"
  | "internationalObligation"
  | "governmentToGovernment"
  | "opportunityCost"
  | "delayNotWaitingOnGovernment"
  | "stateInCommonwealthOnly"
  | "subsidyExcess";

export const EXCLUSIONS: Record<ExclusionReason, { label: string; explanation: string; ref: string }> = {
  sunk: {
    label: "Already incurred (sunk)",
    explanation: "Costs already incurred under the current regime can't be recovered, so removing them is not a saving. Only future avoidable costs count.",
    ref: "RBM pp. 3, 6 (change from business as usual); DECISIONS #6",
  },
  directFinancialCost: {
    label: "Fee, charge, levy or tax paid to government",
    explanation: "The amount paid is excluded. The time spent paying it is an administrative cost: enter that as labour.",
    ref: "RBM pp. 2, 4",
  },
  nonCompliance: {
    label: "Non-compliance cost",
    explanation: "Fines, legal fees and other costs of failing to comply are excluded. Compliance is the default position.",
    ref: "RBM pp. 3-4",
  },
  enforcement: {
    label: "Enforcement (Appendix 3)",
    explanation: "Processes put in place by government to enforce compliance are outside the framework.",
    ref: "RBM pp. 14-15",
  },
  courtAdministration: {
    label: "Court or tribunal administration",
    explanation: "Impacts of court rules and practice directions made by a court or tribunal are excluded.",
    ref: "RBM p. 4",
  },
  indirect: {
    label: "Indirect cost (including competition impacts)",
    explanation: "Indirect costs, such as changes to market structure and competition, are excluded from the RBE. Analyse them elsewhere in the Impact Analysis.",
    ref: "RBM p. 4",
  },
  internationalObligation: {
    label: "Performing an international-market obligation",
    explanation: "The cost of performing obligations required to take part in international markets is excluded. Demonstrating compliance to a Commonwealth regulator stays in scope: cost that separately.",
    ref: "RBM p. 4",
  },
  governmentToGovernment: {
    label: "Government-to-government",
    explanation: "Policy imposed on government agencies and their employees is excluded, except for GBEs, public universities and foreign-government-owned businesses.",
    ref: "RBM pp. 4-5",
  },
  opportunityCost: {
    label: "Opportunity cost not caused by a delay",
    explanation: "Opportunity costs are excluded unless they relate to a delay.",
    ref: "RBM p. 3",
  },
  delayNotWaitingOnGovernment: {
    label: "Delay without waiting on government",
    explanation: "Delay costs count only while the entity is waiting on government action before it can commence operating.",
    ref: "RBM p. 10",
  },
  stateInCommonwealthOnly: {
    label: "State or territory cost in a Commonwealth-only proposal",
    explanation: "State and territory costs are netted in only for inter-jurisdictional reforms with Commonwealth involvement.",
    ref: "RBM p. 6",
  },
  subsidyExcess: {
    label: "Subsidy above the cost it offsets",
    explanation: "A subsidy can reduce an obligation's cost to zero but not below. The excess is a transfer, outside the framework.",
    ref: "RBM p. 3; DECISIONS #7",
  },
};

/** The exclusion implied by an obligation's tags for a given cost type, if any (DECISIONS #46). */
export function tagExclusion(tags: readonly Tag[], costType: CostType): ExclusionReason | undefined {
  const has = (t: Tag) => tags.includes(t);
  // A fee or tax amount is a purchase; the time to pay it (labour) stays in scope (RBM p. 2).
  if ((has("governmentFee") || has("tax")) && costType === "purchase") return "directFinancialCost";
  if (has("fine") || has("nonCompliance")) return "nonCompliance";
  if (has("courtAdministration")) return "courtAdministration";
  if (has("indirectEffect")) return "indirect";
  if (has("internationalObligation")) return "internationalObligation";
  if (has("opportunityCost") && costType !== "delay") return "opportunityCost";
  return undefined;
}

// ---------------------------------------------------------------------------
// Scope screener: plain-language questions mapped to the exclusions (Phase 3 UI).

export type ScreenerQuestionId =
  | "feeToGovernment"
  | "tax"
  | "fine"
  | "enforcement"
  | "doneAnyway"
  | "indirect"
  | "courtRules"
  | "internationalMarkets"
  | "governmentAgency"
  | "outsourced"
  | "waitingOnGovernment"
  | "subsidy"
  | "lostOpportunity"
  | "remakeSunsetting";

export interface ScreenerOutcome {
  questionId: ScreenerQuestionId;
  /** "in" = cost it; "out" = exclude it; "partly" = cost part of it, as explained. */
  scope: "in" | "out" | "partly";
  explanation: string;
  ref: string;
  suggestedTag?: Tag;
}

export interface ScreenerQuestion {
  id: ScreenerQuestionId;
  question: string;
  /** Outcome when the answer is "yes". A "no" answer leaves the default (in scope) unless noOutcome is given. */
  yes: Omit<ScreenerOutcome, "questionId">;
  no?: Omit<ScreenerOutcome, "questionId">;
}

export const SCREENER: readonly ScreenerQuestion[] = [
  {
    id: "feeToGovernment",
    question: "Is this a fee, charge, levy, licence fee or mandatory insurance premium paid to government?",
    yes: { scope: "partly", explanation: "The amount paid is out of scope. The time spent paying it is an administrative cost: cost that as labour.", ref: "RBM pp. 2, 4", suggestedTag: "governmentFee" },
  },
  {
    id: "tax",
    question: "Is it a tax?",
    yes: { scope: "partly", explanation: "Taxes are out of scope. The time spent complying with the tax requirement is an administrative cost.", ref: "RBM pp. 2, 4", suggestedTag: "tax" },
  },
  {
    id: "fine",
    question: "Is it a fine, penalty, or legal cost that arises from failing to comply?",
    yes: { scope: "out", explanation: "Non-compliance costs are excluded. Compliance is the default position.", ref: "RBM pp. 3-4", suggestedTag: "fine" },
  },
  {
    id: "enforcement",
    question: "Is the activity part of a government process to enforce compliance, rather than something done to comply?",
    yes: { scope: "out", explanation: "Enforcement is outside the framework, but only where this can be clearly demonstrated. Otherwise treat it as compliance (the default). A split is allowed if good data exists.", ref: "RBM pp. 14-15", suggestedTag: "enforcementActivity" },
  },
  {
    id: "doneAnyway",
    question: "Would a normally efficient business do some or all of this anyway, without the rule?",
    yes: { scope: "partly", explanation: "Only the cost above what businesses would do anyway counts. Set the do-anyway share.", ref: "RBM pp. 3, 6", suggestedTag: "commonIndustryPractice" },
  },
  {
    id: "indirect",
    question: "Is this an indirect effect, such as changes in prices, market structure or competition?",
    yes: { scope: "out", explanation: "Indirect costs, including competition impacts, are excluded from the RBE. Discuss them elsewhere in the Impact Analysis.", ref: "RBM p. 4", suggestedTag: "indirectEffect" },
  },
  {
    id: "courtRules",
    question: "Does the cost come from court or tribunal rules or practice directions?",
    yes: { scope: "out", explanation: "Regulatory impacts of court and tribunal administration are excluded.", ref: "RBM p. 4", suggestedTag: "courtAdministration" },
  },
  {
    id: "internationalMarkets",
    question: "Is it the cost of performing an obligation required to take part in international markets (e.g. airworthiness directives)?",
    yes: { scope: "partly", explanation: "Performing the obligation is excluded. Demonstrating compliance to a Commonwealth regulator (e.g. reporting) is in scope: cost that as a separate obligation.", ref: "RBM p. 4", suggestedTag: "internationalObligation" },
  },
  {
    id: "governmentAgency",
    question: "Does the cost fall on a government agency or its employees?",
    yes: { scope: "out", explanation: "Government-to-government policy is excluded, unless the entity is a Government Business Enterprise, a public university or a foreign-government-owned business.", ref: "RBM pp. 4-5" },
  },
  {
    id: "outsourced",
    question: "Is the work done by an outside provider, such as an accountant or lawyer?",
    yes: { scope: "in", explanation: "Cost outsourced services as a purchase (substantive compliance), not as labour.", ref: "RBM p. 12", suggestedTag: "outsourcedService" },
  },
  {
    id: "waitingOnGovernment",
    question: "For a delay: is the entity waiting on a government decision before it can start operating (or selling a new product)?",
    yes: { scope: "in", explanation: "Delay costs count for the time the entity waits beyond when it would otherwise be ready. Seek OIA advice on delay costs.", ref: "RBM p. 10" },
    no: { scope: "out", explanation: "Delay costs only count while waiting on government action to commence.", ref: "RBM p. 10" },
  },
  {
    id: "subsidy",
    question: "Does government pay a subsidy towards this cost?",
    yes: { scope: "in", explanation: "Subtract the subsidy from the compliance cost (but not below zero).", ref: "RBM p. 3" },
  },
  {
    id: "lostOpportunity",
    question: "Is this the value of an opportunity the business can no longer pursue, other than because of a delay?",
    yes: { scope: "out", explanation: "Opportunity costs are excluded unless they relate to a delay.", ref: "RBM p. 3", suggestedTag: "opportunityCost" },
  },
  {
    id: "remakeSunsetting",
    question: "Will the change be made by remaking a sunsetting legislative instrument?",
    yes: { scope: "in", explanation: "Compare against no instrument (the instrument sunsetting), not the current settings. Set the baseline toggle to \"no instrument\".", ref: "IA Framework Practical Guide pp. 21-22" },
  },
];

/** Applies screener answers and returns the outcome for every question answered with a defined outcome. */
export function screen(answers: Partial<Record<ScreenerQuestionId, boolean>>): ScreenerOutcome[] {
  const outcomes: ScreenerOutcome[] = [];
  for (const q of SCREENER) {
    const answer = answers[q.id];
    if (answer === undefined) continue;
    const outcome = answer ? q.yes : q.no;
    if (outcome) outcomes.push({ questionId: q.id, ...outcome });
  }
  return outcomes;
}
