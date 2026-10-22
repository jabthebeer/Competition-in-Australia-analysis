// The costing parameters bundled at build time (costing-params-plugin.ts, src/ui/costingData.ts).
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { EMPTY_PARAMETERS, costingParameters } from "../../costing-params-plugin";
import { checkCostingParameters, loadCostingParameters } from "../../src/ui/costingData";

/** Runs the plugin's resolve and load hooks the way Vite does. */
function loadVirtual(path: string): unknown {
  const plugin = costingParameters(path);
  const resolveId = plugin.resolveId as (id: string) => string | undefined;
  const load = plugin.load as (this: { addWatchFile: (p: string) => void }, id: string) => string | undefined;
  const id = resolveId("virtual:costing-parameters");
  expect(id).toBeDefined();
  const code = load.call({ addWatchFile: () => undefined }, id!)!;
  return new Function(`return ${code.replace(/^export default /, "").replace(/;$/, "")}`)();
}

describe("bundled costing parameters", () => {
  it("T-SITE-01 the parameters bundled into this build pass the check", async () => {
    const load = await loadCostingParameters();
    expect(load.ok, load.ok ? "" : load.problem).toBe(true);
    if (load.ok) {
      for (const s of load.parameters.sources) {
        expect(s.id).not.toBe("");
        expect(s.url).toMatch(/^https:\/\//);
        expect(s.licence).not.toBe("");
      }
    }
  });

  it("T-SITE-02 without a parameter file the build carries an empty, valid set", () => {
    const data = loadVirtual(join(mkdtempSync(join(tmpdir(), "costing-")), "missing.json"));
    expect(data).toEqual(EMPTY_PARAMETERS);
    const check = checkCostingParameters(data);
    expect(check.ok && check.parameters.sources).toEqual([]);
  });

  it("T-SITE-03 a parameter file is bundled as written; a malformed one is reported, not thrown", () => {
    const dir = mkdtempSync(join(tmpdir(), "costing-"));
    const file = join(dir, "parameters.json");
    const params = {
      ...EMPTY_PARAMETERS,
      vintage: "2026-08-18",
      sources: [{ id: "x", title: "Illustrative source", publisher: "ABS", release: "2024-25", url: "https://example.org/x", licence: "CC BY 4.0", status: "current" }],
    };
    writeFileSync(file, JSON.stringify(params));
    expect(loadVirtual(file)).toEqual(params);
    expect(checkCostingParameters(loadVirtual(file)).ok).toBe(true);
    expect(checkCostingParameters({ ...params, schema: "something-else" })).toEqual({ ok: false, problem: expect.stringContaining("schema") });
  });
});
