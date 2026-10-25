// A full costing of a policy brief: the central result with its time path and present values, the Monte Carlo
// ranges, the tornado, and the materiality and evidence gate (plan §6.3–6.6), with the brief's warnings.
import { briefWarnings, type BriefWarning, type PolicyBrief } from "./brief";
import type { ChannelId } from "./channels";
import type { CostingContext } from "./context";
import { costBrief, type CostingResult } from "./engine";
import { defaultEvidence } from "./evidence";
import type { Grade } from "./layerA";
import { simulate, tornado, type Ranges, type TornadoBar } from "./uncertainty";

export type GateStatus = "full" | "indicative" | "hidden";

export interface GateResult {
  /** full: economy-wide results with range; indicative: shown, marked indicative; hidden: GDP hidden unless opted in. */
  status: GateStatus;
  /** Whether economy-wide (GDP) figures are shown: always, except when hidden and the brief has not opted in. */
  showGdp: boolean;
  /** Hidden results shown on request, and results resting on unconfirmed estimates, carry a watermark. */
  watermark: boolean;
  reasons: string[];
  /** The channel with the largest long-run GDP change, and its grade. */
  largestChannel: ChannelId | null;
  grade: Grade | null;
  /** IA threshold 2 (PR-03), $ million a year. */
  thresholdDollars: number;
  threshold2: {
    /** Long-run GDP change, $ million a year: central, and the end of the 10–90 range nearer zero. */
    central: number;
    low: number;
    centralMeets: boolean;
    lowMeets: boolean;
  };
}

/** The materiality and evidence gate (F-G-01) and the threshold 2 check (PR-03). */
export function evidenceGate(brief: PolicyBrief, result: CostingResult, ranges: Ranges, warnings: BriefWarning[]): GateResult {
  const threshold = defaultEvidence("F-G-01", "threshold")!.value; // $ million a year
  const central = result.gdpDollars;
  const low = central >= 0 ? Math.min(ranges.gdpDollars.p10, central) : Math.max(ranges.gdpDollars.p90, central);
  const meets = (x: number) => Math.abs(x) >= threshold && Math.sign(x) === Math.sign(central);
  const largest = result.channels.filter((c) => c.gdpPct !== 0).sort((a, b) => Math.abs(b.gdpDollars) - Math.abs(a.gdpDollars))[0];
  const unconfirmed = warnings.some((w) => w.code === "PB-04");
  const reasons: string[] = [];
  let status: GateStatus;
  if (!largest) {
    status = "indicative";
    reasons.push("No channel changes GDP.");
  } else if (largest.grade === "D" || largest.grade === null || unconfirmed) {
    status = "hidden";
    if (largest.grade === "D" || largest.grade === null) reasons.push(`The largest channel (${largest.channel}, ${largest.name}) rests on evidence graded ${largest.grade ?? "D (no evidence)"}.`);
    if (unconfirmed) reasons.push("The brief has language-model estimates that haven't been confirmed.");
  } else if (!meets(central) || largest.grade === "C") {
    status = "indicative";
    if (!meets(central)) reasons.push(`The central effect ($${Math.round(central).toLocaleString("en-AU")}m a year) is below the $${threshold}m threshold.`);
    if (largest.grade === "C") reasons.push(`The largest channel (${largest.channel}, ${largest.name}) is graded C.`);
  } else {
    status = "full";
  }
  const optedIn = brief.analysis.showUngatedEconomyWide;
  return {
    status,
    showGdp: status !== "hidden" || optedIn,
    watermark: unconfirmed || (status === "hidden" && optedIn),
    reasons,
    largestChannel: largest?.channel ?? null,
    grade: largest?.grade ?? null,
    thresholdDollars: threshold,
    threshold2: { central, low, centralMeets: meets(central), lowMeets: meets(low) },
  };
}

export interface Costing {
  result: CostingResult;
  ranges: Ranges;
  tornado: TornadoBar[];
  gate: GateResult;
  warnings: BriefWarning[];
}

/** Costs a parsed brief: central values, ranges from `draws` Monte Carlo draws (the brief's setting by default), the tornado and the gate. */
export function runCosting(brief: PolicyBrief, ctx: CostingContext, opts: { draws?: number; seed?: number } = {}): Costing {
  const result = costBrief(brief, ctx);
  const ranges = simulate(brief, ctx, opts.draws ?? brief.analysis.draws, opts.seed ?? brief.analysis.seed);
  const warnings = briefWarnings(brief);
  return { result, ranges, tornado: tornado(brief, ctx), gate: evidenceGate(brief, result, ranges, warnings), warnings };
}
