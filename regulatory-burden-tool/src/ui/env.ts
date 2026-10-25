// Build flags. Hosted test copies (npm run build:artifact) set both.
/** Opens on the illustrative example when nothing is saved. */
export const DEMO = import.meta.env.VITE_DEMO === "1";
/** Runs inside a hosted viewer that blocks downloads and sits outside the user's own environment. */
export const HOSTED = import.meta.env.VITE_HOSTED === "1";
/** Built as the ALICIA website's Policy costing tab (npm run build:site): evaluation pages are its neighbours. */
export const SITE = import.meta.env.VITE_SITE === "1";
