// The engine entry point: a pure function from a proposal to its results.
// No I/O, no clock, no randomness: the same input always gives the same output.
import { aggregateOption } from "./aggregate";
import { parseProposal } from "./migrate";
import { PARAMETERS } from "./parameters";
import { computeOptionItems } from "./reform";
import { SCHEMA_VERSION, type Proposal } from "./schema";
import type { ProposalResult } from "./types";
import { assumptionsRegister, collectWarnings } from "./validate";

export const ENGINE_VERSION = "0.1.0";

/** Calculates every option of a proposal. Accepts raw input (it is validated and defaulted first). */
export function computeProposal(input: unknown): ProposalResult {
  const proposal: Proposal = parseProposal(input);
  const computed = proposal.options.map((option) => {
    const items = computeOptionItems(proposal, option);
    return { option, items, result: aggregateOption(proposal, option, items) };
  });
  return {
    engineVersion: ENGINE_VERSION,
    schemaVersion: SCHEMA_VERSION,
    parameterVintage: PARAMETERS.vintage,
    proposalId: proposal.id,
    title: proposal.title,
    durationYears: proposal.durationYears,
    baseline: proposal.baseline,
    options: computed.map((c) => c.result),
    warnings: collectWarnings(proposal, computed),
    assumptions: assumptionsRegister(proposal),
  };
}
