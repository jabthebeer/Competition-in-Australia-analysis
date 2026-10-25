// What the bundled data says about the industries in a brief's scope (plan §3.1, step 2): ANZSIC names, business
// counts and entry and exit rates (CABEE), value added (input-output tables, rescaled to the latest GDP) and, for
// divisions, employment (Australian Industry). Display only: the engine reads the same tables through its context.
import { divisionOf, valueAddedOf, type CostingContext } from "../productivity/index";
import type { CostingParameters } from "./costingData";

export interface AnzsicCode {
  code: string;
  name: string;
  level: "division" | "subdivision" | "group" | "class";
}

type Row = Record<string, unknown>;
const rows = (p: CostingParameters, id: string): Row[] => ((p.tables[id] as { rows?: Row[] } | undefined)?.rows ?? []) as Row[];

/** The ANZSIC 2006 codelist bundled with the parameters. */
export function anzsicCodes(p: CostingParameters): Map<string, AnzsicCode> {
  const out = new Map<string, AnzsicCode>();
  for (const r of rows(p, "abs_anzsic.codes")) {
    if (typeof r.code === "string" && typeof r.name === "string") out.set(r.code, { code: r.code, name: r.name, level: r.level as AnzsicCode["level"] });
  }
  return out;
}

export interface IndustryFacts {
  code: string;
  name?: string;
  /** Businesses operating at the end of the CABEE year, and entry and exit rates (per 100 at the start). */
  businesses?: number;
  entryRatePct?: number;
  exitRatePct?: number;
  /** Factor income in the input-output tables, $ million in the latest year's prices. */
  valueAdded: number;
  /** Employment, thousand persons (Australian Industry; divisions only, excluding finance and insurance). */
  employment?: number;
}

export function industryFacts(code: string, ctx: CostingContext, p: CostingParameters, names: Map<string, AnzsicCode>): IndustryFacts {
  const cabee = rows(p, "abs_cabee_latest.class_size").find((r) => r.anzsic === code && r.size_band === "total");
  const div = divisionOf(code);
  const employment = /^[A-S]$/.test(code) && div ? ctx.industryByBand[div]?.total?.employment : undefined;
  const num = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? v : undefined);
  return {
    code,
    name: names.get(code)?.name,
    businesses: num(cabee?.end),
    entryRatePct: num(cabee?.entry_rate_pct),
    exitRatePct: num(cabee?.exit_rate_pct),
    valueAdded: valueAddedOf(code, ctx),
    employment: employment !== undefined && Number.isFinite(employment) ? employment : undefined,
  };
}
