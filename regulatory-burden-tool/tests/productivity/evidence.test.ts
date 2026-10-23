// Evidence library (P3 of docs/forward_plan_policy_costing.md): schema, library rules, coverage of the
// traceability formulas, the Cowork review sheet and the Sources page.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  EVIDENCE,
  EVIDENCE_FILES,
  EvidenceEntrySchema,
  PolicyBriefSchema,
  REVIEW_CHECK_COLUMNS,
  REVIEW_SHEET_COLUMNS,
  defaultEvidence,
  entryFormulas,
  evidenceByChannel,
  evidenceEntryIssues,
  evidenceFor,
  evidenceIdPrefix,
  evidenceReviewCsv,
  libraryIssues,
  loadEvidence,
  parseCsv,
  reviewSheetRows,
  toCsv,
  type EvidenceEntry,
  type EvidenceEntryInput,
} from "../../src/productivity/index";
import { SourcesPage, formatEvidenceNumber } from "../../src/ui/pages/SourcesPage";

const root = join(import.meta.dirname, "..", "..");
const traceability = readFileSync(join(root, "docs", "productivity_traceability.md"), "utf8");
const briefSource = readFileSync(join(root, "src", "productivity", "brief.ts"), "utf8");
const sheetPath = join(root, "..", "docs", "review", "evidence_library_review.csv");

/** A valid entry to vary in the rule tests (synthetic, not in the library). */
function entry(over: Partial<EvidenceEntryInput> = {}): EvidenceEntryInput {
  return {
    id: "c3.sigma.test",
    formula: "F-C3-02",
    parameter: "sigma",
    channel: "C3",
    label: "Test entry (synthetic)",
    value: 0.4,
    low: 0.2,
    high: 0.6,
    units: "elasticity",
    rangeBasis: "plusMinus50",
    country: "Nowhere",
    method: "structural",
    grade: "B",
    tag: "P",
    citation: { authors: "A. Author", year: 2020, title: "A title", publisher: "A journal", url: "https://example.org/paper", locator: "Table 1, p. 3" },
    quote: "an exact quote",
    derivation: "From Table 1.",
    isDefault: true,
    review: { status: "draft" },
    ...over,
  };
}
const parsed = (over: Partial<EvidenceEntryInput> = {}): EvidenceEntry => EvidenceEntrySchema.parse(entry(over));

/**
 * Every parameter of the formulas in productivity_traceability.md §2.3–2.5, and where its value comes from:
 * - library: the evidence library holds exactly one default;
 * - brief: a policy brief field (named in `field`, checked against brief.ts);
 * - data: the parameter pipeline (P2) supplies it by industry;
 * - user: the user must enter it; there is no default and no brief field yet (P4 adds the input).
 * PR-06 (§2.1) is listed because the library holds the OIA discount rates.
 */
