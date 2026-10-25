// Command-line report: the productivity and competition costing of a policy brief (plan §6).
//   npm run pce -- examples/noncompete-ban.brief.json [--draws 2000] [--seed 1] [--show-ungated] [--json] [--params file]
// The parameters are the bundled data/processed/costing/parameters.json unless --params names another file.
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { buildContext, parseBrief, runCosting, type Costing, type Percentiles, type PolicyBrief } from "../productivity/index";

export interface PceOptions {
  file: string;
  params: string;
  draws?: number;
  seed?: number;
  showUngated: boolean;
  json: boolean;
}

const DEFAULT_PARAMS = fileURLToPath(new URL("../../../data/processed/costing/parameters.json", import.meta.url));
const USAGE = "Usage: npm run pce -- <brief.json> [--draws N] [--seed N] [--show-ungated] [--json] [--params parameters.json]";

function integer(flag: string, v: string | undefined): number {
  if (!v || !/^\d+$/.test(v)) throw new Error(`${flag} needs a whole number (got "${v ?? ""}")`);
  return Number(v);
}

export function parseArgs(argv: readonly string[]): PceOptions {
  const opts: PceOptions = { file: "", params: DEFAULT_PARAMS, showUngated: false, json: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--json") opts.json = true;
    else if (a === "--show-ungated") opts.showUngated = true;
    else if (a === "--draws") opts.draws = integer(a, argv[++i]);
    else if (a === "--seed") opts.seed = integer(a, argv[++i]);
    else if (a === "--params") {
      const v = argv[++i];
      if (!v) throw new Error("--params needs a file path");
      opts.params = v;
    } else if (a && !a.startsWith("--")) opts.file = a;
    else throw new Error(`Unknown option "${a}"`);
  }
  if (!opts.file) throw new Error(USAGE);
  return opts;
}

/** A signed percentage: three decimals, or two significant figures when smaller than 0.01%. */
const pct = (x: number) => `${x >= 0 ? "+" : "−"}${x === 0 || Math.abs(x) >= 0.01 ? Math.abs(x).toFixed(3) : Math.abs(x).toPrecision(2)}%`;
const rate = (r: number) => `${Number((r * 100).toFixed(4))}%`;
const num = (x: number) => (Math.abs(x) >= 1000 ? x.toLocaleString("en-AU", { maximumFractionDigits: 0 }) : String(Number(x.toPrecision(4))));
const money = (x: number) => `${x < 0 ? "−" : ""}$${Math.abs(x).toLocaleString("en-AU", { maximumFractionDigits: Math.abs(x) < 10 ? 1 : 0 })}m`;
const range = (p: Percentiles, f: (x: number) => string) => `${f(p.p10)} to ${f(p.p90)}`;
const GATE_TITLE = { full: "shown in full", indicative: "indicative", hidden: "GDP hidden" } as const;

