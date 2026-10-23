// The policy brief (schema v1): everything the Policy costing tab needs to cost a prospective
// policy. It holds the RBM proposal for the burden costing (unchanged, DECISIONS #81) and the
// levers for the productivity and competition costing (plan §5).
//
// Conventions:
// - Every lever field is a CHANGE from the baseline, so it may be negative (a cut).
// - Units are in the field name: ...Dollars ($, in the brief's price base), ...Pct (per cent: -5 means
//   -5%), ...Pp (percentage points), ...Days or ...Months, ...Share (0 to 1).
// - A quantity is a number or a { low, high } range; the midpoint is the central value (as in the RBM, A-07).
// - Lever industries default to the brief's scope and must lie within it.
// - Strict objects throughout: unknown keys are rejected.
import { z } from "zod";
import { formatIssues } from "../engine/migrate";
import {
  AnzsicSchema,
  EmploymentBandSchema,
  EntityTypeSchema,
  OverrideSchema,
  ProposalSchema,
  ProvenanceMapSchema,
  QuantitySchema,
  ShareSchema,
  SourceSchema,
  type Proposal,
} from "../engine/schema";
import { covers, overlaps } from "./anzsic";
import { CHANNEL_IDS, CHANNELS, SHOCK_TYPE_IDS, type ChannelId, type InputBlock } from "./channels";

export const BRIEF_SCHEMA_VERSION = 1 as const;

const finite = z.number().refine(Number.isFinite, "Must be a finite number");
const positive = finite.pipe(z.number().gt(0));
const int = z.number().int();

/** A signed number, or a low–high range whose midpoint is the central value. */
export const SignedQuantitySchema = z.union([
  finite,
  z.strictObject({ low: finite, high: finite }).refine((r) => r.low <= r.high, { message: "The low value must not exceed the high value" }),
]);
export type SignedQuantity = z.output<typeof SignedQuantitySchema>;

/** The central value of a quantity (a range's midpoint). */
export function central(q: SignedQuantity | z.output<typeof QuantitySchema>): number {
  return typeof q === "number" ? q : (q.low + q.high) / 2;
}

const Id = z
  .string()
  .min(1)
  .max(120)
  .regex(/^[A-Za-z0-9_-]+$/, "Use letters, digits, hyphens or underscores only");

export const JurisdictionSchema = z.enum(["CTH", "NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"]);
export const StateSchema = JurisdictionSchema.exclude(["CTH"]);
export const ALL_SIZE_BANDS = EmploymentBandSchema.options;

const Industries = z.array(AnzsicSchema).min(1);

// ---- meta and scope -------------------------------------------------------------------------------------------

export const BriefMetaSchema = z.strictObject({
  title: z.string(),
  summary: z.string().optional(),
  jurisdictions: z.array(JurisdictionSchema).min(1),
  proposalType: z.enum(["new", "reform", "repeal"]).default("reform"),
  /** First financial year of effect, named by the calendar year it starts in (2027 = 2027-28). */
  startYear: int.min(2000).max(2100),
  /** Years until the policy has its full effect; 0 = full effect from the first year. */
  phaseInYears: int.min(0).default(0),
  durationYears: int.min(1).max(30).default(10),
  durationOverride: OverrideSchema.optional(),
  /** Price base of every dollar input, e.g. "2025-26". */
  priceBase: z.string().regex(/^\d{4}-\d{2}$/, 'Use a financial year such as "2025-26"').default("2025-26"),
  source: SourceSchema.optional(),
  provenance: ProvenanceMapSchema.optional(),
});

export const ScopeIndustrySchema = z.strictObject({
  anzsic: AnzsicSchema,
  /** Share of the industry's activity the policy reaches. */
  exposure: ShareSchema.default(1),
  role: z.enum(["direct", "indirect"]).default("direct"),
  note: z.string().optional(),
});

