// Layer A (plan §6.1–6.2; traceability §2.3): each channel turns a brief's levers into industry shocks, shown as a
// chain of factors with their sources. Parameters come through a ParamSource: the evidence library's defaults for
// a central costing, or draws from their ranges for the Monte Carlo (P4). Channels C4 and C5 need data not yet in
// the parameter file and report themselves as not quantified.
import { computeProposal, toTidyRows } from "../engine/index";
import { covers, divisionOf, overlaps } from "./anzsic";
import { central, type PolicyBrief, type SignedQuantity } from "./brief";
import { CHANNELS, type ChannelId } from "./channels";
import { berdOf, berdTotal, divisionOfIndustry, valueAddedOf, knownIndustries, type CostingContext } from "./context";
import { EVIDENCE, EVIDENCE_GRADES, defaultEvidence } from "./evidence";
import { capitalShare, ioigReach, shocksForCode, type IndustryShock } from "./layerB";

export type Grade = (typeof EVIDENCE_GRADES)[number];

/**
 * Where values come from: a formula parameter (the library's default, or a draw from its range) and a brief input
 * (its central value, or a draw from the range the user entered). `key` names the input, e.g. "levers.capital.companyTaxRate.to".
 */
export interface ParamSource {
  get(formula: string, parameter: string): number;
  input(key: string, q: SignedQuantity): number;
}

/** The evidence library's default (central) values, and each input's central value. */
export const CENTRAL: ParamSource = {
  get(formula, parameter) {
    const e = defaultEvidence(formula, parameter);
    if (!e) throw new Error(`The evidence library has no default for ${formula} ${parameter}`);
    return e.value;
  },
  input: (_key, q) => central(q),
};

export interface Factor {
  label: string;
  value: number;
  unit: string;
  /** Evidence entry the value comes from, when it is a parameter. */
  evidence?: string;
}

export interface IndustryEffect {
  anzsic: string;
  measure: string;
  value: number;
  unit: string;
  chain: Factor[];
}

/** An effect reported outside GDP, such as the welfare cost of funding or a change in FDI. */
export interface OtherEffect {
  label: string;
  value: number;
  unit: string;
  chain: Factor[];
}

export interface ChannelOutcome {
  channel: ChannelId;
  name: string;
  status: "costed" | "notQuantified";
  /** Why a channel, or part of it, is not quantified. */
  reasons: string[];
  effects: IndustryEffect[];
  shocks: IndustryShock[];
  other: OtherEffect[];
  /** Evidence entries used. */
  evidence: string[];
  /** Those of them that are the tool's own assumptions (method "assumption", graded D): they set ranges, not the grade (A-P31). */
  assumptions: string[];
  /** The weakest grade among the evidence used, assumptions aside (D is weakest); null when none was used. */
  grade: Grade | null;
  notes: string[];
}

/** Records which evidence a channel draws on. */
function tracker(params: ParamSource) {
  const used = new Set<string>();
  return {
    used,
    get(formula: string, parameter: string): { value: number; id: string } {
      const e = defaultEvidence(formula, parameter);
      if (!e) throw new Error(`The evidence library has no default for ${formula} ${parameter}`);
      used.add(e.id);
      return { value: params.get(formula, parameter), id: e.id };
    },
  };
}

const ENTRY_OF = new Map(EVIDENCE.map((e) => [e.id, e]));
/** The tool's own assumptions: method "assumption" and graded D, which the library allows only for them (a source's assumption, such as the PC's pass-through, keeps its grade). */
const isAssumption = (id: string) => ENTRY_OF.get(id)?.method === "assumption" && ENTRY_OF.get(id)?.grade === "D";

/**
 * The weakest grade among the evidence used (D is weakest), and `base` when given. The tool's own assumptions are
 * left out: their ranges reach the Monte Carlo, but they do not grade the evidence on effects (A-P31, owner decision).
 */
function weakest(ids: Iterable<string>, base?: Grade): Grade | null {
  let worst = base ? EVIDENCE_GRADES.indexOf(base) : -1;
  for (const id of ids) {
    const g = ENTRY_OF.get(id)?.grade;
    if (g && !isAssumption(id)) worst = Math.max(worst, EVIDENCE_GRADES.indexOf(g));
  }
  return worst < 0 ? null : EVIDENCE_GRADES[worst]!;
}

function outcome(channel: ChannelId, part: Partial<ChannelOutcome> & { used?: Set<string>; baseGrade?: Grade }): ChannelOutcome {
  const evidence = [...(part.used ?? [])];
  const costed = (part.effects?.length ?? 0) > 0 || (part.other?.length ?? 0) > 0;
  return {
    channel,
    name: CHANNELS[channel].name,
    status: costed ? "costed" : "notQuantified",
    reasons: part.reasons ?? [],
    effects: part.effects ?? [],
    shocks: part.shocks ?? [],
    other: part.other ?? [],
    evidence,
    assumptions: evidence.filter(isAssumption),
    grade: weakest(evidence, part.baseGrade),
    notes: part.notes ?? [],
  };
}

/** Exposure (0–1) of an ANZSIC code: that of the scope industry covering it. */
export function exposureOf(code: string, brief: PolicyBrief, params: ParamSource): number {
  const s = brief.scope.industries.find((i) => covers(i.anzsic, code));
  return s ? params.input(`scope.${s.anzsic}.exposure`, s.exposure) : 1;
}

/** The codes a lever reaches, with their exposure: the lever's own list, or the brief's scope. */
function reach(brief: PolicyBrief, industries: string[] | undefined, params: ParamSource): { code: string; exposure: number }[] {
  const codes = industries ?? brief.scope.industries.map((i) => i.anzsic);
  return codes.map((code) => ({ code, exposure: exposureOf(code, brief, params) }));
}

/** A uniform shock on every input-output industry (an economy-wide effect). */
function economyWide(type: IndustryShock["type"], sizePct: number, ctx: CostingContext): IndustryShock[] {
  return ctx.weights.map((w) => ({ industry: w.id, type, sizePct, share: 1 }));
}

