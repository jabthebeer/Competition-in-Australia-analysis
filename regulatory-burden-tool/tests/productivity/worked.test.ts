// P6 worked examples (plan §8): five real policies costed end to end, with their outputs frozen.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { buildContext, type ParameterFile } from "../../src/productivity/index";
import { sourcesFingerprint } from "../../src/productivity/validation";
import { runWorked, WORKED, withResults, workedResults, type WorkedOutput } from "../../src/productivity/worked";

const tool = join(import.meta.dirname, "..", "..");
const repo = join(tool, "..");
const params = JSON.parse(readFileSync(join(repo, "data", "processed", "costing", "parameters.json"), "utf8")) as ParameterFile;
const files = Object.fromEntries(WORKED.map((w) => [w.file, JSON.parse(readFileSync(join(tool, "examples", w.file), "utf8"))]));
const frozen = JSON.parse(readFileSync(join(tool, "tests", "productivity", "frozen", "worked-examples.json"), "utf8")) as { fingerprint: string; outputs: WorkedOutput[] };

describe("worked examples", () => {
  const outputs = runWorked(files, buildContext(params));
  const get = (id: string, variant: string | null = null) => outputs.find((o) => o.id === id && o.variant === variant)!;

  it("T-WEX-01 the five worked examples reproduce their frozen outputs; the methods note's results are current", () => {
    const same = frozen.fingerprint === sourcesFingerprint(params);
    if (same) {
      expect(outputs, "rerun: npm run worked:examples").toEqual(frozen.outputs);
      const note = readFileSync(join(repo, "docs", "worked_examples.md"), "utf8");
      expect(note, "rerun: npm run worked:examples").toBe(withResults(note, workedResults(outputs, frozen.fingerprint, String(params.vintage))));
    } else {
      // The bundled data has been refreshed (the Pages workflow does so daily): the structure and the RBE, which rest
      // on the briefs alone, must not move, and GDP effects stay within 25% of the frozen ones.
      console.warn("Worked examples were frozen with other data: rerun npm run worked:examples");
      expect(outputs.map((o) => [o.id, o.variant])).toEqual(frozen.outputs.map((o) => [o.id, o.variant]));
      outputs.forEach((o, i) => {
        const f = frozen.outputs[i]!;
        expect(o.gate, o.title).toBe(f.gate);
        expect(o.channels.map((c) => [c.channel, c.status]), o.title).toEqual(f.channels.map((c) => [c.channel, c.status]));
        expect(o.rbe, o.title).toEqual(f.rbe);
        if (f.gdpPct === 0) expect(o.gdpPct, o.title).toBe(0);
        else expect(Math.abs(o.gdpPct / f.gdpPct - 1), o.title).toBeLessThan(0.25);
      });
    }
  }, 60_000);

  it("T-WEX-02 each example shows what its source says it should, whatever the data vintage", () => {
    // Non-compete ban: the PC's chain, so close to Treasury's $5.1 billion; graded C, so indicative.
    const nc = get("noncompete-ban");
    expect(nc.gate).toBe("indicative");
    expect(nc.channels.find((c) => c.channel === "C8")!.gdpPct).toBeCloseTo(0.1805 * 0.99, 1);
    // AMR: fees are outside the RBE and mutual recognition has no elasticity, so nothing changes GDP.
    expect(get("worked-amr").gdpPct).toBe(0);
    expect(get("worked-amr").gateReasons.join()).toMatch(/No channel changes GDP/);
    // Climate disclosure: the RBE of Treasury's recommended option, $1,150.2 million a year, from the briefs alone.
    const cd = get("worked-climate-disclosure");
    expect(cd.rbe.map((r) => Math.round(r.dollars / 1e5) / 10)).toEqual([1150.2, 1386.7, 1207.3]);
    expect(cd.gdpPct).toBeLessThan(0);
    expect(cd.screen.filter((s) => s.unit === "businesses")).toHaveLength(3);
    // EPBC: the effect grows with the days saved, in proportion (Δln c ≈ r·d is linear in d).
    const epbc = [get("worked-epbc-approvals"), get("worked-epbc-approvals", "medium"), get("worked-epbc-approvals", "high")];
    expect(epbc[1]!.gdpPct / epbc[0]!.gdpPct).toBeCloseTo(141 / 20, 1);
    expect(epbc[2]!.gdpPct / epbc[0]!.gdpPct).toBeCloseTo(288 / 20, 1);
    // Victoria: payroll thresholds are screened through their employee equivalent (A-P34); no GDP effect (A-P05).
    const vic = get("worked-vic-payroll-threshold");
    expect(vic.gdpPct).toBe(0);
    expect(vic.screen.filter((s) => s.unit === "businesses").map((s) => s.label)).toEqual([
      expect.stringMatching(/\$1,000,000 of payroll/),
      expect.stringMatching(/\$700,000 of payroll/),
      expect.stringMatching(/\$3,000,000 of payroll/),
    ]);
  }, 60_000);
});
