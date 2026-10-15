import { describe, expect, it } from "vitest";
import { computeProposal, parseProposal, type Obligation, type Proposal } from "../../src/engine/index";
import {
  addCurrentObligation,
  addOption,
  changeCostType,
  currentObligations,
  newObligation,
  newProposal,
  populationBlockers,
  rebaseReformed,
  reformStatus,
  removePopulation,
  setReformStatus,
  toggleLine,
  updateCurrentObligation,
  updateOptionObligation,
  addPopulation,
  setProposalType,
  setDuration,
  describeIssue,
} from "../../src/ui/model";

// All values ILLUSTRATIVE.
function withReport(type: Proposal["proposalType"] = "reform"): { p: Proposal; id: string } {
  let p = newProposal(type);
  p.populations[0]!.count = 10000;
  const ob = newObligation("administrative", p.populations, "current", "Report");
  ob.current!.lines[0]!.labour = { hours: 4, timesPerYear: 4, staff: 1, rateId: "work" };
  p = addCurrentObligation(p, ob);
  return { p, id: ob.id };
}

describe("UI model helpers", () => {
  it("T-UI-01 new proposals of every type are valid and start at zero", () => {
    for (const type of ["reform", "new", "repeal"] as const) {
      const p = newProposal(type);
      expect(() => parseProposal(p)).not.toThrow();
      expect(computeProposal(p).options.every((o) => o.rbe.total === "0")).toBe(true);
    }
    expect(newProposal("reform").options.map((o) => o.name)).toEqual(["Option A: reformed regulation", "Status quo"]);
  });

  it("T-UI-02 the current regime is shared by every option; 'keep' copies follow edits; repeal options remove", () => {
    const { p, id } = withReport();
    expect(currentObligations(p)).toHaveLength(1);
    expect(p.options.every((o) => reformStatus(o.obligations[0]!) === "keep")).toBe(true);
    const edited = updateCurrentObligation(p, id, (o) => (o.current!.lines[0]!.labour!.hours = 5));
    expect(edited.options.every((o) => o.obligations[0]!.reformed!.lines[0]!.labour!.hours === 5)).toBe(true);
    expect(computeProposal(edited).options.every((o) => o.rbe.total === "0")).toBe(true);
    const repeal = withReport("repeal").p;
    expect(reformStatus(repeal.options[0]!.obligations[0]!)).toBe("remove");
    expect(reformStatus(repeal.options[1]!.obligations[0]!)).toBe("keep"); // status quo
  });

  it("T-UI-03 a reformed side follows the current one except for the fields the reform changed", () => {
    const { p, id } = withReport();
    const optId = p.options[0]!.id;
    let q = setReformStatus(p, optId, id, "modify");
    q = updateOptionObligation(q, optId, id, (o) => {
      o.reformed!.lines[0]!.labour!.hours = 2;
      o.reformed!.lines[0]!.labour!.timesPerYear = 1;
      o.levers = ["lessFrequent", "simplerForm"];
    });
    expect(computeProposal(q).options[0]!.rbe.total).toBe("-12815600");
    // Staff changes in the current regime flow through; the reformed hours and frequency don't.
    const q2 = updateCurrentObligation(q, id, (o) => {
      o.current!.lines[0]!.labour!.staff = 2;
      o.current!.lines[0]!.labour!.hours = 5;
    });
    const ref = q2.options[0]!.obligations[0]!.reformed!.lines[0]!.labour!;
    expect(ref).toEqual({ hours: 2, timesPerYear: 1, staff: 2, rateId: "work" });
    // A reform that changes the timing pattern keeps its own timing.
    const ob = q2.options[0]!.obligations[0]! as Obligation;
    const rebased = rebaseReformed(ob.current!, { ...ob.reformed!, timing: { type: "everyKYears", k: 2, firstYear: 1 } }, { ...ob.current!, timing: { type: "ongoing", startYear: 2 } });
    expect(rebased.timing).toEqual({ type: "everyKYears", k: 2, firstYear: 1 });
  });

  it("T-UI-04 keep, modify and remove statuses", () => {
    const { p, id } = withReport();
    const optId = p.options[0]!.id;
    expect(reformStatus(setReformStatus(p, optId, id, "remove").options[0]!.obligations[0]!)).toBe("remove");
    expect(reformStatus(setReformStatus(p, optId, id, "modify").options[0]!.obligations[0]!)).toBe("modify");
    const back = setReformStatus(setReformStatus(p, optId, id, "remove"), optId, id, "keep");
    expect(reformStatus(back.options[0]!.obligations[0]!)).toBe("keep");
    const withRepeal = addOption(p, "Outright repeal", "repeal");
    expect(withRepeal.options.map((o) => o.name)).toEqual(["Option A: reformed regulation", "Outright repeal", "Status quo"]);
    expect(computeProposal(withRepeal).options[1]!.rbe.total).toBe("-14646400");
  });

  it("T-UI-05 populations: a group an obligation relies on can't be removed; lines toggle per group", () => {
    let { p } = withReport();
    expect(populationBlockers(p, "pop-1")).toEqual(["Report"]);
    p = addPopulation(p);
    expect(removePopulation(p, "pop-1")).toBe(p);
    const side = p.options[0]!.obligations[0]!.current!;
    const two = toggleLine(side, p.populations[1]!, true);
    expect(two.lines).toHaveLength(2);
    expect(toggleLine(toggleLine(two, p.populations[0]!, false), p.populations[1]!, false).lines).toHaveLength(1);
  });

  it("T-UI-06 changing the cost type keeps who it applies to and the compliance rate", () => {
    const { p } = withReport();
    const side = p.options[0]!.obligations[0]!.current!;
    side.lines[0]!.complianceRate = 0.9;
    const purchase = changeCostType(side, "purchase", p.populations);
    expect(purchase.costType).toBe("purchase");
    expect(purchase.lines[0]).toMatchObject({ populationId: "pop-1", complianceRate: 0.9, purchase: { unitCost: 0, timesPerYear: 1 } });
    expect(purchase.lines[0]!.labour).toBeUndefined();
  });

  it("T-UI-07 changing the proposal type resets the default options only while nothing has been entered", () => {
    const fresh = setProposalType(newProposal("reform"), "repeal");
    expect(fresh.options.map((o) => o.name)).toEqual(["Outright repeal", "Status quo"]);
    expect(setProposalType(fresh, "new").options.map((o) => o.name)).toEqual(["Proposed regulation"]);
    const { p } = withReport();
    expect(setProposalType(p, "repeal").options.map((o) => o.name)).toEqual(p.options.map((o) => o.name));
  });

  it("T-UI-08 shortening the period resizes year-by-year schedules; issues are described in plain language", () => {
    let { p, id } = withReport();
    p = updateCurrentObligation(p, id, (o) => (o.current!.timing = { type: "schedule", factors: Array.from({ length: 10 }, () => 1) }));
    const short = setDuration(p, 4);
    expect(short.options[0]!.obligations[0]!.current!.timing).toEqual({ type: "schedule", factors: [1, 1, 1, 1] });
    expect(() => parseProposal({ ...short, durationOverride: { justification: "x", source: { description: "x" } } })).not.toThrow();
    expect(describeIssue(p, "options.0.obligations.0.reformed.lines.0.labour.hours: Too small")).toBe("Option A: reformed regulation › Report (reformed version) › Affected businesses › labour hours: Too small");
    expect(describeIssue(p, "populations.0.count: Expected number")).toBe("Affected businesses › count: Expected number");
  });
});