const pct = (x: number) => x * 100;

// ---- C1: resource cost of compliance (F-C1-01..03) ------------------------------------------------------------

interface BurdenCost {
  optionName: string;
  durationYears: number;
  /** In-scope RBE rows of the option costed, businesses and community organisations only. */
  rows: ReturnType<typeof toTidyRows>;
}
const burdenCache = new WeakMap<object, BurdenCost | null>();

/** The burden proposal's RBE rows for its first option other than the status quo, computed once per proposal. */
function burdenCost(brief: PolicyBrief): BurdenCost | null {
  if (!brief.burden) return null;
  const cached = burdenCache.get(brief.burden);
  if (cached !== undefined) return cached;
  const result = computeProposal(brief.burden);
  const option = result.options.find((o) => !o.isStatusQuo) ?? result.options[0];
  const cost = option
    ? {
        optionName: option.optionName,
        durationYears: result.durationYears,
        rows: toTidyRows(result).filter((r) => r.option_id === option.optionId && !r.excluded_reason && r.stakeholder_group !== "individual"),
      }
    : null;
  burdenCache.set(brief.burden, cost);
  return cost;
}

export function c1Compliance(brief: PolicyBrief, ctx: CostingContext, params: ParamSource = CENTRAL): ChannelOutcome | null {
  if (!brief.burden) return null;
  const t = tracker(params);
  const burden = burdenCost(brief);
  if (!burden) return outcome("C1", { reasons: ["The burden proposal has no option to cost"] });
  const byCode = new Map<string, number>();
  let unallocated = 0;
  // Overlap rule O-1: when C4 costs the entry lever, entrants' compliance costs are left to C4.
  const entrants = new Set(entryCosted(brief) ? (brief.levers.entry?.entrantPopulationIds ?? []) : []);
  let entrantCost = 0;
  for (const row of burden.rows) {
    const perYear = Number(row.delta_contribution) / burden.durationYears;
    if (entrants.has(String(row.population_id))) {
      entrantCost += perYear;
      continue;
    }
    const code = String(row.industry_anzsic ?? "");
    if (code) byCode.set(code, (byCode.get(code) ?? 0) + perYear);
    else unallocated += perYear;
  }
  const notes = [
    `Costs option "${burden.optionName}" of the burden proposal: the average annual change in compliance and delay costs (the RBE), by the industry of each population. Individuals' costs are not in GDP and are left out.`,
  ];
  if (unallocated !== 0) {
    // Costs of populations without an industry are spread over the scope in proportion to value added × exposure.
    const scope = brief.scope.industries.map((i) => ({ code: i.anzsic, w: valueAddedOf(i.anzsic, ctx) * params.input(`scope.${i.anzsic}.exposure`, i.exposure) }));
    const total = scope.reduce((s, x) => s + x.w, 0);
    for (const x of scope) if (total > 0) byCode.set(x.code, (byCode.get(x.code) ?? 0) + (unallocated * x.w) / total);
    notes.push("Some populations have no industry code; their costs are spread over the scope industries in proportion to value added and exposure.");
  }
  const s = t.get("F-C1-02", "s");
  const effects: IndustryEffect[] = [];
  const shocks: IndustryShock[] = [];
  const reasons: string[] = [];
  for (const [code, dC] of [...byCode].sort(([a], [b]) => a.localeCompare(b))) {
    const va = valueAddedOf(code, ctx);
    if (!(va > 0)) {
      reasons.push(`Industry ${code} has no input-output value added`);
      continue;
    }
    const mfp = pct((-dC / (va * 1e6)) * (1 - s.value));
    effects.push({
      anzsic: code,
      measure: "Multifactor productivity (value added)",
      value: mfp,
      unit: "% change",
      chain: [
        { label: "Change in compliance and delay costs, average a year (RBE)", value: dC, unit: "$ a year" },
        { label: `Industry value added (${ctx.gdpYear} dollars)`, value: va, unit: "$ million" },
        { label: "Share of the cost producing no measured benefit (1 − s)", value: 1 - s.value, unit: "share", evidence: s.id },
      ],
    });
    shocks.push(...shocksForCode(code, "mfp", mfp, ctx.mapping, ctx.weights));
  }
  if (entrants.size) {
    notes.push(`Entrants' compliance costs (${[...entrants].join(", ")}: $${Math.round(entrantCost).toLocaleString("en-AU")} a year) are left out of C1 because C4 costs entry (overlap rule O-1).`);
  } else if (entryCosted(brief)) {
    notes.push("If the burden proposal costs new entrants, mark their groups as new entrants on the entry lever, so C1 leaves their costs to C4 (overlap rule O-1).");
  }
  // The RBE is the OIA's own measure (an official method, graded A as A-P16 grades rules), and the step to MFP an
  // accounting identity (A-P01), so C1 rests on grade A evidence; s = 0 is an assumption that sets its range (A-P31).
  return outcome("C1", { used: t.used, effects, shocks, reasons, notes, baseGrade: effects.length ? "A" : undefined });
}

// ---- C2 and C3: the user cost of capital (F-C2-01, F-C3-01..03) ---------------------------------------------

/**
 * Capital deepening as value-added shocks: Δln Y_i = α_i·Δln K_i (F-C3-03, A-P23). α_i is the ABS capital income share
 * of the industry's division; divisions outside the market sector (O, P, Q) take the market-sector share.
 */
function capitalShocks(code: string, exposure: number, dlnK: number, ctx: CostingContext, alphaFallback: () => number): IndustryShock[] {
  return ioigReach(code, ctx.mapping, knownIndustries(ctx)).map((r) => {
    const div = divisionOfIndustry(r.ioig, ctx);
    const alpha = (div && ctx.capitalShare[div]) || alphaFallback();
    return { industry: r.ioig, type: "valueAdded" as const, sizePct: pct(alpha * dlnK), share: r.share * exposure };
  });
}

