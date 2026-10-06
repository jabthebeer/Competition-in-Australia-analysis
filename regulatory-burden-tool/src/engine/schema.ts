// Versioned input schema shared by the engine, the UI and saved/exported files.
// Strict objects: unknown keys (e.g. a discount rate or benefits) are rejected,
// so nothing outside the framework can reach the RBE (DECISIONS #34).
import { z } from "zod";
import { PARAMETERS } from "./parameters";

export const SCHEMA_VERSION = 1 as const;

const nonNegative = z.number().refine(Number.isFinite, "Must be a finite number").pipe(z.number().min(0));
const int = z.number().int();

/** A point value, or a low–high range whose midpoint is the point estimate (A-07). */
export const QuantitySchema = z.union([
  nonNegative,
  z
    .strictObject({ low: nonNegative, high: nonNegative })
    .refine((r) => r.low <= r.high, { message: "The low value must not exceed the high value" }),
]);

/** A share between 0 and 1, or a range within 0–1. */
export const ShareSchema = z.union([
  nonNegative.pipe(z.number().max(1)),
  z
    .strictObject({ low: nonNegative.pipe(z.number().max(1)), high: nonNegative.pipe(z.number().max(1)) })
    .refine((r) => r.low <= r.high, { message: "The low value must not exceed the high value" }),
]);

const Id = z.string().min(1).max(120);

export const SourceSchema = z.strictObject({
  description: z.string().min(1),
  url: z.string().min(1).optional(),
  vintage: z.string().optional(),
  accessed: z.string().optional(),
});

/** Any departure from a default needs a justification and a source (R-36, R-50). */
export const OverrideSchema = z.strictObject({
  justification: z.string().min(1),
  source: SourceSchema,
});

const RateKind = z.enum(["work", "leisure", "volunteer"]);

export const RateTableSchema = z.strictObject({
  work: z.strictObject({
    hourly: nonNegative,
    base: nonNegative,
    multiplier: nonNegative,
    override: OverrideSchema.optional(),
  }),
  leisure: z.strictObject({ hourly: nonNegative, override: OverrideSchema.optional() }),
  volunteer: z.strictObject({ hourly: nonNegative, override: OverrideSchema.optional() }),
  custom: z
    .array(
      z.strictObject({
        id: Id,
        label: z.string().min(1),
        kind: RateKind,
        hourly: nonNegative,
        override: OverrideSchema,
      }),
    )
    .default([]),
});

export function defaultRateTable(): z.output<typeof RateTableSchema> {
  const r = PARAMETERS.rates;
  return {
    work: { hourly: Number(r.work.hourly), base: Number(r.work.base), multiplier: Number(r.work.multiplier) },
    leisure: { hourly: Number(r.leisure.hourly) },
    volunteer: { hourly: Number(r.volunteer.hourly) },
    custom: [],
  };
}

export const GroupSchema = z.enum(["business", "communityOrg", "individual"]);
export const CohortSchema = z.enum(["small", "medium", "large", "all"]);
export const EmploymentBandSchema = z.enum(["nonEmploying", "1-4", "5-19", "20-199", "200+"]);
export const EntityTypeSchema = z.enum([
  "private",
  "gbe",
  "publicUniversity",
  "foreignGovOwnedBusiness",
  "governmentAgency",
]);

/** ANZSIC 2006: division letter (A–S), or a 2-, 3- or 4-digit subdivision, group or class code. */
export const AnzsicSchema = z
  .string()
  .regex(/^([A-S]|\d{2}|\d{3}|\d{4})$/, "Use an ANZSIC 2006 division letter (A–S) or a 2–4 digit code");

export const PopulationSchema = z.strictObject({
  id: Id,
  label: z.string().min(1),
  group: GroupSchema,
  cohort: CohortSchema.default("all"),
  employmentBand: EmploymentBandSchema.optional(),
  industry: AnzsicSchema.optional(),
  count: QuantitySchema,
  source: SourceSchema.optional(),
  nonResident: z.boolean().default(false),
  entityType: EntityTypeSchema.default("private"),
});

