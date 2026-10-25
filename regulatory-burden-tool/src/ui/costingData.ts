// The ALICIA costing parameters bundled into this build (costing-params-plugin.ts), checked on load.
// P1 shows their sources and vintages; the productivity engine reads the tables from P4.
import { z } from "zod";

export const CostingSourceSchema = z.looseObject({
  id: z.string().min(1),
  title: z.string(),
  publisher: z.string(),
  release: z.string(),
  release_date: z.string().nullable().optional(),
  next_release: z.string().nullable().optional(),
  url: z.string(),
  licence: z.string(),
  retrieved: z.string().nullable().optional(),
  status: z.enum(["current", "fallback"]).default("current"),
});

export const CostingParametersSchema = z.looseObject({
  schema: z.literal("alicia-costing-parameters"),
  version: z.literal(1),
  vintage: z.string().nullable(),
  sources: z.array(CostingSourceSchema),
  tables: z.record(z.string(), z.unknown()),
});

export type CostingSource = z.output<typeof CostingSourceSchema>;
export type CostingParameters = z.output<typeof CostingParametersSchema>;

export type CostingLoad = { ok: true; parameters: CostingParameters } | { ok: false; problem: string };

export function checkCostingParameters(data: unknown): CostingLoad {
  const r = CostingParametersSchema.safeParse(data);
  if (r.success) return { ok: true, parameters: r.data };
  const first = r.error.issues[0];
  return { ok: false, problem: first ? `${first.path.join(".") || "(file)"}: ${first.message}` : "unreadable" };
}

/** Loads the bundled parameters. They sit in their own chunk, so pages that don't need them stay small. */
export async function loadCostingParameters(): Promise<CostingLoad> {
  const mod = await import("virtual:costing-parameters");
  return checkCostingParameters(mod.default);
}

// ---- the register export (alicia costing-register) ------------------------------------------------------------

export const RegisterEvaluationSchema = z.looseObject({
  id: z.string(),
  verdict: z.string().nullable().optional(),
  finding: z.string().nullable().optional(),
  grade: z.string().nullable().optional(),
  evaluated_on: z.string().nullable().optional(),
  archived: z.boolean().optional(),
  page: z.string().nullable().optional(),
});

export const RegisterRecordSchema = z.looseObject({
  id: z.string().min(1),
  title: z.string(),
  jurisdiction: z.string(),
  family: z.string().nullable().optional(),
  direction: z.string(),
  direction_rationale: z.string().nullable().optional(),
  direction_sources: z.array(z.string()).default([]),
  channels: z.array(z.string()).default([]),
  industries: z.array(z.looseObject({ anzsic: z.string(), exposure: z.string().optional(), name: z.string().optional() })).default([]),
  commencement: z.string().nullable().optional(),
  review_status: z.string().optional(),
  evaluation: RegisterEvaluationSchema.nullable().optional(),
});

export const CostingRegisterSchema = z.looseObject({
  schema: z.literal("alicia-costing-register"),
  version: z.literal(1),
  channels: z.record(z.string(), z.string()),
  notes: z.string().optional(),
  records: z.array(RegisterRecordSchema),
});

export type RegisterRecord = z.output<typeof RegisterRecordSchema>;
export type CostingRegister = z.output<typeof CostingRegisterSchema>;

export function checkCostingRegister(data: unknown): { ok: true; register: CostingRegister } | { ok: false; problem: string } {
  const r = CostingRegisterSchema.safeParse(data);
  if (r.success) return { ok: true, register: r.data };
  const first = r.error.issues[0];
  return { ok: false, problem: first ? `${first.path.join(".") || "(file)"}: ${first.message}` : "unreadable" };
}

/** Loads the bundled register export, in its own chunk. */
export async function loadCostingRegister() {
  const mod = await import("virtual:costing-register");
  return checkCostingRegister(mod.default);
}
