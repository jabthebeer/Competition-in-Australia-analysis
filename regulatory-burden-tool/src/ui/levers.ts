// Reform levers in policy language, each mapped to the parameters it changes (brief section 6).
import type { Obligation, Tag } from "../engine/index";

export type Lever = Obligation["levers"][number];

/** Field keys used to highlight the inputs a lever usually changes. */
export type LeverField = "timesPerYear" | "timing" | "hours" | "appliesTo" | "entities" | "staff" | "unitCost" | "approvalDelay";

export const LEVERS: readonly { id: Exclude<Lever, "removeObligation">; label: string; help: string; fields: LeverField[] }[] = [
  { id: "lessFrequent", label: "Less frequent reporting or renewal", help: "Lower the times a year, or change the timing to every few years.", fields: ["timesPerYear", "timing"] },
  { id: "simplerForm", label: "Simpler forms, pre-filled data or digital lodgement", help: "Lower the time each occurrence takes.", fields: ["hours"] },
  { id: "threshold", label: "Threshold or exemption (e.g. small business)", help: "Exempt a group, or lower the number of entities it applies to.", fields: ["appliesTo", "entities"] },
  { id: "fewerStaff", label: "Fewer staff involved, or no sign-off required", help: "Lower the number of staff per entity.", fields: ["staff"] },
  { id: "outcomeBased", label: "Outcome-based instead of prescriptive requirements", help: "Change what must be bought, or how often.", fields: ["unitCost", "timesPerYear"] },
  { id: "removeDuplication", label: "Removing duplication ('tell us once')", help: "Do it less often (or remove the obligation instead).", fields: ["timesPerYear"] },
  { id: "longerLicence", label: "Longer licence terms", help: "Renew less often: change the timing to every few years.", fields: ["timing", "timesPerYear"] },
  { id: "fasterApproval", label: "Faster approvals or deemed approval", help: "Shorten the approval time (a delay cost).", fields: ["approvalDelay"] },
  { id: "other", label: "Other change", help: "Any other change to the parameters.", fields: [] },
];

export function highlightedFields(levers: readonly Lever[]): Set<LeverField> {
  return new Set(LEVERS.filter((l) => levers.includes(l.id)).flatMap((l) => l.fields));
}

/** Plain-language scope checks, mapped to the tags the engine uses (RBM pp. 2-4, 12, 14-15). */
export const SCOPE_TAGS: readonly { tag: Tag; label: string; effect: string }[] = [
  { tag: "commonIndustryPractice", label: "Businesses would do some of this anyway (common industry practice)", effect: "Set the do-anyway share: only the cost above it counts (RBM pp. 3, 6)." },
  { tag: "outsourcedService", label: "It's done by an outside provider (e.g. accountant, lawyer)", effect: "Cost it as a purchase, not staff time (RBM p. 12)." },
  { tag: "governmentFee", label: "It's a fee, charge, levy or licence fee paid to government", effect: "The amount is excluded; the time to pay it counts as staff time (RBM pp. 2, 4)." },
  { tag: "tax", label: "It's a tax", effect: "The amount is excluded; the time to comply counts (RBM pp. 2, 4)." },
  { tag: "fine", label: "It's a fine, penalty or cost of failing to comply", effect: "Excluded: compliance is the default position (RBM pp. 3-4)." },
  { tag: "enforcementActivity", label: "It's part of a government process to enforce compliance", effect: "Set the classification to enforcement, with a justification (RBM pp. 14-15)." },
  { tag: "indirectEffect", label: "It's an indirect effect (prices, market structure, competition)", effect: "Excluded from the RBE; discuss it elsewhere in the Impact Analysis (RBM p. 4)." },
  { tag: "courtAdministration", label: "It comes from court or tribunal rules or practice directions", effect: "Excluded (RBM p. 4)." },
  { tag: "internationalObligation", label: "It's performing an obligation needed to trade internationally", effect: "Excluded; reporting it to a Commonwealth regulator still counts, so cost that separately (RBM p. 4)." },
  { tag: "opportunityCost", label: "It's the value of a lost opportunity (other than a delay)", effect: "Excluded unless it relates to a delay (RBM p. 3)." },
];