/** The capital share α by division (F-C3-03), falling back to the market-sector share outside the market sector. */
function alphaOf(t: ReturnType<typeof tracker>, ctx: CostingContext) {
  let fellBack = false;
  const fallback = () => {
    fellBack = true;
    return t.get("F-C3-03", "alpha").value;
  };
  return {
    fallback,
    factor(div: string | undefined): Factor {
      const own = div ? ctx.capitalShare[div] : undefined;
      return own
        ? { label: `Capital share α (division ${div}, ABS productivity ${ctx.capitalShareYear})`, value: own, unit: "share" }
        : { label: "Capital share α (market sector: the division is outside it)", value: fallback(), unit: "share", evidence: t.get("F-C3-03", "alpha").id };
    },
    notes: () => (fellBack ? ["Divisions outside the ABS market sector (public administration, education, health) take the market-sector capital share."] : []),
  };
}

export function c2c3Capital(brief: PolicyBrief, ctx: CostingContext, params: ParamSource = CENTRAL): ChannelOutcome[] {
  const lever = brief.levers.capital;
  if (!lever) return [];
  const out: ChannelOutcome[] = [];
  const codes = reach(brief, lever.industries, params);

  // C3: tax, depreciation and risk premium.
  if (lever.companyTaxRate || lever.depreciationPvChange !== undefined || lever.riskPremiumChangePp !== undefined) {
    const t = tracker(params);
    const r = t.get("F-C3-01", "r");
    const sigma = t.get("F-C3-02", "sigma");
    const alpha = alphaOf(t, ctx);
    const reasons: string[] = [];
    const effects: IndustryEffect[] = [];
    const shocks: IndustryShock[] = [];
    const tax = lever.companyTaxRate
      ? { from: params.input("levers.capital.companyTaxRate.from", lever.companyTaxRate.from), to: params.input("levers.capital.companyTaxRate.to", lever.companyTaxRate.to) }
      : undefined;
    const dz = lever.depreciationPvChange !== undefined ? params.input("levers.capital.depreciationPvChange", lever.depreciationPvChange) : 0;
    const drp = lever.riskPremiumChangePp !== undefined ? params.input("levers.capital.riskPremiumChangePp", lever.riskPremiumChangePp) / 100 : 0;
    if (dz !== 0 && !tax) reasons.push("A change in depreciation deductions needs the company tax rate to be costed; it is left out");
    for (const { code, exposure } of codes) {
      const div = divisionOf(code);
      const delta = div ? ctx.depreciation[div] : undefined;
      if (delta === undefined) {
        reasons.push(`No depreciation rate for industry ${code}`);
        continue;
      }
      const z0 = delta / (r.value + delta); // A-P22: present value of declining-balance deductions at the economic rate
      let dlnc = Math.log((r.value + drp + delta) / (r.value + delta));
      if (tax) dlnc += Math.log((1 - tax.to * (z0 + dz)) / (1 - tax.to)) - Math.log((1 - tax.from * z0) / (1 - tax.from));
      const dlnK = -sigma.value * dlnc;
      effects.push({
        anzsic: code,
        measure: "Capital stock",
        value: pct(dlnK),
        unit: "% change",
        chain: [
          { label: "Required real return r", value: r.value, unit: "a year", evidence: r.id },
          { label: `Depreciation rate δ (division ${div}, ASNA)`, value: delta, unit: "a year" },
          { label: "Present value of deductions z₀ = δ/(r + δ)", value: z0, unit: "per $ invested" },
          ...(tax
            ? [
                { label: "Company tax rate before", value: tax.from, unit: "share" },
                { label: "Company tax rate after", value: tax.to, unit: "share" },
              ]
            : []),
          ...(dz ? [{ label: "Change in z", value: dz, unit: "per $ invested" }] : []),
          ...(drp ? [{ label: "Change in the risk premium", value: drp, unit: "a year" }] : []),
          { label: "Change in the user cost of capital, Δln c", value: dlnc, unit: "log points" },
          { label: "Elasticity of capital to its user cost σ", value: sigma.value, unit: "elasticity", evidence: sigma.id },
          alpha.factor(div),
          { label: "Exposure", value: exposure, unit: "share" },
        ],
      });
      shocks.push(...capitalShocks(code, exposure, dlnK, ctx, alpha.fallback));
    }
    out.push(
      outcome("C3", {
        used: t.used,
        effects,
        shocks,
        reasons,
        notes: [
          "Capital deepening raises each industry's value added by its capital share times the change in capital (Δln Y = α Δln K); it enters GDP directly, with no further capital response (A-P23).",
          ...alpha.notes(),
          ...(tax ? ["The company tax change applies to all capital in the industries reached; unincorporated businesses and imputation credits are not modelled."] : []),
        ],
      }),
    );
  }

  // C2: investment approval delay.
  if (lever.investmentApprovalDelayChangeMonths !== undefined) {
    const t = tracker(params);
    const r = t.get("F-C2-01", "r");
    const sigma = t.get("F-C3-02", "sigma");
    const alpha = alphaOf(t, ctx);
    const years = params.input("levers.capital.investmentApprovalDelayChangeMonths", lever.investmentApprovalDelayChangeMonths) / 12;
    const dlnc = r.value * years; // F-C2-01: Δln c ≈ r·d
    const dlnK = -sigma.value * dlnc;
    const effects: IndustryEffect[] = [];
    const shocks: IndustryShock[] = [];
    const reasons: string[] = [];
    // O-2: industries whose delay costs are already in the RBE (and so in C1) are left out of the user-cost shock.
    const delayed = [...new Set((burdenCost(brief)?.rows ?? []).filter((r) => r.category === "delay" && Number(r.delta_contribution) !== 0 && r.industry_anzsic).map((r) => String(r.industry_anzsic)))];
    for (const { code, exposure } of codes) {
      const hit = delayed.filter((d) => overlaps(d, code));
      if (hit.length) {
        reasons.push(`Industry ${code} is left out: the burden proposal already costs approval delays in ${hit.join(", ")} (overlap rule O-2)`);
        continue;
      }
      effects.push({
        anzsic: code,
        measure: "Capital stock",
        value: pct(dlnK),
        unit: "% change",
        chain: [
          { label: "Change in approval time", value: years, unit: "years" },
          { label: "Required real return r", value: r.value, unit: "a year", evidence: r.id },
          { label: "Change in the user cost of capital, Δln c ≈ r·d", value: dlnc, unit: "log points" },
          { label: "Elasticity of capital to its user cost σ", value: sigma.value, unit: "elasticity", evidence: sigma.id },
          alpha.factor(divisionOf(code)),
          { label: "Exposure", value: exposure, unit: "share" },
        ],
      });
      shocks.push(...capitalShocks(code, exposure, dlnK, ctx, alpha.fallback));
    }
    const notes = [
      "The delay raises the user cost of the investment it applies to by about r × d (A-P02). Set each industry's exposure to the share of its investment that needs the approval: at full exposure every new asset in the industry is delayed.",
    ];
    notes.push(...alpha.notes());
    if (brief.burden) notes.push("Delay costs already in the burden proposal are costed in C1, not again here (overlap rule O-2): enter here only approval delays the proposal does not cost.");
    out.push(outcome("C2", { used: t.used, effects, shocks, reasons, notes }));
  }
  return out;
}