type Source = "library" | "brief" | "data" | "user";
const REQUIRED: { formula: string; parameter: string; source: Source; field?: string }[] = [
  // §2.3 Layer A
  { formula: "F-C1-01", parameter: "deltaC", source: "brief", field: "burden" },
  { formula: "F-C1-01", parameter: "gva", source: "data" },
  { formula: "F-C1-02", parameter: "s", source: "library" },
  { formula: "F-C2-01", parameter: "r", source: "library" },
  { formula: "F-C2-01", parameter: "d", source: "brief", field: "approvalTimeChangeDays" },
  { formula: "F-C2-01", parameter: "d", source: "brief", field: "investmentApprovalDelayChangeMonths" },
  { formula: "F-C3-01", parameter: "r", source: "library" },
  { formula: "F-C3-01", parameter: "tau", source: "brief", field: "companyTaxRate" },
  { formula: "F-C3-01", parameter: "z", source: "brief", field: "depreciationPvChange" },
  { formula: "F-C3-01", parameter: "riskPremium", source: "brief", field: "riskPremiumChangePp" },
  { formula: "F-C3-01", parameter: "delta", source: "data" },
  { formula: "F-C3-02", parameter: "sigma", source: "library" },
  { formula: "F-C3-03", parameter: "alpha", source: "library" },
  { formula: "F-C4-01", parameter: "epsilon", source: "library" },
  { formula: "F-C4-01", parameter: "entryCostShareAU", source: "library" },
  { formula: "F-C4-01", parameter: "entryCostChange", source: "brief", field: "costPerEntrantChangeDollars" },
  { formula: "F-C4-01", parameter: "gdpPerHead", source: "data" },
  { formula: "F-C4-02", parameter: "excludedShare", source: "brief", field: "excludedEntrantShare" },
  { formula: "F-C4-02", parameter: "baselineEntryRate", source: "data" },
  { formula: "F-C4-03", parameter: "beta2", source: "library" },
  { formula: "F-C4-03", parameter: "gap", source: "user" },
  { formula: "F-C5-01", parameter: "band", source: "library" },
  { formula: "F-C5-01", parameter: "threshold", source: "brief", field: "ThresholdLeverSchema" },
  { formula: "F-C5-01", parameter: "firmsNearThreshold", source: "data" },
  { formula: "F-C5-02", parameter: "lowerBound", source: "library" },
  { formula: "F-C5-02", parameter: "upperBound", source: "library" },
  { formula: "F-C5-02", parameter: "labourTaxEquivalent", source: "library" },
  { formula: "F-C5-02", parameter: "bunchingBelow", source: "library" },
  { formula: "F-C5-02", parameter: "bunchingAbove", source: "library" },
  { formula: "F-C5-02", parameter: "payrollResponseAbove", source: "library" },
  { formula: "F-C5-02", parameter: "costAbove", source: "brief", field: "costAbovePerYearDollars" },
  { formula: "F-C5-02", parameter: "employmentNearThreshold", source: "data" },
  { formula: "F-C6-01", parameter: "markupFrom", source: "library" },
  { formula: "F-C6-01", parameter: "markupTo", source: "library" },
  { formula: "F-C6-01", parameter: "misallocationCostChange", source: "library" },
  { formula: "F-C6-01", parameter: "markupChange", source: "brief", field: "markupChangePct" },
  { formula: "F-C7-01", parameter: "beta", source: "library" },
  { formula: "F-C7-01", parameter: "etcrChange", source: "brief", field: "PmrIndicatorSchema" },
  { formula: "F-C7-02", parameter: "betaKY", source: "library" },
  { formula: "F-C8-01", parameter: "elasticity", source: "library" },
  { formula: "F-C8-01", parameter: "pcStringencyCut", source: "library" },
  { formula: "F-C8-01", parameter: "stringencyChange", source: "brief", field: "stringencyChange" },
  { formula: "F-C8-01", parameter: "licensedEmploymentShare", source: "data" },
  { formula: "F-C8-02", parameter: "passThrough", source: "library" },
  { formula: "F-C8-02", parameter: "wageEffectHighUse", source: "library" },
  { formula: "F-C8-02", parameter: "wageEffectLowUse", source: "library" },
  { formula: "F-C8-02", parameter: "coverageChange", source: "brief", field: "coveredShareChange" },
  { formula: "F-C9-01", parameter: "epsilonShortRun", source: "library" },
  { formula: "F-C9-01", parameter: "epsilonLongRun", source: "library" },
  { formula: "F-C9-01", parameter: "rdUserCostChange", source: "brief", field: "rdUserCostChangePct" },
  { formula: "F-C9-02", parameter: "beta", source: "library" },
  { formula: "F-C10-01", parameter: "beta", source: "library" },
  { formula: "F-C10-01", parameter: "opennessChange", source: "brief", field: "opennessChangePp" },
  { formula: "F-C10-02", parameter: "gdpEffect", source: "library" },
  { formula: "F-C10-03", parameter: "elasticity", source: "library" },
  { formula: "F-C10-03", parameter: "fdiRestrictivenessChange", source: "brief", field: "fdiRestrictivenessChangePct" },
  ...["companyIncome", "labourIncome", "personalIncome", "gstCurrentBase", "gstBroadBase", "conveyancingDuty", "landTax"].map((tax) => ({
    formula: "F-C11-01",
    parameter: `meb.${tax}`,
    source: "library" as const,
  })),
  { formula: "F-C11-01", parameter: "meb.other", source: "user" },
  { formula: "F-C11-01", parameter: "revenue", source: "brief", field: "revenueChangeDollarsPerYear" },
  // §2.4 Layer B
  { formula: "F-B-01", parameter: "gdpPerLp", source: "library" },
  { formula: "F-B-01", parameter: "wageBillWeights", source: "data" },
  { formula: "F-B-02", parameter: "alpha", source: "library" },
  { formula: "F-B-02", parameter: "gvaWeights", source: "data" },
  { formula: "F-B-04", parameter: "ecmSpeedMfp", source: "library" },
  { formula: "F-B-04", parameter: "ecmSpeedKY", source: "library" },
  { formula: "F-B-04", parameter: "fiveYearShare", source: "library" },
  { formula: "F-B-04", parameter: "tenYearShare", source: "library" },
  { formula: "F-B-04", parameter: "phaseIn", source: "brief", field: "phaseInYears" },
  { formula: "F-B-05", parameter: "tolerance", source: "library" },
  { formula: "F-B-05", parameter: "modelErrorLp", source: "library" },
  { formula: "F-B-05", parameter: "modelErrorMfp", source: "library" },
  // §2.5 Uncertainty, overlaps and the gate
  { formula: "F-U-01", parameter: "draws", source: "brief", field: "draws" },
  { formula: "F-U-01", parameter: "seed", source: "brief", field: "seed" },
  { formula: "F-U-02", parameter: "halfWidth", source: "library" },
  { formula: "F-U-03", parameter: "realisationFactor", source: "library" },
  { formula: "F-U-03", parameter: "realisationFactor", source: "brief", field: "realisationFactor" },
  { formula: "F-G-01", parameter: "threshold", source: "library" },
  { formula: "F-G-01", parameter: "showUngated", source: "brief", field: "showUngatedEconomyWide" },
  // §2.1, held in general.json
  { formula: "PR-06", parameter: "discountRate", source: "library" },
];
/** Rules in §2.3–2.5 with no numeric parameter of their own. */
const NO_PARAMETER = ["F-C1-03", "F-C2-02", "F-C4-04", "F-C7-03", "F-B-03", "F-B-06", "F-O-01"];

