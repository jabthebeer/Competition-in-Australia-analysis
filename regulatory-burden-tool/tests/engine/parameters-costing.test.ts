import { describe, expect, it } from "vitest";
import { PARAMETERS, deriveWorkRate, parseProposal } from "../../src/engine/index";
import { dec } from "../../src/engine/decimal";
import { cells, codes, labour, ob, opt, option, pop, proposal, purchase, run, side } from "./helpers";

describe("Parameters and rates (RBM Appendix 2)", () => {
  it("T-PAR-01 default work rate is $91.54 exactly (52.31 × 1.75 = 91.5425, published to the cent)", () => {
    expect(PARAMETERS.rates.work.hourly).toBe("91.54");
    expect(dec("52.31").times("1.75").toFixed()).toBe("91.5425");
    expect(deriveWorkRate("52.31", "1.75")).toBe("91.54");
    expect(deriveWorkRate(60, 1.75)).toBe("105.00");
    expect(deriveWorkRate("52.315", "1")).toBe("52.32"); // half-up to the cent
    const p = parseProposal(proposal([pop("b", 1)], [option("o", [])]));
    expect(p.rates.work).toEqual({ hourly: 91.54, base: 52.31, multiplier: 1.75 });
  });

  it("T-PAR-02 default non-work (leisure) rate is $41, and volunteers use it too (DECISIONS #43)", () => {
    expect(PARAMETERS.rates.leisure.hourly).toBe("41");
    expect(PARAMETERS.rates.volunteer.hourly).toBe("41");
    const p = parseProposal(proposal([pop("b", 1)], [option("o", [])]));
    expect(p.rates.leisure.hourly).toBe(41);
    expect(p.rates.volunteer.hourly).toBe(41);
  });

  it("T-PAR-03 rates carry source, reference and next-update metadata; a different vintage raises W-18", () => {
    for (const r of Object.values(PARAMETERS.rates)) {
      expect(r.source.length).toBeGreaterThan(10);
      expect(r.ref).toMatch(/RBM/);
      expect(r.nextUpdate).toBeTruthy();
    }
    expect(PARAMETERS.rates.work.nextUpdate).toMatch(/February 2028.*confirmed/);
    const r = run(proposal([pop("b", 1)], [option("o", [])], { parameterVintage: "RBM-2024-01" }));
    expect(codes(r)).toContain("W-18");
    expect(codes(run(proposal([pop("b", 1)], [option("o", [])])))).not.toContain("W-18");
  });
});

describe("Costing formulas (RBM pp. 8-9)", () => {
  it("T-COST-01 labour, business: 2 h × $91.54 × 24 × 1,000 × 1 staff = $4,393,920 → $4.4", () => {
    const r = run(proposal([pop("biz", 1000)], [option("o", [ob("new", "administrative", null, side("labour", [labour("biz", 2, 24, { staff: 1 })]))])]));
    expect(opt(r).rbe.business).toBe("4393920");
    expect(opt(r).rbe.total).toBe("4393920");
    expect(cells(r)).toEqual(["$4.4", "$0", "$0", "$4.4"]);
  });

  it("T-COST-02 labour, individuals: (time × $41) × times × individuals, with no staff factor", () => {
    const individuals = pop("people", 100000, { group: "individual" });
    const base = (staff?: number) =>
      run(proposal([individuals], [option("o", [ob("form", "administrative", null, side("labour", [labour("people", 0.5, 2, { rateId: "leisure", ...(staff ? { staff } : {}) })]))])]));
    expect(opt(base()).rbe.individual).toBe("4100000");
    expect(cells(base())).toEqual(["$0", "$0", "$4.1", "$4.1"]);
    const withStaff = base(3);
    expect(opt(withStaff).rbe.individual).toBe("4100000"); // staff ignored for individuals
    expect(codes(withStaff)).toContain("W-11");
  });

  it("T-COST-03 purchase: $250 × 2 × 4,000 entities = $2,000,000 (no staff factor)", () => {
    const r = run(proposal([pop("biz", 4000)], [option("o", [ob("kit", "substantive", null, side("purchase", [purchase("biz", 250, 2)]))])]));
    expect(opt(r).rbe.business).toBe("2000000");
  });

  it("T-COST-04 do-anyway (BAU) share and expected compliance rate scale costs", () => {
    const mk = (doAnywayShare: number, complianceRate: number) =>
      run(proposal([pop("biz", 1000)], [option("o", [ob("kit", "substantive", null, side("purchase", [purchase("biz", 1000, 1, { complianceRate })]), { doAnywayShare })])]));
    expect(opt(mk(0, 1)).rbe.total).toBe("1000000");
    expect(opt(mk(0.2, 1)).rbe.total).toBe("800000");
    expect(opt(mk(0.2, 0.8)).rbe.total).toBe("640000");
  });

  it("T-COST-05 subsidies reduce the compliance cost, but not below zero (A-06)", () => {
    const mk = (perEntity: number) =>
      run(proposal([pop("biz", 1000)], [option("o", [ob("kit", "substantive", null, side("purchase", [purchase("biz", 100, 1, { subsidy: { perEntityPerActiveYear: perEntity, source: { description: "Illustrative grant" } } })]))])]));
    const partial = mk(30);
    expect(opt(partial).rbe.total).toBe("70000");
    expect(codes(partial)).not.toContain("W-12");
    const excess = mk(150);
    expect(opt(excess).rbe.total).toBe("0");
    expect(codes(excess)).toContain("W-12");
    const ex = opt(excess).excluded.find((e) => e.reason === "subsidyExcess");
    expect(ex?.annualAmount).toBe("50000");
  });

  it("T-COST-06 a range input uses its midpoint as the point estimate (A-07)", () => {
    const r = run(proposal([pop("biz", { low: 500, high: 1500 })], [option("o", [ob("new", "administrative", null, side("labour", [labour("biz", { low: 1, high: 3 }, 24)]))])]));
    expect(opt(r).rbe.total).toBe("4393920");
  });
});