// ---- C6 and C7: competition (F-C6-01, F-C7-01, F-C7-02) ---------------------------------------------------------

const ETCR_SECTORS = new Set(["energy", "transport", "communications"]);

export function c6c7Conduct(brief: PolicyBrief, ctx: CostingContext, params: ParamSource = CENTRAL): ChannelOutcome | null {
  const lever = brief.levers.conduct;
  if (!lever) return null;
  const codes = reach(brief, lever.industries, params);
  const t = tracker(params);
  if (lever.route === "pmr") {
    if (!ETCR_SECTORS.has(lever.indicator)) {
      return outcome("C7", {
        reasons: [`Only the energy, transport and communications (ETCR) indicators have a verified productivity elasticity (Égert & Gal 2016); "${lever.indicator}" is reported, not quantified (A-P07)`],
      });
    }
    const beta = t.get("F-C7-01", "beta");
    const betaKY = t.get("F-C7-02", "betaKY");
    const dEtcr = lever.to - lever.from;
    const mfp = pct(beta.value * dEtcr);
    const dlnKY = betaKY.value * dEtcr;
    const alpha = capitalShare(ctx.weights);
    const kyGdp = pct((alpha / (1 - alpha)) * dlnKY);
    // The indicator is national and Égert & Gal estimate its effect on economy-wide MFP and K/Y, so the shocks are
    // economy-wide; the lever's industries document where the regulation sits (A-P25).
    return outcome("C7", {
      used: t.used,
      effects: [
        {
          anzsic: "TOT",
          measure: "Multifactor productivity (labour-augmenting), economy-wide, long run",
          value: mfp,
          unit: "% change",
          chain: [
            { label: `Change in the ${lever.indicator} indicator (national, 0–6)`, value: dEtcr, unit: "index points" },
            { label: "Elasticity of MFP to the ETCR β", value: beta.value, unit: "log points per index point", evidence: beta.id },
          ],
        },
        {
          anzsic: "TOT",
          measure: "Value added through the capital-output ratio, economy-wide, long run",
          value: kyGdp,
          unit: "% change",
          chain: [
            { label: "Elasticity of K/Y to the ETCR", value: betaKY.value, unit: "log points per index point", evidence: betaKY.id },
            { label: "Capital share α (input-output weights)", value: alpha, unit: "share" },
            { label: "Δln Y = α/(1 − α) · Δln(K/Y)", value: kyGdp, unit: "%" },
          ],
        },
      ],
      shocks: [...economyWide("labourProductivity", mfp, ctx), ...economyWide("valueAdded", kyGdp, ctx)],
      notes: [
        `The regulation sits in ${codes.map((c) => c.code).join(", ")}; its effect is economy-wide, as Égert & Gal estimate it (A-P25).`,
        "Égert & Gal's MFP is Harrod-neutral, so the shock enters Layer B as labour-augmenting (A-P18); their capital-output effect is added as a direct change in value added.",
        "Long-run effect; about a third arrives within five years (time path, F-B-04).",
      ],
    });
  }
  // C6: mark-ups.
  const m = params.input("levers.conduct.markupChangePct", lever.markupChangePct);
  const from = t.get("F-C6-01", "markupFrom");
  const to = t.get("F-C6-01", "markupTo");
  const loss = t.get("F-C6-01", "misallocationCostChange");
  const span = pct(to.value / from.value - 1); // % rise in the aggregate mark-up behind the H&F result
  const reachedShare = codes.reduce((s, { code, exposure }) => s + valueAddedOf(code, ctx) * exposure, 0) / ctx.weights.reduce((s, w) => s + w.va, 0);
  let aggregate = m * reachedShare;
  const reasons: string[] = [];
  if (Math.abs(aggregate) > span) {
    reasons.push(`The aggregate mark-up change (${aggregate.toFixed(2)}%) is beyond the range Hambur & Freestone computed (${span.toFixed(2)}%); only that much is costed (A-P06)`);
    aggregate = Math.sign(aggregate) * span;
  }
  const tfp = (-loss.value * aggregate) / span;
  return outcome("C6", {
    used: t.used,
    reasons,
    effects: [
      {
        anzsic: "TOT",
        measure: "Multifactor productivity (misallocation), economy-wide",
        value: tfp,
        unit: "% change",
        chain: [
          { label: "Change in the mark-up of the industries reached", value: m, unit: "%" },
          { label: "Their share of value added × exposure", value: reachedShare, unit: "share" },
          { label: "Aggregate mark-up change", value: aggregate, unit: "%" },
          { label: "Mark-up rise behind the H&F result (1.18 → 1.25)", value: span, unit: "%", evidence: to.id },
          { label: "Change in misallocation cost over that rise", value: loss.value, unit: "pp of TFP", evidence: loss.id },
        ],
      },
    ],
    shocks: economyWide("mfp", tfp, ctx),
    notes: ["Interpolated linearly within Hambur & Freestone's computed interval, never beyond it (A-P06); the loss falls on economy-wide productivity through misallocation."],
  });
}

