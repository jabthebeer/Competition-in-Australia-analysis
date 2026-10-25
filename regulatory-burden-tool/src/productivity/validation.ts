// P6 validation (plan §8): the engine against the Productivity Commission's own shock chains in PC National and
// against published models of a company tax cut. `scripts/validate-costing.ts` writes the results to
// docs/costing_validation.md; test T-VAL-01 checks the pass marks and that the note is current.
// Node only (it hashes the parameter sources): not exported from index.ts, so the web app never bundles it.
import { createHash } from "node:crypto";
import { parseBrief, type PolicyBrief } from "./brief";
import type { CostingContext, ParameterFile } from "./context";
import { runCosting } from "./costing";

export interface ValidationRow {
  id: string;
  label: string;
  /** What the tool was given (its Layer A chain or custom shocks). */
  input: string;
  /** Long-run change in real GDP, per cent: the tool's central value and 10–90% range. */
  tool: { central: number; p10: number; p90: number };
  /** The published figure, or its range across models. */
  published: { low: number; high: number; text: string; source: string };
  passMark: string;
  pass: boolean;
  note: string;
}

const ALL = "ABCDEFGHIJKLMNOPQRS".split("");
const L2 = ["30", "31", "32", "F", "46", "47", "48", "49", "52", "53", "69", "80", "81", "84", "85", "86", "87"];

function brief(id: string, industries: string[], levers: object): PolicyBrief {
  return parseBrief({ schemaVersion: 1, kind: "policy-brief", id, meta: { title: `Validation: ${id}`, jurisdictions: ["CTH"], startYear: 2027 }, scope: { industries: industries.map((anzsic) => ({ anzsic })) }, levers });
}

/** The same productivity shock on every division, as PC National applies it, entered as custom shocks citing the workbook. */
function everyIndustry(type: "mfp" | "labourProductivity", size: number) {
  return { custom: ALL.map((d) => ({ id: `pc-${d}`, channel: "C12", industry: d, type, size, justification: "The PC National shock, applied to every industry", source: { description: "PC National workbook (PC 2024)" } })) };
}

/** A fingerprint of the data a validation ran on: each source's id, release and file hashes. */
export function sourcesFingerprint(params: ParameterFile): string {
  const s = params.sources.map((x) => [x.id, x.release, ((x as { files?: { sha256?: string }[] }).files ?? []).map((f) => f.sha256 ?? "")]);
  return createHash("sha256").update(JSON.stringify(s)).digest("hex").slice(0, 16);
}

