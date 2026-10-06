import { describe, expect, it } from "vitest";
import { RBE_CAPTION, formatMoney, rbeTable, verdictText } from "../../src/engine/index";
import { dec, sum } from "../../src/engine/decimal";
import { cells, codes, illustrativeReform, labour, ob, opt, option, pop, proposal, purchase, run, side } from "./helpers";

// A business purchase of $X a year: X dollars per entity × 1 time × 1,000 entities.
const perThousand = (popId: string, totalDollars: number) => purchase(popId, totalDollars / 1000, 1);

describe("RBE table and aggregation (RBM pp. 5-6, 11)", () => {
  it("T-RBE-01 RBM p. 11 deregulatory example: a $400,000 a year saving reads ($0.4) | $0 | $0 | ($0.4)", () => {
    const r = run(proposal([pop("biz", 1000)], [option("o", [ob("dup", "administrative", side("purchase", [perThousand("biz", 400000)]), null)])]));
    const t = rbeTable(opt(r).rbe);
    expect(t.caption).toBe("Average annual regulatory costs (from business as usual)");
    expect(t.caption).toBe(RBE_CAPTION);
    expect(t.headers).toEqual(["Change in costs ($ million)", "Business", "Community organisations", "Individuals", "Total change in costs"]);
    expect(t.cells).toEqual(["Total, by sector", "($0.4)", "$0", "$0", "($0.4)"]);
    expect(t.notes).toEqual([]);
  });

  const interJurisdictional = (jurisdiction: string) =>
    run(
      proposal(
        [pop("biz", 1000)],
        [
          option("o", [
            ob("cth", "administrative", side("purchase", [perThousand("biz", 10000000)]), null, { jurisdiction: "commonwealth" }),
            ob("state", "administrative", null, side("purchase", [perThousand("biz", 2000000)]), { jurisdiction: "stateTerritory" }),
          ]),
        ],
        { jurisdiction },
      ),
    );

  it("T-RBE-02 RBM p. 6 inter-jurisdictional example: Commonwealth −$10m, states +$2m → ($8.0), with the split shown", () => {
    const r = interJurisdictional("interJurisdictional");
    expect(opt(r).rbe.total).toBe("-8000000");
    expect(cells(r)).toEqual(["($8.0)", "$0", "$0", "($8.0)"]);
    expect(opt(r).jurisdictionSplit).toEqual({ commonwealth: "-10000000", stateTerritory: "2000000" });
    expect(formatMoney(opt(r).jurisdictionSplit.commonwealth)).toBe("($10.0)");
    expect(formatMoney(opt(r).jurisdictionSplit.stateTerritory)).toBe("$2.0");
  });

  it("T-RBE-03 a state item in a Commonwealth-only proposal is excluded, with W-15", () => {
    const r = interJurisdictional("commonwealthOnly");
    expect(opt(r).rbe.total).toBe("-10000000");
    expect(codes(r)).toContain("W-15");
    expect(opt(r).excluded.map((e) => e.reason)).toContain("stateInCommonwealthOnly");
  });

  const mixed = () =>
    run(
      proposal(
        [pop("biz", 1000), pop("people", 1000, { group: "individual" })],
        [
          option("o", [
            ob("new-biz", "substantive", null, side("purchase", [perThousand("biz", 3000000)])),
            ob("gone-ind", "substantive", side("purchase", [perThousand("people", 5000000)]), null),
          ]),
        ],
      ),
    );

  it("T-RBE-04 mixed increases and reductions net correctly, with gross figures reported", () => {
    const r = mixed();
    expect(cells(r)).toEqual(["$3.0", "$0", "($5.0)", "($2.0)"]);
    expect(opt(r).gross).toEqual({ increases: "3000000", reductions: "-5000000" });
    expect(verdictText(opt(r).verdict)).toBe("Net reduction of $2.0 million a year");
  });

  it("T-RBE-05 net verdict wording for an increase, a reduction, no change, and a small change", () => {
    expect(verdictText({ kind: "increase", amount: "4393920" })).toBe("Net increase in regulatory burden of $4.4 million a year");
    expect(verdictText({ kind: "reduction", amount: "12724060" })).toBe("Net reduction of $12.7 million a year");
    expect(verdictText({ kind: "none", amount: "0" })).toBe("No net change");
    expect(verdictText({ kind: "increase", amount: "12345" })).toBe("Net increase in regulatory burden of $12,345 a year");
    const none = run(proposal([pop("biz", 1)], [option("sq", [], { isStatusQuo: true })]));
    expect(opt(none).verdict.kind).toBe("none");
  });

  it("T-RBE-06 rounding: half away from zero, totals from unrounded values, precision toggles", () => {
    const r = run(
      proposal(
        [pop("biz", 1000), pop("org", 1000, { group: "communityOrg" }), pop("people", 1000, { group: "individual" })],
        [option("o", [ob("a", "substantive", null, side("purchase", [perThousand("biz", 40000), perThousand("org", 40000), perThousand("people", 40000)]))])],
      ),
    );
    const t = rbeTable(opt(r).rbe);
    expect(t.cells.slice(1)).toEqual(["$0.0", "$0.0", "$0.0", "$0.1"]);
    expect(t.notes[0]).toMatch(/may not add/);
    expect(t.notes[1]).toMatch(/less than \$50,000/);
    expect(formatMoney("50000")).toBe("$0.1");
    expect(formatMoney("-50000")).toBe("($0.1)");
    expect(formatMoney("49999")).toBe("$0.0");
    expect(formatMoney("4393920", 2)).toBe("$4.39");
    expect(formatMoney("4393920", 3)).toBe("$4.394");
    expect(formatMoney("4393920", "dollars")).toBe("$4,393,920");
    expect(formatMoney("-400000", "dollars")).toBe("($400,000)");
    expect(formatMoney("91540.5", "dollars")).toBe("$91,540.50");
    expect(formatMoney("0")).toBe("$0");
    expect(rbeTable(opt(r).rbe, "dollars").headers[0]).toBe("Change in costs ($)");
  });

  it("T-RBE-07 one RBE table per option, including the status quo, side by side", () => {
    const report = ob("report", "administrative", side("labour", [labour("biz", 4, 4)]), null);
    const light = ob("report", "administrative", side("labour", [labour("biz", 4, 4)]), side("labour", [labour("biz", 2, 1)]));
    const r = run(
      proposal([pop("biz", 10000)], [
        option("repeal", [report]),
        option("light", [light]),
        option("sq", [], { isStatusQuo: true }),
      ]),
    );
    expect(r.options.map((o) => o.optionId)).toEqual(["repeal", "light", "sq"]);
    expect(cells(r, 0)).toEqual(["($14.6)", "$0", "$0", "($14.6)"]);
    expect(cells(r, 1)).toEqual(["($12.8)", "$0", "$0", "($12.8)"]);
    expect(cells(r, 2)).toEqual(["$0", "$0", "$0", "$0"]);
  });

  it("T-RBE-08 every breakdown reconciles exactly to the total", () => {
    const r = run(illustrativeReform());
    const o = opt(r);
    for (const b of Object.values(o.breakdowns)) {
      expect(sum(Object.values(b).map((v) => dec(v))).equals(dec(o.rbe.total))).toBe(true);
    }
    const m = opt(mixed());
    for (const b of Object.values(m.breakdowns)) {
      expect(sum(Object.values(b).map((v) => dec(v))).equals(dec(m.rbe.total))).toBe(true);
    }
    expect(o.breakdowns.timing).toEqual({ ongoing: "-12815600", transition: "91540" });
  });

  it("T-RBE-09 change per affected entity per year, by cohort", () => {
    const r = run(
      proposal(
        [pop("small", 8000, { cohort: "small" }), pop("large", 500, { cohort: "large" })],
        [option("o", [ob("kit", "substantive", null, side("purchase", [purchase("small", 100, 1), purchase("large", 1000, 1)]))])],
      ),
    );
    const pe = Object.fromEntries(opt(r).perEntity.map((p) => [p.populationId, p.changePerEntity]));
    expect(pe).toEqual({ small: "100", large: "1000" });
  });

  it("T-RBE-10 the 10-year total sums the yearly changes and drives the IA threshold 1 indicator", () => {
    const o = opt(run(illustrativeReform()));
    expect(o.tenYearTotal).toBe("-127240600");
    expect(sum(o.deltaByYear.map((v) => dec(v))).toFixed()).toBe(o.tenYearTotal);
    expect(dec(o.rbe.total).times(10).toFixed()).toBe(o.tenYearTotal);
    expect(o.iaThreshold1.likelyMet).toBe(true); // |−$127m| ≥ $20m
    const small = opt(run(proposal([pop("biz", 1000)], [option("o", [ob("dup", "administrative", side("purchase", [perThousand("biz", 400000)]), null)])])));
    expect(small.tenYearTotal).toBe("-4000000");
    expect(small.iaThreshold1.likelyMet).toBe(false);
  });
});