export const TimingSchema = z.discriminatedUnion("type", [
  z.strictObject({ type: z.literal("oneOff"), year: int.min(1).default(1) }),
  z.strictObject({ type: z.literal("ongoing"), startYear: int.min(1).default(1), endYear: int.min(1).optional() }),
  z.strictObject({ type: z.literal("everyKYears"), k: int.min(1), firstYear: int.min(1).default(1) }),
  z.strictObject({ type: z.literal("schedule"), factors: z.array(nonNegative).min(1) }),
]);

export const LabourSchema = z.strictObject({
  hours: QuantitySchema,
  timesPerYear: QuantitySchema,
  staff: QuantitySchema.optional(),
  rateId: z.string().min(1).default("work"),
});

export const PurchaseSchema = z.strictObject({
  unitCost: QuantitySchema,
  timesPerYear: QuantitySchema,
});

export const DelaySchema = z.strictObject({
  unit: z.enum(["days", "weeks", "months"]),
  applicationDelay: QuantitySchema.default(0),
  approvalDelay: QuantitySchema,
  readyAfter: QuantitySchema.default(0),
  netIncomePerUnit: QuantitySchema,
  extraExpensesPerUnit: QuantitySchema.default(0),
  waitingOnGovernment: z.boolean(),
});

export const SubsidySchema = z.strictObject({
  perEntityPerActiveYear: QuantitySchema,
  source: SourceSchema,
});

export const LineSchema = z.strictObject({
  populationId: Id,
  entities: QuantitySchema.optional(),
  complianceRate: ShareSchema.default(1),
  labour: LabourSchema.optional(),
  purchase: PurchaseSchema.optional(),
  delay: DelaySchema.optional(),
  subsidy: SubsidySchema.optional(),
  note: z.string().optional(),
});

export const CostTypeSchema = z.enum(["labour", "purchase", "delay"]);

export const SideSchema = z
  .strictObject({
    costType: CostTypeSchema,
    timing: TimingSchema,
    status: z.enum(["future", "alreadyIncurred"]).optional(),
    lines: z.array(LineSchema).min(1),
  })
  .superRefine((side, ctx) => {
    const seen = new Set<string>();
    side.lines.forEach((line, i) => {
      const blocks = (["labour", "purchase", "delay"] as const).filter((b) => line[b] !== undefined);
      if (blocks.length !== 1 || blocks[0] !== side.costType) {
        ctx.addIssue({
          code: "custom",
          path: ["lines", i],
          message: `Each line needs exactly one cost block, matching the side's cost type ("${side.costType}")`,
        });
      }
      if (side.costType === "delay" && line.subsidy) {
        ctx.addIssue({
          code: "custom",
          path: ["lines", i, "subsidy"],
          message: "Subsidies offset compliance costs only, not delay costs (RBM p. 3)",
        });
      }
      if (seen.has(line.populationId)) {
        ctx.addIssue({
          code: "custom",
          path: ["lines", i, "populationId"],
          message: `Population "${line.populationId}" appears twice on the same side`,
        });
      }
      seen.add(line.populationId);
    });
  });

export const TagSchema = z.enum([
  "commonIndustryPractice",
  "outsourcedService",
  "governmentFee",
  "tax",
  "fine",
  "nonCompliance",
  "enforcementActivity",
  "indirectEffect",
  "courtAdministration",
  "internationalObligation",
  "opportunityCost",
]);

export const LeverSchema = z.enum([
  "lessFrequent",
  "simplerForm",
  "threshold",
  "fewerStaff",
  "outcomeBased",
  "removeDuplication",
  "longerLicence",
  "fasterApproval",
  "removeObligation",
  "other",
]);

export const ScopeSchema = z
  .strictObject({
    classification: z.enum(["compliance", "enforcement", "split"]).default("compliance"),
    complianceShare: z.number().min(0).max(1).optional(),
    override: OverrideSchema.optional(),
  })
  .refine((s) => s.classification !== "split" || s.complianceShare !== undefined, {
    message: "A compliance/enforcement split needs a compliance share (RBM p. 15)",
    path: ["complianceShare"],
  });

