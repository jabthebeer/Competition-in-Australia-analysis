// The RBM engine against published Impact Analyses (plan §8, P6c; burden tool Phase 5): each IA's regulatory burden
// estimate is rebuilt from its stated inputs and compared with its published figures, option by option. A difference
// within the published figure's rounding is a match; any other difference carries its explanation. Pure: the
// proposals are passed in. `scripts/recost-ias.ts` writes docs/rbm_recostings.md; test T-RCT-01 checks it.
import { computeProposal } from "./compute";
import type { Proposal } from "./schema";

export interface PublishedFigure {
  optionId: string;
  /** "averageAnnual": the RBE table's average a year over ten years; "tenYear": a one-off or ten-year total. */
  basis: "averageAnnual" | "tenYear";
  /** $ million, as published; a sector the IA does not report is left out. */
  business?: number;
  individual?: number;
  total: number;
  /** Rounding of the published figures, $ million (0.1 for one decimal place). */
  precision: number;
  /** Largest difference that is still rounding, $ million, when the figure adds parts rounded separately; default 1.5 × precision. */
  tolerance?: number;
  where: string;
}

export interface Recosting {
  id: string;
  title: string;
  agency: string;
  published: string;
  url: string;
  /** The file in examples/ and whether it is a policy brief (whose burden is used) or a proposal file. */
  file: string;
  kind: "brief" | "proposal";
  figures: PublishedFigure[];
  /** Why an option differs, by option id. */
  explanations: Record<string, string>;
  notes: string[];
}

export const RECOSTINGS: Recosting[] = [
  {
    id: "climate-disclosure",
    title: "Mandatory climate-related financial disclosure",
    agency: "Treasury",
    published: "Policy Impact Analysis, September 2023",
    url: "https://treasury.gov.au/sites/default/files/2024-01/c2024-466491-pia.pdf",
    file: "worked-climate-disclosure.brief.json",
    kind: "brief",
    figures: [
      { optionId: "option-1b", basis: "averageAnnual", business: 1150.2, total: 1150.2, precision: 0.01, tolerance: 0.05, where: "Table 14 (p. 29): $1,400.19m less the status quo's $249.99m" },
      { optionId: "option-1", basis: "averageAnnual", business: 1386.7, total: 1386.7, precision: 0.01, tolerance: 0.05, where: "Table 14 (p. 29)" },
      { optionId: "option-1a", basis: "averageAnnual", business: 1207.31, total: 1207.31, precision: 0.01, tolerance: 0.05, where: "Table 14 (p. 29)" },
    ],
    explanations: {},
    notes: [
      "Treasury rounds each group's cost to $0.01m before adding four groups and subtracting the status quo, so its totals carry up to about $0.03m of rounding; the rebuild is matched within $0.05m.",
      "Group 3 under Options 1a and 1b has 228 entities, as Table 12 computes; the PIA's text says 278.",
      "Table 11 prints Group 2's transitional and ongoing costs as $755.89m and $412.99m, but its total ($618.03m) uses Table 9's $789.34m and $539.09m; the rebuild follows Table 9.",
    ],
  },
  {
    id: "noncompete",
    title: "Non-compete clauses and other worker restraints",
    agency: "Treasury",
    published: "Impact Analysis, published by the OIA on 21 September 2026",
    url: "https://oia.pmc.gov.au/sites/default/files/posts/2026/09/Impact%20Analysis.pdf",
    file: "noncompete-ban.brief.json",
    kind: "brief",
    figures: [
      { optionId: "option-2-partial-ban", basis: "tenYear", business: 46.4, total: 46.4, precision: 0.1, where: "Table 4 (p. 51): one-off familiarisation cost" },
      { optionId: "option-3-full-ban", basis: "tenYear", business: 16.3, total: 16.3, precision: 0.1, where: "Table 4 (p. 51): one-off familiarisation cost" },
    ],
    explanations: {
      "option-2-partial-ban":
        "Option 2's familiarisation takes 90 minutes against Option 3's 30 (Table 5) with the same people, rates and businesses, so it costs three times as much. The IA's small-business figures keep that ratio ($38.2m against $12.7m), but its medium- and large-business figures do not ($7.5m and $0.7m against $3.3m and $0.3m; three times would be $9.9m and $0.9m). The rebuild from the stated inputs gives three times Option 3's cost, which reproduces the IA. The IA's Option 2 medium and large figures look inconsistent with its own inputs.",
    },
    notes: [
      "The IA does not state the 1.75 on-cost multiplier, but its small-business figures need it: 925,758 × 20.2% × 1.5 hours × $77.88 is $21.8m, and × 1.75 is $38.2m.",
      "The IA's 73,403 medium and large businesses are split by CABEE's June 2024 counts; with that split the rebuild reproduces Option 3's $3.3m and $0.3m.",
    ],
  },
  {
    id: "discretionary-trusts",
    title: "Minimum tax on discretionary trusts",
    agency: "Treasury",
    published: "Impact Analysis, published by the OIA on 21 October 2026",
    url: "https://oia.pmc.gov.au/sites/default/files/posts/2026/10/Detailed%20IA.pdf",
    file: "ia-discretionary-trusts.json",
    kind: "proposal",
    figures: [
      { optionId: "option-2", basis: "averageAnnual", business: 81.0, individual: 60.5, total: 141.5, precision: 0.1, where: "Appendix A, Table 2 (p. 30)" },
      { optionId: "option-3", basis: "averageAnnual", business: 87.8, individual: 69.4, total: 157.2, precision: 0.1, where: "Appendix A, Table 4 (p. 33)" },
    ],
    explanations: {},
    notes: [
      "The IA's range for Option 2 links the restructure and election shares (10% restructuring goes with 90% electing); the RBM engine draws each range separately, so its range is wider. The central values are the same.",
      "Non-business trusts' time is costed at the work rate ($91.54), as the IA does, because their advisers do the work; individual beneficiaries' at the non-work rate ($41).",
    ],
  },
  {
    id: "wholly-owned-relief",
    title: "Financial reporting relief for wholly-owned companies",
    agency: "ASIC",
    published: "Dashboard Impact Analysis, published by the OIA on 14 October 2026",
    url: "https://oia.pmc.gov.au/sites/default/files/posts/2026/10/IA%20Dashboard%20%26%20Statement%20of%20sufficiency.pdf",
    file: "ia-wholly-owned-relief.json",
    kind: "proposal",
    figures: [{ optionId: "class-relief", basis: "tenYear", business: -61.65, total: -61.65, precision: 0.01, where: "Summary table and Regulatory burden (pp. 2–3): a one-off saving of 12,330 × $5,000" }],
    explanations: {
      "class-relief":
        "ASIC counts each company's $3,487 application fee (Corporations (Fees) Act 2001) as a saving. Fees paid to government are outside the RBE (RBM pp. 2, 4), so the rebuild keeps only the adviser fees ($1,513 a company): a saving of $18.66m over ten years. The excluded fees are the other $42.99m (12,330 × $3,487).",
    },
    notes: [
      "ASIC measures the change against no instrument, under which each company would apply for individual relief because the Corporations Act's reporting duty stays. The rebuild enters those applications as the current regime; the engine's no-instrument baseline would drop them.",
    ],
  },
];

