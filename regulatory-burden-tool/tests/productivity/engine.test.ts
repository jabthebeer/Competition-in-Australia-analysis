// The productivity and competition costing engine (plan §6; traceability §2.3): Layer A channels, custom shocks and
// Layer B, at central values. All briefs here are ILLUSTRATIVE (synthetic), except where a test reproduces a
// Productivity Commission scenario.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { computeProposal } from "../../src/engine/index";
import { buildContext, capitalShare, costBrief, defaultEvidence, parseBrief, valueAddedOf, type CostingResult } from "../../src/productivity/index";

const repo = join(import.meta.dirname, "..", "..", "..");
const params = JSON.parse(readFileSync(join(repo, "data", "processed", "costing", "parameters.json"), "utf8"));
const ctx = buildContext(params);
const NON_AGRICULTURE = "BCDEFGHIJKLMNOPQRS".split("");
/** The PC's L2 industries as ANZSIC codes (PC National industries 70–74, 78–81, 83, 96, 103–104, 106–107). */
const L2 = ["30", "31", "32", "F", "46", "47", "48", "49", "52", "53", "69", "80", "81", "84", "85", "86", "87"];

function brief(levers: object, industries: string[] = NON_AGRICULTURE, extra: object = {}) {
  return parseBrief({
    schemaVersion: 1,
    kind: "policy-brief",
    id: "test",
    meta: { title: "Illustrative (synthetic)", jurisdictions: ["CTH"], startYear: 2027 },
    scope: { industries: industries.map((anzsic) => ({ anzsic })) },
    levers,
    ...extra,
  });
}
const channel = (r: CostingResult, id: string) => r.channels.find((c) => c.channel === id)!;
const pc = (code: string) => params.tables["pc_national.simulations"].rows.find((r: { code: string; real_gdp: number }) => r.code === code && r.real_gdp > 0).real_gdp;

describe("costing context", () => {
  it("T-CTX-01 the context comes from the bundled parameters: GDP, rescaled input-output weights, depreciation, capital shares, BERD", () => {
    expect(ctx.gdpYear).toMatch(/^\d{4}-\d{2}$/);
    expect(ctx.gdp).toBeGreaterThan(2_000_000); // $ million
    expect(ctx.ioScale).toBeCloseTo(ctx.gdp / ctx.gdpByYear[ctx.ioYear]!, 12);
    expect(ctx.weights).toHaveLength(115);
    expect(Object.keys(ctx.depreciation).sort()).toEqual("ABCDEFGHIJKLMNOPQRS".split(""));
    for (const d of Object.values(ctx.depreciation)) {
      expect(d).toBeGreaterThan(0);
      expect(d).toBeLessThan(0.3);
    }
    // ABS productivity capital shares cover the 16 market-sector divisions only.
    expect(Object.keys(ctx.capitalShare).sort()).toEqual("ABCDEFGHIJKLMNRS".split(""));
    // GDP per head and population (ASNA Table 1), entry rates (CABEE), businesses and employment by size.
    expect(ctx.population).toBeGreaterThan(2e7);
    expect(ctx.population).toBeLessThan(4e7);
    expect(ctx.entryRate.TOT).toBeGreaterThan(5);
    expect(ctx.entryRateYear).toMatch(/^\d{4}-\d{2}$/);
    expect(ctx.sizeYear).toMatch(/^\d{4}-\d{2}$/);
    expect(Object.keys(ctx.businessesByBand.C!).sort()).toEqual(["1-4", "20-199", "200+", "5-19", "nonemp", "total"]);
    expect(Object.keys(ctx.industryByBand.C!).sort()).toEqual(["0-4", "20-199", "200+", "5-19", "total"]);
    // Value added of a code is the share-weighted sum the Layer B split uses, so the divisions add up to the total.
    const all = ctx.weights.reduce((s, w) => s + w.va, 0);
    expect("ABCDEFGHIJKLMNOPQRS".split("").reduce((s, d) => s + valueAddedOf(d, ctx), 0)).toBeCloseTo(all, 3);
  });
});

