import { describe, expect, it } from "vitest";
import { activeYears, effectiveDelay, formatMoney, parseProposal, timingFactors } from "../../src/engine/index";
import { dec, sum } from "../../src/engine/decimal";
import { cells, codes, delayLine, labour, ob, opt, option, pop, proposal, purchase, run, side } from "./helpers";

const d = (n: number) => dec(n);
const override = { justification: "Policy ends sooner (illustrative)", source: { description: "Illustrative" } };

describe("Delay costs (RBM pp. 2-3, 10; A-01)", () => {
  it("T-DEL-01 RBM p. 10: 6-month approval, ready at 4 months → 2 months; ready on lodgement → 6 months", () => {
    expect(effectiveDelay(d(0), d(6), d(4)).toFixed()).toBe("2");
    expect(effectiveDelay(d(0), d(6), d(0)).toFixed()).toBe("6");
  });

  it("T-DEL-02 application delay counts from the same start point, and the effective delay can't go below zero", () => {
    expect(effectiveDelay(d(1), d(6), d(4)).toFixed()).toBe("3");
    expect(effectiveDelay(d(0), d(6), d(8)).toFixed()).toBe("0");
  });

  it("T-DEL-03 delay cost per year = entities × effective delay × (net income + extra expenses); W-17 asks for OIA advice", () => {
    const mk = (extra: number) =>
      run(proposal([pop("applicants", 10)], [option("o", [ob("licence", "delay", null, side("delay", [delayLine("applicants", { approvalDelay: 2, netIncomePerUnit: 50000, extraExpensesPerUnit: extra })]))])]));
    expect(opt(mk(0)).rbe.total).toBe("1000000");
    expect(opt(mk(5000)).rbe.total).toBe("1100000");
    expect(codes(mk(0))).toContain("W-17");
  });

  it("T-DEL-04 faster approvals: 100 applications a year, 6 → 3 months, $10,000/month → ($3.0)", () => {
    const line = (approvalDelay: number) => delayLine("applicants", { approvalDelay, netIncomePerUnit: 10000 });
    const r = run(proposal([pop("applicants", 100)], [option("o", [ob("approval", "delay", side("delay", [line(6)]), side("delay", [line(3)]), { levers: ["fasterApproval"] })])]));
    expect(opt(r).rbe.total).toBe("-3000000");
    expect(cells(r)).toEqual(["($3.0)", "$0", "$0", "($3.0)"]);
  });

  it("T-DEL-05 OIA calculator Example C (days): 9 applications, 35 → 19 days, $13,800/day is a reduction", () => {
    const line = (approvalDelay: number) => delayLine("apps", { unit: "days", approvalDelay, netIncomePerUnit: 13800 });
    const r = run(proposal([pop("apps", 9)], [option("o", [ob("approval", "delay", side("delay", [line(35)]), side("delay", [line(19)]))])]));
    expect(opt(r).rbe.total).toBe("-1987200");
    expect(opt(r).tenYearTotal).toBe("-19872000"); // OIA states $19.87m, unsigned
    expect(formatMoney(opt(r).tenYearTotal)).toBe("($19.9)");
    expect(cells(r)[3]).toBe("($2.0)");
  });
});

