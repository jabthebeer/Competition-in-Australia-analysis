// P6 validation (plan §8): the engine against PC National's shock chains and published company tax models.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { buildContext, type ParameterFile } from "../../src/productivity/index";
import { runValidation, sourcesFingerprint, validationMarkdown } from "../../src/productivity/validation";

const repo = join(import.meta.dirname, "..", "..", "..");
const params = JSON.parse(readFileSync(join(repo, "data", "processed", "costing", "parameters.json"), "utf8")) as ParameterFile;
const ctx = buildContext(params);

describe("validation", () => {
  const rows = runValidation(params, ctx);

  it("T-VAL-01 PC shock chains and the company tax anchor meet their pass marks; the committed note is current", () => {
    const byId = new Map(rows.map((r) => [r.id, r]));
    for (const id of ["L2", "L1", "H5", "TAX25"]) expect(byId.get(id)!.pass, id).toBe(true);
    // B7tar's compliance part is reported, with its gap explained: it must stay within 25% of the PC's.
    const b7 = byId.get("B7tar")!;
    expect(Math.abs(b7.tool.central / b7.published.low - 1)).toBeLessThan(0.25);
    const committed = readFileSync(join(repo, "docs", "costing_validation.md"), "utf8");
    const stamp = /sources-fingerprint: (\w+)/.exec(committed)?.[1];
    if (stamp === sourcesFingerprint(params)) {
      expect(committed, "rerun: npm run validate:costing").toBe(validationMarkdown(rows, params));
    } else {
      // The bundled data has been refreshed since the note was written (the Pages workflow does so daily): the pass
      // marks above still hold; rerun npm run validate:costing to bring the note up to date.
      console.warn("docs/costing_validation.md was written with other data: rerun npm run validate:costing");
    }
  });
});