export const BriefScopeSchema = z.strictObject({
  industries: z.array(ScopeIndustrySchema).min(1),
  sizeBands: z.array(EmploymentBandSchema).min(1).default([...ALL_SIZE_BANDS]),
  entityTypes: z.array(EntityTypeSchema).min(1).default(["private"]),
  /** States and territories affected; omitted means all within the jurisdictions. */
  states: z.array(StateSchema).min(1).optional(),
  provenance: ProvenanceMapSchema.optional(),
});

// ---- levers ---------------------------------------------------------------------------------------------------

const atLeastOne =
  (fields: readonly string[], what: string) =>
  (v: Record<string, unknown>, ctx: z.RefinementCtx) => {
    if (!fields.some((f) => v[f] !== undefined)) ctx.addIssue({ code: "custom", message: `${what} needs at least one of: ${fields.join(", ")}` });
  };

/** C4 (entry and exit) and C2 (approval time). */
export const EntryLeverSchema = z
  .strictObject({
    industries: Industries.optional(),
    /** One-off cost per new business. */
    costPerEntrantChangeDollars: SignedQuantitySchema.optional(),
    approvalTimeChangeDays: SignedQuantitySchema.optional(),
    numberCap: z
      .strictObject({
        change: z.enum(["introduce", "remove", "tighten", "loosen"]),
        /** Share of would-be entrants the cap keeps out (after the change). */
        excludedEntrantShare: ShareSchema,
      })
      .optional(),
    /** One-off cost per exiting business. */
    exitCostChangeDollars: SignedQuantitySchema.optional(),
    provenance: ProvenanceMapSchema.optional(),
  })
  .superRefine(atLeastOne(["costPerEntrantChangeDollars", "approvalTimeChangeDays", "numberCap", "exitCostChangeDollars"], "An entry lever"));

/** C5: one size threshold. */
export const ThresholdLeverSchema = z
  .strictObject({
    id: Id,
    industries: Industries.optional(),
    metric: z.enum(["employees", "turnover", "payroll", "assets"]),
    change: z.enum(["introduce", "remove", "move"]),
    /** The threshold after the change (persons or dollars); for "remove", the threshold being removed. */
    value: positive,
    /** The threshold before a move. */
    previousValue: positive.optional(),
    /** Ongoing cost a year for a business above the threshold. */
    costAbovePerYearDollars: QuantitySchema,
    design: z.enum(["cliff", "taper"]).default("cliff"),
    provenance: ProvenanceMapSchema.optional(),
  })
  .superRefine((t, ctx) => {
    if (t.change === "move" && (t.previousValue === undefined || t.previousValue === t.value)) {
      ctx.addIssue({ code: "custom", path: ["previousValue"], message: "Moving a threshold needs its previous value, different from the new one" });
    }
    if (t.change !== "move" && t.previousValue !== undefined) {
      ctx.addIssue({ code: "custom", path: ["previousValue"], message: `A previous value only applies when a threshold is moved, not when it is ${t.change === "introduce" ? "introduced" : "removed"}` });
    }
  });

/** C3 (user cost of capital) and C2 (investment approval delay). */
export const CapitalLeverSchema = z
  .strictObject({
    industries: Industries.optional(),
    companyTaxRate: z.strictObject({ from: ShareSchema, to: ShareSchema }).optional(),
    /** Change in the present value of depreciation deductions per dollar invested (z, share units). */
    depreciationPvChange: SignedQuantitySchema.optional(),
    investmentApprovalDelayChangeMonths: SignedQuantitySchema.optional(),
    riskPremiumChangePp: SignedQuantitySchema.optional(),
    provenance: ProvenanceMapSchema.optional(),
  })
  .superRefine(atLeastOne(["companyTaxRate", "depreciationPvChange", "investmentApprovalDelayChangeMonths", "riskPremiumChangePp"], "A capital lever"));

export const RestrictionSchema = z.enum([
  "priceControl",
  "quantityControl",
  "advertising",
  "standards",
  "tradingHours",
  "exclusivity",
  "information",
  "other",
]);

/** OECD PMR (2018 methodology) indicators the brief can move; which have an elasticity is settled by the evidence library (P3). */
export const PmrIndicatorSchema = z.enum([
  "economyWide",
  "adminRegulatoryBurden",
  "barriersToEntry",
  "barriersServiceSectors",
  "energy",
  "transport",
  "communications",
  "lawyers",
  "retailMedicines",
  "other",
]);

