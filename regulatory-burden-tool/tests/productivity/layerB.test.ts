// Layer B: from industry productivity shocks to GDP (plan §6.3; traceability F-B-01, F-B-02, F-B-05).
// The back-test fixtures are the committed outputs of alicia/analyses/costing_calibration/backtest.py.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { aggregate, capitalShare, defaultEvidence, ioWeights, ioigReach, shocksForCode, type IndustryShock, type IndustryWeight } from "../../src/productivity/index";

const repo = join(import.meta.dirname, "..", "..", "..");
const readJson = (...parts: string[]) => JSON.parse(readFileSync(join(repo, ...parts), "utf8"));
const backtest = readJson("alicia", "analyses", "costing_calibration", "backtest.json");
const cases = readJson("alicia", "analyses", "costing_calibration", "cases.json");
const parameters = readJson("data", "processed", "costing", "parameters.json");

/** The PC National industries with the back-test's weights (2018-19 value added, 2023-24 labour shares). */
const pcWeights: IndustryWeight[] = backtest.weights.industries.map((w: { pcn_no: number; name: string; va: number; labour_share: number }) => ({
  id: String(w.pcn_no),
  name: w.name,
  va: w.va,
  wages: w.va * w.labour_share,
}));

function expand(spec: string): number[] {
  return spec.split(",").flatMap((part) => {
    const [lo, hi] = part.split("-").map(Number);
    return Array.from({ length: (hi ?? lo!) - lo! + 1 }, (_, i) => lo! + i);
  });
}

describe("Layer B", () => {
  it("T-LB-01 reproduces the Python back-test against PC National, case by case", () => {
    const kinds = { lp: "labourProductivity", mfp: "mfp" } as const;
    let checked = 0;
    for (const c of backtest.cases as { type: string; size: number; industries: string; layer_b: number }[]) {
      if (c.type === "kp") continue; // capital productivity alone is not a shock type the engine produces
      const shocks: IndustryShock[] = expand(cases.industry_sets[c.industries]).map((n) => ({
        industry: String(n),
        type: kinds[c.type as "lp" | "mfp"],
        sizePct: c.size,
      }));
      expect(aggregate(shocks, pcWeights).gdpPct, `${c.industries} ${c.type}`).toBeCloseTo(c.layer_b, 5); // the fixture is rounded to 6 places
      checked += 1;
    }
    expect(checked).toBe(11);
    expect(capitalShare(pcWeights)).toBeCloseTo(backtest.weights.alpha, 6);
  });

  it("T-LB-02 identities: economy-wide shocks, linearity, additivity and partial reach", () => {
    const all = (type: IndustryShock["type"], sizePct: number, share = 1) => pcWeights.map((w) => ({ industry: w.id, type, sizePct, share }));
    const alpha = capitalShare(pcWeights);
    expect(aggregate(all("labourProductivity", 0.1), pcWeights).gdpPct).toBeCloseTo(0.1, 12); // F-B-01 check: 1% LP gives 1% GDP
    expect(aggregate(all("mfp", 0.1), pcWeights).gdpPct).toBeCloseTo(0.1 / (1 - alpha), 12);
    expect(aggregate(all("labourProductivity", 0.1, 0.5), pcWeights).gdpPct).toBeCloseTo(0.05, 12);
    const one: IndustryShock = { industry: "70", type: "labourProductivity", sizePct: 0.4 };
    const a = aggregate([one], pcWeights).gdpPct;
    expect(aggregate([{ ...one, sizePct: 0.8 }], pcWeights).gdpPct).toBeCloseTo(2 * a, 12);
    const both = aggregate([one, { industry: "78", type: "mfp", sizePct: 1 }], pcWeights);
    expect(both.gdpPct).toBeCloseTo(both.byType.labourProductivity + both.byType.mfp, 12);
    expect(both.contributions.map((c) => c.industry)).toEqual(["70", "78"]);
    expect(() => aggregate([{ industry: "999", type: "mfp", sizePct: 1 }], pcWeights)).toThrow(/no weights/);
    expect(() => aggregate([{ ...one, share: 1.5 }], pcWeights)).toThrow(/between 0 and 1/);
    expect(aggregate([], pcWeights).gdpPct).toBe(0);
  });

  it("T-LB-03 production weights come from the bundled input-output tables and reach ANZSIC codes through the concordance", () => {
    const weights = ioWeights(parameters.tables["abs_io.industries"].rows);
    const mapping = parameters.tables["abs_io.ioig_anzsic"].rows;
    expect(weights).toHaveLength(115);
    const alpha = capitalShare(weights);
    expect(alpha).toBeGreaterThan(0.4);
    expect(alpha).toBeLessThan(0.55);
    // A division reaches its industries in full.
    expect(ioigReach("E", mapping, new Set(weights.map((w) => w.id)))).toEqual([
      { ioig: "3001", share: 1 },
      { ioig: "3002", share: 1 },
      { ioig: "3101", share: 1 },
      { ioig: "3201", share: 1 },
    ]);
    // A class reaches its industry in proportion to that industry's classes; concordance-only IOIGs are skipped.
    const elec = shocksForCode("3232", "labourProductivity", 1, mapping, weights);
    expect(elec).toHaveLength(1);
    expect(elec[0]!.industry).toBe("3201");
    expect(elec[0]!.share).toBeGreaterThan(0);
    expect(elec[0]!.share).toBeLessThan(1);
    expect(shocksForCode("1213", "mfp", 1, mapping, weights).map((s) => s.industry)).toEqual(["1205"]);
    // Every ANZSIC division together reaches every industry exactly once, so an economy-wide shock is exact.
    const everyDivision = "ABCDEFGHIJKLMNOPQRS".split("").flatMap((d) => shocksForCode(d, "labourProductivity", 0.1, mapping, weights));
    expect(aggregate(everyDivision, weights).gdpPct).toBeCloseTo(0.1, 9);
    // Exposure scales the reach.
    expect(aggregate(shocksForCode("E", "mfp", 1, mapping, weights, 0.5), weights).gdpPct).toBeCloseTo(
      aggregate(shocksForCode("E", "mfp", 1, mapping, weights), weights).gdpPct / 2,
      12,
    );
  });

  it("T-LB-04 the model-error band in the evidence library is the back-test's", () => {
    for (const [kind, parameter] of [
      ["lp", "modelErrorLp"],
      ["mfp", "modelErrorMfp"],
    ] as const) {
      const e = defaultEvidence("F-B-05", parameter)!;
      expect([e.value, e.low, e.high], parameter).toEqual([1, backtest.model_error_band[kind].low, backtest.model_error_band[kind].high]);
    }
  });
});
