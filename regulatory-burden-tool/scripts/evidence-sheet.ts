// Writes the Cowork review sheet for the evidence library, docs/review/evidence_library_review.csv at the
// repository root: one row per entry (id, formula, parameter, value, range, citation, url, locator, quote,
// derivation, review status), then the check columns Cowork fills in.
// The check columns already filled in are kept, matched by id, so rebuilding the sheet never loses a review.
// UTF-8 with a byte-order mark, so Excel opens it cleanly. Test T-EVD-10 checks the committed sheet is current.
// Run with: npx tsx scripts/evidence-sheet.ts
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { EVIDENCE, REVIEW_CHECK_COLUMNS, evidenceReviewCsv, parseCsv } from "../src/productivity/evidence";

const out = join(import.meta.dirname, "..", "..", "docs", "review", "evidence_library_review.csv");
const existing = existsSync(out) ? readFileSync(out, "utf8") : undefined;

// Warn about reviews of entries that no longer exist: they are dropped from the rebuilt sheet.
if (existing) {
  const [head, ...rows] = parseCsv(existing);
  const idAt = head?.indexOf("id") ?? -1;
  const checkAt = REVIEW_CHECK_COLUMNS.map((c) => head?.indexOf(c) ?? -1);
  const ids = new Set(EVIDENCE.map((e) => e.id));
  for (const r of rows) {
    const id = r[idAt] ?? "";
    if (id && !ids.has(id) && checkAt.some((j) => j >= 0 && (r[j] ?? "").trim())) {
      console.warn(`Warning: the review of "${id}" is dropped because the library no longer has that entry.`);
    }
  }
}

mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, evidenceReviewCsv(EVIDENCE, existing), "utf8");
console.log(`Wrote ${EVIDENCE.length} rows to ${out}`);
