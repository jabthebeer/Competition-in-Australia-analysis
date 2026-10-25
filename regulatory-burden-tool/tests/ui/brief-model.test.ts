// The productivity draft kept beside the burden proposal (src/ui/briefModel.ts), the bundled register, and similar
// past changes (src/ui/similar.ts). Briefs here are ILLUSTRATIVE (synthetic).
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { computeProposal } from "../../src/engine/index";
import { parseBrief } from "../../src/productivity/index";
import { assembleBrief, checkBrief, isEmptyDraft, newBriefDraft, nextFinancialYear, splitBrief, type BriefDraft } from "../../src/ui/briefModel";
import { loadCostingRegister } from "../../src/ui/costingData";
import { exampleProposal } from "../../src/ui/example";
import { newProposal } from "../../src/ui/model";
import { directionCheck, leverDirection, similarChanges, suggestedCategories } from "../../src/ui/similar";

const repo = join(import.meta.dirname, "..", "..", "..");
const exampleBrief = () => parseBrief(JSON.parse(readFileSync(join(repo, "regulatory-burden-tool", "examples", "noncompete-ban.brief.json"), "utf8")));
const draftWith = (levers: BriefDraft["levers"], industries = ["3232"]): BriefDraft => ({ ...newBriefDraft(), scope: { industries: industries.map((anzsic) => ({ anzsic })) }, levers });

describe("brief draft", () => {
  it("T-UIB-01 a new draft is empty and not costable until it has an industry; the proposal supplies title, type and duration", () => {
    const d = newBriefDraft();
    expect(isEmptyDraft(d)).toBe(true);
    expect(d.meta.startYear).toBe(nextFinancialYear());
    expect(nextFinancialYear(new Date(2026, 9, 25))).toBe(2027);
    expect(nextFinancialYear(new Date(2026, 2, 1))).toBe(2026);
    const p = newProposal("reform");
    const empty = checkBrief(d, p, true);
    expect(empty.ok).toBe(false);
    const ready = checkBrief(draftWith({ labour: { nonCompetes: { coveredShareChange: -0.2 } } }), { ...p, title: "Ban non-competes", durationYears: 8 }, true);
    expect(ready.ok).toBe(true);
    if (ready.ok) {
      expect([ready.brief.meta.title, ready.brief.meta.durationYears, ready.brief.meta.proposalType]).toEqual(["Ban non-competes", 8, "reform"]);
      expect(ready.brief.burden).toBeUndefined(); // no obligations yet: no burden
      expect(ready.withBurden).toBe(false);
    }
  });

  it("T-UIB-02 a proposal with obligations becomes the burden, unless it fails to cost; splitting a brief gives back its draft and burden", () => {
    const p = exampleProposal();
    expect(computeProposal(p).options.length).toBeGreaterThan(0);
    const d = draftWith({ labour: { nonCompetes: { coveredShareChange: -0.2 } } });
    const withIt = checkBrief(d, p, true);
    expect(withIt.ok && withIt.brief.burden?.id).toBe(p.id);
    const without = checkBrief(d, p, false);
    expect(without.ok && without.brief.burden).toBeUndefined();
    const b = exampleBrief();
    const { draft, burden } = splitBrief(b);
    expect(burden?.id).toBe(b.burden?.id);
    // The app shows one title, the brief's, so the burden proposal takes it; everything else comes back as it was.
    expect(parseBrief(assembleBrief(draft, burden!, true))).toEqual({ ...b, burden: { ...b.burden!, title: b.meta.title } });
  });
});

describe("register and similar past changes", () => {
  it("T-UIB-03 the bundled register passes its check", async () => {
    const r = await loadCostingRegister();
    expect(r.ok, r.ok ? "" : r.problem).toBe(true);
    if (r.ok) {
      expect(r.register.records.length).toBeGreaterThan(100);
      expect(Object.keys(r.register.channels).sort()).toEqual(["ability-incentive", "barriers", "consumer-choice", "number-or-type", "prices-market-share"]);
    }
  });

  it("T-UIB-04 levers suggest OIA Step 1 categories; their direction is read from the signs", () => {
    const licensing = draftWith({ labour: { licensing: { occupations: ["381231"], stringencyChange: -0.5 } } });
    expect([...suggestedCategories(licensing).keys()].sort()).toEqual(["barriers", "number-or-type"]);
    expect(leverDirection(licensing)).toBe("enhancing");
    const cap = draftWith({ entry: { numberCap: { change: "introduce", excludedEntrantShare: 0.2 } } });
    expect(leverDirection(cap)).toBe("weakening");
    expect(leverDirection(draftWith({ labour: { licensing: { occupations: ["381231"], stringencyChange: -0.5 } }, entry: { numberCap: { change: "introduce", excludedEntrantShare: 0.2 } } }))).toBe("mixed");
    expect(leverDirection(newBriefDraft())).toBeUndefined();
    const conduct = draftWith({ conduct: { route: "markup", markupChangePct: -2, restrictions: ["priceControl", "information"] } });
    expect([...suggestedCategories(conduct).keys()].sort()).toEqual(["consumer-choice", "prices-market-share"]);
  });

  it("T-UIB-05 similar changes share categories or industries, one per reform family; a contrary direction is flagged", async () => {
    const r = await loadCostingRegister();
    if (!r.ok) throw new Error(r.problem);
    const licensing = draftWith({ labour: { licensing: { occupations: ["381231"], stringencyChange: -0.5 } } });
    const similar = similarChanges(licensing, r.register.records);
    expect(similar.length).toBeGreaterThan(0);
    expect(similar.length).toBeLessThanOrEqual(5);
    for (const s of similar) expect(s.sharedCategories.length + s.sharedIndustries.length).toBeGreaterThan(0);
    const families = similar.map((s) => s.record.family ?? s.record.id);
    expect(new Set(families).size).toBe(families.length);
    expect(similar[0]!.sharedIndustries).toContain("3232");
    // Mutual recognition of electricians' licences: the register expects it to enhance competition, so a tightening is flagged.
    const tighter = draftWith({ labour: { licensing: { occupations: ["381231"], stringencyChange: 0.5 } } });
    expect(directionCheck(tighter, similarChanges(tighter, r.register.records))).toMatch(/harder to compete/);
    expect(directionCheck(licensing, similar)).toBeUndefined();
  });
});
