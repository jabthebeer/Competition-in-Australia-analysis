// Writes docs/costing_validation.md at the repository root: the engine against the PC's shock chains in PC National
// and published models of a company tax cut (plan P6, §8). Test T-VAL-01 checks the committed note is current.
// Run with: npx tsx scripts/validate-costing.ts
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { buildContext, type ParameterFile } from "../src/productivity/index";
import { runValidation, validationMarkdown } from "../src/productivity/validation";

const repo = join(import.meta.dirname, "..", "..");
const params = JSON.parse(readFileSync(join(repo, "data", "processed", "costing", "parameters.json"), "utf8")) as ParameterFile;
const rows = runValidation(params, buildContext(params));
const out = join(repo, "docs", "costing_validation.md");
writeFileSync(out, validationMarkdown(rows, params), "utf8");
console.log(`Wrote ${out}: ${rows.filter((r) => r.pass).length} of ${rows.length} cases pass`);
