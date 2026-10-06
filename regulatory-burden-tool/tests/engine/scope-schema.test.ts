import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import {
  ProposalValidationError,
  SCREENER,
  TagSchema,
  computeProposal,
  loadProposalFile,
  parseProposal,
  screen,
  toProposalFile,
} from "../../src/engine/index";
import { dec, sum } from "../../src/engine/decimal";
import { delayLine, illustrativeReform, labour, ob, opt, option, pop, proposal, purchase, run, side } from "./helpers";

const justified = { justification: "Illustrative: demonstrated as enforcement", source: { description: "Illustrative" } };

/** Each variant adds one item that the framework excludes; the RBE must not move. */
const EXCLUDED_VARIANTS: { name: string; reason: string; obligation: object; population?: object }[] = [
  { name: "enforcement", reason: "enforcement", obligation: ob("x-enf", "substantive", null, side("purchase", [purchase("biz", 123, 1)]), { scope: { classification: "enforcement", override: justified } }) },
  { name: "government fee (amount)", reason: "directFinancialCost", obligation: ob("x-fee", "substantive", null, side("purchase", [purchase("biz", 50, 1)]), { tags: ["governmentFee"] }) },
  { name: "tax", reason: "directFinancialCost", obligation: ob("x-tax", "substantive", null, side("purchase", [purchase("biz", 70, 1)]), { tags: ["tax"] }) },
  { name: "fine", reason: "nonCompliance", obligation: ob("x-fine", "substantive", null, side("purchase", [purchase("biz", 900, 1)]), { tags: ["fine"] }) },
  { name: "indirect / competition", reason: "indirect", obligation: ob("x-ind", "substantive", null, side("purchase", [purchase("biz", 400, 1)]), { tags: ["indirectEffect"] }) },
  { name: "court administration", reason: "courtAdministration", obligation: ob("x-court", "administrative", null, side("labour", [labour("biz", 3, 1)]), { tags: ["courtAdministration"] }) },
  { name: "international obligation", reason: "internationalObligation", obligation: ob("x-intl", "substantive", null, side("purchase", [purchase("biz", 800, 1)]), { tags: ["internationalObligation"] }) },
  { name: "opportunity cost", reason: "opportunityCost", obligation: ob("x-opp", "substantive", null, side("purchase", [purchase("biz", 300, 1)]), { tags: ["opportunityCost"] }) },
  { name: "government agency", reason: "governmentToGovernment", obligation: ob("x-g2g", "administrative", null, side("labour", [labour("agency", 5, 4)])), population: pop("agency", 50, { entityType: "governmentAgency" }) },
  { name: "sunk current cost", reason: "sunk", obligation: ob("x-sunk", "substantive", side("purchase", [purchase("biz", 5000, 1)], { type: "oneOff" }, { status: "alreadyIncurred" }), null) },
  { name: "delay not waiting on government", reason: "delayNotWaitingOnGovernment", obligation: ob("x-delay", "delay", null, side("delay", [delayLine("biz", { approvalDelay: 3, netIncomePerUnit: 1000, waitingOnGovernment: false })])) },
  { name: "state item, Commonwealth-only", reason: "stateInCommonwealthOnly", obligation: ob("x-state", "substantive", null, side("purchase", [purchase("biz", 60, 1)]), { jurisdiction: "stateTerritory" }) },
];

describe("Scope and exclusions (RBM pp. 3-5, 10, 14-15)", () => {
  it("T-SCOPE-01 property: adding any excluded item leaves every RBE figure unchanged, and lists it with its reason", () => {
    const bases = [
      illustrativeReform(),
      proposal([pop("biz", 1000), pop("people", 500, { group: "individual" })], [
        option("o", [ob("a", "substantive", side("purchase", [purchase("biz", 10, 3)]), side("purchase", [purchase("biz", 4, 3)]), { doAnywayShare: 0.1 })]),
      ]),
    ];
    for (const base of bases) {
      const before = opt(run(base));
      for (const v of EXCLUDED_VARIANTS) {
        const p = structuredClone(base) as { populations: object[]; options: { obligations: object[] }[] };
        if (v.population) p.populations.push(v.population);
        p.options[0]!.obligations.push(v.obligation);
        const after = opt(run(p));
        expect(after.rbe, v.name).toEqual(before.rbe);
        expect(after.alternativeBaseline.rbe, v.name).toEqual(before.alternativeBaseline.rbe);
        expect(after.excluded.map((e) => e.reason), v.name).toContain(v.reason);
        expect(after.excluded.find((e) => e.reason === v.reason)?.ref, v.name).toMatch(/RBM/);
      }
    }
  });

  it("T-SCOPE-01b the time spent paying a fee (labour) stays in scope, although the amount doesn't", () => {
    const r = run(proposal([pop("biz", 1000)], [option("o", [ob("pay-fee", "administrative", null, side("labour", [labour("biz", 0.5, 1)]), { tags: ["governmentFee"] })])]));
    expect(opt(r).rbe.total).toBe("45770");
  });

  it("T-SCOPE-02 a 60/40 compliance/enforcement split counts 60% (Appendix 3)", () => {
    const r = run(proposal([pop("biz", 1000)], [option("o", [ob("mixed", "substantive", null, side("purchase", [purchase("biz", 1000, 1)]), { scope: { classification: "split", complianceShare: 0.6, override: justified } })])]));
    expect(opt(r).rbe.total).toBe("600000");
    expect(opt(r).excluded.find((e) => e.reason === "enforcement")?.annualAmount).toBe("400000");
  });

  it("T-SCOPE-03 the screener maps each answer to a scope outcome with a page reference", () => {
    const tags = new Set(TagSchema.options);
    for (const q of SCREENER) {
      expect(q.yes.ref).toMatch(/^(RBM|IA Framework)/);
      if (q.yes.suggestedTag) expect(tags.has(q.yes.suggestedTag)).toBe(true);
    }
    const out = screen({ feeToGovernment: true, waitingOnGovernment: false, fine: false });
    expect(out.find((o) => o.questionId === "feeToGovernment")).toMatchObject({ scope: "partly", ref: "RBM pp. 2, 4" });
    expect(out.find((o) => o.questionId === "waitingOnGovernment")).toMatchObject({ scope: "out", ref: "RBM p. 10" });
    expect(out.find((o) => o.questionId === "fine")).toBeUndefined(); // "no" to an exclusion keeps the default
  });
});

