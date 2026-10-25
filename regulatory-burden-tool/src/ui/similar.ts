// The register in the product (plan §6.9): which OIA competition categories a brief's levers touch, similar past
// changes from the register, and a check of the levers' direction against them. Register directions are hypotheses
// and evaluation verdicts are provisional; neither is used as a parameter.
import { overlaps, type OiaCategory } from "../productivity/index";
import type { BriefDraft } from "./briefModel";
import type { RegisterRecord } from "./costingData";

type Restriction = "priceControl" | "quantityControl" | "advertising" | "standards" | "tradingHours" | "exclusivity" | "information" | "other";

/** The OIA Step 1 categories a conduct restriction touches. */
const RESTRICTION_CATEGORIES: Record<Restriction, OiaCategory[]> = {
  priceControl: ["prices-market-share"],
  quantityControl: ["number-or-type", "prices-market-share"],
  advertising: ["ability-incentive", "consumer-choice"],
  standards: ["ability-incentive", "number-or-type"],
  tradingHours: ["ability-incentive"],
  exclusivity: ["number-or-type", "barriers"],
  information: ["consumer-choice"],
  other: [],
};

/** The categories the levers suggest for OIA Step 1, each with why. */
export function suggestedCategories(d: BriefDraft): Map<OiaCategory, string[]> {
  const out = new Map<OiaCategory, string[]>();
  const add = (c: OiaCategory, why: string) => out.set(c, [...(out.get(c) ?? []), why]);
  const l = d.levers;
  if (l.entry?.costPerEntrantChangeDollars !== undefined || l.entry?.approvalTimeChangeDays !== undefined || l.entry?.exitCostChangeDollars !== undefined) {
    add("barriers", "Entry lever: the cost, time or exit cost for businesses");
  }
  if (l.entry?.numberCap) add("number-or-type", "Entry lever: a cap on the number of businesses");
  if ((l.thresholds ?? []).length) add("barriers", "Size thresholds: a cost of growing past the threshold");
  if (l.capital?.investmentApprovalDelayChangeMonths !== undefined) add("barriers", "Capital lever: investment approval time");
  if (l.conduct) {
    if (l.conduct.route === "markup") add("prices-market-share", "Conduct lever: a change in mark-ups");
    if (l.conduct.route === "pmr" && l.conduct.indicator === "barriersToEntry") add("barriers", "Conduct lever: the PMR barriers-to-entry indicator");
    for (const r of l.conduct.restrictions ?? []) for (const c of RESTRICTION_CATEGORIES[r as Restriction] ?? []) add(c, `Conduct restriction: ${r}`);
  }
  if (l.labour?.licensing) {
    add("barriers", "Occupational licensing: the cost of entering an occupation");
    add("number-or-type", "Occupational licensing: who may supply the service");
  }
  if (l.labour?.nonCompetes) add("ability-incentive", "Non-compete clauses: workers' and rivals' ability to compete");
  if (l.innovation?.productApprovalTimeChangeDays !== undefined) add("barriers", "Product approval time");
  if (l.trade?.tariffChangePp !== undefined) add("prices-market-share", "Tariffs: the price of imported competition");
  if (l.trade?.fdiRestrictivenessChangePct !== undefined || l.trade?.opennessChangePp !== undefined) add("number-or-type", "Trade and foreign investment: foreign suppliers");
  return out;
}

export type Direction = "enhancing" | "weakening" | "mixed";

const sign = (q: unknown): number => {
  if (typeof q === "number") return Math.sign(q);
  if (q && typeof q === "object" && "low" in q && "high" in q) return Math.sign(((q as { low: number }).low + (q as { high: number }).high) / 2);
  return 0;
};

