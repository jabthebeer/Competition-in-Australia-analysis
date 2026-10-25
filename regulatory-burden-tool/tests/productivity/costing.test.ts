// The time path, present values, Monte Carlo ranges, tornado and evidence gate (plan §6.3–6.6; traceability §2.4–2.5).
// All briefs here are ILLUSTRATIVE (synthetic), except where a test reproduces a Productivity Commission scenario.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import {
  buildContext,
  costBrief,
  defaultEvidence,
  evidenceGate,
  fixedSource,
  parseBrief,
  pathParams,
  pathShare,
  percentiles,
  presentValue,
  productivityCurve,
  responseShare,
  runCosting,
  sampledSource,
  simulate,
  tornado,
  triangular,
  uniform,
  CENTRAL,
} from "../../src/productivity/index";
import { parseArgs as parsePceArgs, runCli as runPce } from "../../src/cli/pce";
import { delayLine, ob, option, pop, proposal, side } from "../engine/helpers";

const repo = join(import.meta.dirname, "..", "..", "..");
const ctx = buildContext(JSON.parse(readFileSync(join(repo, "data", "processed", "costing", "parameters.json"), "utf8")));
const NON_AGRICULTURE = "BCDEFGHIJKLMNOPQRS".split("");
const L2 = ["30", "31", "32", "F", "46", "47", "48", "49", "52", "53", "69", "80", "81", "84", "85", "86", "87"];
const ev = (formula: string, parameter: string) => defaultEvidence(formula, parameter)!;

function brief(levers: object, industries: string[] = NON_AGRICULTURE, extra: { meta?: object; analysis?: object; burden?: object } = {}) {
  return parseBrief({
    schemaVersion: 1,
    kind: "policy-brief",
    id: "test",
    meta: { title: "Illustrative (synthetic)", jurisdictions: ["CTH"], startYear: 2027, ...extra.meta },
    scope: { industries: industries.map((anzsic) => ({ anzsic })) },
    levers,
    ...(extra.analysis ? { analysis: extra.analysis } : {}),
    ...(extra.burden ? { burden: extra.burden } : {}),
  });
}
const NON_COMPETES = { labour: { nonCompetes: { coveredShareChange: -0.2 } } };
const LICENSING = { labour: { licensing: { occupations: ["381231"], stringencyChange: -0.5 } } };

