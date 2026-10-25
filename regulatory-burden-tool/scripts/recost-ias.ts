// Writes docs/rbm_recostings.md at the repository root: the RBM engine against published Impact Analyses (plan P6c,
// §8). Test T-RCT-01 checks the committed note is current. Run with: npm run recost:ias
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { loadProposalFile, type Proposal } from "../src/engine/index";
import { recostMarkdown, RECOSTINGS, runRecostings } from "../src/engine/recostings";
import { parseBrief } from "../src/productivity/index";

const tool = join(import.meta.dirname, "..");

export function loadRecostingProposals(): Record<string, Proposal> {
  return Object.fromEntries(
    RECOSTINGS.map((r) => {
      const json = JSON.parse(readFileSync(join(tool, "examples", r.file), "utf8"));
      return [r.file, r.kind === "brief" ? parseBrief(json).burden! : loadProposalFile(json).proposal];
    }),
  );
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const rows = runRecostings(loadRecostingProposals());
  const out = join(tool, "..", "docs", "rbm_recostings.md");
  writeFileSync(out, recostMarkdown(rows), "utf8");
  console.log(`Wrote ${out}: ${rows.filter((r) => r.match).length} of ${rows.length} options match; the rest are explained`);
}