export const ObligationSchema = z
  .strictObject({
    id: Id,
    name: z.string().min(1),
    description: z.string().optional(),
    category: z.enum(["administrative", "substantive", "delay"]),
    jurisdiction: z.enum(["commonwealth", "stateTerritory"]).default("commonwealth"),
    legalReference: z.strictObject({ instrument: z.string().min(1), provision: z.string().optional() }).optional(),
    scope: ScopeSchema.default({ classification: "compliance" }),
    doAnywayShare: ShareSchema.default(0),
    doAnywaySource: SourceSchema.optional(),
    tags: z.array(TagSchema).default([]),
    levers: z.array(LeverSchema).default([]),
    rateChangeJustification: OverrideSchema.optional(),
    current: SideSchema.nullable().default(null),
    reformed: SideSchema.nullable().default(null),
    timingOverride: z
      .strictObject({ reformStartYear: int.min(1).optional(), overlapYears: int.min(0).optional() })
      .optional(),
  })
  .superRefine((o, ctx) => {
    if (!o.current && !o.reformed) {
      ctx.addIssue({ code: "custom", message: "An obligation needs a current side, a reformed side, or both" });
    }
    for (const sideName of ["current", "reformed"] as const) {
      const side = o[sideName];
      if (!side) continue;
      const isDelay = side.costType === "delay";
      if (isDelay !== (o.category === "delay")) {
        ctx.addIssue({
          code: "custom",
          path: [sideName, "costType"],
          message: 'Delay costs use cost type "delay" and category "delay"; other categories use labour or purchase',
        });
      }
    }
    if (o.reformed?.status !== undefined) {
      ctx.addIssue({
        code: "custom",
        path: ["reformed", "status"],
        message: "Only current-regime costs can be marked as already incurred",
      });
    }
  });

export const OptionSchema = z
  .strictObject({
    id: Id,
    name: z.string().min(1),
    description: z.string().optional(),
    isStatusQuo: z.boolean().default(false),
    timing: z
      .strictObject({ reformStartYear: int.min(1).default(1), overlapYears: int.min(0).default(0) })
      .default({ reformStartYear: 1, overlapYears: 0 }),
    obligations: z.array(ObligationSchema).default([]),
    transitions: z.array(ObligationSchema).default([]),
  })
  .superRefine((opt, ctx) => {
    opt.transitions.forEach((t, i) => {
      if (t.current) {
        ctx.addIssue({
          code: "custom",
          path: ["transitions", i, "current"],
          message: "Transition costs are one-off switching costs of the reformed regime: leave the current side empty",
        });
      }
    });
    const ids = new Set<string>();
    [...opt.obligations, ...opt.transitions].forEach((o) => {
      if (ids.has(o.id)) ctx.addIssue({ code: "custom", message: `Duplicate obligation id "${o.id}"` });
      ids.add(o.id);
    });
  });

