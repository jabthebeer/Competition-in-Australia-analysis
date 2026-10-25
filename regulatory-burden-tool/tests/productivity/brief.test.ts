// Policy brief schema (P0 of docs/forward_plan_policy_costing.md). All briefs here are ILLUSTRATIVE (synthetic).
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { computeProposal, rbeTable } from "../../src/engine/index";
import {
  BRIEF_WARNINGS,
  BriefValidationError,
  CHANNELS,
  CHANNEL_IDS,
  OVERLAP_RULES,
  PolicyBriefSchema,
  SUBDIVISION_RANGES,
  briefWarnings,
  central,
  channelsFor,
  covers,
  divisionOf,
  leverReach,
  overlaps,
  parseBrief,
} from "../../src/productivity/index";
import { illustrativeReform, pop } from "../engine/helpers";

const root = join(import.meta.dirname, "..", "..");
type Obj = Record<string, unknown>;

/** A minimal valid brief; `extra` is merged at the top level, `levers` replaces the lever block. */
function brief(extra: Obj = {}, levers?: Obj): Obj {
  return {
    schemaVersion: 1,
    kind: "policy-brief",
    id: "test-brief",
    meta: { title: "Test brief (illustrative, synthetic)", jurisdictions: ["CTH"], startYear: 2027 },
    scope: { industries: [{ anzsic: "E" }, { anzsic: "M" }] },
    ...(levers ? { levers } : {}),
    ...extra,
  };
}

const issues = (input: unknown): string[] => {
  try {
    parseBrief(input);
    return [];
  } catch (e) {
    if (e instanceof BriefValidationError) return e.issues;
    throw e;
  }
};