// ---- C8: labour mobility (F-C8-01, F-C8-02) ----------------------------------------------------------------------

export function c8Labour(brief: PolicyBrief, ctx: CostingContext, params: ParamSource = CENTRAL): ChannelOutcome | null {
  const lever = brief.levers.labour;
  if (!lever) return null;
  const t = tracker(params);
  const effects: IndustryEffect[] = [];
  const shocks: IndustryShock[] = [];
  const notes: string[] = [];
  if (lever.licensing) {
    const e = t.get("F-C8-01", "elasticity");
    const cut = -params.input("levers.labour.licensing.stringencyChange", lever.licensing.stringencyChange);
    const lp = e.value * cut;
    for (const { code, exposure } of reach(brief, lever.licensing.industries, params)) {
      effects.push({
        anzsic: code,
        measure: "Labour productivity",
        value: lp * exposure,
        unit: "% change",
        chain: [
          { label: "Cut in occupational entry regulation stringency", value: cut, unit: "index points" },
          { label: "Labour productivity per index point", value: e.value, unit: "% per point", evidence: e.id },
          { label: "Exposure (share of the industry the licences cover)", value: exposure, unit: "share" },
        ],
      });
      shocks.push(...shocksForCode(code, "labourProductivity", lp, ctx.mapping, ctx.weights, exposure));
    }
    notes.push(
      "Licensing: applied to the whole of each industry reached, scaled by its exposure, as the PC did (L2). Weighting by employment in the licensed occupations (A-P08) waits for employment by OSCA occupation, which the ABS does not yet publish; set each industry's exposure to that share where it is known. Its entry-cost effect is not costed again in C4 (overlap rule O-4).",
    );
  }
  if (lever.nonCompetes) {
    const pass = t.get("F-C8-02", "passThrough");
    const high = t.get("F-C8-02", "wageEffectHighUse");
    const low = t.get("F-C8-02", "wageEffectLowUse");
    const base = t.get("F-C8-02", "baselineCoverage");
    const wage = (high.value + low.value) / 2; // A-P21: the PC's 24 high-use industries are not listed
    const covered = params.input("levers.labour.nonCompetes.coveredShareChange", lever.nonCompetes.coveredShareChange);
    const scale = -covered / base.value;
    const lp = pass.value * wage * scale;
    for (const { code, exposure } of reach(brief, lever.nonCompetes.industries, params)) {
      if (code === "A" || divisionOf(code) === "A") {
        notes.push(`Non-competes: agriculture (${code}) is left out, as in the PC's L1.`);
        continue;
      }
      effects.push({
        anzsic: code,
        measure: "Labour productivity",
        value: lp * exposure,
        unit: "% change",
        chain: [
          { label: "Change in the share of workers bound", value: covered, unit: "share" },
          { label: "Share bound now (a ban removes it all)", value: base.value, unit: "share", evidence: base.id },
          { label: "Wage effect of a ban: midpoint of the PC's high-use (2.4%) and low-use (1.4%) industries", value: wage, unit: "%", evidence: high.id },
          { label: "Pass-through to labour productivity", value: pass.value, unit: "share", evidence: pass.id },
          { label: "Exposure", value: exposure, unit: "share" },
        ],
      });
      shocks.push(...shocksForCode(code, "labourProductivity", lp, ctx.mapping, ctx.weights, exposure));
    }
    notes.push("Non-competes: the PC's L1 chain (10% of the Johnson, Lavetti & Lipsitz wage effect), scaled by the change in coverage (A-P09); the wage effect is the midpoint of the PC's two industry groups because the PC does not list which 24 industries are high-use (A-P21).");
  }
  return outcome("C8", { used: t.used, effects, shocks, notes });
}

// ---- C9: R&D (F-C9-01, F-C9-02) -------------------------------------------------------------------------------

export function c9Innovation(brief: PolicyBrief, ctx: CostingContext, params: ParamSource = CENTRAL): ChannelOutcome | null {
  const lever = brief.levers.innovation;
  if (!lever) return null;
  const reasons: string[] = [];
  if (lever.productApprovalTimeChangeDays !== undefined) reasons.push("A change in product-approval time has no verified productivity elasticity; it is reported, not quantified");
  if (lever.rdUserCostChangePct === undefined) return outcome("C9", { reasons });
  const t = tracker(params);
  const eps = t.get("F-C9-01", "epsilonLongRun");
  const beta = t.get("F-C9-02", "beta");
  const dlnUc = Math.log(1 + params.input("levers.innovation.rdUserCostChangePct", lever.rdUserCostChangePct) / 100);
  const dlnRd = eps.value * dlnUc;
  const codes = reach(brief, lever.industries, params);
  const rd = codes.reduce((s, { code, exposure }) => s + berdOf(code, ctx) * exposure, 0);
  const gdpRd = ctx.gdpByYear[ctx.berdYear];
  if (!gdpRd) return outcome("C9", { reasons: [...reasons, `No GDP for the BERD year (${ctx.berdYear})`] });
  const dIntensityPp = (rd * dlnRd * 100) / gdpRd; // percentage points of GDP
  const mfp = pct(beta.value * dIntensityPp);
  return outcome("C9", {
    used: t.used,
    reasons,
    effects: [
      {
        anzsic: "TOT",
        measure: "Multifactor productivity (labour-augmenting), economy-wide, long run",
        value: mfp,
        unit: "% change",
        chain: [
          { label: "Change in the R&D user cost", value: dlnUc, unit: "log points" },
          { label: "Long-run elasticity of R&D to its user cost", value: eps.value, unit: "elasticity", evidence: eps.id },
          { label: `Business R&D of the industries reached × exposure (BERD ${ctx.berdYear})`, value: rd, unit: "$ million" },
          { label: `Change in business R&D intensity (GDP ${ctx.berdYear})`, value: dIntensityPp, unit: "pp of GDP" },
          { label: "MFP per pp of business R&D intensity", value: beta.value, unit: "log points per pp", evidence: beta.id },
        ],
      },
    ],
    shocks: economyWide("labourProductivity", mfp, ctx),
    notes: [
      `R&D in the industries reached is ${((100 * rd) / berdTotal(ctx)).toFixed(1)}% of all business R&D. Its productivity effect is economy-wide (spillovers, Égert & Gal), and enters as labour-augmenting (A-P18). The short-run elasticity is a tenth of the long run; the time path (F-B-04) phases the effect in.`,
    ],
  });
}

