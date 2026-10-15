// Command-line report: prints the RBE table and supporting results for a proposal file.
//   npm run rbe -- examples/illustrative-reform.json [--precision 2|3|dollars] [--json] [--tidy out.csv]
import { readFileSync, writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import {
  computeProposal,
  formatMoney,
  formatShare,
  loadProposalFile,
  rbeTableMarkdown,
  tidyCsv,
  tidyDictionaryCsv,
  toTidyRows,
  verdictText,
  type Precision,
  type ProposalResult,
} from "../engine/index";

export interface CliOptions {
  file: string;
  precision: Precision;
  json: boolean;
  tidy?: string;
}

export function parseArgs(argv: readonly string[]): CliOptions {
  const opts: CliOptions = { file: "", precision: 1, json: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--json") opts.json = true;
    else if (a === "--precision") {
      const v = argv[++i];
      if (v === "dollars") opts.precision = "dollars";
      else if (v === "1" || v === "2" || v === "3") opts.precision = Number(v) as 1 | 2 | 3;
      else throw new Error(`--precision must be 1, 2, 3 or dollars (got "${v}")`);
    } else if (a === "--tidy") {
      const v = argv[++i];
      if (!v) throw new Error("--tidy needs an output file path");
      opts.tidy = v;
    } else if (a && !a.startsWith("--")) opts.file = a;
    else throw new Error(`Unknown option "${a}"`);
  }
  if (!opts.file) throw new Error("Usage: npm run rbe -- <proposal.json> [--precision 1|2|3|dollars] [--json] [--tidy out.csv]");
  return opts;
}

/** Money in running text: "$4.4m" / "($12.7m)" in million mode, or exact dollars. */
function money(value: string, precision: Precision): string {
  const f = formatMoney(value, precision);
  return precision === "dollars" || f === "$0" ? f : f.replace(/(\d)(\)?)$/, "$1m$2");
}

/** Renders the human-readable report. Pure: no I/O. */
export function renderReport(result: ProposalResult, precision: Precision = 1): string {
  const out: string[] = [];
  out.push(`# ${result.title}`);
  out.push(
    `Duration: ${result.durationYears} years · Baseline: ${result.baseline === "statusQuo" ? "current settings" : "no instrument (sunsetting remake)"} · Parameters: ${result.parameterVintage} · Engine ${result.engineVersion}`,
  );
  out.push("Unofficial aid. Users remain responsible for their estimates; contact OIA for formal advice.");
  for (const o of result.options) {
    out.push("", `## Option: ${o.optionName}`, "", rbeTableMarkdown(o.rbe, precision), "");
    out.push(`**${verdictText(o.verdict)}.**`);
    out.push(`Gross increases ${money(o.gross.increases, precision)}; gross reductions ${money(o.gross.reductions, precision)} (average annual).`);
    out.push(`Total over the analysis period: ${money(o.tenYearTotal, precision)}${o.iaThreshold1.likelyMet ? " (likely meets IA threshold 1 of $20m over 10 years; confirm with OIA)" : ""}.`);
    const altLabel = o.alternativeBaseline.baseline === "statusQuo" ? "current settings" : "no instrument";
    out.push(`Against ${altLabel} instead (context): total change ${money(o.alternativeBaseline.rbe.total, precision)} a year.`);
    if (!o.isStatusQuo && o.context.currentAnnual !== "0") {
      out.push(
        `Context, not RBE: current regime ${money(o.context.currentAnnual, precision)} a year; reformed regime ${money(o.context.reformedAnnual, precision)} a year; ${formatShare(o.context.shareRemoved)} of current burden removed (${formatShare(o.context.shareRemovedNetOfTransition)} net of transition costs).`,
      );
    }
    if (o.perEntity.length) {
      out.push("", "Change per affected entity per year:");
      for (const p of o.perEntity) {
        out.push(`- ${p.label}: ${formatMoney(p.changePerEntity, "dollars")}${p.cliffFlag ? " (cliff: no relief above the threshold)" : ""}`);
      }
    }
    if (o.excluded.length) {
      out.push("", "Excluded from the RBE (note qualitatively in the Impact Analysis if significant):");
      for (const e of o.excluded) out.push(`- ${e.obligationName} (${e.side}): ${e.label}, ${formatMoney(e.annualAmount, "dollars")} a year. ${e.ref}`);
    }
  }
  if (result.warnings.length) {
    out.push("", "## Warnings");
    for (const w of result.warnings) out.push(`- [${w.code}${w.severity === "info" ? ", info" : ""}] ${w.message} (${w.ref})`);
  }
  out.push("", "Regulation's forgone benefits (e.g. safety or consumer protection) are outside the RBM and belong in the Impact Analysis.");
  return out.join("\n");
}

export function runCli(argv: readonly string[]): { stdout: string; exitCode: number } {
  try {
    const opts = parseArgs(argv);
    const file = loadProposalFile(JSON.parse(readFileSync(opts.file, "utf8")));
    const result = computeProposal(file.proposal);
    if (opts.tidy) {
      writeFileSync(opts.tidy, tidyCsv(toTidyRows(result)));
      writeFileSync(opts.tidy.replace(/\.csv$/i, "") + ".dictionary.csv", tidyDictionaryCsv());
    }
    return { stdout: opts.json ? JSON.stringify(result, null, 2) : renderReport(result, opts.precision), exitCode: 0 };
  } catch (e) {
    return { stdout: e instanceof Error ? e.message : String(e), exitCode: 1 };
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  const { stdout, exitCode } = runCli(process.argv.slice(2));
  (exitCode === 0 ? console.log : console.error)(stdout);
  process.exitCode = exitCode;
}