describe("policy brief schema", () => {
  it("T-BRF-01 a minimal brief parses with the plan's defaults", () => {
    const b = parseBrief(brief());
    expect(b.meta).toMatchObject({ proposalType: "reform", phaseInYears: 0, durationYears: 10, priceBase: "2025-26" });
    expect(b.scope.sizeBands).toEqual(["nonEmploying", "1-4", "5-19", "20-199", "200+"]);
    expect(b.scope.entityTypes).toEqual(["private"]);
    expect(b.scope.industries[0]).toMatchObject({ anzsic: "E", exposure: 1, role: "direct" });
    expect(b.levers).toEqual({ thresholds: [], custom: [] });
    // OIA CBA guidance: 7% real, with 3% and 10% sensitivity (plan §2, D-4).
    expect(b.analysis).toEqual({ realisationFactor: 1, discountRate: 0.07, sensitivityRates: [0.03, 0.1], showUngatedEconomyWide: false, draws: 2000, seed: 1 });
  });

  it("T-BRF-02 unknown keys are rejected everywhere (strict objects)", () => {
    expect(issues(brief({ discountRate: 0.05 })).join()).toMatch(/discountRate/);
    expect(issues(brief({}, { entry: { approvalTimeChangeDays: -10, benefit: 5 } })).join()).toMatch(/benefit/);
    expect(issues(brief({ kind: "proposal" })).length).toBeGreaterThan(0);
    expect(issues(brief({ schemaVersion: 2 })).length).toBeGreaterThan(0);
  });

  it("T-BRF-03 lever changes are signed numbers or ordered ranges; the central value is the midpoint", () => {
    expect(issues(brief({}, { entry: { costPerEntrantChangeDollars: -500 } }))).toEqual([]);
    expect(issues(brief({}, { entry: { costPerEntrantChangeDollars: { low: -600, high: -200 } } }))).toEqual([]);
    expect(issues(brief({}, { entry: { costPerEntrantChangeDollars: { low: 5, high: 1 } } })).join()).toMatch(/low value must not exceed/);
    expect(issues(brief({}, { entry: { costPerEntrantChangeDollars: Number.POSITIVE_INFINITY } }))).toEqual(["levers.entry.costPerEntrantChangeDollars: Invalid input"]);
    expect(central(-500)).toBe(-500);
    expect(central({ low: -600, high: -200 })).toBe(-400);
  });

  it("T-BRF-04 scope industries are listed once, and a code inside another is rejected", () => {
    const scope = (codes: string[]) => brief({ scope: { industries: codes.map((anzsic) => ({ anzsic })) } });
    expect(issues(scope(["E", "M", "4511"]))).toEqual([]);
    expect(issues(scope(["E", "E"])).join()).toMatch(/listed twice/);
    expect(issues(scope(["E", "3231"])).join()).toMatch(/E and 3231 overlap/);
    expect(issues(scope(["32", "323"])).join()).toMatch(/32 and 323 overlap/);
    expect(issues(scope(["3231", "3232"]))).toEqual([]);
    expect(issues(scope(["Z"])).join()).toMatch(/ANZSIC/);
  });

  it("T-BRF-05 lever industries must lie within the scope; leverReach defaults to the scope", () => {
    expect(issues(brief({}, { entry: { industries: ["3232"], approvalTimeChangeDays: -30 } }))).toEqual([]);
    expect(issues(brief({}, { entry: { industries: ["G"], approvalTimeChangeDays: -30 } })).join()).toMatch(/levers\.entry\.industries\.0: Industry G is outside/);
    const b = parseBrief(brief({}, { entry: { approvalTimeChangeDays: -30 }, trade: { industries: ["69"], tariffChangePp: -5 } }));
    expect(leverReach(b)).toEqual([
      { block: "entry", industries: ["E", "M"] },
      { block: "trade", industries: ["69"] },
    ]);
    // A part that names no industries reaches the whole scope, even when another part of the same block names some.
    const labour = parseBrief(brief({}, { labour: { licensing: { occupations: ["381231"], industries: ["3232"], stringencyChange: -0.5 }, nonCompetes: { coveredShareChange: -0.2 } } }));
    expect(leverReach(labour)).toEqual([{ block: "labour", industries: ["3232", "E", "M"] }]);
  });

  it("T-BRF-06 the conduct lever takes one route: mark-up (C6) or PMR indicator (C7), never both (O-3)", () => {
    expect(issues(brief({}, { conduct: { route: "markup", markupChangePct: { low: -2, high: -0.5 } } }))).toEqual([]);
    expect(issues(brief({}, { conduct: { route: "pmr", indicator: "barriersServiceSectors", from: 1.91, to: 1.6 } }))).toEqual([]);
    expect(issues(brief({}, { conduct: { route: "markup", markupChangePct: -1, indicator: "energy" } })).join()).toMatch(/indicator/);
    expect(issues(brief({}, { conduct: { route: "pmr", indicator: "energy", from: 7, to: 1 } })).join()).toMatch(/from/);
    expect(issues(brief({}, { conduct: { route: "both", markupChangePct: -1 } })).length).toBeGreaterThan(0);
  });

  it("T-BRF-07 thresholds: a move needs a different previous value; ids are unique", () => {
    const t = (extra: Obj) => ({ id: "t1", metric: "employees", change: "move", value: 20, previousValue: 15, costAbovePerYearDollars: 1200, ...extra });
    expect(issues(brief({}, { thresholds: [t({})] }))).toEqual([]);
    expect(issues(brief({}, { thresholds: [t({ previousValue: undefined })] })).join()).toMatch(/previous value/);
    expect(issues(brief({}, { thresholds: [t({ previousValue: 20 })] })).join()).toMatch(/different/);
    expect(issues(brief({}, { thresholds: [t({ change: "introduce" })] })).join()).toMatch(/only applies when a threshold is moved/);
    expect(issues(brief({}, { thresholds: [t({}), t({})] })).join()).toMatch(/Duplicate threshold id/);
    expect(parseBrief(brief({}, { thresholds: [t({})] })).levers.thresholds[0]!.design).toBe("cliff");
  });

  it("T-BRF-08 a lever block must change something", () => {
    for (const block of ["entry", "capital", "labour", "innovation", "trade"]) {
      expect(issues(brief({}, { [block]: {} })).join(), block).toMatch(/needs at least one of/);
    }
  });

  it("T-BRF-09 a company tax change cannot also be its own funding tax (overlap rule O-5)", () => {
    const capital = { companyTaxRate: { from: 0.3, to: 0.25 } };
    expect(issues(brief({}, { capital, fiscal: { revenueChangeDollarsPerYear: 5e9, fundingTax: "labourIncome" } }))).toEqual([]);
    expect(issues(brief({}, { capital, fiscal: { revenueChangeDollarsPerYear: 5e9, fundingTax: "companyIncome" } })).join()).toMatch(/O-5/);
    expect(issues(brief({}, { capital: { companyTaxRate: { from: 30, to: 25 } } })).length).toBeGreaterThan(0); // shares, not per cent
  });

  it("T-BRF-10 custom shocks: in scope, of a type the channel produces, and explicit when a lever already feeds them (O-6)", () => {
    const shock = (extra: Obj) => ({ id: "s1", channel: "C9", industry: "69", type: "mfp", size: 0.1, justification: "Illustrative", ...extra });
    expect(issues(brief({}, { custom: [shock({})] }))).toEqual([]);
    expect(issues(brief({}, { custom: [shock({ industry: "G" })] })).join()).toMatch(/outside the brief's scope/);
    expect(issues(brief({}, { custom: [shock({ type: "rent" })] })).join()).toMatch(/C9 produces mfp, not rent/);
    expect(issues(brief({}, { custom: [shock({ channel: "C12", type: "rent" })] }))).toEqual([]);
    const withLever = { innovation: { rdUserCostChangePct: -10 } };
    expect(issues(brief({}, { ...withLever, custom: [shock({})] })).join()).toMatch(/replaces it or adds to it/);
    expect(issues(brief({}, { ...withLever, custom: [shock({ relation: "replaces" })] }))).toEqual([]);
    expect(issues(brief({}, { custom: [shock({}), shock({})] })).join()).toMatch(/Duplicate custom shock id/);
  });

  it("T-BRF-11 meta checks: phase-in, duration over 10 years, jurisdictions and states", () => {
    const meta = (extra: Obj) => brief({ meta: { title: "t", jurisdictions: ["CTH"], startYear: 2027, ...extra } });
    expect(issues(meta({ phaseInYears: 12 })).join()).toMatch(/phase-in/);
    expect(issues(meta({ durationYears: 15 })).join()).toMatch(/RBM p\. 6/);
    expect(issues(meta({ durationYears: 15, durationOverride: { justification: "Asset life", source: { description: "Illustrative" } } }))).toEqual([]);
    expect(issues(meta({ jurisdictions: ["NSW", "NSW"] })).join()).toMatch(/listed twice/);
    const state = brief({ meta: { title: "t", jurisdictions: ["VIC"], startYear: 2027 }, scope: { industries: [{ anzsic: "E" }], states: ["NSW"] } });
    expect(issues(state).join()).toMatch(/NSW is not one of the brief's jurisdictions/);
    expect(issues(meta({ startYear: 1990 })).length).toBeGreaterThan(0);
  });

  it("T-BRF-12 the burden proposal is the RBM proposal, unchanged: same defaults and the same RBE", () => {
    const proposal = illustrativeReform();
    const b = parseBrief(brief({ burden: proposal }));
    const direct = computeProposal(proposal);
    const viaBrief = computeProposal(b.burden!);
    expect(rbeTable(viaBrief.options[0]!.rbe, 1).cells).toEqual(rbeTable(direct.options[0]!.rbe, 1).cells);
    expect(b.burden!.rates.work.hourly).toBe(91.54);
    expect(issues(brief({ burden: { ...proposal, durationYears: 5 } })).join()).toMatch(/runs 5 years but the brief 10/);
    expect(issues(brief({ burden: { ...proposal, populations: [] } })).join()).toMatch(/burden\.populations/);
  });

  it("T-BRF-13 warnings PB-01 to PB-04 flag problems that do not block costing", () => {
    const codes = (input: Obj) => briefWarnings(parseBrief(input)).map((w) => w.code);
    expect(codes(brief())).toEqual(["PB-01"]);
    const outside = illustrativeReform();
    outside.populations = [pop("biz", 10000, { industry: "G" })];
    expect(codes(brief({ burden: outside }))).toEqual(["PB-02"]);
    const shock = { id: "s1", channel: "C12", industry: "69", type: "mfp", size: 0.1, justification: "Illustrative" };
    expect(codes(brief({}, { custom: [shock] }))).toEqual(["PB-03"]);
    expect(codes(brief({}, { custom: [{ ...shock, source: { description: "A cited study" } }] }))).toEqual([]);
    const drafted = { approvalTimeChangeDays: -30, provenance: { approvalTimeChangeDays: { origin: "modelEstimate", note: "From the brief" } } };
    const w = briefWarnings(parseBrief(brief({}, { entry: drafted })));
    expect(w).toEqual([{ code: "PB-04", message: expect.stringContaining("levers.entry.approvalTimeChangeDays"), path: "levers.entry.approvalTimeChangeDays" }]);
    expect(Object.keys(BRIEF_WARNINGS)).toEqual(["PB-01", "PB-02", "PB-03", "PB-04"]);
  });

  it("T-BRF-14 the ANZSIC division table matches the bundled ABS codelist", () => {
    const codelist = JSON.parse(readFileSync(join(root, "..", "alicia", "src", "alicia", "data", "anzsic2006.json"), "utf8")) as {
      codelist: string;
      codes: { code: string; parent: string | null }[];
    };
    expect(codelist.codelist).toBe("CL_ANZSIC_2006 1.1.0");
    const parents = new Map(codelist.codes.map((c) => [c.code, c.parent]));
    const divisionAbove = (code: string): string => (code.length === 1 ? code : divisionAbove(parents.get(code)!));
    const subdivisions = codelist.codes.filter((c) => c.code.length === 2);
    expect(subdivisions.length).toBe(86);
    for (const c of codelist.codes.filter((x) => /^\d+$/.test(x.code))) expect(divisionOf(c.code), c.code).toBe(divisionAbove(c.code));
    expect(Object.keys(SUBDIVISION_RANGES)).toEqual("ABCDEFGHIJKLMNOPQRS".split(""));
    expect(covers("E", "3231")).toBe(true);
    expect(covers("32", "3231")).toBe(true);
    expect(covers("3231", "32")).toBe(false);
    expect(covers("E", "4511")).toBe(false);
    expect(overlaps("3231", "32")).toBe(true);
    expect(overlaps("3231", "3232")).toBe(false);
  });

  it("T-BRF-15 every channel is fed by a brief block, and the overlap rules name real channels", () => {
    expect(Object.keys(CHANNELS)).toEqual([...CHANNEL_IDS]);
    expect(channelsFor("burden")).toEqual(["C1", "C2"]);
    expect(channelsFor("entry")).toEqual(["C2", "C4"]);
    expect(channelsFor("conduct.markup")).toEqual(["C6"]);
    expect(channelsFor("conduct.pmr")).toEqual(["C7"]);
    for (const rule of OVERLAP_RULES) {
      for (const c of rule.channels) expect(c === "custom" || c === "any" || (CHANNEL_IDS as readonly string[]).includes(c), `${rule.id}: ${c}`).toBe(true);
    }
  });

  it("T-BRF-16 the synthetic test brief parses and its burden costs through the RBM engine", () => {
    const file = JSON.parse(readFileSync(join(root, "tests", "fixtures", "synthetic-licensing.json"), "utf8"));
    const b = parseBrief(file);
    expect(b.meta.title).toMatch(/^ILLUSTRATIVE/);
    expect(briefWarnings(b)).toEqual([]);
    const result = computeProposal(b.burden!);
    // Renewal: 10,000 businesses × 2 h × $91.54 every year, against once every three years → a saving.
    expect(Number(result.options[0]!.rbe.total.toString())).toBeLessThan(0);
    expect(leverReach(b).map((r) => r.block)).toEqual(["entry", "labour"]);
    expect(PolicyBriefSchema.safeParse({ ...file, levers: { ...file.levers, labour: { licensing: { occupations: ["3812"], stringencyChange: -0.5 } } } }).success).toBe(false);
  });

  it("T-BRF-17 the bundled example, the non-compete ban, parses without warnings and rebuilds the Impact Analysis's familiarisation costs", () => {
    const b = parseBrief(JSON.parse(readFileSync(join(root, "examples", "noncompete-ban.brief.json"), "utf8")));
    expect(briefWarnings(b)).toEqual([]);
    expect(b.scope.industries.map((i) => i.anzsic).join("")).toBe("ABCDEFGHIJKLMNOPQRS");
    const result = computeProposal(b.burden!);
    const tenYear = (id: string) => Number(result.options.find((o) => o.optionId === id)!.rbe.total.toString()) * 10;
    // Option 3 reproduces Treasury's $16.3 million (IA Table 4); Option 2 is three times as long, so three times as much.
    expect(tenYear("option-3-full-ban") / 1e6).toBeCloseTo(16.3, 1);
    expect(tenYear("option-2-partial-ban") / tenYear("option-3-full-ban")).toBeCloseTo(3, 6);
    expect(leverReach(b).map((r) => r.block)).toEqual(["labour"]);
  });
});
