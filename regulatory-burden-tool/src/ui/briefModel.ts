// The productivity part of a costing, kept beside the burden proposal that the existing pages edit. Together they
// make a policy brief (src/productivity/brief.ts): the proposal supplies the title, type and duration, and becomes
// the brief's burden once it has obligations. The draft may be incomplete while the user works (a lever switched on
// but not yet filled in); `checkBrief` says what is missing, and nothing is costed until the brief is valid.
import type { z } from "zod";
import type { Proposal } from "../engine/index";
import {
  AnalysisSchema,
  BriefValidationError,
  briefWarnings,
  parseBrief,
  type BriefWarning,
  type LeversSchema,
  type OiaCategory,
  type PolicyBrief,
  type ScopeIndustrySchema,
} from "../productivity/index";
import { isUntouched } from "./example";
import { BRIEF_KEY } from "./persistence";

export type LeversDraft = z.input<typeof LeversSchema>;
export type ScopeIndustryDraft = z.input<typeof ScopeIndustrySchema>;
export type Jurisdiction = "CTH" | "NSW" | "VIC" | "QLD" | "WA" | "SA" | "TAS" | "ACT" | "NT";
export type SizeBand = "nonEmploying" | "1-4" | "5-19" | "20-199" | "200+";

export interface BriefDraft {
  /** The brief's id when it was loaded from a file; otherwise the proposal's id is used. */
  id?: string;
  meta: { summary?: string; jurisdictions: Jurisdiction[]; startYear: number; phaseInYears: number };
  scope: { industries: ScopeIndustryDraft[]; sizeBands?: SizeBand[]; states?: Exclude<Jurisdiction, "CTH">[] };
  levers: LeversDraft;
  analysis: z.input<typeof AnalysisSchema>;
  /** The competition screen (plan §6.8): the user's Step 1 answers (undefined = take the suggestion) and Step 3 notes. */
  competition?: { categories?: Partial<Record<OiaCategory, boolean>>; benefits?: string; alternatives?: string };
}

export const JURISDICTIONS: readonly { value: Jurisdiction; label: string }[] = [
  { value: "CTH", label: "Commonwealth" },
  { value: "NSW", label: "New South Wales" },
  { value: "VIC", label: "Victoria" },
  { value: "QLD", label: "Queensland" },
  { value: "WA", label: "Western Australia" },
  { value: "SA", label: "South Australia" },
  { value: "TAS", label: "Tasmania" },
  { value: "ACT", label: "Australian Capital Territory" },
  { value: "NT", label: "Northern Territory" },
];

/** The first financial year that starts after today, named by its first calendar year (2027 = 2027-28). */
export function nextFinancialYear(today = new Date()): number {
  return today.getMonth() >= 6 ? today.getFullYear() + 1 : today.getFullYear();
}

export function newBriefDraft(): BriefDraft {
  return {
    meta: { jurisdictions: ["CTH"], startYear: nextFinancialYear(), phaseInYears: 0 },
    scope: { industries: [] },
    levers: { thresholds: [], custom: [] },
    analysis: AnalysisSchema.parse({}),
  };
}

/** The brief the draft and the proposal make together. The proposal is the burden only once it has obligations and costs without error. */
export function assembleBrief(draft: BriefDraft, proposal: Proposal, burdenOk: boolean): unknown {
  const { competition, id, ...rest } = draft;
  return {
    schemaVersion: 1,
    kind: "policy-brief",
    id: id ?? proposal.id,
    meta: {
      ...rest.meta,
      title: proposal.title || "Untitled proposal",
      proposalType: proposal.proposalType,
      durationYears: proposal.durationYears,
      ...(proposal.durationOverride ? { durationOverride: proposal.durationOverride } : {}),
    },
    scope: rest.scope,
    ...(burdenOk && !isUntouched(proposal) ? { burden: proposal } : {}),
    levers: rest.levers,
    analysis: rest.analysis,
    ...(competition ? { competition } : {}),
  };
}

export type BriefCheck = { ok: true; brief: PolicyBrief; warnings: BriefWarning[]; withBurden: boolean } | { ok: false; issues: string[]; withBurden: boolean };

export function checkBrief(draft: BriefDraft, proposal: Proposal, burdenOk: boolean): BriefCheck {
  const withBurden = burdenOk && !isUntouched(proposal);
  try {
    const brief = parseBrief(assembleBrief(draft, proposal, burdenOk));
    return { ok: true, brief, warnings: briefWarnings(brief), withBurden };
  } catch (e) {
    return { ok: false, issues: e instanceof BriefValidationError ? e.issues : [String(e)], withBurden };
  }
}

/** Splits a parsed brief back into the draft and the proposal the pages edit; the app shows one title, the brief's. */
export function splitBrief(brief: PolicyBrief): { draft: BriefDraft; burden: Proposal | undefined } {
  const { meta, scope, levers, analysis, burden, competition } = brief;
  return {
    draft: {
      id: brief.id,
      meta: { ...(meta.summary ? { summary: meta.summary } : {}), jurisdictions: meta.jurisdictions, startYear: meta.startYear, phaseInYears: meta.phaseInYears },
      scope: { industries: scope.industries, sizeBands: scope.sizeBands, ...(scope.states ? { states: scope.states } : {}) },
      levers,
      analysis,
      ...(competition ? { competition } : {}),
    },
    burden: burden ? { ...burden, title: meta.title } : undefined,
  };
}

/** True when the draft is still the empty starting point. */
export function isEmptyDraft(d: BriefDraft): boolean {
  const l = d.levers;
  return d.scope.industries.length === 0 && !l.entry && !(l.thresholds ?? []).length && !l.capital && !l.conduct && !l.labour && !l.innovation && !l.trade && !l.fiscal && !(l.custom ?? []).length;
}

// ---- storage in this browser ----------------------------------------------------------------------------------

const isObject = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);

/** The draft saved in this browser, if it has the draft's shape (its contents are checked when costed). */
export function loadBriefDraft(): BriefDraft | null {
  try {
    const raw = window.localStorage.getItem(BRIEF_KEY);
    if (!raw) return null;
    const d = JSON.parse(raw) as unknown;
    if (!isObject(d) || !isObject(d.meta) || !isObject(d.scope) || !Array.isArray(d.scope.industries) || !isObject(d.levers) || !isObject(d.analysis)) return null;
    return d as unknown as BriefDraft;
  } catch {
    return null;
  }
}

export function saveBriefDraft(d: BriefDraft): boolean {
  try {
    window.localStorage.setItem(BRIEF_KEY, JSON.stringify(d));
    return true;
  } catch {
    return false;
  }
}

export function briefFileName(p: Proposal): string {
  const slug = p.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "costing";
  return `${slug}.brief.json`;
}

/** Downloads the whole costing (brief and burden proposal) as one file, entirely in the browser. */
export function downloadBrief(brief: PolicyBrief, proposal: Proposal): void {
  const blob = new Blob([JSON.stringify(brief, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = briefFileName(proposal);
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
