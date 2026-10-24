// The data a costing needs, built once from the bundled parameters (data/processed/costing/parameters.json):
// input-output weights rescaled to the latest year's nominal GDP, GDP and GDP per head, depreciation rates and capital
// shares by division, business R&D, entry rates, and businesses, employment and wages by size band. Every number here comes from a parameter table; nothing is assumed.
import { divisionOf } from "./anzsic";
import { ioWeights, ioigReach, type IndustryWeight } from "./layerB";

type Row = Record<string, unknown>;
interface Table {
  rows: Row[];
}
export interface ParameterFile {
  vintage: string | null;
  sources: { id: string; release: string }[];
  tables: Record<string, unknown>;
}

export interface CostingContext {
  /** Input-output industries, factor income rescaled to `gdpYear` dollars ($ million). */
  weights: IndustryWeight[];
  mapping: { ioig: string; anzsic: string }[];
  /** Nominal GDP in `gdpYear`, $ million (ASNA). */
  gdp: number;
  gdpYear: string;
  /** Nominal GDP by financial year, $ million (ASNA). */
  gdpByYear: Record<string, number>;
  /** Year of the input-output tables and the factor by which their values are rescaled to `gdpYear`. */
  ioYear: string;
  ioScale: number;
  /** Depreciation rate by ANZSIC division: consumption of fixed capital ÷ net capital stock, current prices (ASNA). */
  depreciation: Record<string, number>;
  /** Capital income share of value added by ANZSIC division, latest year (ABS productivity, market sector only), and its year. */
  capitalShare: Record<string, number>;
  capitalShareYear: string;
  /** Business expenditure on R&D by ANZSIC subdivision or division, $ million (BERD), and its year. */
  berd: Record<string, number>;
  berdYear: string;
  /** GDP per head in `gdpYear`, $ (ASNA Table 1), and the population it implies (GDP ÷ GDP per head). */
  gdpPerCapita: number;
  population: number;
  /** Business entry rate by ANZSIC division and in total ("TOT"), per cent of businesses at the start of the year (CABEE), and its year. */
  entryRate: Record<string, number>;
  entryRateYear: string;
  /** Businesses by ANZSIC code (class, subdivision or division) and employment size band, end of `sizeYear` (CABEE). */
  businessesByBand: Record<string, Record<string, number>>;
  sizeYear: string;
  /** Employment (thousand persons) and wages ($ million) by division and size band (Australian Industry; excludes division K), and their year. */
  industryByBand: Record<string, Record<string, { employment: number; wages: number }>>;
  industryByBandYear: string;
  parameterVintage: string | null;
}

function rows(params: ParameterFile, id: string): Row[] {
  const t = params.tables[id] as Table | undefined;
  if (!t || !Array.isArray(t.rows)) throw new Error(`The parameter file has no table "${id}"`);
  return t.rows;
}

const num = (v: unknown): number => (typeof v === "number" && Number.isFinite(v) ? v : NaN);
/** "2023-24" for release labels such as "2023-24"; the first financial year found otherwise. */
const fyOf = (release: string): string | undefined => /\d{4}-\d{2}/.exec(release)?.[0];

