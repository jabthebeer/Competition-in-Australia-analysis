// The policy brief bundled with the app: a real policy, the ban on non-compete clauses (2025-26 Budget), with the
// burden options of Treasury's Impact Analysis (2026) and the productivity lever of the PC's simulation.
import example from "../../examples/noncompete-ban.brief.json";
import type { Proposal } from "../engine/index";
import { parseBrief } from "../productivity/index";
import { splitBrief, type BriefDraft } from "./briefModel";

export function exampleBrief(): unknown {
  return structuredClone(example);
}

/** The example split into what the pages edit: the burden proposal and the productivity draft. */
export function exampleCosting(): { burden: Proposal; draft: BriefDraft } {
  const { burden, draft } = splitBrief(parseBrief(exampleBrief()));
  return { burden: burden!, draft };
}
