// The worked examples of plan §8 (P6): five real policies costed end to end. `scripts/worked-examples.ts` writes the
// results section of docs/worked_examples.md and the frozen outputs that test T-WEX-01 checks. The briefs are in
// examples/ (written by scripts/make-worked-examples.ts from the published figures each cites).
import { computeProposal } from "../engine/index";
import { parseBrief } from "./brief";
import type { CostingContext } from "./context";
import { runCosting } from "./costing";

export interface WorkedCase {
  id: string;
  file: string;
  /** What the published source says, for the comparison column. */
  published: string;
  /** Runs of the same brief with one input changed. */
  variants?: { id: string; label: string; edit: (brief: Record<string, unknown>) => Record<string, unknown> }[];
}

const delayDays = (days: number) => (b: Record<string, unknown>) => {
  const levers = b.levers as { capital: Record<string, unknown> };
  return { ...b, levers: { ...levers, capital: { ...levers.capital, investmentApprovalDelayChangeMonths: Math.round(((-days * 12) / 365) * 1e4) / 1e4 } } };
};

export const WORKED: WorkedCase[] = [
  {
    id: "noncompete-ban",
    file: "noncompete-ban.brief.json",
    published: "GDP +$5.1 billion a year (the PC's 2024 modelling, cited in the IA); one-off familiarisation cost $46.4 million (Option 2) and $16.3 million (Option 3)",
  },
  {
    id: "worked-amr",
    file: "worked-amr.brief.json",
    published: "\"$2.4 billion over ten years\" (Australian Government, as reported; method not retrieved); multiple licences cost $6.4 million a year (PC 2015)",
  },
  {
    id: "worked-climate-disclosure",
    file: "worked-climate-disclosure.brief.json",
    published: "RBE +$1,150.2 million a year (Option 1b; Option 1 $1,386.7m, Option 1a $1,207.3m); benefits not quantified",
  },
  {
    id: "worked-epbc-approvals",
    file: "worked-epbc-approvals.brief.json",
    published: "Delay costs −$445 million a year at 20 days (−$3,045m at 141 days, −$6,914m at 288 days)",
    variants: [
      { id: "medium", label: "141 days (DCCEEW's medium scenario)", edit: delayDays(141) },
      { id: "high", label: "288 days (DCCEEW's high scenario)", edit: delayDays(288) },
    ],
  },
  {
    id: "worked-vic-payroll-threshold",
    file: "worked-vic-payroll-threshold.brief.json",
    published: "Revenue +$20.3m (2024-25), −$43.6m (2025-26), −$38.7m (2026-27), net of the phase-out; about 6,000 businesses stop paying, 26,000 benefit",
  },
];

export interface WorkedOutput {
  id: string;
  variant: string | null;
  title: string;
  gate: string;
  gateReasons: string[];
  /** Long-run change in real GDP: per cent (central, 10th, 50th, 90th percentiles) and $ million a year. */
  gdpPct: number;
  p10: number;
  p50: number;
  p90: number;
  gdpDollars: number;
  /** Present value over the duration at 7%, $ million. */
  npv7: number;
  welfareDollars: number;
  channels: { channel: string; status: string; grade: string | null; gdpPct: number }[];
  /** Average annual RBE of each option of the burden proposal, $ a year. */
  rbe: { option: string; dollars: number }[];
  /** C5's screen: businesses, employment and cost against wages near each threshold. */
  screen: { label: string; value: number; unit: string }[];
}

/** Six significant figures, so frozen outputs do not record floating-point noise. */
export const sig = (x: number) => (x === 0 ? 0 : Number(x.toPrecision(6)));