// ---- C10: trade and foreign investment (F-C10-01..03) -------------------------------------------------------------

export function c10Trade(brief: PolicyBrief, ctx: CostingContext, params: ParamSource = CENTRAL): ChannelOutcome | null {
  const lever = brief.levers.trade;
  if (!lever) return null;
  const t = tracker(params);
  const effects: IndustryEffect[] = [];
  const other: OtherEffect[] = [];
  const reasons: string[] = [];
  let shocks: IndustryShock[] = [];
  if (lever.opennessChangePp !== undefined) {
    const beta = t.get("F-C10-01", "beta");
    const openness = params.input("levers.trade.opennessChangePp", lever.opennessChangePp);
    const mfp = pct(beta.value * openness);
    effects.push({
      anzsic: "TOT",
      measure: "Multifactor productivity (labour-augmenting), economy-wide, long run",
      value: mfp,
      unit: "% change",
      chain: [
        { label: "Change in trade openness", value: openness, unit: "pp of GDP" },
        { label: "MFP per pp of openness", value: beta.value, unit: "log points per pp", evidence: beta.id },
      ],
    });
    shocks = economyWide("labourProductivity", mfp, ctx);
  }
  if (lever.tariffChangePp !== undefined) {
    const check = t.get("F-C10-02", "gdpEffect");
    reasons.push(`A tariff change is not costed by formula: it works through prices and the terms of trade, which need a CGE model. For scale, the PC found that removing all remaining tariffs raises GDP by about ${check.value}% (0.13–0.25%)`);
  }
  if (lever.fdiRestrictivenessChangePct !== undefined) {
    const e = t.get("F-C10-03", "elasticity");
    const fdi = params.input("levers.trade.fdiRestrictivenessChangePct", lever.fdiRestrictivenessChangePct);
    other.push({
      label: "Change in the stock of foreign direct investment (not added to GDP: no verified productivity elasticity)",
      value: e.value * fdi,
      unit: "% change",
      chain: [
        { label: "Change in the FDI restrictiveness index", value: fdi, unit: "%" },
        { label: "Elasticity of bilateral FDI stocks to the index", value: e.value, unit: "elasticity", evidence: e.id },
      ],
    });
  }
  return outcome("C10", { used: t.used, effects, shocks, other, reasons });
}

// ---- C11: the efficiency cost of funding (F-C11-01) -------------------------------------------------------------

export function c11Fiscal(brief: PolicyBrief, _ctx: CostingContext, params: ParamSource = CENTRAL): ChannelOutcome | null {
  const lever = brief.levers.fiscal;
  if (!lever) return null;
  if (lever.fundingTax === "other") return outcome("C11", { reasons: ["The funding tax is \"other\": enter its marginal excess burden as a custom value to cost it"] });
  const t = tracker(params);
  const meb = t.get("F-C11-01", `meb.${lever.fundingTax}`);
  const revenue = params.input("levers.fiscal.revenueChangeDollarsPerYear", lever.revenueChangeDollarsPerYear);
  return outcome("C11", {
    used: t.used,
    other: [
      {
        label: "Efficiency (welfare) cost of the funding, a year (negative is a cost)",
        value: -meb.value * revenue,
        unit: "$ a year",
        chain: [
          { label: "Revenue raised (+) or given up (−) through the funding tax", value: revenue, unit: "$ a year" },
          { label: "Marginal excess burden of that tax", value: meb.value, unit: "$ per $", evidence: meb.id },
        ],
      },
    ],
    notes: ["A welfare cost, reported beside GDP rather than in it (plan §3.2, principle 4)."],
  });
}

// ---- C4: entry and exit (F-C4-01..04) -------------------------------------------------------------------------------

const GRADE_ORDER = ["A", "B", "C", "D"] as const;
/** The weaker of two grades (D is weakest). */
export const weaker = (a: Grade | null, b: Grade): Grade => (a === null ? b : GRADE_ORDER[Math.max(GRADE_ORDER.indexOf(a), GRADE_ORDER.indexOf(b))]!);

/** True when the entry lever is costed in C4, so its entrants' compliance costs leave C1 (overlap rule O-1). */
export function entryCosted(brief: PolicyBrief): boolean {
  const e = brief.levers.entry;
  return !!e && (e.costPerEntrantChangeDollars !== undefined || e.numberCap !== undefined);
}

