/// <reference types="vite/client" />

/** The ALICIA costing parameters, bundled at build time (costing-params-plugin.ts). Validate before use. */
declare module "virtual:costing-parameters" {
  const parameters: unknown;
  export default parameters;
}

/** The ALICIA register export (records, channels, evaluation verdicts), bundled at build time. Validate before use. */
declare module "virtual:costing-register" {
  const register: unknown;
  export default register;
}
