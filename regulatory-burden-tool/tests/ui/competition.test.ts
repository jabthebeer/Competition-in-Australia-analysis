// The competition screen's measures (src/ui/competition.ts). Proposals here are ILLUSTRATIVE (synthetic).
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { computeProposal, parseProposal } from "../../src/engine/index";
import { buildContext } from "../../src/productivity/index";
import { newBriefDraft, type BriefDraft } from "../../src/ui/briefModel";
import { checkCostingParameters, loadCostingRegister } from "../../src/ui/costingData";
import { bandsOf, categoryReasons, cohortBurden, regulationBarrier, revenuePerBusiness, shareAffected, smallToLarge } from "../../src/ui/competition";
import { labour, ob, option, pop, proposal, side } from "../engine/helpers";

const repo = join(import.meta.dirname, "..", "..", "..");
const raw = JSON.parse(readFileSync(join(repo, "data", "processed", "costing", "parameters.json"), "utf8"));
const ctx = buildContext(raw);
const params = (() => {
  const c = checkCostingParameters(raw);
  if (!c.ok) throw new Error(c.problem);
  return c.parameters;
})();

/** A new reporting obligation, the same 10 hours a year for small and large construction businesses (synthetic). */
const twoSizes = parseProposal(
  proposal(
    [pop("small", 9000, { cohort: "small", industry: "E" }), pop("large", 100, { cohort: "large", industry: "E" })],
    [option("o", [ob("report", "administrative", null, side("labour", [labour("small", 10, 1), labour("large", 10, 1)]))])],
    { proposalType: "new" },
  ),
);

describe("competition screen", () => {
  it("T-UIC-01 a group's size bands come from its employment band, else its cohort", () => {
    expect(bandsOf(twoSizes.populations[0]!)).toEqual(["0-4", "5-19"]);
    expect(bandsOf(twoSizes.populations[1]!)).toEqual(["200+"]);
    expect(bandsOf({ ...twoSizes.populations[0]!, employmentBand: "nonEmploying" })).toEqual(["0-4"]);
    expect(bandsOf({ ...twoSizes.populations[0]!, cohort: "all" })).toEqual([]);
  });

  it("T-UIC-02 cost against revenue by size: Australian Industry sales over CABEE counts; the small-to-large ratio weights by businesses", () => {
    const sales = (b: string) => ctx.industryByBand.E![b]!.sales * 1e6;
    const n = (b: string) => ctx.businessesByBand.E![b]!;
    expect(revenuePerBusiness("E", ["0-4", "5-19"], ctx)).toBeCloseTo((sales("0-4") + sales("5-19")) / (n("nonemp") + n("1-4") + n("5-19")), 6);
    expect(revenuePerBusiness("E", ["200+"], ctx)).toBeCloseTo(sales("200+") / n("200+"), 6);
    expect(revenuePerBusiness("K", ["200+"], ctx)).toBeUndefined(); // Australian Industry leaves out finance and insurance
    expect(revenuePerBusiness("E", ["total"], ctx)).toBeCloseTo(sales("total") / n("total"), 6);
    const opt = computeProposal(twoSizes).options[0]!;
    const rows = cohortBurden(opt, twoSizes, ctx);
    expect(rows.map((r) => r.size)).toEqual(["small", "large"]);
    for (const r of rows) expect(r.costShare).toBeCloseTo(r.costPerEntity / r.revenue!, 12);
    // Same cost per business, far less revenue: the cost weighs much more on small businesses.
    const ratio = smallToLarge(rows)!;
    expect(ratio).toBeCloseTo(rows[0]!.costShare! / rows[1]!.costShare!, 12);
    expect(ratio).toBeGreaterThan(10);
    expect(smallToLarge(rows.slice(0, 1))).toBeUndefined();
  });

  it("T-UIC-03 share of the scope's businesses affected; the BCS incidence of regulation as a barrier by size and division", () => {
    const draft: BriefDraft = { ...newBriefDraft(), scope: { industries: [{ anzsic: "E" }] } };
    const s = shareAffected(twoSizes, draft, ctx)!;
    expect(s.affected).toBe(9100);
    expect(s.inScope).toBe(ctx.businessesByBand.E!.total);
    const bcs = regulationBarrier(params, ["E"]);
    expect(bcs.map((r) => r.label)).toEqual(["All businesses", "0–4 persons", "5–19 persons", "20–199 persons", "200 or more persons", "Division E"]);
    expect(bcs.every((r) => r.pct > 0 && r.pct < 100)).toBe(true);
  });

  it("T-UIC-04 Step 1 categories come from the levers and from similar past changes", async () => {
    const r = await loadCostingRegister();
    if (!r.ok) throw new Error(r.problem);
    const draft: BriefDraft = { ...newBriefDraft(), scope: { industries: [{ anzsic: "3232" }] }, levers: { labour: { licensing: { occupations: ["381231"], stringencyChange: -0.5 } } } };
    const reasons = categoryReasons(draft, r.register.records);
    expect(reasons.get("barriers")?.[0]).toMatch(/Occupational licensing/);
    expect([...reasons.values()].flat().some((x) => /similar past change/.test(x))).toBe(true);
  });
});