export function c4Entry(brief: PolicyBrief, ctx: CostingContext, params: ParamSource = CENTRAL): ChannelOutcome | null {
  const lever = brief.levers.entry;
  if (!lever) return null;
  const t = tracker(params);
  const reasons: string[] = [];
  const notes: string[] = [];
  const effects: IndustryEffect[] = [];
  const shocks: IndustryShock[] = [];
  const other: OtherEffect[] = [];
  const codes = reach(brief, lever.industries, params);
  const all = ctx.entryRate.TOT;

  // Step 1: the change in each industry's entry rate, percentage points (F-C4-01, F-C4-02).
  const step1 = new Map<string, { pp: number; chain: Factor[] }>();
  const add = (code: string, pp: number, chain: Factor[]) => {
    const prev = step1.get(code);
    step1.set(code, { pp: (prev?.pp ?? 0) + pp, chain: [...(prev?.chain ?? []), ...chain] });
  };
  if (lever.costPerEntrantChangeDollars !== undefined) {
    const eps = t.get("F-C4-01", "epsilon");
    const share = t.get("F-C4-01", "entryCostShareAU");
    const own = lever.baselineCostPerEntrantDollars !== undefined;
    const base = own ? params.input("levers.entry.baselineCostPerEntrantDollars", lever.baselineCostPerEntrantDollars!) : (share.value / 100) * ctx.gdpPerCapita;
    const change = params.input("levers.entry.costPerEntrantChangeDollars", lever.costPerEntrantChangeDollars);
    if (!(base + change > 0)) {
      reasons.push(`The cut in entry cost ($${-change}) is as large as the baseline cost per new business ($${Math.round(base)}); the log form of F-C4-01 needs a cost above zero (A-P11)`);
    } else {
      const dln = Math.log((base + change) / base);
      for (const { code } of codes) {
        const div = divisionOf(code);
        const rate = div ? ctx.entryRate[div] : undefined;
        if (rate === undefined || all === undefined) {
          reasons.push(`No entry rate for industry ${code}`);
          continue;
        }
        if (rate < all) {
          notes.push(`Industry ${code}: its division's entry rate (${rate}%, ${ctx.entryRateYear}) is below the all-industry rate (${all}%), so it is not a naturally high-entry industry and the entry-cost effect is not applied (A-P03, A-P29).`);
          continue;
        }
        add(code, eps.value * dln, [
          {
            label: own ? "Cost per new business before the change (entered)" : `Cost per new business before the change: ${share.value}% of GDP per head (${ctx.gdpYear})`,
            value: base,
            unit: "$",
            ...(own ? {} : { evidence: share.id }),
          },
          { label: "Change in the cost per new business", value: change, unit: "$" },
          { label: "Change in ln(entry cost ÷ GDP per head)", value: dln, unit: "log points" },
          { label: "Entry rate per log point of entry cost (naturally high-entry industries)", value: eps.value, unit: "pp per log point", evidence: eps.id },
          { label: `Division entry rate (${ctx.entryRateYear}), all industries ${all}%`, value: rate, unit: "%" },
        ]);
      }
      if (!own) notes.push("The baseline entry cost is Djankov et al.'s measure for Australia (2.25% of GDP per head in 1999, one simple start-up), applied to every industry; enter the industries' own cost per new business where it is known.");
    }
  }
  if (lever.numberCap) {
    const cap = lever.numberCap;
    const s = params.input("levers.entry.numberCap.excludedEntrantShare", cap.excludedEntrantShare);
    const sign = cap.change === "introduce" || cap.change === "tighten" ? -1 : 1;
    for (const { code } of codes) {
      const div = divisionOf(code);
      const rate = div ? ctx.entryRate[div] : undefined;
      if (rate === undefined) {
        reasons.push(`No entry rate for industry ${code}`);
        continue;
      }
      add(code, sign * s * rate, [
        { label: `Share of would-be entrants the cap ${sign < 0 ? "keeps out" : "lets in"}`, value: s, unit: "share" },
        { label: `Division entry rate (${ctx.entryRateYear})`, value: rate, unit: "%" },
      ]);
    }
  }
  if (lever.approvalTimeChangeDays !== undefined) {
    reasons.push("A change in approval time for new businesses has no verified entry elasticity; it is reported, not quantified. Enter its cost to an entrant (for example, income forgone while waiting) as a change in the cost per new business to cost it");
  }
  if (lever.exitCostChangeDollars !== undefined) reasons.push("Exit costs have no verified elasticity; they are reported, not quantified (F-C4-04)");

  // Overlap rule O-4: licensing is costed in C8; entry costs here must not include it.
  const licensed = brief.levers.labour?.licensing ? reach(brief, brief.levers.labour.licensing.industries, params).map((c) => c.code) : [];
  const both = [...step1.keys()].filter((code) => licensed.some((l) => overlaps(l, code)));
  if (both.length) {
    notes.push(`${both.length > 1 ? "Industries" : "Industry"} ${both.join(", ")} also ${both.length > 1 ? "have" : "has"} a licensing change, costed in C8: the entry cost here must leave out the cost of the licence (overlap rule O-4).`);
  }

  // Step 2: faster convergence to the frontier (F-C4-03). The long-run gain closes part of the gap (A-P30).
  let gapUsed = false;
  if (step1.size) {
    const beta2 = t.get("F-C4-03", "beta2");
    const lambda0 = t.get("F-C4-03", "lambda0");
    const gap = lever.frontierGapLogPoints !== undefined ? params.input("levers.entry.frontierGapLogPoints", lever.frontierGapLogPoints) : undefined;
    for (const [code, { pp, chain }] of step1) {
      const exposure = exposureOf(code, brief, params);
      const dLambda = beta2.value * pp;
      const steps: Factor[] = [
        ...chain,
        { label: "Change in the entry rate", value: pp, unit: "pp" },
        { label: "Extra convergence speed per pp of entry rate (β₂)", value: beta2.value, unit: "per pp", evidence: beta2.id },
        { label: "Convergence speed at the average entry rate (λ)", value: lambda0.value, unit: "a year", evidence: lambda0.id },
        { label: "Change in the convergence speed", value: dLambda, unit: "a year" },
      ];
      if (gap === undefined) {
        effects.push({ anzsic: code, measure: "Entry rate", value: pp, unit: "pp", chain: steps });
        other.push({ label: `Change in the speed of convergence to the frontier, industry ${code} (no productivity effect without the gap)`, value: dLambda, unit: "a year", chain: steps });
        continue;
      }
      gapUsed = true;
      const lp = pct((gap * dLambda) / (lambda0.value + dLambda));
      effects.push({
        anzsic: code,
        measure: "Labour productivity, long run (faster catch-up to the frontier)",
        value: lp * exposure,
        unit: "% change",
        chain: [
          ...steps,
          { label: "Distance from the frontier (entered), ln(frontier ÷ industry)", value: gap, unit: "log points" },
          { label: "Long-run gain gap × Δλ/(λ + Δλ)", value: lp, unit: "%" },
          { label: "Exposure", value: exposure, unit: "share" },
        ],
      });
      shocks.push(...shocksForCode(code, "labourProductivity", lp, ctx.mapping, ctx.weights, exposure));
    }
    notes.push(
      gap === undefined
        ? "Step 2 (F-C4-03): the productivity effect needs the industries' distance from the global frontier, which no public source gives (it needs BLADE), so only the change in convergence speed is reported (A-P12)."
        : "Step 2 (F-C4-03): faster convergence closes part of the distance from the frontier; at speed λ the long-run labour productivity gain is gap × Δλ/(λ + Δλ), most of it within five years (A-P30). The gap is the user's, graded D.",
    );
  }
  const o = outcome("C4", { used: t.used, effects, shocks, other, reasons, notes });
  if (gapUsed) o.grade = weaker(o.grade, "D"); // A-P12: a user-entered gap
  return o;
}