export function buildContext(params: ParameterFile): CostingContext {
  const gdpRows = rows(params, "abs_asna.gdp")
    .filter((r) => Number.isFinite(num(r.gdp_current)))
    .sort((a, b) => String(a.fy).localeCompare(String(b.fy)));
  const latest = gdpRows.at(-1);
  if (!latest) throw new Error("The parameter file has no GDP");
  const gdpYear = String(latest.fy);
  const ioRelease = params.sources.find((s) => s.id === "abs_io")?.release ?? "";
  const ioYear = fyOf(ioRelease);
  const ioGdp = gdpRows.find((r) => r.fy === ioYear);
  if (!ioYear || !ioGdp) throw new Error(`The input-output tables' year (${ioRelease || "unknown"}) has no GDP to rescale from`);
  const ioScale = num(latest.gdp_current) / num(ioGdp.gdp_current);
  const weights = ioWeights(rows(params, "abs_io.industries") as never).map((w) => ({ ...w, va: w.va * ioScale, wages: w.wages * ioScale }));

  const capital = rows(params, "abs_asna.capital");
  const capYear = capital.map((r) => String(r.fy)).sort().at(-1);
  const depreciation: Record<string, number> = {};
  for (const r of capital) {
    if (r.fy !== capYear || typeof r.anzsic !== "string" || !/^[A-S]$/.test(r.anzsic)) continue;
    const rate = num(r.cfc_current) / num(r.ncs_current);
    if (Number.isFinite(rate) && rate > 0) depreciation[r.anzsic] = rate;
  }

  const mfp = rows(params, "abs_mfp.industry");
  const mfpYear = mfp.map((r) => String(r.fy)).sort().at(-1) ?? "";
  const capitalShare: Record<string, number> = {};
  for (const r of mfp) {
    const share = num(r.capital_income_share);
    if (r.fy === mfpYear && typeof r.anzsic === "string" && /^[A-S]$/.test(r.anzsic) && share > 0 && share < 1) capitalShare[r.anzsic] = share;
  }

  const berd: Record<string, number> = {};
  for (const r of rows(params, "abs_berd.subdivision_size")) {
    if (typeof r.anzsic === "string" && Number.isFinite(num(r.rd_total))) berd[r.anzsic] = num(r.rd_total) / 1000; // $ thousand → $ million
  }
  const berdYear = fyOf(params.sources.find((s) => s.id === "abs_berd")?.release ?? "") ?? "";

  const perCapita = rows(params, "abs_asna.key_aggregates").find((r) => r.fy === gdpYear);
  const gdpPerCapita = num(perCapita?.gdp_per_capita_current);
  if (!(gdpPerCapita > 0)) throw new Error(`The parameter file has no GDP per head for ${gdpYear}`);

  const cabee = rows(params, "abs_cabee_latest.division_fy");
  const entryRateYear = cabee.map((r) => String(r.fy)).sort().at(-1) ?? "";
  const entryRate: Record<string, number> = {};
  for (const r of cabee) if (r.fy === entryRateYear && typeof r.anzsic === "string" && Number.isFinite(num(r.entry_rate_pct))) entryRate[r.anzsic] = num(r.entry_rate_pct);

  const businessesByBand: Record<string, Record<string, number>> = {};
  for (const r of rows(params, "abs_cabee_latest.class_size")) {
    if (typeof r.anzsic !== "string" || !Number.isFinite(num(r.end))) continue;
    (businessesByBand[r.anzsic] ??= {})[String(r.size_band)] = num(r.end);
  }
  // The size table is CABEE cube 2, whose release reads e.g. "jul2021-jun2025 (cube 2)": its last financial year.
  const cube2 = /jun(\d{4}) \(cube 2\)/.exec(params.sources.find((s) => s.id === "abs_cabee_latest")?.release ?? "");
  const sizeYear = cube2?.[1] ? `${Number(cube2[1]) - 1}-${cube2[1].slice(2)}` : "";

  const ai = rows(params, "abs_australian_industry.size_division");
  const industryByBandYear = ai.map((r) => String(r.fy)).sort().at(-1) ?? "";
  const industryByBand: Record<string, Record<string, { employment: number; wages: number }>> = {};
  for (const r of ai) {
    if (r.fy !== industryByBandYear || typeof r.anzsic !== "string") continue;
    (industryByBand[r.anzsic] ??= {})[String(r.size_band)] = { employment: num(r.employment), wages: num(r.wages) };
  }

  return {
    weights,
    mapping: rows(params, "abs_io.ioig_anzsic") as never,
    gdp: num(latest.gdp_current),
    gdpYear,
    gdpByYear: Object.fromEntries(gdpRows.map((r) => [String(r.fy), num(r.gdp_current)])),
    ioYear,
    ioScale,
    depreciation,
    capitalShare,
    capitalShareYear: mfpYear,
    berd,
    berdYear,
    gdpPerCapita,
    population: (num(latest.gdp_current) * 1e6) / gdpPerCapita,
    entryRate,
    entryRateYear,
    businessesByBand,
    sizeYear,
    industryByBand,
    industryByBandYear,
    parameterVintage: params.vintage,
  };
}

const knownCache = new WeakMap<CostingContext, ReadonlySet<string>>();

/** Known input-output industries. */
export function knownIndustries(ctx: CostingContext): ReadonlySet<string> {
  let known = knownCache.get(ctx);
  if (!known) knownCache.set(ctx, (known = new Set(ctx.weights.map((w) => w.id))));
  return known;
}

/**
 * Factor income of an ANZSIC code, $ million: the input-output industries it reaches, each counted in proportion to the
 * share of its classes the code covers. This is the split Layer B uses (A-P20), so a cost shock divided by it and
 * spread by `shocksForCode` reaches GDP exactly as the cost itself would.
 */
export function valueAddedOf(code: string, ctx: CostingContext): number {
  const byId = new Map(ctx.weights.map((w) => [w.id, w]));
  return ioigReach(code, ctx.mapping, knownIndustries(ctx)).reduce((s, r) => s + r.share * (byId.get(r.ioig)?.va ?? 0), 0);
}

/** The ANZSIC division of an input-output industry: the division of its first class. */
export function divisionOfIndustry(ioig: string, ctx: CostingContext): string | undefined {
  let first = firstClassCache.get(ctx);
  if (!first) {
    first = new Map();
    for (const m of ctx.mapping) if (!first.has(m.ioig)) first.set(m.ioig, m.anzsic);
    firstClassCache.set(ctx, first);
  }
  const cls = first.get(ioig);
  return cls ? divisionOf(cls) : undefined;
}
const firstClassCache = new WeakMap<CostingContext, Map<string, string>>();

/**
 * Business R&D of an ANZSIC code, $ million (BERD is published by subdivision): a division sums its subdivisions; a
 * group or class takes its subdivision's figure in proportion to value added (the A-P20 split). Subdivisions the ABS
 * suppresses count as zero, so a code that needs one is understated.
 */
export function berdOf(code: string, ctx: CostingContext): number {
  if (/^[A-S]$/.test(code)) {
    return ctx.berd[code] ?? Object.entries(ctx.berd).reduce((s, [k, v]) => s + (/^\d{2}$/.test(k) && divisionOf(k) === code ? v : 0), 0);
  }
  if (/^\d{2}$/.test(code)) return ctx.berd[code] ?? 0;
  const sub = code.slice(0, 2);
  const subVa = valueAddedOf(sub, ctx);
  return subVa > 0 ? ((ctx.berd[sub] ?? 0) * valueAddedOf(code, ctx)) / subVa : 0;
}

/** Total business R&D, $ million. */
export function berdTotal(ctx: CostingContext): number {
  return ctx.berd.TOT ?? Object.entries(ctx.berd).reduce((s, [k, v]) => s + (/^\d{2}$/.test(k) ? v : 0), 0);
}