describe("Exact arithmetic, schema versioning, determinism", () => {
  it("T-NUM-01 money arithmetic is exact: no floating-point residue in totals", () => {
    expect(0.1 * 3).not.toBe(0.3); // binary floating point would drift
    const r = run(proposal([pop("biz", 3)], [option("o", [ob("tiny", "substantive", null, side("purchase", [purchase("biz", 0.1, 1)]))])]));
    expect(opt(r).rbe.total).toBe("0.3");
    const many = run(proposal([pop("biz", 1)], [option("o", Array.from({ length: 10 }, (_, i) => ob(`c${i}`, "substantive", null, side("purchase", [purchase("biz", 0.1, 1)]))))]));
    expect(opt(many).rbe.total).toBe("1");
    const thirds = opt(run(proposal([pop("biz", 1)], [option("o", [ob("buy", "substantive", null, side("purchase", [purchase("biz", 1000000, 1)], { type: "oneOff" }))])], { durationYears: 3, durationOverride: justified })));
    expect(dec(thirds.rbe.total).times(3).minus(1000000).abs().lessThan("1e-30")).toBe(true);
    const o = opt(run(illustrativeReform()));
    const items = sum(o.items.map((i) => dec(i.deltaAnnual)));
    expect(items.equals(dec(o.rbe.total))).toBe(true);
  });

  it("T-SCH-01 versioned files round-trip; newer and unversioned files are rejected with clear messages; migrations run", () => {
    const p = parseProposal(illustrativeReform());
    const file = JSON.parse(JSON.stringify(toProposalFile(p, "2026-10-06T00:00:00Z")));
    expect(loadProposalFile(file).proposal).toEqual(p);
    expect(() => loadProposalFile({ ...file, schemaVersion: 2 })).toThrow(/newer version/);
    expect(() => loadProposalFile({ proposal: p })).toThrow(/no schemaVersion/);
    expect(() => loadProposalFile({ ...file, schemaVersion: 0 })).toThrow(/no migration from v0/);
    // Synthetic v0 format (title was called "name") to exercise the migration registry.
    const { title, ...rest } = p;
    const v0 = { schemaVersion: 0, proposal: { ...rest, name: title } };
    const migrations = {
      0: (f: Record<string, unknown>) => {
        const { name, ...prop } = f.proposal as Record<string, unknown>;
        return { schemaVersion: 1, proposal: { ...prop, title: name } };
      },
    };
    expect(loadProposalFile(v0, migrations).proposal).toEqual(p);
    expect(() => loadProposalFile(v0, { 0: (f) => f })).toThrow(/did not produce v1/);
    try {
      parseProposal({ id: "x", title: "t", populations: [], options: [] });
    } catch (e) {
      expect(e).toBeInstanceOf(ProposalValidationError);
      expect((e as ProposalValidationError).issues.length).toBeGreaterThan(0);
    }
  });

  it("T-SCH-02 the engine is deterministic and pure (no I/O, clock, randomness or UI imports)", () => {
    const a = JSON.stringify(computeProposal(illustrativeReform()));
    const b = JSON.stringify(computeProposal(illustrativeReform()));
    expect(a).toBe(b);
    const dir = join(__dirname, "../../src/engine");
    for (const f of readdirSync(dir)) {
      const src = readFileSync(join(dir, f), "utf8");
      expect(src, f).not.toMatch(/from "node:|from "fs"|from "react|Date\.now|new Date\(|Math\.random|fetch\(/);
    }
  });

  it("T-SCH-03 structural errors are reported: unknown population, wrong cost block, schedule length", () => {
    const bad = proposal([pop("biz", 1)], [
      option("o", [
        ob("a", "administrative", null, side("labour", [labour("nobody", 1, 1)])),
        ob("b", "administrative", null, side("labour", [purchase("biz", 1, 1)])),
        ob("c", "substantive", null, side("purchase", [purchase("biz", 1, 1)], { type: "schedule", factors: [1, 1] })),
      ]),
    ]);
    try {
      parseProposal(bad);
      expect.unreachable();
    } catch (e) {
      const issues = (e as ProposalValidationError).issues.join("\n");
      expect(issues).toMatch(/Unknown population "nobody"/);
      expect(issues).toMatch(/exactly one cost block/);
      expect(issues).toMatch(/exactly 10 values/);
    }
  });
});