export function runValidation(params: ParameterFile, ctx: CostingContext, draws = 2000): ValidationRow[] {
  const sims = ((params.tables["pc_national.simulations"] as { rows: { code: string; real_gdp: number }[] }).rows ?? []).filter((r) => r.real_gdp !== null);
  const pc = (code: string) => {
    const r = sims.find((x) => x.code === code);
    if (!r) throw new Error(`PC National has no simulation ${code}`);
    return r.real_gdp;
  };
  const run = (b: PolicyBrief) => {
    const c = runCosting(b, ctx, { draws, seed: 1 });
    return { central: c.result.gdpPct, p10: c.ranges.gdpPct.p10, p90: c.ranges.gdpPct.p90 };
  };
  const within = (tool: number, target: number, tol = 0.15) => Math.abs(tool / target - 1) <= tol;
  const rows: ValidationRow[] = [];

  const l2 = run(brief("pc-l2", L2, { labour: { licensing: { occupations: ["381231"], stringencyChange: -0.5 } } }));
  rows.push({
    id: "L2",
    label: "Occupational licensing reform (PC National L2)",
    input: "C8 licensing: stringency −0.5 × 1.6 = +0.8% labour productivity in the PC's 15 licensed industries (17 ANZSIC codes)",
    tool: l2,
    published: { low: pc("L2"), high: pc("L2"), text: `${pc("L2").toFixed(3)}%`, source: "PC National, L2" },
    passMark: "±15% of the PC's real GDP",
    pass: within(l2.central, pc("L2")),
    note: "The shock is the PC's exactly (1.6 × 0.5); the difference is Layer B's aggregation.",
  });

  const l1 = run(brief("pc-l1", ALL, { labour: { nonCompetes: { coveredShareChange: -0.2 } } }));
  rows.push({
    id: "L1",
    label: "Non-compete ban (PC National L1)",
    input: "C8 non-competes: coverage −20 pp → 10% × 1.9% = +0.19% labour productivity in every non-agricultural industry",
    tool: l1,
    published: { low: pc("L1"), high: pc("L1"), text: `${pc("L1").toFixed(3)}%`, source: "PC National, L1" },
    passMark: "±15% of the PC's real GDP",
    pass: within(l1.central, pc("L1")),
    note: "The PC applies 0.24% in 24 service industries and 0.14% in the rest; it does not list the 24, so the tool uses the midpoint everywhere (A-P21).",
  });

  const h5 = run(brief("pc-h5", ALL, everyIndustry("labourProductivity", 0.03)));
  rows.push({
    id: "H5",
    label: "Labour productivity +0.03% (PC National H5)",
    input: "Custom shocks: +0.03% labour productivity in every division",
    tool: h5,
    published: { low: pc("H5"), high: pc("H5"), text: `${pc("H5").toFixed(4)}%`, source: "PC National, H5" },
    passMark: "±15% of the PC's real GDP",
    pass: within(h5.central, pc("H5")),
    note: "No lever covers the PC's telehealth chain, so its shock is entered as custom shocks.",
  });

  // B7tar: tariff removal plus +0.06% MFP for the compliance costs; its upper (0.09%) and lower (0.03%) runs differ
  // only in the MFP shock, so their difference isolates the compliance part from the tariff effects the tool does not model.
  const perPp = (pc("B7tar_upper") - pc("B7tar_lower")) / (0.09 - 0.03);
  const b7 = run(brief("pc-b7tar", ALL, everyIndustry("mfp", 0.06)));
  rows.push({
    id: "B7tar",
    label: "Tariff compliance costs, the MFP part of PC National B7tar",
    input: "Custom shocks: +0.06% multifactor productivity in every division",
    tool: b7,
    published: { low: perPp * 0.06, high: perPp * 0.06, text: `${(perPp * 0.06).toFixed(3)}% (from the upper and lower runs)`, source: "PC National, B7tar_upper − B7tar_lower" },
    passMark: "Within Layer B's MFP model-error band (0.58–1.147 × the PC's)",
    pass: b7.central / (perPp * 0.06) <= 1.147 && b7.central / (perPp * 0.06) >= 0.58,
    note: `The tariff removal itself works through prices and the terms of trade and is not costed by formula (F-C10-02). The isolation assumes the PC model is linear in the MFP shock; PC National's linearity tests (B9, D4hl, L2) find results within about 1% of proportional. The gap is the multiplier on an economy-wide MFP shock: ${(b7.central / 0.06).toFixed(2)} in the tool (1/(1 − α), α from the input-output tables) against ${perPp.toFixed(2)} in the PC's runs. The back-test's MFP cases shock single industries, so this case is outside them.`,
  });

  const tax = run(brief("company-tax-25", ALL, { capital: { companyTaxRate: { from: 0.3, to: 0.25 } } }));
  rows.push({
    id: "TAX25",
    label: "Company tax rate cut from 30% to 25%",
    input: "C3: company tax 30% → 25% in every division (user cost of capital, σ = 0.40)",
    tool: tax,
    published: {
      low: 0.6,
      high: 1.2,
      text: "0.6% to 1.2% (Treasury 1.0–1.2%, Independent Economics 0.7–0.9%, KPMG 0.6–0.8%, across three funding assumptions)",
      source: "Treasury, Economy-wide modelling for the 2016-17 Budget, Table 3 (p. 4); Treasury WP 2016-02, p. 18",
    },
    passMark: "Central value within the published models' range",
    pass: tax.central >= 0.6 && tax.central <= 1.2,
    note: "The models are CGE models in which employment changes by −0.1% to +0.4%; the tool's closure fixes employment, so it sits in the lower part of their range. It applies the rate to all capital in the industries reached, unincorporated businesses included.",
  });
  return rows;
}

const pct = (x: number) => `${x >= 0 ? "+" : "−"}${Math.abs(x).toFixed(3)}%`;

export function validationMarkdown(rows: readonly ValidationRow[], params: ParameterFile, draws = 2000): string {
  const out: string[] = [];
  out.push("# Policy costing: validation against published models");
  out.push("");
  out.push(
    `Generated by \`npx tsx scripts/validate-costing.ts\` (plan P6, §8). Parameters: vintage ${params.vintage ?? "unknown"}, sources fingerprint ${sourcesFingerprint(params)}. Tool ranges are the 10th and 90th percentiles of ${draws.toLocaleString("en-AU")} Monte Carlo draws (seed 1). Test T-VAL-01 checks the pass marks and that this note is current.`,
  );
  out.push("");
  out.push("Long-run change in the level of real GDP, per cent.");
  out.push("");
  out.push("| Case | What the tool was given | Tool, central (10–90%) | Published | Pass mark | Result |");
  out.push("|---|---|---|---|---|---|");
  for (const r of rows) {
    out.push(`| ${r.id}: ${r.label} | ${r.input} | ${pct(r.tool.central)} (${pct(r.tool.p10)} to ${pct(r.tool.p90)}) | ${r.published.text}; ${r.published.source} | ${r.passMark} | ${r.pass ? "Pass" : "Outside"}: ${(r.tool.central / ((r.published.low + r.published.high) / 2)).toFixed(2)} × |`);
  }
  out.push("");
  out.push("## Notes");
  out.push("");
  for (const r of rows) out.push(`- **${r.id}.** ${r.note}`);
  out.push(
    "- **Not reproduced: the PC's 2025 company tax package** (a 20% rate below $1 billion of revenue, 28% above, and a 5% net cash-flow tax). The brief has one company tax rate and no cash-flow tax, so the package cannot be entered; its modelled GDP gain (0.4% to 0.7% in the PC's two models) is context only.",
  );
  out.push("- Layer B's back-test against every PC National productivity simulation is in [`costing_calibration.md`](costing_calibration.md).");
  out.push("");
  out.push(`<!-- sources-fingerprint: ${sourcesFingerprint(params)} -->`);
  return `${out.join("\n")}\n`;
}