// ---- C5: size thresholds (F-C5-01, F-C5-02) -------------------------------------------------------------------------

/** Employment size bands of CABEE and Australian Industry (persons employed), with the CABEE bands each covers. */
const SIZE_BANDS = [
  { band: "0-4", lo: 0, hi: 4, cabee: ["nonemp", "1-4"] },
  { band: "5-19", lo: 5, hi: 19, cabee: ["5-19"] },
  { band: "20-199", lo: 20, hi: 199, cabee: ["20-199"] },
  { band: "200+", lo: 200, hi: Infinity, cabee: ["200+"] },
] as const;

export function c5Thresholds(brief: PolicyBrief, ctx: CostingContext, params: ParamSource = CENTRAL): ChannelOutcome | null {
  if (!brief.levers.thresholds.length) return null;
  const t = tracker(params);
  const band = t.get("F-C5-01", "band");
  const taxEquivalent = t.get("F-C5-02", "labourTaxEquivalent");
  const other: OtherEffect[] = [];
  const reasons: string[] = [];
  for (const th of brief.levers.thresholds) {
    if (th.metric !== "employees") {
      reasons.push(`Threshold "${th.id}": the parameter file has size bands by employment only, not by ${th.metric}, so the screen is not run`);
      continue;
    }
    const codes = reach(brief, th.industries, params);
    const cost = params.input(`levers.thresholds.${th.id}.costAbovePerYearDollars`, th.costAbovePerYearDollars);
    for (const value of [th.value, ...(th.previousValue !== undefined ? [th.previousValue] : [])]) {
      const lo = value * (1 - band.value);
      const hi = value * (1 + band.value);
      const near = SIZE_BANDS.filter((b) => b.lo <= hi && b.hi >= lo);
      const above = SIZE_BANDS.find((b) => b.lo <= value && value <= b.hi) ?? near.at(-1)!;
      let businesses = 0;
      let employment = 0;
      let wagesAbove = 0;
      let businessesAbove = 0;
      for (const { code, exposure } of codes) {
        const counts = ctx.businessesByBand[code];
        const div = divisionOf(code);
        if (!counts || !div) {
          reasons.push(`Threshold "${th.id}": no business counts by size for industry ${code}`);
          continue;
        }
        const n = (b: (typeof SIZE_BANDS)[number]) => b.cabee.reduce((s, c) => s + (counts[c] ?? 0), 0) * exposure;
        businesses += near.reduce((s, b) => s + n(b), 0);
        const ai = ctx.industryByBand[div];
        // Australian Industry is by division: a finer code takes its division's figures in proportion to its businesses.
        const divCounts = ctx.businessesByBand[div];
        const shareOf = (b: (typeof SIZE_BANDS)[number]) => {
          const d = divCounts ? b.cabee.reduce((s, c) => s + (divCounts[c] ?? 0), 0) : 0;
          return d > 0 ? n(b) / d : 0;
        };
        if (ai) {
          employment += near.reduce((s, b) => s + (ai[b.band]?.employment ?? 0) * shareOf(b), 0);
          wagesAbove += (ai[above.band]?.wages ?? 0) * shareOf(above);
          businessesAbove += n(above);
        }
      }
      const window = `${Math.ceil(lo)}–${Math.floor(hi)} employees`;
      const bands = near.map((b) => b.band).join(", ");
      other.push({
        label: `Threshold "${th.id}" at ${value} employees: businesses in the size bands that overlap ${window} (${bands}; CABEE ${ctx.sizeYear})`,
        value: businesses,
        unit: "businesses",
        chain: [{ label: "Screening band either side of the threshold", value: band.value, unit: "share", evidence: band.id }],
      });
      if (employment > 0) {
        other.push({ label: `Threshold "${th.id}" at ${value} employees: employment in those bands (Australian Industry ${ctx.industryByBandYear})`, value: employment, unit: "thousand persons", chain: [] });
      }
      if (wagesAbove > 0 && businessesAbove > 0) {
        const perBusiness = (wagesAbove * 1e6) / businessesAbove;
        other.push({
          label: `Threshold "${th.id}": cost a year above the threshold as a share of an average wage bill in the ${above.band} band, against the French rules' 2.3% labour-tax equivalent`,
          value: pct(cost / perBusiness),
          unit: "% of wages",
          chain: [
            { label: "Cost a year for a business above the threshold", value: cost, unit: "$" },
            { label: `Average wage bill of a business in the ${above.band} band`, value: perBusiness, unit: "$" },
            { label: "Labour-tax equivalent of the French 50-employee rules (GLVR2016)", value: taxEquivalent.value, unit: "%", evidence: taxEquivalent.id },
          ],
        });
      }
    }
  }
  reasons.push(
    "The GDP cost of a size threshold is not quantified: the published structural estimates (Gourio & Roys, under 0.3% of output per worker; Garicano, Lelarge & Van Reenen, 1.3–3.4% of GDP) are for French rules and cannot be scaled to this threshold without the share of employment within ±10% of it, which the ABS size bands do not resolve (A-P05)",
  );
  return outcome("C5", { used: t.used, other, reasons, notes: ["A screen (F-C5-01): how many businesses and workers sit near the threshold, and how large its cost is against wages."] });
}
