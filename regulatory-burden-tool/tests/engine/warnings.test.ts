import { describe, expect, it } from "vitest";
import { WARNING_CATALOGUE } from "../../src/engine/index";
import { codes, delayLine, illustrativeReform, labour, ob, option, pop, proposal, purchase, run, side } from "./helpers";

// Each warning has a firing case and a non-firing case. All data is ILLUSTRATIVE.
const src = { justification: "Illustrative", source: { description: "Illustrative" } };
const newOb = (extra: object = {}, s: object = side("purchase", [purchase("biz", 10, 1)])) => ob("x", "substantive", null, s, extra);
const one = (o: object, extra: object = {}, pops: object[] = [pop("biz", 100)]) => run(proposal(pops, [option("o", [o])], extra));

describe("Validation warnings (brief section 7)", () => {
  it("every warning code has a title and a reference", () => {
    for (const [code, w] of Object.entries(WARNING_CATALOGUE)) {
      expect(code).toMatch(/^W-\d\d$/);
      expect(w.ref.length).toBeGreaterThan(3);
    }
  });

  it("W-01 fee or tax entered as a purchase cost", () => {
    expect(codes(one(newOb({ tags: ["governmentFee"] })))).toContain("W-01");
    expect(codes(one(newOb({ tags: ["governmentFee"] }, side("labour", [labour("biz", 1, 1)]))))).not.toContain("W-01");
  });

  it("W-02 outsourced service entered as labour", () => {
    expect(codes(one(ob("x", "administrative", null, side("labour", [labour("biz", 1, 1)]), { tags: ["outsourcedService"] })))).toContain("W-02");
    expect(codes(one(newOb({ tags: ["outsourcedService"] })))).not.toContain("W-02");
  });

  it("W-03 delay cost where the entity isn't waiting on government", () => {
    const d = (waitingOnGovernment: boolean) => ob("x", "delay", null, side("delay", [delayLine("biz", { approvalDelay: 1, netIncomePerUnit: 1, waitingOnGovernment })]));
    expect(codes(one(d(false)))).toContain("W-03");
    expect(codes(one(d(true)))).not.toContain("W-03");
  });

  it("W-04 leisure rate for non-resident individuals", () => {
    const o = ob("x", "administrative", null, side("labour", [labour("p", 1, 1, { rateId: "leisure" })]));
    expect(codes(one(o, {}, [pop("p", 10, { group: "individual", nonResident: true })]))).toContain("W-04");
    expect(codes(one(o, {}, [pop("p", 10, { group: "individual" })]))).not.toContain("W-04");
  });

  it("W-05 default rate overridden without a justification", () => {
    const rates = (override?: object) => ({ rates: { work: { hourly: 120, base: 68.57, multiplier: 1.75, ...(override ? { override } : {}) }, leisure: { hourly: 41 }, volunteer: { hourly: 41 } } });
    expect(codes(one(newOb(), rates()))).toContain("W-05");
    expect(codes(one(newOb(), rates(src)))).not.toContain("W-05");
  });

  it("W-06 labour rate differs between current and reformed versions (see also T-REF-11)", () => {
    const o = (extra: object = {}) => ob("x", "administrative", side("labour", [labour("biz", 1, 1)]), side("labour", [labour("biz", 1, 1, { rateId: "leisure" })]), extra);
    expect(codes(one(o()))).toContain("W-06");
    expect(codes(one(o({ rateChangeJustification: src })))).not.toContain("W-06");
  });

  it("W-07 do-anyway share of 0% on common industry practice", () => {
    expect(codes(one(newOb({ tags: ["commonIndustryPractice"] })))).toContain("W-07");
    expect(codes(one(newOb({ tags: ["commonIndustryPractice"], doAnywayShare: 0.2 })))).not.toContain("W-07");
  });

  it("W-08 start-up cost on the current regime (see also T-REF-10)", () => {
    const cur = (status?: string) => ob("x", "substantive", side("purchase", [purchase("biz", 1, 1)], { type: "oneOff" }, status ? { status } : {}), null);
    expect(codes(one(cur()))).toContain("W-08");
    expect(codes(one(cur("future")))).not.toContain("W-08");
  });

  it("W-09 reform with no transition costs", () => {
    expect(codes(run(illustrativeReform({}, { transitions: [] })))).toContain("W-09");
    expect(codes(run(illustrativeReform()))).not.toContain("W-09");
  });

  it("W-10 exemption threshold creates a cliff (see also T-REF-09)", () => {
    const pops = [pop("s", 10, { cohort: "small" }), pop("m", 10, { cohort: "medium" })];
    const mk = (mediumReformed: number) =>
      run(proposal(pops, [option("o", [ob("x", "substantive", side("purchase", [purchase("s", 10, 1), purchase("m", 10, 1)]), side("purchase", [purchase("m", mediumReformed, 1)]))], { transitions: [] })]));
    expect(codes(mk(10))).toContain("W-10");
    expect(codes(mk(5))).not.toContain("W-10"); // medium also gets relief: no cliff
  });

  it("W-11 implausible inputs", () => {
    expect(codes(one(ob("x", "administrative", null, side("labour", [labour("biz", 1, 400)]))))).toContain("W-11");
    expect(codes(one(ob("x", "administrative", null, side("labour", [labour("biz", 30, 1)]))))).toContain("W-11");
    expect(codes(one(ob("x", "administrative", null, side("labour", [labour("s", 1, 1, { staff: 25 })])), {}, [pop("s", 10, { cohort: "small" })]))).toContain("W-11");
    expect(codes(one(ob("x", "administrative", null, side("labour", [labour("s", 1, 12, { staff: 3 })])), {}, [pop("s", 10, { cohort: "small" })]))).not.toContain("W-11");
  });

  it("W-12 subsidy larger than the cost (see also T-COST-05)", () => {
    const sub = (amount: number) => newOb({}, side("purchase", [purchase("biz", 10, 1, { subsidy: { perEntityPerActiveYear: amount, source: { description: "x" } } })]));
    expect(codes(one(sub(20)))).toContain("W-12");
    expect(codes(one(sub(5)))).not.toContain("W-12");
  });

  it("W-13 government-to-government obligation", () => {
    const o = ob("x", "administrative", null, side("labour", [labour("g", 1, 1)]));
    expect(codes(one(o, {}, [pop("g", 5, { entityType: "governmentAgency" })]))).toContain("W-13");
    expect(codes(one(o, {}, [pop("g", 5, { entityType: "gbe" })]))).not.toContain("W-13");
  });

  it("W-14 enforcement classification without a justification, or enforcement-tagged item still counted", () => {
    expect(codes(one(newOb({ scope: { classification: "enforcement" } })))).toContain("W-14");
    expect(codes(one(newOb({ tags: ["enforcementActivity"] })))).toContain("W-14");
    expect(codes(one(newOb({ scope: { classification: "enforcement", override: src } })))).not.toContain("W-14");
  });

  it("W-15 state or territory cost in a Commonwealth-only proposal (see also T-RBE-03)", () => {
    expect(codes(one(newOb({ jurisdiction: "stateTerritory" })))).toContain("W-15");
    expect(codes(one(newOb({ jurisdiction: "stateTerritory" }), { jurisdiction: "interJurisdictional" }))).not.toContain("W-15");
  });

  it("W-16 duration differs from 10 years without a justification (see also T-ANN-06)", () => {
    expect(codes(one(newOb(), { durationYears: 4 }))).toContain("W-16");
    expect(codes(one(newOb(), { durationYears: 4, durationOverride: src }))).not.toContain("W-16");
  });

  it("W-17 delay costs: seek OIA advice (information)", () => {
    const r = one(ob("x", "delay", null, side("delay", [delayLine("biz", { approvalDelay: 1, netIncomePerUnit: 1 })])));
    expect(r.warnings.find((w) => w.code === "W-17")?.severity).toBe("info");
    expect(codes(one(newOb()))).not.toContain("W-17");
  });

  it("W-18 different parameter vintage (see also T-PAR-03)", () => {
    expect(codes(one(newOb(), { parameterVintage: "RBM-2024-01" }))).toContain("W-18");
    expect(codes(one(newOb()))).not.toContain("W-18");
  });

  it("W-19 expected compliance rate differs between versions (information)", () => {
    const o = (rate: number) => ob("x", "substantive", side("purchase", [purchase("biz", 1, 1)]), side("purchase", [purchase("biz", 1, 1, { complianceRate: rate })]));
    expect(codes(one(o(0.9)))).toContain("W-19");
    expect(codes(one(o(1)))).not.toContain("W-19");
  });

  it("W-20 timing outside the analysis period (information)", () => {
    expect(codes(one(newOb({}, side("purchase", [purchase("biz", 1, 1)], { type: "oneOff", year: 12 }))))).toContain("W-20");
    expect(codes(one(newOb({}, side("purchase", [purchase("biz", 1, 1)], { type: "oneOff", year: 10 }))))).not.toContain("W-20");
  });

  it("W-21 baseline doesn't match how the change is made (see also T-REF-14)", () => {
    expect(codes(one(newOb(), { remakesSunsettingInstrument: true }))).toContain("W-21");
    expect(codes(one(newOb(), { remakesSunsettingInstrument: false, baseline: "noInstrument" }))).toContain("W-21");
    expect(codes(one(newOb(), { remakesSunsettingInstrument: false }))).not.toContain("W-21");
  });
});