export interface RecostRow {
  recosting: string;
  optionId: string;
  optionName: string;
  basis: PublishedFigure["basis"];
  /** $ million, on the published basis. */
  tool: { business: number; individual: number; total: number };
  published: PublishedFigure;
  match: boolean;
  explanation?: string;
}

const m = (x: string) => Number(x) / 1e6;

export function runRecostings(proposals: Record<string, Proposal>): RecostRow[] {
  const rows: RecostRow[] = [];
  for (const r of RECOSTINGS) {
    const proposal = proposals[r.file];
    if (!proposal) throw new Error(`No proposal for ${r.file}`);
    const result = computeProposal(proposal);
    for (const f of r.figures) {
      const o = result.options.find((x) => x.optionId === f.optionId);
      if (!o) throw new Error(`${r.id}: no option ${f.optionId}`);
      // The RBE row is the average a year; a ten-year figure is that times the duration.
      const scale = f.basis === "tenYear" ? result.durationYears : 1;
      const tool = { business: m(o.rbe.business) * scale, individual: m(o.rbe.individual) * scale, total: m(o.rbe.total) * scale };
      // Within the published rounding, plus the rounding of the published parts it is the sum of.
      const tol = f.tolerance ?? f.precision * 1.5;
      const close = (a: number, b: number | undefined) => b === undefined || Math.abs(a - b) <= tol;
      const match = close(tool.total, f.total) && close(tool.business, f.business) && close(tool.individual, f.individual);
      rows.push({ recosting: r.id, optionId: f.optionId, optionName: o.optionName, basis: f.basis, tool, published: f, match, ...(match ? {} : { explanation: r.explanations[f.optionId] }) });
    }
  }
  return rows;
}

const money = (x: number, dp: number) => (x < 0 ? `(${Math.abs(x).toFixed(dp)})` : x.toFixed(dp));

export function recostMarkdown(rows: readonly RecostRow[]): string {
  const out: string[] = [];
  out.push("# RBM re-costings of published Impact Analyses");
  out.push("");
  out.push(
    "Generated by `npm run recost:ias` (plan P6, §8; burden tool Phase 5). Each IA's regulatory burden estimate is rebuilt in the RBM engine from the inputs the IA states, and compared with its published figures. $ million; savings in brackets. A difference within the published rounding is a match; every other difference is explained. The proposals are in `regulatory-burden-tool/examples/`. Test T-RCT-01 checks the matches and that this note is current.",
  );
  out.push("");
  out.push("| Impact Analysis | Option | Basis | Published: business; individuals; total | RBM engine: business; individuals; total | Result |");
  out.push("|---|---|---|---|---|---|");
  for (const row of rows) {
    const r = RECOSTINGS.find((x) => x.id === row.recosting)!;
    const p = row.published;
    const dp = p.precision < 0.1 ? 2 : 1;
    const pub = [p.business, p.individual, p.total].map((x) => (x === undefined ? "–" : money(x, dp))).join("; ");
    const tool = [row.tool.business, row.tool.individual, row.tool.total].map((x) => money(x, dp)).join("; ");
    out.push(
      `| ${r.title} (${r.agency}, ${r.published}) | ${row.optionName} | ${p.basis === "tenYear" ? "Ten-year total (one-off)" : "Average a year"}; ${p.where} | ${pub} | ${tool} | ${row.match ? "Match" : "Differs: explained below"} |`,
    );
  }
  out.push("");
  out.push("## Differences");
  out.push("");
  for (const row of rows.filter((x) => !x.match)) {
    const r = RECOSTINGS.find((x) => x.id === row.recosting)!;
    out.push(`- **${r.title}, ${row.optionName}.** ${row.explanation ?? "Not explained."}`);
  }
  out.push("");
  out.push("## Notes");
  out.push("");
  for (const r of RECOSTINGS) for (const n of r.notes) out.push(`- **${r.title}.** ${n}`);
  out.push("");
  out.push("## Sources");
  out.push("");
  for (const r of RECOSTINGS) out.push(`- ${r.agency}, *${r.title}*, ${r.published}: <${r.url}>`);
  return `${out.join("\n")}\n`;
}