/** Renders the human-readable report. Pure: no I/O. */
export function renderReport(brief: PolicyBrief, c: Costing, parameterVintage: string | null): string {
  const { result: r, ranges, gate } = c;
  const out: string[] = [];
  out.push(`# ${brief.meta.title}`);
  out.push(
    `Brief ${brief.id} · Parameters ${parameterVintage ?? "unknown"} · GDP ${r.gdpYear}: ${money(r.gdpLevel)} · ${brief.meta.durationYears} years from ${brief.meta.startYear}-${String((brief.meta.startYear + 1) % 100).padStart(2, "0")}, phase-in ${brief.meta.phaseInYears} years · ${ranges.draws.toLocaleString("en-AU")} draws, seed ${ranges.seed}`,
  );
  out.push("Unofficial, indicative analysis: not an Australian Government costing. Results are changes in the level of real GDP against the baseline.");
  out.push("", `## Evidence gate: ${GATE_TITLE[gate.status]}`);
  for (const reason of gate.reasons) out.push(`- ${reason}`);
  if (gate.watermark) out.push("- DRAFT: shown although the gate would hide it, or resting on unconfirmed estimates.");

  if (gate.showGdp) {
    out.push("", "## Long-run effect on real GDP", "", "| Channel | Status | Grade | GDP | $ a year | 10–90% range |", "|---|---|---|---:|---:|---|");
    for (const ch of r.channels) {
      const p = ranges.byChannel.find((b) => b.channel === ch.channel)?.gdpPct;
      const costed = ch.status === "costed";
      out.push(`| ${ch.channel} ${ch.name} | ${costed ? "costed" : "not quantified"} | ${ch.grade ?? "–"} | ${costed ? pct(ch.gdpPct) : "–"} | ${costed ? money(ch.gdpDollars) : "–"} | ${costed && p ? range(p, pct) : ""} |`);
    }
    out.push(`| **Total** | | | **${pct(r.gdpPct)}** | **${money(r.gdpDollars)}** | ${range(ranges.gdpPct, pct)} |`);
    if (r.gdpPct > ranges.gdpPct.p90 || r.gdpPct < ranges.gdpPct.p10) {
      out.push("", `The central estimate uses each parameter's default; some defaults sit at the end of their range, so it lies outside the 10–90% range. The median of the simulations is ${pct(ranges.gdpPct.p50)}.`);
    }
    if (r.realisationFactor !== 1) out.push("", `Realisation factor ${r.realisationFactor}: every productivity effect is scaled by it.`);
    const t2 = gate.threshold2;
    out.push(
      "",
      `IA threshold 2 ($${gate.thresholdDollars}m a year): central ${money(t2.central)} ${t2.centralMeets ? "meets it" : "does not meet it"}; the low end of the range, ${money(t2.low)}, ${t2.lowMeets ? "meets it" : "does not"}.`,
    );
    const at = (year: number) => r.path[year - 1]!;
    out.push("", "## Time path", "", "| | Year 1 | Year 5 | Year 10 | Long run |", "|---|---:|---:|---:|---:|");
    out.push(`| GDP | ${[1, 5, 10].map((y) => pct(at(y).gdpPct)).join(" | ")} | ${pct(r.gdpPct)} |`);
    out.push(`| $ a year | ${[1, 5, 10].map((y) => money(at(y).gdpDollars)).join(" | ")} | ${money(r.gdpDollars)} |`);
    out.push(`| 10–90% | ${ranges.byYear.map((y) => range(y.gdpPct, pct)).join(" | ")} | ${range(ranges.gdpPct, pct)} |`);
    const [main, ...others] = r.npv;
    out.push(
      "",
      `Present value over ${brief.meta.durationYears} years: ${money(main!.dollars)} at ${rate(main!.rate)} (10–90%: ${range(ranges.npv, money)})${others.length ? `; ${others.map((n) => `${money(n.dollars)} at ${rate(n.rate)}`).join(", ")}` : ""}.`,
    );
    if (c.tornado.length) {
      out.push("", "## Sensitivity (long-run GDP, $ a year, one parameter at a time)", "", "| Parameter | Low → high | At low | At high |", "|---|---|---:|---:|");
      for (const b of c.tornado) out.push(`| ${b.label} (${b.key}) | ${b.low} → ${b.high} | ${money(b.gdpDollarsAtLow)} | ${money(b.gdpDollarsAtHigh)} |`);
    }
  } else {
    out.push("", "Economy-wide figures are hidden by the evidence gate. Set analysis.showUngatedEconomyWide in the brief, or pass --show-ungated, to show them with a watermark.");
  }
  if (r.welfareDollars !== 0) out.push("", `Efficiency cost of funding (C11), beside GDP rather than in it: ${money(r.welfareDollars / 1e6)} a year.`);

  out.push("", "## Direct effects by channel");
  for (const ch of r.channels) {
    out.push("", `### ${ch.channel} ${ch.name}${ch.grade ? ` (grade ${ch.grade})` : ""}`);
    for (const e of ch.effects) {
      out.push(`- ${e.anzsic}: ${e.measure} ${e.value >= 0 ? "+" : "−"}${Math.abs(e.value).toPrecision(3)} (${e.unit})`);
      for (const f of e.chain) out.push(`  - ${f.label}: ${num(f.value)} ${f.unit}${f.evidence ? ` [${f.evidence}]` : ""}`);
    }
    for (const o of ch.other) out.push(`- ${o.label}: ${num(o.value)} (${o.unit})`);
    for (const reason of ch.reasons) out.push(`- Not costed: ${reason}`);
    for (const note of ch.notes) out.push(`- Note: ${note}`);
  }
  if (c.warnings.length) {
    out.push("", "## Warnings");
    for (const w of c.warnings) out.push(`- [${w.code}] ${w.message} (${w.path})`);
  }
  out.push("", "## Not modelled");
  for (const n of r.notModelled) out.push(`- ${n}`);
  return out.join("\n");
}

export function runCli(argv: readonly string[]): { stdout: string; exitCode: number } {
  try {
    const opts = parseArgs(argv);
    const params = JSON.parse(readFileSync(opts.params, "utf8"));
    const raw = JSON.parse(readFileSync(opts.file, "utf8"));
    const brief = parseBrief(opts.showUngated ? { ...raw, analysis: { ...raw.analysis, showUngatedEconomyWide: true } } : raw);
    const costing = runCosting(brief, buildContext(params), { draws: opts.draws, seed: opts.seed });
    return { stdout: opts.json ? JSON.stringify(costing, null, 2) : renderReport(brief, costing, params.vintage ?? null), exitCode: 0 };
  } catch (e) {
    return { stdout: e instanceof Error ? e.message : String(e), exitCode: 1 };
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  const { stdout, exitCode } = runCli(process.argv.slice(2));
  (exitCode === 0 ? console.log : console.error)(stdout);
  process.exitCode = exitCode;
}
