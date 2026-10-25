// The policy brief bundled with the app: a real policy, the ban on non-compete clauses (2025-26 Budget), with the
// burden options of Treasury's Impact Analysis (2026) and the productivity lever of the PC's simulation.
import example from "../../examples/noncompete-ban.brief.json";

export function exampleBrief(): unknown {
  return structuredClone(example);
}
