// The productivity costing as tidy CSV (plan §3.1 step 7): one row per figure, each with its central value and,
// where it has one, its 10–90% range, its channel's evidence grade and the evidence gate's status, so no figure
// travels without its bounds (plan §3.2, principle 6). GDP figures the gate hides are left out unless the brief
// opts in to showing them.
import type { CostingContext } from "./context";
import type { GateResult } from "./costing";
import type { CostingResult } from "./engine";
import type { PolicyBrief } from "./brief";
import type { Ranges } from "./uncertainty";

export const COSTING_CSV_COLUMNS = [
  { name: "brief_id", description: "Policy brief identifier" },
  { name: "parameter_vintage", description: "Release date of the newest source in the bundled parameters" },
  { name: "gate", description: "Evidence gate: full, indicative, or hidden (shown only when the brief opts in)" },
  { name: "section", description: "gdp (economy-wide), npv, channel, effect (direct, by industry), other (reported beside GDP) or industry (GDP by input-output industry)" },
  { name: "channel", description: "Channel id (C1 to C12), blank for totals" },
  { name: "industry", description: "ANZSIC code (effects) or input-output industry (industry rows); TOT = whole economy" },
  { name: "year", description: "Year of the policy (1 = its first financial year); blank for the long run" },
  { name: "measure", description: "What the figure measures" },
  { name: "unit", description: "Unit of central, p10 and p90" },
  { name: "central", description: "Central estimate (all parameters at their evidence-library defaults)" },
  { name: "p10", description: "10th percentile of the Monte Carlo (blank where the figure has no range)" },
  { name: "p90", description: "90th percentile of the Monte Carlo" },
  { name: "grade", description: "The channel's evidence grade (A strongest to D), the tool's own assumptions aside" },
] as const;

type Row = Partial<Record<(typeof COSTING_CSV_COLUMNS)[number]["name"], string | number>>;

/** A CSV cell; text that a spreadsheet would read as a formula gets a leading apostrophe. */
function cell(v: string | number | undefined): string {
  if (v === undefined) return "";
  if (typeof v === "number") return Number.isFinite(v) ? String(v) : "";
  const s = /^[=+@\t\r-]/.test(v) ? `'${v}` : v;
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function costingCsv(brief: PolicyBrief, r: CostingResult, ranges: Ranges, gate: GateResult, ctx: CostingContext): string {
  const base: Row = { brief_id: brief.id, parameter_vintage: ctx.parameterVintage ?? "", gate: gate.status };
  const rows: Row[] = [];
  const grade = new Map(r.channels.map((c) => [c.channel, c.grade ?? ""]));
  if (gate.showGdp) {
    rows.push({ section: "gdp", measure: "Change in real GDP, long run", unit: "%", central: r.gdpPct, p10: ranges.gdpPct.p10, p90: ranges.gdpPct.p90 });
    rows.push({ section: "gdp", measure: `Change in real GDP, long run (${r.gdpYear} dollars a year)`, unit: "$ million", central: r.gdpDollars, p10: ranges.gdpDollars.p10, p90: ranges.gdpDollars.p90 });
    r.path.forEach((p, i) => rows.push({ section: "gdp", year: p.year, measure: "Change in real GDP", unit: "%", central: p.gdpPct, p10: ranges.path[i]?.gdpPct.p10, p90: ranges.path[i]?.gdpPct.p90 }));
    r.npv.forEach((n, i) => rows.push({ section: "npv", measure: `Present value over ${brief.meta.durationYears} years at ${n.rate * 100}%`, unit: "$ million", central: n.dollars, ...(i === 0 ? { p10: ranges.npv.p10, p90: ranges.npv.p90 } : {}) }));
    for (const c of r.channels) {
      const p = ranges.byChannel.find((b) => b.channel === c.channel)?.gdpPct;
      rows.push({ section: "channel", channel: c.channel, measure: `Change in real GDP, long run: ${c.name}`, unit: "%", central: c.gdpPct, p10: p?.p10, p90: p?.p90, grade: grade.get(c.channel) });
    }
    const names = new Map(ctx.weights.map((w) => [w.id, w.name]));
    const byIndustry = new Map<string, number>();
    for (const x of r.layerB.contributions) byIndustry.set(x.industry, (byIndustry.get(x.industry) ?? 0) + x.gdpPct * r.realisationFactor);
    for (const [id, v] of byIndustry) if (v !== 0) rows.push({ section: "industry", industry: `${id} ${names.get(id) ?? ""}`.trim(), measure: "Change in real GDP from this industry, long run", unit: "%", central: v });
  }
  for (const c of r.channels) {
    for (const e of c.effects) rows.push({ section: "effect", channel: c.channel, industry: e.anzsic, measure: e.measure, unit: e.unit, central: e.value, grade: grade.get(c.channel) });
    for (const o of c.other) rows.push({ section: "other", channel: c.channel, measure: o.label, unit: o.unit, central: o.value, grade: grade.get(c.channel) });
  }
  const header = COSTING_CSV_COLUMNS.map((c) => c.name);
  const lines = [header.join(","), ...rows.map((row) => header.map((h) => cell({ ...base, ...row }[h])).join(","))];
  return `${lines.join("\r\n")}\r\n`;
}
