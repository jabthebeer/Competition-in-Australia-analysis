// The productivity and competition costing of a policy brief (plan §6): Layer A channels, custom shocks, Layer B,
// the time path and present values, for one set of parameter values (central by default). The Monte Carlo and the
// evidence gate run this many times (uncertainty.ts, costing.ts). The RBE is never changed: the burden proposal is
// only read (DECISIONS #81).
import { type PolicyBrief } from "./brief";
import { CHANNELS, type ChannelId } from "./channels";
import { knownIndustries, type CostingContext } from "./context";
import {
  CENTRAL,
  c1Compliance,
  c2c3Capital,
  c4Entry,
  c5Thresholds,
  c6c7Conduct,
  c8Labour,
  c9Innovation,
  c10Trade,
  c11Fiscal,
  exposureOf,
  weaker,
  type ChannelOutcome,
  type Grade,
  type ParamSource,
} from "./layerA";
import { aggregate, ioigReach, shocksForCode, type LayerBResult } from "./layerB";
import { covers } from "./anzsic";
import { pathParams, pathShare, presentValue, type Response } from "./timePath";

export interface ChannelResult extends ChannelOutcome {
  /** Long-run change in real GDP from this channel, per cent (after the realisation factor and the model error). */
  gdpPct: number;
  /** The same in dollars a year, $ million in `gdpYear` prices. */
  gdpDollars: number;
  /** Change in real GDP, per cent, in years 1, 2, … of the policy (index 0 is year 1). */
  path: number[];
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
  /** The same per person, $ a year (population from ASNA: GDP ÷ GDP per head), with population fixed. */
  gdpPerPersonDollars: number;
  /** Change in real GDP by year of the policy, years 1 to max(10, duration); dollars in $ million a year. */
  path: { year: number; gdpPct: number; gdpDollars: number }[];
  /** Present value of the GDP change over the brief's duration, $ million, at each discount rate (PR-06). */
  npv: { rate: number; dollars: number }[];
  /** Welfare cost of funding (C11), $ a year (negative is a cost). Reported beside GDP, not in it. */
  welfareDollars: number;
  layerB: LayerBResult;
  /** What the costing does not cover (F-B-06). */
  notModelled: string[];
}

export const NOT_MODELLED = [
  "Gross national income, the terms of trade, consumer prices and state GSP are not modelled (F-B-06). GNI can rise much less than GDP when foreign owners earn part of the capital income.",
  "Dollar effects apply the percentage change to the latest year's GDP, held constant in real terms: growth in the economy is not projected, so later years' dollar effects are understated.",
  "GDP per person holds population fixed at the latest year's: the policy is assumed not to change it.",
];

/** Custom shocks (plan §5.1): added to their channel, or replacing its modelled shocks for the industry (overlap rule O-6). */
function applyCustom(brief: PolicyBrief, ctx: CostingContext, outcomes: Map<ChannelId, ChannelOutcome>, params: ParamSource): void {
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
    const exposure = exposureOf(s.industry, brief, params);
    const size = params.input(`levers.custom.${s.id}.size`, s.size);
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
  add(c4Entry(brief, ctx, params));
  add(c5Thresholds(brief, ctx, params));
  add(c6c7Conduct(brief, ctx, params));
  add(c8Labour(brief, ctx, params));
  add(c9Innovation(brief, ctx, params));
  add(c10Trade(brief, ctx, params));
  add(c11Fiscal(brief, ctx, params));
  applyCustom(brief, ctx, outcomes, params);

  const realisation = brief.analysis.realisationFactor;
  // Layer B's model error (A-P19): central 1; the Monte Carlo draws it from the back-test band. Capital deepening
  // takes the band of the capital-and-labour-productivity cases.
  const errorLp = params.get("F-B-05", "modelErrorLp");
  const errorMfp = params.get("F-B-05", "modelErrorMfp");
  const layerB = aggregate(
    [...outcomes.values()].flatMap((o) => o.shocks),
    ctx.weights,
  );
  const timing = pathParams(params, layerB.alpha);
  const { phaseInYears, durationYears } = brief.meta;
  const years = Array.from({ length: Math.max(10, durationYears) }, (_, i) => i + 1);
  const curve = (kind: Response) => years.map((t) => pathShare(kind, t, phaseInYears, timing));
  const curves = { productivity: curve("productivity"), capital: curve("capital"), directThenCapital: curve("directThenCapital"), convergence: curve("convergence") };

  const ordered = [...outcomes.values()].sort((a, b) => Number(a.channel.slice(1)) - Number(b.channel.slice(1)));
  const channels: ChannelResult[] = ordered.map((o) => {
    const by = aggregate(o.shocks, ctx.weights).byType;
    const lp = by.labourProductivity * errorLp * realisation;
    const mfp = by.mfp * errorMfp * realisation;
    const va = by.valueAdded * errorMfp * realisation;
    const mfpCurve = o.channel === "C1" ? curves.directThenCapital : curves.productivity; // A-P26
    const lpCurve = o.channel === "C4" ? curves.convergence : curves.productivity; // A-P30
    const path = years.map((_, i) => lp * lpCurve[i]! + mfp * mfpCurve[i]! + va * curves.capital[i]!);
    const gdpPct = lp + mfp + va;
    return { ...o, gdpPct, gdpDollars: (gdpPct / 100) * ctx.gdp, path };
  });
  const gdpPct = channels.reduce((s, c) => s + c.gdpPct, 0);
  const path = years.map((year, i) => {
    const pct = channels.reduce((s, c) => s + c.path[i]!, 0);
    return { year, gdpPct: pct, gdpDollars: (pct / 100) * ctx.gdp };
  });
  const flows = path.slice(0, durationYears).map((p) => p.gdpDollars);
  const welfareDollars = channels.flatMap((c) => c.other).filter((x) => x.unit === "$ a year").reduce((s, x) => s + x.value, 0);
  return {
    briefId: brief.id,
    gdpYear: ctx.gdpYear,
    gdpLevel: ctx.gdp,
    realisationFactor: realisation,
    channels,
    gdpPct,
    gdpDollars: (gdpPct / 100) * ctx.gdp,
    gdpPerPersonDollars: ((gdpPct / 100) * ctx.gdp * 1e6) / ctx.population,
    path,
    npv: [brief.analysis.discountRate, ...brief.analysis.sensitivityRates].map((rate) => ({ rate, dollars: presentValue(flows, rate) })),
    welfareDollars,
    layerB,
    notModelled: NOT_MODELLED,
  };
}