export const ProposalSchema = z
  .strictObject({
    id: Id,
    title: z.string().min(1),
    description: z.string().optional(),
    proposalType: z.enum(["reform", "new", "repeal"]).default("reform"),
    durationYears: int.min(PARAMETERS.duration.minYears).max(PARAMETERS.duration.maxYears).default(10),
    durationOverride: OverrideSchema.optional(),
    jurisdiction: z.enum(["commonwealthOnly", "interJurisdictional"]).default("commonwealthOnly"),
    baseline: z.enum(["statusQuo", "noInstrument"]).default("statusQuo"),
    remakesSunsettingInstrument: z.boolean().optional(),
    parameterVintage: z.string().default(PARAMETERS.vintage),
    rates: RateTableSchema.default(defaultRateTable),
    populations: z.array(PopulationSchema).min(1),
    options: z.array(OptionSchema).min(1),
  })
  .superRefine((p, ctx) => {
    if (p.durationYears > PARAMETERS.duration.maxYearsWithoutOverride && !p.durationOverride) {
      ctx.addIssue({
        code: "custom",
        path: ["durationYears"],
        message: "The framework sets a 10-year default and only contemplates shorter periods (RBM p. 6). Record OIA's agreement in durationOverride to use a longer period",
      });
    }
    const popIds = new Set<string>();
    p.populations.forEach((pop, i) => {
      if (popIds.has(pop.id)) ctx.addIssue({ code: "custom", path: ["populations", i, "id"], message: `Duplicate population id "${pop.id}"` });
      popIds.add(pop.id);
      if (pop.employmentBand && pop.cohort !== "all") {
        const bandCohort = PARAMETERS.employmentBands[pop.employmentBand].cohort;
        if (bandCohort !== pop.cohort) {
          ctx.addIssue({
            code: "custom",
            path: ["populations", i, "employmentBand"],
            message: `ABS employment band "${pop.employmentBand}" belongs to the ${bandCohort} cohort, not ${pop.cohort}`,
          });
        }
      }
    });
    const rateIds = new Set<string>(["work", "leisure", "volunteer", ...p.rates.custom.map((r) => r.id)]);
    const optIds = new Set<string>();
    p.options.forEach((opt, oi) => {
      if (optIds.has(opt.id)) ctx.addIssue({ code: "custom", path: ["options", oi, "id"], message: `Duplicate option id "${opt.id}"` });
      optIds.add(opt.id);
      const all = [
        ...opt.obligations.map((o, i) => ({ o, path: ["options", oi, "obligations", i] as (string | number)[] })),
        ...opt.transitions.map((o, i) => ({ o, path: ["options", oi, "transitions", i] as (string | number)[] })),
      ];
      for (const { o, path } of all) {
        for (const sideName of ["current", "reformed"] as const) {
          const side = o[sideName];
          if (!side) continue;
          if (side.timing.type === "schedule" && side.timing.factors.length !== p.durationYears) {
            ctx.addIssue({
              code: "custom",
              path: [...path, sideName, "timing", "factors"],
              message: `A year-by-year schedule needs exactly ${p.durationYears} values (one per year of the duration)`,
            });
          }
          side.lines.forEach((line, li) => {
            if (!popIds.has(line.populationId)) {
              ctx.addIssue({
                code: "custom",
                path: [...path, sideName, "lines", li, "populationId"],
                message: `Unknown population "${line.populationId}"`,
              });
            }
            if (line.labour && !rateIds.has(line.labour.rateId)) {
              ctx.addIssue({
                code: "custom",
                path: [...path, sideName, "lines", li, "labour", "rateId"],
                message: `Unknown labour rate "${line.labour.rateId}"`,
              });
            }
          });
        }
      }
    });
  });

export const ProposalFileSchema = z.strictObject({
  schemaVersion: z.literal(SCHEMA_VERSION),
  savedAt: z.string().optional(),
  proposal: ProposalSchema,
});

export type Quantity = z.output<typeof QuantitySchema>;
export type Source = z.output<typeof SourceSchema>;
export type Override = z.output<typeof OverrideSchema>;
export type RateTable = z.output<typeof RateTableSchema>;
export type Group = z.output<typeof GroupSchema>;
export type Cohort = z.output<typeof CohortSchema>;
export type Population = z.output<typeof PopulationSchema>;
export type Timing = z.output<typeof TimingSchema>;
export type Line = z.output<typeof LineSchema>;
export type CostType = z.output<typeof CostTypeSchema>;
export type Side = z.output<typeof SideSchema>;
export type Tag = z.output<typeof TagSchema>;
export type Obligation = z.output<typeof ObligationSchema>;
export type Option = z.output<typeof OptionSchema>;
export type Proposal = z.output<typeof ProposalSchema>;
export type ProposalInput = z.input<typeof ProposalSchema>;
export type ProposalFile = z.output<typeof ProposalFileSchema>;
