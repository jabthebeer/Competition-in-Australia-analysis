// Build flags. Hosted test copies (npm run build:artifact) set both.
/** Opens on the illustrative example when nothing is saved. */
export const DEMO = import.meta.env.VITE_DEMO === "1";
/** Runs inside a hosted viewer that blocks downloads and sits outside the user's own environment. */
export const HOSTED = import.meta.env.VITE_HOSTED === "1";