describe("Annualisation (RBM pp. 6, 8)", () => {
  const oneOff = (extra: object = {}) =>
    proposal([pop("biz", 1)], [option("o", [ob("buy", "substantive", null, side("purchase", [purchase("biz", 1000000, 1)], { type: "oneOff", year: 1 }))])], extra);

  it("T-ANN-01 a one-off cost of X is X/10 a year over 10 years, or X/4 over 4 years", () => {
    expect(opt(run(oneOff())).rbe.total).toBe("100000");
    expect(opt(run(oneOff({ durationYears: 4, durationOverride: override }))).rbe.total).toBe("250000");
  });

  it("T-ANN-02 a constant ongoing cost annualises to its year-1 cost", () => {
    const r = run(proposal([pop("biz", 1000)], [option("o", [ob("rec", "administrative", null, side("labour", [labour("biz", 2, 24)]))])]));
    expect(opt(r).rbe.total).toBe(opt(r).deltaByYear[0]);
  });

  it("T-ANN-03 every 2 years over 10 years = 5 occurrences ÷ 10, whether it starts in year 1 or 2", () => {
    for (const firstYear of [1, 2]) {
      const t = { type: "everyKYears" as const, k: 2, firstYear };
      expect(sum(timingFactors(t, 10)).toFixed()).toBe("5");
      const r = run(proposal([pop("biz", 1)], [option("o", [ob("audit", "substantive", null, side("purchase", [purchase("biz", 1000, 1)], t))])]));
      expect(opt(r).rbe.total).toBe("500");
    }
    expect(activeYears({ type: "everyKYears", k: 2, firstYear: 1 }, 10)).toEqual([1, 3, 5, 7, 9]);
    expect(activeYears({ type: "everyKYears", k: 2, firstYear: 2 }, 10)).toEqual([2, 4, 6, 8, 10]);
  });

  it("T-ANN-04 every 3 years: the first occurrence year changes the count (A-10)", () => {
    expect(activeYears({ type: "everyKYears", k: 3, firstYear: 1 }, 10)).toEqual([1, 4, 7, 10]);
    expect(activeYears({ type: "everyKYears", k: 3, firstYear: 4 }, 10)).toEqual([4, 7, 10]);
  });

  it("T-ANN-05 an explicit year-by-year schedule: sum of factors × annual cost ÷ duration", () => {
    const factors = [1, 1, 0.5, 0, 0, 0, 0, 0, 0, 0];
    const r = run(proposal([pop("biz", 1)], [option("o", [ob("phase", "substantive", null, side("purchase", [purchase("biz", 1000, 1)], { type: "schedule", factors }))])]));
    expect(opt(r).rbe.total).toBe("250");
    expect(opt(r).deltaByYear.slice(0, 3)).toEqual(["1000", "1000", "500"]);
  });

  it("T-ANN-06 a shorter duration truncates the profile; ≠ 10 years without a justification raises W-16", () => {
    const ongoing = (extra: object) =>
      proposal([pop("biz", 1)], [option("o", [ob("rec", "substantive", null, side("purchase", [purchase("biz", 1200, 1)]))])], extra);
    const r = run(ongoing({ durationYears: 3 }));
    expect(opt(r).deltaByYear).toHaveLength(3);
    expect(opt(r).rbe.total).toBe("1200");
    expect(codes(r)).toContain("W-16");
    expect(codes(run(ongoing({ durationYears: 3, durationOverride: override })))).not.toContain("W-16");
    expect(opt(run(oneOff({ durationYears: 3, durationOverride: override }))).rbe.total).toBe("333333.3333333333333333333333333333333333");
  });

  it("T-ANN-07 real terms with no discounting: discount, inflation and benefit fields are rejected", () => {
    for (const extra of [{ discountRate: 0.07 }, { inflation: 0.025 }, { benefits: [] }]) {
      expect(() => parseProposal(proposal([pop("b", 1)], [option("o", [])], extra))).toThrow(/Unrecognized key/);
    }
    expect(() => parseProposal(proposal([pop("b", 1)], [option("o", [], { discountRate: 0.07 })]))).toThrow(/Unrecognized key/);
    expect(() => parseProposal(proposal([pop("b", 1)], [option("o", [])], { durationYears: 12 }))).toThrow(/OIA/);
  });

  it("T-ANN-08 OIA calculator Examples A, B and D reproduce OIA's stated answers", () => {
    // Example A: 110 wholesalers × 22 h/yr at $150/h (user rate) → $3.63m over 10 years.
    const a = run(
      proposal([pop("w", 110)], [option("o", [ob("collect-report", "administrative", null, side("labour", [labour("w", 22, 1, { rateId: "oia150" })]))])], {
        rates: {
          work: { hourly: 91.54, base: 52.31, multiplier: 1.75 },
          leisure: { hourly: 41 },
          volunteer: { hourly: 41 },
          custom: [{ id: "oia150", label: "Example A rate", kind: "work", hourly: 150, override: { justification: "Given in OIA Example A", source: { description: "OIA RBE calculator, sheet 5. Examples" } } }],
        },
      }),
    );
    expect(opt(a).tenYearTotal).toBe("3630000");
    expect(cells(a)[3]).toBe("$0.4");
    // Example B: 15,000 centres, 4 h initial course in year 1, 1 h refresher every 3 years (years 4, 7, 10) → $9.61m.
    const b = run(
      proposal([pop("c", 15000)], [
        option("o", [
          ob("initial", "administrative", null, side("labour", [labour("c", 4, 1)], { type: "oneOff", year: 1 })),
          ob("refresher", "administrative", null, side("labour", [labour("c", 1, 1)], { type: "everyKYears", k: 3, firstYear: 4 })),
        ]),
      ]),
    );
    expect(opt(b).tenYearTotal).toBe("9611700");
    expect(cells(b)[3]).toBe("$1.0");
    // Example D: 30,000 retailers; $800 system + 2 h set-up in year 1; 1 h a year from year 2 → $54.21m.
    const dd = run(
      proposal([pop("r", 30000)], [
        option("o", [
          ob("system", "substantive", null, side("purchase", [purchase("r", 800, 1)], { type: "oneOff", year: 1 })),
          ob("setup", "administrative", null, side("labour", [labour("r", 2, 1)], { type: "oneOff", year: 1 })),
          ob("review", "administrative", null, side("labour", [labour("r", 1, 1)], { type: "ongoing", startYear: 2 })),
        ]),
      ]),
    );
    expect(opt(dd).tenYearTotal).toBe("54208200");
    expect(cells(dd)[3]).toBe("$5.4");
  });
});
