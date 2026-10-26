// P6c (plan §8; burden tool Phase 5): the RBM engine against published Impact Analyses.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { recostMarkdown, RECOSTINGS, runRecostings } from "../../src/engine/recostings";
import { loadRecostingProposals } from "../../scripts/recost-ias";

const repo = join(import.meta.dirname, "..", "..", "..");

describe("re-costings of published Impact Analyses", () => {
  const rows = runRecostings(loadRecostingProposals());

  it("T-RCT-01 four IAs rebuilt from their stated inputs: each option matches its published figure or its difference is explained; the note is current", () => {
    expect(RECOSTINGS).toHaveLength(4);
    const byOption = new Map(rows.map((r) => [`${r.recosting}/${r.optionId}`, r]));
    for (const key of ["climate-disclosure/option-1b", "climate-disclosure/option-1", "climate-disclosure/option-1a", "noncompete/option-3-full-ban", "discretionary-trusts/option-2", "discretionary-trusts/option-3"]) {
      expect(byOption.get(key)!.match, key).toBe(true);
    }
    // The two differences, and why: an inconsistency inside the IA, and a fee the RBM leaves out.
    const nc = byOption.get("noncompete/option-2-partial-ban")!;
    expect(nc.match).toBe(false);
    expect(nc.tool.total / byOption.get("noncompete/option-3-full-ban")!.tool.total).toBeCloseTo(3, 9);
    const asic = byOption.get("wholly-owned-relief/class-relief")!;
    expect(asic.match).toBe(false);
    expect(asic.tool.total).toBeCloseTo(-(12330 * 1513) / 1e6, 6);
    expect(asic.published.total - asic.tool.total).toBeCloseTo(-(12330 * 3487) / 1e6, 2);
    for (const r of rows.filter((x) => !x.match)) expect(r.explanation, r.optionId).toBeTruthy();
    expect(readFileSync(join(repo, "docs", "rbm_recostings.md"), "utf8"), "rerun: npm run recost:ias").toBe(recostMarkdown(rows));
  });
});
