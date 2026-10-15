import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { runCli } from "../../src/cli/rbe";
import {
  TIDY_COLUMNS,
  computeProposal,
  parseProposal,
  runExtensions,
  tidyCsv,
  tidyDictionaryCsv,
  toTidyRows,
  type EngineExtension,
} from "../../src/engine/index";
import { dec, sum } from "../../src/engine/decimal";
import { illustrativeReform, labour, ob, opt, option, pop, proposal, side } from "./helpers";

const example = join(__dirname, "../../examples/illustrative-reform.json");

describe("Extension interface and tidy export (DECISIONS #44)", () => {
  // ILLUSTRATIVE competition-costing style extension: cost per entity as a share of an assumed revenue.
  const costShare: EngineExtension<{ populationId: string; costShareOfRevenue: string }[]> = {
    id: "illustrative-cost-share",
    version: "0.0.1",
    title: "Illustrative compliance cost share",
    description: "Example only: per-entity change ÷ an assumed revenue. Sits outside the RBE.",
    compute: ({ result }) =>
      result.options[0]!.perEntity.map((p) => ({ populationId: p.populationId, costShareOfRevenue: dec(p.changePerEntity).dividedBy(2000000).toFixed() })),
  };
  const vandal: EngineExtension = {
    id: "vandal",
    version: "0.0.1",
    title: "Tries to change the RBE",
    description: "Must fail",
    compute: ({ result }) => {
      (result.options[0]!.rbe as { total: string }).total = "0";
      return "changed";
    },
  };

  it("T-EXT-01 extensions read results and add outputs, but can't change the RBE", () => {
    const p = parseProposal(illustrativeReform());
    const result = computeProposal(p);
    const before = JSON.stringify(result);
    const outcomes = runExtensions(p, result, [costShare, vandal]);
    expect(outcomes[0]).toMatchObject({ id: "illustrative-cost-share", ok: true });
    expect(outcomes[0]!.ok && outcomes[0]!.output).toEqual([{ populationId: "biz", costShareOfRevenue: "-0.000636203" }]);
    expect(outcomes[1]).toMatchObject({ id: "vandal", ok: false });
    expect(JSON.stringify(result)).toBe(before);
  });

  it("T-TIDY-01 tidy export: one row per item × year, merge keys for ABS data, sums back to the RBE", () => {
    const p = proposal(
      [pop("smallRetail", 1000, { cohort: "small", employmentBand: "5-19", industry: "G" })],
      [option("o", [ob("report", "administrative", side("labour", [labour("smallRetail", 4, 4)]), side("labour", [labour("smallRetail", 2, 1)]), { legalReference: { instrument: "ILLUSTRATIVE Act", provision: "s 1" } })])],
    );
    const result = computeProposal(p);
    const rows = toTidyRows(result);
    expect(rows).toHaveLength(opt(result).items.length * 10);
    expect(Object.keys(rows[0]!)).toEqual(TIDY_COLUMNS.map((c) => c.name));
    expect(rows[0]).toMatchObject({ industry_anzsic: "G", employment_band: "5-19", cohort: "small", legal_provision: "s 1", year: 1 });
    const totalDelta = sum(rows.map((r) => dec(String(r.delta_contribution))));
    expect(totalDelta.equals(dec(opt(result).rbe.total).times(10))).toBe(true);
    const csv = tidyCsv(rows);
    expect(csv.split("\r\n")[0]).toBe(TIDY_COLUMNS.map((c) => c.name).join(","));
    expect(csv.split("\r\n").length).toBe(rows.length + 2); // header + rows + trailing newline
    expect(tidyDictionaryCsv().split("\r\n").length).toBe(TIDY_COLUMNS.length + 2);
    const quoted = tidyCsv([{ ...rows[0]!, obligation_name: 'Report, "annual"' }]);
    expect(quoted).toContain('"Report, ""annual"""');
  });
});

describe("CLI", () => {
  it("T-CLI-01 prints the framework-format RBE table for a JSON proposal file", () => {
    const { stdout, exitCode } = runCli([example]);
    expect(exitCode).toBe(0);
    expect(stdout).toContain("**Average annual regulatory costs (from business as usual)**");
    expect(stdout).toContain("| Change in costs ($ million) | Business | Community organisations | Individuals | Total change in costs |");
    expect(stdout).toContain("| Total, by sector | ($12.7) | $0 | $0 | ($12.7) |");
    expect(stdout).toContain("Net reduction of $12.7 million a year");
    expect(stdout).toContain("| Total, by sector | ($11.3) | $0 | $0 | ($11.3) |"); // dual-running option
    expect(stdout).toContain("| Total, by sector | ($14.6) | $0 | $0 | ($14.6) |"); // outright repeal
    expect(stdout).toContain("Unofficial aid");
    expect(runCli([example, "--precision", "dollars"]).stdout).toContain("($12,724,060)");
    expect(JSON.parse(runCli([example, "--json"]).stdout).options[0].rbe.total).toBe("-12724060");
    const dir = mkdtempSync(join(tmpdir(), "rbe-"));
    expect(runCli([example, "--tidy", join(dir, "out.csv")]).exitCode).toBe(0);
    expect(readFileSync(join(dir, "out.csv"), "utf8")).toMatch(/^proposal_id,option_id/);
    expect(readFileSync(join(dir, "out.dictionary.csv"), "utf8")).toMatch(/^name,type,description/);
    expect(runCli(["does-not-exist.json"]).exitCode).toBe(1);
    expect(runCli([]).exitCode).toBe(1);
  });
});
