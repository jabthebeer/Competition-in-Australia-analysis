// Public API of the productivity and competition engine (plan: docs/forward_plan_policy_costing.md).
// It sits beside the RBM engine and never changes the RBE (DECISIONS #81).
// P0 holds the input contract; P3 the evidence library; P4 the channels, aggregation and costing engine.
export * from "./brief";
export { CHANNELS, CHANNEL_IDS, OVERLAP_RULES, SHOCK_TYPES, channelsFor, type Channel, type ChannelId, type InputBlock, type ShockType } from "./channels";
export { SUBDIVISION_RANGES, covers, divisionOf, overlaps, type Division } from "./anzsic";
// P3: the evidence library (plan §6.7) — sourced defaults and ranges for every formula parameter.
export * from "./evidence";
// P4: Layer B, from industry shocks to GDP (plan §6.3); Layer A channels and the costing engine (plan §6.1–6.2).
export * from "./layerB";
export * from "./context";
export * from "./layerA";
export * from "./engine";
