// Ranges (F-U-01, F-U-02): a seeded Monte Carlo over every evidence parameter and brief input that has a range, and
// a tornado of the parameters that move the result most. Draws are triangular on low, central and high. Each draw is
// fixed by the seed, the draw number and the parameter's key, so a run is reproducible and adding a parameter never
// moves the draws of another.
import { central, type PolicyBrief, type SignedQuantity } from "./brief";
import type { ChannelId } from "./channels";
import type { CostingContext } from "./context";
import { costBrief, type CostingResult } from "./engine";
import { defaultEvidence, type EvidenceEntry } from "./evidence";
import type { ParamSource } from "./layerA";

export interface Percentiles {
  p10: number;
  p50: number;
  p90: number;
}

function hash32(s: string): number {
  let h = 2166136261; // FNV-1a
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/** A uniform draw in [0, 1) fixed by the seed, the draw number and the key (FNV-1a hash, then two mulberry32 steps). */
export function uniform(seed: number, draw: number, key: string): number {
  let a = hash32(`${seed}:${draw}:${key}`);
  let out = 0;
  for (let i = 0; i < 2; i++) {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    out = ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  return out;
}

/** The inverse of the triangular distribution on [low, high] with its mode at `mode`. */
export function triangular(u: number, low: number, mode: number, high: number): number {
  if (high <= low) return mode;
  const f = (mode - low) / (high - low);
  return u < f ? low + Math.sqrt(u * (high - low) * (mode - low)) : high - Math.sqrt((1 - u) * (high - low) * (high - mode));
}

function entry(formula: string, parameter: string): EvidenceEntry {
  const e = defaultEvidence(formula, parameter);
  if (!e) throw new Error(`The evidence library has no default for ${formula} ${parameter}`);
  return e;
}

/** Draw number `draw` of every parameter and input. A brief range's mode is its midpoint. */
export function sampledSource(seed: number, draw: number): ParamSource {
  return {
    get(formula, parameter) {
      const e = entry(formula, parameter);
      return triangular(uniform(seed, draw, e.id), e.low, e.value, e.high);
    },
    input(key, q) {
      return typeof q === "number" ? q : triangular(uniform(seed, draw, `input:${key}`), q.low, central(q), q.high);
    },
  };
}

/** Every value central except the overrides, keyed by evidence id or by "input:<key>" for a brief input. */
export function fixedSource(overrides: ReadonlyMap<string, number>): ParamSource {
  return {
    get(formula, parameter) {
      const e = entry(formula, parameter);
      return overrides.get(e.id) ?? e.value;
    },
    input(key, q) {
      return overrides.get(`input:${key}`) ?? central(q);
    },
  };
}

/** Central values, recording which evidence entries and brief inputs a costing reads. */
export function recordingSource(): { source: ParamSource; evidence: Map<string, EvidenceEntry>; inputs: Map<string, SignedQuantity> } {
  const evidence = new Map<string, EvidenceEntry>();
  const inputs = new Map<string, SignedQuantity>();
  return {
    evidence,
    inputs,
    source: {
      get(formula, parameter) {
        const e = entry(formula, parameter);
        evidence.set(e.id, e);
        return e.value;
      },
      input(key, q) {
        inputs.set(key, q);
        return central(q);
      },
    },
  };
}

/** The 10th, 50th and 90th percentiles, interpolating between order statistics (R's type 7). */
export function percentiles(xs: readonly number[]): Percentiles {
  const s = [...xs].sort((a, b) => a - b);
  const q = (p: number) => {
    if (!s.length) return NaN;
    const h = (s.length - 1) * p;
    const lo = Math.floor(h);
    return s[lo]! + (h - lo) * ((s[Math.min(lo + 1, s.length - 1)] ?? s[lo]!) - s[lo]!);
  };
  return { p10: q(0.1), p50: q(0.5), p90: q(0.9) };
}

export interface Ranges {
  draws: number;
  seed: number;
  /** Long-run change in real GDP, per cent, and in $ million a year. */
  gdpPct: Percentiles;
  gdpDollars: Percentiles;
  /** Present value over the duration at the brief's discount rate, $ million. */
  npv: Percentiles;
  /** GDP change, per cent, in years 1, 5 and 10. */
  byYear: { year: number; gdpPct: Percentiles }[];
  byChannel: { channel: ChannelId; gdpPct: Percentiles }[];
}

const REPORTED_YEARS = [1, 5, 10];

/** The Monte Carlo (F-U-01): `draws` costings, each with every ranged parameter and input drawn afresh. */
export function simulate(brief: PolicyBrief, ctx: CostingContext, draws = brief.analysis.draws, seed = brief.analysis.seed): Ranges {
  const runs: CostingResult[] = [];
  for (let i = 0; i < draws; i++) runs.push(costBrief(brief, ctx, sampledSource(seed, i)));
  const channels = runs[0]?.channels.map((c) => c.channel) ?? [];
  return {
    draws,
    seed,
    gdpPct: percentiles(runs.map((r) => r.gdpPct)),
    gdpDollars: percentiles(runs.map((r) => r.gdpDollars)),
    npv: percentiles(runs.map((r) => r.npv[0]!.dollars)),
    byYear: REPORTED_YEARS.map((year) => ({ year, gdpPct: percentiles(runs.map((r) => r.path[year - 1]!.gdpPct)) })),
    byChannel: channels.map((channel) => ({ channel, gdpPct: percentiles(runs.map((r) => r.channels.find((c) => c.channel === channel)!.gdpPct)) })),
  };
}

export interface TornadoBar {
  /** Evidence id, or "input:<key>" for a brief input. */
  key: string;
  label: string;
  low: number;
  high: number;
  /** Long-run GDP change, $ million a year, with this parameter at its low and at its high value and all else central. */
  gdpDollarsAtLow: number;
  gdpDollarsAtHigh: number;
  swing: number;
}

/** One-at-a-time sensitivity: the `top` parameters whose range moves the long-run GDP change most. */
export function tornado(brief: PolicyBrief, ctx: CostingContext, top = 10): TornadoBar[] {
  const rec = recordingSource();
  costBrief(brief, ctx, rec.source);
  const candidates: { key: string; label: string; low: number; high: number }[] = [
    ...[...rec.evidence.values()].filter((e) => e.high > e.low).map((e) => ({ key: e.id, label: e.label, low: e.low, high: e.high })),
    ...[...rec.inputs].flatMap(([key, q]) => (typeof q === "number" || q.high <= q.low ? [] : [{ key: `input:${key}`, label: `Brief input ${key}`, low: q.low, high: q.high }])),
  ];
  const at = (key: string, value: number) => costBrief(brief, ctx, fixedSource(new Map([[key, value]]))).gdpDollars;
  return candidates
    .map((c) => {
      const gdpDollarsAtLow = at(c.key, c.low);
      const gdpDollarsAtHigh = at(c.key, c.high);
      return { ...c, gdpDollarsAtLow, gdpDollarsAtHigh, swing: Math.abs(gdpDollarsAtHigh - gdpDollarsAtLow) };
    })
    .filter((b) => b.swing > 0)
    .sort((a, b) => b.swing - a.swing || a.key.localeCompare(b.key))
    .slice(0, top);
}
