// Layer B (plan §6.3; traceability F-B-01 to F-B-05): from industry productivity shocks to the long-run change in
// real GDP, under the closure PC National uses (fixed aggregate employment, fixed rate of return, so capital
// adjusts). With industry value added VA_i (factor income), wage bill W_i and aggregate capital share
// alpha = 1 - sum W / sum VA:
//   labour-augmenting shock x_i:     dlnY = sum_i (W_i / sum W) x_i                    (F-B-01)
//   Hicks-neutral value-added z_i:   dlnY = sum_i (VA_i / sum VA) z_i / (1 - alpha)    (F-B-02)
//   direct value-added change v_i:   dlnY = sum_i (VA_i / sum VA) v_i                  (no further capital response;
//                                    used for capital deepening from a change in the user cost of capital, A-P23)
// Back-tested against PC National in alicia/analyses/costing_calibration (docs/costing_calibration.md, F-B-05);
// the model-error band from that back-test is the range of this step (A-P19).
// Égert & Gal's MFP is Harrod-neutral, so shocks built from their coefficients enter as labour-augmenting (A-P18).
import { covers } from "./anzsic";

/**
 * Shock types Layer B aggregates. `labourProductivity` and `mfp` follow SHOCK_TYPES in channels.ts; `valueAdded` is a
 * direct % change in an industry's real value added that already includes its capital response (A-P23).
 */
export type AggregateShockType = "labourProductivity" | "mfp" | "valueAdded";

export interface IndustryWeight {
  /** Input-output industry group (IOIG), or any stable id. */
  id: string;
  name: string;
  /** Factor income (compensation of employees plus gross operating surplus and mixed income). */
  va: number;
  /** Compensation of employees. */
  wages: number;
}

export interface IndustryShock {
  industry: string;
  type: AggregateShockType;
  /** Per cent change (0.1 = +0.1%). */
  sizePct: number;
  /** Share of the industry the shock reaches (0–1): scope exposure times the share of the IOIG's classes covered. */
  share?: number;
}

export interface Contribution extends Required<IndustryShock> {
  gdpPct: number;
}

export interface LayerBResult {
  /** Long-run change in real GDP, per cent. */
  gdpPct: number;
  alpha: number;
  contributions: Contribution[];
  byType: Record<AggregateShockType, number>;
}

/** Aggregate capital share of factor income. */
export function capitalShare(weights: readonly IndustryWeight[]): number {
  const va = weights.reduce((s, w) => s + w.va, 0);
  const wages = weights.reduce((s, w) => s + w.wages, 0);
  if (!(va > 0) || wages < 0 || wages > va) throw new Error("Layer B weights need positive value added and wages within it");
  return 1 - wages / va;
}

/** Long-run change in real GDP from industry shocks (F-B-01, F-B-02). */
export function aggregate(shocks: readonly IndustryShock[], weights: readonly IndustryWeight[]): LayerBResult {
  const byId = new Map(weights.map((w) => [w.id, w]));
  const va = weights.reduce((s, w) => s + w.va, 0);
  const wages = weights.reduce((s, w) => s + w.wages, 0);
  const alpha = capitalShare(weights);
  const byType: Record<AggregateShockType, number> = { labourProductivity: 0, mfp: 0, valueAdded: 0 };
  const contributions = shocks.map((s): Contribution => {
    const w = byId.get(s.industry);
    if (!w) throw new Error(`Layer B has no weights for industry "${s.industry}"`);
    const share = s.share ?? 1;
    if (!(share >= 0 && share <= 1)) throw new Error(`The share of industry "${s.industry}" reached must be between 0 and 1`);
    const gdpPct =
      s.type === "labourProductivity"
        ? share * s.sizePct * (w.wages / wages)
        : s.type === "mfp"
          ? (share * s.sizePct * (w.va / va)) / (1 - alpha)
          : share * s.sizePct * (w.va / va);
    byType[s.type] += gdpPct;
    return { industry: s.industry, type: s.type, sizePct: s.sizePct, share, gdpPct };
  });
  return { gdpPct: byType.labourProductivity + byType.mfp + byType.valueAdded, alpha, contributions, byType };
}

// ---- weights from the bundled parameters (ABS input-output tables) ---------------------------------------------

interface IoRow {
  ioig: string;
  name: string;
  coe: number;
  gos_mi: number;
}
interface IoigAnzsicRow {
  ioig: string;
  anzsic: string;
}

/** One weight per input-output industry group, from `abs_io.industries` (the total row is left out). */
export function ioWeights(rows: readonly IoRow[]): IndustryWeight[] {
  return rows
    .filter((r) => r.ioig !== "TOT")
    .map((r) => ({ id: r.ioig, name: r.name, va: r.coe + r.gos_mi, wages: r.coe }));
}

/**
 * The input-output industries an ANZSIC code reaches, each with the share of its ANZSIC classes the code covers
 * (`abs_io.ioig_anzsic`). Classes within an IOIG are weighted equally: class-level value added is not published
 * (interpretation A-P20). `known` limits the result to industries with weights: the concordance also lists IOIGs
 * 1203 and 1204, which the published tables combine as 1205.
 */
export function ioigReach(code: string, mapping: readonly IoigAnzsicRow[], known?: ReadonlySet<string>): readonly { ioig: string; share: number }[] {
  // Costings call this for the same codes many times (every Monte Carlo draw), so results are kept per mapping and set.
  const byKnown = reachCache.get(mapping) ?? new WeakMap();
  reachCache.set(mapping, byKnown);
  const cache = byKnown.get(known ?? ALL) ?? { classes: groupClasses(mapping, known), byCode: new Map() };
  byKnown.set(known ?? ALL, cache);
  const hitCached = cache.byCode.get(code);
  if (hitCached) return hitCached;
  const out: { ioig: string; share: number }[] = [];
  for (const [ioig, list] of cache.classes) {
    const hit = list.filter((c) => covers(code, c)).length;
    if (hit > 0) out.push({ ioig, share: hit / list.length });
  }
  cache.byCode.set(code, out);
  return out;
}

const ALL: ReadonlySet<string> = new Set();
const reachCache = new WeakMap<readonly IoigAnzsicRow[], WeakMap<ReadonlySet<string>, { classes: [string, string[]][]; byCode: Map<string, readonly { ioig: string; share: number }[]> }>>();

function groupClasses(mapping: readonly IoigAnzsicRow[], known: ReadonlySet<string> | undefined): [string, string[]][] {
  const classes = new Map<string, string[]>();
  for (const m of mapping) {
    if (known && !known.has(m.ioig)) continue;
    classes.set(m.ioig, [...(classes.get(m.ioig) ?? []), m.anzsic]);
  }
  return [...classes].sort(([a], [b]) => a.localeCompare(b));
}

/** A uniform shock to an ANZSIC code (division to class), spread over the input-output industries it reaches. */
export function shocksForCode(
  code: string,
  type: AggregateShockType,
  sizePct: number,
  mapping: readonly IoigAnzsicRow[],
  weights: readonly IndustryWeight[],
  exposure = 1,
): IndustryShock[] {
  let known = knownByWeights.get(weights);
  if (!known) knownByWeights.set(weights, (known = new Set(weights.map((w) => w.id))));
  return ioigReach(code, mapping, known).map((r) => ({ industry: r.ioig, type, sizePct, share: r.share * exposure }));
}
const knownByWeights = new WeakMap<readonly IndustryWeight[], ReadonlySet<string>>();