const conductBase = {
  industries: Industries.optional(),
  restrictions: z.array(RestrictionSchema).default([]),
  description: z.string().optional(),
  provenance: ProvenanceMapSchema.optional(),
};

/** C6 or C7: one route per policy (overlap rule O-3). */
export const ConductLeverSchema = z.discriminatedUnion("route", [
  z.strictObject({ route: z.literal("markup"), ...conductBase, markupChangePct: SignedQuantitySchema }),
  z.strictObject({
    route: z.literal("pmr"),
    ...conductBase,
    indicator: PmrIndicatorSchema,
    /** Indicator values on the OECD 0–6 scale. */
    from: finite.pipe(z.number().min(0).max(6)),
    to: finite.pipe(z.number().min(0).max(6)),
  }),
]);

/** C8. */
export const LabourLeverSchema = z
  .strictObject({
    licensing: z
      .strictObject({
        /** OSCA 2024 occupation codes (six digits). */
        occupations: z.array(z.string().regex(/^\d{6}$/, "Use a six-digit OSCA 2024 occupation code")).min(1),
        industries: Industries.optional(),
        /** Change in occupational entry regulation stringency (OECD index points). */
        stringencyChange: SignedQuantitySchema,
        mutualRecognition: z.boolean().default(false),
      })
      .optional(),
    nonCompetes: z
      .strictObject({
        industries: Industries.optional(),
        /** Change in the share of workers bound by a non-compete clause. */
        coveredShareChange: SignedQuantitySchema,
      })
      .optional(),
    provenance: ProvenanceMapSchema.optional(),
  })
  .superRefine(atLeastOne(["licensing", "nonCompetes"], "A labour lever"));

/** C9. */
export const InnovationLeverSchema = z
  .strictObject({
    industries: Industries.optional(),
    rdUserCostChangePct: SignedQuantitySchema.optional(),
    productApprovalTimeChangeDays: SignedQuantitySchema.optional(),
    provenance: ProvenanceMapSchema.optional(),
  })
  .superRefine(atLeastOne(["rdUserCostChangePct", "productApprovalTimeChangeDays"], "An innovation lever"));

/** C10. */
export const TradeLeverSchema = z
  .strictObject({
    industries: Industries.optional(),
    tariffChangePp: SignedQuantitySchema.optional(),
    /** Change in trade openness (exports plus imports, % of GDP), in percentage points. */
    opennessChangePp: SignedQuantitySchema.optional(),
    fdiRestrictivenessChangePct: SignedQuantitySchema.optional(),
    provenance: ProvenanceMapSchema.optional(),
  })
  .superRefine(atLeastOne(["tariffChangePp", "opennessChangePp", "fdiRestrictivenessChangePct"], "A trade lever"));

/** Taxes with a marginal excess burden in Treasury WP 2015-01 (Cao et al.). */
export const FundingTaxSchema = z.enum([
  "companyIncome",
  "labourIncome",
  "personalIncome",
  "gstCurrentBase",
  "gstBroadBase",
  "conveyancingDuty",
  "landTax",
  "other",
]);

/** C11. Positive: revenue raised through the funding tax; negative: revenue given up. */
export const FiscalLeverSchema = z.strictObject({
  revenueChangeDollarsPerYear: SignedQuantitySchema,
  fundingTax: FundingTaxSchema,
  provenance: ProvenanceMapSchema.optional(),
});

/** An effect the user enters directly. Graded D unless it has a source. */
export const CustomShockSchema = z.strictObject({
  id: Id,
  channel: z.enum(CHANNEL_IDS),
  industry: AnzsicSchema,
  type: z.enum(SHOCK_TYPE_IDS),
  /** In the shock type's unit (SHOCK_TYPES). */
  size: SignedQuantitySchema,
  /** Required when a lever already feeds this channel for this industry (overlap rule O-6). */
  relation: z.enum(["adds", "replaces"]).optional(),
  justification: z.string().min(1),
  source: SourceSchema.optional(),
  provenance: ProvenanceMapSchema.optional(),
});

