// The competition screen's measures (plan §6.8; PR-04, PR-07, PR-08): compliance cost against revenue by business
// size, the small-to-large ratio, the share of the scope's businesses affected, the categories the OIA's Step 1
// asks about, and the Business Characteristics Survey's measured incidence of regulation as a barrier. Revenue per
// business is Australian Industry sales over CABEE business counts for the population's division and size band, so
// it is an average for that size, not the population's own.
import type { OptionResult, Proposal } from "../engine/index";
import { divisionOf, OIA_CATEGORIES, type CostingContext, type OiaCategory } from "../productivity/index";
import type { BriefDraft } from "./briefModel";
import type { CostingParameters, RegisterRecord } from "./costingData";
import { similarChanges, suggestedCategories } from "./similar";

/** Australian Industry size bands and the CABEE bands each spans. */
const AI_BANDS: Record<string, string[]> = { "0-4": ["nonemp", "1-4"], "5-19": ["5-19"], "20-199": ["20-199"], "200+": ["200+"], total: ["total"] };

type Population = Proposal["populations"][number];

/** The Australian Industry bands a population falls in: its employment band, or else its cohort (small < 20, medium 20–199, large 200+). */
export function bandsOf(p: Population): string[] {
  switch (p.employmentBand) {
    case "nonEmploying":
    case "1-4":
      return ["0-4"];
    case "5-19":
    case "20-199":
    case "200+":
      return [p.employmentBand];
  }
  return p.cohort === "small" ? ["0-4", "5-19"] : p.cohort === "medium" ? ["20-199"] : p.cohort === "large" ? ["200+"] : [];
}

/** Average annual sales per business, $, for a division and a set of size bands (Australian Industry ÷ CABEE). */
export function revenuePerBusiness(division: string, bands: readonly string[], ctx: CostingContext): number | undefined {
  const ai = ctx.industryByBand[division];
  const counts = ctx.businessesByBand[division];
  if (!ai || !counts || bands.length === 0) return undefined;
  const sales = bands.reduce((s, b) => s + (ai[b]?.sales ?? NaN), 0);
  const businesses = bands.reduce((s, b) => s + (AI_BANDS[b] ?? []).reduce((t, c) => t + (counts[c] ?? 0), 0), 0);
  return Number.isFinite(sales) && businesses > 0 ? (sales * 1e6) / businesses : undefined;
}

export interface CohortBurden {
  populationId: string;
  label: string;
  size: "small" | "medium" | "large" | "unknown";
  count: number;
  /** $ a year per entity: the change (the RBE's measure) and the cost under the option. */
  changePerEntity: number;
  costPerEntity: number;
  revenue?: number;
  /** Shares of revenue. */
  changeShare?: number;
  costShare?: number;
  cliff: boolean;
}

const sizeOf = (bands: string[]): CohortBurden["size"] =>
  bands.length === 0 ? "unknown" : bands.every((b) => b === "0-4" || b === "5-19") ? "small" : bands.every((b) => b === "20-199") ? "medium" : bands.every((b) => b === "200+") ? "large" : "unknown";

/** Each business population's compliance cost against the average revenue of businesses its size in its division. */
export function cohortBurden(option: OptionResult, proposal: Proposal, ctx: CostingContext): CohortBurden[] {
  const pops = new Map(proposal.populations.map((p) => [p.id, p]));
  return option.perEntity
    .filter((e) => e.group === "business")
    .map((e) => {
      const p = pops.get(e.populationId);
      const bands = p ? bandsOf(p) : [];
      const div = p?.industry ? divisionOf(p.industry) : undefined;
      // A group of all sizes, or of no stated size, is compared with the division's average business.
      const revenue = div ? revenuePerBusiness(div, bands.length ? bands : ["total"], ctx) : undefined;
      const change = Number(e.changePerEntity);
      const cost = Number(e.reformedAnnualPerEntity);
      return {
        populationId: e.populationId,
        label: e.label,
        size: sizeOf(bands),
        count: Number(e.count),
        changePerEntity: change,
        costPerEntity: cost,
        revenue,
        changeShare: revenue ? change / revenue : undefined,
        costShare: revenue ? cost / revenue : undefined,
        cliff: e.cliffFlag,
      };
    });
}

/**
 * Cost under the option as a share of revenue for small businesses over the same for large ones, each a mean
 * weighted by the number of businesses; undefined unless both sizes are present with revenue.
 */
export function smallToLarge(rows: readonly CohortBurden[]): number | undefined {
  const mean = (size: CohortBurden["size"]) => {
    const r = rows.filter((x) => x.size === size && x.costShare !== undefined && x.count > 0);
    const n = r.reduce((s, x) => s + x.count, 0);
    return n > 0 ? r.reduce((s, x) => s + x.costShare! * x.count, 0) / n : undefined;
  };
  const small = mean("small");
  const large = mean("large");
  return small !== undefined && large !== undefined && large > 0 ? small / large : undefined;
}

/** Businesses the burden proposal counts, as a share of the businesses in the scope industries (CABEE). */
export function shareAffected(proposal: Proposal, draft: BriefDraft, ctx: CostingContext): { affected: number; inScope: number } | undefined {
  const affected = proposal.populations.filter((p) => p.group === "business").reduce((s, p) => s + (typeof p.count === "number" ? p.count : (p.count.low + p.count.high) / 2), 0);
  const inScope = draft.scope.industries.reduce((s, i) => s + (ctx.businessesByBand[i.anzsic]?.total ?? 0), 0);
  return affected > 0 && inScope > 0 ? { affected, inScope } : undefined;
}

/** Step 1's categories: why each is suggested, from the levers and from similar past changes in the register. */
export function categoryReasons(draft: BriefDraft, records: readonly RegisterRecord[]): Map<OiaCategory, string[]> {
  const out = new Map(suggestedCategories(draft));
  for (const s of similarChanges(draft, records)) {
    for (const c of s.record.channels) {
      if (!(OIA_CATEGORIES as readonly string[]).includes(c)) continue;
      const cat = c as OiaCategory;
      out.set(cat, [...(out.get(cat) ?? []), `A similar past change touched it: ${s.record.title}`]);
    }
  }
  return out;
}

/** The Business Characteristics Survey's share of businesses reporting government regulation as a barrier, by size and for the given divisions. */
export function regulationBarrier(p: CostingParameters, divisions: readonly string[]): { label: string; pct: number }[] {
  const rows = ((p.tables["abs_bcs.barriers"] as { rows?: Record<string, unknown>[] } | undefined)?.rows ?? []).filter((r) => r.population === "all");
  const pick = (cat: string) => rows.find((r) => r.category === cat)?.government_regulation;
  const out: { label: string; pct: number }[] = [];
  const add = (label: string, v: unknown) => typeof v === "number" && out.push({ label, pct: v });
  add("All businesses", pick("total"));
  add("0–4 persons", pick("0-4"));
  add("5–19 persons", pick("5-19"));
  add("20–199 persons", pick("20-199"));
  add("200 or more persons", pick("200+"));
  for (const d of divisions) add(`Division ${d}`, pick(d));
  return out;
}
