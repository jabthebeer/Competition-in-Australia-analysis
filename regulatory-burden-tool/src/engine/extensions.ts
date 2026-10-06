// Extension interface (DECISIONS #44). Future modules, such as a competition
// costing module that applies externally estimated entry/exit elasticities, or a
// cost-benefit module, read the engine's results and produce their own outputs.
// They receive frozen copies, so they can never alter the RBE.
import { PARAMETERS } from "./parameters";
import type { Proposal } from "./schema";
import { toTidyRows, type TidyRow } from "./tidy";
import type { ProposalResult } from "./types";

export interface ExtensionContext {
  readonly proposal: Readonly<Proposal>;
  readonly result: Readonly<ProposalResult>;
  readonly tidy: readonly Readonly<TidyRow>[];
  readonly parameters: typeof PARAMETERS;
}

export interface EngineExtension<TOutput = unknown> {
  /** Stable identifier, e.g. "competition-costing". */
  id: string;
  version: string;
  title: string;
  /** What the module adds, and that it sits outside the RBE. */
  description: string;
  compute(context: ExtensionContext): TOutput;
}

export type ExtensionOutcome<TOutput = unknown> =
  | { id: string; version: string; ok: true; output: TOutput }
  | { id: string; version: string; ok: false; error: string };

function deepFreeze<T>(value: T): T {
  if (value !== null && typeof value === "object" && !Object.isFrozen(value)) {
    Object.freeze(value);
    for (const v of Object.values(value as Record<string, unknown>)) deepFreeze(v);
  }
  return value;
}

/**
 * Runs extensions after the RBE has been calculated. Each receives its own frozen
 * copy of the inputs; a failing extension is reported without affecting the others
 * or the RBE.
 */
export function runExtensions(
  proposal: Proposal,
  result: ProposalResult,
  extensions: readonly EngineExtension[],
): ExtensionOutcome[] {
  return extensions.map((ext) => {
    const context: ExtensionContext = deepFreeze({
      proposal: structuredClone(proposal),
      result: structuredClone(result),
      tidy: toTidyRows(result),
      parameters: PARAMETERS,
    });
    try {
      return { id: ext.id, version: ext.version, ok: true as const, output: ext.compute(context) };
    } catch (e) {
      return { id: ext.id, version: ext.version, ok: false as const, error: e instanceof Error ? e.message : String(e) };
    }
  });
}
