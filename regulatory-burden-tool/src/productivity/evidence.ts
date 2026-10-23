// The evidence library (plan §6.7): one entry per parameter that the Layer A and Layer B formulas use
// (docs/productivity_traceability.md §2.3–2.5). Each entry gives its value, range, source, an exact quote and
// a page or table reference, so that it can be checked against the source (docs/review/evidence_library_review.csv).
//
// Rules (tested in tests/productivity/evidence.test.ts, T-EVD-*):
// - ids are unique, and each id starts with its channel (c1 … c12, layer-b, general);
// - exactly one default per (formula, parameter), counting the formulas an entry is also used by;
// - a default is never tagged [S], and is graded D only when it is the tool's assumption and says why;
// - an entry tagged [P] or [A] has a non-empty quote and locator; every URL is https;
// - low ≤ value ≤ high, and the range matches its stated basis (±50%, fixed or from the source).
// The JSON files in ./evidence/ are the source of truth; entries start as review "draft" until Cowork checks them.
import { z } from "zod";
import { formatIssues } from "../engine/migrate";
import { CHANNELS, CHANNEL_IDS } from "./channels";
import c1 from "./evidence/c1.json";
import c2 from "./evidence/c2.json";
import c3 from "./evidence/c3.json";
import c4 from "./evidence/c4.json";
import c5 from "./evidence/c5.json";
import c6 from "./evidence/c6.json";
import c7 from "./evidence/c7.json";
import c8 from "./evidence/c8.json";
import c9 from "./evidence/c9.json";
import c10 from "./evidence/c10.json";
import c11 from "./evidence/c11.json";
import general from "./evidence/general.json";
import layerB from "./evidence/layer-b.json";

// ---- vocabulary ------------------------------------------------------------------------------------------------

/** Channels C1–C12, Layer B (aggregation and time path), and general settings (discounting, ranges, the gate). */
export const EVIDENCE_CHANNELS = [...CHANNEL_IDS, "layerB", "general"] as const;
export type EvidenceChannel = (typeof EVIDENCE_CHANNELS)[number];

export const EVIDENCE_CHANNEL_NAMES: Readonly<Record<EvidenceChannel, string>> = {
  ...(Object.fromEntries(CHANNEL_IDS.map((id) => [id, CHANNELS[id].name])) as Record<(typeof CHANNEL_IDS)[number], string>),
  layerB: "Economy-wide aggregation and time path (Layer B)",
  general: "Discounting, ranges and the evidence gate",
};

/**
 * How the source got its number. `data` (a measured statistic, e.g. an ABS income share) and `rule` (a value an
 * official framework sets, e.g. the OIA discount rate) are not estimated effects (interpretation A-P16).
 */
export const EVIDENCE_METHODS = ["causal", "structural", "correlational", "model", "assumption", "data", "rule"] as const;
export const EVIDENCE_GRADES = ["A", "B", "C", "D"] as const;
/** [P] primary source read; [A] abstract or official summary read; [S] secondary coverage only (never a default). */
export const VERIFICATION_TAGS = ["P", "A", "S"] as const;
/**
 * Where low and high come from:
 * - `source`: the source's own range, specifications or confidence interval;
 * - `plusMinus50`: the tool's ±50% rule for a value with no published range (F-U-02); the central value keeps its grade (A-P15);
 * - `sensitivity`: alternative cases reported side by side, not sampled (e.g. 3% and 10% discount rates);
 * - `fixed`: no range (a measured statistic, a rule, or a value whose uncertainty another entry carries).
 */
export const RANGE_BASES = ["source", "plusMinus50", "sensitivity", "fixed"] as const;

export const EVIDENCE_GRADE_LABELS = {
  A: "Australian causal or structural estimate (or an Australian official statistic or rule)",
  B: "International causal estimate",
  C: "Cross-country correlation, or a model result used as a rule of thumb",
  D: "The tool's assumption, or a user entry",
} as const;
export const VERIFICATION_TAG_LABELS = {
  P: "Read in the primary source",
  A: "Read in the abstract or official summary",
  S: "From secondary coverage only (never a default)",
} as const;

const ID_PREFIX: Readonly<Record<EvidenceChannel, string>> = {
  ...(Object.fromEntries(CHANNEL_IDS.map((id) => [id, id.toLowerCase()])) as Record<(typeof CHANNEL_IDS)[number], string>),
  layerB: "layer-b",
  general: "general",
};

/** The id prefix entries of a channel must use, e.g. "c3" or "layer-b". */
export function evidenceIdPrefix(channel: EvidenceChannel): string {
  return ID_PREFIX[channel];
}

// ---- schema ----------------------------------------------------------------------------------------------------

