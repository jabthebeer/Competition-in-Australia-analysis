// The illustrative example (synthetic data) bundled with the app.
import example from "../../examples/illustrative-reform.json";
import { importDraft, type Proposal } from "../engine/index";

export function exampleProposal(): Proposal {
  const r = importDraft(JSON.stringify(example));
  if (!r.ok) throw new Error(`The bundled example is invalid: ${r.issues.join("; ")}`);
  return r.file.proposal;
}

/** True while nothing has been entered: no obligations or transitions in any option. */
export function isUntouched(p: Proposal): boolean {
  return p.options.every((o) => o.obligations.length === 0 && o.transitions.length === 0);
}