export const LeversSchema = z.strictObject({
  entry: EntryLeverSchema.optional(),
  thresholds: z.array(ThresholdLeverSchema).default([]),
  capital: CapitalLeverSchema.optional(),
  conduct: ConductLeverSchema.optional(),
  labour: LabourLeverSchema.optional(),
  innovation: InnovationLeverSchema.optional(),
  trade: TradeLeverSchema.optional(),
  fiscal: FiscalLeverSchema.optional(),
  custom: z.array(CustomShockSchema).default([]),
});

/** How results are computed and shown (plan §6.3–6.6). */
export const AnalysisSchema = z.strictObject({
  /** Scales every productivity effect (plan §6.4); 1 = as estimated. */
  realisationFactor: finite.pipe(z.number().min(0).max(2)).default(1),
  /** Real discount rate for the productivity NPV (OIA CBA guidance: 7%). */
  discountRate: finite.pipe(z.number().min(0).max(0.2)).default(0.07),
  sensitivityRates: z.array(finite.pipe(z.number().min(0).max(0.2))).default([0.03, 0.1]),
  /** Show economy-wide figures that the evidence gate would hide (plan §6.6). */
  showUngatedEconomyWide: z.boolean().default(false),
  draws: int.min(100).max(20000).default(2000),
  seed: int.min(0).default(1),
});

// ---- the brief ------------------------------------------------------------------------------------------------

type LeverPart = { block: InputBlock; path: (string | number)[]; industries?: string[] };

/** Every lever part present in the brief (a threshold, licensing, non-competes, …), with the industries it names, if any. */
function leverParts(levers: z.output<typeof LeversSchema>): LeverPart[] {
  const out: LeverPart[] = [];
  const add = (block: InputBlock, path: (string | number)[], part: { industries?: string[] } | undefined) => {
    if (part) out.push({ block, path: [...path, "industries"], ...(part.industries ? { industries: part.industries } : {}) });
  };
  add("entry", ["levers", "entry"], levers.entry);
  levers.thresholds.forEach((t, i) => add("thresholds", ["levers", "thresholds", i], t));
  add("capital", ["levers", "capital"], levers.capital);
  if (levers.conduct) add(levers.conduct.route === "markup" ? "conduct.markup" : "conduct.pmr", ["levers", "conduct"], levers.conduct);
  add("labour", ["levers", "labour", "licensing"], levers.labour?.licensing);
  add("labour", ["levers", "labour", "nonCompetes"], levers.labour?.nonCompetes);
  add("innovation", ["levers", "innovation"], levers.innovation);
  add("trade", ["levers", "trade"], levers.trade);
  add("fiscal", ["levers", "fiscal"], levers.fiscal ? {} : undefined); // economy-wide: reaches the scope
  return out;
}

/** The lever blocks present, each with the industries it reaches: a part that names none reaches the whole scope. */
export function leverReach(brief: Pick<PolicyBrief, "levers" | "scope">): { block: InputBlock; industries: string[] }[] {
  const scope = brief.scope.industries.map((i) => i.anzsic);
  const reach = new Map<InputBlock, Set<string>>();
  for (const part of leverParts(brief.levers)) {
    const set = reach.get(part.block) ?? new Set<string>();
    for (const code of part.industries ?? scope) set.add(code);
    reach.set(part.block, set);
  }
  return [...reach].map(([block, industries]) => ({ block, industries: [...industries] }));
}