describe("time path and present value", () => {
  const p = pathParams(CENTRAL, 0.4);

  it("T-TP-01 productivity shocks pass through Égert & Gal's 5- and 10-year shares; the implied speed matches their MFP error correction", () => {
    expect(responseShare("productivity", 5, p)).toBeCloseTo(ev("F-B-04", "fiveYearShare").value, 12);
    expect(responseShare("productivity", 10, p)).toBeCloseTo(ev("F-B-04", "tenYearShare").value, 12);
    expect(responseShare("productivity", 500, p)).toBeCloseTo(1, 9);
    // b ≈ 0.050 a year, inside the speeds implied by their MFP error-correction terms (−0.033 to −0.052).
    const { b } = productivityCurve(p.fiveYearShare, p.tenYearShare);
    const mfp = ev("F-B-04", "ecmSpeedMfp");
    expect(b).toBeGreaterThan(-Math.log(1 + mfp.high));
    expect(b).toBeLessThan(-Math.log(1 + mfp.low));
    expect(() => productivityCurve(0.5, 0.4)).toThrow(/rise towards 1/);
  });

  it("T-TP-02 capital deepening follows the K/Y error-correction speed; a compliance cost change is direct, then capital", () => {
    const rho = ev("F-B-04", "ecmSpeedKY").value;
    expect(responseShare("capital", 10, p)).toBeCloseTo(1 - (1 + rho) ** 10, 12);
    expect(responseShare("directThenCapital", 1, p)).toBeCloseTo(0.6 + 0.4 * (1 - (1 + rho)), 12);
    expect(responseShare("directThenCapital", 2000, p)).toBeCloseTo(1, 9);
    expect(responseShare("capital", 0, p)).toBe(0);
  });

  it("T-TP-03 the phase-in arrives in equal steps over phaseInYears + 1 years, each building up on its own", () => {
    for (let t = 1; t <= 12; t++) expect(pathShare("productivity", t, 0, p)).toBe(responseShare("productivity", t, p));
    expect(pathShare("capital", 1, 2, p)).toBeCloseTo(responseShare("capital", 1, p) / 3, 12);
    const t = 7;
    const steps = [1, 2, 3].map((k) => responseShare("productivity", t - k + 1, p));
    expect(pathShare("productivity", t, 2, p)).toBeCloseTo(steps.reduce((a, b) => a + b) / 3, 12);
  });

  it("T-TP-04 present values discount end-of-year flows to the start of year 1", () => {
    expect(presentValue([100, 100], 0.1)).toBeCloseTo(100 / 1.1 + 100 / 1.21, 12);
    expect(presentValue([1, 2, 3], 0)).toBe(6);
  });

  it("T-TP-05 the engine's path is each channel's long-run effect times its path share; NPVs cover the duration at each rate", () => {
    const b = brief(NON_COMPETES, NON_AGRICULTURE, { meta: { phaseInYears: 1, durationYears: 5 } });
    const r = costBrief(b, ctx);
    const timing = pathParams(CENTRAL, r.layerB.alpha);
    expect(r.path).toHaveLength(10); // years 1 to max(10, duration)
    r.path.forEach((y) => expect(y.gdpPct).toBeCloseTo(r.gdpPct * pathShare("productivity", y.year, 1, timing), 12));
    expect(r.npv.map((n) => n.rate)).toEqual([0.07, 0.03, 0.1]);
    expect(r.npv[0]!.dollars).toBeCloseTo(presentValue(r.path.slice(0, 5).map((y) => y.gdpDollars), 0.07), 6);
    // A compliance saving reaches GDP at once, apart from the capital that responds to it.
    const ex = parseBrief(JSON.parse(readFileSync(join(repo, "regulatory-burden-tool", "examples", "illustrative-licensing.brief.json"), "utf8")));
    const c1 = costBrief(ex, ctx).channels.find((c) => c.channel === "C1")!;
    const exTiming = pathParams(CENTRAL, costBrief(ex, ctx).layerB.alpha);
    expect(c1.path[9]).toBeCloseTo(c1.gdpPct * pathShare("directThenCapital", 10, ex.meta.phaseInYears, exTiming), 12);
  });
});