/** Whether the levers make it easier to compete (enhancing), harder (weakening), or both; undefined when no lever says. */
export function leverDirection(d: BriefDraft): Direction | undefined {
  const s: number[] = [];
  const l = d.levers;
  s.push(-sign(l.entry?.costPerEntrantChangeDollars), -sign(l.entry?.approvalTimeChangeDays), -sign(l.entry?.exitCostChangeDollars));
  if (l.entry?.numberCap) s.push(l.entry.numberCap.change === "introduce" || l.entry.numberCap.change === "tighten" ? -1 : 1);
  for (const t of l.thresholds ?? []) s.push(t.change === "introduce" ? -1 : t.change === "remove" ? 1 : 0);
  s.push(-sign(l.capital?.investmentApprovalDelayChangeMonths));
  if (l.conduct?.route === "markup") s.push(-sign(l.conduct.markupChangePct));
  if (l.conduct?.route === "pmr") s.push(-Math.sign(l.conduct.to - l.conduct.from));
  s.push(-sign(l.labour?.licensing?.stringencyChange), -sign(l.labour?.nonCompetes?.coveredShareChange));
  s.push(-sign(l.innovation?.productApprovalTimeChangeDays), -sign(l.trade?.tariffChangePp), -sign(l.trade?.fdiRestrictivenessChangePct), sign(l.trade?.opennessChangePp));
  const up = s.some((x) => x > 0);
  const down = s.some((x) => x < 0);
  return up && down ? "mixed" : up ? "enhancing" : down ? "weakening" : undefined;
}

export interface SimilarChange {
  record: RegisterRecord;
  score: number;
  sharedCategories: string[];
  sharedIndustries: string[];
  /** Other jurisdictions where the same reform family matched, shown with this record rather than on their own. */
  alsoIn: string[];
}

/**
 * Register records ranked by shared OIA categories (two points each), industries (one point per scope industry the
 * record's industries overlap at any ANZSIC level, two for a direct one) and jurisdiction type (one point when both
 * are Commonwealth, or both state or territory). A reform family made in several jurisdictions appears once, as its
 * best match, with the other jurisdictions listed.
 */
export function similarChanges(d: BriefDraft, records: readonly RegisterRecord[], limit = 5): SimilarChange[] {
  const cats = new Set(suggestedCategories(d).keys());
  const scope = d.scope.industries.map((i) => i.anzsic);
  const briefCth = d.meta.jurisdictions.includes("CTH");
  const briefStates = d.meta.jurisdictions.some((j) => j !== "CTH");
  return records
    .map((record) => {
      const sharedCategories = record.channels.filter((c) => cats.has(c as OiaCategory));
      const hits = record.industries.filter((i) => scope.some((s) => overlaps(s, i.anzsic)));
      const sharedIndustries = [...new Set(hits.map((i) => i.anzsic))];
      const jur = (record.jurisdiction === "CTH" && briefCth) || (record.jurisdiction !== "CTH" && briefStates) ? 1 : 0;
      const score = 2 * sharedCategories.length + hits.reduce((s, i) => s + (i.exposure === "direct" ? 2 : 1), 0) + (sharedCategories.length || hits.length ? jur : 0);
      return { record, score, sharedCategories, sharedIndustries };
    })
    .filter((m) => m.sharedCategories.length > 0 || m.sharedIndustries.length > 0)
    .sort((a, b) => b.score - a.score || (b.record.commencement ?? "").localeCompare(a.record.commencement ?? "") || a.record.id.localeCompare(b.record.id))
    .reduce((out, m) => {
      const family = m.record.family ?? m.record.id;
      const first = out.find((x) => (x.record.family ?? x.record.id) === family);
      if (first) {
        if (!first.alsoIn.includes(m.record.jurisdiction) && m.record.jurisdiction !== first.record.jurisdiction) first.alsoIn.push(m.record.jurisdiction);
      } else out.push({ ...m, alsoIn: [] });
      return out;
    }, [] as SimilarChange[])
    .slice(0, limit);
}

/** A note when the levers' direction disagrees with most similar changes whose hypothesised direction is clear. */
export function directionCheck(d: BriefDraft, similar: readonly SimilarChange[]): string | undefined {
  const mine = leverDirection(d);
  if (mine !== "enhancing" && mine !== "weakening") return undefined;
  const clear = similar.filter((s) => s.record.direction === "enhancing" || s.record.direction === "weakening");
  const opposite = clear.filter((s) => s.record.direction !== mine);
  if (clear.length < 2 || opposite.length * 2 <= clear.length) return undefined;
  return `Your levers make it ${mine === "enhancing" ? "easier" : "harder"} to compete, but ${opposite.length} of the ${clear.length} similar past changes with a clear direction were hypothesised to ${mine === "enhancing" ? "weaken" : "enhance"} competition. Check the levers' signs.`;
}