export const PolicyBriefSchema = z
  .strictObject({
    schemaVersion: z.literal(BRIEF_SCHEMA_VERSION),
    kind: z.literal("policy-brief"),
    id: Id,
    meta: BriefMetaSchema,
    scope: BriefScopeSchema,
    /** The RBM proposal for the burden costing (C1, C2). */
    burden: ProposalSchema.optional(),
    levers: LeversSchema.default({ thresholds: [], custom: [] }),
    analysis: AnalysisSchema.default({
      realisationFactor: 1,
      discountRate: 0.07,
      sensitivityRates: [0.03, 0.1],
      showUngatedEconomyWide: false,
      draws: 2000,
      seed: 1,
    }),
    /** Vintage of the bundled parameter file the brief was costed with (P2). */
    parameterVintage: z.string().optional(),
  })
  .superRefine((b, ctx) => {
    const issue = (path: (string | number)[], message: string) => ctx.addIssue({ code: "custom", path, message });
    const m = b.meta;

    if (new Set(m.jurisdictions).size !== m.jurisdictions.length) issue(["meta", "jurisdictions"], "A jurisdiction is listed twice");
    if (m.phaseInYears > m.durationYears) issue(["meta", "phaseInYears"], `The phase-in (${m.phaseInYears} years) is longer than the duration (${m.durationYears} years)`);
    if (m.durationYears > 10 && !m.durationOverride) {
      issue(["meta", "durationYears"], "The RBM sets a 10-year default (RBM p. 6). Record the justification in durationOverride to use a longer period");
    }

    // Scope: each industry once, and no code inside another (it would be counted twice).
    const codes = b.scope.industries.map((i) => i.anzsic);
    codes.forEach((c, i) => {
      codes.slice(0, i).forEach((earlier) => {
        if (overlaps(c, earlier)) {
          issue(["scope", "industries", i, "anzsic"], c === earlier ? `Industry ${c} is listed twice` : `Industries ${earlier} and ${c} overlap: list one or the other`);
        }
      });
    });
    const inScope = (code: string) => codes.some((s) => covers(s, code));

    const states = b.scope.states;
    if (states && !m.jurisdictions.includes("CTH")) {
      states.forEach((s, i) => {
        if (!m.jurisdictions.includes(s)) issue(["scope", "states", i], `${s} is not one of the brief's jurisdictions`);
      });
    }

    for (const { path, industries } of leverParts(b.levers)) {
      industries?.forEach((code, i) => {
        if (!inScope(code)) issue([...path, i], `Industry ${code} is outside the brief's scope`);
      });
    }

    const thresholdIds = new Set<string>();
    b.levers.thresholds.forEach((t, i) => {
      if (thresholdIds.has(t.id)) issue(["levers", "thresholds", i, "id"], `Duplicate threshold id "${t.id}"`);
      thresholdIds.add(t.id);
    });

    // Overlap rule O-5: a company tax cut cannot also be the funding tax.
    if (b.levers.capital?.companyTaxRate && b.levers.fiscal?.fundingTax === "companyIncome") {
      issue(["levers", "fiscal", "fundingTax"], "The company tax change is costed in C3; choose the tax that funds it (overlap rule O-5)");
    }

    // Custom shocks: in scope, unique, and explicit about overlapping a lever (overlap rule O-6).
    const reach = leverReach(b);
    const fed = (channel: ChannelId, industry: string) =>
      reach.some((r) => CHANNELS[channel].inputs.includes(r.block) && r.industries.some((code) => overlaps(code, industry))) ||
      (b.burden !== undefined && CHANNELS[channel].inputs.includes("burden") && inScope(industry));
    const customIds = new Set<string>();
    b.levers.custom.forEach((s, i) => {
      if (customIds.has(s.id)) issue(["levers", "custom", i, "id"], `Duplicate custom shock id "${s.id}"`);
      customIds.add(s.id);
      if (!inScope(s.industry)) issue(["levers", "custom", i, "industry"], `Industry ${s.industry} is outside the brief's scope`);
      if (!CHANNELS[s.channel].shocks.includes(s.type) && s.channel !== "C12") {
        issue(["levers", "custom", i, "type"], `Channel ${s.channel} produces ${CHANNELS[s.channel].shocks.join(", ") || "no productivity shock"}, not ${s.type}`);
      }
      if (s.relation === undefined && fed(s.channel, s.industry)) {
        issue(["levers", "custom", i, "relation"], `A lever already feeds ${s.channel} for industry ${s.industry}: say whether this shock replaces it or adds to it (overlap rule O-6)`);
      }
    });

    if (b.burden && b.burden.durationYears !== m.durationYears) {
      issue(["burden", "durationYears"], `The burden proposal runs ${b.burden.durationYears} years but the brief ${m.durationYears}; use the same duration`);
    }
  });