describe("Monte Carlo and tornado", () => {
  it("T-MC-01 draws are uniform, fixed by seed, draw and key; the triangular inverse maps 0, the mode's quantile and 1 to low, mode and high", () => {
    const us = Array.from({ length: 4000 }, (_, i) => uniform(1, i, "k"));
    expect(Math.min(...us)).toBeGreaterThanOrEqual(0);
    expect(Math.max(...us)).toBeLessThan(1);
    expect(us.reduce((a, b) => a + b) / us.length).toBeCloseTo(0.5, 1);
    expect(uniform(1, 7, "k")).toBe(uniform(1, 7, "k"));
    expect(uniform(1, 7, "k")).not.toBe(uniform(2, 7, "k"));
    expect(triangular(0, 1, 2, 4)).toBe(1);
    expect(triangular(1 / 3, 1, 2, 4)).toBeCloseTo(2, 12);
    expect(triangular(1, 1, 2, 4)).toBe(4);
    expect(triangular(0.3, 5, 5, 5)).toBe(5);
    const xs = us.map((u) => triangular(u, 1, 2, 4));
    expect(xs.reduce((a, b) => a + b) / xs.length).toBeCloseTo(7 / 3, 1); // mean (a + b + c)/3
    expect(percentiles([1, 2, 3, 4, 5])).toEqual({ p10: 1.4, p50: 3, p90: 4.6 });
  });

  it("T-MC-02 an evidence entry shared by two formulas takes one draw; a brief range is sampled; runs are reproducible", () => {
    const s = sampledSource(3, 11);
    expect(s.get("F-C2-01", "r")).toBe(s.get("F-C3-01", "r")); // both read c2.r.oia-cba (A-P13)
    const x = s.input("levers.trade.opennessChangePp", { low: 0.5, high: 1.5 });
    expect(x).toBeGreaterThanOrEqual(0.5);
    expect(x).toBeLessThanOrEqual(1.5);
    expect(s.input("levers.trade.opennessChangePp", 1)).toBe(1);
    const a = simulate(brief(NON_COMPETES), ctx, 300, 5);
    expect(simulate(brief(NON_COMPETES), ctx, 300, 5)).toEqual(a);
    expect(simulate(brief(NON_COMPETES), ctx, 300, 6).gdpPct.p50).not.toBe(a.gdpPct.p50);
    const point = simulate(brief({ trade: { opennessChangePp: 1 } }), ctx, 300, 5).gdpPct;
    const ranged = simulate(brief({ trade: { opennessChangePp: { low: 0.5, high: 1.5 } } }), ctx, 300, 5).gdpPct;
    expect(ranged.p90 - ranged.p10).toBeGreaterThan(point.p90 - point.p10);
  });

  it("T-MC-03 the PC's L2 chain: the central value lies within the 10–90 range, which includes Layer B's model error", () => {
    const b = brief(LICENSING, L2);
    const r = costBrief(b, ctx);
    const m = simulate(b, ctx, 1000, 1);
    expect(m.gdpPct.p10).toBeLessThan(r.gdpPct);
    expect(m.gdpPct.p90).toBeGreaterThan(r.gdpPct);
    expect(m.byYear.map((y) => y.year)).toEqual([1, 5, 10]);
    expect(m.byChannel.map((c) => c.channel)).toEqual(["C8"]);
    // With the model error at its back-test band ends and all else central, GDP moves by exactly those factors (A-P19).
    const lp = ev("F-B-05", "modelErrorLp");
    expect(costBrief(b, ctx, fixedSource(new Map([[lp.id, lp.low]]))).gdpPct).toBeCloseTo(r.gdpPct * lp.low, 12);
  });

  it("T-MC-04 the tornado ranks parameters and ranged inputs by the swing they cause, at most ten, largest first", () => {
    const bars = tornado(brief({ ...LICENSING, trade: { opennessChangePp: { low: 0.5, high: 1.5 } } }, L2), ctx);
    expect(bars.length).toBeLessThanOrEqual(10);
    expect(bars[0]!.key).toBe("c8.licensing.bnvr2020");
    for (let i = 1; i < bars.length; i++) expect(bars[i]!.swing).toBeLessThanOrEqual(bars[i - 1]!.swing);
    expect(bars.map((b) => b.key)).toContain("input:levers.trade.opennessChangePp");
    expect(bars.every((b) => b.swing > 0)).toBe(true);
  });
});

