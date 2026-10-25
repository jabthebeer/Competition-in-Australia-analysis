// The illustrative policy brief (synthetic data) bundled with the app: a burden proposal with productivity levers.
import example from "../../examples/illustrative-licensing.brief.json";

export function exampleBrief(): unknown {
  return structuredClone(example);
}