const finite = z.number().refine(Number.isFinite, "Must be a finite number");
const text = z.string().trim().min(1);
/** A formula or rule id from the productivity traceability document, e.g. F-C3-02, F-B-04, F-U-02 or PR-06. */
export const FormulaIdSchema = z.string().regex(/^(?:F-(?:C\d{1,2}|B|U|O|G)-\d{2}|PR-\d{2})$/, "Use a formula id from docs/productivity_traceability.md, e.g. F-C3-02");
const HttpsUrl = z.string().regex(/^https:\/\/[^\s]+$/, "Use an https URL");
const IsoDate = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Use a date such as 2026-10-22");

export const CitationSchema = z.strictObject({
  authors: text,
  year: z.number().int().min(1900).max(2100),
  title: text,
  /** Publisher, or journal with volume and issue. */
  publisher: text,
  url: HttpsUrl,
  /** Page, table, equation or section, e.g. "Table 1, p. 10 (PDF p. 11)". Required for [P] and [A] entries. */
  locator: text.optional(),
  /** Which version was read, when it matters (a revised working paper, a copy of a DOI). */
  version: text.optional(),
});
export type Citation = z.output<typeof CitationSchema>;

export const ReviewSchema = z
  .strictObject({
    status: z.enum(["draft", "checked"]),
    by: text.optional(),
    on: IsoDate.optional(),
    comment: z.string().optional(),
  })
  .refine((r) => r.status === "draft" || (r.by !== undefined && r.on !== undefined), {
    message: "A checked entry records who checked it and when (by, on)",
  });

/** Per-industry values the parameter pipeline supplies (P2); the entry's value is the economy-wide fallback. */
export const DataSuppliedSchema = z.strictObject({
  source: text,
  table: text,
  note: text,
});

export const EvidenceEntrySchema = z
  .strictObject({
    /** Stable id: channel prefix, parameter, source, e.g. "c3.sigma.cfm2011". */
    id: z.string().regex(/^(?:c\d{1,2}|layer-b|general)(?:\.[a-z0-9]+(?:-[a-z0-9]+)*){2,}$/, 'Use an id such as "c3.sigma.cfm2011"'),
    formula: FormulaIdSchema,
    /** Other formulas that read the same entry (e.g. the required return r in F-C2-01 and F-C3-01). */
    alsoUsedBy: z.array(FormulaIdSchema).min(1).optional(),
    /** The symbol in the formula, e.g. "sigma", or a dotted name such as "meb.companyIncome". */
    parameter: z.string().regex(/^[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z][A-Za-z0-9]*)*$/, 'Use a parameter name such as "sigma"'),
    channel: z.enum(EVIDENCE_CHANNELS),
    label: text,
    value: finite,
    low: finite,
    high: finite,
    units: text,
    rangeBasis: z.enum(RANGE_BASES),
    country: text,
    method: z.enum(EVIDENCE_METHODS),
    grade: z.enum(EVIDENCE_GRADES),
    tag: z.enum(VERIFICATION_TAGS),
    citation: CitationSchema,
    /** Exact text from the source. Several excerpts from the locator are joined with " … ". */
    quote: z.string().optional(),
    /** How value, low and high come from the source. */
    derivation: text,
    /** The one entry per (formula, parameter) that the engine uses by default. */
    isDefault: z.boolean(),
    dataSupplied: DataSuppliedSchema.optional(),
    notes: z.string().optional(),
    review: ReviewSchema,
  })
  .superRefine((e, ctx) => {
    const issue = (path: (string | number)[], message: string) => ctx.addIssue({ code: "custom", path, message });
    if (!(e.low <= e.value && e.value <= e.high)) issue(["value"], `Need low ≤ value ≤ high (got ${e.low}, ${e.value}, ${e.high})`);
    if (!e.id.startsWith(`${evidenceIdPrefix(e.channel)}.`)) issue(["id"], `An entry in ${e.channel} has an id starting "${evidenceIdPrefix(e.channel)}."`);
    if (e.tag !== "S") {
      if (!e.quote?.trim()) issue(["quote"], `An entry tagged [${e.tag}] needs an exact quote from the source`);
      if (!e.citation.locator) issue(["citation", "locator"], `An entry tagged [${e.tag}] needs a page, table or section`);
    }
    if (e.quote !== undefined && e.quote !== e.quote.trim()) issue(["quote"], "Trim spaces around the quote");
    if (e.isDefault && e.tag === "S") issue(["isDefault"], "An entry from secondary coverage only ([S]) is never a default");
    if (e.isDefault && e.grade === "D" && (e.method !== "assumption" || !e.notes?.trim())) {
      issue(["grade"], "A grade-D default must be the tool's assumption (method \"assumption\") and say why in notes");
    }
    if (e.alsoUsedBy?.includes(e.formula)) issue(["alsoUsedBy"], "alsoUsedBy repeats the entry's own formula");
    const near = (a: number, b: number) => Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(a), Math.abs(b));
    switch (e.rangeBasis) {
      case "fixed":
        if (!(e.low === e.value && e.value === e.high)) issue(["rangeBasis"], "A fixed entry has low = value = high");
        break;
      case "plusMinus50":
        if (!near(e.low, e.value - 0.5 * Math.abs(e.value)) || !near(e.high, e.value + 0.5 * Math.abs(e.value))) {
          issue(["rangeBasis"], `The ±50% rule gives low ${e.value - 0.5 * Math.abs(e.value)} and high ${e.value + 0.5 * Math.abs(e.value)}`);
        }
        break;
      default:
        if (!(e.low < e.high)) issue(["rangeBasis"], `A range from the ${e.rangeBasis === "source" ? "source" : "sensitivity cases"} has low < high; use "fixed" otherwise`);
    }
    if (e.review.status === "checked" && e.tag === "S") issue(["review", "status"], "An [S] entry cannot be checked against its primary source");
  });