export type PolicyBrief = z.output<typeof PolicyBriefSchema>;
export type PolicyBriefInput = z.input<typeof PolicyBriefSchema>;

export class BriefValidationError extends Error {
  readonly issues: string[];
  constructor(issues: string[]) {
    super(`The policy brief is not valid:\n${issues.map((i) => `  - ${i}`).join("\n")}`);
    this.name = "BriefValidationError";
    this.issues = issues;
  }
}

/** Parses a policy brief, applying defaults; throws BriefValidationError with every problem found. */
export function parseBrief(input: unknown): PolicyBrief {
  const result = PolicyBriefSchema.safeParse(input);
  if (!result.success) throw new BriefValidationError(formatIssues(result.error));
  return result.data;
}

// ---- warnings (do not block costing) ---------------------------------------------------------------------------

export const BRIEF_WARNINGS = {
  "PB-01": "Nothing to cost: the brief has no burden proposal and no levers.",
  "PB-02": "A burden population's industry is outside the brief's scope.",
  "PB-03": "A custom shock has no source, so it is graded D and economy-wide results are gated (plan §6.6).",
  "PB-04": "A value is an unconfirmed language-model estimate; results are marked as a draft until it is confirmed.",
} as const;
export type BriefWarningCode = keyof typeof BRIEF_WARNINGS;

export interface BriefWarning {
  code: BriefWarningCode;
  message: string;
  path: string;
}

function modelEstimates(prov: Record<string, { origin: string }> | undefined, at: string): string[] {
  return Object.entries(prov ?? {})
    .filter(([, p]) => p.origin === "modelEstimate")
    .map(([key]) => `${at}.${key}`);
}

/** Soft problems in a parsed brief. The burden proposal's own warnings come from the RBM engine. */
export function briefWarnings(b: PolicyBrief): BriefWarning[] {
  const out: BriefWarning[] = [];
  const l = b.levers;
  const anyLever = !!(l.entry || l.thresholds.length || l.capital || l.conduct || l.labour || l.innovation || l.trade || l.fiscal || l.custom.length);
  if (!b.burden && !anyLever) out.push({ code: "PB-01", message: BRIEF_WARNINGS["PB-01"], path: "levers" });

  const codes = b.scope.industries.map((i) => i.anzsic);
  b.burden?.populations.forEach((pop: Proposal["populations"][number], i: number) => {
    if (pop.industry && !codes.some((s) => covers(s, pop.industry!))) {
      out.push({ code: "PB-02", message: `Population "${pop.label || pop.id}" is in industry ${pop.industry}, outside the brief's scope.`, path: `burden.populations.${i}.industry` });
    }
  });

  l.custom.forEach((s, i) => {
    if (!s.source) out.push({ code: "PB-03", message: `Custom shock "${s.id}" has no source: graded D.`, path: `levers.custom.${i}.source` });
  });

  const provenanced: [Record<string, { origin: string }> | undefined, string][] = [
    [b.meta.provenance, "meta"],
    [b.scope.provenance, "scope"],
    [l.entry?.provenance, "levers.entry"],
    ...l.thresholds.map((t, i): [Record<string, { origin: string }> | undefined, string] => [t.provenance, `levers.thresholds.${i}`]),
    [l.capital?.provenance, "levers.capital"],
    [l.conduct?.provenance, "levers.conduct"],
    [l.labour?.provenance, "levers.labour"],
    [l.innovation?.provenance, "levers.innovation"],
    [l.trade?.provenance, "levers.trade"],
    [l.fiscal?.provenance, "levers.fiscal"],
    ...l.custom.map((s, i): [Record<string, { origin: string }> | undefined, string] => [s.provenance, `levers.custom.${i}`]),
  ];
  for (const [prov, at] of provenanced) {
    for (const path of modelEstimates(prov, at)) {
      out.push({ code: "PB-04", message: `${path} is a language-model estimate that hasn't been confirmed.`, path });
    }
  }
  return out;
}