describe("evidence gate and overlap rules in the engine", () => {
  it("T-GATE-01 a material effect whose largest channel is graded A is shown in full; below $200m it is indicative", () => {
    const big = runCosting(brief({ conduct: { route: "markup", markupChangePct: -5 } }), ctx, { draws: 200 });
    expect(big.gate.grade).toBe("A");
    expect(big.gate.status).toBe("full");
    expect(big.gate.threshold2.centralMeets).toBe(true);
    expect(big.gate.thresholdDollars).toBe(200);
    const small = runCosting(brief({ conduct: { route: "markup", markupChangePct: -0.01 } }, ["G"]), ctx, { draws: 200 });
    expect(small.gate.status).toBe("indicative");
    expect(small.gate.reasons.join()).toMatch(/below the \$200m threshold/);
    expect(small.gate.showGdp).toBe(true);
  });

  it("T-GATE-02 graded C is indicative; graded D or unconfirmed estimates hide GDP unless the brief opts in, with a watermark", () => {
    expect(runCosting(brief(NON_COMPETES), ctx, { draws: 200 }).gate.status).toBe("indicative");
    // The tool's own assumptions (here r, graded D) set ranges but not the grade (A-P31): a tax cut rests on σ (B).
    const tax = runCosting(brief({ capital: { companyTaxRate: { from: 0.3, to: 0.25 } } }), ctx, { draws: 200 });
    expect([tax.gate.status, tax.gate.grade]).toEqual(["full", "B"]);
    expect(tax.result.channels[0]!.assumptions).toEqual(["c2.r.oia-cba"]);
    // An unsourced custom shock is graded D (A-P24).
    const custom = { custom: [{ id: "s1", channel: "C12", industry: "F", type: "labourProductivity", size: 2, justification: "Illustrative" }] };
    const hidden = runCosting(brief(custom), ctx, { draws: 200 }).gate;
    expect([hidden.status, hidden.grade, hidden.showGdp, hidden.watermark]).toEqual(["hidden", "D", false, false]);
    const shown = runCosting(brief(custom, NON_AGRICULTURE, { analysis: { showUngatedEconomyWide: true } }), ctx, { draws: 200 }).gate;
    expect([shown.status, shown.showGdp, shown.watermark]).toEqual(["hidden", true, true]);
    const draft = parseBrief({ ...brief(NON_COMPETES), meta: { ...brief(NON_COMPETES).meta, provenance: { title: { origin: "modelEstimate" } } } });
    const r = costBrief(draft, ctx);
    const gate = evidenceGate(draft, r, simulate(draft, ctx, 100, 1), [{ code: "PB-04", message: "", path: "meta.title" }]);
    expect([gate.status, gate.watermark]).toEqual(["hidden", true]);
    // The low end checked against threshold 2 is the end of the range nearer zero.
    expect(Math.abs(tax.gate.threshold2.low)).toBeLessThanOrEqual(Math.abs(tax.gate.threshold2.central));
  });

  it("T-GATE-03 a burden costing rests on the RBE (grade A); s = 0 is an assumption that sets the range, not the grade", () => {
    const ex = parseBrief(JSON.parse(readFileSync(join(repo, "regulatory-burden-tool", "examples", "illustrative-licensing.brief.json"), "utf8")));
    const c1 = costBrief(ex, ctx).channels.find((c) => c.channel === "C1")!;
    expect(c1.grade).toBe("A");
    expect(c1.assumptions).toEqual(["c1.s.assumption"]);
  });

  it("T-PCE-13 O-2: an approval delay in an industry whose delay costs the burden proposal already counts is left out of C2", () => {
    const burden = proposal(
      [pop("builders", 1000, { industry: "E" })],
      [option("faster", [ob("permit", "delay", side("delay", [delayLine("builders", { approvalDelay: 3, netIncomePerUnit: 5000 })]), side("delay", [delayLine("builders", { approvalDelay: 1, netIncomePerUnit: 5000 })]))])],
      { durationYears: 10 },
    );
    const r = costBrief(brief({ capital: { investmentApprovalDelayChangeMonths: -2 } }, ["E", "F"], { burden }), ctx);
    const c2 = r.channels.find((c) => c.channel === "C2")!;
    expect(c2.effects.map((e) => e.anzsic)).toEqual(["F"]);
    expect(c2.reasons.join()).toMatch(/E is left out.*O-2/);
    expect(r.channels.find((c) => c.channel === "C1")!.gdpPct).toBeGreaterThan(0); // the delay saving is costed in C1
  });
});

describe("pce command line", () => {
  const example = join(repo, "regulatory-burden-tool", "examples", "illustrative-licensing.brief.json");

  it("T-PCLI-01 the CLI parses its options, reports the gate, the time path and NPVs, and hides GDP when the gate says so", () => {
    expect(parsePceArgs(["b.json", "--draws", "100", "--seed", "4", "--json"])).toMatchObject({ file: "b.json", draws: 100, seed: 4, json: true, showUngated: false });
    expect(() => parsePceArgs([])).toThrow(/Usage/);
    expect(() => parsePceArgs(["b.json", "--draws", "x"])).toThrow(/whole number/);
    const report = runPce([example, "--draws", "100"]);
    expect(report.exitCode).toBe(0);
    expect(report.stdout).toMatch(/## Evidence gate: indicative/);
    expect(report.stdout).toMatch(/Present value over 10 years: .* at 7% /);
    expect(report.stdout).toMatch(/\| GDP \| .* \| .* \| .* \| .* \|/);
    const json = JSON.parse(runPce([example, "--draws", "100", "--json"]).stdout);
    expect(json.ranges.draws).toBe(100);
    expect(json.gate.status).toBe("indicative");
    expect(runPce(["missing.brief.json"]).exitCode).toBe(1);
  });
});

