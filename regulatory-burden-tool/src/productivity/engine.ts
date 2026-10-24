// The productivity and competition costing of a policy brief (plan §6): Layer A channels, custom shocks, then
// Layer B. Central values here; the Monte Carlo, the time path and the evidence gate build on this (P4).
// The RBE is never changed: the burden proposal is only read (DECISIONS #81).
import { central, type PolicyBrief } from "./brief";
import { CHANNELS, type ChannelId } from "./channels";
import { knownIndustries, type CostingContext } from "./context";
import { CENTRAL, c1Compliance, c2c3Capital, c4c5Pending, c6c7Conduct, c8Labour, c9Innovation, c10Trade, c11Fiscal, type ChannelOutcome, type Grade, type ParamSource } from "./layerA";
import { aggregate, ioigReach, shocksForCode, type LayerBResult } from "./layerB";
import { covers } from "./anzsic";

export interface ChannelResult extends ChannelOutcome {
  /** Long-run change in real GDP from this channel, per cent (after the realisation factor). */
  gdpPct: number;
  /** The same in dollars a year, $ million in `gdpYear` prices. */
  gdpDollars: number;
}

export interface CostingResult {
  briefId: string;
  gdpYear: string;
  /** Nominal GDP the percentages apply to, $ million. */
  gdpLevel: number;
  realisationFactor: number;
  channels: ChannelResult[];
  /** Long-run change in real GDP, per cent, and in $ million a year. */
  gdpPct: number;
  gdpDollars: number;
  /** Welfare cost of funding (C11), $ a year (negative is a cost). Reported beside GDP, not in it. */
  welfareDollars: number;
  layerB: LayerBResult;
  /** What the costing does not cover (F-B-06). */
  notModelled: string[];
}

export const NOT_MODELLED = [
  "Gross national income, the terms of trade, consumer prices and state GSP are not modelled (F-B-06). GNI can rise much less than GDP when foreign owners earn part of the capital income.",
  "Results are long-run effects on the level of GDP; the time path, ranges and the evidence gate are added in the next part of P4.",
];

const GRADES = ["A", "B", "C", "D"] as const;
const weaker = (a: Grade | null, b: Grade): Grade => (a === null ? b : GRADES[Math.max(GRADES.indexOf(a), GRADES.indexOf(b))]!);

/** Custom shocks (plan §5.1): added to their channel, or replacing its modelled shocks for the industry (overlap rule O-6). */
function applyCustom(brief: PolicyBrief, ctx: CostingContext, outcomes: Map<ChannelId, ChannelOutcome>): void {
  for (const s of brief.levers.custom) {
    const o =
      outcomes.get(s.channel) ??
      ({
        channel: s.channel,
        name: CHANNELS[s.channel].name,
        status: "notQuantified",
        reasons: [],
        effects: [],
        shocks: [],
        other: [],
        evidence: [],
        grade: null,
        notes: [],
      } satisfies ChannelOutcome);
    outcomes.set(s.channel, o);
    const grade: Grade = s.source ? "C" : "D"; // A-P24: a user's own shock is graded D, or C when it cites a source
    if (s.type !== "mfp" && s.type !== "labourProductivity") {
      o.reasons.push(`Custom shock "${s.id}" (${s.type}) is reported, not added to GDP: only productivity shocks reach Layer B`);
      continue;
    }
    if (s.relation === "replaces") {
      const hit = new Set(ioigReach(s.industry, ctx.mapping, knownIndustries(ctx)).map((r) => r.ioig));
      o.shocks = o.shocks.filter((x) => !hit.has(x.industry));
      o.effects = o.effects.filter((e) => !covers(s.industry, e.anzsic) && !covers(e.anzsic, s.industry));
    }
    const exposure = central(brief.scope.industries.find((i) => covers(i.anzsic, s.industry))?.exposure ?? 1);
    const size = central(s.size);
    o.shocks.push(...shocksForCode(s.industry, s.type, size, ctx.mapping, ctx.weights, exposure));
    o.effects.push({
      anzsic: s.industry,
      measure: s.type === "mfp" ? "Multifactor productivity (custom)" : "Labour productivity (custom)",
      value: size * exposure,
      unit: "% change",
      chain: [
        { label: `Custom shock "${s.id}": ${s.justification}`, value: size, unit: "%" },
        { label: "Exposure", value: exposure, unit: "share" },
      ],
    });
    o.status = "costed";
    o.grade = weaker(o.grade, grade);
    o.notes.push(`Custom shock "${s.id}" ${s.relation === "replaces" ? "replaces the modelled shocks" : "is added to the modelled shocks"} for industry ${s.industry}${s.source ? ` (source: ${s.source.description})` : " (no source: grade D)"}.`);
  }
}

/** Costs a parsed brief. `params` supplies parameter values (central by default). */
export function costBrief(brief: PolicyBrief, ctx: CostingContext, params: ParamSource = CENTRAL): CostingResult {
  const outcomes = new Map<ChannelId, ChannelOutcome>();
  const add = (o: ChannelOutcome | null) => o && outcomes.set(o.channel, o);
  add(c1Compliance(brief, ctx, params));
  c2c3Capital(brief, ctx, params).forEach(add);
  c4c5Pending(brief).forEach(add);
  add(c6c7Conduct(brief, ctx, params));
  add(c8Labour(brief, ctx, params));
  add(c9Innovation(brief, ctx, params));
  add(c10Trade(brief, ctx, params));
  add(c11Fiscal(brief, ctx, params));
  applyCustom(brief, ctx, outcomes);

  const realisation = brief.analysis.realisationFactor;
  const ordered = [...outcomes.values()].sort((a, b) => Number(a.channel.slice(1)) - Number(b.channel.slice(1)));
  const channels: ChannelResult[] = ordered.map((o) => {
    const gdpPct = aggregate(o.shocks, ctx.weights).gdpPct * realisation;
    return { ...o, gdpPct, gdpDollars: (gdpPct / 100) * ctx.gdp };
  });
  const layerB = aggregate(
    ordered.flatMap((o) => o.shocks),
    ctx.weights,
  );
  const gdpPct = layerB.gdpPct * realisation;
  const welfareDollars = channels.flatMap((c) => c.other).filter((x) => x.unit === "$ a year").reduce((s, x) => s + x.value, 0);
  return {
    briefId: brief.id,
    gdpYear: ctx.gdpYear,
    gdpLevel: ctx.gdp,
    realisationFactor: realisation,
    channels,
    gdpPct,
    gdpDollars: (gdpPct / 100) * ctx.gdp,
    welfareDollars,
    layerB,
    notModelled: NOT_MODELLED,
  };
}