/** Formula ids in the tables of traceability §2.3–2.5. */
function tracedFormulas(): string[] {
  const start = traceability.indexOf("### 2.3");
  const end = traceability.indexOf("## 3.", start);
  const section = traceability.slice(start, end);
  return [...new Set([...section.matchAll(/^\| (F-[A-Z0-9]+-\d{2}) \|/gm)].map((m) => m[1]!))];
}

describe("evidence library", () => {
  it("T-EVD-01 every bundled file parses with the strict schema, and unknown keys are rejected", () => {
    const { entries, issues } = loadEvidence(EVIDENCE_FILES);
    expect(issues).toEqual([]);
    expect(entries.length).toBe(EVIDENCE.length);
    expect(EVIDENCE.length).toBeGreaterThanOrEqual(50);
    expect(evidenceEntryIssues(entry())).toEqual([]);
    expect(evidenceEntryIssues({ ...entry(), confidence: "high" }).join()).toMatch(/confidence/);
    expect(evidenceEntryIssues(entry({ citation: { ...entry().citation, doi: "10.1/x" } as never })).join()).toMatch(/doi/);
    expect(evidenceEntryIssues(entry({ method: "guess" as never })).length).toBeGreaterThan(0);
    // A broken file reports the file name.
    expect(loadEvidence({ "bad.json": { channel: "C3", entries: [{ ...entry(), grade: "E" }] } }).issues.join()).toMatch(/^bad\.json: entries\.0\.grade/);
  });

  it("T-EVD-02 ids are unique, stable in form, and start with their channel; each file holds one channel", () => {
    const ids = EVIDENCE.map((e) => e.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const e of EVIDENCE) expect(e.id.startsWith(`${evidenceIdPrefix(e.channel)}.`)).toBe(true);
    expect(evidenceEntryIssues(entry({ id: "c4.sigma.test" })).join()).toMatch(/starting "c3\."/);
    expect(evidenceEntryIssues(entry({ id: "C3.Sigma" })).join()).toMatch(/id/);
    expect(libraryIssues([parsed(), parsed({ isDefault: false })])).toContain('Duplicate evidence id "c3.sigma.test"');
    expect(loadEvidence({ "c4.json": { channel: "C4", entries: [entry()] } }).issues.join()).toMatch(/in the C4 file but names channel C3/);
  });

  it("T-EVD-03 exactly one default per formula and parameter, counting formulas an entry is also used by", () => {
    expect(libraryIssues(EVIDENCE)).toEqual([]);
    const two = [parsed(), parsed({ id: "c3.sigma.test-two" })];
    expect(libraryIssues(two).join()).toMatch(/F-C3-02 sigma has 2 defaults/);
    const none = [parsed({ isDefault: false })];
    expect(libraryIssues(none).join()).toMatch(/F-C3-02 sigma has no default/);
    // alsoUsedBy counts: a second default for F-C3-01 r would clash with the shared C2 entry.
    const shared = EVIDENCE.find((e) => e.id === "c2.r.oia-cba")!;
    expect(entryFormulas(shared)).toEqual(["F-C2-01", "F-C3-01"]);
    const clash = [...EVIDENCE, parsed({ id: "c3.r.test", formula: "F-C3-01", parameter: "r" })];
    expect(libraryIssues(clash).join()).toMatch(/F-C3-01 r has 2 defaults/);
    expect(evidenceEntryIssues(entry({ alsoUsedBy: ["F-C3-02"] })).join()).toMatch(/repeats/);
  });

  it("T-EVD-04 a default is never tagged [S], and is graded D only when it is the tool's assumption and says why", () => {
    for (const e of EVIDENCE.filter((x) => x.isDefault)) {
      expect(e.tag, e.id).not.toBe("S");
      if (e.grade === "D") {
        expect(e.method, e.id).toBe("assumption");
        expect(e.notes?.trim(), e.id).toBeTruthy();
      }
    }
    expect(evidenceEntryIssues(entry({ tag: "S", quote: undefined })).join()).toMatch(/never a default/);
    expect(evidenceEntryIssues(entry({ tag: "S", quote: undefined, isDefault: false }))).toEqual([]);
    expect(evidenceEntryIssues(entry({ grade: "D" })).join()).toMatch(/grade-D default/);
    expect(evidenceEntryIssues(entry({ grade: "D", method: "assumption" })).join()).toMatch(/grade-D default/);
    expect(evidenceEntryIssues(entry({ grade: "D", method: "assumption", notes: "No source exists." }))).toEqual([]);
    expect(evidenceEntryIssues(entry({ grade: "D", isDefault: false }))).toEqual([]);
  });

  it("T-EVD-05 [P] and [A] entries have an exact quote and a locator, and every URL is https", () => {
    for (const e of EVIDENCE) {
      if (e.tag !== "S") {
        expect(e.quote?.trim(), e.id).toBeTruthy();
        expect(e.citation.locator?.trim(), e.id).toBeTruthy();
      }
      expect(e.citation.url, e.id).toMatch(/^https:\/\//);
    }
    expect(evidenceEntryIssues(entry({ quote: undefined })).join()).toMatch(/needs an exact quote/);
    expect(evidenceEntryIssues(entry({ quote: "  " })).join()).toMatch(/needs an exact quote/);
    const { locator: _locator, ...noLocator } = entry().citation;
    expect(evidenceEntryIssues(entry({ tag: "A", citation: noLocator })).join()).toMatch(/needs a page, table or section/);
    expect(evidenceEntryIssues(entry({ citation: { ...entry().citation, url: "http://example.org" } })).join()).toMatch(/https/);
    expect(evidenceEntryIssues(entry({ quote: " padded " })).join()).toMatch(/Trim/);
  });

  it("T-EVD-06 low ≤ value ≤ high, and each range matches its basis (source, ±50%, sensitivity or fixed)", () => {
    for (const e of EVIDENCE) {
      expect(e.low, e.id).toBeLessThanOrEqual(e.value);
      expect(e.value, e.id).toBeLessThanOrEqual(e.high);
      if (e.rangeBasis === "fixed") expect([e.low, e.high], e.id).toEqual([e.value, e.value]);
      if (e.rangeBasis === "plusMinus50") {
        expect(e.low, e.id).toBeCloseTo(e.value - Math.abs(e.value) / 2, 12);
        expect(e.high, e.id).toBeCloseTo(e.value + Math.abs(e.value) / 2, 12);
      }
      if (e.rangeBasis === "source" || e.rangeBasis === "sensitivity") expect(e.low, e.id).toBeLessThan(e.high);
    }
    expect(evidenceEntryIssues(entry({ value: 0.7 })).join()).toMatch(/low ≤ value ≤ high/);
    expect(evidenceEntryIssues(entry({ low: 0.1 })).join()).toMatch(/±50% rule gives low 0.2/);
    expect(evidenceEntryIssues(entry({ value: -1, low: -1.5, high: -0.5 }))).toEqual([]);
    expect(evidenceEntryIssues(entry({ rangeBasis: "fixed" })).join()).toMatch(/low = value = high/);
    expect(evidenceEntryIssues(entry({ rangeBasis: "source", low: 0.4, high: 0.4, value: 0.4 })).join()).toMatch(/use "fixed"/);
  });

  it("T-EVD-07 every parameter of traceability §2.3–2.5 has a library default, a brief field, pipeline data, or is marked user-set", () => {
    // Every formula id in §2.3–2.5 is covered by the list.
    const covered = new Set([...REQUIRED.map((r) => r.formula), ...NO_PARAMETER]);
    const traced = tracedFormulas();
    expect(traced.length).toBeGreaterThanOrEqual(37); // 26 Layer A, 6 Layer B, 5 uncertainty and gate rules (22 Oct 2026)
    expect(traced.filter((f) => !covered.has(f))).toEqual([]);
    for (const r of REQUIRED) {
      const label = `${r.formula} ${r.parameter}`;
      if (r.source === "library") {
        const d = defaultEvidence(r.formula, r.parameter);
        expect(d, label).toBeDefined();
        expect(d!.tag, label).not.toBe("S");
      }
      if (r.source === "user") expect(defaultEvidence(r.formula, r.parameter), label).toBeUndefined();
      if (r.source === "brief") expect(briefSource, label).toContain(r.field!);
    }
    for (const f of NO_PARAMETER) expect(EVIDENCE.filter((e) => entryFormulas(e).includes(f)), f).toEqual([]);
    // No orphan entries: every (formula, parameter) in the library is on the list, and every formula id is in the document.
    const listed = new Set(REQUIRED.filter((r) => r.source === "library").map((r) => `${r.formula} ${r.parameter}`));
    for (const e of EVIDENCE) {
      for (const f of entryFormulas(e)) {
        expect(listed.has(`${f} ${e.parameter}`), `${e.id}: ${f} ${e.parameter}`).toBe(true);
        expect(traceability, e.id).toContain(f);
      }
    }
  });

  it("T-EVD-08 lookups return the default and its alternatives, including entries shared between formulas", () => {
    expect(defaultEvidence("F-C3-02", "sigma")?.id).toBe("c3.sigma.cfm2011");
    expect(evidenceFor("F-C3-02", "sigma").map((e) => e.id)).toEqual(["c3.sigma.cfm2011", "c3.sigma.kpb2016"]);
    expect(defaultEvidence("F-C3-01", "r")?.id).toBe("c2.r.oia-cba");
    expect(evidenceFor("F-C2-01", "r").map((e) => e.id)).toEqual(["c2.r.oia-cba", "c2.r.pc2025-net-zero"]);
    expect(defaultEvidence("F-C4-03", "gap")).toBeUndefined();
    expect(evidenceFor("F-X-99", "nothing")).toEqual([]);
    const groups = evidenceByChannel();
    expect(groups.map((g) => g.channel)).toEqual(["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "layerB", "general"]);
    expect(groups.reduce((n, g) => n + g.entries.length, 0)).toBe(EVIDENCE.length);
  });

  it("T-EVD-09 defaults agree with the values the plan and the brief rely on", () => {
    const v = (formula: string, parameter: string) => {
      const d = defaultEvidence(formula, parameter)!;
      return [d.value, d.low, d.high];
    };
    expect(v("F-C3-02", "sigma")).toEqual([0.4, 0.2, 0.6]);
    expect(v("F-C4-03", "beta2")).toEqual([0.009, 0.00312, 0.01488]);
    expect(v("F-C6-01", "misallocationCostChange")).toEqual([1.84, 1.16, 2.52]);
    expect(v("F-C7-01", "beta")).toEqual([-0.047, -0.047, -0.037]);
    expect(v("F-C7-02", "betaKY")).toEqual([-0.03, -0.035, -0.025]);
    expect(v("F-C8-01", "elasticity")[0]).toBe(1.6);
    expect(v("F-C8-02", "passThrough")).toEqual([0.1, 0.05, 0.1]);
    expect(v("F-C10-01", "beta")).toEqual([0.006, 0.006, 0.008]);
    expect(v("F-C11-01", "meb.companyIncome")).toEqual([0.5, 0.2, 1.35]);
    expect(v("F-C11-01", "meb.landTax")[0]).toBe(-0.1);
    expect(v("F-B-01", "gdpPerLp")).toEqual([1, 1, 1]);
    // The PC's L1 and L2 shocks rebuild from the library: 10% × 2.4% = 0.24%; 0.5 × 1.6% = 0.8%.
    expect(v("F-C8-02", "passThrough")[0]! * v("F-C8-02", "wageEffectHighUse")[0]!).toBeCloseTo(0.24, 12);
    expect(v("F-C8-02", "passThrough")[0]! * v("F-C8-02", "wageEffectLowUse")[0]!).toBeCloseTo(0.14, 12);
    expect(v("F-C8-01", "pcStringencyCut")[0]! * v("F-C8-01", "elasticity")[0]!).toBeCloseTo(0.8, 12);
    // The brief's analysis defaults are the library's general entries.
    const brief = PolicyBriefSchema.parse({ schemaVersion: 1, kind: "policy-brief", id: "t", meta: { title: "t (synthetic)", jurisdictions: ["CTH"], startYear: 2027 }, scope: { industries: [{ anzsic: "E" }] } });
    const rate = defaultEvidence("PR-06", "discountRate")!;
    expect(brief.analysis.discountRate).toBe(rate.value);
    expect(brief.analysis.sensitivityRates).toEqual([rate.low, rate.high]);
    expect(brief.analysis.realisationFactor).toBe(defaultEvidence("F-U-03", "realisationFactor")!.value);
  });

  it("T-EVD-10 the committed review sheet is up to date with the library and rebuilding it keeps the checks", () => {
    const committed = readFileSync(sheetPath, "utf8");
    expect(committed.startsWith("﻿")).toBe(true);
    const [head, ...rows] = parseCsv(committed);
    expect(head).toEqual([...REVIEW_SHEET_COLUMNS, ...REVIEW_CHECK_COLUMNS]);
    const expected = reviewSheetRows(EVIDENCE);
    expect(rows.length, "rerun: npx tsx scripts/evidence-sheet.ts").toBe(expected.length);
    rows.forEach((r, i) => expect(r.slice(0, REVIEW_SHEET_COLUMNS.length), `row ${i + 2} is stale: rerun npx tsx scripts/evidence-sheet.ts`).toEqual(expected[i]));
    // Rebuilding carries Cowork's check columns over by id.
    const checks = ["0.40", "exact", "Abstract, p. 1", "agrees", "looked, fine"];
    const reviewed = toCsv([head!, [...rows[0]!.slice(0, REVIEW_SHEET_COLUMNS.length), ...checks], ...rows.slice(1)]);
    const rebuilt = parseCsv(evidenceReviewCsv(EVIDENCE, reviewed));
    expect(rebuilt[1]!.slice(-REVIEW_CHECK_COLUMNS.length)).toEqual(checks);
    expect(rebuilt.slice(2).every((r) => r.slice(-REVIEW_CHECK_COLUMNS.length).every((c) => c === ""))).toBe(true);
    // CSV round trip with commas, quotes and line breaks; no text cell can start a spreadsheet formula.
    const tricky = [["a,b", 'say "hi"', "line\nbreak", ""], ["x", "y", "z", "w"]];
    expect(parseCsv(toCsv(tricky))).toEqual(tricky);
    for (const r of rows) for (const cell of r) if (Number.isNaN(Number(cell))) expect(cell, cell).not.toMatch(/^[=+\-@]/);
  });

  it("T-EVD-11 every entry starts as a draft review, and a checked entry records who checked it and when", () => {
    for (const e of EVIDENCE) expect(["draft", "checked"]).toContain(e.review.status);
    expect(EVIDENCE.every((e) => e.review.status === "draft")).toBe(true);
    expect(evidenceEntryIssues(entry({ review: { status: "checked" } })).join()).toMatch(/who checked it and when/);
    expect(evidenceEntryIssues(entry({ review: { status: "checked", by: "Cowork", on: "2026-11-01" } }))).toEqual([]);
    expect(evidenceEntryIssues(entry({ review: { status: "checked", by: "Cowork", on: "1 Nov" } })).join()).toMatch(/date/);
    expect(evidenceEntryIssues(entry({ tag: "S", quote: undefined, isDefault: false, review: { status: "checked", by: "Cowork", on: "2026-11-01" } })).join()).toMatch(/cannot be checked/);
  });

  it("T-EVD-12 the Sources page lists every entry by channel with value, range, grade, tag, citation link, locator and quote", () => {
    const html = renderToStaticMarkup(createElement(SourcesPage));
    expect(html).toContain("<h1");
    expect(html).toContain("Sources and parameters");
    expect(html.match(/data-testid="evidence-entry"/g)?.length).toBe(EVIDENCE.length);
    for (const g of evidenceByChannel()) expect(html).toContain(`id="evidence-group-${g.channel}"`);
    const sigma = EVIDENCE.find((e) => e.id === "c3.sigma.cfm2011")!;
    const card = html.slice(html.indexOf('data-evidence-id="c3.sigma.cfm2011"'), html.indexOf('data-evidence-id="c3.sigma.kpb2016"'));
    expect(card).toContain("Grade B");
    expect(card).toContain("[A]");
    expect(card).toContain("0.2 to 0.6");
    expect(card).toContain(`href="${sigma.citation.url}"`);
    expect(card).toContain("Abstract");
    expect(card).toContain("<blockquote");
    expect(card).toContain("precisely estimated elasticity of 0.40");
    expect(card).toContain("Not yet checked");
    // Headings label each card; links never open the network by themselves.
    expect(html.match(/<article[^>]*aria-labelledby="evidence-[^"]+"/g)?.length).toBe(EVIDENCE.length);
    expect(html).not.toMatch(/<(script|img|iframe)\b/);
    expect(formatEvidenceNumber(-0.04700000001)).toBe("−0.047");
  });
});