export type EvidenceEntry = z.output<typeof EvidenceEntrySchema>;
export type EvidenceEntryInput = z.input<typeof EvidenceEntrySchema>;

/** One JSON file: the entries of one channel. */
export const EvidenceFileSchema = z
  .strictObject({
    channel: z.enum(EVIDENCE_CHANNELS),
    entries: z.array(EvidenceEntrySchema).min(1),
  })
  .superRefine((f, ctx) => {
    f.entries.forEach((e, i) => {
      if (e.channel !== f.channel) ctx.addIssue({ code: "custom", path: ["entries", i, "channel"], message: `Entry ${e.id} is in the ${f.channel} file but names channel ${e.channel}` });
    });
  });

// ---- library rules ---------------------------------------------------------------------------------------------

/** The formulas an entry serves: its own and any it is also used by. */
export function entryFormulas(e: Pick<EvidenceEntry, "formula" | "alsoUsedBy">): string[] {
  return [e.formula, ...(e.alsoUsedBy ?? [])];
}

const pairKey = (formula: string, parameter: string) => `${formula} ${parameter}`;

/** Rules that need the whole library: unique ids and exactly one default per (formula, parameter). */
export function libraryIssues(entries: readonly EvidenceEntry[]): string[] {
  const issues: string[] = [];
  const seen = new Set<string>();
  for (const e of entries) {
    if (seen.has(e.id)) issues.push(`Duplicate evidence id "${e.id}"`);
    seen.add(e.id);
  }
  const defaults = new Map<string, string[]>();
  for (const e of entries) {
    for (const f of entryFormulas(e)) {
      const key = pairKey(f, e.parameter);
      const list = defaults.get(key) ?? [];
      if (e.isDefault) list.push(e.id);
      defaults.set(key, list);
    }
  }
  for (const [key, ids] of defaults) {
    const [formula, parameter] = key.split(" ");
    if (ids.length !== 1) {
      issues.push(`${formula} ${parameter} has ${ids.length === 0 ? "no default" : `${ids.length} defaults (${ids.join(", ")})`}: exactly one entry must be the default`);
    }
  }
  return issues;
}

export class EvidenceValidationError extends Error {
  readonly issues: string[];
  constructor(issues: string[]) {
    super(`The evidence library is not valid:\n${issues.map((i) => `  - ${i}`).join("\n")}`);
    this.name = "EvidenceValidationError";
    this.issues = issues;
  }
}

/** Parses evidence files ({ name: json }) and checks the library rules. Returns every problem found. */
export function loadEvidence(files: Readonly<Record<string, unknown>>): { entries: EvidenceEntry[]; issues: string[] } {
  const entries: EvidenceEntry[] = [];
  const issues: string[] = [];
  for (const [name, json] of Object.entries(files)) {
    const r = EvidenceFileSchema.safeParse(json);
    if (r.success) entries.push(...r.data.entries);
    else issues.push(...formatIssues(r.error).map((i) => `${name}: ${i}`));
  }
  if (!issues.length) issues.push(...libraryIssues(entries));
  return { entries, issues };
}

/** Validates one entry on its own (schema rules only); returns the problems found. */
export function evidenceEntryIssues(input: unknown): string[] {
  const r = EvidenceEntrySchema.safeParse(input);
  return r.success ? [] : formatIssues(r.error);
}

/** The bundled files, in display order (channels C1–C11, Layer B, general). C12 has no entries in v1. */
export const EVIDENCE_FILES: Readonly<Record<string, unknown>> = {
  "c1.json": c1,
  "c2.json": c2,
  "c3.json": c3,
  "c4.json": c4,
  "c5.json": c5,
  "c6.json": c6,
  "c7.json": c7,
  "c8.json": c8,
  "c9.json": c9,
  "c10.json": c10,
  "c11.json": c11,
  "layer-b.json": layerB,
  "general.json": general,
};

