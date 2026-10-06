// Loading and saving versioned proposal files. Older files are migrated step by
// step to the current schema version so they keep loading (DECISIONS #34).
import type { z } from "zod";
import { ProposalFileSchema, ProposalSchema, SCHEMA_VERSION, type Proposal, type ProposalFile } from "./schema";

export class ProposalValidationError extends Error {
  readonly issues: string[];
  constructor(issues: string[]) {
    super(`The proposal is not valid:\n${issues.map((i) => `  - ${i}`).join("\n")}`);
    this.name = "ProposalValidationError";
    this.issues = issues;
  }
}

/** A migration upgrades a file object from version n to version n + 1. */
export type Migration = (file: Record<string, unknown>) => Record<string, unknown>;

/** Registry of migrations, keyed by the version they upgrade from. Empty while only v1 exists. */
export const MIGRATIONS: Readonly<Record<number, Migration>> = {};

export function formatIssues(error: z.ZodError): string[] {
  return error.issues.map((issue) => {
    const path = issue.path.length ? issue.path.join(".") : "(file)";
    return `${path}: ${issue.message}`;
  });
}

/** Parses a proposal object (without the file envelope), applying defaults. */
export function parseProposal(input: unknown): Proposal {
  const result = ProposalSchema.safeParse(input);
  if (!result.success) throw new ProposalValidationError(formatIssues(result.error));
  return result.data;
}

/** Loads a saved file of any supported schema version. */
export function loadProposalFile(
  json: unknown,
  migrations: Readonly<Record<number, Migration>> = MIGRATIONS,
): ProposalFile {
  if (typeof json !== "object" || json === null || !("schemaVersion" in json)) {
    throw new ProposalValidationError(["(file): not a regulatory burden proposal file (no schemaVersion)"]);
  }
  let file = json as Record<string, unknown>;
  const declared = file.schemaVersion;
  if (typeof declared !== "number" || !Number.isInteger(declared) || declared < 0) {
    throw new ProposalValidationError([`schemaVersion: "${String(declared)}" is not a valid version`]);
  }
  let version: number = declared;
  if (version > SCHEMA_VERSION) {
    throw new ProposalValidationError([
      `schemaVersion: this file was saved by a newer version of the tool (schema v${version}); this version reads up to v${SCHEMA_VERSION}`,
    ]);
  }
  while (version < SCHEMA_VERSION) {
    const migrate = migrations[version];
    if (!migrate) throw new ProposalValidationError([`schemaVersion: no migration from v${version}`]);
    file = migrate(file);
    if (file.schemaVersion !== version + 1) {
      throw new ProposalValidationError([`schemaVersion: migration from v${version} did not produce v${version + 1}`]);
    }
    version += 1;
  }
  const result = ProposalFileSchema.safeParse(file);
  if (!result.success) throw new ProposalValidationError(formatIssues(result.error));
  return result.data;
}

/** Wraps a proposal in the versioned file envelope for export. */
export function toProposalFile(proposal: Proposal, savedAt?: string): ProposalFile {
  return savedAt === undefined
    ? { schemaVersion: SCHEMA_VERSION, proposal }
    : { schemaVersion: SCHEMA_VERSION, savedAt, proposal };
}

export type DraftImport =
  | { ok: true; file: ProposalFile }
  | { ok: false; issues: string[] };

/**
 * Loads pasted text as a draft proposal (DECISIONS #60): a saved file, or the reply from a
 * language model, which may wrap the JSON in a code fence or omit the file envelope.
 * Problems come back as a list, so they can be shown to the user or pasted back to the model.
 */
export function importDraft(text: string): DraftImport {
  const fenced = /```(?:json)?\s*([\s\S]*?)```/i.exec(text);
  let body = (fenced?.[1] ?? text).trim();
  const first = body.indexOf("{");
  const last = body.lastIndexOf("}");
  if (first < 0 || last < first) return { ok: false, issues: ["(text): no JSON object found"] };
  body = body.slice(first, last + 1);
  let json: unknown;
  try {
    json = JSON.parse(body);
  } catch (e) {
    return { ok: false, issues: [`(text): not valid JSON (${e instanceof Error ? e.message : String(e)})`] };
  }
  if (typeof json !== "object" || json === null || Array.isArray(json)) {
    return { ok: false, issues: ["(text): expected a JSON object"] };
  }
  const obj = json as Record<string, unknown>;
  const file = "schemaVersion" in obj ? obj : "proposal" in obj ? { schemaVersion: SCHEMA_VERSION, ...obj } : { schemaVersion: SCHEMA_VERSION, proposal: obj };
  try {
    return { ok: true, file: loadProposalFile(file) };
  } catch (e) {
    return { ok: false, issues: e instanceof ProposalValidationError ? e.issues : [String(e)] };
  }
}