describe("costing engine", () => {
  it("T-PCE-01 a brief with no levers costs nothing", () => {
    const r = costBrief(brief({}), ctx);
    expect(r.channels).toEqual([]);
    expect(r.gdpPct).toBe(0);
    expect(r.gdpDollars).toBe(0);
    expect(r.notModelled.join(" ")).toMatch(/terms of trade/);
  });

  it("T-PCE-02 C8 licensing reproduces the PC's L2 chain: 0.8% labour productivity in 15 industries, GDP within the back-test tolerance", () => {
    const r = costBrief(brief({ labour: { licensing: { occupations: ["381231"], stringencyChange: -0.5 } } }, L2), ctx);
    const c8 = channel(r, "C8");
    expect(c8.effects.map((e) => e.value)).toEqual(L2.map(() => 0.8)); // 1.6 × 0.5, the PC's shock
    expect(c8.evidence).toEqual(["c8.licensing.bnvr2020"]);
    expect(c8.grade).toBe("C");
    expect(Math.abs(r.gdpPct / pc("L2") - 1)).toBeLessThan(defaultEvidence("F-B-05", "tolerance")!.value);
  });

  it("T-PCE-03 C8 non-competes: a ban reproduces the PC's L1 within the tolerance, and agriculture is left out", () => {
    const r = costBrief(brief({ labour: { nonCompetes: { coveredShareChange: -0.2 } } }, ["A", ...NON_AGRICULTURE]), ctx);
    const c8 = channel(r, "C8");
    expect(c8.effects.map((e) => e.anzsic)).toEqual(NON_AGRICULTURE);
    expect(c8.effects[0]!.value).toBeCloseTo(0.1 * 1.9, 12); // 10% pass-through × the midpoint wage effect (A-P21)
    expect(Math.abs(r.gdpPct / pc("L1") - 1)).toBeLessThan(0.15);
    // Half the coverage change gives half the effect (linear, A-P09).
    const half = costBrief(brief({ labour: { nonCompetes: { coveredShareChange: -0.1 } } }), ctx);
    expect(half.gdpPct).toBeCloseTo(r.gdpPct / 2, 12);
  });

  it("T-PCE-04 C1: the burden's resource cost lowers MFP by its share of value added, and reaches GDP as the cost itself (Hulten)", () => {
    const ex = parseBrief(JSON.parse(readFileSync(join(repo, "regulatory-burden-tool", "tests", "fixtures", "synthetic-licensing.json"), "utf8")));
    const r = costBrief(ex, ctx);
    const c1 = channel(r, "C1");
    const rbe = computeProposal(ex.burden!).options[0]!.rbe.total;
    const dC = Number(rbe.toString());
    expect(c1.effects).toHaveLength(1);
    expect(c1.effects[0]!.anzsic).toBe("3232");
    expect(c1.effects[0]!.value).toBeCloseTo((-dC / (valueAddedOf("3232", ctx) * 1e6)) * 100, 12);
    const all = ctx.weights.reduce((s, w) => s + w.va, 0);
    expect(c1.gdpPct).toBeCloseTo((-dC / (all * 1e6) / (1 - capitalShare(ctx.weights))) * 100, 12);
    expect(c1.gdpPct).toBeGreaterThan(0); // a saving
  });

  it("T-PCE-05 C3: a company tax cut lowers the user cost of capital and raises GDP; a rise does the opposite", () => {
    const cut = costBrief(brief({ capital: { companyTaxRate: { from: 0.3, to: 0.25 } } }), ctx);
    const rise = costBrief(brief({ capital: { companyTaxRate: { from: 0.3, to: 0.35 } } }), ctx);
    expect(cut.gdpPct).toBeGreaterThan(0.2);
    // Partial equilibrium, below Treasury's general-equilibrium +1.2% for 30% → 25% (WP 2016-02).
    expect(cut.gdpPct).toBeLessThan(1.2);
    expect(rise.gdpPct).toBeLessThan(0);
    // The scope includes public administration, education and health, which take the market-sector capital share.
    expect(channel(cut, "C3").evidence.sort()).toEqual(["c2.r.oia-cba", "c3.alpha.abs-mfp", "c3.sigma.cfm2011"]);
    // A market-sector division uses its own ABS capital income share (F-C3-03).
    const mining = costBrief(brief({ capital: { companyTaxRate: { from: 0.3, to: 0.25 } } }, ["B"]), ctx);
    const alpha = channel(mining, "C3").effects[0]!.chain.find((f) => f.label.startsWith("Capital share"))!;
    expect(alpha.value).toBe(ctx.capitalShare.B);
    expect(channel(mining, "C3").evidence).not.toContain("c3.alpha.abs-mfp");
    // A depreciation change without the tax rate is reported, not costed.
    const dz = costBrief(brief({ capital: { depreciationPvChange: 0.05 } }), ctx);
    expect(channel(dz, "C3").reasons.join()).toMatch(/needs the company tax rate/);
  });

  it("T-PCE-06 C2: investment approval delay works through the user cost (Δln c ≈ r·d), scaled by exposure", () => {
    const full = costBrief(brief({ capital: { investmentApprovalDelayChangeMonths: -6 } }), ctx);
    const c2 = channel(full, "C2");
    expect(c2.effects[0]!.chain.find((f) => f.label.startsWith("Change in the user cost"))!.value).toBeCloseTo(0.07 * -0.5, 12);
    expect(full.gdpPct).toBeGreaterThan(0);
    const tenth = costBrief(parseBrief({ ...brief({ capital: { investmentApprovalDelayChangeMonths: -6 } }), scope: { industries: NON_AGRICULTURE.map((anzsic) => ({ anzsic, exposure: 0.1 })) } }), ctx);
    expect(tenth.gdpPct).toBeCloseTo(full.gdpPct / 10, 12);
  });

  it("T-PCE-07 C7: an ETCR indicator change is costed economy-wide; other indicators are reported, not quantified (A-P07)", () => {
    const r = costBrief(brief({ conduct: { route: "pmr", indicator: "energy", from: 1, to: 0.69 } }, ["D"]), ctx);
    const c7 = channel(r, "C7");
    expect(c7.effects[0]!.value).toBeCloseTo(-0.047 * -0.31 * 100, 12); // Égert & Gal's typical reform: +1.46% MFP
    // Close to Égert & Gal's long-run +2.09% of GDP per head for a typical reform (they use α = 0.33 and add employment).
    expect(r.gdpPct).toBeGreaterThan(1.8);
    expect(r.gdpPct).toBeLessThan(2.6);
    const other = costBrief(brief({ conduct: { route: "pmr", indicator: "lawyers", from: 1.29, to: 1 } }, ["M"]), ctx);
    expect(channel(other, "C7").status).toBe("notQuantified");
    expect(other.gdpPct).toBe(0);
  });

  it("T-PCE-08 C6: a mark-up change is interpolated within Hambur & Freestone's interval and capped beyond it (A-P06)", () => {
    const small = costBrief(brief({ conduct: { route: "markup", markupChangePct: -2 } }, ["G"]), ctx);
    expect(small.gdpPct).toBeGreaterThan(0);
    expect(channel(small, "C6").reasons).toEqual([]);
    const huge = costBrief(brief({ conduct: { route: "markup", markupChangePct: -50 } }), ctx);
    expect(channel(huge, "C6").reasons.join()).toMatch(/beyond the range/);
    const span = costBrief(brief({ conduct: { route: "markup", markupChangePct: -100 } }), ctx);
    expect(span.gdpPct).toBeCloseTo(huge.gdpPct, 12); // both capped at the computed interval
  });

  it("T-PCE-09 C9 and C10: R&D and openness raise economy-wide productivity; tariffs and FDI are reported, not added to GDP", () => {
    const rd = costBrief(brief({ innovation: { rdUserCostChangePct: -10, productApprovalTimeChangeDays: -30 } }), ctx);
    expect(rd.gdpPct).toBeGreaterThan(0);
    expect(channel(rd, "C9").reasons.join()).toMatch(/product-approval time/);
    const trade = costBrief(brief({ trade: { opennessChangePp: 1, tariffChangePp: -1, fdiRestrictivenessChangePct: -10 } }), ctx);
    expect(trade.gdpPct).toBeCloseTo(0.6, 9); // 0.006 per pp, labour-augmenting, economy-wide: GDP moves one for one
    const c10 = channel(trade, "C10");
    expect(c10.reasons.join()).toMatch(/tariff change is not costed/);
    expect(c10.other[0]!.value).toBeCloseTo(-0.208 * -10, 12);
  });

  it("T-PCE-10 C11: the welfare cost of funding is revenue × the funding tax's MEB, beside GDP rather than in it", () => {
    const r = costBrief(brief({ fiscal: { revenueChangeDollarsPerYear: 1e9, fundingTax: "labourIncome" } }), ctx);
    expect(r.welfareDollars).toBeCloseTo(-0.21e9, 3);
    expect(r.gdpPct).toBe(0);
    const other = costBrief(brief({ fiscal: { revenueChangeDollarsPerYear: 1e9, fundingTax: "other" } }), ctx);
    expect(channel(other, "C11").status).toBe("notQuantified");
  });

  it("T-PCE-11 custom shocks add to or replace a channel's shocks (O-6); other shock types are reported; grades follow A-P24", () => {
    const lic = { licensing: { occupations: ["381231"], stringencyChange: -0.5 } };
    const shock = { id: "s1", channel: "C8", industry: "F", type: "labourProductivity", size: 2, justification: "Illustrative" };
    const modelled = costBrief(brief({ labour: lic }, ["F"]), ctx).gdpPct;
    const added = costBrief(brief({ labour: lic, custom: [{ ...shock, relation: "adds" }] }, ["F"]), ctx);
    const replaced = costBrief(brief({ labour: lic, custom: [{ ...shock, relation: "replaces" }] }, ["F"]), ctx);
    expect(added.gdpPct).toBeCloseTo(modelled * (1 + 2 / 0.8), 12);
    expect(replaced.gdpPct).toBeCloseTo(modelled * (2 / 0.8), 12);
    expect(channel(added, "C8").grade).toBe("D"); // no source
    const sourced = costBrief(brief({ custom: [{ ...shock, channel: "C12", source: { description: "A cited study" } }] }, ["F"]), ctx);
    expect(channel(sourced, "C12").grade).toBe("C");
    const rent = costBrief(brief({ custom: [{ ...shock, channel: "C12", type: "rent", size: 1e6 }] }, ["F"]), ctx);
    expect(channel(rent, "C12").reasons.join()).toMatch(/reported, not added to GDP/);
    expect(rent.gdpPct).toBe(0);
  });

  it("T-PCE-12 the realisation factor scales GDP; channels add up; GDP per person uses ASNA's population", () => {
    const levers = { labour: { nonCompetes: { coveredShareChange: -0.2 } }, trade: { opennessChangePp: 0.5 } };
    const r = costBrief(brief(levers), ctx);
    expect(r.gdpPct).toBeCloseTo(r.channels.reduce((s, c) => s + c.gdpPct, 0), 12);
    expect(r.gdpDollars).toBeCloseTo((r.gdpPct / 100) * ctx.gdp, 6);
    expect(r.gdpPerPersonDollars).toBeCloseTo((r.gdpDollars * 1e6) / ctx.population, 6);
    const half = costBrief(brief(levers, NON_AGRICULTURE, { analysis: { realisationFactor: 0.5 } }), ctx);
    expect(half.gdpPct).toBeCloseTo(r.gdpPct / 2, 12);
  });

  it("T-PCE-14 C4 step 1: an entry-cost cut raises entry in naturally high-entry industries only, in the log form (A-P11, A-P29)", () => {
    const r = costBrief(brief({ entry: { costPerEntrantChangeDollars: -500 } }), ctx);
    const c4 = channel(r, "C4");
    const base = 0.0225 * ctx.gdpPerCapita;
    const expected = -0.546 * Math.log((base - 500) / base);
    const high = NON_AGRICULTURE.filter((d) => ctx.entryRate[d]! >= ctx.entryRate.TOT!);
    expect(c4.effects.map((e) => e.anzsic)).toEqual(high);
    c4.effects.forEach((e) => expect(e.value).toBeCloseTo(expected, 12));
    expect(c4.notes.join()).toMatch(/Industry C: .* not a naturally high-entry industry/);
    expect(r.gdpPct).toBe(0); // no frontier gap: no productivity effect (A-P12)
    expect(c4.other[0]!.value).toBeCloseTo(0.009 * expected, 12);
    expect(c4.evidence.sort()).toEqual(["c4.beta2.ahhw2022", "c4.entry-cost-au.dj2002", "c4.epsilon.klr2004", "c4.lambda0.ahhw2022"]);
    // An industry's own baseline cost replaces Djankov et al.'s; a cut as large as the cost is not costed.
    const own = channel(costBrief(brief({ entry: { costPerEntrantChangeDollars: -500, baselineCostPerEntrantDollars: 1000 } }, ["I"]), ctx), "C4");
    expect(own.effects[0]!.value).toBeCloseTo(-0.546 * Math.log(0.5), 12);
    const all = channel(costBrief(brief({ entry: { costPerEntrantChangeDollars: -1000, baselineCostPerEntrantDollars: 1000 } }, ["I"]), ctx), "C4");
    expect(all.reasons.join()).toMatch(/as large as the baseline/);
  });

  it("T-PCE-15 C4: a cap moves entry by the share kept out; with a frontier gap, faster convergence raises labour productivity, graded D", () => {
    const cap = channel(costBrief(brief({ entry: { numberCap: { change: "introduce", excludedEntrantShare: 0.25 } } }, ["C"]), ctx), "C4");
    expect(cap.effects[0]!.value).toBeCloseTo(-0.25 * ctx.entryRate.C!, 12); // caps bind in every industry
    const gap = 0.6;
    const b = brief({ entry: { numberCap: { change: "remove", excludedEntrantShare: 0.25 }, frontierGapLogPoints: gap } }, ["I"]);
    const r = costBrief(b, ctx);
    const c4 = channel(r, "C4");
    const dLambda = 0.009 * 0.25 * ctx.entryRate.I!;
    expect(c4.effects[0]!.value).toBeCloseTo(((gap * dLambda) / (0.415 + dLambda)) * 100, 12);
    expect(c4.grade).toBe("D");
    expect(r.gdpPct).toBeGreaterThan(0);
    // The gain arrives at the convergence speed: 1 − (1 − λ)^t of the long run in year t.
    expect(c4.path[0]! / c4.gdpPct).toBeCloseTo(0.415, 12);
    expect(c4.path[4]! / c4.gdpPct).toBeCloseTo(1 - 0.585 ** 5, 12);
    const time = channel(costBrief(brief({ entry: { approvalTimeChangeDays: -30, exitCostChangeDollars: -100 } }), ctx), "C4");
    expect(time.status).toBe("notQuantified");
    expect(time.reasons).toHaveLength(2);
  });

  it("T-PCE-16 C5 screens an employee threshold: businesses and employment in the bands near it, and its cost against wages; no GDP effect", () => {
    const r = costBrief(brief({ thresholds: [{ id: "t20", metric: "employees", change: "introduce", value: 20, costAbovePerYearDollars: 10000 }] }, ["C"]), ctx);
    const c5 = channel(r, "C5");
    const n = (band: string) => ctx.businessesByBand.C![band]!;
    expect(c5.other[0]!.value).toBe(n("5-19") + n("20-199")); // 18–22 employees overlaps both bands
    expect(c5.other[1]!.value).toBeCloseTo(ctx.industryByBand.C!["5-19"]!.employment + ctx.industryByBand.C!["20-199"]!.employment, 9);
    const perBusiness = (ctx.industryByBand.C!["20-199"]!.wages * 1e6) / n("20-199");
    expect(c5.other[2]!.value).toBeCloseTo((10000 / perBusiness) * 100, 9);
    expect(r.gdpPct).toBe(0);
    expect(c5.reasons.join()).toMatch(/not quantified/);
    const assets = channel(costBrief(brief({ thresholds: [{ id: "t", metric: "assets", change: "introduce", value: 1e7, costAbovePerYearDollars: 1 }] }), ctx), "C5");
    expect(assets.reasons[0]).toMatch(/no size bands by assets/);
  });

  it("T-PCE-18 C5 screens a payroll or turnover threshold through its employee equivalent: the value over wages (or sales) per person employed", () => {
    const total = ctx.industryByBand.C!.total!;
    const perPerson = (total.wages * 1e6) / (total.employment * 1e3);
    // A payroll threshold worth 20 employees screens exactly as the 20-employee threshold of T-PCE-16.
    const payroll = channel(costBrief(brief({ thresholds: [{ id: "p", metric: "payroll", change: "introduce", value: 20 * perPerson, costAbovePerYearDollars: 10000 }] }, ["C"]), ctx), "C5");
    const employees = channel(costBrief(brief({ thresholds: [{ id: "p", metric: "employees", change: "introduce", value: 20, costAbovePerYearDollars: 10000 }] }, ["C"]), ctx), "C5");
    expect(payroll.other.map((o) => o.value)).toEqual(employees.other.map((o) => o.value));
    expect(payroll.other[0]!.chain[1]!.value).toBeCloseTo(20, 9);
    expect(payroll.notes.join()).toMatch(/A-P34/);
    const sales = (ctx.industryByBand.C!.total!.sales * 1e6) / (total.employment * 1e3);
    const turnover = channel(costBrief(brief({ thresholds: [{ id: "s", metric: "turnover", change: "introduce", value: 20 * sales, costAbovePerYearDollars: 10000 }] }, ["C"]), ctx), "C5");
    expect(turnover.other[0]!.value).toBe(employees.other[0]!.value);
  });

  it("T-PCE-19 C8: mutual recognition is recorded with a note, not costed", () => {
    const lic = { occupations: ["381231"], stringencyChange: -0.5 };
    const plain = channel(costBrief(brief({ labour: { licensing: lic } }, ["E"]), ctx), "C8");
    const mr = channel(costBrief(brief({ labour: { licensing: { ...lic, mutualRecognition: true } } }, ["E"]), ctx), "C8");
    expect(mr.effects).toEqual(plain.effects);
    expect(mr.notes.join()).toMatch(/Mutual recognition is recorded but not costed.*A-P35/);
    expect(plain.notes.join()).not.toMatch(/Mutual recognition/);
  });

  it("T-PCE-17 O-1: entrants' compliance costs leave C1 when C4 costs entry; entrant populations must be the burden's", () => {
    const ex = JSON.parse(readFileSync(join(repo, "regulatory-burden-tool", "tests", "fixtures", "synthetic-licensing.json"), "utf8"));
    const withEntrants = parseBrief({ ...ex, levers: { ...ex.levers, entry: { ...ex.levers.entry, entrantPopulationIds: ["electricians"] } } });
    const c1 = channel(costBrief(withEntrants, ctx), "C1");
    expect(c1.effects).toEqual([]);
    expect(c1.notes.join()).toMatch(/left out of C1 .* O-1/);
    expect(() => parseBrief({ ...ex, levers: { ...ex.levers, entry: { ...ex.levers.entry, entrantPopulationIds: ["nobody"] } } })).toThrow(/not a population of the burden proposal/);
  });
});