function loadBundled(): EvidenceEntry[] {
  const { entries, issues } = loadEvidence(EVIDENCE_FILES);
  if (issues.length) throw new EvidenceValidationError(issues);
  return entries;
}

/** The evidence library, validated when this module loads. */
export const EVIDENCE: readonly EvidenceEntry[] = Object.freeze(loadBundled());

/** Every entry for a formula's parameter (the default and its alternatives). */
export function evidenceFor(formula: string, parameter: string, library: readonly EvidenceEntry[] = EVIDENCE): EvidenceEntry[] {
  return library.filter((e) => e.parameter === parameter && entryFormulas(e).includes(formula));
}

/** The entry the engine uses by default for a formula's parameter, or undefined if the library has none. */
export function defaultEvidence(formula: string, parameter: string, library: readonly EvidenceEntry[] = EVIDENCE): EvidenceEntry | undefined {
  return evidenceFor(formula, parameter, library).find((e) => e.isDefault);
}

/** The library grouped by channel, in display order; channels with no entries are left out. */
export function evidenceByChannel(library: readonly EvidenceEntry[] = EVIDENCE): { channel: EvidenceChannel; name: string; entries: EvidenceEntry[] }[] {
  return EVIDENCE_CHANNELS.map((channel) => ({ channel, name: EVIDENCE_CHANNEL_NAMES[channel], entries: library.filter((e) => e.channel === channel) })).filter(
    (g) => g.entries.length > 0,
  );
}

/** "Authors (year), Title. Publisher." */
export function citationText(c: Citation): string {
  return `${c.authors} (${c.year}), ${c.title}. ${c.publisher}.`;
}

// ---- review sheet (docs/review/evidence_library_review.csv) ----------------------------------------------------

/** Columns written from the library; the check columns after them are Cowork's and are kept when the sheet is rebuilt. */
export const REVIEW_SHEET_COLUMNS = [
  "id",
  "formula",
  "parameter",
  "is_default",
  "value",
  "low",
  "high",
  "units",
  "tag",
  "citation",
  "url",
  "locator",
  "quote",
  "derivation",
  "review_status",
] as const;
export const REVIEW_CHECK_COLUMNS = ["check_value", "check_quote", "check_locator", "verdict", "reviewer_notes"] as const;

/** The library columns of the review sheet, one row per entry. */
export function reviewSheetRows(library: readonly EvidenceEntry[] = EVIDENCE): string[][] {
  return library.map((e) => [
    e.id,
    [e.formula, ...(e.alsoUsedBy ?? [])].join("; "),
    e.parameter,
    e.isDefault ? "yes" : "no",
    String(e.value),
    String(e.low),
    String(e.high),
    e.units,
    e.tag,
    citationText(e.citation),
    e.citation.url,
    e.citation.locator ?? "",
    e.quote ?? "",
    e.derivation,
    e.review.status,
  ]);
}

const csvField = (v: string) => (/[",\r\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v);

/** RFC 4180 CSV text with a UTF-8 byte-order mark (so Excel opens it as UTF-8) and LF line endings. */
export function toCsv(rows: readonly (readonly string[])[]): string {
  return `﻿${rows.map((r) => r.map(csvField).join(",")).join("\n")}\n`;
}

/** Parses RFC 4180 CSV (quoted fields, doubled quotes, embedded line breaks); ignores a leading byte-order mark. */
export function parseCsv(input: string): string[][] {
  const s = input.replace(/^﻿/, "");
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < s.length; i++) {
    const ch = s[i]!;
    if (quoted) {
      if (ch === '"' && s[i + 1] === '"') {
        field += '"';
        i++;
      } else if (ch === '"') quoted = false;
      else field += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && s[i + 1] === "\n") i++;
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else field += ch;
  }
  if (field !== "" || row.length) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

/**
 * The review sheet for the library. When the existing sheet is given, the check columns already filled in for an
 * id are carried over, so rebuilding the sheet never loses Cowork's work.
 */
export function evidenceReviewCsv(library: readonly EvidenceEntry[] = EVIDENCE, existing?: string): string {
  const header = [...REVIEW_SHEET_COLUMNS, ...REVIEW_CHECK_COLUMNS];
  const kept = new Map<string, string[]>();
  if (existing) {
    const [head, ...rows] = parseCsv(existing);
    const idAt = head?.indexOf("id") ?? -1;
    const checkAt = REVIEW_CHECK_COLUMNS.map((c) => head?.indexOf(c) ?? -1);
    if (idAt >= 0) for (const r of rows) kept.set(r[idAt] ?? "", checkAt.map((j) => (j >= 0 ? (r[j] ?? "") : "")));
  }
  const body = reviewSheetRows(library).map((r) => [...r, ...(kept.get(r[0]!) ?? REVIEW_CHECK_COLUMNS.map(() => ""))]);
  return toCsv([header, ...body]);
}
