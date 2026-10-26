// Costs the worked examples (plan P6, §8), writes the results section of docs/worked_examples.md and freezes the
// outputs in tests/productivity/frozen/worked-examples.json, which test T-WEX-01 compares against.
// Run with: npm run worked:examples
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { buildContext, type ParameterFile } from "../src/productivity/index";
import { sourcesFingerprint } from "../src/productivity/validation";
import { runWorked, WORKED, withResults, workedResults } from "../src/productivity/worked";

const tool = join(import.meta.dirname, "..");
const repo = join(tool, "..");
const params = JSON.parse(readFileSync(join(repo, "data", "processed", "costing", "parameters.json"), "utf8")) as ParameterFile;
const files = Object.fromEntries(WORKED.map((w) => [w.file, JSON.parse(readFileSync(join(tool, "examples", w.file), "utf8"))]));
const outputs = runWorked(files, buildContext(params));
const fingerprint = sourcesFingerprint(params);

mkdirSync(join(tool, "tests", "productivity", "frozen"), { recursive: true });
writeFileSync(join(tool, "tests", "productivity", "frozen", "worked-examples.json"), `${JSON.stringify({ fingerprint, vintage: params.vintage, outputs }, null, 2)}\n`, "utf8");
const notePath = join(repo, "docs", "worked_examples.md");
writeFileSync(notePath, withResults(readFileSync(notePath, "utf8"), workedResults(outputs, fingerprint, String(params.vintage))), "utf8");
console.log(`Froze ${outputs.length} worked-example runs and updated ${notePath}`);
