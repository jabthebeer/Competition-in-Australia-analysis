import { describe, expect, it } from "vitest";
import { copyCurrentToReformed, parseProposal, reformDiff } from "../../src/engine/index";
import { dec, sum } from "../../src/engine/decimal";
import { WORK_RATE, cells, codes, illustrativeReform, labour, ob, opt, option, pop, proposal, purchase, run, side } from "./helpers";

// All data in this file is ILLUSTRATIVE (synthetic), unless stated otherwise.

describe("Reform comparison: remove and replace (brief section 6)", () => {
  it("T-REF-01 illustrative reform: quarterly 4 h → annual 2 h, plus 1 h familiarisation → ($12.7)", () => {
    const o = opt(run(illustrativeReform()));
    expect(o.context.currentAnnual).toBe("14646400");
    expect(o.context.reformedAnnual).toBe("1830800");
    expect(o.context.transitionAnnual).toBe("91540");
    expect(o.rbe.total).toBe("-12724060");
    expect(o.rbe.business).toBe("-12724060");
    expect(o.context.shareRemoved).toBe("0.875");
    expect(o.context.shareRemovedNetOfTransition).toBe("0.86875");
    const r = run(illustrativeReform());
    expect(cells(r)).toEqual(["($12.7)", "$0", "$0", "($12.7)"]);
  });

  const richObligation = () =>
    parseProposal(
      proposal(
        [pop("small", 800, { cohort: "small" }), pop("large", 50, { cohort: "large" })],
        [
          option("o", [
            ob(
              "records",
              "administrative",
              side("labour", [labour("small", 1.5, 12, { staff: 2 }), labour("large", { low: 2, high: 6 }, 12, { staff: 5 })]),
              null,
              { doAnywayShare: 0.3 },
            ),
            ob("audit", "substantive", side("purchase", [purchase("small", 900, 1, { subsidy: { perEntityPerActiveYear: 100, source: { description: "Illustrative" } } }), purchase("large", 5000, 1)], { type: "everyKYears", k: 3, firstYear: 2 }), null),
          ]),
        ],
      ),
    );

  it("T-REF-02 identity: a reformed regime identical to the current one changes nothing, in every year and breakdown", () => {
    const p = richObligation();
    const opt0 = p.options[0]!;
    opt0.obligations = opt0.obligations.map(copyCurrentToReformed);
    const o = opt(run(p));
    expect(o.rbe).toEqual({ business: "0", communityOrg: "0", individual: "0", total: "0" });
    expect(o.deltaByYear.every((v) => v === "0")).toBe(true);
    for (const b of Object.values(o.breakdowns)) expect(Object.values(b).every((v) => v === "0")).toBe(true);
    expect(o.verdict.kind).toBe("none");
  });

  it("T-REF-03 an empty current regime reproduces a standard new-regulation costing", () => {
    const newReg = run(proposal([pop("biz", 1000)], [option("o", [ob("new", "administrative", null, side("labour", [labour("biz", 2, 24)]))])], { proposalType: "new" }));
    expect(opt(newReg).rbe.total).toBe("4393920");
    expect(opt(newReg).context.currentAnnual).toBe("0");
    expect(opt(newReg).context.shareRemoved).toBeNull();
  });

  // $1,000 per entity per year for 1,000 entities = $1,000,000 a year today.
  const doAnyway = (reformedPerEntity: number | null, share: number) =>
    opt(
      run(
        proposal([pop("biz", 1000)], [
          option("o", [
            ob(
              "records",
              "substantive",
              side("purchase", [purchase("biz", 1000, 1)]),
              reformedPerEntity === null ? null : side("purchase", [purchase("biz", reformedPerEntity, 1)]),
              { doAnywayShare: share },
            ),
          ]),
        ]),
      ),
    );

  it("T-REF-04 do-anyway share on removal: 25% of the activity continues, so the saving is cut by 25%", () => {
    expect(doAnyway(null, 0).rbe.total).toBe("-1000000");
    expect(doAnyway(null, 0.25).rbe.total).toBe("-750000");
  });

  it("T-REF-05 reduction above the do-anyway level: the full cut is saved ($1,000 → $500, 25%)", () => {
    expect(doAnyway(500, 0.25).rbe.total).toBe("-500000");
  });

  it("T-REF-06 reduction below the do-anyway level: the saving is capped ($1,000 → $100, 25%)", () => {
    expect(doAnyway(100, 0.25).rbe.total).toBe("-750000");
    // Policy illustration: 16 h quarterly → one 2 h report; firms do 4 h anyway → 12 h saved per business.
    const r = opt(
      run(
        proposal([pop("biz", 1)], [
          option("o", [ob("report", "administrative", side("labour", [labour("biz", 4, 4)]), side("labour", [labour("biz", 2, 1)]), { doAnywayShare: 0.25 })]),
        ]),
      ),
    );
    expect(r.rbe.total).toBe(dec(-12).times(WORK_RATE).toFixed());
  });

  it("T-REF-07 one year of dual running: year 1 adds only the reformed cost; savings start in year 2", () => {
    const o = opt(run(illustrativeReform({}, { timing: { reformStartYear: 1, overlapYears: 1 } })));
    const report = o.items.filter((i) => i.obligationId === "report");
    expect(sum(report.map((i) => dec(i.deltaByYear[0]!))).toFixed()).toBe("1830800");
    expect(o.deltaByYear[0]).toBe("2746200"); // reformed 1,830,800 + familiarisation 915,400
    expect(o.deltaByYear[1]).toBe("-12815600");
    expect(o.rbe.total).toBe("-11259420");
    expect(cells(run(illustrativeReform({}, { timing: { reformStartYear: 1, overlapYears: 1 } })))[3]).toBe("($11.3)");
  });

  it("T-REF-08 deferred commencement (phase-in without dual running): no change until the reform starts", () => {
    const o = opt(run(illustrativeReform({}, { timing: { reformStartYear: 2, overlapYears: 0 } })));
    expect(o.deltaByYear[0]).toBe("0");
    expect(o.deltaByYear[1]).toBe(dec(-12815600).plus(915400).toFixed()); // transition moves with the reform
    expect(o.rbe.total).toBe("-11442500");
  });

  const threshold = (exemptAs: "missing" | "zero") => {
    const cohorts = [pop("small", 8000, { cohort: "small", employmentBand: "5-19" }), pop("medium", 1500, { cohort: "medium" }), pop("large", 500, { cohort: "large" })];
    const reformedLines = [labour("medium", 4, 4), labour("large", 4, 4)];
    if (exemptAs === "zero") reformedLines.unshift(labour("small", 4, 4, { line: { entities: 0 } }));
    return run(
      proposal(cohorts, [
        option("o", [
          ob("report", "administrative", side("labour", [labour("small", 4, 4), labour("medium", 4, 4), labour("large", 4, 4)]), side("labour", reformedLines), { levers: ["threshold"] }),
        ]),
      ]),
    );
  };

  it("T-REF-09 small-business exemption: only the small cohort changes, per-entity results are right, and the cliff is flagged", () => {
    for (const variant of ["missing", "zero"] as const) {
      const r = threshold(variant);
      const o = opt(r);
      expect(o.rbe.total).toBe("-11717120");
      expect(cells(r)[3]).toBe("($11.7)");
      const pe = Object.fromEntries(o.perEntity.map((p) => [p.populationId, p]));
      expect(pe.small?.changePerEntity).toBe("-1464.64");
      expect(pe.medium?.changePerEntity).toBe("0");
      expect(pe.large?.changePerEntity).toBe("0");
      expect(pe.medium?.cliffFlag).toBe(true);
      expect(pe.large?.cliffFlag).toBe(false);
      expect(codes(r)).toContain("W-10");
    }
  });

  it("T-REF-10 sunk costs are not savings; future periodic costs are avoidable", () => {
    const r = run(
      proposal([pop("biz", 1000)], [
        option("o", [
          ob("system", "substantive", side("purchase", [purchase("biz", 5000, 1)], { type: "oneOff", year: 1 }, { status: "alreadyIncurred" }), null),
          ob("replace", "substantive", side("purchase", [purchase("biz", 2000, 1)], { type: "everyKYears", k: 5, firstYear: 3 }), null),
        ]),
      ]),
    );
    const o = opt(r);
    expect(o.rbe.total).toBe(dec(-2000).times(1000).times(2).dividedBy(10).toFixed()); // years 3 and 8 avoided
    expect(o.excluded.find((e) => e.obligationId === "system")?.reason).toBe("sunk");
    expect(r.warnings.find((w) => w.code === "W-08")?.severity).toBe("info");
    const unconfirmed = run(proposal([pop("biz", 1)], [option("o", [ob("system", "substantive", side("purchase", [purchase("biz", 5000, 1)], { type: "oneOff", year: 1 }), null)])]));
    expect(unconfirmed.warnings.find((w) => w.code === "W-08")?.severity).toBe("warning");
  });

  it("T-REF-11 the reformed version keeps the current labour rate unless a justified change is made", () => {
    const p = parseProposal(proposal([pop("biz", 100)], [option("o", [ob("report", "administrative", side("labour", [labour("biz", 4, 4)]), null)])]));
    const copied = copyCurrentToReformed(p.options[0]!.obligations[0]!);
    expect(copied.reformed?.lines[0]?.labour?.rateId).toBe("work");
    const changed = structuredClone(copied);
    changed.reformed!.lines[0]!.labour!.rateId = "leisure";
    p.options[0]!.obligations = [changed];
    expect(codes(run(p))).toContain("W-06");
    p.options[0]!.obligations = [{ ...changed, rateChangeJustification: { justification: "Illustrative", source: { description: "Illustrative" } } }];
    expect(codes(run(p))).not.toContain("W-06");
  });

  it("T-REF-12 copy-on-reform: the diff lists only the levers that changed", () => {
    const p = parseProposal(proposal([pop("biz", 100)], [option("o", [ob("report", "administrative", side("labour", [labour("biz", 4, 4)]), null)])]));
    const copied = copyCurrentToReformed(p.options[0]!.obligations[0]!);
    expect(reformDiff(copied)).toEqual([]);
    copied.reformed!.lines[0]!.labour!.hours = 2;
    copied.reformed!.lines[0]!.labour!.timesPerYear = 1;
    expect(reformDiff(copied).map((c) => c.path)).toEqual(["lines.biz.labour.hours", "lines.biz.labour.timesPerYear"]);
    expect(reformDiff(copied)[0]).toEqual({ path: "lines.biz.labour.hours", current: 4, reformed: 2 });
  });

  it("T-REF-13 the waterfall reconciles: current + removed + reduced + increased + new + transition = current + net change", () => {
    const perEntity = (cost: number) => side("purchase", [purchase("biz", cost, 1)]);
    const r = run(
      proposal([pop("biz", 1000)], [
        option("o", [
          ob("removed", "substantive", perEntity(300), null),
          ob("reduced", "substantive", perEntity(500), perEntity(200)),
          ob("increased", "substantive", perEntity(100), perEntity(150)),
          ob("new", "substantive", null, perEntity(40)),
        ], { transitions: [ob("t", "administrative", null, side("labour", [labour("biz", 1, 1)], { type: "oneOff" }))] }),
      ]),
    );
    const o = opt(r);
    const w = Object.fromEntries(o.waterfall.map((s) => [s.step, s.value]));
    expect(w).toEqual({ current: "900000", removed: "-300000", reduced: "-300000", increased: "50000", new: "40000", transition: "9154", end: "399154" });
    const middle = sum(["removed", "reduced", "increased", "new", "transition"].map((k) => dec(w[k]!)));
    expect(middle.toFixed()).toBe(o.rbe.total);
  });

  it("T-REF-14 baseline toggle: current settings vs no instrument (sunsetting remake); the other is shown as context", () => {
    const sq = opt(run(illustrativeReform()));
    expect(sq.rbe.total).toBe("-12724060");
    expect(sq.alternativeBaseline.rbe.total).toBe("1922340");
    const ni = run(illustrativeReform({ baseline: "noInstrument" }));
    expect(opt(ni).rbe.total).toBe("1922340");
    expect(cells(ni)[3]).toBe("$1.9");
    expect(opt(ni).alternativeBaseline.rbe.total).toBe("-12724060");
    expect(codes(run(illustrativeReform({ remakesSunsettingInstrument: true })))).toContain("W-21");
    expect(codes(run(illustrativeReform({ baseline: "noInstrument", remakesSunsettingInstrument: true })))).not.toContain("W-21");
  });
});