export function runWorked(files: Record<string, unknown>, ctx: CostingContext, draws = 2000): WorkedOutput[] {
  const out: WorkedOutput[] = [];
  for (const w of WORKED) {
    const raw = files[w.file] as Record<string, unknown> | undefined;
    if (!raw) throw new Error(`Missing worked example ${w.file}`);
    for (const v of [null, ...(w.variants ?? [])]) {
      const brief = parseBrief(v ? v.edit(raw) : raw);
      const c = runCosting(brief, ctx, { draws, seed: 1 });
      const r = c.result;
      const rbe = brief.burden
        ? computeProposal(brief.burden).options.filter((o) => !o.isStatusQuo).map((o) => ({ option: o.optionId, dollars: sig(Number(o.rbe.total.toString())) }))
        : [];
      out.push({
        id: w.id,
        variant: v?.id ?? null,
        title: v ? `${brief.meta.title}: ${v.label}` : brief.meta.title,
        gate: c.gate.status,
        gateReasons: c.gate.reasons,
        gdpPct: sig(r.gdpPct),
        p10: sig(c.ranges.gdpPct.p10),
        p50: sig(c.ranges.gdpPct.p50),
        p90: sig(c.ranges.gdpPct.p90),
        gdpDollars: sig(r.gdpDollars),
        npv7: sig(r.npv[0]!.dollars),
        welfareDollars: sig(r.welfareDollars),
        channels: r.channels.map((ch) => ({ channel: ch.channel, status: ch.status, grade: ch.grade, gdpPct: sig(ch.gdpPct) })),
        rbe,
        screen: r.channels.filter((ch) => ch.channel === "C5").flatMap((ch) => ch.other.map((o) => ({ label: o.label, value: sig(o.value), unit: o.unit }))),
      });
    }
  }
  return out;
}

const pct = (x: number) => (x === 0 ? "0" : `${x > 0 ? "+" : "−"}${Math.abs(x) >= 0.01 ? Math.abs(x).toFixed(3) : Math.abs(x).toPrecision(2)}%`);
const money = (x: number) => `${x < 0 ? "−" : x > 0 ? "+" : ""}$${Math.abs(x).toLocaleString("en-AU", { maximumFractionDigits: 0 })}m`;

/** The generated results section of docs/worked_examples.md. */
export function workedResults(outputs: readonly WorkedOutput[], fingerprint: string, vintage: string, draws = 2000): string {
  const rows: string[] = [];
  rows.push(
    `Generated by \`npm run worked:examples\`. Parameters: vintage ${vintage}, sources fingerprint ${fingerprint}; ${draws.toLocaleString("en-AU")} Monte Carlo draws, seed 1. Long-run change in the level of real GDP; dollars a year in ${"2025-26"} prices.`,
    "",
    "| Example | Gate | GDP, central | 10–90% range | $ a year | PV at 7% (10 years) | RBE a year (first option) | Published |",
    "|---|---|---:|---|---:|---:|---:|---|",
  );
  for (const o of outputs) {
    const w = WORKED.find((x) => x.id === o.id)!;
    const shown = o.gate !== "hidden";
    rows.push(
      `| ${o.title} | ${o.gate} | ${shown ? pct(o.gdpPct) : "hidden"} | ${shown ? `${pct(o.p10)} to ${pct(o.p90)}` : ""} | ${shown ? money(o.gdpDollars) : ""} | ${shown ? money(o.npv7) : ""} | ${o.rbe.length ? money(o.rbe[0]!.dollars / 1e6) : "–"} | ${o.variant ? "" : w.published} |`,
    );
  }
  rows.push("", "**By channel** (long-run GDP, per cent; grade):", "");
  for (const o of outputs.filter((x) => !x.variant)) {
    rows.push(`- ${o.title}: ${o.channels.map((c) => `${c.channel} ${c.status === "costed" ? pct(c.gdpPct) : "not quantified"}${c.grade ? ` (${c.grade})` : ""}`).join("; ")}.`);
  }
  const withRbe = outputs.filter((o) => !o.variant && o.rbe.length);
  rows.push("", "**RBE by option** (average a year over ten years):", "");
  for (const o of withRbe) rows.push(`- ${o.title}: ${o.rbe.map((r) => `${r.option} ${money(r.dollars / 1e6)}`).join("; ")}.`);
  const screened = outputs.filter((o) => !o.variant && o.screen.length);
  rows.push("", "**C5 screens:**", "");
  for (const o of screened) {
    rows.push(`- ${o.title}:`);
    for (const s of o.screen) rows.push(`  - ${s.label}: ${s.value.toLocaleString("en-AU", { maximumFractionDigits: 2 })} ${s.unit}`);
  }
  return rows.join("\n");
}

export const RESULTS_START = "<!-- worked-results:start -->";
export const RESULTS_END = "<!-- worked-results:end -->";

/** The note with its results section replaced. */
export function withResults(note: string, results: string): string {
  const a = note.indexOf(RESULTS_START);
  const b = note.indexOf(RESULTS_END);
  if (a < 0 || b < a) throw new Error("docs/worked_examples.md has no results markers");
  return `${note.slice(0, a + RESULTS_START.length)}\n${results}\n${note.slice(b)}`;
}
