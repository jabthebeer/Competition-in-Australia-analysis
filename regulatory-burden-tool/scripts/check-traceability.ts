// Checks that docs/framework_traceability.md stays true to the code:
//  - every test ID it cites (e.g. T-REF-07, ranges like T-DEL-01..05) exists as a test title;
//  - every warning code it cites (W-xx) has a test;
//  - every code reference (e.g. `reform.ts#doAnywayShares`) points at a real file and symbol.
// Run with: npm run trace
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

const root = join(import.meta.dirname, "..");
const doc = readFileSync(join(root, "docs/framework_traceability.md"), "utf8");
const tests = ["tests/engine", "tests/ui", "e2e"]
  .flatMap((dir) =>
    readdirSync(join(root, dir))
      .filter((f) => f.endsWith(".test.ts") || f.endsWith(".spec.ts"))
      .map((f) => readFileSync(join(root, dir, f), "utf8")),
  )
  .join("\n");

const testTitles = new Set([...tests.matchAll(/(?:it|test)\("((?:T-[A-Z0-9]+-\d{2}[a-z]?)|(?:W-\d{2}))\b/g)].map((m) => m[1]!));
const problems: string[] = [];

// Test IDs, expanding ranges such as T-DEL-01..05 and wildcards such as T-REF-*.
for (const m of doc.matchAll(/T-([A-Z0-9]+)-(\d{2}|\*)(?:\.\.(\d{2}))?/g)) {
  const [, prefix, from, to] = m;
  if (from === "*") {
    if (![...testTitles].some((t) => t.startsWith(`T-${prefix}-`))) problems.push(`No tests for T-${prefix}-*`);
    continue;
  }
  const end = to ? Number(to) : Number(from);
  for (let n = Number(from); n <= end; n++) {
    const id = `T-${prefix}-${String(n).padStart(2, "0")}`;
    if (!testTitles.has(id)) problems.push(`Test ${id} is cited in the traceability document but no test has that ID`);
  }
}

for (const m of new Set([...doc.matchAll(/W-(\d{2})/g)].map((x) => x[0]))) {
  if (!testTitles.has(m)) problems.push(`Warning ${m} is cited but has no test`);
}

// Code references like `reform.ts#doAnywayShares` (engine) or `src/ui/model.ts#rebaseReformed`.
for (const m of doc.matchAll(/`((?:src\/(?:engine|ui)\/)[\w/]+\.tsx?|[a-z]+\.ts)(?:#(\w+))?/g)) {
  const [, file, symbol] = m;
  const path = file!.startsWith("src/") ? join(root, file!) : join(root, "src/engine", file!);
  let src: string;
  try {
    src = readFileSync(path, "utf8");
  } catch {
    problems.push(`Code reference ${file} doesn't exist`);
    continue;
  }
  if (symbol && !new RegExp(`(function|const|class|interface|type)\\s+${symbol}\\b`).test(src)) {
    problems.push(`Code reference ${file}#${symbol}: symbol not found`);
  }
}

const unique = [...new Set(problems)];
if (unique.length) {
  console.error(`Traceability check failed (${unique.length}):\n${unique.map((p) => `  - ${p}`).join("\n")}`);
  process.exitCode = 1;
} else {
  console.log(`Traceability check passed: ${testTitles.size} test IDs; every cited test, warning and code reference resolves.`);
}
